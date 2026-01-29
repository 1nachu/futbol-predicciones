# 🚀 QUICK REFERENCE - MERCADOS DE CÓRNERS

## 📋 Cheatsheet de Nuevas Funcionalidades

### 1. ¿Cómo obtener predicción de córners?

```python
from timba_core import predecir_partido, calcular_fuerzas
import pandas as pd

# Cargar datos
df = pd.read_csv('E0.csv')  # Premier League

# Calcular fuerzas (incluye córners)
fuerzas, media_local, media_vis = calcular_fuerzas(df)

# Predicción (con córners)
pred = predecir_partido('Liverpool', 'Arsenal', fuerzas, media_local, media_vis)

# Acceder a datos de córners
print(f"Over 8.5 Córners: {pred['Over_85']*100:.1f}%")
print(f"Ganador Córners - Local: {pred['Prob_Local_Mas_Corners']*100:.1f}%")
```

---

## 🎯 Nuevas Claves en Diccionario de Predicción

```python
# Mercados de Goles (existentes)
pred['Over_15']           # P(goles > 1.5)
pred['Over_25']           # P(goles > 2.5)
pred['Under_35']          # P(goles ≤ 3.5)

# Mercados de Córners (NUEVOS)
pred['Corners_Lambda_Total']      # λ total esperado
pred['Over_85']                   # P(córners > 8.5)
pred['Over_95']                   # P(córners > 9.5)
pred['Under_105']                 # P(córners ≤ 10.5)
pred['Prob_Local_Mas_Corners']    # P(local gana córners)
pred['Prob_Empate_Corners']       # P(empate técnico)
pred['Prob_Vis_Mas_Corners']      # P(visitante gana córners)
```

---

## 📊 Nuevas Claves en Diccionario de Fuerzas

```python
fuerzas['Liverpool']['Corners_Casa']           # Córners en casa
fuerzas['Liverpool']['Corners_Fuera']          # Córners fuera
fuerzas['Liverpool']['Corners_Casa_Contra']    # Córners recibidos casa
fuerzas['Liverpool']['Corners_Fuera_Contra']   # Córners recibidos fuera
fuerzas['Liverpool']['Corners_Promedio']       # Promedio combinado
```

---

## 🔧 Parámetros de Validación

```python
# Verificar si hay datos de córners
if prediccion['Corners_Lambda_Total'] > 0:
    # Hay datos de córners - mostrar recomendaciones
    print(f"Over 8.5: {prediccion['Over_85']}")
else:
    # Sin datos de córners - no mostrar
    print("Datos de córners no disponibles")
```

---

## 💡 Umbrales de Recomendación

```python
# Semáforo Visual
umbral_alto = 0.70    # 🔥 Fuerte (mostrar destacado)
umbral_medio = 0.55   # ⚠️ Medio (mostrar amarillo)

if pred['Over_85'] >= umbral_alto:
    print("🔥 Over 8.5 Córners: MUY PROBABLE")
elif pred['Over_85'] >= umbral_medio:
    print("⚠️ Over 8.5 Córners: Probable")
else:
    print("(No mostrar - confianza baja)")
```

---

## 📈 Interpretación de Probabilidades

| Probabilidad | Interpretación | Emoji |
|-------------|-----------------|-------|
| ≥ 70% | Muy probable | 🔥 |
| 55-69% | Probable | ⚠️ |
| 40-54% | Dudoso | — |
| < 40% | Poco probable | — |

---

## 🚩 Nuevos Emojis en Semáforo

```
🔥  = Recomendación fuerte (≥70%)
⚠️  = Recomendación media (55-69%)
🚩  = Información de córners
⚽  = Información de goles
🛡️  = Información de seguridad (Under/Baja)
```

---

## 📱 Salida en Streamlit

```python
if pred['Over_85'] >= 0.70:
    st.success(f"🚩 Over 8.5 Córners ({pred['Over_85']*100:.1f}%)")
elif pred['Over_85'] >= 0.55:
    st.warning(f"🚩 Over 8.5 Córners ({pred['Over_85']*100:.1f}%)")
else:
    st.info(f"📌 No hay recomendación de córners")
```

---

## 💻 Salida en CLI

```python
if pred['Over_85'] >= 0.70:
    print(f"🔥 CÓRNERS +8.5: {pred['Over_85']*100:.1f}%")
elif pred['Over_85'] >= 0.55:
    print(f"🚩 CÓRNERS +8.5: {pred['Over_85']*100:.1f}%")
```

---

## 🧮 Fórmulas Rápidas

