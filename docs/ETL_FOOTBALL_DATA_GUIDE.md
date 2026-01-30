# 📊 FOOTBALL DATA ETL PIPELINE

## Descripción General

**Football Data ETL** es un pipeline profesional de extracción, transformación y carga (ETL) de datos históricos de fútbol desde **Football-Data.co.uk**.

Diseñado para crear un **dataset robusto de entrenamiento** sin depender de APIs restringidas, permitiendo entrenar modelos de predicción de fútbol con histórico de 10 temporadas de 3 ligas principales.

---

## 🎯 Características Principales

### ✅ Extracción
- Descarga automática de archivos CSV desde Football-Data.co.uk
- **10 temporadas** de histórico para cada liga
- **3 ligas principales**: Premier League, La Liga, Bundesliga
- Reintentos automáticos con backoff exponencial
- Respetuoso con rate limits

### 🔄 Transformación
- **Normalización de fechas** a formato ISO 8601
- Mantiene **columnas críticas** para predicción:
  - `Date`: Fecha del partido
  - `HomeTeam` / `AwayTeam`: Equipos
  - `FTHG` / `FTAG`: Goles finales
  - `FTR`: Resultado final (1/D/2)
  - `HS` / `AS`: Tiros totales
  - `HST` / `AST`: Tiros al arco
  - `B365H` / `B365D` / `B365A`: Cuotas Bet365
  - `HF` / `AF`: Faltas
  - `HR` / `AR`: Tarjetas rojas
  - `HY` / `AY`: Tarjetas amarillas
- Enriquecimiento con columnas derivadas:
  - `Total_Goles`: Goles totales del partido
  - `Over_25`: Flag si fue Over 2.5
  - `Diferencia_Tiros`: HS - AS
  - `Efectividad`: Tiros al arco / tiros totales
- Validación de datos (duplicados, NULL, FTR válidos)
- Limpieza automática

### 💾 Carga
- Soporta **SQLite** (desarrollo) y **PostgreSQL** (producción)
- Inserción masiva en chunks (optimizado)
- Creación automática de índices
- Constraints de unicidad

### 📈 Análisis
- Estadísticas por equipo (casa/fuera)
- Historial directo (H2H)
- Rankings por métricas
- Probabilidades de resultado
- Tendencias de mercado
- Detección de outliers

### 📥 Exportación
- Exportar a **Excel** (múltiples sheets)
- Exportar a **CSV**
- Exportar a **JSON**
- Exportar a **Parquet**

---

## 🚀 Instalación

### 1. Dependencias

```bash
# Instalar dependencias
pip install -r requirements.txt
```

### 2. Crear Directorios (automático)

```
proyecto/
├── data/
│   └── databases/          # BD SQLite
├── logs/                   # Logs de ejecución
└── src/
    ├── etl_football_data.py       # Pipeline principal
    ├── etl_cli.py                 # CLI
    ├── etl_config.py              # Configuración
    └── etl_data_analysis.py       # Análisis
```

---

## 💻 Uso

### Opción 1: CLI (Recomendado)

```bash
cd src

# Ejecutar pipeline completo (SQLite)
python etl_cli.py run

# Ligas específicas
python etl_cli.py run --ligas E0,SP1

# Usar PostgreSQL
python etl_cli.py run --db-type postgresql \
  --connection "postgresql://user:pass@localhost/football"

# Ver estadísticas
python etl_cli.py stats

# Validar integridad de datos
python etl_cli.py validate

# Exportar a Excel
python etl_cli.py export --output reporte.xlsx
```

### Opción 2: Script de Python

```python
from src.etl_football_data import FootballETLPipeline

# Crear pipeline
pipeline = FootballETLPipeline(
    db_type='sqlite',
    connection_string='sqlite:///football_data.db'
)

# Ejecutar
pipeline.ejecutar(ligas=['E0', 'SP1', 'D1'])
```

### Opción 3: Módulos Individuales

```python
# Extracción
from src.etl_football_data import FootballDataExtractor

extractor = FootballDataExtractor()
datos = extractor.descargar_multiples_ligas(['E0'])

# Transformación
from src.etl_football_data import FootballDataTransformer

transformer = FootballDataTransformer()
df_clean = transformer.transformar(datos['E0'])

# Carga
from src.etl_football_data import FootballDataLoader

loader = FootballDataLoader('sqlite')
loader.crear_tablas()
loader.cargar_datos(df_clean)
```

---

## 🔍 Análisis de Datos

### Usar el Analizador

```python
from src.etl_data_analysis import FootballDataAnalyzer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

# Estadísticas de equipo
stats = analyzer.obtener_estadisticas_equipo('Manchester City')
print(stats)

# Historial directo
h2h = analyzer.obtener_enfrentamientos_directos('Liverpool', 'Manchester United', limit=10)
print(h2h)

# Probabilidades de partido
probs = analyzer.calcular_probabilidades_match('Liverpool', 'Manchester City')
print(f"Local: {probs['local']:.1%}, Empate: {probs['empate']:.1%}, Visitante: {probs['visitante']:.1%}")

# Tendencias de mercado
tendencias = analyzer.obtener_tendencias_mercado(dias=30)
print(f"Over 2.5: {tendencias['over_25_pct']}%")
```

