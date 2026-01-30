# API-Football v3 Integration - Guía Completa

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Estrategia de Llamadas](#estrategia-de-llamadas)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Uso Básico](#uso-básico)
7. [Batch Strategy](#batch-strategy)
8. [Predicciones](#predicciones)
9. [Extracción de Features](#extracción-de-features)
10. [Integración ETL](#integración-etl)
11. [Monitoreo de Cuota](#monitoreo-de-cuota)
12. [Ejemplos](#ejemplos)

---

## 🎯 Descripción General

Módulo de integración con **API-Football v3** para enriquecer datos con:

- **Predicciones matemáticas** de partidos
- **Probabilidades** (Home Win, Draw, Away Win)
- **Expected Goals (xG)** para ambos equipos
- **Over/Under probabilities**

**Restricción crítica:** 100 llamadas/día (Plan STARTER)

### Estrategia Optimizada

```
┌─────────────────────────────────────────────────────┐
│         OPTIMIZACIÓN DE CUOTA (100 llamadas/día)    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 00:00 UTC                                           │
│   ↓ BATCH FETCH (1 llamada)                        │
│   └─→ Obtiene fixture del día                      │
│       Agenda predicciones 30 min antes              │
│                                                     │
│ 30 min antes de cada partido                        │
│   ↓ PREDICTION FETCH (1 llamada por partido)       │
│   └─→ Obtiene predicciones                         │
│       Extrae features ML                            │
│                                                     │
│ Antes de cada llamada                               │
│   ↓ QUOTA CHECK (Gratuito)                         │
│   └─→ Verifica /status                             │
│       Detiene si se agota cuota                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌──────────────────────────────────────────────────────┐
│        APIFootballScheduler                          │
│        (Orquestación temporal)                       │
├──────────────────────────────────────────────────────┤
│  • Batch fetch @ 00:00 UTC                          │
│  • Predicciones 30 min antes                        │
│  • Verificación cuota cada 6 horas                  │
└────────────────┬─────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────────┐      ┌──────────────────┐
│APIFootball   │      │ETLIntegration    │
│Enricher      │      │                  │
└──────────────┘      └──────────────────┘
    │ │ │                 │
    │ │ └─────────┬───────┘
    │ │           ▼
    │ │      ┌─────────────┐
    │ │      │ ML Features │
    │ │      │ Extraction  │
    │ │      └─────────────┘
    │ │
    │ ├─→ BatchFetcher
    │ │   └─→ /fixtures
    │ │
    │ └─→ PredictionFetcher
    │     └─→ /predictions
    │
    └─→ APIFootballCache (SQLite)
```

---

## ⚡ Estrategia de Llamadas

### Cálculo de Cuota

```
100 llamadas/día para:
  1. Batch fixtures (00:00 UTC):          ~1 llamada
  2. Predicciones (30 min antes):         ~50-80 partidos = 50-80 llamadas
  3. Status checks (gratuito):            Sin costo
  4. Margin de seguridad:                 10-20 llamadas
  ────────────────────────────────────────────────
  Total disponible:                       95-99 llamadas
```

### Ejemplo de Distribución

```
Día de Liga (típicamente sábado Premier League):

00:00 UTC: Batch fetch
  - 1 llamada → obtiene ~10 partidos del día
  - Agenda predicciones para 30 min antes

09:30 UTC: Predicción partido 1
  - 1 llamada → Home 60%, Draw 20%, Away 20%

10:00 UTC: Predicción partido 2
  - 1 llamada → Home 40%, Draw 25%, Away 35%

... (patrón similar para todos los partidos)

18:00 UTC: Status check (gratuito)
  - Verifica cuota restante
  - Avisa si se agota

Total cuota: ~15-20 llamadas para jornada completa
Margin: 80+ llamadas disponibles para otros usos
```

---

## 🔧 Instalación

### 1. Obtener API Key

```bash
# Registrarse en https://www.api-football.com/
# Plan STARTER (gratuito):
#   - 100 llamadas/día
#   - 1 solicitud/segundo
#   - 1 año de datos históricos
```

### 2. Configurar

```bash
# Opción 1: Variable de entorno
export API_FOOTBALL_KEY="tu_clave_aqui"

# Opción 2: .env
echo "API_FOOTBALL_KEY=tu_clave_aqui" >> .env

# Opción 3: Parámetro directo
from src.api_football_enricher import APIFootballEnricher
enricher = APIFootballEnricher("tu_clave_aqui")
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt

# Dependencias específicas:
pip install requests schedule scikit-learn
```

---

## 🚀 Uso Básico

### 1. Cliente Simple

```python
from src.api_football_enricher import APIFootballEnricher

enricher = APIFootballEnricher("tu_api_key")

# Verificar cuota
quota = enricher.get_quota_status()
print(f"Disponibles: {quota.requests_available}")

# Obtener predicción
prediction = enricher.fetch_pre_match_predictions(match_id=123)
print(f"{prediction.home_team} vs {prediction.away_team}")
print(f"Home Win: {prediction.probability_home_win:.1%}")

# Extraer features ML
features = enricher.extract_ml_features(123, prediction)
print(f"XG Difference: {features.xg_diff:.2f}")
```

### 2. Con Scheduler

```python
from src.api_football_scheduler import APIFootballScheduler
import time

scheduler = APIFootballScheduler("tu_api_key")
scheduler.start()  # Inicia en background

# Registrar callbacks
def on_prediction(prediction, features):
    print(f"✓ {prediction.home_team} vs {prediction.away_team}")
    print(f"  {features.prediction_label} ({features.prediction_confidence:.0%})")

scheduler.register_prediction_callback(on_prediction)

# Dejar corriendo
time.sleep(3600)
scheduler.stop()
```

### 3. Integración ETL

```python
from src.api_football_etl_integration import ETLFootballIntegration

integration = ETLFootballIntegration("tu_api_key")

# Enriquecer partidos
enriched = integration.enrich_match_data(match_id=123)

# Estadísticas
stats = integration.get_enrichment_statistics()
print(f"Enriquecidos: {stats['total_enriched']}")

# Exportar features
features_df = integration.export_ml_features(output_format='csv')

# Preparar datos para ML
training_df = integration.prepare_training_data(
    output_file='data/training_data.csv'
)
```

---

## 📅 Batch Strategy

### Ejecución Diaria (00:00 UTC)

```python
fixtures = enricher.fetch_daily_fixtures(league_id=39, season=2026)

# Retorna:
# [
#   MatchFixture(
#       match_id=123,
#       date="2026-01-30T15:00:00Z",
#       home_team="Manchester United",
#       away_team="Liverpool",
#       ...
#   ),
#   ...
# ]
```

**Beneficios:**
- ✅ Una sola llamada al día
- ✅ Automático a las 00:00 UTC
- ✅ Agenda predicciones para el día
- ✅ Máximo 30-50 predicciones posibles

**Costo:** 1 llamada/día

---

## 📊 Predicciones

### Fetch 30 minutos antes

```python
# Automático con scheduler
scheduler.schedule_prediction_fetch(
    match_id=123,
    match_date="2026-01-30T15:00:00Z",
    home_team="Manchester United",
    away_team="Liverpool"
)

# O manual
prediction = enricher.fetch_pre_match_predictions(123)

# Datos disponibles:
# - probability_home_win: 0.65
# - probability_draw: 0.20
# - probability_away_win: 0.15
# - expected_goals_home: 1.8
# - expected_goals_away: 0.9
# - over_2_5_probability: 0.52
# - under_2_5_probability: 0.48
```

**Timing Crítico:**
- ⏰ Exactamente 30 minutos antes
- ⏰ Coordenado en UTC
- ⏰ Automático con scheduler

**Costo:** 1 llamada por predicción

---

## 🎯 Extracción de Features

### Features Disponibles

```python
features = enricher.extract_ml_features(123, prediction)

# Features primarios (de API-Football):
# - home_win_prob: Probabilidad HOME WIN (0-1)
# - draw_prob: Probabilidad DRAW (0-1)
# - away_win_prob: Probabilidad AWAY WIN (0-1)
# - xg_home: Expected Goals local (0-5)
# - xg_away: Expected Goals visitante (0-5)
# - over_2_5_prob: Over 2.5 goals
# - under_2_5_prob: Under 2.5 goals

# Features engineered (en integración):
# - max_probability: Máximo de las 3 probabilidades
# - prediction_entropy: Incertidumbre de predicción
# - xg_ratio: Ratio XG (home/away)
# - xg_total: Total expected goals
# - xg_diff: Diferencia XG (home - away)
```

### Ejemplo de Extracción

```python
features_dict = {
    'match_id': 123,
    'home_win_prob': 0.65,
    'draw_prob': 0.20,
    'away_win_prob': 0.15,
    'xg_home': 1.8,
    'xg_away': 0.9,
    'xg_diff': 0.9,  # 1.8 - 0.9
    'prediction_label': 'HOME_WIN',
    'prediction_confidence': 0.65
}
```

---

## 🔗 Integración ETL

### Flujo Completo

```python
# 1. Enriquecer partidos
enriched = integration.enrich_match_data(match_id=123)

# 2. Guardar features en DB
# → Tabla: ml_features
# → Tabla: match_enrichment

# 3. Estadísticas
stats = integration.get_enrichment_statistics()
# {
#   'total_enriched': 150,
#   'with_prediction': 140,
#   'enrichment_rate': 0.93,
#   'avg_confidence': 0.68
# }

# 4. Exportar para ML
training_df = integration.prepare_training_data(
    output_file='data/training_data.csv'
)
# Exporta:
# - 150 registros
# - 13 features (primarios + engineered)
# - Target variable (HOME_WIN=1, DRAW=0, AWAY_WIN=-1)
# - Listo para scikit-learn
```

### Feature Importance

```python
importance = integration.get_feature_importance()

# Output:
# home_win_prob:        0.8234
# away_win_prob:        0.7891
# xg_diff:              0.7123
# prediction_confidence: 0.6945
# xg_home:              0.5678
# draw_prob:            0.4321
# ...
```

---

## 🔐 Monitoreo de Cuota

### Status Check (Gratuito)

```python
quota = enricher.get_quota_status()

# Retorna:
# {
#   'requests_used': 45,
#   'requests_available': 55,
#   'requests_remaining': 55,
#   'reset_date': '2026-01-31',
#   'plan_name': 'STARTER'
# }

# Verificación
if quota.is_exhausted:
    print("❌ Cuota agotada")

if quota.requests_available < 10:
    print("⚠️  Cuota baja")
```

### Logging de Uso

```python
# Automático en:
# logs/api_football_enricher.log

# Ejemplo de log:
# 2026-01-30 15:00:00 - INFO - Cuota: 95 llamadas disponibles
# 2026-01-30 15:05:00 - INFO - /fixtures - Tiempo: 0.35s - Cuota: 94
# 2026-01-30 15:35:00 - INFO - /predictions - Tiempo: 0.22s - Cuota: 93
```

### Alertas de Cuota

```python
scheduler.register_quota_warning_callback(
    lambda quota: print(f"⚠️  {quota.requests_available} llamadas restantes")
)
```

---

## 📝 Ejemplos

### Ejemplo 1: Batch Diario

```python
from src.api_football_scheduler import APIFootballScheduler

scheduler = APIFootballScheduler("tu_api_key")

def on_batch_complete(fixtures):
    print(f"✓ {len(fixtures)} fixtures del día")
    for f in fixtures:
        print(f"  {f.home_team} vs {f.away_team} @ {f.date}")

scheduler.register_batch_callback(on_batch_complete)
scheduler.start()
```

### Ejemplo 2: Predicciones en Vivo

```python
scheduler.register_prediction_callback(
    lambda pred, features: print(
        f"{pred.home_team} vs {pred.away_team}: "
        f"{features.prediction_label} ({features.prediction_confidence:.0%})"
    )
)
```

### Ejemplo 3: Exportar Training Data

```python
integration = ETLFootballIntegration("tu_api_key")

# Preparar datos
training_df = integration.prepare_training_data(
    output_file='data/ml_training_set.csv'
)

# Estadísticas
print(f"Registros: {len(training_df)}")
print(f"Features: {len(training_df.columns) - 1}")
print(f"Target distribution:")
print(training_df['target_encoded'].value_counts(normalize=True))

# Usar con scikit-learn
from sklearn.model_selection import train_test_split

X = training_df.drop('target_encoded', axis=1)
y = training_df['target_encoded']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

---

## 🛡️ Protección contra Errores

### Quota Exceeded

```python
try:
    prediction = enricher.fetch_pre_match_predictions(123)
except Exception as e:
    if "Cuota" in str(e):
        print("⚠️  Cuota agotada para hoy")
        # Usar caché
        cached = enricher.client.cache.get_prediction(123)
```

### Rate Limit

```python
# Automático entre requests
time.sleep(1)  # 1 segundo mínimo entre calls
```

---

## 📊 Estructura de Base de Datos

### Tabla: ml_features

```sql
CREATE TABLE ml_features (
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
```

### Tabla: match_enrichment

```sql
CREATE TABLE match_enrichment (
    match_id INTEGER PRIMARY KEY,
    has_prediction BOOLEAN,
    prediction_confidence REAL,
    features_extracted BOOLEAN,
    enriched_at DATETIME
)
```

---

## ✅ Checklist de Implementación

- [x] Cliente API-Football con rate limiting
- [x] Batch strategy (00:00 UTC)
- [x] Predicciones (30 min antes)
- [x] Quota protection
- [x] Feature extraction para ML
- [x] Scheduler automático
- [x] Integración ETL
- [x] Caché de predicciones
- [x] Logging detallado
- [x] Documentación

---

## 🚀 Próximos Pasos

1. **Configurar API Key**
   ```bash
   export API_FOOTBALL_KEY="tu_clave"
   ```

2. **Validar conexión**
   ```bash
   python3 src/api_football_enricher.py
   ```

3. **Iniciar scheduler**
   ```bash
   python3 src/api_football_scheduler.py
   ```

4. **Enriquecer datos**
   ```python
   from src.api_football_etl_integration import ETLFootballIntegration
   integration = ETLFootballIntegration("tu_api_key")
   training_df = integration.prepare_training_data()
   ```

---

**Versión:** 1.0.0  
**Última actualización:** 30 de Enero 2026  
**Autor:** Backend Integration Team
