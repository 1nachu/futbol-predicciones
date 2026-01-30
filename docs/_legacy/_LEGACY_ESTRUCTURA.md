# 📁 Estructura del Proyecto - Índice Completo

## 🏗️ Organización de Directorios

```
proyecto timba/
│
├── 📂 src/                          # CÓDIGO FUENTE
│   ├── timba_core.py              # Motor de predicciones (625+ líneas)
│   │   ├── LIGAS (9 ligas)
│   │   ├── ALIAS_TEAMS (150+ equipos)
│   │   ├── calcular_fuerzas()
│   │   ├── predecir_partido()
│   │   ├── obtener_proximos_partidos()
│   │   └── descargar_csv_safe()
│   │
│   ├── app.py                     # Interfaz Streamlit (540+ líneas)
│   │   ├── Selección de liga
│   │   ├── Predicción manual
│   │   ├── Análisis automático
│   │   ├── Exportación Excel
│   │   └── Visualizaciones
│   │
│   └── cli.py                     # Interfaz CLI (240+ líneas)
│       ├── Análisis por liga
│       ├── Selección de partidos
│       └── Salida en consola
│
├── 📂 tests/                        # PRUEBAS UNITARIAS
│   ├── test_corners.py            # Validación de mercados de córners
│   ├── test_semaforo.py           # Validación de recomendaciones
│   └── test_sudamerica.py         # Validación de Brasil/Argentina
│
├── 📂 docs/                         # DOCUMENTACIÓN (10 archivos, 1500+ líneas)
│   ├── README.md                  # Documentación principal (325+ líneas)
│   ├── SISTEMA_COMPLETO.md        # Arquitectura técnica (400+ líneas)
│   ├── EXPORTACION_EXCEL.md       # Guía de exportación (200+ líneas)
│   ├── EXPANSION_SUDAMERICANA.md  # Detalles técnicos Brasil/Argentina
│   ├── CAMBIOS_CORNERS.md         # Cambios v2.0
│   ├── v2.1_RELEASE_NOTES.md      # Release notes v2.1
│   ├── COMPARACION_ANTES_DESPUES.md # Delta de cambios
│   ├── RESUMEN_EJECUTIVO.md       # Resumen para stakeholders
│   ├── QUICK_REFERENCE.md         # Referencia rápida
│   └── LIMPIEZA_PROYECTO.md       # Histórico de limpieza
│
├── 📂 scripts/                      # SCRIPTS AUXILIARES
│   ├── run_streamlit.py           # Lanzar app (simplificado)
│   ├── install_dependencies.sh    # Instalación de deps
│   └── push_to_github.sh          # Push a GitHub
│
├── 📂 config/                       # CONFIGURACIÓN
│   └── requirements.txt           # Dependencias Python (6 paquetes)
│
├── 📂 logs/                         # REGISTROS
│   ├── STATUS.txt                 # Estado actual del proyecto
│   └── PUSH_GITHUB_LOG.txt        # Histórico de commits
│
├── 📂 .venv/                        # VIRTUALENV (Python 3.12)
│   └── (ambiente aislado de Python)
│
├── 📂 .git/                         # REPOSITORIO GIT
│   └── (historial de commits)
│
├── 🔧 .gitignore                    # Archivo ignore mejorado
│   └── (excluye __pycache__, *.pyc, logs, xlsx, etc.)
│
├── 📖 README.md                     # Índice principal (este archivo)
├── 🛠️ utils.sh                      # Script de utilidades (nuevo)
│
└── 📊 TREE VISUAL (tú estás aquí)
    └── Guía de estructura completa

```

---

## 📋 Contenido Detallado de Cada Carpeta

### `src/` - Código Fuente

**timba_core.py** (625 líneas)
- Diccionario LIGAS (9 ligas: 7 europeas + Brasil + Argentina)
- Diccionario URLS_FIXTURE (URLs de fixtures)
- Diccionario ALIAS_TEAMS (150+ equipos mapeados)
- Función normalizar_csv() - Normaliza columnas CSV
- Función descargar_csv_safe() - Descarga con fallback
- Función obtener_proximos_partidos() - Obtiene fixtures próximas
- Función emparejar_equipo() - Normaliza nombres de equipos
- Función calcular_fuerzas() - Calcula métricas atacantes/defensivas/córners
- Función predecir_partido() - Genera predicción con Poisson
- Función obtener_h2h() - Historial entre equipos

**app.py** (540 líneas)
- Configuración Streamlit
- Sidebar con selección de liga
- Pestaña 1: Predicción Manual
  - Seleccionar local/visitante
  - Mostrar predicción detallada
  - Métricas y probabilidades
  - H2H histórico
- Pestaña 2: Análisis Automático
  - Obtener fixtures próximas
  - Procesar todos los partidos
  - Mostrar predicciones
  - **NUEVO**: Exportar a Excel
