# 🎯 REFERENCIA RÁPIDA - COMANDOS ETL

## Instalación (una sola vez)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Validar setup
python setup_etl.py
```

---

## Ejecución Rápida

### Opción 1: CLI (Recomendado)

```bash
cd src

# Descargar datos (10 temporadas)
python etl_cli.py run

# Ver resultado
python etl_cli.py stats

# Validar integridad
python etl_cli.py validate

# Exportar a Excel
python etl_cli.py export --output datos.xlsx
```

### Opción 2: Python Directo

```python
from src.etl_football_data import FootballETLPipeline

pipeline = FootballETLPipeline()
pipeline.ejecutar(['E0', 'SP1', 'D1'])
```

### Opción 3: Ejemplos Prácticos

```bash
python examples.py descargar_datos                          # Descarga todo
python examples.py analizar_equipo "Manchester City"        # Stats de equipo
python examples.py h2h "Liverpool" "Manchester United"      # Historial
python examples.py predecir "Liverpool" "Chelsea"           # Predicción
python examples.py top_equipos                              # Rankings
python examples.py tendencias                               # Análisis
python examples.py exportar                                 # Exportar datos
python examples.py validar                                  # Validar
```

---

## Análisis de Datos

```python
from src.etl_data_analysis import FootballDataAnalyzer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

# Estadísticas de equipo
stats = analyzer.obtener_estadisticas_equipo('Liverpool')

# Historial directo
h2h = analyzer.obtener_enfrentamientos_directos('Liverpool', 'Manchester United')

# Probabilidades
probs = analyzer.calcular_probabilidades_match('Liverpool', 'Chelsea')

# Rankings
top = analyzer.obtener_top_equipos('goles_promedio', limit=10)

# Tendencias
tendencias = analyzer.obtener_tendencias_mercado(dias=30)
```

---

## Base de Datos

### Ubicación

```
data/databases/football_data.db    (SQLite)
PostgreSQL: postgresql://user:pass@host/football_data
```

### Tabla Principal

```sql
SELECT * FROM matches;      -- Todos los partidos
SELECT COUNT(*) FROM matches;      -- Total de registros
SELECT DISTINCT home_team FROM matches;   -- Equipos únicos
SELECT * FROM matches WHERE home_team = 'Liverpool';  -- Partidos de Liverpool
```

---

## Exportación

```bash
cd src

# Excel (con gráficos)
python etl_cli.py export --output reporte.xlsx

# CSV
python etl_cli.py export --output datos.csv

# JSON
python etl_cli.py export --output datos.json

# Parquet (comprimido, para ML)
python etl_cli.py export --output datos.parquet
```

---

## Configuración

### SQLite (Default)

```bash
# Automático, sin configuración
python etl_cli.py run
# BD creada en: data/databases/football_data.db
```

### PostgreSQL

```bash
# Instalar (macOS)
brew install postgresql
createdb football_data

# Ejecutar
python etl_cli.py run --db-type postgresql \
  --connection "postgresql://postgres@localhost/football_data"
```

---

## Troubleshooting

### Problema: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
python setup_etl.py
```

### Problema: "Timeout en descarga"

```bash
# Reintentar (incluye backoff automático)
python etl_cli.py run
```

### Problema: "Database locked (SQLite)"

```bash
# Esperar o usar PostgreSQL
# Para PostgreSQL:
python etl_cli.py run --db-type postgresql
```

### Problema: "No hay datos en BD"

```bash
# Verificar conexión
python etl_cli.py stats

# Si vacío, ejecutar:
python etl_cli.py run
```

---

## Integración con Streamlit

```python
# En src/app.py
from src.etl_data_analysis import FootballDataAnalyzer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

# Usar en Streamlit
equipo = st.selectbox('Selecciona equipo', 
                      ['Liverpool', 'Manchester City', ...])
stats = analyzer.obtener_estadisticas_equipo(equipo)
st.write(stats)
```

---

## Integración con ML

```python
# Exportar para entrenar
python etl_cli.py export --output training_data.parquet

# En Python
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_parquet('training_data.parquet')

# Preparar
X = df[['hs', 'hst', 'as_shots', 'ast', 'b365h', 'b365d', 'b365a']]
y = df['ftr']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Entrenar modelo (scikit-learn, XGBoost, etc)
```

---

## Scheduler (Producción)

### Cron (Linux/macOS)

```bash
# Ejecutar ETL cada día a las 00:00
0 0 * * * cd /path/to/proyecto && python src/etl_cli.py run

# Ejecutar cada semana
0 0 * * 0 cd /path/to/proyecto && python src/etl_cli.py run

# Ejecutar cada mes
0 0 1 * * cd /path/to/proyecto && python src/etl_cli.py run
```

### Task Scheduler (Windows)

```powershell
# Crear tarea
$action = New-ScheduledTaskAction -Execute "python" -Argument "src\etl_cli.py run" -WorkingDirectory "C:\path\to\proyecto"
Register-ScheduledTask -TaskName "ETL Football Data" -Action $action -Trigger (New-ScheduledTaskTrigger -Daily -At 00:00)
```

---

## Logs

```bash
# Ver logs en tiempo real
tail -f logs/etl_football_data.log

# Búsqueda de errores
grep "ERROR" logs/etl_football_data.log

# Último evento
tail -5 logs/etl_football_data.log
```

---

## Validación

```bash
# Checklist rápido
python setup_etl.py

# Validación completa
python etl_cli.py validate

# Estadísticas
python etl_cli.py stats
```

---

## Ejemplos Rápidos

### Obtener goles promedio

```python
analyzer = FootballDataAnalyzer(engine)
top = analyzer.obtener_top_equipos('goles_promedio', limit=5)
print(top)
```

### Predecir partido

```python
probs = analyzer.calcular_probabilidades_match('Liverpool', 'Manchester City')
print(f"1: {probs['local']:.1%}")
print(f"X: {probs['empate']:.1%}")
print(f"2: {probs['visitante']:.1%}")
```

### Historial H2H

```python
h2h = analyzer.obtener_enfrentamientos_directos('Liverpool', 'Chelsea', limit=10)
h2h[['date', 'home_team', 'away_team', 'fthg', 'ftag', 'ftr']].head()
```

---

## Ayuda

```bash
python etl_cli.py --help
python etl_cli.py run --help
python etl_cli.py stats --help
python etl_cli.py validate --help
python etl_cli.py export --help
```

---

## Documentación Completa

- 📖 [ETL_FOOTBALL_DATA_GUIDE.md](docs/ETL_FOOTBALL_DATA_GUIDE.md)
- ⚡ [ETL_QUICKSTART.md](ETL_QUICKSTART.md)
- 📚 [examples.py](examples.py)
- 📋 [ETL_INDEX.py](ETL_INDEX.py)
- 📊 [RESUMEN_ETL.md](RESUMEN_ETL.md)

---

**Estado:** ✅ Producción  
**Versión:** 1.0.0  
**Última actualización:** 30 de Enero de 2025
