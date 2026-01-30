# 🔴 ETL Football Data - Quick Start

## TL;DR - Empezar en 5 minutos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar ETL (descargar y cargar datos)
cd src
python etl_cli.py run

# 3. Ver estadísticas
python etl_cli.py stats

# ✅ Listo! Database en data/databases/football_data.db
```

---

## 📊 ¿Qué hace el ETL?

```
Football-Data.co.uk
    ↓ (Descarga 30 archivos CSV)
Extracción (3 ligas × 10 temporadas)
    ↓ (Normaliza, limpia, enriquece)
Transformación (5000+ registros)
    ↓ (Inserta en BD)
Carga (SQLite/PostgreSQL)
    ↓
Database Listo para Predicción ✅
```

---

## 🎯 Características

✅ **Descarga automática** desde Football-Data.co.uk
✅ **10 temporadas** de histórico
✅ **3 ligas** (Premier League, La Liga, Bundesliga)
✅ **Columnas críticas** para predicción
✅ **Normalización ISO 8601**
✅ **Validación** automática
✅ **SQLite/PostgreSQL**
✅ **Análisis integrado**
✅ **Exportación múltiple** (Excel, CSV, Parquet)

---

## 🚀 Comandos Principales

### Run ETL

```bash
python etl_cli.py run
```

Opciones:
```bash
# Ligas específicas
python etl_cli.py run --ligas E0,SP1

# PostgreSQL
python etl_cli.py run --db-type postgresql \
  --connection "postgresql://user:pass@localhost/football"

# Sin reinicializar tablas
python etl_cli.py run --skip-create-tables
```

### Estadísticas

```bash
python etl_cli.py stats
```

Output:
```
temporada  total_matches  unique_teams  avg_goles  pct_over_25
2425       380            20            2.45       52.1
2324       380            20            2.38       50.8
...
```

### Validación

```bash
python etl_cli.py validate
```

Verifica:
- ✓ Total de registros
- ✓ Valores NULL
- ✓ Duplicados
- ✓ FTR válidos

### Exportar

```bash
python etl_cli.py export --output datos.xlsx
```

Formatos soportados:
- Excel (.xlsx)
- CSV (.csv)
- JSON (.json)
- Parquet (.parquet)

---

## 📚 Ejemplos de Python

### Obtener estadísticas de equipo

```python
from src.etl_data_analysis import FootballDataAnalyzer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

stats = analyzer.obtener_estadisticas_equipo('Liverpool')
print(stats)
```

### Predecir resultado

```python
probs = analyzer.calcular_probabilidades_match('Liverpool', 'Manchester City')
print(f"Liverpool gana: {probs['local']:.1%}")
print(f"Empate: {probs['empate']:.1%}")
print(f"City gana: {probs['visitante']:.1%}")
```

### Historial directo (H2H)

```python
h2h = analyzer.obtener_enfrentamientos_directos('Liverpool', 'Manchester United')
print(h2h)
```

### Top equipos

```python
top = analyzer.obtener_top_equipos('goles_promedio', limit=10)
print(top)
```

---

## 🗄️ Base de Datos

### SQLite (Default)

```
data/databases/football_data.db
```

Auto-creada, sin configuración necesaria.

### PostgreSQL (Producción)

```bash
# Instalar PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Crear base de datos
createdb football_data

# Ejecutar ETL
python etl_cli.py run --db-type postgresql \
  --connection "postgresql://postgres@localhost/football_data"
```

---

## 📋 Columnas de Base de Datos

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `date` | DATE | Fecha (ISO 8601) |
| `home_team` / `away_team` | VARCHAR | Equipos |
| `fthg` / `ftag` | INTEGER | Goles finales |
| `ftr` | VARCHAR | Resultado (1/D/2) |
| `hs` / `as_shots` | INTEGER | Tiros |
| `hst` / `ast` | INTEGER | Tiros al arco |
| `b365h` / `b365d` / `b365a` | DECIMAL | Cuotas Bet365 |
| `total_goles` | INTEGER | Suma goles |
| `over_25` | INTEGER | Flag Over 2.5 |

---

## 🔍 Troubleshooting

### "Connection refused (PostgreSQL)"

```bash
# Verificar que PostgreSQL esté corriendo
psql -U postgres -d football_data

