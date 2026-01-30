# 📊 Estructura Completa del Proyecto Timba Predictor v2.1

## 🎯 Visión General

**Timba Predictor** es un sistema completo de análisis y predicción de partidos de fútbol que integra:
- Predicciones matemáticas basadas en Poisson
- Normalización inteligente de nombres de equipos
- Marcadores en vivo en tiempo real
- Análisis ETL de datos históricos
- Interfaz CLI y web (Streamlit)

---

## 📁 Estructura de Directorios

```
projecto timba/
│
├── 📚 DOCUMENTACIÓN
│   ├── README.md                          # Guía principal del proyecto
│   ├── PROJECT_STRUCTURE.md              # Este archivo (estructura completa)
│   ├── ESTRUCTURA.md                      # Descripción de archivos legacy
│   ├── QUICK_REFERENCE.md                # Referencia rápida de funciones
│   ├── RESUMEN_EJECUTIVO.md              # Resumen ejecutivo del sistema
│   ├── SISTEMA_COMPLETO.md               # Descripción integral
│   ├── v2.1_RELEASE_NOTES.md             # Notas de versión
│   ├── ETL_QUICKSTART.md                 # Guía rápida ETL
│   ├── README_LIVE_SCORES.md             # Documentación Live Scores
│   └── docs/                             # Carpeta de documentación adicional
│       ├── CAMBIOS_CORNERS.md
│       ├── COMPARACION_ANTES_DESPUES.md
│       ├── EXPANSION_SUDAMERICANA.md
│       └── ...
│
├── 🐍 CÓDIGO FUENTE (src/)
│   ├── MÓDULO CORE - Predicciones
│   │   ├── timba_core.py                 # Motor de predicciones (Poisson)
│   │   ├── app.py                        # Interfaz web Streamlit ✨ ACTUALIZADO
│   │   └── cli.py                        # Interfaz CLI con 6 funciones team
│   │
│   ├── MÓDULO NORMALIZACIÓN DE EQUIPOS
│   │   ├── team_normalization.py         # Motor fuzzy matching (765 líneas)
│   │   └── team_normalization_cli.py     # CLI para team normalization
│   │
│   ├── MÓDULO LIVE SCORES
│   │   ├── football_api_client.py        # Cliente HTTP Football-Data.org
│   │   ├── live_scores.py                # Manager de live scores (576 líneas)
│   │   └── live_scores_cli.py            # CLI para live scores (422 líneas)
│   │
│   ├── MÓDULO ETL (Extracción-Transformación-Carga)
│   │   ├── etl_football_data.py          # Pipeline ETL (718 líneas) ✨ FIJO
│   │   ├── etl_team_integration.py       # Integración team normalization
│   │   ├── etl_cli.py                    # CLI para ETL
│   │   ├── etl_config.py                 # Configuración ETL
│   │   └── etl_data_analysis.py          # Análisis de datos
│   │
│   ├── MÓDULO API-FOOTBALL v3
│   │   ├── api_football_client.py        # Cliente API-Football v3
│   │   ├── api_football_enricher.py      # Enriquecedor de datos (832 líneas)
│   │   ├── api_football_etl_integration.py # Integración ETL
│   │   └── api_football_scheduler.py     # Scheduler de tareas
│   │
│   ├── 🔧 UTILIDADES COMPARTIDAS
│   │   └── utils/
│   │       ├── shared.py                 # Funciones centralizadas
│   │       └── __init__.py
│   │
│   └── __pycache__/                      # Archivos compilados Python
│
├── ⚙️ CONFIGURACIÓN
│   └── config/
│       └── requirements.txt              # Dependencias de config
│
├── 💾 DATOS
│   └── data/
│       ├── databases/
│       │   ├── football_data.db          # BD SQLite históricos
│       │   └── api_football_cache.db     # Caché API-Football
│       └── fixtures/                     # Datos de fixtures
│
├── 📊 SCRIPTS
│   ├── install_dependencies.sh           # Script instalación
│   ├── push_to_github.sh                 # Script git push
│   ├── run_streamlit.py                  # Launcher Streamlit
│   └── setup_etl.py                      # Setup de ETL
│
├── 🧪 TESTS
│   ├── test_corners.py
│   ├── test_semaforo.py
│   └── test_sudamerica.py
│
├── 📝 LOGS
│   ├── STATUS.txt                        # Estado del sistema
│   └── PUSH_GITHUB_LOG.txt               # Log de pushes
│
├── 🎯 ROOT FILES (Archivos principales)
│   ├── requirements.txt                  # Dependencias principales
│   ├── README.md                         # Guía de uso
│   ├── utils.sh                          # Utilidades shell
│   ├── examples.py                       # Ejemplos de uso
│   ├── examples_live_scores.py           # Ejemplos live scores
│   ├── examples_team_normalization.py    # Ejemplos team normalization
│   ├── ENTREGA_FINAL.py                  # Script entrega final
│   ├── LIVE_SCORES_DELIVERY.py           # Entrega live scores
│   ├── ETL_INDEX.py                      # Índice ETL
│   └── RESUMEN_ETL.md                    # Resumen ETL
│
└── 📦 VERSIONAMIENTO
    └── .git/                             # Repositorio git
        └── .gitignore

```

