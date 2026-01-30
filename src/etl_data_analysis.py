"""
ETL Data Analysis & Utils
==========================

Módulo con utilidades para análisis, consultas y operaciones sobre datos cargados.

Proporciona:
- Queries predefinidas comunes
- Análisis exploratorio de datos
- Funciones de validación y limpieza
- Utilidades para predicción

Autor: Data Engineering Team
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FootballDataAnalyzer:
    """
    Analizador de datos de fútbol.
    Proporciona métodos para extraer insights de la base de datos.
    """
    
    def __init__(self, engine):
        """
        Inicializa el analizador con un engine SQLAlchemy.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
    
    def obtener_estadisticas_equipo(self, equipo: str) -> Dict:
        """
        Obtiene estadísticas completas de un equipo.
        
        Args:
            equipo: Nombre del equipo
        
        Returns:
            Diccionario con estadísticas
        """
        with self.engine.connect() as conn:
            # Casa
            casa = pd.read_sql(f"""
                SELECT 
                    COUNT(*) as partidos,
                    ROUND(AVG(fthg), 2) as goles_marcados,
                    ROUND(AVG(ftag), 2) as goles_recibidos,
                    ROUND(AVG(hs), 2) as tiros_promedio,
                    ROUND(AVG(hst), 2) as tiros_arco_promedio,
                    SUM(CASE WHEN ftr = '1' THEN 1 ELSE 0 END) as victorias,
                    SUM(CASE WHEN ftr = 'D' THEN 1 ELSE 0 END) as empates,
                    SUM(CASE WHEN ftr = '2' THEN 1 ELSE 0 END) as derrotas
                FROM matches
                WHERE home_team = '{equipo}'
            """, conn)
            
            # Fuera
            fuera = pd.read_sql(f"""
                SELECT 
                    COUNT(*) as partidos,
                    ROUND(AVG(ftag), 2) as goles_marcados,
                    ROUND(AVG(fthg), 2) as goles_recibidos,
                    ROUND(AVG(as_shots), 2) as tiros_promedio,
                    ROUND(AVG(ast), 2) as tiros_arco_promedio,
                    SUM(CASE WHEN ftr = '2' THEN 1 ELSE 0 END) as victorias,
                    SUM(CASE WHEN ftr = 'D' THEN 1 ELSE 0 END) as empates,
                    SUM(CASE WHEN ftr = '1' THEN 1 ELSE 0 END) as derrotas
                FROM matches
                WHERE away_team = '{equipo}'
            """, conn)
            
            return {
                'equipo': equipo,
                'casa': casa.to_dict(orient='records')[0] if not casa.empty else {},
                'fuera': fuera.to_dict(orient='records')[0] if not fuera.empty else {}
            }
    
    def obtener_enfrentamientos_directos(self, equipo1: str, equipo2: str,
                                        limit: int = 10) -> pd.DataFrame:
        """
        Obtiene historial directo entre dos equipos.
        
        Args:
            equipo1: Primer equipo
            equipo2: Segundo equipo
            limit: Número máximo de enfrentamientos
        
        Returns:
            DataFrame con enfrentamientos
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(f"""
                SELECT 
                    date,
                    home_team,
                    away_team,
                    fthg,
                    ftag,
                    ftr,
                    hs,
                    as_shots,
                    hst,
                    ast
                FROM matches
                WHERE (
                    (home_team = '{equipo1}' AND away_team = '{equipo2}') OR
                    (home_team = '{equipo2}' AND away_team = '{equipo1}')
                )
                ORDER BY date DESC
                LIMIT {limit}
            """, conn)
            
            return df
    
    def obtener_top_equipos(self, metrica: str = 'goles_promedio',
                           limit: int = 10) -> pd.DataFrame:
        """
        Obtiene ranking de equipos por métrica.
        
        Args:
            metrica: 'goles_promedio', 'defensa', 'victorias', etc
            limit: Top N equipos
        
        Returns:
            DataFrame con ranking
        """
        metricas_disponibles = {
            'goles_promedio': """
                SELECT home_team as equipo, ROUND(AVG(fthg + ftag), 2) as valor
                FROM matches
                GROUP BY home_team
                ORDER BY valor DESC
                LIMIT {limit}
            """,
            'victorias': """
                SELECT home_team as equipo, COUNT(*) as valor
                FROM matches
                WHERE ftr = '1'
                GROUP BY home_team
                ORDER BY valor DESC
                LIMIT {limit}
            """,
            'defensa': """
                SELECT home_team as equipo, ROUND(AVG(ftag), 2) as valor
                FROM matches
                GROUP BY home_team
                ORDER BY valor ASC
                LIMIT {limit}
            """
        }
        
        if metrica not in metricas_disponibles:
            raise ValueError(f"Métrica desconocida: {metrica}")
        
        query = metricas_disponibles[metrica].format(limit=limit)
        
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
            return df
    
    def obtener_fixture_proximo(self, dias_adelante: int = 7) -> pd.DataFrame:
        """
        Obtiene próximos partidos (simulado - requiere data externa).
        
        Args:
            dias_adelante: Días a considerar adelante
        
        Returns:
            DataFrame con próximos partidos
        """
        logger.info("Nota: Este método requiere integración con API de fixtures")
        return pd.DataFrame()
    
    def calcular_probabilidades_match(self, home_team: str, away_team: str) -> Dict:
        """
        Calcula probabilidades de resultado basado en histórico.
        
        Usa método de Poisson para estimación.
        
        Args:
            home_team: Equipo local
            away_team: Equipo visitante
        
        Returns:
            Diccionario con probabilidades
        """
        from scipy.stats import poisson
        
        stats_local = self.obtener_estadisticas_equipo(home_team)
        stats_visitante = self.obtener_estadisticas_equipo(away_team)
        
        # Goles esperados (simplificado)
        goles_esp_local = stats_local['casa'].get('goles_marcados', 1.5)
        goles_esp_visitante = stats_visitante['fuera'].get('goles_marcados', 1.0)
        
        # Calcular probabilidades usando Poisson
        probs = {}
        
        for g_l in range(5):
            for g_v in range(5):
                prob = poisson.pmf(g_l, goles_esp_local) * poisson.pmf(g_v, goles_esp_visitante)
                
                if g_l > g_v:
                    probs['1'] = probs.get('1', 0) + prob
                elif g_l == g_v:
                    probs['D'] = probs.get('D', 0) + prob
                else:
                    probs['2'] = probs.get('2', 0) + prob
        
        return {
            'local': round(probs.get('1', 0), 3),
            'empate': round(probs.get('D', 0), 3),
            'visitante': round(probs.get('2', 0), 3),
            'goles_esp_local': round(goles_esp_local, 2),
            'goles_esp_visitante': round(goles_esp_visitante, 2)
        }
    
    def obtener_tendencias_mercado(self, dias: int = 30) -> Dict:
        """
        Obtiene tendencias de mercado (Over/Under, BTTS, etc).
        
        Args:
            dias: Últimos N días de datos
        
        Returns:
            Diccionario con tendencias
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(f"""
                SELECT 
                    total_goles,
                    over_25,
                    date
                FROM matches
                WHERE date >= date('now', '-{dias} days')
            """, conn)
            
            if df.empty:
                return {}
            
            tendencias = {
                'over_25_pct': round(df['over_25'].mean() * 100, 1),
                'promedio_goles': round(df['total_goles'].mean(), 2),
                'partidos_analizados': len(df)
            }
            
            return tendencias


