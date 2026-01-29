# ⚽ TIMBA PREDICTOR - Football Match Prediction System

## 📁 Estructura del Proyecto

```
proyecto timba/
│
├── 📂 src/                          # Código fuente principal
│   ├── timba_core.py               # Motor de predicciones (Poisson, cálculos)
│   ├── app.py                      # Interfaz web (Streamlit)
│   └── cli.py                      # Interfaz CLI (línea de comandos)
│
├── 📂 tests/                        # Suite de pruebas
│   ├── test_corners.py             # Validación de mercados de córners
│   ├── test_semaforo.py            # Validación de recomendaciones
│   └── test_sudamerica.py          # Validación de ligas sudamericanas
│
├── 📂 docs/                         # Documentación del proyecto
│   ├── README.md                   # Documentación principal
│   ├── SISTEMA_COMPLETO.md         # Arquitectura y componentes
│   ├── EXPORTACION_EXCEL.md        # Guía: Exportar reportes
│   ├── EXPANSION_SUDAMERICANA.md   # Guía: Brasil y Argentina
│   ├── CAMBIOS_CORNERS.md          # Cambios v2.0
│   ├── v2.1_RELEASE_NOTES.md       # Release notes v2.1
│   ├── COMPARACION_ANTES_DESPUES.md# Delta de cambios
│   ├── RESUMEN_EJECUTIVO.md        # Resumen para stakeholders
│   ├── QUICK_REFERENCE.md          # Guía rápida
│   └── LIMPIEZA_PROYECTO.md        # Histórico de limpieza
│
├── 📂 scripts/                      # Scripts auxiliares
│   ├── run_streamlit.py            # Lanzar app web
│   ├── install_dependencies.sh     # Instalar dependencias
│   └── push_to_github.sh           # Script de push a GitHub
│
├── 📂 config/                       # Configuración
│   └── requirements.txt            # Dependencias Python
│
├── 📂 logs/                         # Registros y estado
│   ├── STATUS.txt                  # Estado del proyecto
│   └── PUSH_GITHUB_LOG.txt         # Histórico de commits
│
├── .gitignore                       # Archivo git ignore mejorado
├── .venv/                           # Virtualenv de Python
├── .git/                            # Repositorio Git
│
└── README.md                        # Este archivo
```

---

## 🚀 Inicio Rápido

### 1. **Instalar Dependencias**
```bash
cd proyecto\ timba
pip install -r config/requirements.txt
```

### 2. **Ejecutar App Web (Streamlit)**
```bash
streamlit run src/app.py
```

O usar el script:
```bash
bash scripts/run_streamlit.py
```

### 3. **Usar CLI**
```bash
python src/cli.py
```

---

## 📊 Estructura del Código

### `src/timba_core.py` (Motor de Predicciones)
- **LIGAS**: Diccionario con 9 ligas (7 europeas + 2 sudamericanas)
- **ALIAS_TEAMS**: Mapeo de 154+ equipos para normalización
- **calcular_fuerzas()**: Calcula métricas de ataque/defensa/córners
- **predecir_partido()**: Genera predicción usando Poisson distribution
- **obtener_proximos_partidos()**: Obtiene fixtures próximas

### `src/app.py` (Interfaz Streamlit)
- Selección de liga y análisis manual
- **Análisis Automático**: Procesa todos los partidos
- **Exportación a Excel**: Genera reportes en XLSX
- Visualización de predicciones con semáforo

### `src/cli.py` (Interfaz CLI)
- Análisis en línea de comandos
- Salida formateada en consola
- Útil para scripts automatizados

---

## 🎯 Características Principales

### v2.0 - Mercados de Córners
- 14 mercados totales (+56% vs v1.5)
- Cálculo de Corners esperados (Poisson)
- Over/Under de córners (8.5, 9.5, 10.5)
- Ganador de Córners (1X2)

### v2.1 - Expansión Sudamericana
- Brasil Série A (30+ equipos)
- Argentina Liga Profesional (25+ equipos)
- Defensiva vs datos faltantes (HC/AC)
- Córners se ocultan inteligentemente