---

## 🔑 Módulos Principales

### 1️⃣ CORE: Predicción de Partidos

**Archivo:** `src/timba_core.py` (514 líneas)

**Funciones clave:**
- `calcular_fuerzas(df)` - Calcula índices de ataque/defensa
- `predecir_partido(local, visitante, fuerzas, ...)` - Predicción Poisson
- `obtener_h2h(local, visitante, df)` - Historial directo
- `obtener_proximos_partidos(url_fixture)` - Próximos partidos ✨ NUEVO
- `emparejar_equipo()` - Fuzzy matching básico
- `descargar_csv_safe()` - Descarga robusta de datos

**Tecnología:** Poisson, scipy, pandas

---

### 2️⃣ NORMALIZACIÓN DE EQUIPOS

**Archivos:**
- `src/team_normalization.py` (765 líneas)
- `src/team_normalization_cli.py` (388 líneas)

**Características:**
- Fuzzy matching avanzado con token-set ratio
- Tabla maestra centralizada de equipos (SQLite)
- Mapeos automáticos a múltiples fuentes
- UUID único por equipo
- Aliases inteligentes

**Tecnología:** thefuzz, python-Levenshtein, SQLAlchemy

---

### 3️⃣ MARCADORES EN VIVO

**Archivos:**
- `src/football_api_client.py` (1200+ líneas)
- `src/live_scores.py` (576 líneas)
- `src/live_scores_cli.py` (422 líneas)

**Características:**
- Cliente HTTP con rate limiting Leaky Bucket
- Reintentos automáticos con backoff exponencial
- Caching inteligente (TTL configurable)
- Detección de eventos en tiempo real
- State machine para seguimiento de partidos
- Webhooks/callbacks personalizables

**Tecnología:** requests, Football-Data.org API

---

### 4️⃣ PIPELINE ETL

**Archivos:**
- `src/etl_football_data.py` (718 líneas) ✨ RECIÉN FIJO
- `src/etl_team_integration.py` (489 líneas)
- `src/etl_config.py` - Configuración
- `src/etl_cli.py` - CLI

**Características:**
- Descarga de datos históricos
- Normalización de esquemas
- Cálculo de estadísticas
- Persistencia en SQLite
- Validación de datos
- Logging completo

**Tecnología:** pandas, numpy, SQLAlchemy

---

### 5️⃣ API-FOOTBALL v3 (Enriquecimiento)

**Archivos:**
- `src/api_football_enricher.py` (832 líneas)
- `src/api_football_etl_integration.py`
- `src/api_football_scheduler.py`

**Características:**
- Batch strategy: 1 llamada/día a las 00:00 UTC
- Predicciones pre-match (30 min antes)
- Quota protection
- Feature extraction para ML
- Límite: 100 llamadas/día (Plan STARTER)

**Tecnología:** API-Football v3

---

### 6️⃣ INTERFACES DE USUARIO

#### 🌐 Web (Streamlit)
**Archivo:** `src/app.py` (733 líneas) ✨ ACTUALIZADO

**Tabs principales:**
1. **🔮 Predicción Manual** - Análisis 1v1
2. **🤖 Próxima Fecha Automática** - Análisis de fixture con exportación Excel
3. **🎯 Gestión de Equipos** (si disponible)
   - 🔍 Normalizar Equipo
   - 📊 Ver Estadísticas
   - 📋 Listar Equipos
   - ➕ Agregar Equipo
4. **⚽ Marcadores en Vivo** (si disponible) ✨ NUEVO
   - 📊 Marcadores en Vivo
   - 🔮 Predicciones en Vivo

**Características:**
- Caching automático de datos
- Exportación a Excel
- Gráficos interactivos
- Semáforo visual de recomendaciones
- Soporte para 9 ligas

#### 🖥️ CLI (Click)
**Archivo:** `src/cli.py` (477 líneas)

**Opciones principales:**
- Opción 1-8: Predicciones por liga
- **Opción 99: Gestión de Equipos** (6 funciones)
  1. Normalizar equipo
  2. Ver estadísticas
  3. Listar equipos
  4. Agregar equipo
  5. Exportar equipos
  6. Ver estadísticas

---

## 📊 Estadísticas del Código

| Módulo | Líneas | Estado |
|--------|--------|--------|
| timba_core.py | 514 | ✅ Operativo |
| team_normalization.py | 765 | ✅ Operativo |
| live_scores.py | 576 | ✅ Operativo |
| football_api_client.py | 1200+ | ✅ Operativo |
| api_football_enricher.py | 832 | ✅ Operativo |
| etl_football_data.py | 718 | ✅ RECIÉN FIJO |
| etl_team_integration.py | 489 | ✅ Operativo |
| app.py | 733 | ✅ ACTUALIZADO |
| cli.py | 477 | ✅ Operativo |
| **TOTAL PRODUCCIÓN** | **2,442** | **✨ LISTO** |

