# Implementación de API-Football v3

## ✅ Configuración Completada

**Fecha:** 30 de Enero de 2026  
**API Key:** Configurada ✓  
**Estado:** Listo para usar

---

## 📋 Qué se Implementó

### 1. Archivo `.env` Creado
```ini
# .env
API_FOOTBALL_KEY=dd12ead2b9a57c36c4af891c5947c5ec
API_FOOTBALL_DB_PATH=data/databases/api_football_cache.db
LOG_LEVEL=INFO
```

**Ubicación:** `/home/nahuel/Documentos/projecto timba/.env`

### 2. Script de Setup Python (`setup_api.py`)
```python
python3 setup_api.py
```

**Funcionalidades:**
- ✓ Carga variables desde `.env`
- ✓ Valida configuración
- ✓ Inicializa Timba Core
- ✓ Verifica cuota de API
- ✓ Crea directorios necesarios

**Salida:**
```
✅ Configuración validada correctamente
✓ Cliente API-Football conectado
✓ Cuota de API disponible
```

### 3. Script de Setup Bash (`setup_env.sh`)
```bash
source setup_env.sh
# o
bash setup_env.sh
```

**Funcionalidades:**
- ✓ Carga `.env` automáticamente
- ✓ Exporta variables de ambiente
- ✓ Crea directorios (logs, data)
- ✓ Configura PYTHONPATH

---

## 🚀 Cómo Usar

### Opción 1: Setup Automático (Recomendado)
```bash
# Ejecutar setup
python3 setup_api.py

# Luego usar normalmente
streamlit run src/app.py
python3 src/cli.py
```

### Opción 2: Setup Manual
```bash
# Cargar variables
source setup_env.sh

# Ejecutar aplicaciones
streamlit run src/app.py
```

### Opción 3: En Python
```python
from timba_core import inicializar_timba_core, obtener_timba_core

# Inicializar
timba_core = inicializar_timba_core()

# Ahora acceder a API-Football
fixtures = timba_core.fetch_daily_fixtures(league_id=39, season=2026)
quota = timba_core.get_quota_status()
```

---

## 📊 Información de la API Key

**Proveedor:** API-Football v3  
**Plan:** STARTER (100 llamadas/día)  
**Base URL:** `https://v3.football.data-api.com`  
**Autenticación:** Header `x-apisports-key`

### Límites Disponibles
- **Llamadas diarias:** 100
- **Fixtures:** 1 llamada cada 24 horas
- **Predicciones:** 1 llamada por partido (30 min antes)
- **Status:** Gratuito (no cuenta en cuota)

---

## 🔍 Validación

**Estado de la API Key:**
```
✓ Longitud válida: 32 caracteres (hexadecimal)
✓ Formato correcto: dd12ead2b9a57c36c4af891c5947c5ec
✓ Cliente inicializado correctamente
✓ Caché SQLite operativo
✓ Logs configurados
```

**Logs de inicialización:**
```
2026-01-30 16:02:12 - Cliente API-Football inicializado
2026-01-30 16:02:12 - ✓ Timba Core API inicializado correctamente
2026-01-30 16:02:12 - Cliente API-Football conectado
```

---

## 📁 Estructura de Archivos

```
projecto timba/
├── .env                          ← API Key y configuración
├── setup_api.py                  ← Setup Python (validación)
├── setup_env.sh                  ← Setup Bash (ambiente)
├── src/
│   ├── timba_core.py             ← Core con API integrada
│   ├── app.py                    ← App con timba_core
│   ├── cli.py                    ← CLI con timba_core
│   └── ...
├── data/
│   └── databases/
│       └── api_football_cache.db ← Caché SQLite
├── logs/
│   ├── timba_core_api.log        ← Logs de API
│   ├── app.log                   ← Logs de app
│   └── cli.log                   ← Logs de CLI
└── docs/
    ├── CENTRALIZACION_API_TIMBA_CORE.md
    └── ...
```

---

## 🔐 Seguridad

### Protección de la API Key
- ✓ Almacenada en `.env` (no en git)
- ✓ Agregado a `.gitignore`
- ✓ No mostrada en logs (solo primeros y últimos 8 chars)
- ✓ Cargada automáticamente desde ambiente

### Revisar .gitignore
```bash
grep ".env" .gitignore  # Debe incluir .env
```

---

## 🎯 Funcionalidades Disponibles

Con la API Key configurada, ahora tienes acceso a:

