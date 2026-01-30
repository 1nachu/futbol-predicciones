#!/usr/bin/env python3
"""
API-Football v3 Scheduler
==========================

Scheduler para ejecutar estrategias de batching y predicciones en horarios específicos.

Estrategia:
1. 00:00 UTC: Batch fetch de fixtures del día
2. 30 min antes: Fetch de predicciones para partidos clave
3. Constante: Verificación de cuota antes de llamadas

Uso:
    from api_football_scheduler import APIFootballScheduler
    
    scheduler = APIFootballScheduler("tu_api_key")
    scheduler.start()  # Inicia scheduler en background
    
    # El scheduler automáticamente:
    # - Hace batch fetch a las 00:00 UTC
    # - Programa predicciones 30 min antes
    # - Verifica cuota antes de cada llamada
    
    time.sleep(3600)  # Dejar corriendo...
    scheduler.stop()

Autor: Backend Integration Team
Versión: 1.0.0
"""

import os
import sys
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Callable, List

import schedule

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from api_football_enricher import (
    APIFootballEnricher,
    MatchFixture,
    MatchPrediction,
    APIQuotaStatus
)

# ========== CONFIGURACIÓN ==========

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_football_scheduler.log'),
        logging.StreamHandler()
    ]
)


# ========== SCHEDULER ==========

class APIFootballScheduler:
    """Scheduler para API-Football con batching y predicciones"""
    
    def __init__(self, api_key: str, league_id: int = 39, season: int = 2026):
        """
        Inicializa scheduler
        
        Args:
            api_key: API Key de API-Football
            league_id: ID de liga (39 = Premier League)
            season: Año de temporada
        """
        self.api_key = api_key
        self.league_id = league_id
        self.season = season
        self.enricher = APIFootballEnricher(api_key)
        
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.RLock()
        
        # Callbacks
        self.on_batch_completed: Optional[Callable] = None
        self.on_prediction_fetched: Optional[Callable] = None
        self.on_quota_warning: Optional[Callable] = None
        
        logger.info("Scheduler inicializado")
    
    def schedule_jobs(self):
        """Programa trabajos del scheduler"""
        logger.info("Programando trabajos...")
        
        # Batch fetch a las 00:00 UTC
        schedule.every().day.at("00:00").do(
            self._batch_fetch_job,
            self.league_id,
            self.season
        )
        logger.info("✓ Batch fetch programado para 00:00 UTC")
        
        # Verificar predicciones pendientes cada minuto
        schedule.every(1).minutes.do(self._check_predictions_job)
        logger.info("✓ Verificación de predicciones cada minuto")
        
        # Verificar cuota cada 6 horas
        schedule.every(6).hours.do(self._quota_check_job)
        logger.info("✓ Verificación de cuota cada 6 horas")
    
    def _batch_fetch_job(self, league_id: int, season: int):
        """Job de batch fetch (00:00 UTC)"""
        logger.info("\n" + "="*70)
        logger.info("🔄 INICIANDO BATCH FETCH (00:00 UTC)")
        logger.info("="*70 + "\n")
        
        try:
            fixtures = self.enricher.fetch_daily_fixtures(league_id, season)
            
            logger.info(f"\n✓ Batch completado: {len(fixtures)} fixtures")
            
            # Agendar predicciones
            self._schedule_predictions_for_day(fixtures)
            
            # Callback
            if self.on_batch_completed:
                self.on_batch_completed(fixtures)
        
        except Exception as e:
            logger.error(f"Error en batch fetch: {e}")
    
    def _schedule_predictions_for_day(self, fixtures: List[MatchFixture]):
        """Agenda predicciones para todos los fixtures del día"""
        for fixture in fixtures:
            try:
                self.enricher.schedule_prediction_fetch(
                    match_id=fixture.match_id,
                    match_date=fixture.date,
                    home_team=fixture.home_team,
                    away_team=fixture.away_team
                )
            except Exception as e:
                logger.error(f"Error agendando predicción: {e}")
    
    def _check_predictions_job(self):
        """Job que verifica si hay predicciones pendientes"""
        pending = self.enricher.prediction_fetcher.get_pending_predictions()
        
        if not pending:
            return
        
        logger.info(f"📊 Predicciones pendientes: {len(pending)}")
        
        for match_id in pending:
            try:
                prediction = self.enricher.fetch_pre_match_predictions(match_id)
                
                if prediction:
                    # Extraer features
                    features = self.enricher.extract_ml_features(
                        match_id, prediction
                    )
                    
                    logger.info(
                        f"✓ Features extraídas: "
                        f"{prediction.home_team} vs {prediction.away_team}"
                    )
                    
                    # Callback
                    if self.on_prediction_fetched:
                        self.on_prediction_fetched(prediction, features)
            
            except Exception as e:
                logger.error(f"Error fetching prediction {match_id}: {e}")
    
    def _quota_check_job(self):
        """Job de verificación de cuota"""
        try:
            quota = self.enricher.get_quota_status()
            used = self.enricher.get_usage_today()
            
            logger.info("\n" + "="*70)
            logger.info("📊 ESTADO DE CUOTA DIARIA")
            logger.info("="*70)
            logger.info(f"Utilizadas hoy: {used}/100 llamadas")
            logger.info(f"Disponibles: {quota.requests_available}")
            logger.info(f"Plan: {quota.plan_name}")
            logger.info("="*70 + "\n")
            
            # Warning si casi se acaba
            if quota.requests_available < 10:
                logger.warning(f"⚠️  CUOTA BAJA: Solo {quota.requests_available} llamadas disponibles")
                
                if self.on_quota_warning:
                    self.on_quota_warning(quota)
        
        except Exception as e:
            logger.error(f"Error en quota check: {e}")
    
    def _run_scheduler(self):
        """Loop del scheduler (ejecuta en thread separado)"""
        logger.info("Scheduler iniciado en background thread")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error en scheduler loop: {e}")
                time.sleep(5)
    
    def start(self):
        """Inicia scheduler en background"""
        if self.running:
            logger.warning("Scheduler ya está corriendo")
            return
        
        with self.lock:
            self.running = True
            self.schedule_jobs()
            
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler,
                daemon=True
            )
            self.scheduler_thread.start()
            
            logger.info("✓ Scheduler iniciado")
    
    def stop(self):
        """Detiene scheduler"""
        with self.lock:
            self.running = False
            
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            
            schedule.clear()
            
            logger.info("✓ Scheduler detenido")
    
    def register_batch_callback(self, callback: Callable):
        """Registra callback para batch completado"""
        self.on_batch_completed = callback
    
    def register_prediction_callback(self, callback: Callable):
        """Registra callback para predicción obtenida"""
        self.on_prediction_fetched = callback
    
    def register_quota_warning_callback(self, callback: Callable):
        """Registra callback para warning de cuota"""
        self.on_quota_warning = callback
    
    def get_status(self) -> dict:
        """Obtiene estado actual del scheduler"""
        return {
            'running': self.running,
            'quota_used': self.enricher.get_usage_today(),
            'quota_status': self.enricher.get_quota_status().__dict__,
        }


