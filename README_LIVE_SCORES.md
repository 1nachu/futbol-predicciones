# 🔴 Live Scores Module

**Módulo de Marcadores en Tiempo Real para Football-Data.org**

Proporciona acceso a scores en vivo de fútbol con rate limiting automático, detección de eventos y persistencia en SQLite.

## 🎯 Características Principales

✅ **Cliente HTTP Inteligente**
- Autenticación con X-Auth-Token
- Caché TTL-based
- Retry automático con exponential backoff
- 8 tipos de excepciones específicas

✅ **Rate Limiting (Leaky Bucket)**
- 10 requests/minuto (conforme a API)
- 6 segundos mínimo entre requests
- Token-based refill
- Thread-safe con threading.Lock

✅ **Polling Adaptativo**
- 15 segundos para partidos en VIVO
- 10 minutos para partidos SCHEDULED
- 1 hora para partidos FINISHED
- Detección automática de estado

✅ **Detección de Eventos**
- ⚽ Goles (HOME/AWAY)
- 🔔 Inicio de partido
- 🏁 Final de partido
- ⏸️ Pausas (HALFTIME)
- 🚗 Cambios de estado
- ✂️ Cambios de jugadores
- ❌ Cancelaciones

✅ **Persistencia en SQLite**
- Registro de eventos
- Snapshots de estado
- Histórico de partidos
- Consultas SQL directas

✅ **CLI Profesional**
- `validate-key`: Validar API Key
- `competitions`: Listar competiciones
- `status`: Estado actual
- `monitor`: Monitoreo en vivo
- `export`: Exportar a JSON
- `detailed-stats`: Estadísticas

## 🚀 Inicio Rápido

### 1. Configuración

```bash
# Obtener API Key (gratis)
# https://www.football-data.org/client/register

# Configurar variable de entorno
export FOOTBALL_DATA_API_KEY="tu_clave_aqui"

# O crear archivo .env
echo "FOOTBALL_DATA_API_KEY=tu_clave_aqui" >> .env
```

### 2. Validar Instalación

```bash
# Validar API Key
python3 src/live_scores_cli.py validate-key

# Output esperado:
# ✓ API Key válida
# ✓ Conexión a API exitosa
# Rate Limit: 10 req/60s
# Tokens disponibles: 10.00
```

### 3. Ver Estado Actual

```bash
# Ver partidos en vivo ahora
python3 src/live_scores_cli.py status

# Output:
# ✓ Total de partidos: 12
# ✓ Partidos en vivo: 3
#
# ⚽ PARTIDOS EN VIVO:
#   [PL] Manchester United 2-1 Liverpool (45' minuto)
#   [CL] Barcelona 1-0 PSG (67' minuto)
#   [PD] Real Madrid 0-0 Atletico (25' minuto)
```

### 4. Usar en Python

```python
from src.football_api_client import FootballDataClient
from src.live_scores import LiveScoresManager, DefaultCallbacks

# Crear cliente
client = FootballDataClient("tu_api_key")

# Crear manager
manager = LiveScoresManager(client)

# Registrar callbacks
manager.register_callback(DefaultCallbacks.console_callback)

# Iniciar monitoreo
manager.start_polling(interval=30)  # 30 segundos

# Dejar corriendo...
import time
time.sleep(300)

# Obtener partidos en vivo
live = manager.get_live_matches()
for match in live:
    print(f"{match['home_team']} {match['home_score']}-"
          f"{match['away_score']} {match['away_team']}")

# Detener
manager.stop_polling()
```

## 📚 Documentación

- **[LIVE_SCORES_GUIDE.md](docs/LIVE_SCORES_GUIDE.md)** - Guía completa con ejemplos
- **[examples_live_scores.py](examples_live_scores.py)** - 8 ejemplos prácticos
- **[tests/test_live_scores_integration.py](tests/test_live_scores_integration.py)** - Suite de pruebas

## 📋 Archivos del Módulo

```
src/
├── football_api_client.py      # Cliente HTTP + Rate Limiting
├── live_scores.py              # Manager de polling + eventos
└── live_scores_cli.py          # CLI

tests/
└── test_live_scores_integration.py  # Pruebas

examples_live_scores.py         # 8 ejemplos prácticos
```

## 🔧 Comandos CLI

### Validar Configuración

```bash
python3 src/live_scores_cli.py validate-key
```

Valida API Key y conexión a Football-Data.org

### Listar Competiciones

```bash
python3 src/live_scores_cli.py competitions
```

Muestra todas las competiciones disponibles

### Ver Estado Actual

```bash
python3 src/live_scores_cli.py status
```

Estadísticas en tiempo real:
- Total de partidos
- Partidos en vivo
- Distribución por estado
- Rate limit disponible

### Monitorear Scores

```bash
python3 src/live_scores_cli.py monitor [--duration 300] [--interval 30]
```

**Opciones:**
- `--duration`: Duración en segundos (default: 300)
- `--interval`: Intervalo entre polls en segundos (default: 30)

Ejemplo: Monitorear 10 minutos con updates cada 30s

```bash
python3 src/live_scores_cli.py monitor --duration 600 --interval 30
```

### Exportar Datos

```bash
python3 src/live_scores_cli.py export [--output archivo.json]
```

