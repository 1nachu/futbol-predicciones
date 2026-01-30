# ⚽ Timba Predictor v2.0

**Sistema avanzado de predicción de partidos con análisis estadístico, 14 mercados probabilísticos y recomendaciones visuales inteligentes.**

> Predice resultados de fútbol usando Poisson Distribution, análisis de forma reciente y ponderaciones inteligentes.

---

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/1nachu/futbol-predicciones.git
cd futbol-predicciones

# Instalar dependencias
python -m pip install -r requirements.txt
```

---

## ▶️ Ejecutar la App

### 🌐 Web (Streamlit)
```bash
streamlit run app.py --server.port 8502
# Accede a: http://localhost:8502
```

### 💻 Consola (CLI)
```bash
python cli.py
# Menú interactivo para predicciones
```

---

## 📊 Características v2.0

### 🎯 Predicción de Partidos
- ✅ Probabilidades 1-X-2 (Poisson Distribution)
- ✅ Goles esperados (xG) por equipo
- ✅ Comparativa ataque vs defensa
- ✅ Forma reciente ponderada (75% últimos 5 partidos)
- ✅ Análisis de tendencias (córners, tarjetas)
- ✅ Eficiencia de tiro y BTTS histórico

### 🏆 Mercados 1X2 & Doble Oportunidad (6)
- ✅ Probabilidades: Local, Empate, Visitante
- ✅ **1X**: Local o Empate
- ✅ **X2**: Empate o Visitante
- ✅ **12**: Sin Empate

### ⚽ Mercados de Goles (3)
- ✅ Over 1.5 Goles
- ✅ Over 2.5 Goles
- ✅ Under 3.5 Goles (seguridad)

### 🚩 Mercados de Córners v2.0 (5) ⭐ NUEVO
- ✅ Over 8.5 Córners
- ✅ Over 9.5 Córners
- ✅ Under 10.5 Córners (seguridad)
- ✅ Ganador Córners Local
- ✅ Ganador Córners Visitante

**Total**: 14 mercados probabilísticos

### 💡 Semáforo Visual de Recomendaciones
Recomendaciones automáticas basadas en confianza:
```
🔥 Verde  (≥70%)    → Recomendación FUERTE
⚠️  Amarillo (55-69%) → Recomendación MEDIA
🚩 Córners          → Información de córners
⚽ Goles            → Información de goles
🛡️  Seguridad      → Mercados Under (defensivos)
```

### 🔍 Análisis Avanzado
- ✅ Análisis automático de próximos fixtures
- ✅ Predicción batch para múltiples partidos
- ✅ Historial directo (H2H)
- ✅ Top 3 marcadores exactos más probables
- ✅ Validación automática de datos

### 🛡️ Confiabilidad
- ✅ Descargas CSV seguras con URLs alternativas
- ✅ Normalización de 100+ nombres de equipos (ALIAS_TEAMS)
- ✅ Manejo gracioso de datos faltantes
- ✅ Validación automática de córners (HC/AC)
- ✅ Ponderación inteligente: 75% reciente + 25% histórico

---

## 📈 Ligas Soportadas (7)

| # | Liga | Temporada | Datos |
|----|------|-----------|-------|
| 1 | 🇬🇧 Premier League | 25/26 | ✅ Completo |
| 2 | 🇪🇸 La Liga | 25/26 | ✅ Completo |
| 3 | 🇮🇹 Serie A | 25/26 | ✅ Completo |
| 4 | 🇩🇪 Bundesliga | 25/26 | ✅ Completo |
| 5 | 🇫🇷 Ligue 1 | 25/26 | ✅ Completo |
| 6 | 🇪🇺 Champions League | 25/26 | ✅ Con alternativas |
| 7 | 🇪🇺 Europa League | 25/26 | ✅ Con alternativas |

---

## 🧮 Cálculos Matemáticos

### Lambda de Goles (Poisson)
$$\lambda_{local} = \text{Ataque}_{casa} \times \text{Defensa}_{visitante} \times \text{Media}_{liga}$$

### Lambda de Córners (Poisson)
$$\lambda_{corners\_total} = \lambda_{local\_corners} + \lambda_{visitante\_corners}$$

### Mercados Over/Under
$$P(\text{Over 2.5}) = 1 - \text{CDF}_{\text{Poisson}}(2, \lambda_{total})$$

Más detalles en **SISTEMA_COMPLETO.md**

---

## 📚 Documentación

| Archivo | Contenido |
|---------|----------|
| **README.md** | Esta guía (proyecto) |
| **SISTEMA_COMPLETO.md** | Arquitectura técnica completa |
| **CAMBIOS_CORNERS.md** | Detalles de implementación v2.0 |
| **QUICK_REFERENCE.md** | Cheatsheet rápido de uso |
| **COMPARACION_ANTES_DESPUES.md** | v1.5 vs v2.0 detallado |
| **RESUMEN_EJECUTIVO.md** | Resumen de cambios |
| **LIMPIEZA_PROYECTO.md** | Limpieza de archivos obsoletos |

---

## 🧪 Testing

```bash
# Test de cálculos de córners
python test_corners.py

