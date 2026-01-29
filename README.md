# Timba Predictor

App avanzada de predicción de partidos (Streamlit) y utilidades CLI con análisis estadístico, mercados de goles y recomendaciones visuales.

## 🚀 Instalación rápida:

```bash
python -m pip install -r requirements.txt
```

## ▶️ Ejecutar la app web:

```bash
streamlit run app.py --server.port 8502
```

## ▶️ Ejecutar CLI:

```bash
python cli.py
```

## 📊 Características Principales

### Predicción de Partidos
- ✅ Probabilidades 1-X-2 usando Poisson
- ✅ Goles esperados (xG) por equipo
- ✅ Comparativa ofensiva/defensiva
- ✅ Forma reciente (últimos 5 partidos)
- ✅ Tendencias (córners, tarjetas)
- ✅ Eficiencia de tiro y BTTS histórico

### Mercados de Goles (🆕)
- ✅ Over/Under 1.5, 2.5, 3.5 goles
- ✅ Cálculos con distribución Poisson
- ✅ Probabilidades precisas en tiempo real

### Doble Oportunidad (🆕)
- ✅ 1X: Local o Empate
- ✅ X2: Empate o Visitante
- ✅ 12: Sin Empate

### 💡 Semáforo Visual de Recomendaciones (🆕)
Recomendaciones automáticas basadas en confianza:
- 🔥 **Verde** (≥70%): Recomendación fuerte
- ⚠️ **Amarillo** (55-69%): Probabilidad media
- 🛡️ Mercados defensivos (Under)
- ⚽ Mercados ofensivos (Over)

### Análisis Avanzado
- ✅ Análisis automático de próximos fixtures
- ✅ Predicción batch para múltiples partidos
- ✅ Historial directo (H2H)
- ✅ Top 3 marcadores exactos

### Confiabilidad
- ✅ Descargas CSV seguras con URLs alternativas
- ✅ Normalización de 100+ nombres de equipos
- ✅ Manejo gracioso de datos faltantes

## 📝 Novedades (v1.2.0)

**Semáforo Visual + Mercados Avanzados:**
- Nuevas claves en predicción: `Over_15`, `Over_25`, `Under_35`, `Prob_1X`, `Prob_X2`, `Prob_12`
- Nueva sección en Streamlit: "💡 SUGERENCIAS DEL ALGORITMO"
- CLI actualizado con recomendaciones automáticas
- Documentación técnica en `SEMAFORO_VISUAL.md`