### v2.2 - Exportación Excel
- Recolección automática de datos
- Generación de XLSX en memoria
- 11 campos por predicción
- Botón de descarga en Streamlit

---

## 📈 Mercados Disponibles

### Goles
- Over/Under 1.5, 2.5, 3.5

### Doble Oportunidad
- 1X (Local o Empate)
- X2 (Empate o Visitante)
- 12 (Sin Empate)

### Córners (cuando datos disponibles)
- Over/Under 8.5, 9.5, 10.5
- Ganador Córners (1X2)

### Otros
- BTTS (Ambos marcan)
- Over 2.5
- Eficiencia de tiro
- Goles 2T

---

## 🧪 Tests

### Ejecutar todos los tests
```bash
cd src
python -m pytest ../tests/ -v
```

### Tests específicos
```bash
python ../tests/test_corners.py      # Validar córners
python ../tests/test_semaforo.py     # Validar UI
python ../tests/test_sudamerica.py   # Validar Brasil/Argentina
```

---

## 📦 Dependencias

| Librería | Versión | Uso |
|----------|---------|-----|
| streamlit | latest | Web UI |
| pandas | latest | DataFrames |
| numpy | latest | Cálculos |
| scipy | latest | Poisson distribution |
| requests | latest | HTTP requests |
| openpyxl | latest | Excel generation |

---

## 🔗 Ligas Disponibles

| ID | Liga | País | Fuente |
|----|------|------|--------|
| 1 | Premier League | 🇬🇧 | football-data.co.uk |
| 2 | La Liga | 🇪🇸 | football-data.co.uk |
| 3 | Serie A | 🇮🇹 | football-data.co.uk |
| 4 | Bundesliga | 🇩🇪 | football-data.co.uk |
| 5 | Ligue 1 | 🇫🇷 | football-data.co.uk |
| 6 | Champions League | 🇪🇺 | footballcsv |
| 7 | Europa League | 🇪🇺 | footballcsv |
| 11 | Brasileirão Série A | 🇧🇷 | footballcsv |
| 12 | Liga Profesional Argentina | 🇦🇷 | footballcsv |

---

## 📚 Documentación

Consulta la carpeta `docs/` para:
- **README.md**: Guía completa de uso
- **SISTEMA_COMPLETO.md**: Arquitectura técnica
- **EXPORTACION_EXCEL.md**: Cómo usar exportación
- **EXPANSION_SUDAMERICANA.md**: Detalles Brasil/Argentina
- **QUICK_REFERENCE.md**: Referencia rápida

---

## 🔧 Configuración

### Instalar dependencias
```bash
pip install -r config/requirements.txt
```

### Actualizar dependencias
```bash
pip freeze > config/requirements.txt
```

---

## 📊 Historial de Versiones

- **v1.0**: Predicciones básicas (goles)
- **v2.0**: 14 mercados con córners
- **v2.1**: Expansión Sudamericana (Brasil + Argentina)
- **v2.2**: Exportación a Excel

---

## 🔐 .gitignore Mejorado

El archivo `.gitignore` ahora cubre:
- Python cache (__pycache__, .pyc, venv)
- IDE (.vscode, .idea)
- OS (.DS_Store)
- Logs y temporales
- Archivos Excel generados

---

## 🚀 Próximos Pasos

1. **Más ligas sudamericanas**: Chile, Uruguay, Colombia
2. **Gráficos en Excel**: Visualizaciones automáticas
3. **Base de datos**: Histórico de predicciones
4. **API REST**: Integración con terceros
5. **ML mejorado**: Ajuste dinámico de factores

---

## 💡 Estructura Inspirada en

- Professional Python projects (pip, pytest, sphinx)
- Django (src/ structure)
- FastAPI (config/, docs/)

---

## 📝 Notas

- Código modular y reutilizable
- Documentación completa en `docs/`
- Tests para cada componente mayor
- Scripts auxiliares organizados
- Configuración centralizada

---

**Status**: ✅ **Organizado y Listo para Producción**

Última actualización: 29 de enero de 2026
