#!/usr/bin/env python3
"""
Integration: API-Football + ETL
================================

Módulo de integración entre API-Football v3 y el pipeline ETL existente.

Propósito:
- Enriquecer datos históricos del ETL con predicciones
- Agregar features ML de API-Football al dataset
- Mantener sincronización de datos
- Exportar features para modelo ML

Uso:
    from api_football_etl_integration import ETLFootballIntegration
    
    integration = ETLFootballIntegration("api_key", db_path="data/databases/football_data.db")
    
    # Enriquecer partidos con predicciones
    enriched = integration.enrich_match_data(match_id=123)
    
    # Exportar features ML
    features_df = integration.export_ml_features()

Autor: Backend Integration Team
Versión: 1.0.0
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import sqlite3
import json

import pandas as pd
import numpy as np

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from api_football_enricher import (
    APIFootballEnricher,
    MLFeatures,
    MatchPrediction
)

# ========== CONFIGURACIÓN ==========

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# ========== INTEGRACIÓN ==========

class ETLFootballIntegration:
    """Integra API-Football con pipeline ETL"""
    
    def __init__(self, api_key: str, db_path: str = "data/databases/football_data.db"):
        """
        Inicializa integración
        
        Args:
            api_key: API Key de API-Football
            db_path: Ruta a base de datos ETL
        """
        self.api_key = api_key
        self.db_path = db_path
        self.enricher = APIFootballEnricher(api_key)
        
        self._init_enrichment_tables()
        
        logger.info(f"Integración inicializada")
        logger.info(f"  Base de datos ETL: {db_path}")
        logger.info(f"  Caché API: data/databases/api_football_cache.db")
    
    def _init_enrichment_tables(self):
        """Inicializa tablas de enriquecimiento en DB ETL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de features ML
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_features (
                match_id INTEGER PRIMARY KEY,
                home_win_prob REAL,
                draw_prob REAL,
                away_win_prob REAL,
                over_2_5_prob REAL,
                under_2_5_prob REAL,
                xg_home REAL,
                xg_away REAL,
                xg_diff REAL,
                prediction_label TEXT,
                prediction_confidence REAL,
                last_updated DATETIME
            )
        """)
        
        # Tabla de enriquecimiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_enrichment (
                match_id INTEGER PRIMARY KEY,
                api_football_match_id INTEGER,
                has_prediction BOOLEAN,
                prediction_confidence REAL,
                features_extracted BOOLEAN,
                enriched_at DATETIME,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def enrich_match_data(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Enriquece datos de un partido con predicciones
        
        Args:
            match_id: ID del partido (API-Football)
        
        Returns:
            Datos enriquecidos del partido
        """
        logger.info(f"Enriqueciendo match {match_id}...")
        
        try:
            # Obtener predicción
            prediction = self.enricher.fetch_pre_match_predictions(match_id)
            
            if not prediction:
                logger.warning(f"No prediction available for match {match_id}")
                return None
            
            # Extraer features
            features = self.enricher.extract_ml_features(match_id, prediction)
            
            # Guardar features
            self._save_ml_features(match_id, features)
            
            # Marcar como enriquecido
            self._mark_enriched(match_id, prediction, features)
            
            enriched_data = {
                'match_id': match_id,
                'prediction': prediction,
                'features': features,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✓ Match {match_id} enriquecido")
            
            return enriched_data
        
        except Exception as e:
            logger.error(f"Error enriching match: {e}")
            return None
    
    def _save_ml_features(self, match_id: int, features: MLFeatures):
        """Guarda ML features en base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ml_features
            (match_id, home_win_prob, draw_prob, away_win_prob,
             over_2_5_prob, under_2_5_prob, xg_home, xg_away, xg_diff,
             prediction_label, prediction_confidence, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            features.match_id,
            features.home_win_prob,
            features.draw_prob,
            features.away_win_prob,
            features.over_2_5_prob,
            features.under_2_5_prob,
            features.xg_home,
            features.xg_away,
            features.xg_diff,
            features.prediction_label,
            features.prediction_confidence,
            datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def _mark_enriched(self, match_id: int, prediction: MatchPrediction,
                      features: MLFeatures):
        """Marca match como enriquecido"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO match_enrichment
            (match_id, has_prediction, prediction_confidence,
             features_extracted, enriched_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            match_id,
            True,
            features.prediction_confidence,
            True,
            datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def export_ml_features(self, output_format: str = 'csv',
                          output_file: Optional[str] = None) -> Any:
        """
        Exporta features ML para modelo
        
        Args:
            output_format: 'csv', 'json', 'parquet', 'pandas'
            output_file: Ruta de salida (opcional)
        
        Returns:
            Datos en formato especificado
        """
        logger.info(f"Exportando ML features ({output_format})...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Obtener datos
        query = """
            SELECT
                mf.*,
                CASE 
                    WHEN prediction_label = 'HOME_WIN' THEN 1
                    WHEN prediction_label = 'DRAW' THEN 0
                    WHEN prediction_label = 'AWAY_WIN' THEN -1
                END as target_encoded
            FROM ml_features mf
            ORDER BY match_id
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            logger.warning("No ML features to export")
            return None
        
        # Exportar según formato
        if output_format == 'csv':
            filename = output_file or 'data/exports/ml_features.csv'
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(filename, index=False)
            logger.info(f"✓ Exportado a {filename}")
            return filename
        
        elif output_format == 'json':
            filename = output_file or 'data/exports/ml_features.json'
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            df.to_json(filename, orient='records')
            logger.info(f"✓ Exportado a {filename}")
            return filename
        
        elif output_format == 'parquet':
            filename = output_file or 'data/exports/ml_features.parquet'
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(filename, index=False)
            logger.info(f"✓ Exportado a {filename}")
            return filename
        
        elif output_format == 'pandas':
            logger.info(f"✓ DataFrame con {len(df)} registros")
            return df
        
        else:
            raise ValueError(f"Formato no soportado: {output_format}")
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de enriquecimiento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total enriquecidos
        cursor.execute("SELECT COUNT(*) FROM match_enrichment WHERE features_extracted = 1")
        total_enriched = cursor.fetchone()[0]
        
        # Con predicción
        cursor.execute("SELECT COUNT(*) FROM match_enrichment WHERE has_prediction = 1")
        with_prediction = cursor.fetchone()[0]
        
        # Features quality
        cursor.execute("""
            SELECT
                AVG(prediction_confidence) as avg_confidence,
                MIN(prediction_confidence) as min_confidence,
                MAX(prediction_confidence) as max_confidence
            FROM ml_features
        """)
        
        quality = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_enriched': total_enriched,
            'with_prediction': with_prediction,
            'enrichment_rate': with_prediction / max(total_enriched, 1),
            'avg_confidence': quality[0] if quality[0] else 0,
            'min_confidence': quality[1] if quality[1] else 0,
            'max_confidence': quality[2] if quality[2] else 0,
        }
    
    def feature_engineering(self) -> pd.DataFrame:
        """
        Ingeniería de features para ML
        
        Crea features adicionales a partir de las probabilidades
        
        Returns:
            DataFrame con features mejorados
        """
        logger.info("Realizando ingeniería de features...")
        
        df = self.export_ml_features(output_format='pandas')
        
        if df is None or df.empty:
            return None
        
        # Feature: Certeza de predicción (max prob)
        df['max_probability'] = df[['home_win_prob', 'draw_prob', 'away_win_prob']].max(axis=1)
        
        # Feature: Entropia de predicción (incertidumbre)
        df['prediction_entropy'] = -1 * (
            df['home_win_prob'] * np.log(df['home_win_prob'] + 1e-10) +
            df['draw_prob'] * np.log(df['draw_prob'] + 1e-10) +
            df['away_win_prob'] * np.log(df['away_win_prob'] + 1e-10)
        )
        
        # Feature: Over/Under balance
        df['over_under_diff'] = np.abs(df['over_2_5_prob'] - df['under_2_5_prob'])
        
        # Feature: Expected goals ratio
        df['xg_ratio'] = df['xg_home'] / (df['xg_away'] + 1e-10)
        
        # Feature: Expected goals total
        df['xg_total'] = df['xg_home'] + df['xg_away']
        
        logger.info(f"✓ {len(df)} registros con features mejorados")
        
        return df
    
    def prepare_training_data(self, output_file: Optional[str] = None) -> pd.DataFrame:
        """
        Prepara datos para entrenamiento del modelo
        
        Returns:
            DataFrame listo para entrenamiento
        """
        logger.info("Preparando datos para entrenamiento...")
        
        # Obtener features con ingeniería
        df = self.feature_engineering()
        
        if df is None or df.empty:
            logger.warning("No data available")
            return None
        
        # Seleccionar features relevantes
        feature_cols = [
            'home_win_prob', 'draw_prob', 'away_win_prob',
            'over_2_5_prob', 'under_2_5_prob',
            'xg_home', 'xg_away', 'xg_diff',
            'max_probability', 'prediction_entropy',
            'over_under_diff', 'xg_ratio', 'xg_total',
            'prediction_confidence'
        ]
        
        target_col = 'target_encoded'
        
        # Filtrar solo filas completas
        training_df = df[feature_cols + [target_col]].dropna()
        
        logger.info(f"✓ Dataset de entrenamiento: {len(training_df)} registros")
        logger.info(f"  Features: {len(feature_cols)}")
        logger.info(f"  Distribución target:")
        
        for label, count in training_df[target_col].value_counts().items():
            pct = count / len(training_df) * 100
            label_name = {1: 'HOME_WIN', 0: 'DRAW', -1: 'AWAY_WIN'}.get(label, 'UNKNOWN')
            logger.info(f"    {label_name}: {count} ({pct:.1f}%)")
        
        # Guardar si se especifica
        if output_file:
            training_df.to_csv(output_file, index=False)
            logger.info(f"✓ Guardado en {output_file}")
        
        return training_df
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Calcula importancia de features basada en correlación
        
        Returns:
            Dict con importancia de cada feature
        """
        df = self.feature_engineering()
        
        if df is None or df.empty:
            return {}
        
        feature_cols = [
            'home_win_prob', 'draw_prob', 'away_win_prob',
            'over_2_5_prob', 'under_2_5_prob',
            'xg_home', 'xg_away', 'xg_diff',
            'max_probability', 'prediction_entropy',
            'over_under_diff', 'xg_ratio', 'xg_total'
        ]
        
        # Correlación con target
        correlations = {}
        for col in feature_cols:
            if col in df.columns:
                corr = df[col].corr(df['target_encoded'])
                correlations[col] = abs(corr)
        
        # Ordenar por importancia
        sorted_corr = dict(sorted(
            correlations.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        logger.info("Feature Importance (Correlation):")
        for feature, importance in sorted_corr.items():
            logger.info(f"  {feature:<25} {importance:.4f}")
        
        return sorted_corr


# ========== UTILIDADES ==========

def create_enrichment_summary(integration: ETLFootballIntegration) -> Dict[str, Any]:
    """Crea resumen de enriquecimiento"""
    
    stats = integration.get_enrichment_statistics()
    
    summary = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'statistics': stats,
        'status': {
            'total_enriched': stats['total_enriched'],
            'enrichment_rate': f"{stats['enrichment_rate']:.1%}",
            'avg_prediction_confidence': f"{stats['avg_confidence']:.2%}",
        }
    }
    
    return summary


if __name__ == '__main__':
    # Test
    import os
    
    api_key = os.getenv("API_FOOTBALL_KEY")
    
    if not api_key:
        print("❌ API_FOOTBALL_KEY no está configurada")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("ETL + API-FOOTBALL INTEGRATION - TEST")
    print("="*70 + "\n")
    
    integration = ETLFootballIntegration(api_key)
    
    # Estadísticas
    stats = integration.get_enrichment_statistics()
    print(f"✓ Estadísticas de enriquecimiento:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
