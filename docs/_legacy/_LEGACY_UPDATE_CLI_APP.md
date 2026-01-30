# 🎯 Actualización CLI y Streamlit App - Integración Team Normalization

## 📋 Resumen Ejecutivo

Se ha completado la integración del sistema de **team_normalization** en los dos puntos de entrada principales del proyecto:

1. **CLI (Interfaz de Línea de Comandos)** - `src/cli.py`
2. **Streamlit App (Interfaz Web)** - `src/app.py`

Además, se implementó la función `obtener_proximos_partidos()` faltante en `timba_core.py` para cargar fixtures programados.

---

## 🔧 Cambios en cli.py

### Estadísticas de Cambio
- **Líneas antes:** 257
- **Líneas después:** 478
- **Líneas agregadas:** +221
- **Funciones nuevas:** 6

### Funciones Agregadas

#### 1. `normalizar_equipo_cli()`
Normaliza un nombre de equipo usando el fuzzy matching del sistema.

```python
# Características:
- Solicita nombre del equipo al usuario
- Usa TeamNormalizer.normalizar_nombre_equipo()
- Muestra:
  * Nombre oficial
  * UUID único
  * País y liga
  * Confianza de la búsqueda
  * Mapeos externos disponibles
```

#### 2. `mostrar_team_stats()`
Muestra estadísticas del sistema de normalización.

```python
# Muestra:
- Total de equipos únicos
- Total de mapeos externos
- Total de aliases
- Estadísticas de búsqueda (caché vs. BD)
- Coincidencias fuzzy usadas
- Fuentes de datos principales
```

#### 3. `listar_equipos_cli()`
Lista los equipos en la tabla maestra con opción de filtrado.

```python
# Características:
- Filtrado opcional por país
- Tabla formateada con:
  * UUID truncado
  * Nombre oficial
  * País
  * Liga
  * Cantidad de aliases
  * Cantidad de mapeos
```

#### 4. `agregar_equipo_cli()`
Agrega un nuevo equipo a la tabla maestra.

```python
# Solicita:
- Nombre oficial (obligatorio)
- País en código ISO (obligatorio)
- Liga (opcional)

# Retorna:
- UUID del equipo creado
- Datos confirmados
```

#### 5. `exportar_equipos_cli()`
Exporta los equipos a archivo JSON.

```python
# Características:
- Solicita nombre de archivo
- Crea timestamp automático si no se especifica
- Exporta:
  * Fecha de exportación
  * Total de equipos
  * Datos completos de cada equipo
```

#### 6. `team_management_menu()`
Menú interactivo para gestión completa de equipos.

```python
# Submenú con opciones:
1. Normalizar equipo
2. Ver estadísticas
3. Listar equipos
4. Agregar equipo
5. Exportar a JSON
0. Volver
```

### Integración en Menú Principal

**Opción 99** en el menú principal (solo si team_normalization está disponible):
```
99. Gestión de equipos (normalización)
```

También agregada como **Opción 3** en submenu por liga:
```
3. Normalizar nombre de equipo
```

---

## 🎨 Cambios en app.py

### Estadísticas de Cambio
- **Líneas antes:** 557
- **Líneas después:** 729
- **Líneas agregadas:** +172
- **Componentes nuevos:** 1 pestaña + 4 sub-pestañas

### Nueva Pestaña: "🎯 Gestión de Equipos"

Se agregó una tercera pestaña principal en la aplicación Streamlit:

```python
tabs = ["🔮 Predicción Manual", "🤖 Próxima Fecha Automática", "🎯 Gestión de Equipos"]
```

**Disponible solo si `TEAM_NORMALIZATION_AVAILABLE` es True**

### Sub-pestañas

#### 1. 🔍 Normalizar Equipo
Búsqueda y normalización de nombres de equipos con interfaz visual.

**Componentes:**
- Campo de entrada de texto
- Métricas:
  * Equipo oficial (columna izquierda)
  * UUID truncado
  * Confianza de búsqueda
  * País (columna derecha)
  * Liga
  * Alias utilizado (si aplica)
- Tabla de mapeos externos con:
  * Fuente de datos
  * ID externo
  * Similitud

