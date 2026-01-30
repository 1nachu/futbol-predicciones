# Centralización de Funcionalidades de API en Timba Core

## Resumen Ejecutivo

Se ha completado la refactorización para centralizar **todas las funcionalidades de API-Football v3** directamente en `timba_core.py`. Esto elimina dependencias dispersas y proporciona un único punto de acceso para todas las operaciones de cálculo y predicción.

**Fecha:** 30 de Enero de 2026  
**Estado:** ✅ COMPLETADO  
**Versión:** 2.2.0

---

## Cambios Principales

### 1. **Timba Core Extendido** (`src/timba_core.py`)

#### Nuevas Clases Integradas:

**Estructura de Datos:**
- `APIQuotaStatus` - Estado de cuota diaria de API-Football
- `MatchPrediction` - Predicción de partido con probabilidades
- `MatchFixture` - Fixture de partido desde API
- `MLFeatures` - Features para modelos de ML
- `MatchStatus` - Enum de estados de partidos
- `PredictionType` - Enum de tipos de predicción

**Gestión de Caché:**
- `APIFootballCache` - SQLite con tablas para:
  - Fixtures (match_id, equipos, fecha, status, etc.)
  - Predicciones (probabilidades, XG, confianza)
  - Logs de uso de API (endpoint, costo, tiempo)
  - Cuota diaria

**Cliente HTTP:**
- `APIFootballClient` - Cliente profesional para API-Football v3:
  - Sesiones con retry strategy (3 reintentos)
  - Verificación de cuota antes de requests
  - Logging detallado de uso
  - Thread-safe con locks

**Estrategias de Fetching:**
- `BatchFetcher` - Obtiene fixtures una sola vez al día (00:00 UTC)
- `PredictionFetcher` - Obtiene predicciones 30 min antes de partidos
- `MLFeatureExtractor` - Extrae features para modelos ML

**Orquestador Principal:**
- `TimbaCoreAPI` - Clase que encapsula todas las funcionalidades:
  - Inicialización automática con variable de ambiente
  - Métodos públicos para fetch y predicciones
  - Métodos auxiliares para cálculos históricos
  - Instancia global para fácil acceso

#### Funciones Auxiliares:

```python
# Acceso centralizado
timba_core = inicializar_timba_core()  # Inicializa con soporte de API
timba_core = obtener_timba_core()      # Obtiene instancia global

# Métodos disponibles
timba_core.fetch_daily_fixtures(league_id=39, season=2026)
timba_core.fetch_prediction(match_id)
timba_core.schedule_predictions(fixtures)
timba_core.extract_ml_features(match_id, prediction)
timba_core.get_quota_status()
timba_core.get_usage_today()
timba_core.calcular_fuerzas(df)
timba_core.predecir_partido(local, visitante, fuerzas, media_local, media_visitante)
timba_core.obtener_h2h(local, visitante, df)
timba_core.obtener_proximos_partidos(fixture_url)
```

---

### 2. **App.py Actualizado** (`src/app.py`)

**Cambios:**
- Importación centralizada: `from timba_core import inicializar_timba_core`
- Inicialización al inicio: `timba_core = inicializar_timba_core()`
- Todas las llamadas a funciones usan `timba_core.` como prefijo:
  - `timba_core.calcular_fuerzas(df)` (línea 296, 78)
  - `timba_core.predecir_partido(...)` (líneas 340, 394)
  - `timba_core.obtener_h2h(...)` (línea 846)

**Beneficios:**
- Código más limpio y legible
- Una única fuente de verdad para cálculos
- Fácil debugging y logging centralizado

---

### 3. **CLI Actualizado** (`src/cli.py`)

**Cambios:**
- Importación: `from timba_core import inicializar_timba_core`
- Inicialización: `timba_core = inicializar_timba_core()`
- Todas las llamadas con prefijo:
  - `timba_core.calcular_fuerzas(df)` (línea 135, 187)
  - `timba_core.obtener_proximos_partidos(url_fix)` (línea 141)
  - `timba_core.predecir_partido(...)` (líneas 160, 208)