# ========== CALLBACKS DE EJEMPLO ==========

def example_batch_callback(fixtures: List[MatchFixture]):
    """Callback de ejemplo cuando batch se completa"""
    print("\n" + "="*70)
    print("CALLBACK: Batch completado")
    print("="*70)
    
    for fixture in fixtures[:3]:  # Mostrar primeros 3
        print(f"\n📅 {fixture.date}")
        print(f"   {fixture.home_team} vs {fixture.away_team}")
        print(f"   Estado: {fixture.status}")


def example_prediction_callback(prediction, features):
    """Callback de ejemplo cuando predicción se obtiene"""
    print("\n" + "="*70)
    print("CALLBACK: Predicción obtenida")
    print("="*70)
    print(f"Partido: {prediction.home_team} vs {prediction.away_team}")
    print(f"Predicción: {features.prediction_label} ({features.prediction_confidence:.2%})")
    print(f"Probabilidades:")
    print(f"  HOME WIN: {features.home_win_prob:.2%}")
    print(f"  DRAW: {features.draw_prob:.2%}")
    print(f"  AWAY WIN: {features.away_win_prob:.2%}")
    print(f"XG Difference: {features.xg_diff:.2f}")


def example_quota_warning_callback(quota):
    """Callback de ejemplo para warning de cuota"""
    print("\n" + "="*70)
    print(f"⚠️  WARNING: Cuota baja ({quota.requests_available} disponibles)")
    print("="*70)


# ========== MAIN ==========

if __name__ == '__main__':
    api_key = os.getenv("API_FOOTBALL_KEY")
    
    if not api_key:
        print("❌ API_FOOTBALL_KEY no está configurada")
        print("   Ejecuta: export API_FOOTBALL_KEY='tu_clave'")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("API-FOOTBALL v3 SCHEDULER - DEMO")
    print("="*70 + "\n")
    
    # Crear scheduler
    scheduler = APIFootballScheduler(api_key)
    
    # Registrar callbacks
    scheduler.register_batch_callback(example_batch_callback)
    scheduler.register_prediction_callback(example_prediction_callback)
    scheduler.register_quota_warning_callback(example_quota_warning_callback)
    
    # Iniciar
    scheduler.start()
    
    print("✓ Scheduler corriendo en background")
    print("  - Batch fetch: 00:00 UTC")
    print("  - Predicciones: 30 min antes de cada partido")
    print("  - Verificación cuota: cada 6 horas")
    print("\nPresiona Ctrl+C para detener\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nDeteniendo scheduler...")
        scheduler.stop()
        print("✓ Scheduler detenido")
