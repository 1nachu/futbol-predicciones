# Live Scores Module - Guía Completa

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Uso Básico](#uso-básico)
6. [API Client](#api-client)
7. [Rate Limiting](#rate-limiting)
8. [Live Scores Manager](#live-scores-manager)
9. [CLI](#cli)
10. [Ejemplos](#ejemplos)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción General

El módulo **Live Scores** proporciona acceso en tiempo real a marcadores de fútbol desde la API de Football-Data.org. Incluye:

- ✅ Cliente HTTP con autenticación
- ✅ Rate limiting automático (Leaky Bucket algorithm)
- ✅ Polling inteligente de competiciones
- ✅ Detección de eventos (goles, cambios de estado)
- ✅ Persistencia en SQLite
- ✅ CLI profesional para operaciones

**Características principales:**

| Característica | Detalles |
|---|---|
| Rate Limiting | 10 req/min, 6s mínimo entre llamadas |
| Competiciones | 8 ligas soportadas (PL, CL, PD, BL1, SA, FL1, etc) |
| Eventos | GOAL, HALFTIME, FULLTIME, STATUS_CHANGE |
| Polling | Adaptativo (15s en vivo, 10min programado, 1h finalizado) |
| Persistencia | SQLite con 3 tablas (events, snapshots, history) |
| Threading | Thread-safe con RLock |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────┐
│    Live Scores CLI (live_scores_cli.py)
│    - Commands: monitor, status, export
│    - Argparse interface
└──────────────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐   ┌──────▼──────────────┐
│ LiveScoresManager │   │FootballDataClient   │
│ - Polling logic  │   │ - HTTP requests     │
│ - Event detect   │   │ - Authentication    │
│ - SQLite persist │   │ - Caching (TTL)     │
└────────┬─────────┘   └──────┬──────────────┘
         │                    │
         └────────┬───────────┘
                  │
         ┌────────▼────────┐
         │ LeakyBucket     │
         │ Rate Limiting   │
         │ (10 req/min)    │
         └─────────────────┘
                  │
                  ▼
      ┌──────────────────────┐
      │Football-Data.org API │
      │ (10 req/min limit)   │
      └──────────────────────┘
```

### Flujo de Datos

```
1. CLI → start_polling()
2. LiveScoresManager → _polling_loop()
3. Para cada competición:
   a. Obtener matches vivos
   b. Comparar con snapshot anterior
   c. Detectar eventos
   d. Ejecutar callbacks
   e. Guardar en SQLite
4. Esperar adaptativo (15s si en vivo, 10min si scheduled)
5. Repetir hasta stop_polling()
```

---

## 🔧 Instalación

### 1. Requisitos Previos

```bash
# Python 3.8+
python3 --version

# Git (para clonar)
git clone <repo>
cd projecto\ timba
```

### 2. Instalar Dependencias

```bash
# Crear virtualenv (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar requisitos
pip install -r requirements.txt

# Requisitos adicionales para Live Scores
pip install requests[socks] python-dateutil pytz
```

### 3. Verificar Instalación

```bash
# Verificar módulos
python3 -c "from src.football_api_client import FootballDataClient; print('✓ OK')"
python3 -c "from src.live_scores import LiveScoresManager; print('✓ OK')"

# Verificar CLI
python3 src/live_scores_cli.py --help
```

---

## ⚙️ Configuración

### 1. API Key de Football-Data.org

Obtener API Key en https://www.football-data.org/

```bash
# Opción 1: Variable de entorno
export FOOTBALL_DATA_API_KEY="tu_api_key_aqui"

# Opción 2: Archivo .env
echo "FOOTBALL_DATA_API_KEY=tu_api_key_aqui" >> .env

# Opción 3: Argumentos CLI
python3 src/live_scores_cli.py --api-key "tu_api_key_aqui" status
```

### 2. Validar Configuración

```bash
# Validar API Key y conexión
python3 src/live_scores_cli.py validate-key

# Output esperado:
# ✓ API Key válida
# ✓ Conexión a API exitosa
# Rate Limit: 10 req/60s
# Tokens disponibles: 10.00
```

### 3. Configurar Competiciones (Opcional)

```python
# En código
manager = LiveScoresManager(client)
manager.competitions = ['PL', 'CL', 'PD']  # Solo Premier, Champions, La Liga

# En CLI: se usan automáticamente las competiciones por defecto
```

### 4. Configurar Persistencia

```bash
# Crear directorio de datos
mkdir -p data/databases

# Base de datos SQLite se crea automáticamente en:
# data/databases/live_scores.db
```

---

## 🚀 Uso Básico

### Importar en Python

```python
from src.football_api_client import FootballDataClient
from src.live_scores import LiveScoresManager, DefaultCallbacks

# Crear cliente
api_key = "tu_api_key"
client = FootballDataClient(api_key)

# Crear manager
manager = LiveScoresManager(client)

# Registrar callbacks
manager.register_callback(DefaultCallbacks.console_callback)

# Iniciar polling
manager.start_polling(interval=30)  # 30 segundos

# Esperar un poco
import time
time.sleep(60)

# Obtener partidos en vivo
live_matches = manager.get_live_matches()
for match in live_matches:
    print(f"{match['home_team']} {match['home_score']}-"
          f"{match['away_score']} {match['away_team']}")

# Detener
manager.stop_polling()
```

### CLI Básico

```bash
# Validar API Key
python3 src/live_scores_cli.py validate-key

# Ver estado actual
python3 src/live_scores_cli.py status

# Monitorear 5 minutos
python3 src/live_scores_cli.py monitor --duration 300

# Exportar datos
python3 src/live_scores_cli.py export --output current_scores.json
```

---

## 🌐 API Client

### FootballDataClient

Cliente HTTP para Football-Data.org con autenticación, caché y rate limiting.

#### Métodos Principales

```python
client = FootballDataClient(api_key)

# 1. Obtener competiciones
competitions = client.get_competitions()
# [{'code': 'PL', 'name': 'Premier League', ...}, ...]

# 2. Obtener partidos de una competición
matches = client.get_matches('PL', status='LIVE')
# [{'id': 123, 'status': 'LIVE', 'homeTeam': {...}, ...}, ...]

# 3. Obtener solo partidos en vivo
live = client.get_live_matches()
# [partidos en vivo de todas las competiciones]

# 4. Obtener partidos de una competición específica
matches = client.get_competition_matches('CL')

# 5. Rate limit status
status = client.get_rate_limit_status()
# {'capacity': 10, 'available_tokens': 9.5, 'refill_time': 60, ...}

# 6. Forzar actualización (ignorar caché)
matches = client.get_matches('PL', force_refresh=True)
```

#### Configuración de Caché

```python
# TTL por defecto en segundos
client = FootballDataClient(api_key)

# - Competiciones: 60s
# - Partidos: 300s (5 min)
# - Partidos en vivo: 0s (no se cachean)
# - Detalles: 300s

# Forzar refresco
matches = client.get_live_matches(force_refresh=True)
```

#### Manejo de Errores

```python
from src.football_api_client import (
    FootballAPIError,
    RateLimitError,
    AuthenticationError,
    NotFoundError
)

try:
    matches = client.get_matches('PL')
except RateLimitError as e:
    print(f"Rate limit: {e}")
    # Esperar y reintentar
except AuthenticationError as e:
    print(f"API Key inválida: {e}")
except FootballAPIError as e:
    print(f"Error API: {e}")
```

---

## ⚡ Rate Limiting

### Algoritmo: Leaky Bucket

Sistema de tokens con refill automático:

```
Capacidad: 10 tokens
Refill: 60 segundos
Mínimo entre requests: 6 segundos

┌─────────────────────────────────────┐
│ Leaky Bucket (10 tokens)            │
├─────────────────────────────────────┤
│ Token 1: ●                          │
│ Token 2: ●                          │
│ Token 3: ●                          │
│ Token 4: ●                          │
│ Token 5: ●                          │
│ Token 6: ●                          │
│ Token 7: ●                          │
│ Token 8: ●                          │
│ Token 9: ●                          │
│ Token 10: ●                         │
└─────────────────────────────────────┘

Cada request consume 1 token
Cada 60s se agregan tokens (hasta 10)
```

### Uso en Código

```python
# Automático (usado internamente)
client = FootballDataClient(api_key)
matches = client.get_matches('PL')  # Automáticamente rate-limited

# Acceso directo a bucket
bucket = client.rate_limiter
print(f"Tokens disponibles: {bucket.tokens}")
print(f"Espera necesaria: {bucket.get_wait_time()}s")

# Esperar manualmente si es necesario
if not bucket.acquire(timeout=60):
    print("No se pudieron obtener tokens")
```

### Monitoreo de Rate Limit

```bash
# Ver estado
python3 src/live_scores_cli.py status

# Output incluye:
# Rate Limit:
#   Tokens disponibles: 9.50/10
#   Tiempo de espera: 3.21s
#   Entradas en caché: 5
```

---

## 🔄 Live Scores Manager

### LiveScoresManager

Orquestador de polling con detección de eventos y persistencia.

#### Inicialización

```python
from src.live_scores import LiveScoresManager
from src.football_api_client import FootballDataClient

client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Opciones
manager.competitions = ['PL', 'CL', 'PD']  # Competiciones a monitorear
manager.db_path = 'data/databases/live_scores.db'  # Ruta DB
```

#### Métodos Principales

```python
# 1. Iniciar polling en background
manager.start_polling(interval=30)
# interval: segundos entre polls (adaptativo si se especifica)

# 2. Detener polling
manager.stop_polling()

# 3. Obtener partidos en vivo
live = manager.get_live_matches()
for match in live:
    print(f"{match['home_team']} {match['home_score']}-"
          f"{match['away_score']} {match['away_team']}")

# 4. Obtener estadísticas
stats = manager.get_statistics()
print(f"Partidos en vivo: {stats['live_matches']}")
print(f"Eventos detectados: {stats['total_events']}")

# 5. Exportar datos
manager.export_to_json('scores.json')

# 6. Registrar callbacks
manager.register_callback(my_callback_function)
```

#### Callbacks

```python
from src.live_scores import DefaultCallbacks

def my_callback(event):
    """
    event = {
        'type': MatchEvent.GOAL_HOME,  # o GOAL_AWAY, FULLTIME, etc
        'match_id': 123,
        'home_team': 'Manchester United',
        'away_team': 'Liverpool',
        'home_score': 2,
        'away_score': 1,
        'minute': 45,
        'timestamp': datetime.now(),
        ...
    }
    """
    if event['type'].name == 'GOAL_HOME':
        print(f"⚽ Gol de {event['home_team']} (min {event['minute']})")

# Registrar
manager.register_callback(my_callback)

# O usar callbacks por defecto
manager.register_callback(DefaultCallbacks.console_callback)
manager.register_callback(DefaultCallbacks.log_callback)
```

#### Eventos Detectados

```python
from src.live_scores import MatchEvent

# Eventos disponibles:
MatchEvent.MATCH_STARTED          # Comenzó el partido
MatchEvent.GOAL_HOME              # Gol del equipo local
MatchEvent.GOAL_AWAY              # Gol del equipo visitante
MatchEvent.HALFTIME               # Final del primer tiempo
MatchEvent.FULLTIME               # Final del partido
MatchEvent.STATUS_CHANGE          # Cambio de estado
MatchEvent.MINUTE_UPDATE          # Actualización de minuto
MatchEvent.TEAM_SUBSTITUTION      # Cambio de jugador
MatchEvent.MATCH_CANCELLED        # Partido cancelado
```

#### Persistencia en SQLite

```python
# Automática - se guarda en:
# data/databases/live_scores.db

# Tablas:
# - match_events: Registro de todos los eventos detectados
# - match_snapshots: Última captura de estado de cada partido
# - matches_history: Histórico de partidos

# Consultar SQLite
import sqlite3
conn = sqlite3.connect('data/databases/live_scores.db')
cursor = conn.cursor()

# Goles por equipo
cursor.execute("""
    SELECT home_team, COUNT(*) as goals
    FROM match_events
    WHERE type = 'GOAL_HOME'
    GROUP BY home_team
    ORDER BY goals DESC
""")
for row in cursor:
    print(f"{row[0]}: {row[1]} goles")

conn.close()
```

---

## 💻 CLI

### Comandos Disponibles

```bash
# 1. Validar configuración
python3 src/live_scores_cli.py validate-key

# 2. Listar competiciones
python3 src/live_scores_cli.py competitions

# 3. Ver estado actual
python3 src/live_scores_cli.py status

# 4. Monitorear en tiempo real
python3 src/live_scores_cli.py monitor [OPTIONS]
  --duration SEGUNDOS    (default: 300)
  --interval SEGUNDOS    (default: 30)

# 5. Exportar datos
python3 src/live_scores_cli.py export [OPTIONS]
  --output ARCHIVO       (default: live_scores.json)

# 6. Estadísticas detalladas
python3 src/live_scores_cli.py detailed-stats
```

### Ejemplos de CLI

```bash
# Monitorear 10 minutos con polls cada 30 segundos
python3 src/live_scores_cli.py monitor --duration 600 --interval 30

# Ver estado actual
python3 src/live_scores_cli.py status

# Exportar a archivo
python3 src/live_scores_cli.py export --output scores_2026-01-30.json

# Listar todas las competiciones
python3 src/live_scores_cli.py competitions

# Validar API Key
python3 src/live_scores_cli.py validate-key
```

---

## 📝 Ejemplos

### Ejemplo 1: Monitoreo Simple

```python
from src.football_api_client import FootballDataClient
from src.live_scores import LiveScoresManager, DefaultCallbacks
import time

# Setup
api_key = "tu_api_key"
client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Registrar logs
manager.register_callback(DefaultCallbacks.console_callback)
manager.register_callback(DefaultCallbacks.log_callback)

# Iniciar
print("Iniciando monitoreo...")
manager.start_polling(interval=30)

# Dejar corriendo 5 minutos
try:
    time.sleep(300)
finally:
    manager.stop_polling()
    print("Monitoreo finalizado")
```

### Ejemplo 2: Callbacks Personalizados

```python
from src.live_scores import LiveScoresManager, MatchEvent
from datetime import datetime

def goal_alert(event):
    """Alerta cuando hay gol"""
    if event['type'] in [MatchEvent.GOAL_HOME, MatchEvent.GOAL_AWAY]:
        print(f"\n🚨 ¡¡GOL!! a los {event['minute']} minutos")
        print(f"   {event['home_team']} {event['home_score']}-"
              f"{event['away_score']} {event['away_team']}\n")

def fulltime_alert(event):
    """Alerta al terminar"""
    if event['type'] == MatchEvent.FULLTIME:
        print(f"\n✅ Final: {event['home_team']} "
              f"{event['home_score']}-{event['away_score']} "
              f"{event['away_team']}\n")

manager.register_callback(goal_alert)
manager.register_callback(fulltime_alert)
manager.start_polling()
```

### Ejemplo 3: Exportar Estadísticas

```python
from src.live_scores import LiveScoresManager
from src.football_api_client import FootballDataClient
import json
from datetime import datetime

client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Un poll único
for comp in manager.competitions:
    manager.poll_competition(comp)

# Exportar
data = {
    'timestamp': datetime.now().isoformat(),
    'live_matches': manager.get_live_matches(),
    'statistics': manager.get_statistics(),
}

with open('scores_export.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)

print("✓ Exportado a scores_export.json")
```

### Ejemplo 4: Análisis de Goles

```python
from src.live_scores import LiveScoresManager, MatchEvent
from src.football_api_client import FootballDataClient
import sqlite3
from collections import Counter

client = FootballDataClient(api_key)
manager = LiveScoresManager(client)

# Ejecutar polling por 30 minutos
manager.start_polling()
import time
time.sleep(1800)
manager.stop_polling()

# Analizar datos
conn = sqlite3.connect(manager.db_path)
cursor = conn.cursor()

# Goles por equipo
cursor.execute("""
    SELECT home_team, COUNT(*) as count
    FROM match_events
    WHERE type = 'GOAL_HOME'
    GROUP BY home_team
    ORDER BY count DESC
""")

print("⚽ Goles de equipos locales:")
for team, count in cursor.fetchall():
    print(f"  {team}: {count}")

conn.close()
```

---

## 🐛 Troubleshooting

### Problema: "API Key inválida"

```bash
# Solución 1: Verificar API Key
python3 src/live_scores_cli.py validate-key

# Solución 2: Regenerar desde https://www.football-data.org/client

# Solución 3: Verificar variable de entorno
echo $FOOTBALL_DATA_API_KEY  # Debe mostrar tu key
```

### Problema: "Rate limit exceeded"

```python
# El rate limiting es automático, pero si ocurre:
# 1. Esperar 60 segundos
# 2. Verificar logs
# 3. Revisar get_rate_limit_status()

from src.football_api_client import FootballDataClient
client = FootballDataClient(api_key)
status = client.get_rate_limit_status()
print(f"Espera recomendada: {status['wait_time']}s")
```

### Problema: "Connection refused"

```bash
# Solución: Verificar conexión a Internet
ping api.football-data.org

# O revisar logs
tail -f logs/football_api_client.log
```

### Problema: "No matches found"

```python
# Normal fuera de horarios de partidos
manager = LiveScoresManager(client)
live = manager.get_live_matches()

if not live:
    print("No hay partidos en vivo")
    print("Próximos partidos programados:")
    stats = manager.get_statistics()
    print(f"  Scheduled: {stats['by_status']['SCHEDULED']}")
```

### Problema: "SQLite database is locked"

```bash
# Solución: Cerrar otras conexiones
# Si es persistente, borrar DB y recrear:
rm data/databases/live_scores.db
# Se crea automáticamente en el próximo poll
```

### Revisar Logs

```bash
# Ver logs en tiempo real
tail -f logs/football_api_client.log

# O usar Python
import logging
logging.basicConfig(level=logging.DEBUG)

client = FootballDataClient(api_key)  # Verá logs detallados
```

---

## 📊 Casos de Uso

### 1. Dashboard de Live Scores

```python
# Actualizar sitio web cada 30 segundos
manager.start_polling(interval=30)

# En tu servidor web:
@app.route('/api/live')
def get_live():
    live = manager.get_live_matches()
    return jsonify(live)
```

### 2. Sistema de Alertas

```python
def send_alert(event):
    if event['type'].name == 'GOAL_HOME':
        # Enviar email/SMS/push
        send_email(
            "¡Gol!",
            f"{event['home_team']} anotó a los {event['minute']} min"
        )

manager.register_callback(send_alert)
```

### 3. Análisis de Datos

```python
# Recopilar datos de toda la temporada
manager.start_polling(interval=60)  # Polls cada minuto
# Dejar corriendo 24/7...

# Luego analizar patrones
import pandas as pd
df = pd.read_sql_query(
    "SELECT * FROM match_events",
    conn
)
# ... análisis ...
```

---

## 📚 Referencias

- **API Documentation**: https://www.football-data.org/documentation/api
- **Rate Limiting**: https://en.wikipedia.org/wiki/Leaky_bucket
- **Football-Data Plans**: https://www.football-data.org/client/register

---

**Última actualización**: 30 de Enero 2026
**Versión**: 1.0.0
**Estado**: Producción
