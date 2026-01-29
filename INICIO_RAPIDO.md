# 🚀 INICIO RÁPIDO - TIMBA PREDICTOR WEB

## ¿Dónde está la aplicación?

La aplicación **Streamlit** está corriendo ahora en:

### 🌐 http://localhost:8502

Abre el navegador en esa URL para acceder.

---

## ¿Qué puedo hacer?

### 1️⃣ **Predicción Manual** (Pestaña 🔮)

```
1. En el SIDEBAR izquierdo → Selecciona una liga (ej: Premier League)
2. Espera a que carguen los datos ✅
3. En la pestaña 🔮 Predicción Manual:
   - Elige equipo LOCAL (ej: Manchester City)
   - Elige equipo VISITANTE (ej: Liverpool)
   - Haz clic en "⚽ Analizar Partido"
4. Verás: Probabilidades, xG, Forma, H2H, etc.
```

### 2️⃣ **Análisis Automático** (Pestaña 🤖)

```
1. En el SIDEBAR → Selecciona una liga
2. En la pestaña 🤖 Próxima Fecha Automática:
   - Haz clic en "⚙️ Analizar Próxima Fecha"
3. Se descargan y analizan todos los partidos de la próxima semana
4. Cada partido es expandible para ver detalles
```

---

## 📚 Documentación Completa

Para más detalles, lee:

- **RESUMEN_TRANSFORMACION.md** ← Cambios realizados
- **STREAMLIT_README.md** ← Guía completa de uso

---

## 🛠️ Si algo falla...

### ❌ La app no carga

```bash
# Reinicia Streamlit
pkill -f "streamlit run app.py"
cd ~/Documentos/projecto\ timba
streamlit run app.py
```

### ❌ Puerto 8502 en uso

```bash
# Usa otro puerto
streamlit run app.py --server.port 8503
```

### ❌ Falta una librería

```bash
pip install streamlit pandas scipy requests
```

---

## 📊 Datos que Ves

Cada análisis muestra:

| Sección | Qué es |
|---------|--------|
| **Probabilidades** | % de victoria, empate, derrota |
| **Cuotas** | Cuotas justas calculadas |
| **xG** | Goles esperados para cada equipo |
| **Ataque/Defensa** | Comparativa de fuerzas |
| **Forma Reciente** | Últimos 5 partidos (goles) |
| **Tendencias** | Córners y tarjetas |
| **Marcadores** | Top 3 más probables |
| **H2H** | Últimos enfrentamientos |

---

## 🎯 Ligas Disponibles

1. ⚪ **Premier League** (Inglaterra)
2. 🔴 **La Liga** (España)
3. 🔵 **Serie A** (Italia)
4. ⚫ **Bundesliga** (Alemania)
5. 🔵 **Ligue 1** (Francia)
6. 🏆 **Champions League**
7. 🏆 **Europa League**

---

## ⚡ Velocidad de Carga

- **Primera carga de liga**: 5-10 segundos (descarga datos)
- **Cambio de equipos**: <100ms (cachea datos)
- **Cambio de liga**: 5-10 segundos (descarga nueva)
- **Día siguiente**: 5-10 segundos (cache expirado)

---

## 🎨 Cómo se ve

```
┌─────────────────────────────────────────────────────┐
│ ⚽ TIMBA PREDICTOR - Análisis de Partidos con... │
├─────────────────────────────────────────────────────┤
│  SIDEBAR            │  CONTENIDO PRINCIPAL         │
│ ┌───────────────────┼─────────────────────────────┐│
│ │ 🏆 Liga Selec.  │ 🔮 Predicción Manual │ 🤖  ││
│ │                 │                     │        ││
│ │ [Premier   ▼]  │ ⚪ Local: [City   ▼] │ (tab) ││
│ │               │ ⚫ Visit: [Liv    ▼] │        ││
│ │ ✅ 20 equipos  │                     │        ││
│ │ cargados       │   [⚽ Analizar]    │        ││
│ │               │                     │        ││
│ │               │ 📊 RESULTADOS        │        ││
│ │               │ ────────────────────│        ││
│ │               │ 🏆 Manchester 55.2% │        ││
│ │               │ ████████░░░░░░░░     │        ││
│ │               │ 🤝 Empate 25.0%      │        ││
│ │               │ ████░░░░░░░░░░░░     │        ││
│ └───────────────┴─────────────────────┴────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 💡 Tips Útiles

✅ Cambiar de liga es instantáneo (caching)
✅ Los datos se cachean 1 hora
✅ Puedes dejar abierta la tab y volver en 5 minutos
✅ Cada liga tiene su propio análisis independiente
✅ No hay input() lento - todo es instantáneo

---

## 🆘 Preguntas Frecuentes

**P: ¿Por qué dice "no se pudo emparejar" un equipo?**
R: El nombre en el fixture no coincide exactamente. Será arreglado en próximas versiones con IA.

**P: ¿Los datos se actualizan automáticamente?**
R: Se cachean 1 hora. Después se descargan nuevamente.

**P: ¿Puedo usar esto en móvil?**
R: Sí, si accedes a `http://[tu-ip]:8502` desde la red local.

**P: ¿Es la lógica matemática igual a la versión original?**
R: Sí, 100% igual. Solo cambió la interfaz.

---

## 🚀 Comando Rápido

Cualquier momento que quieras reiniciar:

```bash
cd ~/Documentos/projecto\ timba
streamlit run app.py
```

¡Y listo! La app estará en http://localhost:8502 🎉

---

**Última actualización:** 29 de enero de 2026