**Mejoras:**
- Mismo patrón que app.py para consistencia
- Facilita testing y mantenimiento
- Acceso a cuota de API desde CLI

---

## Arquitectura de Cálculo

### Flujo de Cálculo Centralizado:

```
┌─────────────────────────────────────────────────┐
│         APP.PY / CLI.PY / OTROS MÓDULOS         │
└─────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│      TIMBA CORE API (Orquestador Principal)     │
│                                                 │
│  - Inicialización de cliente API                │
│  - Gestión de caché SQLite                      │
│  - Scheduleo de predicciones                    │
│  - Extracción de features ML                    │
│  - Logging de uso                               │
└─────────────────────────────────────────────────┘
         │                              │
         ├─→ BatchFetcher              │
         │   (fixtures diarios)        │
         │                              │
         ├─→ PredictionFetcher          │
         │   (predicciones 30min antes) │
         │                              │
         ├─→ MLFeatureExtractor         │
         │   (features para ML)        │
         │                              │
         └─→ APIFootballClient           │
             (requests autenticados)    │
                     │
                     ↓
        ┌─────────────────────────────┐
        │   API-FOOTBALL v3 (100API)  │
        │   - Fixtures                │
        │   - Predicciones            │
        │   - Status de cuota         │
        └─────────────────────────────┘
         
         Respuestas cacheadas en SQLite
```

### Cálculos Matemáticos:

1. **Fuerzas de Equipos**: `calcular_fuerzas(df)`
   - Ataque/Defensa casa y fuera
   - Ponderación 75% reciente + 25% histórico
   - Córners, tarjetas, eficiencia de tiro

2. **Predicción de Partidos**: `predecir_partido(...)`
   - Distribución Poisson para goles
   - Probabilidades 1X2, O/U, BTTS
   - Mercados de córners
   - Top 3 marcadores exactos

3. **Features ML**: `extract_ml_features(...)`
   - Probabilidades normalizadas
   - XG Difference
   - Labels de predicción
   - Confianza del modelo

---

## Ventajas de la Centralización

### 1. **Mantenibilidad**
- ✅ Un único punto de actualización para lógica de cálculo
- ✅ Fácil agregar nuevas funcionalidades
- ✅ Reducción de código duplicado

### 2. **Performance**
- ✅ Caché SQLite centralizado
- ✅ Reutilización de sesiones HTTP
- ✅ Retry strategy eficiente
- ✅ Thread-safe para concurrencia

### 3. **Testing**
- ✅ Fácil mockear `timba_core` en tests
- ✅ Métodos públicos claros
- ✅ Logging para debugging
- ✅ Uso de API controlado

### 4. **Extensibilidad**
- ✅ Agregar nuevas predicciones sin cambiar app.py/cli.py
- ✅ Integración con otros módulos simplificada
- ✅ API consistente en toda la aplicación

---

## Configuración Requerida

### Variables de Ambiente:

```bash
# API-Football v3 (requerida para predicciones)
export API_FOOTBALL_KEY="tu_clave_aqui"

# Ruta de base de datos de caché (opcional, default: data/databases/api_football_cache.db)
export API_FOOTBALL_DB_PATH="data/databases/api_football_cache.db"
```

### Logs:

```
logs/
├── timba_core_api.log          # Logs de operaciones de API
├── api_football_scheduler.log  # Logs del scheduler (si se usa)
├── api_football_enricher.log   # Logs del enricher (legacy)
└── football_api_client.log     # Logs del cliente HTTP
```

---

## Uso Práctico

### Ejemplo 1: Predicción Simple