class FootballDataExporter:
    """
    Exportador de datos a diferentes formatos.
    """
    
    @staticmethod
    def exportar_csv(df: pd.DataFrame, archivo: str):
        """Exporta DataFrame a CSV"""
        df.to_csv(archivo, index=False)
        logger.info(f"✓ Exportado a {archivo}")
    
    @staticmethod
    def exportar_excel(df: pd.DataFrame, archivo: str, sheet_name: str = 'data'):
        """Exporta DataFrame a Excel"""
        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"✓ Exportado a {archivo}")
    
    @staticmethod
    def exportar_json(df: pd.DataFrame, archivo: str):
        """Exporta DataFrame a JSON"""
        df.to_json(archivo, orient='records', date_format='iso')
        logger.info(f"✓ Exportado a {archivo}")
    
    @staticmethod
    def exportar_parquet(df: pd.DataFrame, archivo: str):
        """Exporta DataFrame a Parquet"""
        df.to_parquet(archivo, index=False)
        logger.info(f"✓ Exportado a {archivo}")


class FootballDataValidator:
    """
    Validador de datos para asegurar calidad.
    """
    
    @staticmethod
    def validar_completitud(df: pd.DataFrame, columnas_requeridas: List[str]) -> bool:
        """
        Valida que todas las columnas requeridas existan.
        
        Args:
            df: DataFrame a validar
            columnas_requeridas: Lista de columnas requeridas
        
        Returns:
            True si válido, False en contrario
        """
        faltantes = set(columnas_requeridas) - set(df.columns)
        
        if faltantes:
            logger.error(f"Columnas faltantes: {faltantes}")
            return False
        
        return True
    
    @staticmethod
    def validar_rangos(df: pd.DataFrame) -> bool:
        """
        Valida que los valores estén en rangos válidos.
        """
        validaciones = {
            'FTHG': (df['FTHG'] >= 0).all() and (df['FTHG'] <= 15).all(),
            'FTAG': (df['FTAG'] >= 0).all() and (df['FTAG'] <= 15).all(),
            'FTR': df['FTR'].isin(['1', 'D', '2']).all(),
            'B365H': (df['B365H'] > 1).all(),
            'B365D': (df['B365D'] > 1).all(),
            'B365A': (df['B365A'] > 1).all()
        }
        
        invalidos = [col for col, valido in validaciones.items() if not valido]
        
        if invalidos:
            logger.error(f"Validaciones fallidas: {invalidos}")
            return False
        
        return True
    
    @staticmethod
    def detectar_outliers(df: pd.DataFrame, columna: str, 
                         metodo: str = 'iqr') -> pd.DataFrame:
        """
        Detecta outliers en una columna.
        
        Args:
            df: DataFrame
            columna: Nombre de columna
            metodo: 'iqr' o 'zscore'
        
        Returns:
            DataFrame con outliers detectados
        """
        if metodo == 'iqr':
            Q1 = df[columna].quantile(0.25)
            Q3 = df[columna].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[columna] < Q1 - 1.5*IQR) | (df[columna] > Q3 + 1.5*IQR)]
        
        elif metodo == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df[columna]))
            outliers = df[z_scores > 3]
        
        else:
            raise ValueError(f"Método desconocido: {metodo}")
        
        return outliers


# ========== FUNCIONES UTILITARIAS ==========
def obtener_resumen_rapido(engine) -> str:
    """Obtiene resumen rápido de datos"""
    with engine.connect() as conn:
        total = pd.read_sql("SELECT COUNT(*) as total FROM matches", conn)
        equipos = pd.read_sql(
            "SELECT COUNT(DISTINCT home_team) as equipos FROM matches", conn
        )
        fecha_rango = pd.read_sql(
            "SELECT MIN(date) as inicio, MAX(date) as fin FROM matches", conn
        )
    
    resumen = f"""
    Total de registros: {total['total'].values[0]:,}
    Equipos únicos: {equipos['equipos'].values[0]:,}
    Período: {fecha_rango['inicio'].values[0]} a {fecha_rango['fin'].values[0]}
    """
    
    return resumen
