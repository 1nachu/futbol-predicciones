# Team Normalization System - Guía Completa

## 📋 Contenido
1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Instalación](#instalación)
4. [API de Referencia](#api-de-referencia)
5. [Ejemplos Prácticos](#ejemplos-prácticos)
6. [Casos de Uso](#casos-de-uso)
7. [Troubleshooting](#troubleshooting)

---

## Visión General

El **Team Normalization System** resuelve un problema crítico en datos de fútbol: diferentes APIs y fuentes usan IDs distintos para el mismo equipo.

### El Problema

```
Football-Data.org:  ID 66 = "Manchester United"
API-Football v3:    ID 33 = "Manchester United"
CSV Histórico:      ID 234 = "Manchester United"
                    ↓
               ¿Cuál es el VERDADERO ID?
```

### La Solución

```
┌─────────────────────────────────────────────────────────┐
│         TABLA MAESTRA (Master Teams)                    │
├─────────────────────────────────────────────────────────┤
│ UUID Único Interno: a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5 │
│ Nombre Oficial: Manchester United FC                   │
│ País: England                                           │
│ Liga: Premier League                                    │
└─────────────────────────────────────────────────────────┘
        ↑                    ↑                    ↑
        │                    │                    │
   Mapeo 1:             Mapeo 2:              Mapeo 3:
   footballdata/66      apifootball/33       csv/234
   (100% similitud)     (100% similitud)     (100% similitud)
```

---

## Arquitectura

### Diagrama de Componentes

```
┌────────────────────────────────────────────────────────────────┐
│                   TeamNormalizer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   Búsqueda Fuzzy (Levenshtein)                          │  │
│  │   ┌─────────────────────────────────────────────┐       │  │
│  │   │ Entrada: "Man Utd"                          │       │  │
│  │   │ ↓                                            │       │  │
│  │   │ Comparar con tabla maestra                  │       │  │
│  │   │ ↓                                            │       │  │
│  │   │ Similitud: 95% (> 90%) ✓                    │       │  │
│  │   │ ↓                                            │       │  │
│  │   │ Auto-mapear a UUID interno                  │       │  │
│  │   └─────────────────────────────────────────────┘       │  │
│  │                                                          │  │
│  │   Caché en Memoria (rápido)                            │  │
│  │   ┌─────────────────────────────────────────────┐       │  │
│  │   │ "manchester united" → UUID                  │       │  │
│  │   │ ("footballdata", "66") → UUID               │       │  │
│  │   └─────────────────────────────────────────────┘       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Base de Datos (SQLite)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  master_teams (Tabla Maestra)                                  │
│  ├─ team_uuid (PK)                                             │
│  ├─ official_name (UNIQUE)                                     │
│  ├─ country                                                    │
│  ├─ league                                                     │
│  └─ timestamps                                                 │
│                                                                 │
│  external_team_mappings (Mapeos)                               │
│  ├─ mapping_id (PK)                                            │
│  ├─ team_uuid (FK)                                             │
│  ├─ source (footballdata, apifootball, etc.)                   │
│  ├─ external_id (ID en la fuente)                              │
│  ├─ external_name (Nombre en la fuente)                        │
│  ├─ similarity_score (0-100%)                                  │
│  ├─ is_automatic (bool)                                        │
│  └─ timestamps                                                 │
│                                                                 │
│  team_aliases (Alias/Apodos)                                   │
│  ├─ alias_id (PK)                                              │
│  ├─ team_uuid (FK)                                             │
│  ├─ alias_name (ej: "Man United")                              │
│  ├─ priority (orden de búsqueda)                               │
│  ├─ source (origen del alias)                                  │
│  └─ timestamps                                                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Flujo de Normalización

```
Equipo Entrante
    ↓
├─ ¿Existe mapeo externo? → SÍ → Retornar UUID (100%)
│
├─ ¿Existe nombre exacto? → SÍ → Retornar UUID (100%)
│
├─ ¿Existe alias exacto? → SÍ → Retornar UUID (100%)
│
├─ Fuzzy match contra tabla maestra
│  ├─ Similitud ≥ 90% → Auto-mapear → Retornar UUID + similitud
│  │
│  └─ Similitud < 90% → Crear nuevo equipo → Retornar UUID (0%)
│
└─ Retornar NULL si no permitido crear
```

---

## Instalación

### 1. Instalar dependencias

```bash
pip install thefuzz python-Levenshtein
```

### 2. Verificar importación

```python
from src.team_normalization import TeamNormalizer

normalizer = TeamNormalizer(db_path="data/databases/football_data.db")
print("✓ TeamNormalizer inicializado")
```

---

## API de Referencia

### Clase: `TeamNormalizer`

#### Método: `add_team()`

Agrega un nuevo equipo a la tabla maestra.

```python
uuid = normalizer.add_team(
    official_name="Manchester United FC",
    country="England",
    league="Premier League",
    source="footballdata",          # Opcional
    external_id="66",               # Opcional
    external_name="Manchester United"  # Opcional
)
```

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| official_name | str | ✓ | Nombre oficial del equipo |
| country | str | ✓ | País |
| league | str | ✗ | Liga |
| source | str | ✗ | Fuente de datos |
| external_id | str | ✗ | ID externo |
| external_name | str | ✗ | Nombre en fuente externa |

**Retorna:** UUID único (string)

**Ejemplo:**
```python
uuid = normalizer.add_team(
    official_name="Liverpool Football Club",
    country="England",
    league="Premier League"
)
# "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5"
```

---

#### Método: `normalize_team()`

Normaliza un nombre a UUID usando fuzzy matching.

```python
uuid, similarity = normalizer.normalize_team(
    team_name="Man United",
    source="footballdata",      # Opcional
    external_id="66",           # Opcional
    create_if_missing=True      # Default: True
)
```

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| team_name | str | - | Nombre del equipo |
| source | str | None | Fuente de datos |
| external_id | str | None | ID externo |
| create_if_missing | bool | True | Crear si no existe |

**Retorna:** Tuple (uuid, similarity_score: float 0-100)

**Ejemplos:**
```python
# Búsqueda exacta
uuid, sim = normalizer.normalize_team("Manchester United FC")
# ('a1b2c3d4...', 100.0)

# Fuzzy matching > 90%
uuid, sim = normalizer.normalize_team("Man United")
# ('a1b2c3d4...', 95.3)

# Fuzzy matching < 90%, crear nuevo
uuid, sim = normalizer.normalize_team("Random Team Name")
# ('x1y2z3w4...', 0.0)  ← Nuevo equipo creado

# Con mapeo externo
uuid, sim = normalizer.normalize_team(
    "Manchester United",
    source="footballdata",
    external_id="66"
)
# ('a1b2c3d4...', 100.0)
```

---

#### Método: `add_external_mapping()`

Mapea un ID externo a UUID interno.

```python
mapping_id = normalizer.add_external_mapping(
    team_uuid="a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5",
    source="footballdata",
    external_id="66",
    external_name="Manchester United",
    similarity_score=100.0,
    is_automatic=False
)
```

**Parámetros:**
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| team_uuid | str | ✓ | UUID interno |
| source | str | ✓ | Fuente ('footballdata', 'apifootball', etc.) |
| external_id | str | ✓ | ID en la fuente |
| external_name | str | ✓ | Nombre en la fuente |
| similarity_score | float | ✓ | Similitud (0-100) |
| is_automatic | bool | ✓ | ¿Automático o manual? |

**Retorna:** ID del mapeo (string)

---

#### Método: `add_alias()`

Agrega un apodo/alias para un equipo.

```python
alias_id = normalizer.add_alias(
    team_uuid="a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5",
    alias_name="Man United",
    priority=10,
    source="footballdata"
)
```

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| team_uuid | str | - | UUID del equipo |
| alias_name | str | - | Nombre alternativo |
| priority | int | 0 | Mayor = más prioritario |
| source | str | None | Origen del alias |

**Retorna:** ID del alias (string)

**Ejemplo:**
```python
# Agregar múltiples alias con prioridades
normalizer.add_alias(uuid, "Man United", priority=10)
normalizer.add_alias(uuid, "Manchester Utd", priority=9)
normalizer.add_alias(uuid, "MUFC", priority=5)

# Al buscar "Man United" → Se prefiere sobre otros aliases
```

---

#### Método: `get_team()`

Obtiene información completa de un equipo.

```python
team = normalizer.get_team(team_uuid)
```

**Retorna:**
```python
{
    'team_uuid': 'a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5',
    'official_name': 'Manchester United FC',
    'country': 'England',
    'league': 'Premier League',
    'created_at': '2026-01-30T12:00:00',
    'updated_at': '2026-01-30T12:00:00',
    'mappings': [
        {
            'source': 'footballdata',
            'external_id': '66',
            'external_name': 'Manchester United',
            'similarity_score': 100.0,
            'is_automatic': False
        },
        {
            'source': 'apifootball',
            'external_id': '33',
            'external_name': 'Manchester United',
            'similarity_score': 100.0,
            'is_automatic': True
        }
    ],
    'aliases': [
        {'alias_name': 'Man United', 'priority': 10, 'source': 'footballdata'},
        {'alias_name': 'Manchester Utd', 'priority': 9, 'source': 'footballdata'}
    ]
}
```

---

#### Método: `get_stats()`

Obtiene estadísticas del sistema.

```python
stats = normalizer.get_stats()
```

**Retorna:**
```python
{
    'total_teams': 500,
    'total_mappings': 1200,
    'auto_mappings': 950,
    'manual_mappings': 250,
    'total_aliases': 300,
    'mappings_by_source': {
        'footballdata': 350,
        'apifootball': 450,
        'csv': 400
    },
    'cache_size': 500
}
```

---

#### Método: `export_mappings()`

Exporta todos los mapeos a JSON.

```python
normalizer.export_mappings(output_file="team_mappings.json")
```

---

### Clase: `TeamETLIntegrator`

Integrador que procesa datos de múltiples fuentes ETL.

#### Método: `process_apifootball_teams()`

```python
integrator = TeamETLIntegrator()

processed, new = integrator.process_apifootball_teams(
    teams_data=[
        {'id': 1, 'name': 'Manchester United', 'country': 'England'},
        {'id': 2, 'name': 'Liverpool FC', 'country': 'England'},
    ],
    season=2026,
    league_id=39
)
print(f"Procesados: {processed}, Nuevos: {new}")
```

---

#### Método: `process_footballdataorg_api()`

```python
processed, new = integrator.process_footballdataorg_api(
    teams_response={
        'teams': [
            {'id': 123, 'name': 'Man. United', 'area': {'name': 'England'}},
            {'id': 124, 'name': 'Liverpool FC', 'area': {'name': 'England'}}
        ]
    }
)
```

---

#### Método: `get_mapping_report()`

Genera reporte de mapeos.

```python
report = integrator.get_mapping_report()
```

**Retorna:**
```python
{
    'timestamp': '2026-01-30T12:00:00',
    'summary': { ... },  # Stats
    'mappings_by_source': [ ... ],
    'unmapped_count': 5,
    'unmapped_teams': [ ... ],
    'conflicts_count': 2,
    'conflicts': [ ... ]
}
```

---

#### Método: `validate_integrity()`

Valida integridad referencial.

```python
validation = integrator.validate_integrity()
```

**Retorna:**
```python
{
    'orphaned_mappings': 0,
    'orphaned_aliases': 0,
    'duplicate_aliases': 0,
    'details': [ ... ]
}
```

---

## Ejemplos Prácticos

### Ejemplo 1: Inicialización Básica

```python
from src.team_normalization import TeamNormalizer

# Crear normalizador
normalizer = TeamNormalizer(db_path="data/databases/football_data.db")

# Agregar equipos
mu_uuid = normalizer.add_team("Manchester United FC", "England", "Premier League")
lfc_uuid = normalizer.add_team("Liverpool FC", "England", "Premier League")

# Agregar aliases
normalizer.add_alias(mu_uuid, "Man United", priority=10)
normalizer.add_alias(lfc_uuid, "LFC", priority=10)

# Normalizar nombres
uuid1, sim1 = normalizer.normalize_team("Manchester United")  # 100%
uuid2, sim2 = normalizer.normalize_team("Man United")         # 100% (alias)
uuid3, sim3 = normalizer.normalize_team("Manchester Utd")     # 95% (fuzzy)

print(f"UUID1: {uuid1} ({sim1}%)")
print(f"UUID2: {uuid2} ({sim2}%)")
print(f"UUID3: {uuid3} ({sim3}%)")
```

---

### Ejemplo 2: Procesar API-Football

```python
from src.etl_team_integration import TeamETLIntegrator

integrator = TeamETLIntegrator()

# Datos de API-Football
teams_data = [
    {'id': 33, 'name': 'Manchester United', 'country': 'England'},
    {'id': 40, 'name': 'Liverpool', 'country': 'England'},
    {'id': 541, 'name': 'Real Madrid', 'country': 'Spain'},
]

# Procesar
processed, new = integrator.process_apifootball_teams(teams_data)
print(f"Procesados: {processed}, Nuevos: {new}")

# Obtener reporte
report = integrator.get_mapping_report()
print(f"Total equipos: {report['summary']['total_teams']}")
print(f"Auto-mapeados: {report['summary']['auto_mappings']}")
```

---

### Ejemplo 3: Reconciliar Múltiples Fuentes

```python
from src.etl_team_integration import TeamETLIntegrator

integrator = TeamETLIntegrator()

# 1. Procesar Football-Data.org
print("Procesando Football-Data.org...")
footballdataorg = {
    'teams': [
        {'id': 66, 'name': 'Manchester United', 'area': {'name': 'England'}},
        {'id': 64, 'name': 'Liverpool', 'area': {'name': 'England'}}
    ]
}
p1, n1 = integrator.process_footballdataorg_api(footballdataorg)

# 2. Procesar API-Football
print("Procesando API-Football...")
apifootball = [
    {'id': 33, 'name': 'Manchester United', 'country': 'England'},
    {'id': 40, 'name': 'Liverpool', 'country': 'England'}
]
p2, n2 = integrator.process_apifootball_teams(apifootball)

# 3. Procesar CSV histórico
print("Procesando CSV histórico...")
p3, n3 = integrator.process_footballdata_teams("data/teams.csv", league="Premier League")

# 4. Generar reporte
print("\n=== REPORTE DE RECONCILIACIÓN ===")
report = integrator.get_mapping_report()
print(f"Total equipos reconciliados: {report['summary']['total_teams']}")
print(f"Total mapeos: {report['summary']['total_mappings']}")
print(f"Conflictos detectados: {report['conflicts_count']}")

for conflict in report['conflicts']:
    print(f"  CONFLICTO: {conflict['source']}/{conflict['external_id']} "
          f"mapea a {conflict['conflicting_uuids']} UUIDs diferentes")

# 5. Exportar datos normalizados
integrator.export_normalized_data("normalized_teams.csv")
```

---

### Ejemplo 4: Integración con ETL Existente

```python
from src.team_normalization import TeamNormalizer
from src.etl_football_data import FootballDataETL

# Inicializar ambos sistemas
normalizer = TeamNormalizer()
etl = FootballDataETL()

# Procesar partidos con IDs normalizados
for match in etl.get_matches():
    # Normalizar equipos
    home_uuid, _ = normalizer.normalize_team(match['home_team'])
    away_uuid, _ = normalizer.normalize_team(match['away_team'])
    
    # Guardar con UUIDs
    etl.save_match(
        match_id=match['id'],
        home_team_uuid=home_uuid,
        away_team_uuid=away_uuid,
        score=match['score'],
        date=match['date']
    )
```

---

## Casos de Uso

### Caso 1: Setup Inicial de Tabla Maestra

**Objetivo:** Crear tabla maestra con equipos de las tres principales ligas españolas.

```python
from src.team_normalization import TeamNormalizer

normalizer = TeamNormalizer()

# Ligas españolas
teams = [
    ("Real Madrid CF", "Spain", "La Liga"),
    ("FC Barcelona", "Spain", "La Liga"),
    ("Atlético Madrid", "Spain", "La Liga"),
    # ... 17 más
]

for name, country, league in teams:
    uuid = normalizer.add_team(name, country, league)
    print(f"✓ {name}: {uuid}")

stats = normalizer.get_stats()
print(f"\nTotal equipos: {stats['total_teams']}")
```

---

### Caso 2: Auto-Reconciliación de Datos Históricos

**Objetivo:** Reconciliar datos históricos de 10 años con tabla maestra.

```python
from src.etl_team_integration import TeamETLIntegrator

integrator = TeamETLIntegrator()

# Procesar histórico por temporada
for season in range(2014, 2024):
    csv_file = f"data/historical/{season}_matches.csv"
    processed, new = integrator.process_footballdata_teams(csv_file)
    print(f"{season}: {processed} procesados, {new} nuevos")

# Verificar calidad de mapeos
report = integrator.get_mapping_report()
auto_rate = (report['summary']['auto_mappings'] / 
             report['summary']['total_mappings'] * 100)
print(f"Tasa de auto-mapeo: {auto_rate:.1f}%")

# Resolver conflictos
for conflict in report['conflicts']:
    print(f"⚠️ CONFLICTO: {conflict['source']}/{conflict['external_id']}")
```

---

### Caso 3: Pipeline de Ingesta en Tiempo Real

**Objetivo:** Integrar datos en tiempo real desde API-Football.

```python
from src.api_football_enricher import APIFootballEnricher
from src.etl_team_integration import TeamETLIntegrator

enricher = APIFootballEnricher(api_key="tu_clave")
integrator = TeamETLIntegrator()

# Fetch diario de fixtures
fixtures = enricher.fetch_daily_fixtures(league_id=39, season=2026)

# Normalizar equipos
for fixture in fixtures:
    home_uuid, _ = integrator.normalizer.normalize_team(
        fixture['teams']['home']['name'],
        source='apifootball',
        external_id=fixture['teams']['home']['id']
    )
    away_uuid, _ = integrator.normalizer.normalize_team(
        fixture['teams']['away']['name'],
        source='apifootball',
        external_id=fixture['teams']['away']['id']
    )
    
    # Guardar con UUIDs normalizados
    save_match(home_uuid, away_uuid, fixture)
```

---

## Troubleshooting

### Problema 1: Similitud < 90% pero es el equipo correcto

**Síntoma:** Nombres como "Manchester City FC" vs "Manchester City" solo alcanzan 85% similitud.

**Solución 1:** Agregar alias de prioridad alta

```python
normalizer.add_alias(uuid, "Manchester City FC", priority=100)
normalizer.add_alias(uuid, "Manchester City", priority=99)
```

**Solución 2:** Mapeo manual explícito

```python
normalizer.add_external_mapping(
    team_uuid=uuid,
    source="apifootball",
    external_id="10",
    external_name="Manchester City FC",
    similarity_score=85.0,
    is_automatic=False
)
```

---

### Problema 2: Múltiples UUIDs para el mismo equipo (duplicados)

**Síntoma:** Conflicto detectado en reporte.

```python
report = integrator.get_mapping_report()
# 'conflicts': [
#     {
#         'source': 'footballdata',
#         'external_id': '66',
#         'conflicting_uuids': 2,
#         'team_uuids': 'uuid1,uuid2'
#     }
# ]
```

**Solución:**

1. Identificar equipos duplicados:
```python
conflicting = report['conflicts'][0]
uuids = conflicting['team_uuids'].split(',')

for uuid in uuids:
    team = normalizer.get_team(uuid)
    print(f"{uuid}: {team['official_name']}")
```

2. Mergear equipos (manual):
```sql
UPDATE external_team_mappings
SET team_uuid = 'uuid_correcto'
WHERE team_uuid IN ('uuid_incorrecto1', 'uuid_incorrecto2');

DELETE FROM master_teams
WHERE team_uuid IN ('uuid_incorrecto1', 'uuid_incorrecto2');
```

---

### Problema 3: Rendimiento lento en tablas grandes

**Síntoma:** Normalize_team() tarda >1 segundo con 5000+ equipos.

**Solución 1:** Usar caché en memoria (ya incluido)

```python
# La caché se carga automáticamente
# Primera búsqueda: ~50ms
# Búsquedas posteriores: <1ms
uuid1, sim1 = normalizer.normalize_team("Manchester")  # 50ms
uuid2, sim2 = normalizer.normalize_team("Manchester")  # <1ms
```

**Solución 2:** Forzar recarga de caché

```python
normalizer._cache.clear()
normalizer._load_cache()
```

---

### Problema 4: Base de datos bloqueada (SQLite)

**Síntoma:** `sqlite3.OperationalError: database is locked`

**Causa:** Múltiples procesos escribiendo simultáneamente.

**Solución:**

```python
# Usar timeout
conn = sqlite3.connect(
    db_path,
    timeout=30  # 30 segundos de espera
)

# O usar mode journal_mode = WAL (Write-Ahead Logging)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode = WAL")
```

---

## Conclusiones

✅ **Ventajas del Sistema:**
- Reconciliación automática con similitud >90%
- Tabla maestra única de equipos
- Mapeos flexibles a múltiples fuentes
- Caché en memoria para rendimiento
- Trazabilidad completa de mapeos
- Validación de integridad

✅ **Casos de Uso Recomendados:**
- Integración de múltiples APIs
- Limpieza y normalización de datos históricos
- Construcción de datasets consolidados para ML
- Auditoría y trazabilidad de datos

✅ **Próximas Mejoras:**
- GUI web para gestión de mapeos
- Validación de conflictos interactiva
- Estadísticas en dashboard Streamlit
- Exportación a múltiples formatos (Parquet, PostgreSQL)

---

**Autor:** Backend Integration Team  
**Fecha:** 30 de Enero 2026  
**Versión:** 1.0.0
