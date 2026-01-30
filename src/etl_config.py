"""
ETL Configuration Module
========================

Módulo de configuración centralizada para el pipeline ETL.
Incluye parámetros de bases de datos, rutas, y validaciones.

Autor: Data Engineering Team
"""

import os
from pathlib import Path
from typing import Dict, Optional


# ========== DIRECTORIOS ==========
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
DB_DIR = BASE_DIR / 'data' / 'databases'

# Crear directorios si no existen
for directory in [DATA_DIR, LOGS_DIR, DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ========== CONFIGURACIÓN DE BASES DE DATOS ==========
DATABASE_CONFIG = {
    'sqlite': {
        'driver': 'sqlite',
        'path': str(DB_DIR / 'football_data.db'),
        'connection_string': f'sqlite:///{DB_DIR / "football_data.db"}',
        'description': 'SQLite local (recomendado para desarrollo)'
    },
    'postgresql': {
        'driver': 'postgresql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'football_data'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'description': 'PostgreSQL remoto (producción)',
        'connection_string': (
            f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
            f"{os.getenv('DB_PASSWORD', '')}@"
            f"{os.getenv('DB_HOST', 'localhost')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'football_data')}"
        )
    }
}


# ========== CONFIGURACIÓN DE ETL ==========
ETL_CONFIG = {
    # Ligas a descargar
    'ligas': {
        'E0': {
            'nombre': 'Premier League',
            'pais': 'Inglaterra',
            'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
        },
        'SP1': {
            'nombre': 'La Liga',
            'pais': 'España',
            'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
        },
        'D1': {
            'nombre': 'Bundesliga',
            'pais': 'Alemania',
            'temporadas': ['2425', '2324', '2223', '2122', '2021', '1920', '1819', '1718', '1617', '1516']
        }
    },
    
    # URLs
    'base_url': 'https://www.football-data.co.uk',
    'timeout': 30,
    'retry_attempts': 3,
    
    # Transformación
    'columnas_criticas': [
        'Date', 'HomeTeam', 'AwayTeam',           # Básico
        'FTHG', 'FTAG', 'FTR',                    # Resultado final
        'HS', 'AS', 'HST', 'AST',                 # Tiros
        'B365H', 'B365D', 'B365A',                # Cuotas
        'HF', 'AF', 'HR', 'AR', 'HY', 'AY'        # Faltas/tarjetas
    ],
    
    # Carga
    'batch_size': 1000,
    'if_exists': 'append'  # 'fail', 'replace', 'append'
}


# ========== VALIDACIONES ==========
def validar_configuracion() -> bool:
    """Valida que la configuración sea correcta."""
    try:
        # Verificar directorios
        assert DATA_DIR.exists(), f"Directorio data no existe: {DATA_DIR}"
        assert LOGS_DIR.exists(), f"Directorio logs no existe: {LOGS_DIR}"
        
        # Verificar DB_DIR es escribible
        test_file = DB_DIR / '.write_test'
        test_file.touch()
        test_file.unlink()
        
        return True
    except Exception as e:
        print(f"✗ Error en configuración: {e}")
        return False


def obtener_db_config(db_type: str = 'sqlite') -> Dict:
    """
    Obtiene configuración de BD según tipo.
    
    Args:
        db_type: 'sqlite' o 'postgresql'
    
    Returns:
        Diccionario con configuración
    """
    if db_type.lower() not in DATABASE_CONFIG:
        raise ValueError(f"Tipo de BD desconocido: {db_type}")
    
    return DATABASE_CONFIG[db_type.lower()]


# ========== VALIDACIÓN AL IMPORTAR ==========
if not validar_configuracion():
    raise RuntimeError("Configuración inválida")
