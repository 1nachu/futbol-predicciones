"""

ETL SCRIPT - Football Historical Data Pipeline
===============================================
Extrae datos históricos de Football-Data.co.uk, transforma y carga en base de datos.

Características:
- Descarga 10 temporadas de 3 ligas principales
- Normaliza fechas a ISO 8601
- Mantiene columnas críticas: FTR, HS/AS, HST/AST, cuotas B365
- Soporta SQLite y PostgreSQL
- Manejo robusto de errores
- Logging detallado

Autor: Data Engineering Team
Última actualización: 2025-01-30
"""

import os
import sys
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import time
from urllib.parse import urljoin

# ========== CONFIGURACIÓN DE LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('etl_football_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ========== CONFIGURACIÓN DE LIGAS Y TEMPORADAS ==========
FOOTBALL_DATA_BASE_URL = "https://www.football-data.co.uk"

LIGAS_CONFIG = {
    'E0': {
        'nombre': 'Premier League',
        'pais': 'Inglaterra',
        'codigo': 'E0',
        'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
    },
    'SP1': {
        'nombre': 'La Liga',
        'pais': 'España',
        'codigo': 'SP1',
        'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
    },
    'D1': {
        'nombre': 'Bundesliga',
        'pais': 'Alemania',
        'codigo': 'D1',
        'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
    }
}

# Columnas críticas a mantener después de la transformación
COLUMNAS_CRITICAS = [
    'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR',  # Fecha, equipos, goles, resultado
    'HS', 'AS', 'HST', 'AST',                               # Tiros y tiros al arco
    'B365H', 'B365D', 'B365A',                             # Cuotas Bet365
    'HF', 'AF', 'HR', 'AR'                                 # Faltas y tarjetas rojas
]

# Columnas de tarjetas (varían según temporada)
COLUMNAS_TARJETAS = ['HY', 'AY', 'HR', 'AR']