- Funciones auxiliares:
  - mostrar_recomendaciones_semaforo()
  - mostrar_prediccion_streamlit()

**cli.py** (240 líneas)
- Menú interactivo en consola
- Análisis por liga
- Análisis de próxima fecha
- Selección de partidos
- Salida formateada

---

### `tests/` - Pruebas Unitarias

**test_corners.py**
- Validación del cálculo de córners
- Test de Over/Under
- Test de Ganador de Córners

**test_semaforo.py**
- Validación de recomendaciones
- Test de colores/emojis
- Test de lógica de probabilidades

**test_sudamerica.py**
- Test con CSVs sin HC/AC
- Validación defensiva
- Test de ALIAS_TEAMS sudamericanos

---

### `docs/` - Documentación Completa

| Archivo | Líneas | Contenido |
|---------|--------|----------|
| README.md | 325 | Guía completa, inicio rápido, características |
| SISTEMA_COMPLETO.md | 400 | Arquitectura, componentes, flujo |
| EXPORTACION_EXCEL.md | 200 | Guía de exportación, casos de uso |
| EXPANSION_SUDAMERICANA.md | 250 | Detalles Brasil/Argentina |
| CAMBIOS_CORNERS.md | 150 | Cambios introducidos v2.0 |
| v2.1_RELEASE_NOTES.md | 250 | Release notes v2.1 |
| COMPARACION_ANTES_DESPUES.md | 200 | Delta de cambios |
| RESUMEN_EJECUTIVO.md | 150 | Resumen ejecutivo |
| QUICK_REFERENCE.md | 100 | Referencia rápida |
| LIMPIEZA_PROYECTO.md | 50 | Histórico de limpieza |

**Total**: 1500+ líneas de documentación

---

### `scripts/` - Scripts Auxiliares

**run_streamlit.py**
```python
#!/usr/bin/env python3
import subprocess
subprocess.run(['streamlit', 'run', 'src/app.py'])
```

**install_dependencies.sh**
```bash
pip install -r config/requirements.txt
```

**push_to_github.sh**
```bash
git add -A
git commit -m "mensaje"
git push origin main
```

---

### `config/` - Configuración

**requirements.txt** (6 dependencias)
```
streamlit       # Web UI
pandas          # DataFrames
numpy           # Cálculos
scipy           # Poisson distribution
requests        # HTTP
openpyxl        # Excel generation
```

---

### `logs/` - Registros

**STATUS.txt**
- Estado actual del proyecto
- Versión actual
- Funcionalidades completadas

**PUSH_GITHUB_LOG.txt**
- Historial de commits
- Hashes de commits
- Mensajes de commit

---

## 🎯 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Líneas de código** | 1400+ |
| **Líneas de documentación** | 1500+ |
| **Funciones principales** | 15+ |
| **Ligas soportadas** | 9 |
| **Equipos mapeados** | 150+ |
| **Mercados disponibles** | 14+ |
| **Tests** | 3+ suites |
| **Versión actual** | 2.2 |

---

## 🔧 Nuevo: Script de Utilidades (utils.sh)

Facilita operaciones comunes:

```bash
./utils.sh init                # Inicializar proyecto
./utils.sh app                 # Ejecutar app web
./utils.sh cli                 # Ejecutar CLI
./utils.sh test                # Ejecutar tests
./utils.sh clean               # Limpiar temporales
./utils.sh deps                # Actualizar dependencias
./utils.sh status              # Ver estado del proyecto
./utils.sh help                # Ver ayuda
```

---

## 📝 Cómo Usar Cada Carpeta

### Para **Desarrollador**:
1. `src/` - Modificar código
2. `tests/` - Escribir tests
3. `.gitignore` - Excluir archivos

### Para **Usuario**:
1. `README.md` - Leer documentación
2. `scripts/` - Ejecutar app/cli
3. `config/requirements.txt` - Instalar dependencias

### Para **DevOps/Deployment**:
1. `config/` - Actualizar dependencias
2. `scripts/` - Scripts de automatización
3. `logs/` - Monitorear estado

---

## ✅ Ventajas de Esta Estructura

✅ **Modular**: Cada carpeta tiene propósito claro  
✅ **Escalable**: Fácil agregar nuevas funciones  
✅ **Mantenible**: Código y docs bien organizados  
✅ **Profesional**: Sigue estándares de Python  
✅ **Documentado**: 1500+ líneas de docs  
✅ **Testeado**: Suite completa de tests  
✅ **Automatizado**: Scripts para tareas comunes  

---

## 🔄 Actualizar Estructura

Si necesitas:
- **Agregar módulo**: Crear archivo en `src/`
- **Agregar test**: Crear archivo en `tests/`
- **Agregar doc**: Crear archivo en `docs/`
- **Agregar script**: Crear en `scripts/`

---

**Status**: ✅ **Estructura Organizada y Profesional**

Última actualización: 29 de enero de 2026
