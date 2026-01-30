# 🚀 GUÍA RÁPIDA DE INTEGRACIÓN v2.1

## 📋 Tabla de Contenidos

1. [Qué cambió](#qué-cambió)
2. [Nuevas funcionalidades](#nuevas-funcionalidades)
3. [Estructura mejorada](#estructura-mejorada)
4. [Cómo usar](#cómo-usar)
5. [Troubleshooting](#troubleshooting)

---

## 🔄 Qué cambió

### ✨ Actualizaciones principales en v2.1

#### app.py - 733 líneas (ACTUALIZADO)
```
ANTES: 2 tabs (Predicción + Próxima Fecha)
AHORA: 4 tabs + Live Scores (si disponible)
```

**Nuevos imports:**
```python
try:
    from football_api_client import FootballDataClient
    from live_scores import LiveScoresManager
    LIVE_SCORES_AVAILABLE = True
except Exception:
    LIVE_SCORES_AVAILABLE = False
```

**Nuevas funciones:**
- `inicializar_live_scores_manager(api_key)` - Caché con @st.cache_resource
- `mostrar_panel_live_scores()` - Panel de marcadores en vivo
- `mostrar_panel_predicciones_live()` - Predicciones con datos en vivo

#### etl_football_data.py - FIXES CRÍTICOS
```python
# ✅ ARREGLADO: numpy no importado
import numpy as np  # Línea 22

# ✅ ARREGLADO: sqlalchemy con try/except
try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

# ✅ ARREGLADO: Métodos usan import global
def _crear_engine_sqlite(self):
    if sqlalchemy is None:
        raise ImportError("sqlalchemy no está instalado")
    return sqlalchemy.create_engine(...)
```

---

## ✨ Nuevas funcionalidades

### 1. Marcadores en Vivo (Live Scores)

**Ubicación:** Tab 4 en `app.py` (si Football-Data.org disponible)

**Paneles:**
```
⚽ Marcadores y Datos en Vivo
├── 📊 Marcadores en Vivo
│   └── Actualización con Football-Data.org API
└── 🔮 Predicciones en Vivo
    └── Combinación predicciones + datos reales
```

**Código de ejemplo:**
```python
from football_api_client import FootballDataClient
from live_scores import LiveScoresManager

# Inicializar
api_key = "tu_api_key_football_data_org"
client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Obtener matches en vivo
matches = manager.get_live_matches(['PL', 'CL', 'PD'])

# Procesarlos
for match in matches:
    print(f"{match['homeTeam']} vs {match['awayTeam']}")
    print(f"Score: {match['score']['fullTime']}")
```

### 2. Mejoras en obtener_proximos_partidos()

**Ubicación:** `src/timba_core.py` (función nueva)

**Cambios:**
- Manejo robusto de errores
- Timeout de 15 segundos
- Filtrado inteligente de fechas (próximos 7 días)
- Retorna estructura clara: `{'local': str, 'visitante': str, 'fecha': datetime}`

**Ejemplo:**
```python
from timba_core import obtener_proximos_partidos

url = "https://example.com/fixture.csv"
partidos = obtener_proximos_partidos(url)

for partido in partidos:
    print(f"{partido['fecha']} - {partido['local']} vs {partido['visitante']}")
```

### 3. Panel de Gestión de Equipos Mejorado

**Ubicación:** Tab 3 en `app.py`

**4 Subtabs:**
```
🎯 Gestión de Equipos
├── 🔍 Normalizar Equipo      (fuzzy matching)
├── 📊 Ver Estadísticas        (métricas del sistema)
├── 📋 Listar Equipos          (tabla con filtros)
└── ➕ Agregar Equipo          (formulario)
```

---

## 📚 Estructura mejorada

### Organización por módulos

```
CORE (Predicciones)
├── timba_core.py           ← Motor Poisson
├── app.py                  ← Web UI ✨ ACTUALIZADO
└── cli.py                  ← CLI

NORMALIZACIÓN
├── team_normalization.py   ← Fuzzy matching avanzado
└── team_normalization_cli.py

LIVE SCORES (NUEVO)
├── football_api_client.py  ← Cliente HTTP
├── live_scores.py          ← Manager de eventos
└── live_scores_cli.py      ← CLI

ETL
├── etl_football_data.py    ← Pipeline ✨ FIJO
├── etl_team_integration.py
├── etl_config.py
└── etl_cli.py

API-FOOTBALL v3
├── api_football_enricher.py
├── api_football_etl_integration.py
└── api_football_scheduler.py

UTILS
└── utils/shared.py         ← Centralizadas
```

### Punto de entrada único

**Web:**
```bash
streamlit run src/app.py
# Abre: http://localhost:8501
```

**CLI:**
```bash
python src/cli.py
# Menú interactivo con 9 opciones
```

---

## 🎯 Cómo usar

### Instalación (primero)

```bash
# Clonar/entrar al proyecto
cd "projecto timba"

# Crear venv
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# (Opcional) Para Live Scores
export FOOTBALL_DATA_API_KEY="tu_api_key"
```

### Ejecutar Web (Recomendado)

```bash
# Terminal 1
cd src
streamlit run app.py

# Se abre automáticamente en http://localhost:8501
```

**Interfaz:**
```
SIDEBAR
├── 🏆 Selecciona una Liga (dropdown)
└── ✅ X equipos cargados

MAIN (Tabs)
├── 🔮 Predicción Manual
│   ├── Elige 2 equipos
│   └── Obtén análisis completo
│
├── 🤖 Próxima Fecha Automática
│   ├── Analiza fixture completa
│   └── Exporta a Excel
│
├── 🎯 Gestión de Equipos (si enabled)
│   ├── 🔍 Normalizar
│   ├── 📊 Estadísticas
│   ├── 📋 Listar
│   └── ➕ Agregar
│
└── ⚽ Marcadores en Vivo (si API key)
    ├── 📊 Live scores
    └── 🔮 Predicciones vivo
```

### Ejecutar CLI

```bash
python src/cli.py

# Menú:
# 1. Predicciones Liga 1
# 2. Predicciones Liga 2
# ...
# 8. Predicciones Liga 9
# 99. Gestión de Equipos
#     ├── 1. Normalizar equipo
#     ├── 2. Ver estadísticas
#     ├── 3. Listar equipos
#     ├── 4. Agregar equipo
#     ├── 5. Exportar equipos
#     └── 6. Ver stats

# 0. Salir
```

### Usar como librería

```python
from src.timba_core import predecir_partido, calcular_fuerzas
from src.team_normalization import TeamNormalizer
from src.football_api_client import FootballDataClient
from src.live_scores import LiveScoresManager

# Predicción
fuerzas, media_local, media_vis, df = ...  # Obtén datos
pred = predecir_partido("River", "Boca", fuerzas, media_local, media_vis)

# Normalización
normalizer = TeamNormalizer()
result = normalizer.normalizar_nombre_equipo("Real Madrid")

# Live Scores
client = FootballDataClient("tu_api_key")
manager = LiveScoresManager(client)
matches = manager.get_live_matches(['PL'])
```

---

## 🔍 Verificación rápida

### Comprobar que todo está bien

```bash
# 1. Compilación
python -m py_compile src/app.py
python -m py_compile src/timba_core.py
python -m py_compile src/etl_football_data.py

# 2. Imports
python -c "from src.app import *; print('✅ app.py OK')"
python -c "from src.football_api_client import FootballDataClient; print('✅ live_scores OK')"

# 3. Ejecutar web
streamlit run src/app.py

# 4. Ejecutar CLI
python src/cli.py
```

---

## ⚠️ Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'football_api_client'"

**Solución:**
```python
# app.py ya maneja esto:
try:
    from football_api_client import FootballDataClient
    LIVE_SCORES_AVAILABLE = True
except Exception:
    LIVE_SCORES_AVAILABLE = False  # ← Se desactiva gracefully
```

### Problema: "numpy" o "sqlalchemy" no encontrado en etl_football_data.py

**Solución:** Ya está fijo en v2.1
```python
# Línea 22
import numpy as np

# Líneas 32-35
try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None
```

### Problema: API Key de Football-Data.org inválida

**Solución:**
```python
# En app.py, Live Scores tab:
api_key = st.text_input("API Key...", type="password")

if not api_key:
    st.info("💡 Obtén una API Key gratuita en: https://www.football-data.org/")
```

### Problema: Team Normalization deshabilitada

**Verificar:**
```python
# Línea 28-31 en app.py
try:
    from team_normalization import TeamNormalizer
    normalizer = TeamNormalizer()
    TEAM_NORMALIZATION_AVAILABLE = True
except Exception as e:
    TEAM_NORMALIZATION_AVAILABLE = False
    print(f"⚠️ Team Normalization deshabilitado: {e}")
```

---

## 📊 Verificación de Compilación

Última compilación exitosa:
```
✅ src/app.py              (733 líneas)
✅ src/timba_core.py       (514 líneas)
✅ src/etl_football_data.py (718 líneas) ← RECIÉN FIJO
✅ src/cli.py              (477 líneas)
─────────────────────────────────────────
✅ TOTAL: 2,442 líneas de código
```

---

## 📈 Próximos pasos

**Roadmap v2.2:**
- [ ] Integración completa de predicciones en vivo
- [ ] ML para detección de outliers
- [ ] Notificaciones push
- [ ] Base de datos en la nube
- [ ] API REST propia
- [ ] Versión móvil

---

## 📝 Git History

```bash
# Ver cambios recientes
git log --oneline -5

# Ver estructura
git ls-tree -r HEAD src/

# Ver cambios en app.py
git diff HEAD~1 src/app.py
```

---

**Versión:** 2.1  
**Última actualización:** 30 de enero de 2026  
**Estado:** ✅ Producción lista  
**Contacto:** Backend Integration Team