class FootballDataExtractor:
    """
    Clase responsable de extraer datos desde Football-Data.co.uk
    """
    
    def __init__(self, timeout: int = 30, retry_attempts: int = 3):
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Timba Predictor ETL/1.0)'
        })
    
    def descargar_csv(self, liga_codigo: str, temporada: str) -> Optional[pd.DataFrame]:
        """
        Descarga archivo CSV de una liga y temporada específica.
        
        Args:
            liga_codigo: Código de liga (E0, SP1, D1, etc)
            temporada: Formato AABB (ej: 2425 para 2024-25)
        
        Returns:
            DataFrame con los datos o None si hay error
        """
        url = f"{FOOTBALL_DATA_BASE_URL}/mmz4281/{temporada}/{liga_codigo}.csv"
        
        logger.info(f"Descargando: {LIGAS_CONFIG[liga_codigo]['nombre']} ({temporada})")
        
        for intento in range(self.retry_attempts):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                df = pd.read_csv(io.StringIO(response.text))
                logger.info(f"✓ Descargados {len(df)} registros de {liga_codigo}/{temporada}")
                return df
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en intento {intento + 1}/{self.retry_attempts} - {liga_codigo}/{temporada}")
                time.sleep(2 ** intento)  # Backoff exponencial
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 404:
                    logger.warning(f"✗ Archivo no encontrado: {liga_codigo}/{temporada}")
                    return None
                logger.error(f"Error HTTP {response.status_code}: {liga_codigo}/{temporada}")
                return None
                
            except Exception as e:
                logger.error(f"Error descargando {liga_codigo}/{temporada}: {str(e)}")
                time.sleep(2)
        
        return None
    
    def descargar_multiples_ligas(self, liga_codigos: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Descarga datos de múltiples ligas y temporadas.
        
        Args:
            liga_codigos: Lista de códigos de liga a descargar
        
        Returns:
            Diccionario con DataFrames por liga
        """
        if liga_codigos is None:
            liga_codigos = list(LIGAS_CONFIG.keys())
        
        resultados = {}
        
        for liga_codigo in liga_codigos:
            if liga_codigo not in LIGAS_CONFIG:
                logger.warning(f"Código de liga desconocido: {liga_codigo}")
                continue
            
            liga_info = LIGAS_CONFIG[liga_codigo]
            logger.info(f"\n{'='*60}")
            logger.info(f"Procesando: {liga_info['nombre']} ({liga_info['pais']})")
            logger.info(f"{'='*60}")
            
            dfs_liga = []
            
            for temporada in liga_info['temporadas']:
                df = self.descargar_csv(liga_codigo, temporada)
                if df is not None:
                    df['Temporada'] = temporada
                    dfs_liga.append(df)
                    time.sleep(1)  # Respetar rate limits
            
            if dfs_liga:
                resultados[liga_codigo] = pd.concat(dfs_liga, ignore_index=True)
                logger.info(f"✓ Total: {len(resultados[liga_codigo])} registros para {liga_info['nombre']}")
            else:
                logger.warning(f"✗ No se descargó data para {liga_info['nombre']}")
        
        return resultados


class FootballDataTransformer:
    """
    Clase responsable de transformar y normalizar datos
    """
    
    @staticmethod
    def normalizar_fechas(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza columna de fechas a formato ISO 8601.
        
        Soporta múltiples formatos de entrada:
        - DD/MM/YYYY
        - YYYY-MM-DD
        - DD-MM-YYYY
        """
        df = df.copy()
        
        try:
            # Intentar detectar automáticamente el formato
            df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True)
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            logger.info(f"✓ Fechas normalizadas a ISO 8601")
        except Exception as e:
            logger.error(f"Error normalizando fechas: {str(e)}")
            raise
        
        return df
    
    @staticmethod
    def seleccionar_columnas_criticas(df: pd.DataFrame) -> pd.DataFrame:
        """
        Selecciona solo las columnas críticas para predicción.
        Maneja variaciones según temporada.
        """
        df = df.copy()
        
        # Columnas que definitivamente existen
        columnas_base = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR',
                         'HS', 'AS', 'HST', 'AST']
        
        # Columnas opcionales (dependen de la temporada)
        columnas_opcionales = ['B365H', 'B365D', 'B365A', 'HF', 'AF', 'HR', 'AR', 'HY', 'AY']
        
        # Construir lista de columnas disponibles
        columnas_disponibles = []
        
        for col in columnas_base:
            if col in df.columns:
                columnas_disponibles.append(col)
            else:
                logger.warning(f"Columna base no encontrada: {col}")
        
        for col in columnas_opcionales:
            if col in df.columns:
                columnas_disponibles.append(col)
        
        # Agregar columna de temporada si existe
        if 'Temporada' in df.columns:
            columnas_disponibles.append('Temporada')
        
        df_subset = df[columnas_disponibles].copy()
        logger.info(f"✓ Seleccionadas {len(columnas_disponibles)} columnas críticas")
        
        return df_subset
    
    @staticmethod
    def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y valida los datos.
        - Elimina duplicados
        - Rellena valores faltantes apropiadamente
        - Valida tipos de datos
        """
        df = df.copy()
        
        registros_antes = len(df)
        
        # Eliminar duplicados basados en fecha, equipos y resultado
        df_sin_dup = df.drop_duplicates(
            subset=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG'],
            keep='first'
        )
        
        duplicados_removidos = registros_antes - len(df_sin_dup)
        if duplicados_removidos > 0:
            logger.info(f"✓ Removidos {duplicados_removidos} registros duplicados")
        
        # Validar que FTR sea válido (1, D, 2)
        df_validado = df_sin_dup[df_sin_dup['FTR'].isin(['1', 'D', '2', 1, 2])].copy()
        removidos = len(df_sin_dup) - len(df_validado)
        if removidos > 0:
            logger.warning(f"✓ Removidos {removidos} registros con FTR inválido")
        
        # Asegurar tipos de datos correctos
        columnas_numericas = ['FTHG', 'FTAG', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HR', 'AR', 'HY', 'AY']
        for col in columnas_numericas:
            if col in df_validado.columns:
                df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce')
        
        # Cuotas
        columnas_cuotas = ['B365H', 'B365D', 'B365A']
        for col in columnas_cuotas:
            if col in df_validado.columns:
                df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce')
        
        logger.info(f"✓ Validación completada: {len(df_validado)} registros finales")
        
        return df_validado
    
    @staticmethod
    def enriquecer_datos(df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriquece los datos con columnas derivadas útiles para predicción.
        """
        df = df.copy()
        
        # Total de goles
        df['Total_Goles'] = df['FTHG'] + df['FTAG']
        
        # Over/Under 2.5
        df['Over_25'] = (df['Total_Goles'] > 2.5).astype(int)
        
        # Diferencia de tiros
        if 'HS' in df.columns and 'AS' in df.columns:
            df['Diff_Tiros'] = df['HS'] - df['AS']
        
        # Efectividad de tiros (si hay datos disponibles)
        if 'HS' in df.columns and 'HST' in df.columns:
            df['HST'] = pd.to_numeric(df['HST'], errors='coerce')
            df['HS'] = pd.to_numeric(df['HS'], errors='coerce')
            df['Efectividad_Local'] = (df['HST'] / df['HS']).replace([np.inf, -np.inf], np.nan)
        
        logger.info(f"✓ Datos enriquecidos con columnas derivadas")
        
        return df
    
    @classmethod
    def transformar(cls, df_raw: pd.DataFrame, liga_codigo: str = None) -> pd.DataFrame:
        """
        Pipeline completo de transformación.
        """
        logger.info(f"Iniciando transformación...")
        
        # Paso 1: Normalizar fechas
        df = cls.normalizar_fechas(df_raw)
        
        # Paso 2: Seleccionar columnas críticas
        df = cls.seleccionar_columnas_criticas(df)
        
        # Paso 3: Limpiar datos
        df = cls.limpiar_datos(df)
        
        # Paso 4: Enriquecer datos
        df = cls.enriquecer_datos(df)
        
        # Paso 5: Ordenar por fecha
        df = df.sort_values('Date').reset_index(drop=True)
        
        logger.info(f"✓ Transformación completada")
        
        return df


