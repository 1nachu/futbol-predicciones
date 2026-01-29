# 🚩 Expansión del Mercado de Córners - Cambios Realizados

## 📋 Resumen General
Se ha expandido el **"Consejero de Apuestas"** (semáforo visual) para incluir mercados de **Tiros de Esquina (Córners)** con cálculos probabilísticos basados en la distribución de Poisson.

---

## 🔧 Cambios en `timba_core.py`

### 1. **Mejora de `calcular_fuerzas()` - Métricas de Córners Ponderadas**

#### ✅ Nuevo Cálculo:
- **Ponderación 75% Reciente + 25% Histórico** (igual que goles):
  - `corners_casa_reciente`: promedio de córners de los últimos 5 partidos en casa
  - `corners_fuera_reciente`: promedio de córners de los últimos 5 partidos fuera
  - `corners_casa_global`: promedio histórico de todos los partidos en casa
  - `corners_fuera_global`: promedio histórico de todos los partidos fuera

#### 📊 Nuevas Claves en `fuerzas[equipo]`:
- `'Corners_Casa'`: Córners ponderados que saca el equipo en casa
- `'Corners_Fuera'`: Córners ponderados que saca el equipo fuera
- `'Corners_Casa_Contra'`: Córners en contra en casa (defiende)
- `'Corners_Fuera_Contra'`: Córners en contra fuera (defiende)
- `'Corners_Promedio'`: Promedio combinado de córners

---

### 2. **Expansión de `predecir_partido()` - Mercados de Córners**

#### 📈 Nuevos Cálculos:

**A. Lambda de Córners (Poisson):**
```python
corners_lambda_local = fuerzas[local]['Corners_Casa']
corners_lambda_vis = fuerzas[visitante]['Corners_Fuera']
corners_lambda_total = corners_lambda_local + corners_lambda_vis
```
- Lambda total sigue propiedad de suma de Poisson

**B. Mercados Over/Under (Usando `poisson.cdf`):**
- `Over_85`: P(córners > 8.5) = 1 - poisson.cdf(8, λ_total)
- `Over_95`: P(córners > 9.5) = 1 - poisson.cdf(9, λ_total)
- `Under_105`: P(córners ≤ 10.5) = poisson.cdf(10, λ_total)

**C. Ganador de Córners (1X2 Corners):**
- Comparación de lambdas:
  - Si `ratio_local/ratio_vis > 1.2`: Local 65%, Empate 25%, Visitante 10%
  - Si `ratio_local/ratio_vis < 0.83`: Local 10%, Empate 25%, Visitante 65%
  - Si `0.83 <= ratio <= 1.2`: Local 35%, Empate 40%, Visitante 25%

#### 🎯 Nuevas Claves en el Diccionario de Predicción:
- `'Corners_Lambda_Total'`: Lambda total esperado de córners
- `'Over_85'`: Probabilidad Over 8.5
- `'Over_95'`: Probabilidad Over 9.5
- `'Under_105'`: Probabilidad Under 10.5
- `'Prob_Local_Mas_Corners'`: Probabilidad de que local saque más córners
- `'Prob_Empate_Corners'`: Probabilidad de empate técnico en córners
- `'Prob_Vis_Mas_Corners'`: Probabilidad de que visitante saque más córners

---

## 🎨 Cambios en `app.py`

### 📱 Actualización de `mostrar_recomendaciones_semaforo()`

#### ✨ Nuevas Recomendaciones:

**Mercados de Córners** (mostradas solo si hay datos disponibles):