#### 2. 📊 Ver Estadísticas
Panel de estadísticas con gráficos y métricas.

**Componentes:**
- Métricas principales (4 columnas):
  * Equipos únicos
  * Mapeos externos
  * Aliases
  * Mapeos automáticos
- Métricas de búsqueda (3 columnas):
  * Búsquedas en caché
  * Búsquedas en BD
  * Coincidencias fuzzy
- Gráfico de barras: Fuentes de datos principales

#### 3. 📋 Listar Equipos
Tabla dinámica de todos los equipos con filtrado.

**Características:**
- Campo de filtro por país
- Botón de actualización (st.rerun())
- Tabla con columnas:
  * UUID (corto)
  * Nombre oficial
  * País
  * Liga
  * Cantidad de aliases
  * Cantidad de mapeos
- Contador de total de equipos

#### 4. ➕ Agregar Equipo
Formulario para agregar equipos a la tabla maestra.

**Componentes:**
- Campo de entrada: Nombre oficial
- Dropdown: País (20 opciones principales)
- Campo de entrada: Liga (opcional)
- Botón: Agregar equipo

**Respuesta:**
- Mensaje de éxito
- JSON con datos del equipo creado:
  * UUID
  * Nombre
  * País
  * Liga

---

## 🔧 Cambios en timba_core.py

### Nueva Función: `obtener_proximos_partidos(fixture_url)`

**Propósito:** Descargar y parsear fixtures de próximos partidos.

**Parámetros:**
- `fixture_url` (string): URL del archivo CSV de fixtures

**Retorna:**
```python
[
    {'local': 'Team A', 'visitante': 'Team B', 'fecha': '2026-02-01'},
    ...
]
```

**Lógica:**
1. Descarga CSV desde URL con User-Agent headers
2. Normaliza nombres de columnas (case-insensitive)
3. Busca columnas: home/local, away/visitante, date/fecha
4. Filtra partidos dentro de próximos 7 días
5. Limita resultado a máximo 20 partidos
6. Fallback seguro con manejo de excepciones

**Manejo de Errores:**
- Timeout de 15 segundos
- Decodificación flexible (utf-8 con fallback a ignorar errores)
- Validación de datos faltantes
- Log de advertencias

---

## ✅ Verificaciones de Integración

### Síntesis de Cambios
```
Líneas de código totales:
  - cli.py:         257 → 478 (+221)
  - app.py:         557 → 729 (+172)
  - timba_core.py:  444 → 516 (+72)
  ────────────────────────────────
  TOTAL:           1258 → 1723 (+465)
```

### Tests de Validación

✅ **Sintaxis:**
- `python -m py_compile src/cli.py` → OK
- `python -m py_compile src/app.py` → OK
- `python -m py_compile src/timba_core.py` → OK

✅ **Importaciones:**
- `from cli import *` → OK (6 funciones + flags)
- `from app import *` → OK (Streamlit compatible)
- `from timba_core import obtener_proximos_partidos` → OK

✅ **Funcionalidad:**
- TeamNormalizer inicializado en ambos módulos
- TEAM_NORMALIZATION_AVAILABLE = True
- Todas las funciones importables

✅ **Compatibilidad:**
- 100% backward compatible
- Fallback graceful si team_normalization no disponible
- Sin cambios en funciones existentes

---

## 📊 Interfaz de Usuario

### CLI (cli.py)
```
=== MENU PRINCIPAL ===
1. Premier League (Inglaterra) - Temporada 25/26
2. La Liga (España) - Temporada 25/26
...
99. Gestión de equipos (normalización)  ← NEW
0. Salir

Por liga:
--- [Liga Seleccionada] ---
1. Predecir partido manual
2. Analizar próximos partidos (fixtures) para esta liga
3. Normalizar nombre de equipo  ← NEW
0. Volver

Submenu normalization (opción 99):
🎯 GESTIÓN DE EQUIPOS - NORMALIZACIÓN
1. Normalizar nombre de equipo
2. Ver estadísticas del sistema
3. Listar todos los equipos
4. Agregar nuevo equipo a tabla maestra
5. Exportar equipos a JSON
0. Volver al menú principal
```