class FootballDataLoader:
    """
    Clase responsable de cargar datos en base de datos.
    Soporta SQLite y PostgreSQL.
    """
    
    def __init__(self, db_type: str = 'sqlite', connection_string: str = None):
        """
        Inicializa el loader.
        
        Args:
            db_type: 'sqlite' o 'postgresql'
            connection_string: String de conexión (opcional para SQLite)
        """
        self.db_type = db_type.lower()
        
        if self.db_type == 'sqlite':
            self.connection_string = connection_string or 'sqlite:///football_data.db'
            self.engine = self._crear_engine_sqlite()
        elif self.db_type == 'postgresql':
            if not connection_string:
                raise ValueError("Se requiere connection_string para PostgreSQL")
            self.connection_string = connection_string
            self.engine = self._crear_engine_postgresql()
        else:
            raise ValueError(f"Tipo de BD no soportado: {db_type}")
        
        logger.info(f"✓ Motor de BD inicializado: {self.db_type}")
    
    def _crear_engine_sqlite(self):
        """Crea engine de SQLite"""
        try:
            import sqlalchemy
            return sqlalchemy.create_engine(self.connection_string)
        except Exception as e:
            logger.error(f"Error creando engine SQLite: {str(e)}")
            raise
    
    def _crear_engine_postgresql(self):
        """Crea engine de PostgreSQL"""
        try:
            import sqlalchemy
            return sqlalchemy.create_engine(self.connection_string)
        except Exception as e:
            logger.error(f"Error creando engine PostgreSQL: {str(e)}")
            raise
    
    def crear_tablas(self):
        """
        Crea las tablas necesarias si no existen.
        """
        logger.info("Creando esquema de base de datos...")
        
        try:
            with self.engine.connect() as conn:
                # Tabla principal de partidos
                crear_tabla_sql = f"""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    home_team VARCHAR(100) NOT NULL,
                    away_team VARCHAR(100) NOT NULL,
                    fthg INTEGER,
                    ftag INTEGER,
                    ftr VARCHAR(1),
                    hs INTEGER,
                    as_shots INTEGER,
                    hst INTEGER,
                    ast INTEGER,
                    hf INTEGER,
                    af INTEGER,
                    hr INTEGER,
                    ar INTEGER,
                    hy INTEGER,
                    ay INTEGER,
                    b365h DECIMAL(5,2),
                    b365d DECIMAL(5,2),
                    b365a DECIMAL(5,2),
                    total_goles INTEGER,
                    over_25 INTEGER,
                    diff_tiros INTEGER,
                    efectividad_local DECIMAL(5,2),
                    temporada VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, home_team, away_team)
                );
                """
                
                if self.db_type == 'sqlite':
                    conn.execute(f"DROP TABLE IF EXISTS matches")  # Para limpieza
                    conn.execute(crear_tabla_sql)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_date ON matches(date);
                        CREATE INDEX IF NOT EXISTS idx_teams ON matches(home_team, away_team);
                        CREATE INDEX IF NOT EXISTS idx_temporada ON matches(temporada);
                    """)
                
                conn.commit()
                logger.info("✓ Tablas creadas exitosamente")
                
        except Exception as e:
            logger.error(f"Error creando tablas: {str(e)}")
            raise
    
    def cargar_datos(self, df: pd.DataFrame, tabla: str = 'matches', 
                    if_exists: str = 'append', chunksize: int = 1000):
        """
        Carga DataFrame a la base de datos de forma masiva.
        
        Args:
            df: DataFrame a cargar
            tabla: Nombre de la tabla destino
            if_exists: 'fail', 'replace', 'append'
            chunksize: Tamaño de chunks para inserción
        """
        logger.info(f"Cargando {len(df)} registros en tabla '{tabla}'...")
        
        try:
            # Normalizar nombres de columnas
            df_normalizado = self._normalizar_columnas_bd(df)
            
            # Cargar en chunks
            registros_insertados = 0
            for i in range(0, len(df_normalizado), chunksize):
                chunk = df_normalizado.iloc[i:i+chunksize]
                chunk.to_sql(tabla, self.engine, if_exists=if_exists, 
                            index=False, method='multi')
                registros_insertados += len(chunk)
                if (i // chunksize + 1) % 10 == 0:
                    logger.info(f"  Progreso: {registros_insertados}/{len(df_normalizado)} registros")
            
            logger.info(f"✓ Cargados {registros_insertados} registros exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            raise
    
    def _normalizar_columnas_bd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nombres de columnas para la base de datos (snake_case).
        """
        df = df.copy()
        
        mapeo = {
            'Date': 'date',
            'HomeTeam': 'home_team',
            'AwayTeam': 'away_team',
            'FTHG': 'fthg',
            'FTAG': 'ftag',
            'FTR': 'ftr',
            'HS': 'hs',
            'AS': 'as_shots',
            'HST': 'hst',
            'AST': 'ast',
            'HF': 'hf',
            'AF': 'af',
            'HR': 'hr',
            'AR': 'ar',
            'HY': 'hy',
            'AY': 'ay',
            'B365H': 'b365h',
            'B365D': 'b365d',
            'B365A': 'b365a',
            'Total_Goles': 'total_goles',
            'Over_25': 'over_25',
            'Diff_Tiros': 'diff_tiros',
            'Efectividad_Local': 'efectividad_local',
            'Temporada': 'temporada'
        }
        
        df = df.rename(columns=mapeo)
        return df
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del dataset cargado.
        """
        try:
            with self.engine.connect() as conn:
                # Total de registros
                total = pd.read_sql(
                    "SELECT COUNT(*) as total FROM matches",
                    conn
                )
                
                # Registros por temporada
                por_temporada = pd.read_sql(
                    "SELECT temporada, COUNT(*) as registros FROM matches GROUP BY temporada ORDER BY temporada DESC",
                    conn
                )
                
                # Rango de fechas
                fechas = pd.read_sql(
                    "SELECT MIN(date) as fecha_inicio, MAX(date) as fecha_fin FROM matches",
                    conn
                )
                
                # Equipos únicos
                equipos = pd.read_sql(
                    "SELECT COUNT(DISTINCT home_team) as total_equipos FROM matches",
                    conn
                )
                
                stats = {
                    'total_registros': total['total'].values[0],
                    'temporadas': por_temporada.to_dict(orient='list'),
                    'fecha_inicio': fechas['fecha_inicio'].values[0],
                    'fecha_fin': fechas['fecha_fin'].values[0],
                    'total_equipos': equipos['total_equipos'].values[0]
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}


class FootballETLPipeline:
    """
    Orquestador principal del pipeline ETL.
    Coordina extracción, transformación y carga.
    """
    
    def __init__(self, db_type: str = 'sqlite', connection_string: str = None):
        self.extractor = FootballDataExtractor()
        self.transformer = FootballDataTransformer()
        self.loader = FootballDataLoader(db_type, connection_string)
    
    def ejecutar(self, ligas: List[str] = None, crear_tablas: bool = True):
        """
        Ejecuta el pipeline completo.
        
        Args:
            ligas: Lista de códigos de liga a procesar
            crear_tablas: Si debe crear tablas en BD
        """
        try:
            logger.info("\n" + "="*70)
            logger.info("INICIANDO PIPELINE ETL - FOOTBALL DATA")
            logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70 + "\n")
            
            # Paso 1: Crear tablas
            if crear_tablas:
                self.loader.crear_tablas()
            
            # Paso 2: Extraer datos
            logger.info("\n[FASE 1: EXTRACCIÓN]")
            datos_crudos = self.extractor.descargar_multiples_ligas(ligas)
            
            if not datos_crudos:
                logger.error("✗ No se descargó data de ninguna liga")
                return False
            
            # Paso 3: Transformar y cargar
            logger.info("\n[FASE 2: TRANSFORMACIÓN Y CARGA]")
            for liga_codigo, df_raw in datos_crudos.items():
                logger.info(f"\nProcesando: {LIGAS_CONFIG[liga_codigo]['nombre']}")
                
                # Transformar
                df_transformado = self.transformer.transformar(df_raw, liga_codigo)
                
                # Cargar
                self.loader.cargar_datos(df_transformado)
                
                logger.info(f"✓ {LIGAS_CONFIG[liga_codigo]['nombre']} completada\n")
            
            # Paso 4: Estadísticas finales
            logger.info("\n[FASE 3: VALIDACIÓN]")
            stats = self.loader.obtener_estadisticas()
            
            logger.info("\n" + "="*70)
            logger.info("ESTADÍSTICAS FINALES")
            logger.info("="*70)
            logger.info(f"Total de registros: {stats.get('total_registros', 0)}")
            logger.info(f"Total de equipos: {stats.get('total_equipos', 0)}")
            logger.info(f"Período: {stats.get('fecha_inicio', 'N/A')} a {stats.get('fecha_fin', 'N/A')}")
            logger.info(f"Temporadas: {len(stats.get('temporadas', {}).get('temporada', []))} cargadas")
            
            logger.info("\n✓ PIPELINE COMPLETADO EXITOSAMENTE\n")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"\n✗ ERROR EN PIPELINE: {str(e)}")
            return False


# ========== UTILITARIOS ==========
def obtener_resumen_bd(db_type: str = 'sqlite', connection_string: str = None) -> pd.DataFrame:
    """
    Obtiene resumen de datos cargados en BD.
    Útil para análisis exploratorio.
    """
    try:
        loader = FootballDataLoader(db_type, connection_string)
        
        with loader.engine.connect() as conn:
            df = pd.read_sql(
                """
                SELECT 
                    temporada,
                    COUNT(*) as total_matches,
                    COUNT(DISTINCT home_team) as unique_teams,
                    ROUND(AVG(fthg + ftag), 2) as avg_goles,
                    ROUND(AVG(total_goles > 2.5), 2) as pct_over_25
                FROM matches
                GROUP BY temporada
                ORDER BY temporada DESC
                """,
                conn
            )
            
            return df
            
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {str(e)}")
        return pd.DataFrame()


# ========== PUNTO DE ENTRADA ==========
if __name__ == "__main__":
    import argparse
    import io
    
    parser = argparse.ArgumentParser(
        description='ETL Pipeline para descarga de datos de football-data.co.uk'
    )
    parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgresql'],
        default='sqlite',
        help='Tipo de base de datos (default: sqlite)'
    )
    parser.add_argument(
        '--connection',
        type=str,
        default='sqlite:///football_data.db',
        help='String de conexión a BD'
    )
    parser.add_argument(
        '--ligas',
        type=str,
        default='E0,SP1,D1',
        help='Códigos de ligas separados por coma (default: E0,SP1,D1)'
    )
    parser.add_argument(
        '--skip-create-tables',
        action='store_true',
        help='No crear tablas'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Solo mostrar estadísticas (no ejecutar ETL)'
    )
    
    args = parser.parse_args()
    
    if args.stats_only:
        logger.info("Obteniendo estadísticas...")
        df_stats = obtener_resumen_bd(args.db_type, args.connection)
        print("\n" + df_stats.to_string())
    else:
        ligas_lista = args.ligas.split(',')
        
        pipeline = FootballETLPipeline(args.db_type, args.connection)
        exitoso = pipeline.ejecutar(ligas_lista, crear_tablas=not args.skip_create_tables)
        
        sys.exit(0 if exitoso else 1)
