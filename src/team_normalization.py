"""
Team Normalization System
=========================

Sistema de normalización de nombres de equipos usando Levenshtein fuzzy matching
y tabla maestra con UUIDs únicos internos para reconciliar datos de múltiples
fuentes (Football-Data.org, API-Football, CSVs históricos).

Features:
- Tabla maestra de equipos con UUID único interno
- Mapeo automático de IDs externos a internos
- Similitud configurable (default: >90% para mapeo automático)
- Caché en memoria para optimizar búsquedas
- Logging detallado de mapeos y conflictos
- Soporte para alias de equipos
- Validación de integridad referencial

Usage:
    from src.team_normalization import TeamNormalizer
    
    normalizer = TeamNormalizer(db_path="data/databases/football_data.db")
    
    # Mapear nombre a UUID interno
    team_uuid = normalizer.normalize_team("Manchester United", source="footballdata")
    
    # Agregar nuevo equipo
    new_uuid = normalizer.add_team(
        official_name="Manchester United FC",
        country="England",
        source="footballdata",
        external_id="12345"
    )
"""

import sqlite3
import uuid
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from thefuzz import fuzz, process
from pathlib import Path
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MasterTeam:
    """Representa un equipo en la tabla maestra."""
    team_uuid: str
    official_name: str
    country: str
    league: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()