Exporta scores actuales a JSON

### Estadísticas Detalladas

```bash
python3 src/live_scores_cli.py detailed-stats
```

Estadísticas por competición

## 💻 API de Programación

### FootballDataClient

Cliente HTTP para Football-Data.org

```python
from src.football_api_client import FootballDataClient

client = FootballDataClient(api_key)

# Obtener competiciones
competitions = client.get_competitions()

# Obtener partidos de una liga
matches = client.get_matches('PL')

# Obtener solo partidos en vivo
live = client.get_live_matches()

# Obtener partidos de una competición
matches = client.get_competition_matches('CL')

# Ver rate limit
status = client.get_rate_limit_status()
```

### LiveScoresManager

Gestor de monitoreo continuo

```python
from src.live_scores import LiveScoresManager

manager = LiveScoresManager(client)

# Iniciar polling en background
manager.start_polling(interval=30)

# Obtener partidos en vivo
live = manager.get_live_matches()

# Obtener estadísticas
stats = manager.get_statistics()

# Registrar callbacks para eventos
def on_goal(event):
    print(f"¡Gol! {event['home_team']}")

manager.register_callback(on_goal)

# Detener polling
manager.stop_polling()
```

## 🎯 Casos de Uso

### 1. Dashboard Web

```python
# En servidor Flask/FastAPI
from src.live_scores import LiveScoresManager

manager = LiveScoresManager(client)
manager.start_polling(interval=30)

@app.route('/api/live')
def get_live():
    return manager.get_live_matches()
```

### 2. Alertas en Tiempo Real

```python
def send_email_alert(event):
    if event['type'].name == 'GOAL_HOME':
        send_email(f"¡Gol de {event['home_team']}!")

manager.register_callback(send_email_alert)
```

### 3. Análisis de Datos

```python
# Recopilar datos de jornadas completas
manager.start_polling()  # Dejar 24/7

# Luego consultar SQLite
import sqlite3
conn = sqlite3.connect('data/databases/live_scores.db')

# Goles por equipo
cursor = conn.execute("""
    SELECT home_team, COUNT(*) as goals
    FROM match_events
    WHERE type = 'GOAL_HOME'
    GROUP BY home_team
""")
```

## 📊 Estructura de Datos

### MatchSnapshot

```python
@dataclass
class MatchSnapshot:
    match_id: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str  # LIVE, SCHEDULED, FINISHED, PAUSED, etc
    minute: int  # Minuto del partido
    timestamp: datetime
```

### Event

```python
event = {
    'type': MatchEvent.GOAL_HOME,  # Tipo de evento
    'match_id': 123,
    'home_team': 'Manchester United',
    'away_team': 'Liverpool',
    'home_score': 2,
    'away_score': 1,
    'minute': 45,
    'timestamp': datetime.now(),
}
```

## 🔒 Rate Limiting

Football-Data.org permite **10 requests/minuto**

El módulo implementa automáticamente:

- ✅ **Leaky Bucket Algorithm**: Token-based
- ✅ **6-second minimum**: Entre requests
- ✅ **Exponential backoff**: En reintentos
- ✅ **Thread-safe**: Con threading.Lock

No necesitas hacer nada - está incluido!

## 🐛 Solución de Problemas

### API Key inválida

```bash
python3 src/live_scores_cli.py validate-key
```

Obtener nueva key: https://www.football-data.org/client

### Rate limit excedido

Espera 60 segundos - el módulo maneja automáticamente

### No hay partidos en vivo

Es normal fuera de horarios. Ver próximos:

```bash
python3 src/live_scores_cli.py status
```

### Revisar logs

```bash
tail -f logs/football_api_client.log
```

## 📈 Ejemplos

### Ejemplo 1: Monitoreo Simple

```bash
python3 examples_live_scores.py
# Opción 1: Validación y estado
# Muestra API Key válida y conexión
```

### Ejemplo 2: Callbacks

```bash
python3 examples_live_scores.py
# Opción 4: Monitoreo con callbacks
# Alertas cuando marcan goles
```

### Ejemplo 3: Estadísticas

```bash
python3 examples_live_scores.py
# Opción 7: Análisis de datos
# Top goleadores, estadísticas, etc
```

## 🧪 Pruebas

```bash
# Ejecutar todas las pruebas
python3 -m pytest tests/test_live_scores_integration.py -v

# O con unittest
python3 tests/test_live_scores_integration.py
```

## 📦 Dependencias

- `requests>=2.31.0`: HTTP client
- `python-dateutil>=2.8.0`: Date parsing
- `pytz>=2023.3`: Timezone support

## 📞 Soporte

**Documentación oficial:** https://www.football-data.org/documentation/api

**Planes y límites:** https://www.football-data.org/client

## 📝 Notas

- El plan **FREE** permite 10 requests/minuto
- Para planes superiores, cambiar `LeakyBucket(capacity=...)` en `football_api_client.py`
- Todos los datos se guardan en `data/databases/live_scores.db`
- Los logs se guardan en `logs/football_api_client.log`

## 📄 Licencia

MIT - Uso libre para propósitos comerciales y privados

---

**Creado por:** Backend Integration Team
**Versión:** 1.0.0
**Última actualización:** 30 de Enero 2026
