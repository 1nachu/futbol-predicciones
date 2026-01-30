#!/usr/bin/env python3
"""
API-Football v3 Data Enricher
==============================

Integración con API-Football v3 para enriquecer datos de partidos.

Características:
- Batch strategy: Una llamada diaria a las 00:00 UTC para fixture
- Predicciones: 30 minutos antes del inicio del partido (partidos clave)
- Quota protection: Verificar /status antes de cada llamada
- Feature extraction: Probabilidades matemáticas para ML

Límite: 100 llamadas/día (Plan STARTER)

Uso:
    from api_football_enricher import APIFootballEnricher
    
    enricher = APIFootballEnricher("tu_api_key")
    
    # Batch: Una vez al día a las 00:00 UTC
    fixtures = enricher.fetch_daily_fixtures(league_id=39, season=2026)
    
    # Predicciones: 30 min antes
    predictions = enricher.fetch_pre_match_predictions(match_id=123)
    
    # Features para ML
    features = enricher.extract_ml_features(match_data)

Autor: Backend Integration Team
Versión: 1.0.0
"""

import os
import sys
import json
import logging
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== CONFIGURACIÓN ==========

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_football_enricher.log'),
        logging.StreamHandler()
    ]
)

API_BASE_URL = "https://v3.football.data-api.com"
DB_PATH = "data/databases/api_football_cache.db"
DAILY_LIMIT = 100
FIXTURE_REQUEST_COST = 1
PREDICTION_REQUEST_COST = 1
STATUS_REQUEST_COST = 0  # Gratuito


# ========== ENUMS ==========

class MatchStatus(Enum):
    """Estado del partido"""
    SCHEDULED = "Scheduled"
    LIVE = "Live"
    FINISHED = "Finished"
    POSTPONED = "Postponed"
    CANCELLED = "Cancelled"


class PredictionType(Enum):
    """Tipos de predicción disponibles"""
    FULL_TIME = "full_time"
    UNDER_OVER = "under_over"
    DOUBLE_CHANCE = "double_chance"


# ========== DATACLASSES ==========

@dataclass
class APIQuotaStatus:
    """Estado de cuota diaria"""
    requests_used: int
    requests_available: int
    requests_remaining: int
    reset_date: str
    plan_name: str
    
    @property
    def is_exhausted(self) -> bool:
        """Verifica si la cuota está agotada"""
        return self.requests_available <= 0
    
    @property
    def can_request(self, cost: int = 1) -> bool:
        """Verifica si se puede hacer una solicitud"""
        return self.requests_available >= cost


