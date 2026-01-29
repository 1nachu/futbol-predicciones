# 🎯 Flujo Visual de la Aplicación Streamlit

## Estructura de la App

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TIMBA PREDICTOR WEB                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SIDEBAR (Izquierda)          │  CONTENIDO (Centro-Derecha)       │
│  ├─ 🏆 Selecciona Liga        │  ├─ 🔮 Predicción Manual         │
│  │  ├─ 1. Premier League      │  │  ├─ Selectbox: Local          │
│  │  ├─ 2. La Liga             │  │  ├─ Selectbox: Visitante       │
│  │  ├─ 3. Serie A             │  │  ├─ Botón: Analizar           │
│  │  ├─ 4. Bundesliga          │  │  └─ Resultados...             │
│  │  ├─ 5. Ligue 1             │  │                                │
│  │  ├─ 6. Champions League    │  ├─ 🤖 Próxima Fecha Automática  │
│  │  └─ 7. Europa League       │  │  ├─ Botón: Analizar Fecha     │
│  │                            │  │  ├─ Partidos Expandibles      │
│  │  ✅ XX equipos cargados    │  │  └─ Resultados...             │
│  │                            │  │                                │
│  │  (Datos se cachean 1 hora) │  │                                │
│  │                            │  │                                │
│  └────────────────────────────┴──────────────────────────────────┘
│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de Usuario: Predicción Manual

```
START
  │
  ├─→ Abre http://localhost:8502
  │
  ├─→ SIDEBAR: Selecciona Liga (ej: Premier League)
  │   │
  │   ├─→ st.spinner: "Descargando datos..."
  │   │
  │   ├─→ @st.cache_data: Descarga CSV
  │   │
  │   ├─→ st.spinner: "Calculando fuerzas..."
  │   │
  │   ├─→ @st.cache_data: Calcula fuerzas
  │   │
  │   └─→ st.success: "✅ 20 equipos cargados"
  │
  ├─→ Haz clic en Pestaña "🔮 Predicción Manual"
  │
  ├─→ Selectbox: Equipo LOCAL (ej: Man. City)
  │
  ├─→ Selectbox: Equipo VISITANTE (ej: Liverpool)
  │
  ├─→ Botón: "⚽ Analizar Partido"
  │   │
  │   ├─→ predecir_partido()
  │   │   │
  │   │   ├─→ Poisson distribution
  │   │   ├─→ xG calculation
  │   │   ├─→ Win/Draw/Loss probabilities
  │   │   └─→ Top 3 scorelines
  │   │
  │   └─→ mostrar_prediccion_streamlit()
  │       │
  │       ├─→ st.metric: Probabilidades
  │       ├─→ st.progress: Barras
  │       ├─→ st.write: Comparativas
  │       ├─→ st.table: H2H
  │       └─→ st.expander: Detalles
  │
  └─→ END

```

---

## Flujo de Usuario: Análisis Automático

```
START
  │
  ├─→ SIDEBAR: Selecciona Liga (ej: La Liga)
  │   (se cachean datos)
  │
  ├─→ Haz clic en Pestaña "🤖 Próxima Fecha Automática"
  │
  ├─→ Botón: "⚙️ Analizar Próxima Fecha"
  │   │
  │   ├─→ st.spinner: "Obteniendo partidos..."
  │   │
  │   ├─→ obtener_proximos_partidos(url)
  │   │   │
  │   │   └─→ requests.get(fixturedownload.com)
  │   │       └─→ JSON parsing
  │   │
  │   ├─→ st.success: "✅ Se encontraron 10 partidos"
  │   │
  │   └─→ Para cada partido:
  │       │
  │       ├─→ Emparejar nombres (difflib)
  │       │
  │       ├─→ predecir_partido()
  │       │
  │       └─→ st.expander:
  │           │
  │           ├─→ mostrar_prediccion_streamlit()
  │           │   ├─→ Probabilidades
  │           │   ├─→ xG
  │           │   ├─→ Ataque/Defensa
  │           │   ├─→ Forma reciente
  │           │   ├─→ Marcadores
  │           │   └─→ H2H
  │           │
  │           └─→ (cerrar expander)
  │
  └─→ END

```