### Exportar Datos

```python
from src.etl_data_analysis import FootballDataExporter

exporter = FootballDataExporter()

# Excel
exporter.exportar_excel(df, 'datos.xlsx')

# CSV
exporter.exportar_csv(df, 'datos.csv')

# JSON
exporter.exportar_json(df, 'datos.json')

# Parquet
exporter.exportar_parquet(df, 'datos.parquet')
```

---

## 🗄️ Configuración de Bases de Datos

### SQLite (Desarrollo - Recomendado para Empezar)

```bash
# Automático: crea BD en data/databases/football_data.db
python etl_cli.py run
```

**Ventajas:**
- ✅ No requiere instalación adicional
- ✅ Portátil
- ✅ Perfecto para desarrollo y pruebas

**Desventajas:**
- ❌ No para producción multi-usuario
- ❌ Menos performance con datos grandes

### PostgreSQL (Producción)

```bash
# Instalar PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql
# Windows: https://www.postgresql.org/download/windows/

# Crear base de datos
createdb football_data

# Ejecutar ETL
python etl_cli.py run --db-type postgresql \
  --connection "postgresql://user:password@localhost:5432/football_data"
```

**Variables de entorno (.env):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_data
DB_USER=postgres
DB_PASSWORD=mi_contraseña
```

---

## 📋 Esquema de Base de Datos

### Tabla: `matches`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER | Clave primaria |
| `date` | DATE | Fecha del partido (ISO 8601) |
| `home_team` | VARCHAR(100) | Equipo local |
| `away_team` | VARCHAR(100) | Equipo visitante |
| `fthg` | INTEGER | Goles marcados (local) |
| `ftag` | INTEGER | Goles marcados (visitante) |
| `ftr` | VARCHAR(1) | Resultado (1/D/2) |
| `hs` | INTEGER | Tiros (local) |
| `as_shots` | INTEGER | Tiros (visitante) |
| `hst` | INTEGER | Tiros al arco (local) |
| `ast` | INTEGER | Tiros al arco (visitante) |
| `hf` | INTEGER | Faltas (local) |
| `af` | INTEGER | Faltas (visitante) |
| `hr` | INTEGER | Tarjetas rojas (local) |
| `ar` | INTEGER | Tarjetas rojas (visitante) |
| `hy` | INTEGER | Tarjetas amarillas (local) |
| `ay` | INTEGER | Tarjetas amarillas (visitante) |
| `b365h` | DECIMAL | Cuota (1) Bet365 |
| `b365d` | DECIMAL | Cuota (X) Bet365 |
| `b365a` | DECIMAL | Cuota (2) Bet365 |
| `total_goles` | INTEGER | Suma de goles |
| `over_25` | INTEGER | Flag: 1 si Over 2.5 |
| `diff_tiros` | INTEGER | Diferencia de tiros |
| `efectividad_local` | DECIMAL | % tiros al arco / tiros |
| `temporada` | VARCHAR(10) | Código temporada (ej: 2425) |
| `created_at` | TIMESTAMP | Timestamp inserción |

**Índices:**
- `idx_date`: Para consultas por fecha
- `idx_teams`: Para búsquedas de equipos
- `idx_temporada`: Para filtrar por temporada

---

## 📊 Estructura de Datos

### Input: CSV de Football-Data.co.uk

Ejemplo de estructura original:

```
Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HS,AS,HST,AST,HF,AF,HR,AR,HY,AY,B365H,B365D,B365A,...
28/08/2021,Manchester City,Tottenham,1,0,1,6,3,2,1,8,9,0,0,2,1,1.40,4.50,9.00,...
```

### Output: Base de Datos Normalizada

```
date: 2021-08-28
home_team: Manchester City
away_team: Tottenham
fthg: 1
ftag: 0
ftr: 1
hs: 6
as_shots: 3
... (todas las columnas)
```

---

## 📈 Casos de Uso

### 1️⃣ Entrenar Modelo de Predicción

```python
from src.etl_data_analysis import FootballDataAnalyzer
import pandas as pd

engine = create_engine('sqlite:///football_data.db')

# Cargar datos para entrenamiento
with engine.connect() as conn:
    df_training = pd.read_sql("""
        SELECT 
            fthg, ftag, ftr,
            hs, as_shots, hst, ast,
            b365h, b365d, b365a,
            hf, af, hy, ay
        FROM matches
        WHERE temporada IN ('2425', '2324', '2223')
    """, conn)

# Usar para entrenar modelo (scikit-learn, XGBoost, etc)
```

### 2️⃣ Análisis Exploratorio

```python
analyzer = FootballDataAnalyzer(engine)

# Top 10 equipos por goles
top_ofensiva = analyzer.obtener_top_equipos('goles_promedio', limit=10)
print(top_ofensiva)