```python
from timba_core import inicializar_timba_core, LIGAS, URLS_FIXTURE

# Inicializar
timba_core = inicializar_timba_core()

# Descargar datos
liga_id = 1  # Premier League
url = LIGAS[liga_id]['url']
df, _ = descargar_csv_safe(url)

# Calcular fuerzas
fuerzas, media_local, media_vis = timba_core.calcular_fuerzas(df)

# Predecir
prediccion = timba_core.predecir_partido(
    local="Manchester United",
    visitante="Liverpool",
    fuerzas=fuerzas,
    media_liga_local=media_local,
    media_liga_visitante=media_vis
)

print(f"Prob Local: {prediccion['Prob_Local']:.2%}")
print(f"Goles Esperados: {prediccion['Goles_Esp_Local']:.2f} - {prediccion['Goles_Esp_Vis']:.2f}")
```

### Ejemplo 2: Con Predicciones de API

```python
# Obtener fixtures de hoy
fixtures = timba_core.fetch_daily_fixtures(league_id=39, season=2026)

# Agendar predicciones (se ejecutan 30 min antes)
timba_core.schedule_predictions(fixtures)

# Obtener cuota
quota = timba_core.get_quota_status()
print(f"Cuota: {quota.requests_available}/{quota.requests_used + quota.requests_available}")

# Uso de hoy
uso_hoy = timba_core.get_usage_today()
print(f"Usado hoy: {uso_hoy} llamadas")
```

---

## Módulos Relacionados (Sin Cambios)

Los siguientes módulos permanecen sin cambios pero ahora interactúan con `timba_core`:

- `api_football_enricher.py` - Aún disponible para compatibilidad (legacy)
- `api_football_scheduler.py` - Aún disponible para compatibilidad (legacy)
- `football_api_client.py` - Aún disponible para live scores
- `live_scores.py` - Sigue funcionando de forma independiente
- `team_normalization.py` - Sigue funcionando de forma independiente
- `etl_football_data.py` - Sigue funcionando de forma independiente

**Recomendación:** Migrar gradualmente otros módulos para usar `timba_core` cuando sea práctico.

---

## Validación

✅ **Compilación:**
- `timba_core.py` - Sin errores
- `app.py` - Sin errores (actualizado correctamente)
- `cli.py` - Sin errores (actualizado correctamente)

✅ **Funcionalidades:**
- Todas las clases de API integradas ✓
- Caché SQLite operativo ✓
- Cliente HTTP con retry strategy ✓
- Batch fetcher implementado ✓
- Prediction fetcher implementado ✓
- ML feature extractor implementado ✓
- Instancia global y métodos públicos ✓

✅ **Integraciones:**
- `app.py` usa `timba_core` centralizado ✓
- `cli.py` usa `timba_core` centralizado ✓
- Imports correctos en ambos ✓
- Referencias de funciones actualizadas ✓

---

## Próximos Pasos (Opcional)

1. **Migrar otros módulos a usar `timba_core`**
   - `etl_football_data.py` puede usar `timba_core.fetch_daily_fixtures()`
   - `live_scores.py` puede usar `timba_core` para predicciones

2. **Scheduler integrado en `timba_core`**
   - Mover lógica de `api_football_scheduler.py` a `TimbaCoreAPI`
   - Agregar métodos `start_scheduler()` y `stop_scheduler()`

3. **Métricas y Monitoreo**
   - Agregar tablero de uso de API
   - Alertas cuando cuota está baja
   - Reportes de predicciones y aciertos

4. **Testing Automatizado**
   - Tests unitarios para `calcular_fuerzas()`
   - Tests de integración con API-Football
   - Mock de API para CI/CD

---

## Soporte

Para preguntas o problemas con la centralización de API:

1. Revisar logs en `logs/timba_core_api.log`
2. Verificar variable de ambiente `API_FOOTBALL_KEY`
3. Comprobar caché en `data/databases/api_football_cache.db`
4. Verificar cuota en `timba_core.get_quota_status()`

---

**Autor:** Backend Integration Team  
**Versión:** 2.2.0  
**Última Actualización:** 30 de Enero de 2026