---

## Estructura del Código

```
app.py
├─ Imports (streamlit, pandas, scipy, etc.)
│
├─ st.set_page_config()
│  └─ Título, ícono, layout='wide'
│
├─ LIGAS (diccionario)
├─ URLS_FIXTURE (diccionario)
│
├─ Funciones de Caching:
│  ├─ @st.cache_data descargar_datos_liga()
│  ├─ @st.cache_data calcular_y_cachear_fuerzas()
│
├─ Funciones Auxiliares:
│  ├─ normalizar_csv()
│  ├─ calcular_fuerzas()
│  ├─ predecir_partido()
│  ├─ obtener_h2h()
│  ├─ obtener_proximos_partidos()
│  ├─ emparejar_equipo()
│  ├─ encontrar_equipo_similar()
│
├─ Función de Visualización:
│  └─ mostrar_prediccion_streamlit()
│      ├─ st.metric()
│      ├─ st.progress()
│      ├─ st.write()
│      ├─ st.table()
│      └─ st.info()
│
├─ main():
│  ├─ st.title()
│  ├─ SIDEBAR:
│  │  └─ st.sidebar.selectbox()
│  ├─ Carga de datos
│  ├─ st.tabs():
│  │  ├─ Tab 1: Predicción Manual
│  │  │  ├─ st.selectbox (Local)
│  │  │  ├─ st.selectbox (Visitante)
│  │  │  └─ st.button (Analizar)
│  │  │
│  │  └─ Tab 2: Próxima Fecha
│  │     └─ st.button (Analizar Fecha)
│  │
│  └─ mostrar_prediccion_streamlit()
│
└─ if __name__ == "__main__": main()
```

---

## Flujo de Datos (Caching)

```
┌─────────────────────────────────────────────┐
│         PRIMERA VEZ (5-10 segundos)         │
├─────────────────────────────────────────────┤
│                                             │
│  1. Descargar CSV → football-data.co.uk    │
│     (guardarlo en CACHE por 1 hora)        │
│                                             │
│  2. Procesar DataFrame                      │
│                                             │
│  3. Calcular Fuerzas (lento)                │
│     (guardar en CACHE por 1 hora)          │
│                                             │
│  4. Mostrar resultados                      │
│                                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   CAMBIO DE EQUIPOS (<100 milisegundos)    │
├─────────────────────────────────────────────┤
│                                             │
│  1. REUTILIZAR fuerzas del CACHE          │
│                                             │
│  2. Calcular predicción (muy rápido)       │
│                                             │
│  3. Mostrar resultados (instantáneo)       │
│                                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   CAMBIO DE LIGA (5-10 segundos)           │
├─────────────────────────────────────────────┤
│                                             │
│  1. Cache expiró o es nueva → Descargar   │
│     nuevo CSV                              │
│                                             │
│  2. Calcular nuevas fuerzas                │
│                                             │
│  3. Mostrar resultados                      │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Componentes Streamlit Utilizados

```
┌──────────────────────────────────────────────────────┐
│            COMPONENTES STREAMLIT EN app.py           │
├──────────────────────────────────────────────────────┤
│                                                      │
│  st.set_page_config()         ← Configuración       │
│  st.title()                   ← Título principal    │
│  st.sidebar.selectbox()       ← Selector de liga    │
│  st.spinner()                 ← Indicador de carga  │
│  st.success()                 ← Mensaje de éxito    │
│  st.error()                   ← Mensaje de error    │
│  st.warning()                 ← Advertencia         │
│  st.info()                    ← Información         │
│  st.tabs()                    ← Pestañas            │
│  st.selectbox()               ← Selector            │
│  st.button()                  ← Botón               │
│  st.metric()                  ← Métrica con delta   │
│  st.progress()                ← Barra de progreso   │
│  st.write()                   ← Texto flexible      │
│  st.table()                   ← Tabla               │
│  st.expander()                ← Expandible          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Comparativa: Consola vs Streamlit