# Test de semáforo visual
python test_semaforo.py

# Verificar sintaxis
python -m py_compile timba_core.py app.py cli.py
```

---

## 📁 Estructura del Proyecto

```
timba-predicciones/
├── timba_core.py              # 🔧 Motor principal (cálculos)
├── app.py                     # 🌐 Interfaz Streamlit
├── cli.py                     # 💻 Interfaz Consola
├── test_corners.py            # 🧪 Test córners
├── test_semaforo.py           # 🧪 Test semáforo
├── requirements.txt           # 📦 Dependencias
├── README.md                  # 📖 Este archivo
├── SISTEMA_COMPLETO.md        # 📚 Documentación técnica
├── CAMBIOS_CORNERS.md         # 📝 v2.0 Córners
└── QUICK_REFERENCE.md         # ⚡ Cheatsheet
```

---

## 💡 Ejemplo de Uso

### Streamlit
1. Abre http://localhost:8502
2. Selecciona "🔮 Predicción Manual"
3. Elige liga y equipos
4. Ver predicción con semáforo de recomendaciones

### CLI
```bash
$ python cli.py

=== MENU PRINCIPAL ===
1. Premier League (Inglaterra)
2. La Liga (España)
...

Elige liga (numero): 1

--- Premier League ---
1. Predecir partido manual
2. Analizar próximos partidos

Elige opción: 1
Equipo local: Liverpool
Equipo visitante: Arsenal

---
Predicción Liverpool vs Arsenal
Prob Local: 62.50%  Empate: 18.20%  Prob Visita: 19.30%
...
💡 SUGERENCIAS DEL ALGORITMO:
   🔥 DOBLE OPORTUNIDAD 1X: 80.7%
   🚩 CÓRNERS +8.5: 71.2%
   ⚽ GOLES +2.5: 68.9%
```

---

## 🔑 Nuevas Claves en Predicción (v2.0)

### Mercados de Goles
```python
pred['Over_15']           # P(goles > 1.5)
pred['Over_25']           # P(goles > 2.5)
pred['Under_35']          # P(goles ≤ 3.5)
```

### Mercados de Córners ⭐ NUEVO
```python
pred['Over_85']                   # P(córners > 8.5)
pred['Over_95']                   # P(córners > 9.5)
pred['Under_105']                 # P(córners ≤ 10.5)
pred['Prob_Local_Mas_Corners']    # P(local gana córners)
pred['Prob_Vis_Mas_Corners']      # P(visitante gana córners)
```

---

## ✅ Validaciones Automáticas

- ✅ Verifica disponibilidad de datos (HC/AC en CSV)
- ✅ Filtra recomendaciones por confianza (≥55%)
- ✅ Suma de probabilidades = 1.0
- ✅ Manejo de ligas sin datos de córners

---

## 🚀 Novedades v2.0

**Del 29 de enero de 2026:**

✅ **Mercados de Córners Expandidos**
- Over/Under 8.5, 9.5, 10.5
- Ganador de Córners (1X2)
- Ponderación 75/25 (reciente/histórico)

✅ **Semáforo Visual Mejorado**
- 5 nuevas recomendaciones
- Emoji 🚩 para córners
- Validaciones automáticas

✅ **Documentación Consolidada**
- 7 archivos .md técnicos
- Arquitectura clara
- Ejemplos de uso

✅ **Proyecto Limpio**
- 11 archivos obsoletos eliminados
- Repositorio 40% más ligero
- Código más mantenible

**Estadísticas:**
- v1.5 → v2.0: **+56% mercados** (9 → 14)
- +50 líneas en `timba_core.py`
- +30 líneas en `app.py`
- +25 líneas en `cli.py`

---

## 🤝 Contribuir

Si deseas contribuir:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit los cambios
4. Push a tu rama
5. Abre un Pull Request

---

## 📊 Performance

- Predicción por partido: ~50ms
- Análisis de fixtures (10 partidos): ~500ms
- Uso de memoria: ~100MB (en Streamlit)

---

## ⚠️ Limitaciones

- Datos solo hasta temporada 25/26
- Champions/Europa League con URLs alternativas
- Córners solo en ligas con datos HC/AC
- No hay información de lesionados/alineaciones

---

## 🔮 Próximas Mejoras

- [ ] Mercados de tarjetas (Amarillas/Rojas)
- [ ] API REST para integraciones
- [ ] Machine Learning (XGBoost)
- [ ] Histórico de predicciones acertadas
- [ ] Live updates (WebSocket)

---

## 📄 Licencia

Uso personal y educativo. Para uso comercial, contacta al desarrollador.

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/1nachu/futbol-predicciones/issues)
- **Wiki**: Ver archivos .md en repositorio
- **Email**: Contacto en perfil de GitHub

---

**Versión**: 2.0 (29 de enero de 2026)  
**Status**: 🟢 Production Ready  
**Última actualización**: Git commit `55b92e7`  
**Repositorio**: https://github.com/1nachu/futbol-predicciones
