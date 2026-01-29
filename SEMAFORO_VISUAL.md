# 📊 SEMÁFORO VISUAL - GUÍA DE IMPLEMENTACIÓN

## ✅ Cambios Realizados

### 1. **Cálculos de Mercados de Goles (Over/Under)**
📍 `timba_core.py` → función `predecir_partido()`

Se agregaron cálculos de probabilidades para mercados Over/Under usando la **distribución de Poisson**:

```python
lambda_total = lambda_local + lambda_visitante

# Mercados
Over_15 = 1 - poisson.cdf(1, lambda_total)   # P(goles > 1.5)
Over_25 = 1 - poisson.cdf(2, lambda_total)   # P(goles > 2.5)
Under_35 = poisson.cdf(3, lambda_total)      # P(goles ≤ 3.5)
```

**Matemática:**
- `poisson.cdf(n, λ)` = P(X ≤ n) = probabilidad acumulada
- `P(X > 1.5) = 1 - P(X ≤ 1) = P(X ≥ 2)`

### 2. **Cálculos de Doble Oportunidad**
📍 `timba_core.py` → función `predecir_partido()`

Se agregaron tres nuevos mercados de doble oportunidad:

```python
Prob_1X = Prob_Local + Prob_Empate           # Gana Local o Empata
Prob_X2 = Prob_Empate + Prob_Visitante      # Empata o Gana Visitante
Prob_12 = Prob_Local + Prob_Visitante       # Sin Empate (1 o 2)
```

### 3. **Función Semáforo Visual en Streamlit**
📍 `app.py` → nueva función `mostrar_recomendaciones_semaforo()`

```python
def mostrar_recomendaciones_semaforo(prediccion, umbral_alto=0.70, umbral_medio=0.55):
    """
    Muestra recomendaciones con umbrales de confianza:
    - 🔥 Verde/Fuego (≥ 70%): Recomendación fuerte
    - ⚠️  Amarillo (55-69%): Probabilidad media
    - 🛡️  Azul: Mercados defensivos
    - ⚽ Goles: Mercados ofensivos
    """
```

**Integración en Streamlit:** Se añade al final de `mostrar_prediccion_streamlit()` como una sección independiente:
```
💡 SUGERENCIAS DEL ALGORITMO
  🔥 Doble Oportunidad 1X: 82%
  ⚽ Goles +2.5: 65%
  🛡️  Seguridad -3.5: 55%
```

### 4. **Función Semáforo Visual en Consola**
📍 `cli.py` → nueva función `mostrar_recomendaciones_semaforo_cli()`

Versión CLI con el mismo formato de umbrales:

```python
def mostrar_recomendaciones_semaforo_cli(prediccion, umbral_alto=0.70, umbral_medio=0.55):
    """
    Imprime recomendaciones en consola con emojis y porcentajes.
    Se llama automáticamente después de cada predicción.
    """
```

### 5. **Integración Completa**
- ✅ `app.py`: Integrado en `mostrar_prediccion_streamlit()` (línea ~430)
- ✅ `cli.py`: Llamado después de mostrar marcadores (auto en ambas funciones)
- ✅ `timba_core.py`: Retorna 6 nuevas claves en el dict de `predecir_partido()`

---

## 📌 Nuevas Claves en el Diccionario de Predicción

```python
{
    # ... todas las claves anteriores ...
    
    # Mercados de goles
    'Over_15': float,      # Probabilidad de +1.5 goles
    'Over_25': float,      # Probabilidad de +2.5 goles
    'Under_35': float,     # Probabilidad de ≤3.5 goles
    
    # Doble oportunidad
    'Prob_1X': float,      # Local o Empate
    'Prob_X2': float,      # Empate o Visitante
    'Prob_12': float,      # Sin empate
}
```

---

## 🎯 Umbrales de Confianza

| Confianza | Color | Emoji | Acción |
|-----------|-------|-------|--------|
| ≥ 70% | 🟢 Verde | 🔥 | Mostrar recomendación fuerte |
| 55-69% | 🟡 Amarillo | ⚠️ | Mostrar como probabilidad media |
| < 55% | ⚪ Oculto | — | No mostrar |

---

## 🧪 Validación

Archivo de prueba: `test_semaforo.py`

Ejecutar:
```bash
cd /home/nahuel/Documentos/projecto\ timba
python test_semaforo.py
```

Verificaciones:
- ✅ Imports correctos (timba_core)
- ✅ Cálculos de fuerzas
- ✅ Predicción con nuevas claves
- ✅ Valores de Over/Under en rango [0,1]
- ✅ Valores de Doble Oportunidad en rango [0,1]

---

## 📱 Flujo de Uso

### Streamlit (Web)
1. Usuario selecciona teams en Manual Prediction
2. Sistema calcula predicción (incluye Over/Under + Doble Oportunidad)
3. Se muestra:
   - Probabilidades clásicas (1, X, 2)
   - Goles esperados (xG)
   - Comparativas ataque/defensa
   - **[NUEVO]** Semáforo visual con recomendaciones

### CLI (Consola)
1. Usuario selecciona liga y opción (manual/automática)
2. Sistema itera partidos o valida equipos
3. Se muestra:
   - Probabilidades
   - Goles esperados
   - Top 3 marcadores
   - **[NUEVO]** Recomendaciones del semáforo

---

## 🔧 Configuración Personalizable

En `app.py` línea ~45 (función `mostrar_recomendaciones_semaforo`):
```python
def mostrar_recomendaciones_semaforo(prediccion, umbral_alto=0.70, umbral_medio=0.55):
    # Cambiar aquí los umbrales si lo deseas
    # Ejemplo: umbral_alto=0.65 para recomendaciones más liberales
```

Lo mismo aplica en `cli.py` para la versión de consola.

---

## 🐛 Notas Técnicas

1. **Independencia de Poisson:** λ_total = λ_local + λ_visitante porque la suma de dos distribuciones Poisson es otra Poisson
2. **CDF vs PMF:** Usamos `cdf()` (función de distribución acumulada) para probabilidades "menores que"
3. **Emojis:** Compatible con Streamlit y terminales UTF-8 modernas
4. **Cálculos:** Basados en 100+ matches históricos por equipo (cuando disponible)

---

## 📊 Ejemplo de Salida

### Streamlit
```
💡 SUGERENCIAS DEL ALGORITMO

🔥 Doble Oportunidad: Local o Empate (82.5%)
⚠️  Doble Oportunidad: Empate o Visitante (61.3%)
⚽ Goles: +2.5 Goles (67.8%)
🛡️  Seguridad: -3.5 Goles (72.1%)

📌 No hay recomendaciones claras. Analiza los datos detallados abajo.
```

### Consola
```
💡 SUGERENCIAS DEL ALGORITMO:
   🔥 DOBLE OPORTUNIDAD 1X: 82.5%
   ⚠️  DOBLE OPORTUNIDAD X2: 61.3%
   ⚽ GOLES +2.5: 67.8%
   🛡️  SEGURIDAD -3.5: 72.1%
```

---

**Estado:** ✅ Implementación completa
**Archivos modificados:** timba_core.py, app.py, cli.py
**Líneas de código nuevas:** ~150 (funciones + integraciones)
**Sintaxis validada:** ✅ Sin errores