@dataclass
class ExternalTeamMapping:
    """Mapeo de ID externo a UUID interno."""
    mapping_id: str
    team_uuid: str
    source: str  # 'footballdata', 'apifootball', 'csv', etc.
    external_id: str
    external_name: str
    similarity_score: float  # 0-100 (similitud con official_name)
    is_automatic: bool  # True si fue mapeado automáticamente
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class TeamAlias:
    """Alias alternativo para un equipo (ej: "Man United" → "Manchester United")."""
    alias_id: str
    team_uuid: str
    alias_name: str
    priority: int = 0  # Orden de prioridad en búsquedas
    source: Optional[str] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class TeamNormalizer:
    """
    Gestor central de normalización de equipos con tabla maestra.
    
    Proporciona:
    - CRUD para tabla maestra de equipos
    - Mapeo fuzzy de nombres a UUIDs
    - Gestión de mappings externos
    - Sistema de aliases
    - Caché en memoria
    """
    
    SIMILARITY_THRESHOLD = 90  # % para mapeo automático
    CACHE_SIZE = 1000
    
    def __init__(self, db_path: str = "data/databases/football_data.db"):
        """
        Inicializa el normalizador.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self._cache = {}  # {team_name: team_uuid}
        self._external_cache = {}  # {(source, external_id): team_uuid}
        self._initialized = False
        
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        self._load_cache()
        logger.info(f"TeamNormalizer initialized with DB: {db_path}")
    
    def _init_db(self):
        """Crea las tablas necesarias si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla maestra de equipos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_teams (
                team_uuid TEXT PRIMARY KEY,
                official_name TEXT NOT NULL UNIQUE,
                country TEXT NOT NULL,
                league TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Tabla de mapeos externos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_team_mappings (
                mapping_id TEXT PRIMARY KEY,
                team_uuid TEXT NOT NULL,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                external_name TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                is_automatic INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (team_uuid) REFERENCES master_teams(team_uuid),
                UNIQUE(source, external_id)
            )
        """)
        
        # Tabla de aliases
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_aliases (
                alias_id TEXT PRIMARY KEY,
                team_uuid TEXT NOT NULL,
                alias_name TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                source TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (team_uuid) REFERENCES master_teams(team_uuid),
                UNIQUE(team_uuid, alias_name)
            )
        """)
        
        # Índices para optimizar búsquedas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_master_teams_official_name 
            ON master_teams(official_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_mappings_source_id 
            ON external_team_mappings(source, external_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aliases_name 
            ON team_aliases(alias_name)
        """)
        
        conn.commit()
        conn.close()
        self._initialized = True
        logger.info("Database initialized successfully")
    
    def _load_cache(self):
        """Carga la caché desde la BD."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cargar teams
        cursor.execute("SELECT official_name, team_uuid FROM master_teams")
        for name, uuid_val in cursor.fetchall():
            self._cache[name.lower()] = uuid_val
        
        # Cargar external mappings
        cursor.execute("""
            SELECT source, external_id, team_uuid 
            FROM external_team_mappings
        """)
        for source, ext_id, uuid_val in cursor.fetchall():
            self._external_cache[(source, ext_id)] = uuid_val
        
        conn.close()
        logger.info(f"Cache loaded: {len(self._cache)} teams, {len(self._external_cache)} mappings")
    
    def add_team(
        self,
        official_name: str,
        country: str,
        league: Optional[str] = None,
        source: Optional[str] = None,
        external_id: Optional[str] = None,
        external_name: Optional[str] = None
    ) -> str:
        """
        Agrega un nuevo equipo a la tabla maestra.
        
        Args:
            official_name: Nombre oficial del equipo
            country: País
            league: Liga (opcional)
            source: Fuente de datos (para mapeo externo)
            external_id: ID externo
            external_name: Nombre en la fuente externa
        
        Returns:
            UUID único del equipo
        """
        team_uuid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        team = MasterTeam(
            team_uuid=team_uuid,
            official_name=official_name,
            country=country,
            league=league,
            created_at=now,
            updated_at=now
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO master_teams 
                (team_uuid, official_name, country, league, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (team.team_uuid, team.official_name, team.country, team.league, 
                  team.created_at, team.updated_at))
            
            # Agregar mapeo externo si se proporciona
            if source and external_id:
                similarity = 100.0  # Nombre nuevo, 100% confianza
                self.add_external_mapping(
                    team_uuid=team_uuid,
                    source=source,
                    external_id=external_id,
                    external_name=external_name or official_name,
                    similarity_score=similarity,
                    is_automatic=False
                )
            
            conn.commit()
            conn.close()
            
            # Actualizar caché
            self._cache[official_name.lower()] = team_uuid
            
            logger.info(f"Team added: {official_name} ({team_uuid})")
            return team_uuid
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding team {official_name}: {e}")
            raise
    
    def add_external_mapping(
        self,
        team_uuid: str,
        source: str,
        external_id: str,
        external_name: str,
        similarity_score: float,
        is_automatic: bool = False
    ) -> str:
        """
        Agrega un mapeo de ID externo a UUID interno.
        
        Args:
            team_uuid: UUID interno
            source: Fuente de datos ('footballdata', 'apifootball', etc.)
            external_id: ID en la fuente externa
            external_name: Nombre en la fuente externa
            similarity_score: Similitud (0-100)
            is_automatic: True si fue mapeado automáticamente
        
        Returns:
            ID del mapeo
        """
        mapping_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        mapping = ExternalTeamMapping(
            mapping_id=mapping_id,
            team_uuid=team_uuid,
            source=source,
            external_id=external_id,
            external_name=external_name,
            similarity_score=similarity_score,
            is_automatic=is_automatic,
            created_at=now
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO external_team_mappings
                (mapping_id, team_uuid, source, external_id, external_name, 
                 similarity_score, is_automatic, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mapping.mapping_id, mapping.team_uuid, mapping.source, 
                  mapping.external_id, mapping.external_name, 
                  mapping.similarity_score, int(mapping.is_automatic), mapping.created_at))
            
            conn.commit()
            conn.close()
            
            # Actualizar caché
            self._external_cache[(source, external_id)] = team_uuid
            
            action = "auto-mapped" if is_automatic else "manually-mapped"
            logger.info(f"External mapping added: {source}/{external_id} → {team_uuid} ({action})")
            return mapping_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding mapping {source}/{external_id}: {e}")
            raise
    
    def normalize_team(
        self,
        team_name: str,
        source: Optional[str] = None,
        external_id: Optional[str] = None,
        create_if_missing: bool = True
    ) -> Tuple[str, float]:
        """
        Normaliza un nombre de equipo a UUID interno usando fuzzy matching.
        
        Strategy:
        1. Si (source, external_id) existe en mappings → return UUID
        2. Si nombre exacto existe → return UUID
        3. Si alias exacto existe → return UUID
        4. Fuzzy match con threshold 90% → auto-map y return UUID
        5. Si no encontrado y create_if_missing → crear nuevo equipo
        6. Si no encontrado y no create_if_missing → return None
        
        Args:
            team_name: Nombre del equipo
            source: Fuente de datos (opcional)
            external_id: ID externo (opcional)
            create_if_missing: Crear nuevo equipo si no existe
        
        Returns:
            Tuple (team_uuid, similarity_score)
        """
        
        # 1. Buscar por mapeo externo
        if source and external_id:
            cache_key = (source, external_id)
            if cache_key in self._external_cache:
                uuid_val = self._external_cache[cache_key]
                logger.info(f"Found in external cache: {source}/{external_id} → {uuid_val}")
                return uuid_val, 100.0
        
        # 2. Buscar por nombre exacto
        team_name_lower = team_name.lower()
        if team_name_lower in self._cache:
            uuid_val = self._cache[team_name_lower]
            logger.info(f"Found exact match: {team_name} → {uuid_val}")
            return uuid_val, 100.0
        
        # 3. Buscar por alias exacto
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT team_uuid FROM team_aliases 
            WHERE LOWER(alias_name) = ? 
            ORDER BY priority DESC LIMIT 1
        """, (team_name_lower,))
        
        result = cursor.fetchone()
        if result:
            uuid_val = result[0]
            logger.info(f"Found alias match: {team_name} → {uuid_val}")
            conn.close()
            return uuid_val, 100.0
        
        # 4. Fuzzy match contra tabla maestra
        cursor.execute("SELECT official_name, team_uuid FROM master_teams")
        teams = cursor.fetchall()
        conn.close()
        
        if teams:
            names = [t[0] for t in teams]
            matches = process.extract(team_name, names, scorer=fuzz.token_set_ratio, limit=3)
            
            if matches:
                best_name, similarity = matches[0]
                team_uuid = next(t[1] for t in teams if t[0] == best_name)
                
                logger.info(f"Fuzzy match: {team_name} → {best_name} (similarity: {similarity}%)")
                
                # Auto-mapear si similitud > threshold
                if similarity >= self.SIMILARITY_THRESHOLD:
                    logger.info(f"Auto-mapping: {team_name} → {team_uuid} ({similarity}%)")
                    
                    if source and external_id:
                        self.add_external_mapping(
                            team_uuid=team_uuid,
                            source=source,
                            external_id=external_id,
                            external_name=team_name,
                            similarity_score=float(similarity),
                            is_automatic=True
                        )
                    
                    return team_uuid, float(similarity)
                else:
                    logger.warning(f"Similarity {similarity}% below threshold ({self.SIMILARITY_THRESHOLD}%)")
        
        # 5. Crear nuevo equipo si es necesario
        if create_if_missing:
            logger.warning(f"Creating new team: {team_name}")
            new_uuid = self.add_team(
                official_name=team_name,
                country="Unknown",
                source=source,
                external_id=external_id,
                external_name=team_name
            )
            return new_uuid, 0.0
        
        logger.error(f"No mapping found for: {team_name}")
        return None, 0.0
    
    def add_alias(
        self,
        team_uuid: str,
        alias_name: str,
        priority: int = 0,
        source: Optional[str] = None
    ) -> str:
        """
        Agrega un alias para un equipo.
        
        Args:
            team_uuid: UUID del equipo
            alias_name: Nombre alternativo
            priority: Prioridad en búsquedas (mayor = más prioritario)
            source: Fuente del alias
        
        Returns:
            ID del alias
        """
        alias_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        alias = TeamAlias(
            alias_id=alias_id,
            team_uuid=team_uuid,
            alias_name=alias_name,
            priority=priority,
            source=source,
            created_at=now
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO team_aliases
                (alias_id, team_uuid, alias_name, priority, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (alias.alias_id, alias.team_uuid, alias.alias_name, 
                  alias.priority, alias.source, alias.created_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Alias added: {alias_name} → {team_uuid}")
            return alias_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding alias {alias_name}: {e}")
            raise
    
    def get_team(self, team_uuid: str) -> Optional[Dict]:
        """Obtiene información completa de un equipo."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT team_uuid, official_name, country, league, created_at, updated_at
            FROM master_teams WHERE team_uuid = ?
        """, (team_uuid,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        team = {
            'team_uuid': row[0],
            'official_name': row[1],
            'country': row[2],
            'league': row[3],
            'created_at': row[4],
            'updated_at': row[5],
            'mappings': [],
            'aliases': []
        }
        
        # Obtener mapeos externos
        cursor.execute("""
            SELECT source, external_id, external_name, similarity_score, is_automatic
            FROM external_team_mappings WHERE team_uuid = ?
            ORDER BY created_at DESC
        """, (team_uuid,))
        
        for source, ext_id, ext_name, sim, is_auto in cursor.fetchall():
            team['mappings'].append({
                'source': source,
                'external_id': ext_id,
                'external_name': ext_name,
                'similarity_score': sim,
                'is_automatic': bool(is_auto)
            })
        
        # Obtener aliases
        cursor.execute("""
            SELECT alias_name, priority, source
            FROM team_aliases WHERE team_uuid = ?
            ORDER BY priority DESC
        """, (team_uuid,))
        
        for alias_name, priority, source in cursor.fetchall():
            team['aliases'].append({
                'alias_name': alias_name,
                'priority': priority,
                'source': source
            })
        
        conn.close()
        return team
    
    def get_all_teams(self) -> List[Dict]:
        """Obtiene todos los equipos de la tabla maestra."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT team_uuid, official_name, country, league, created_at, updated_at
            FROM master_teams
            ORDER BY official_name
        """)
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                'team_uuid': row[0],
                'official_name': row[1],
                'country': row[2],
                'league': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        conn.close()
        return teams
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del normalizador."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM master_teams")
        total_teams = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM external_team_mappings")
        total_mappings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM team_aliases")
        total_aliases = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT source, COUNT(*) FROM external_team_mappings 
            GROUP BY source
        """)
        mappings_by_source = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT COUNT(*) FROM external_team_mappings 
            WHERE is_automatic = 1
        """)
        auto_mappings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_teams': total_teams,
            'total_mappings': total_mappings,
            'auto_mappings': auto_mappings,
            'manual_mappings': total_mappings - auto_mappings,
            'total_aliases': total_aliases,
            'mappings_by_source': mappings_by_source,
            'cache_size': len(self._cache)
        }
    
    def export_mappings(self, output_file: str = "team_mappings.json"):
        """Exporta todos los mapeos a JSON para auditoría."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        export = {
            'timestamp': datetime.utcnow().isoformat(),
            'teams': [],
            'mappings': []
        }
        
        # Exportar equipos
        cursor.execute("SELECT * FROM master_teams")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export['teams'].append(dict(zip(columns, row)))
        
        # Exportar mapeos
        cursor.execute("SELECT * FROM external_team_mappings")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export['mappings'].append(dict(zip(columns, row)))
        
        conn.close()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Mappings exported to {output_file}")
        return output_file


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TEAM NORMALIZATION SYSTEM - TEST")
    print("="*80 + "\n")
    
    # Inicializar normalizador
    normalizer = TeamNormalizer(db_path="data/databases/football_data.db")
    
    # Agregar algunos equipos de prueba
    print("1. Agregando equipos de prueba...")
    teams_data = [
        ("Manchester United FC", "England", "Premier League"),
        ("Liverpool Football Club", "England", "Premier League"),
        ("Real Madrid Club de Fútbol", "Spain", "La Liga"),
        ("FC Barcelona", "Spain", "La Liga"),
    ]
    
    team_uuids = {}
    for name, country, league in teams_data:
        uuid_val = normalizer.add_team(name, country, league)
        team_uuids[name] = uuid_val
        print(f"  ✓ {name}: {uuid_val}")
    
    # Agregar aliases
    print("\n2. Agregando aliases...")
    normalizer.add_alias(team_uuids["Manchester United FC"], "Man United", priority=10)
    normalizer.add_alias(team_uuids["Manchester United FC"], "Manchester Utd", priority=9)
    normalizer.add_alias(team_uuids["Liverpool Football Club"], "LFC", priority=10)
    normalizer.add_alias(team_uuids["Real Madrid Club de Fútbol"], "Real Madrid", priority=10)
    print("  ✓ Aliases agregados")
    
    # Agregar mapeos externos
    print("\n3. Agregando mapeos externos...")
    normalizer.add_external_mapping(
        team_uuid=team_uuids["Manchester United FC"],
        source="footballdata",
        external_id="66",
        external_name="Manchester United",
        similarity_score=100.0,
        is_automatic=False
    )
    print("  ✓ Mapeos externos agregados")
    
    # Normalizar nombres variantes
    print("\n4. Normalizando nombres con fuzzy matching...")
    test_names = [
        ("Manchester United", None, None),
        ("Man United", None, None),
        ("Manchester Utd", None, None),
        ("Liverpool", None, None),
        ("Real Madrid", None, None),
        ("Barcelona", None, None),
        ("Manchester City", "footballdata", "65"),  # No existe, debería crear
    ]
    
    for team_name, source, ext_id in test_names:
        uuid_val, similarity = normalizer.normalize_team(
            team_name, 
            source=source, 
            external_id=ext_id
        )
        status = "✓" if uuid_val else "✗"
        print(f"  {status} {team_name} → {uuid_val} (similarity: {similarity:.0f}%)")
    
    # Mostrar estadísticas
    print("\n5. Estadísticas del sistema:")
    stats = normalizer.get_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    # Mostrar información completa de un equipo
    print("\n6. Información completa de un equipo:")
    team_info = normalizer.get_team(team_uuids["Manchester United FC"])
    if team_info:
        print(f"  Equipo: {team_info['official_name']}")
        print(f"  UUID: {team_info['team_uuid']}")
        print(f"  País: {team_info['country']}")
        print(f"  Mapeos externos: {len(team_info['mappings'])}")
        print(f"  Aliases: {len(team_info['aliases'])}")
        for alias in team_info['aliases']:
            print(f"    - {alias['alias_name']} (priority: {alias['priority']})")
    
    # Exportar mapeos
    print("\n7. Exportando mapeos...")
    normalizer.export_mappings("team_mappings.json")
    print("  ✓ Mapeos exportados a team_mappings.json")
    
    print("\n" + "="*80)
    print("TEST COMPLETADO EXITOSAMENTE")
    print("="*80 + "\n")