```
Lambda total de córners:
  λ_total = λ_local_corners + λ_visitante_corners

Over/Under usando Poisson CDF:
  P(Over 8.5) = 1 - CDF(8, λ_total)
  P(Over 9.5) = 1 - CDF(9, λ_total)
  P(Under 10.5) = CDF(10, λ_total)

Ganador Córners basado en ratio:
  ratio = λ_local / λ_visitante
  
  if ratio > 1.2:
    Local 65%, Empate 25%, Visitante 10%
  elif ratio < 0.83:
    Local 10%, Empate 25%, Visitante 65%
  else:
    Local 35%, Empate 40%, Visitante 25%
```

---

## 🔍 Validaciones Automáticas

```python
# 1. Verificar disponibilidad de datos
if prediccion['Corners_Lambda_Total'] > 0:
    # ✅ Mostrar recomendaciones

# 2. Verificar confianza
if probabilidad >= 0.55:
    # ✅ Mostrar recomendación

# 3. Verificar suma de probabilidades (Ganador Córners)
suma = (pred['Prob_Local_Mas_Corners'] + 
        pred['Prob_Empate_Corners'] + 
        pred['Prob_Vis_Mas_Corners'])
assert abs(suma - 1.0) < 0.01  # ✅ Debe ser ≈1.0
```

---

## 📊 Ejemplos de Casos

### Caso 1: Equipo Fuerte en Casa
```
Equipo: Liverpool
Corners_Casa: 7.8 (arriba del promedio)
Corners_Casa_Contra: 5.1 (defensa fuerte)

Predicción vs Arsenal:
  Over_85: 72.3% 🔥
  Prob_Local_Mas_Corners: 76.1% 🔥
  
→ Apostar a que Liverpool saca más córners
```

### Caso 2: Partido Defensivo
```
Equipo Local: Burnley (defensivo)
Corners_Casa: 4.2 (bajo)

Equipo Visitante: Manchester United
Corners_Fuera: 3.8 (bajo fuera)

Predicción:
  Over_85: 31.2% ❌ (no mostrar)
  Under_105: 78.9% 🔥
  
→ Esperar menos de 11 córners
```

### Caso 3: Partido Ofensivo
```
Local: Manchester City
Corners_Casa: 8.1 (alto)

Visitante: Liverpool
Corners_Fuera: 7.3 (alto)

Predicción:
  Over_85: 84.2% 🔥
  Over_95: 67.3% ⚠️
  
→ Claramente más de 8.5 córners
```

---

## 🧪 Test Rápido

```bash
# Ejecutar test de córners
python test_corners.py

# Verificar sintaxis
python -m py_compile timba_core.py app.py cli.py

# Ejecutar predicción manual
python cli.py
```

---

## 📚 Documentación Completa

| Archivo | Contenido |
|---------|----------|
| `CAMBIOS_CORNERS.md` | Detalles técnicos |
| `SISTEMA_COMPLETO.md` | Arquitectura completa |
| `RESUMEN_EJECUTIVO.md` | Resumen de cambios |
| `COMPARACION_ANTES_DESPUES.md` | Comparación v1.5 vs v2.0 |
| `test_corners.py` | Script de prueba |

---

## ✅ Checklist de Validación

- [ ] CSVs tienen columnas HC/AC
- [ ] `Corners_Lambda_Total > 0`
- [ ] Probabilidades entre 0 y 1
- [ ] Suma de Ganador Córners = 1.0
- [ ] Recomendaciones solo si ≥ 55%
- [ ] Destaque si ≥ 70%

---

## 🚀 Próximas Expansiones

```
v2.0 actual:
  ✅ Mercados de goles
  ✅ Mercados de córners
  ⏳ Mercados de tarjetas

v2.1 esperado:
  + Tarjetas amarillas Over/Under
  + Tarjetas rojas probabilidad
  + Expulsiones esperadas

v3.0 esperado:
  + API REST
  + WebSocket para live updates
  + ML models (XGBoost)
  + Historical performance tracking
```

---

## 📞 Troubleshooting

| Problema | Solución |
|----------|----------|
| `Over_85 = 0` | Verificar HC/AC en CSV |
| `Ganador Córners suma ≠ 1.0` | Bug en cálculo de ratio |
| `No se muestran recomendaciones` | Confianza < 55% |
| `KeyError: 'Corners_Lambda_Total'` | Versión antigua de timba_core.py |

---

## 🎓 Aprendizajes Claves

1. **Ponderación 75/25**: Forma reciente es más importante
2. **Poisson es ideal**: Para eventos discretos como córners
3. **Validación es crítica**: HC/AC pueden ser 0 en ligas menores
4. **Semáforo funciona**: Umbrales claros evitan falsos positivos
5. **Escalable**: Fácil agregar más mercados

---

**Versión**: 2.0  
**Última actualización**: 29 de enero de 2026  
**Estado**: ✅ Production Ready  

Para más detalles, ver documentación completa en archivos .md