# Probabilidad de partido
probs = analyzer.calcular_probabilidades_match('Liverpool', 'Chelsea')
print(probs)
```

### 3️⃣ Dashboard Streamlit

```python
# En src/app.py, puedes integrar:
from src.etl_data_analysis import FootballDataAnalyzer

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

# Mostrar estadísticas en Streamlit
st.write(analyzer.obtener_estadisticas_equipo('Liverpool'))
```

---

## 🔧 Troubleshooting

### Error: "Timeout en descarga"
```bash
# Aumentar timeout
python etl_cli.py run --timeout 60
```

### Error: "Base de datos está bloqueada (SQLite)"
```bash
# Reintentar con delay
python etl_cli.py run
# Esperar y reintentar
```

### Error: "No se encuentra tabla"
```bash
# Recrear tablas
python etl_cli.py run --recreate-tables
```

### Error: "Conexión a PostgreSQL rechazada"
```bash
# Verificar credenciales
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=mi_contraseña
export DB_NAME=football_data

python etl_cli.py run --db-type postgresql
```

---

## 📝 Logging

Los logs se guardan en `logs/etl_football_data.log`

```
2025-01-30 14:23:45,123 - INFO - [etl_football_data] - Descargando: Premier League (2425)
2025-01-30 14:23:47,456 - INFO - [etl_football_data] - ✓ Descargados 380 registros de E0/2425
2025-01-30 14:23:50,789 - INFO - [etl_football_data] - ✓ Fechas normalizadas a ISO 8601
```

---

## 🔐 Seguridad

### Variables de Entorno (.env)

```bash
# NO guardar en Git, usar .env.local
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=contraseña_segura
DB_NAME=football_data
```

### Credenciales PostgreSQL

```bash
# .pgpass (Linux/macOS)
localhost:5432:football_data:postgres:contraseña

chmod 600 ~/.pgpass
```

---

## 📦 Estructura Completa del Proyecto

```
projecto timba/
├── requirements.txt                    # Dependencias
├── src/
│   ├── etl_football_data.py           # 🔴 Pipeline principal (3 clases)
│   ├── etl_cli.py                     # 🟢 CLI (comandos run/stats/validate/export)
│   ├── etl_config.py                  # 🟡 Configuración centralizada
│   ├── etl_data_analysis.py           # 🔵 Análisis y queries
│   ├── app.py                         # Streamlit app
│   ├── timba_core.py                  # Núcleo de predicción
│   └── cli.py                         # CLI existente
├── data/
│   └── databases/
│       └── football_data.db           # BD SQLite
├── logs/
│   └── etl_football_data.log          # Logs
└── docs/
    └── ETL_GUIDE.md                   # Esta guía
```

---

## 🎓 Ejemplos Completos

### Ejemplo 1: Descarga y análisis básico

```bash
cd src
python etl_cli.py run --ligas E0
python etl_cli.py stats
```

### Ejemplo 2: Exportar datos para modelo ML

```python
from src.etl_football_data import FootballDataLoader
from src.etl_data_analysis import FootballDataExporter
from sqlalchemy import create_engine
import pandas as pd

# Conectar
engine = create_engine('sqlite:///football_data.db')

# Extraer datos para ML
with engine.connect() as conn:
    df = pd.read_sql("""
        SELECT 
            home_team, away_team, fthg, ftag, ftr,
            hs, hst, as_shots, ast, 
            b365h, b365d, b365a
        FROM matches
        WHERE temporada IN ('2425', '2324')
    """, conn)

# Exportar
exporter = FootballDataExporter()
exporter.exportar_parquet(df, 'datos_entrenamiento.parquet')
```

### Ejemplo 3: Dashboard de equipo

```python
from src.etl_data_analysis import FootballDataAnalyzer
from sqlalchemy import create_engine

engine = create_engine('sqlite:///football_data.db')
analyzer = FootballDataAnalyzer(engine)

equipo = 'Liverpool'
stats = analyzer.obtener_estadisticas_equipo(equipo)

print(f"Estadísticas de {equipo}:")
print(f"  Casa:")
print(f"    Goles/partido: {stats['casa']['goles_marcados']}")
print(f"    Victorias: {stats['casa']['victorias']}")
print(f"  Fuera:")
print(f"    Goles/partido: {stats['fuera']['goles_marcados']}")
print(f"    Victorias: {stats['fuera']['victorias']}")
```

---

## 🤝 Contribuciones

Para reportar bugs o sugerir mejoras:

1. Revisar [LIMPIEZA_PROYECTO.md](../docs/LIMPIEZA_PROYECTO.md)
2. Crear issue en el repositorio
3. Proponer pull request

---

## 📄 Licencia

Datos: [Football-Data.co.uk](https://www.football-data.co.uk/) - Licencia de datos históricos
Código: Proyecto Timba Predictor

---

## 📞 Soporte

- 📧 Email: [support](mailto:support@example.com)
- 📚 Documentación: [SISTEMA_COMPLETO.md](../docs/SISTEMA_COMPLETO.md)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

**Última actualización:** 30 de Enero de 2025
**Versión:** 1.0.0
**Estado:** ✅ Producción