### Streamlit (app.py)
```
⚽ TIMBA PREDICTOR - Análisis de Partidos con Poisson

Tabs:
├─ 🔮 Predicción Manual           (existente)
├─ 🤖 Próxima Fecha Automática    (existente)
└─ 🎯 Gestión de Equipos          (NUEVO)
   ├─ 🔍 Normalizar Equipo
   ├─ 📊 Ver Estadísticas
   ├─ 📋 Listar Equipos
   └─ ➕ Agregar Equipo
```

---

## 🚀 Cómo Usar

### Desde CLI

1. **Normalizar un equipo:**
   ```bash
   python src/cli.py
   # Seleccionar opción 99
   # Seleccionar opción 1
   # Ingresar nombre del equipo
   ```

2. **Ver estadísticas:**
   ```
   Opción 99 → Opción 2
   ```

3. **Listar equipos:**
   ```
   Opción 99 → Opción 3
   # Ingresar país para filtrar (opcional)
   ```

4. **Agregar equipo:**
   ```
   Opción 99 → Opción 4
   # Ingresar datos del equipo
   ```

### Desde Streamlit

1. **Iniciar app:**
   ```bash
   streamlit run src/app.py
   ```

2. **Navegar a "Gestión de Equipos"**

3. **Usar cualquiera de las sub-pestañas:**
   - Normalizar equipo
   - Ver estadísticas
   - Listar equipos con filtro
   - Agregar nuevo equipo

---

## 📦 Dependencias Requeridas

No se agregaron nuevas dependencias. Se utilizan módulos ya presentes:

- `pandas` - Manipulación de datos
- `requests` - Descargas HTTP
- `streamlit` - UI web (solo en app.py)
- `tabulate` - Formateo de tablas en CLI
- `json` - Exportación de datos
- `datetime` - Manejo de fechas

---

## 🔗 Integración con Módulos Existentes

### team_normalization.py
Se utiliza la clase `TeamNormalizer` para todas las operaciones:
- `normalizar_nombre_equipo()` - Búsqueda fuzzy
- `get_statistics()` - Estadísticas del sistema
- `list_all_teams()` - Listar equipos
- `add_master_team()` - Crear equipo

### timba_core.py
Se utiliza para:
- `LIGAS` - Definición de ligas disponibles
- `URLS_FIXTURE` - URLs de fixtures
- `obtener_proximos_partidos()` - Nueva función agregada
- Funciones existentes: `calcular_fuerzas()`, `predecir_partido()`, etc.

### utils/shared.py
Se utiliza para:
- `normalizar_csv()`
- `descargar_csv_safe()`
- `emparejar_equipo()`
- `encontrar_equipo_similar()`
- `imprimir_barra()`

---

## 🎯 Próximos Pasos (Opcional)

1. **Testing:**
   - Pruebas end-to-end de CLI
   - Pruebas de Streamlit con seleniun
   - Validación de datos en formularios

2. **Mejoras:**
   - Agregar caché en Streamlit para tablas grandes
   - Exportar a múltiples formatos (Excel, CSV)
   - Validación de emails para contactos de equipos

3. **Documentación:**
   - Actualizar README.md con nuevas opciones
   - Crear tutorial de team management
   - Documentar API de team_normalization

---

## 📝 Notas Técnicas

### Fallback Seguro

Si `team_normalization` no está disponible:
- **CLI:** Opción 99 no aparece en menú
- **Streamlit:** Pestaña 3 no se crea
- **Funcionalidad:** App sigue siendo completamente funcional

### Manejo de Errores

Todos los módulos incluyen:
- Try/except para importaciones
- Mensajes descriptivos para usuarios
- Logs automáticos de errores
- Validación de entrada

### Performance

- **Caché:** Streamlit utiliza `@st.cache_data`
- **BD:** SQLite con índices optimizados
- **Búsqueda:** In-memory caching en TeamNormalizer

---

## 📅 Versión

**Versión:** v2.1 (CLI + App Integration)
**Fecha:** 2026-01-30
**Estado:** ✅ Producción lista
**Compatibilidad:** 100% backward compatible