@dataclass
class MatchPrediction:
    """Predicción de partido"""
    match_id: int
    home_team: str
    away_team: str
    match_date: str
    probability_home_win: float
    probability_draw: float
    probability_away_win: float
    under_2_5_probability: float
    over_2_5_probability: float
    expected_goals_home: float
    expected_goals_away: float
    prediction: str  # HOME_WIN, AWAY_WIN, DRAW
    confidence: float
    comparison: str  # <, =, >
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MatchFixture:
    """Fixture de partido"""
    match_id: int
    league_id: int
    season: int
    round: int
    date: str
    home_team_id: int
    home_team: str
    away_team_id: int
    away_team: str
    status: str
    venue: str
    referee: Optional[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MLFeatures:
    """Features para modelo ML"""
    match_id: int
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    over_2_5_prob: float
    under_2_5_prob: float
    xg_home: float
    xg_away: float
    xg_diff: float
    prediction_label: str
    prediction_confidence: float
    last_updated: str


# ========== CACHÉ Y PERSISTENCIA ==========

class APIFootballCache:
    """Gestor de caché SQLite para API-Football"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa caché"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa base de datos"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de fixtures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixtures (
                match_id INTEGER PRIMARY KEY,
                league_id INTEGER,
                season INTEGER,
                round INTEGER,
                date TEXT,
                home_team_id INTEGER,
                home_team TEXT,
                away_team_id INTEGER,
                away_team TEXT,
                status TEXT,
                venue TEXT,
                referee TEXT,
                cached_at DATETIME,
                UNIQUE(match_id, league_id, season)
            )
        """)
        
        # Tabla de predicciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                match_id INTEGER PRIMARY KEY,
                home_team TEXT,
                away_team TEXT,
                match_date TEXT,
                prob_home_win REAL,
                prob_draw REAL,
                prob_away_win REAL,
                prob_under_2_5 REAL,
                prob_over_2_5 REAL,
                xg_home REAL,
                xg_away REAL,
                prediction TEXT,
                confidence REAL,
                cached_at DATETIME,
                FOREIGN KEY(match_id) REFERENCES fixtures(match_id)
            )
        """)
        
        # Tabla de uso de API
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                cost INTEGER,
                success BOOLEAN,
                response_time REAL,
                timestamp DATETIME,
                quota_remaining INTEGER
            )
        """)
        
        # Tabla de cuota diaria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_quota (
                date DATE PRIMARY KEY,
                requests_used INTEGER,
                reset_time TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_fixture(self, match_id: int) -> Optional[MatchFixture]:
        """Obtiene fixture del caché"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM fixtures WHERE match_id = ?", (match_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MatchFixture(**dict(row))
    
    def save_fixture(self, fixture: MatchFixture):
        """Guarda fixture en caché"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO fixtures
            (match_id, league_id, season, round, date, home_team_id, home_team,
             away_team_id, away_team, status, venue, referee, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fixture.match_id, fixture.league_id, fixture.season, fixture.round,
            fixture.date, fixture.home_team_id, fixture.home_team,
            fixture.away_team_id, fixture.away_team, fixture.status,
            fixture.venue, fixture.referee, datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def get_prediction(self, match_id: int) -> Optional[MatchPrediction]:
        """Obtiene predicción del caché"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM predictions WHERE match_id = ?", (match_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MatchPrediction(**dict(row))
    
    def save_prediction(self, prediction: MatchPrediction):
        """Guarda predicción en caché"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO predictions
            (match_id, home_team, away_team, match_date, prob_home_win,
             prob_draw, prob_away_win, prob_under_2_5, prob_over_2_5,
             xg_home, xg_away, prediction, confidence, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.match_id, prediction.home_team, prediction.away_team,
            prediction.match_date, prediction.probability_home_win,
            prediction.probability_draw, prediction.probability_away_win,
            prediction.under_2_5_probability, prediction.over_2_5_probability,
            prediction.expected_goals_home, prediction.expected_goals_away,
            prediction.prediction, prediction.confidence, datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def log_api_usage(self, endpoint: str, cost: int, success: bool,
                     response_time: float, quota_remaining: int):
        """Registra uso de API"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_usage_log
            (endpoint, cost, success, response_time, timestamp, quota_remaining)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (endpoint, cost, success, response_time, datetime.now(timezone.utc), quota_remaining))
        
        conn.commit()
        conn.close()
    
    def get_today_usage(self) -> int:
        """Obtiene consumo de hoy"""
        today = datetime.now(timezone.utc).date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(cost) as total FROM api_usage_log
            WHERE DATE(timestamp) = ? AND success = 1
        """, (today,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] or 0


# ========== CLIENTE API-FOOTBALL ==========

class APIFootballClient:
    """Cliente para API-Football v3"""
    
    def __init__(self, api_key: str):
        """Inicializa cliente"""
        if not api_key or len(api_key) < 10:
            raise ValueError("API Key inválida para API-Football")
        
        self.api_key = api_key
        self.session = self._create_session()
        self.cache = APIFootballCache()
        self.lock = threading.RLock()
        
        logger.info("Cliente API-Football inicializado")
    
    def _create_session(self) -> requests.Session:
        """Crea sesión con retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def check_quota_status(self) -> APIQuotaStatus:
        """Verifica estado de cuota (gratuito)"""
        logger.info("Verificando estado de cuota...")
        
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{API_BASE_URL}/status",
                headers={"x-apisports-key": self.api_key},
                timeout=10
            )
            
            response_time = time.time() - start_time
            response.raise_for_status()
            
            data = response.json().get("response", {})
            
            status = APIQuotaStatus(
                requests_used=data.get("requests", 0),
                requests_available=data.get("requests_remaining", 0),
                requests_remaining=data.get("requests_remaining", 0),
                reset_date=data.get("results", ""),
                plan_name=data.get("plan", "STARTER")
            )
            
            logger.info(f"Cuota: {status.requests_available} llamadas disponibles")
            
            return status
        
        except Exception as e:
            logger.error(f"Error verificando cuota: {e}")
            raise
    
    def request(self, endpoint: str, params: Dict[str, Any],
                cost: int = 1) -> Dict[str, Any]:
        """Hace request a API con verificación de cuota"""
        with self.lock:
            # Verificar cuota
            quota = self.check_quota_status()
            
            if quota.is_exhausted:
                raise Exception("Cuota diaria agotada (100 llamadas/día)")
            
            if quota.requests_available < cost:
                logger.warning(
                    f"Cuota insuficiente: disponibles {quota.requests_available}, "
                    f"necesarias {cost}"
                )
                raise Exception("Cuota insuficiente para esta solicitud")
            
            # Hacer request
            logger.info(f"Solicitando {endpoint} (costo: {cost})")
            
            try:
                start_time = time.time()
                
                response = self.session.get(
                    f"{API_BASE_URL}{endpoint}",
                    params=params,
                    headers={"x-apisports-key": self.api_key},
                    timeout=30
                )
                
                response_time = time.time() - start_time
                response.raise_for_status()
                
                data = response.json()
                
                # Log de uso
                self.cache.log_api_usage(
                    endpoint=endpoint,
                    cost=cost,
                    success=True,
                    response_time=response_time,
                    quota_remaining=quota.requests_available - cost
                )
                
                logger.info(
                    f"✓ {endpoint} - Tiempo: {response_time:.2f}s "
                    f"- Cuota restante: {quota.requests_available - cost}"
                )
                
                return data
            
            except Exception as e:
                logger.error(f"Error en request: {e}")
                
                self.cache.log_api_usage(
                    endpoint=endpoint,
                    cost=0,
                    success=False,
                    response_time=time.time() - start_time,
                    quota_remaining=quota.requests_available
                )
                
                raise


# ========== ESTRATEGIA DE BATCHING ==========

class BatchFetcher:
    """Fetch batch de fixtures una vez al día"""
    
    def __init__(self, client: APIFootballClient):
        """Inicializa fetcher"""
        self.client = client
        self.cache = client.cache
        self.last_fetch = None
    
    def should_fetch_today(self) -> bool:
        """Verifica si ya se ejecutó hoy"""
        if self.last_fetch is None:
            return True
        
        today_utc = datetime.now(timezone.utc).date()
        fetch_date = self.last_fetch.date()
        
        return today_utc > fetch_date
    
    def fetch_daily_fixtures(self, league_id: int = 39, season: int = 2026) -> List[MatchFixture]:
        """
        Fetch batch una sola vez al día (00:00 UTC)
        
        Args:
            league_id: ID de liga (39 = Premier League)
            season: Año de temporada
        
        Returns:
            Lista de fixtures del día
        """
        logger.info("="*70)
        logger.info("BATCH FETCH: Obteniendo fixtures del día")
        logger.info("="*70)
        
        if not self.should_fetch_today():
            logger.info("✓ Ya se ejecutó batch hoy, usando caché")
            return []
        
        try:
            # Request fixtures
            data = self.client.request(
                endpoint="/fixtures",
                params={
                    "league": league_id,
                    "season": season,
                    "timezone": "UTC"
                },
                cost=FIXTURE_REQUEST_COST
            )
            
            fixtures = []
            
            for match_data in data.get("response", []):
                fixture = self._parse_fixture(match_data)
                self.cache.save_fixture(fixture)
                fixtures.append(fixture)
            
            self.last_fetch = datetime.now(timezone.utc)
            
            logger.info(f"✓ Batch completado: {len(fixtures)} fixtures obtenidos")
            
            return fixtures
        
        except Exception as e:
            logger.error(f"Error en batch fetch: {e}")
            return []
    
    def _parse_fixture(self, data: Dict[str, Any]) -> MatchFixture:
        """Parsea dato de fixture desde API"""
        fixture = data.get("fixture", {})
        league = data.get("league", {})
        teams = data.get("teams", {})
        
        return MatchFixture(
            match_id=fixture.get("id"),
            league_id=league.get("id"),
            season=league.get("season"),
            round=int(league.get("round", "1").split()[-1]),
            date=fixture.get("date"),
            home_team_id=teams.get("home", {}).get("id"),
            home_team=teams.get("home", {}).get("name"),
            away_team_id=teams.get("away", {}).get("id"),
            away_team=teams.get("away", {}).get("name"),
            status=fixture.get("status"),
            venue=fixture.get("venue", {}).get("name", ""),
            referee=data.get("league", {}).get("referee")
        )


# ========== ESTRATEGIA DE PREDICCIONES ==========

class PredictionFetcher:
    """Fetch predicciones 30 minutos antes del inicio"""
    
    def __init__(self, client: APIFootballClient):
        """Inicializa fetcher"""
        self.client = client
        self.cache = client.cache
        self.scheduled_matches = {}
    
    def schedule_prediction_fetch(self, match_id: int, match_date: str,
                                  home_team: str, away_team: str):
        """Agenda fetch de predicción para 30 min antes"""
        match_dt = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        fetch_time = match_dt - timedelta(minutes=30)
        
        self.scheduled_matches[match_id] = {
            'fetch_time': fetch_time,
            'match_date': match_date,
            'home_team': home_team,
            'away_team': away_team
        }
        
        logger.info(f"Predicción agendada para {home_team} vs {away_team}")
        logger.info(f"  Hora partido: {match_dt.isoformat()}")
        logger.info(f"  Hora fetch: {fetch_time.isoformat()}")
    
    def get_pending_predictions(self) -> List[int]:
        """Obtiene IDs de partidos listos para fetch"""
        now_utc = datetime.now(timezone.utc)
        pending = []
        
        for match_id, data in self.scheduled_matches.items():
            fetch_time = data['fetch_time']
            
            if now_utc >= fetch_time and now_utc < fetch_time + timedelta(minutes=1):
                pending.append(match_id)
        
        return pending
    
    def fetch_prediction(self, match_id: int) -> Optional[MatchPrediction]:
        """
        Fetch predicción para un partido específico
        (30 minutos antes del inicio)
        
        Args:
            match_id: ID del partido
        
        Returns:
            Predicción del partido o None
        """
        # Verificar caché primero
        cached = self.cache.get_prediction(match_id)
        if cached:
            logger.info(f"✓ Predicción en caché para match {match_id}")
            return cached
        
        try:
            logger.info(f"Fetch predicción para match {match_id}...")
            
            data = self.client.request(
                endpoint="/predictions",
                params={"fixture": match_id},
                cost=PREDICTION_REQUEST_COST
            )
            
            predictions = data.get("response", [])
            
            if not predictions:
                logger.warning(f"No predictions available for match {match_id}")
                return None
            
            prediction = self._parse_prediction(match_id, predictions[0])
            self.cache.save_prediction(prediction)
            
            logger.info(f"✓ Predicción obtenida para {prediction.home_team} vs {prediction.away_team}")
            
            return prediction
        
        except Exception as e:
            logger.error(f"Error fetching prediction: {e}")
            return None
    
    def _parse_prediction(self, match_id: int, data: Dict[str, Any]) -> MatchPrediction:
        """Parsea predicción desde API"""
        predictions = data.get("predictions", {})
        teams = data.get("teams", {})
        fixture = data.get("fixture", {})
        
        # Extraer probabilidades
        prob_home = predictions.get("win", {}).get("home", 0)
        prob_draw = predictions.get("draw", 0)
        prob_away = predictions.get("win", {}).get("away", 0)
        
        # Normalizar si es necesario
        total = prob_home + prob_draw + prob_away
        if total > 0:
            prob_home /= total
            prob_draw /= total
            prob_away /= total
        
        # Determinar predicción
        probs = {'HOME_WIN': prob_home, 'DRAW': prob_draw, 'AWAY_WIN': prob_away}
        prediction_label = max(probs, key=probs.get)
        confidence = probs[prediction_label]
        
        return MatchPrediction(
            match_id=match_id,
            home_team=teams.get("home", {}).get("name", ""),
            away_team=teams.get("away", {}).get("name", ""),
            match_date=fixture.get("date", ""),
            probability_home_win=prob_home,
            probability_draw=prob_draw,
            probability_away_win=prob_away,
            under_2_5_probability=predictions.get("under_over", {}).get("under", 0),
            over_2_5_probability=predictions.get("under_over", {}).get("over", 0),
            expected_goals_home=predictions.get("goals", {}).get("home", 0),
            expected_goals_away=predictions.get("goals", {}).get("away", 0),
            prediction=prediction_label,
            confidence=confidence,
            comparison=data.get("comparison", "")
        )


# ========== EXTRACCIÓN DE FEATURES ==========

class MLFeatureExtractor:
    """Extrae features para modelo ML"""
    
    @staticmethod
    def extract_features(match_id: int, prediction: MatchPrediction) -> MLFeatures:
        """
        Extrae features matemáticas para modelo ML
        
        Args:
            match_id: ID del partido
            prediction: Predicción del partido
        
        Returns:
            Features para modelo ML
        """
        # XG difference
        xg_diff = prediction.expected_goals_home - prediction.expected_goals_away
        
        # Determinar label
        if prediction.probability_home_win > max(prediction.probability_draw, prediction.probability_away_win):
            label = "HOME_WIN"
        elif prediction.probability_away_win > max(prediction.probability_draw, prediction.probability_home_win):
            label = "AWAY_WIN"
        else:
            label = "DRAW"
        
        return MLFeatures(
            match_id=match_id,
            home_win_prob=prediction.probability_home_win,
            draw_prob=prediction.probability_draw,
            away_win_prob=prediction.probability_away_win,
            over_2_5_prob=prediction.over_2_5_probability,
            under_2_5_prob=prediction.under_2_5_probability,
            xg_home=prediction.expected_goals_home,
            xg_away=prediction.expected_goals_away,
            xg_diff=xg_diff,
            prediction_label=label,
            prediction_confidence=prediction.confidence,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def features_to_dict(features: MLFeatures) -> Dict[str, Any]:
        """Convierte features a diccionario"""
        return asdict(features)


# ========== CLASE PRINCIPAL ==========

class APIFootballEnricher:
    """Orquestador de enriquecimiento de datos con API-Football"""
    
    def __init__(self, api_key: str):
        """Inicializa enricher"""
        self.api_key = api_key
        self.client = APIFootballClient(api_key)
        self.batch_fetcher = BatchFetcher(self.client)
        self.prediction_fetcher = PredictionFetcher(self.client)
        self.feature_extractor = MLFeatureExtractor()
        
        logger.info("API-Football Enricher inicializado")
    
    def fetch_daily_fixtures(self, league_id: int = 39, 
                            season: int = 2026) -> List[MatchFixture]:
        """Fetch diario de fixtures (00:00 UTC)"""
        return self.batch_fetcher.fetch_daily_fixtures(league_id, season)
    
    def fetch_pre_match_predictions(self, match_id: int) -> Optional[MatchPrediction]:
        """Fetch de predicción 30 min antes del inicio"""
        return self.prediction_fetcher.fetch_prediction(match_id)
    
    def extract_ml_features(self, match_id: int,
                          prediction: MatchPrediction) -> MLFeatures:
        """Extrae features para modelo ML"""
        return self.feature_extractor.extract_features(match_id, prediction)
    
    def schedule_prediction_fetch(self, match_id: int, match_date: str,
                                 home_team: str, away_team: str):
        """Agenda fetch de predicción"""
        self.prediction_fetcher.schedule_prediction_fetch(
            match_id, match_date, home_team, away_team
        )
    
    def get_quota_status(self) -> APIQuotaStatus:
        """Obtiene estado de cuota"""
        return self.client.check_quota_status()
    
    def get_usage_today(self) -> int:
        """Obtiene consumo de hoy"""
        return self.client.cache.get_today_usage()


# ========== UTILIDADES ==========

def validate_api_key(api_key: str) -> bool:
    """Valida formato de API Key"""
    if not api_key or len(api_key) < 10:
        return False
    return True


if __name__ == '__main__':
    # Test
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print("❌ API_FOOTBALL_KEY no está configurada")
        sys.exit(1)
    
    try:
        enricher = APIFootballEnricher(api_key)
        
        # Verificar cuota
        quota = enricher.get_quota_status()
        print(f"\n✓ Cuota disponible: {quota.requests_available}")
        print(f"  Plan: {quota.plan_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