### 1. Obtener Fixtures Diarios
```python
fixtures = timba_core.fetch_daily_fixtures(league_id=39, season=2026)
# Retorna lista de MatchFixture
```

### 2. Obtener Predicciones
```python
prediction = timba_core.fetch_prediction(match_id=123456)
# Retorna MatchPrediction con probabilidades
```

### 3. Agendar Predicciones
```python
timba_core.schedule_predictions(fixtures)
# Automáticamente 30 min antes del inicio
```

### 4. Verificar Cuota
```python
quota = timba_core.get_quota_status()
print(f"Cuota disponible: {quota.requests_available}/100")
print(f"Plan: {quota.plan_name}")
```

### 5. Obtener Uso del Día
```python
uso_hoy = timba_core.get_usage_today()
print(f"Llamadas usadas hoy: {uso_hoy}")
```

---

## 📝 Ejemplos Rápidos

### Ejemplo 1: Carga Simple
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from timba_core import inicializar_timba_core

# Cargar y validar
timba_core = inicializar_timba_core()
print("✓ Timba Core inicializado")

# Verificar cuota
quota = timba_core.get_quota_status()
print(f"✓ Cuota disponible: {quota.requests_available}")
```

### Ejemplo 2: Obtener Fixtures
```python
# Obtener fixtures del día
fixtures = timba_core.fetch_daily_fixtures(
    league_id=39,  # Premier League
    season=2026
)

for fixture in fixtures[:5]:  # Primeros 5
    print(f"{fixture.home_team} vs {fixture.away_team}")
    print(f"  Hora: {fixture.date}")
    print(f"  Status: {fixture.status}")
```

### Ejemplo 3: Predicción + Features
```python
# Obtener predicción
prediction = timba_core.fetch_prediction(match_id=123456)

if prediction:
    # Extraer features
    features = timba_core.extract_ml_features(123456, prediction)
    
    print(f"Predicción: {features.prediction_label}")
    print(f"Confianza: {features.prediction_confidence:.2%}")
    print(f"Prob Local: {features.home_win_prob:.2%}")
    print(f"Prob Empate: {features.draw_prob:.2%}")
    print(f"Prob Visitante: {features.away_win_prob:.2%}")
```

---

## 🔄 Workflow Recomendado

```
1. Setup Inicial (una vez)
   python3 setup_api.py
   
2. Desarrollo
   - Usar timba_core en app.py
   - Usar timba_core en cli.py
   - Usar timba_core en scripts personalizados
   
3. Monitoreo
   - Revisar logs en logs/timba_core_api.log
   - Verificar cuota con timba_core.get_quota_status()
   - Revisar caché en data/databases/api_football_cache.db
   
4. Producción
   - Asegurar que .env está seguro
   - Monitorear cuota diaria
   - Alertas si cuota < 10 llamadas
```

---

## 🚨 Resolución de Problemas

### Problema: "API_FOOTBALL_KEY no configurada"
**Solución:**
```bash
# Verificar .env existe
ls -la .env

# Ejecutar setup
python3 setup_api.py

# O cargar manualmente
export API_FOOTBALL_KEY=dd12ead2b9a57c36c4af891c5947c5ec
```

### Problema: "Error verificando cuota"
**Causas posibles:**
- Sin conexión a internet
- API Key inválida
- Límite de reintentos agotado

**Solución:**
- Verificar conexión: `ping google.com`
- Verificar API Key: `echo $API_FOOTBALL_KEY`
- Revisar logs: `tail -f logs/timba_core_api.log`

### Problema: "SQLite database is locked"
**Solución:**
```bash
# Eliminar caché y recrear
rm data/databases/api_football_cache.db
python3 setup_api.py
```

---

## 📚 Documentación Relacionada

- [CENTRALIZACION_API_TIMBA_CORE.md](CENTRALIZACION_API_TIMBA_CORE.md)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- [SISTEMA_COMPLETO.md](SISTEMA_COMPLETO.md)

---

## ✨ Beneficios

✅ **Centralizado**: Un único punto de acceso a API-Football  
✅ **Cacheado**: SQLite para minimizar llamadas  
✅ **Thread-safe**: Seguro para concurrencia  
✅ **Logging**: Auditoría completa de operaciones  
✅ **Flexible**: Modo degradado sin API Key  
✅ **Documentado**: Ejemplos y guías disponibles

---

**Autor:** Backend Integration Team  
**Versión:** 2.2.0  
**Última Actualización:** 30 de Enero de 2026