```
┌─────────────────────┬──────────────────────┐
│      CONSOLA        │    STREAMLIT         │
├─────────────────────┼──────────────────────┤
│ input()             │ st.selectbox()       │
│ print()             │ st.write()           │
│ while True          │ Eventos (botones)    │
│ Barras ASCII        │ st.progress()        │
│ Colores ANSI        │ Colores nativos      │
│ Scroll lento        │ Responsive           │
│ Sin cache           │ @st.cache_data       │
│ Terminal            │ Navegador web        │
│ Difícil compartir   │ Acceso desde cualq.  │
│ Pobre UX            │ Interfaz moderna     │
└─────────────────────┴──────────────────────┘
```

---

## Performance Timeline

```
ESCENARIO 1: Primera carga
┌────────────┬─────────┬──────────────────────┐
│ Acción     │ Tiempo  │ Qué ocurre            │
├────────────┼─────────┼──────────────────────┤
│ Descargar  │ 3-5s    │ CSV desde web        │
│ Procesar   │ 1-2s    │ Normalizar datos     │
│ Fuerzas    │ 2-4s    │ Calcular (lento)     │
│ CACHE      │ ---     │ Se guarda en memoria │
│ Mostrar    │ 0.5s    │ Renderizar UI        │
├────────────┼─────────┼──────────────────────┤
│ TOTAL      │ 7-16s   │ (primera vez)        │
└────────────┴─────────┴──────────────────────┘

ESCENARIO 2: Cambio de equipos
┌────────────┬─────────┬──────────────────────┐
│ Acción     │ Tiempo  │ Qué ocurre            │
├────────────┼─────────┼──────────────────────┤
│ CACHE      │ 0ms     │ Reutilizar fuerzas   │
│ Predicción │ 50-100ms│ Poisson calc         │
│ Mostrar    │ 0.5s    │ Renderizar UI        │
├────────────┼─────────┼──────────────────────┤
│ TOTAL      │ <1s     │ (muy rápido)         │
└────────────┴─────────┴──────────────────────┘

ESCENARIO 3: Cambio de liga
┌────────────┬─────────┬──────────────────────┐
│ Acción     │ Tiempo  │ Qué ocurre            │
├────────────┼─────────┼──────────────────────┤
│ CACHE expi │ 0ms     │ Detectar expiración  │
│ Descargar  │ 3-5s    │ Nuevo CSV            │
│ Procesar   │ 1-2s    │ Normalizar           │
│ Fuerzas    │ 2-4s    │ Calcular (lento)     │
│ Mostrar    │ 0.5s    │ Renderizar UI        │
├────────────┼─────────┼──────────────────────┤
│ TOTAL      │ 7-16s   │ (nueva liga)         │
└────────────┴─────────┴──────────────────────┘
```

---

## Diagrama de Decisión: ¿Qué Pestaña Usar?

```
                    ¿Qué quieres hacer?
                            │
                ┌───────────┼───────────┐
                │           │           │
                v           v           v
        
    Analizar      Análisis      Comparar
    un partido    automático    múltiples
    específico    de la fecha   partidos
        │               │           │
        │               │           │
        └──────┬────────┴───────────┘
               │
         ┌─────v──────┐
         │  Usa 🔮    │ o 🤖?
         └─────┬──────┘
               │
        ┌──────┴───────┐
        │              │
        v              v
    🔮 MANUAL     🤖 AUTOMÁTICA
    ├─ Input     ├─ Descarga fixtures
    │  equipos   ├─ Analiza todos
    ├─ 1         └─ Muestra expandibles
    │  predicción│
    └─ Detallado└─ Rápido overview
```

---

Este diagrama Visual muestra cómo fluye la información a través de la app.
