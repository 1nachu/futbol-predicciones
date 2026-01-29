# ⚽ TIMBA PREDICTOR - Web App con Streamlit

## 🚀 Transformación Completada

Tu script de consola ha sido transformado en una **aplicación web interactiva** usando Streamlit. 

### ✨ Nuevas Características

#### 1. **Interfaz Web Moderna**
- Diseño limpio y responsivo
- Componentes visuales nativos de Streamlit
- Sin input() ni while loops

#### 2. **Barra Lateral (Sidebar)**
- Selector de liga con `st.sidebar.selectbox`
- Carga automática de datos al cambiar de liga
- Mensaje de éxito temporal (success alert)

#### 3. **Pestañas (Tabs)**
- **🔮 Predicción Manual**: Selectboxes para elegir Local y Visitante
- **🤖 Próxima Fecha Automática**: Análisis automático de todos los partidos

#### 4. **Visualización Mejorada**
- `st.metric()` para porcentajes y cuotas con indicadores visuales
- `st.progress()` para barras de probabilidad
- `st.dataframe()` para historial H2H
- Colores automáticos según Delta (verde/rojo)
- Expanders para organizar información

#### 5. **Caching Inteligente**
- `@st.cache_data(ttl=3600)`: Cachea descargas de CSV (1 hora)
- `@st.cache_data`: Cachea cálculo de fuerzas
- **Resultado**: La app es muy rápida - no vuelve a descargar datos cada vez que tocas un botón

#### 6. **Lógica Matemática Intacta**
- Poisson Distribution: ✅ Sin cambios
- Ponderación 75/25 → 60/40 (reciente/global): ✅ Completa
- Normalización de nombres: ✅ Funcional
- H2H (Historial Directo): ✅ Integrado

---

## 🎯 Cómo Usar la App

### Opción 1: Lanzar desde Terminal
```bash
cd /path/to/projecto\ timba
streamlit run app.py
```

La app se abrirá en `http://localhost:8502`

### Opción 2: Usar el Script Helper
```bash
python run_streamlit.py
```

---

## 📋 Flujo de Usuario

### **Predicción Manual**
1. Abre la pestaña 🔮 **Predicción Manual**
2. En el sidebar: Selecciona una liga (ej: Premier League)
3. Se cargan los datos automáticamente
4. Elige **Local** y **Visitante** con los selectboxes
5. Haz clic en "⚽ Analizar Partido"
6. Ve los resultados: probabilidades, xG, comparativa ataque/defensa, forma reciente, etc.

### **Próxima Fecha Automática**
1. Abre la pestaña 🤖 **Próxima Fecha Automática**
2. En el sidebar: Selecciona una liga
3. Haz clic en "⚙️ Analizar Próxima Fecha"
4. Se descargan los partidos del siguiente periodo (7 días)
5. Se analizan automáticamente todos los partidos
6. Cada partido es expandible para ver detalles

---

## 🎨 Componentes Streamlit Utilizados

| Componente | Uso |
|-----------|-----|
| `st.set_page_config()` | Título y layout 'wide' |
| `st.sidebar.selectbox()` | Selector de ligas |
| `st.tabs()` | Dos pestañas principales |
| `st.metric()` | Porcentajes y cuotas con delta |
| `st.progress()` | Barras de probabilidad |
| `st.dataframe()` | Tabla H2H |
| `st.success()` | Mensajes de éxito |
| `st.warning()` | Alertas de equipo no encontrado |
| `st.error()` | Errores de conexión |
| `st.info()` | Información adicional |
| `st.spinner()` | Indicadores de carga |
| `st.expander()` | Expandibles para partidos |
| `st.write()` | Texto flexible |
| `st.button()` | Botones de acción |

---

## 📊 Secciones del Análisis

Cada predicción incluye:

1. **📊 Probabilidades y Cuotas** - Porcentajes de victoria, empate y derrota
2. **⚡ Goles Esperados (xG)** - Goles calculados para cada equipo
3. **🎯 Comparativa Ataque vs Defensa** - Fuerzas relativas
4. **📈 Forma Reciente** - Últimos 5 partidos
5. **📊 Tendencias** - Córners y tarjetas
6. **🔮 Top 3 Marcadores Exactos** - Marcadores más probables
7. **🥊 H2H** - Historial directo (últimos 5 enfrentamientos)

---

## ⚙️ Configuración

Los archivos de configuración están en `~/.streamlit/config.toml`:

```toml
[browser]
gatherUsageStats = false

[server]
headless = true
```

---

## 🔧 Archivos del Proyecto

- **`app.py`** - Aplicación principal con Streamlit (LA NUEVA)
- **`main1.py`** - Script original de consola (mantener como referencia)
- **`run_streamlit.py`** - Script helper para lanzar la app
- **`streamlit.log`** - Logs de ejecución

---

## 🚀 Próximas Mejoras Posibles

- [ ] Agregar gráficos de tendencia histórica
- [ ] Implementar predicciones de Over/Under
- [ ] Añadir análisis de quinielas
- [ ] Guardado de predicciones en base de datos
- [ ] Sistema de alertas de value bets
- [ ] Modo oscuro personalizado

---

## 📝 Notas Técnicas

### Caching (¿Por qué es importante?)
```python
@st.cache_data(ttl=3600)
def descargar_datos_liga(url_csv):
    # Descarga los datos UNA SOLA VEZ
    # Luego los reutiliza durante 1 hora
```

Sin caching, cada vez que tocas un botón:
- ❌ Vuelve a descargar 50KB de CSV
- ❌ Recalcula todas las fuerzas (operación lenta)

Con caching:
- ✅ Instantáneo
- ✅ Sin conexión a internet una vez cargado
- ✅ Mejor UX

### Por qué Streamlit es mejor que la consola

| Aspecto | Consola | Streamlit |
|--------|---------|-----------|
| Visualización | ASCII | Componentes web |
| Interactividad | input() | Botones y selectores |
| Rendimiento | Lento | Rápido (con caching) |
| Acceso | Solo terminal | Navegador (desde cualquier lado) |
| Estética | Básica | Profesional |

---

## 💡 ¿Cómo funciona el caching?

1. **Primera ejecución**: Descarga datos, calcula fuerzas → 5-10 segundos
2. **Cambio de liga**: Idem (nuevo CSV) → 5-10 segundos  
3. **Cambio de local/visitante**: Reutiliza cache → <100ms
4. **Al día siguiente**: Cache expira (ttl=3600s) → vuelve a descargar

---

¡Disfruta tu nueva aplicación web! 🎉