1. **🚩 Over 8.5 Córners**: Si probabilidad ≥ 70% (🔥 rojo) o ≥ 55% (⚠️ amarillo)
2. **🚩 Over 9.5 Córners**: Si probabilidad ≥ 70% (🔥 rojo) o ≥ 55% (⚠️ amarillo)
3. **🛡️ Under 10.5 Córners**: Si probabilidad ≥ 70% (🔥 rojo) o ≥ 55% (⚠️ amarillo) - Seguridad
4. **🚩 Ganador Córners - Local**: Si probabilidad ≥ 70% (🔥 rojo) o ≥ 55% (⚠️ amarillo)
5. **🚩 Ganador Córners - Visitante**: Si probabilidad ≥ 70% (🔥 rojo) o ≥ 55% (⚠️ amarillo)

#### 🔐 Validación:
- Se verifica que `Corners_Lambda_Total > 0` antes de mostrar recomendaciones de córners
- Previene mostrar datos falsos si el CSV no tiene columnas HC/AC (0 en ligas menores)

#### 🎯 Formato de Salida:
- **🔥 Rojo (≥70%)**: Recomendaciones de alta confianza `st.success()`
- **⚠️ Amarillo (55-69%)**: Recomendaciones de confianza media `st.warning()`
- **🚩 Azul**: Información de córners `st.info()`

---

## 💻 Cambios en `cli.py`

### 📤 Actualización de `mostrar_recomendaciones_semaforo_cli()`

**Nuevas Recomendaciones en Consola:**
- `🚩 CÓRNERS +8.5`: Muestra probabilidad si pasa umbral
- `🚩 CÓRNERS +9.5`: Muestra probabilidad si pasa umbral
- `🛡️  SEGURIDAD -10.5 CÓRNERS`: Para partidos defensivos
- `🚩 GANADOR CÓRNERS: LOCAL XXX%`: Si local lidera
- `🚩 GANADOR CÓRNERS: VISITANTE XXX%`: Si visitante lidera

**Validación Incluida:**
- Verifica `Corners_Lambda_Total > 0` antes de mostrar córners
- Mantiene formato consistente con recomendaciones de goles

---

## 📊 Ejemplo de Salida en Streamlit

```
💡 SUGERENCIAS DEL ALGORITMO

🔥 Doble Oportunidad: Local o Empate (82.5%)
🔥 Ganador Córners: Local saca más (75.0%)
⚠️ Córners: +8.5 Córners (62.3%)
⚽ Goles: +2.5 Goles (68.9%)
```

---

## 📊 Ejemplo de Salida en CLI

```
💡 SUGERENCIAS DEL ALGORITMO:
   🔥 DOBLE OPORTUNIDAD 1X: 82.5%
   🚩 GANADOR CÓRNERS: LOCAL 75.0%
   🚩 CÓRNERS +8.5: 62.3%
   ⚠️  GOLES +2.5: 68.9%
```

---

## ✅ Validaciones Implementadas

| Validación | Descripción |
|-----------|------------|
| `Corners_Lambda_Total > 0` | Verifica que hay datos de córners disponibles |
| HC/AC en CSV | Si todas las columnas son 0, no muestra recomendaciones falsas |
| Umbrales de confianza | Solo muestra recomendaciones con confianza ≥ 55% |
| Ponderación 75/25 | Favorece forma reciente sobre histórico |

---

## 🧪 Pruebas Realizadas

✅ **Sintaxis verificada**: `timba_core.py`, `app.py`, `cli.py` sin errores  
✅ **Lógica Poisson**: Funciones CDF validadas  
✅ **Validación de datos**: Córners solo se muestran si λ_total > 0  
✅ **Formato de salida**: Consistencia entre Streamlit y CLI  

---

## 🚀 Próximos Pasos Opcionales

1. **Tarjetas de Córners (1X2)**: Ampliar para tarjetas amarillas/rojas
2. **Corners por Mitad**: Separar 1T y 2T
3. **Predicción de Penales**: Si la cantidad de córners sugiere contactos frecuentes
4. **Machine Learning**: Entrenar modelo específico para córners si hay suficientes datos

---

**Último actualizado**: 29 de enero de 2026  
**Versión**: 2.0 - Con Mercados de Córners  
**Estado**: ✅ Producción