---

## 🎯 Flujo de Datos

```
                    ┌─────────────────────────┐
                    │   FUENTES DE DATOS      │
                    └────────┬────────────────┘
                             │
                ┌────────────┼────────────────┐
                │            │                │
         ┌──────▼─────┐ ┌───▼──────┐ ┌──────▼──────┐
         │  CSV HTTP  │ │  SQLite  │ │  API-Football│
         │  (Fixture) │ │(Histórico)│ │   (en vivo) │
         └──────┬─────┘ └───┬──────┘ └──────┬──────┘
                │            │                │
                └────────────┼────────────────┘
                             │
                    ┌────────▼──────────┐
                    │   ETL Pipeline    │
                    │ - Normalización   │
                    │ - Validación      │
                    │ - Transformación  │
                    └────────┬──────────┘
                             │
                ┌────────────┼────────────────┐
                │            │                │
         ┌──────▼──────┐ ┌───▼──────┐ ┌──────▼──────┐
         │    timba    │ │ team_norm│ │ live_scores │
         │   _core     │ │alization │ │             │
         └──────┬──────┘ └───┬──────┘ └──────┬──────┘
                │            │                │
                └────────────┼────────────────┘
                             │
                    ┌────────▼──────────┐
                    │  Predicciones     │
                    │  - Probabilidades │
                    │  - xG             │
                    │  - Mercados       │
                    └────────┬──────────┘
                             │
                ┌────────────┼────────────────┐
                │            │                │
         ┌──────▼──────┐ ┌───▼──────┐ ┌──────▼──────┐
         │    Web      │ │   CLI    │ │   Reports  │
         │  (Streamlit)│ │  (Click) │ │ (Excel/JSON)│
         └─────────────┘ └──────────┘ └────────────┘

```

---

## 🔧 Dependencias Principales

### Requeridas
```txt
streamlit>=1.28.0          # Web UI
pandas>=2.0.0              # Data processing
numpy>=1.24.0              # Numerical computing
scipy>=1.10.0              # Statistical distributions
requests>=2.31.0           # HTTP client
thefuzz>=0.19.0            # Fuzzy matching
python-Levenshtein>=0.21.0 # String similarity
click>=8.1.0               # CLI framework
sqlalchemy>=2.0.0          # ORM (optional)
openpyxl>=3.1.0            # Excel export
tabulate>=0.9.0            # Table formatting
```

### Opcionales
```txt
sqlalchemy>=2.0.0          # Para base de datos avanzada
python-dotenv>=1.0.0       # Variables de entorno
```

---

## 🚀 Cómo Usar

### Instalación
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Ejecutar Web (Streamlit)
```bash
streamlit run src/app.py
```

### Ejecutar CLI
```bash
python src/cli.py
```

### Usar Live Scores
```python
from src.football_api_client import FootballDataClient
from src.live_scores import LiveScoresManager

api_key = "tu_api_key"
client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Obtener partidos en vivo
matches = manager.get_live_matches(['PL', 'CL'])
```

---

## ✅ Estado del Proyecto

| Componente | Estado | Fecha |
|------------|--------|-------|
| Core Predicción | ✅ Operativo | v1.0 |
| Team Normalization | ✅ Operativo | v2.0 |
| Live Scores | ✅ Operativo | v2.1 |
| ETL Pipeline | ✅ FIJO (imports) | v2.1 |
| Web Interface | ✅ ACTUALIZADO | v2.1 |
| CLI | ✅ Operativo | v2.1 |
| API-Football | ✅ Operativo | v2.1 |

---

## 📝 Cambios Recientes (v2.1)

### ✨ Nuevas Características
- Panel de marcadores en vivo en app.py
- Función `obtener_proximos_partidos()` mejorada
- 4 subtabs en Gestión de Equipos
- Integración live scores en web UI

### 🔧 Fixes
- ✅ Imports en etl_football_data.py (numpy, sqlalchemy)
- ✅ Estructura de app.py (indentación, funciones)
- ✅ Compatibilidad total con versión anterior

### 📚 Documentación
- PROJECT_STRUCTURE.md (este archivo)
- QUICK_REFERENCE.md actualizada
- Ejemplos de live scores añadidos

---

## 🎓 Recursos Adicionales

- **Football-Data.org**: https://www.football-data.org/
- **API-Football v3**: https://www.api-football.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **Click CLI**: https://click.palletsprojects.com/
- **Poisson Distribution**: https://en.wikipedia.org/wiki/Poisson_distribution

---

**Versión:** 2.1  
**Última actualización:** 30 de enero de 2026  
**Estado:** ✅ Producción  
**Líneas de código:** 2,442 (core)