# O usar SQLite (default)
python etl_cli.py run
```

### "Timeout en descarga"

Reintentar automáticamente con backoff exponencial. Si persiste:

```bash
# Aumentar timeout
python etl_cli.py run --timeout 60
```

### "Database locked (SQLite)"

Esperar a que se libere la BD, o usar PostgreSQL para parallelismo.

---

## 📦 Instalación Paso a Paso

### 1. Clonar/Descargar

```bash
cd proyectotimba
```

### 2. Crear ambiente virtual (opcional pero recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar ETL

```bash
cd src
python etl_cli.py run
```

### 5. Verificar

```bash
python etl_cli.py stats
```

---

## 🎓 Casos de Uso

### 1️⃣ Dataset para Machine Learning

```python
# Exportar datos limpios
python etl_cli.py export --output training_data.parquet

# En Python
import pandas as pd
df = pd.read_parquet('training_data.parquet')
```

### 2️⃣ Dashboard en Streamlit

```python
# En src/app.py
from src.etl_data_analysis import FootballDataAnalyzer

analyzer = FootballDataAnalyzer(engine)
st.write(analyzer.obtener_estadisticas_equipo(equipo_seleccionado))
```

### 3️⃣ Análisis Exploratorio

```python
python examples.py analizar_equipo "Manchester City"
python examples.py predecir "Liverpool" "Manchester United"
python examples.py top_equipos
```

---

## 📊 Datos Descargados

### Por Temporada
- **2024-25** a **2015-16**
- 10 temporadas totales

### Por Liga
1. **Premier League** (E0) - 380 partidos/temporada
2. **La Liga** (SP1) - 380 partidos/temporada
3. **Bundesliga** (D1) - 306 partidos/temporada

### Total
- **~10,500+ partidos**
- **~300 equipos únicos**
- **20 años de histórico**

---

## 🔐 Variables de Entorno

Para PostgreSQL, crear `.env`:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_NAME=football_data
```

---

## 📝 Logs

Ver logs en: `logs/etl_football_data.log`

```
2025-01-30 14:30:00 - INFO - Descargando Premier League (2425)...
2025-01-30 14:30:05 - INFO - ✓ 380 registros descargados
2025-01-30 14:30:06 - INFO - ✓ Transformación completada
2025-01-30 14:30:08 - INFO - ✓ Datos cargados en BD
```

---

## 🤝 Integración con Timba Predictor

El ETL proporciona datos para el sistema de predicción:

```python
# En src/app.py o src/timba_core.py
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('sqlite:///football_data.db')

# Cargar datos históricos
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM matches", conn)

# Usar para entrenar/predecir
```

---

## ✅ Checklist

- [ ] Instalar `pip install -r requirements.txt`
- [ ] Ejecutar `python etl_cli.py run`
- [ ] Verificar con `python etl_cli.py stats`
- [ ] Ver logs en `logs/etl_football_data.log`
- [ ] Explorar data en `data/databases/football_data.db`
- [ ] Ejecutar ejemplos en `examples.py`

---

## 📞 Más Información

- 📖 Guía completa: [ETL_FOOTBALL_DATA_GUIDE.md](../docs/ETL_FOOTBALL_DATA_GUIDE.md)
- 🎯 Ejemplos: [examples.py](../examples.py)
- 📊 Sistema completo: [SISTEMA_COMPLETO.md](../docs/SISTEMA_COMPLETO.md)

---

**Estado:** ✅ Listo para Producción
**Versión:** 1.0.0
**Última actualización:** 30 de Enero de 2025
