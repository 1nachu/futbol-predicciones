import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import io
import requests
from scipy.stats import poisson
import numpy as np
from difflib import get_close_matches
from datetime import datetime, timedelta
import json
from timba_core import LIGAS, URLS_FIXTURE, normalizar_csv, calcular_fuerzas, predecir_partido, obtener_h2h, obtener_proximos_partidos, emparejar_equipo, encontrar_equipo_similar, descargar_csv_safe

# ========== CONFIGURACIÓN INICIAL ==========
st.set_page_config(
    page_title="⚽ Timba Predictor - Análisis de Partidos",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCIONES DE CACHING ==========
@st.cache_data(ttl=3600)
def descargar_datos_liga(url_csv):
    """
    Descarga y cachea los datos históricos de una liga.
    """
    # url_csv puede ser string o lista de alternativas
    try:
        df, ok = descargar_csv_safe(url_csv)
        if not ok:
            return None
        return df
    except Exception as e:
        st.error(f"❌ Error descargando datos: {e}")
        return None


@st.cache_data(ttl=3600)
def calcular_y_cachear_fuerzas(df_csv_string):
    """
    Calcula y cachea las fuerzas de los equipos.
    """
    df = pd.read_csv(io.StringIO(df_csv_string))
    df = normalizar_csv(df)
    fuerzas, media_local, media_vis = calcular_fuerzas(df)
    return fuerzas, media_local, media_vis, df

# Las funciones auxiliares se importan desde `timba_core.py`.

# ========== FUNCIÓN DE SEMÁFORO VISUAL ==========
def mostrar_recomendaciones_semaforo(prediccion, umbral_alto=0.70, umbral_medio=0.55):
    """
    Muestra un semáforo visual con recomendaciones basadas en probabilidades.
    umbral_alto: si prob >= 70%, se muestra en 🔥 (verde/recomendado)
    umbral_medio: si prob >= 55%, se muestra en ⚠️ (amarillo/probable)
    """
    st.subheader("💡 SUGERENCIAS DEL ALGORITMO")
    
    recomendaciones = []
    tiene_datos_corners = prediccion.get('Corners_Lambda_Total', 0) > 0
    
    # Doble Oportunidad
    if prediccion['Prob_1X'] >= umbral_alto:
        recomendaciones.append(("🔥", f"Doble Oportunidad: Local o Empate", f"{prediccion['Prob_1X']*100:.1f}%"))
    elif prediccion['Prob_1X'] >= umbral_medio:
        recomendaciones.append(("⚠️", f"Doble Oportunidad: Local o Empate", f"{prediccion['Prob_1X']*100:.1f}%"))
    
    if prediccion['Prob_X2'] >= umbral_alto:
        recomendaciones.append(("🔥", "Doble Oportunidad: Empate o Visitante", f"{prediccion['Prob_X2']*100:.1f}%"))
    elif prediccion['Prob_X2'] >= umbral_medio:
        recomendaciones.append(("⚠️", "Doble Oportunidad: Empate o Visitante", f"{prediccion['Prob_X2']*100:.1f}%"))
    
    if prediccion['Prob_12'] >= umbral_alto:
        recomendaciones.append(("🔥", "Sin Empate: Gana alguien", f"{prediccion['Prob_12']*100:.1f}%"))
    elif prediccion['Prob_12'] >= umbral_medio:
        recomendaciones.append(("⚠️", "Sin Empate: Gana alguien", f"{prediccion['Prob_12']*100:.1f}%"))
    
    # Mercados de goles
    if prediccion['Over_15'] >= umbral_alto:
        recomendaciones.append(("⚽", f"Goles: +1.5 Goles", f"{prediccion['Over_15']*100:.1f}%"))
    elif prediccion['Over_15'] >= umbral_medio:
        recomendaciones.append(("⚽", f"Goles: +1.5 Goles", f"{prediccion['Over_15']*100:.1f}%"))
    
    if prediccion['Over_25'] >= umbral_alto:
        recomendaciones.append(("⚽", f"Goles: +2.5 Goles", f"{prediccion['Over_25']*100:.1f}%"))
    elif prediccion['Over_25'] >= umbral_medio:
        recomendaciones.append(("⚽", f"Goles: +2.5 Goles", f"{prediccion['Over_25']*100:.1f}%"))
    
    if prediccion['Under_35'] >= umbral_alto:
        recomendaciones.append(("🛡️", f"Seguridad: -3.5 Goles", f"{prediccion['Under_35']*100:.1f}%"))
    elif prediccion['Under_35'] >= umbral_medio:
        recomendaciones.append(("🛡️", f"Seguridad: -3.5 Goles", f"{prediccion['Under_35']*100:.1f}%"))
    
    # Mercados de córners (solo si hay datos disponibles)
    if tiene_datos_corners:
        if prediccion.get('Over_85', 0) >= umbral_alto:
            recomendaciones.append(("🚩", f"Córners: +8.5 Córners", f"{prediccion['Over_85']*100:.1f}%"))
        elif prediccion.get('Over_85', 0) >= umbral_medio:
            recomendaciones.append(("🚩", f"Córners: +8.5 Córners", f"{prediccion['Over_85']*100:.1f}%"))
        
        if prediccion.get('Over_95', 0) >= umbral_alto:
            recomendaciones.append(("🚩", f"Córners: +9.5 Córners", f"{prediccion['Over_95']*100:.1f}%"))
        elif prediccion.get('Over_95', 0) >= umbral_medio:
            recomendaciones.append(("🚩", f"Córners: +9.5 Córners", f"{prediccion['Over_95']*100:.1f}%"))
        
        if prediccion.get('Under_105', 0) >= umbral_alto:
            recomendaciones.append(("🛡️", f"Seguridad: -10.5 Córners", f"{prediccion['Under_105']*100:.1f}%"))
        elif prediccion.get('Under_105', 0) >= umbral_medio:
            recomendaciones.append(("🛡️", f"Seguridad: -10.5 Córners", f"{prediccion['Under_105']*100:.1f}%"))
        
        # Ganador de córners
        if prediccion.get('Prob_Local_Mas_Corners', 0) >= umbral_alto:
            recomendaciones.append(("🚩", f"Ganador Córners: Local saca más", f"{prediccion['Prob_Local_Mas_Corners']*100:.1f}%"))
        elif prediccion.get('Prob_Local_Mas_Corners', 0) >= umbral_medio:
            recomendaciones.append(("🚩", f"Ganador Córners: Local saca más", f"{prediccion['Prob_Local_Mas_Corners']*100:.1f}%"))
        
        if prediccion.get('Prob_Vis_Mas_Corners', 0) >= umbral_alto:
            recomendaciones.append(("🚩", f"Ganador Córners: Visitante saca más", f"{prediccion['Prob_Vis_Mas_Corners']*100:.1f}%"))
        elif prediccion.get('Prob_Vis_Mas_Corners', 0) >= umbral_medio:
            recomendaciones.append(("🚩", f"Ganador Córners: Visitante saca más", f"{prediccion['Prob_Vis_Mas_Corners']*100:.1f}%"))
    
    if recomendaciones:
        for emoji, texto, extra in recomendaciones:
            if emoji == "🔥":
                st.success(f"{emoji} {texto} ({extra})")
            elif emoji == "⚠️":
                st.warning(f"{emoji} {texto} ({extra})")
            elif emoji == "🚩":
                st.info(f"{emoji} {texto} ({extra})")
            else:
                st.info(f"{emoji} {texto} ({extra})")
    else:
        st.info("📌 No hay recomendaciones claras. Analiza los datos detallados abajo.")

# ========== INTERFAZ PRINCIPAL ==========
def main():
    st.title("⚽ TIMBA PREDICTOR - Análisis de Partidos con Poisson")
    st.markdown("---")
    
    # ========== SIDEBAR: Selección de Liga ==========
    st.sidebar.header("🏆 Selecciona una Liga")
    
    opciones_ligas = {liga_id: liga_info['nombre'] for liga_id, liga_info in LIGAS.items()}
    liga_seleccionada_id = st.sidebar.selectbox(
        "Elige tu liga favorita:",
        options=list(opciones_ligas.keys()),
        format_func=lambda x: opciones_ligas[x]
    )
    
    liga_info = LIGAS[liga_seleccionada_id]
    liga_nombre = liga_info['nombre'].split(' - ')[0]
    
    # ========== CARGAR DATOS ==========
    with st.spinner(f"📥 Descargando datos de {liga_nombre}..."):
        df = descargar_datos_liga(liga_info.get('alternativas', liga_info.get('url')))

    data_available = True
    if df is None or df.empty:
        data_available = False
        st.warning("⚠️ No se encontraron estadísticas históricas para esta competición. Solo se mostrará el calendario.")
        fuerzas = {}
        media_local = media_vis = 0
    else:
        with st.spinner(f"🧠 Calculando fuerzas de los equipos..."):
            fuerzas, media_local, media_vis = calcular_fuerzas(df)
    
    equipos_validos = sorted(list(fuerzas.keys())) if data_available else []
    
    st.sidebar.success(f"✅ {len(equipos_validos)} equipos cargados")
    
    # ========== TABS: Predicción Manual y Automática ==========
    tab1, tab2 = st.tabs(["🔮 Predicción Manual", "🤖 Próxima Fecha Automática"])
    
    # ========== TAB 1: PREDICCIÓN MANUAL ==========
    with tab1:
        st.header("🔮 Predictor de Partidos")
        st.write(f"**Liga seleccionada:** {liga_nombre}")
        if not data_available:
            st.warning("⚠️ No hay estadísticas históricas para esta competición. Puedes ver el fixture en la pestaña 'Próxima Fecha Automática'.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                equipo_local = st.selectbox(
                    "⚪ Selecciona Equipo LOCAL:",
                    options=equipos_validos,
                    key="local"
                )
            with col2:
                equipo_visitante = st.selectbox(
                    "⚫ Selecciona Equipo VISITANTE:",
                    options=equipos_validos,
                    key="visitante"
                )
            if st.button("⚽ Analizar Partido", key="analizar_manual", use_container_width=True):
                if equipo_local == equipo_visitante:
                    st.error("❌ Los equipos deben ser diferentes.")
                else:
                    prediccion = predecir_partido(equipo_local, equipo_visitante, fuerzas, media_local, media_vis)
                    if prediccion:
                        st.success("✅ Predicción calculada")
                        mostrar_prediccion_streamlit(equipo_local, equipo_visitante, prediccion, fuerzas, df)
                    else:
                        st.error("❌ Error al calcular la predicción.")
    
    # ========== TAB 2: PRÓXIMA FECHA AUTOMÁTICA ==========
    with tab2:
        st.header("🤖 Análisis Automático")
        st.write(f"**Liga seleccionada:** {liga_nombre}")
        st.info(f"💡 Se analizarán todos los partidos de {liga_nombre} en los próximos 7 días.")
        
        if st.button("⚙️ Analizar Próxima Fecha", key="analizar_auto", use_container_width=True):
            fixture_url = URLS_FIXTURE.get(liga_seleccionada_id, {}).get('url')
            
            if not fixture_url:
                st.error("❌ No se encontró URL de fixture para esta liga.")
            else:
                with st.spinner(f"⏳ Obteniendo partidos de {liga_nombre}..."):
                    partidos = obtener_proximos_partidos(fixture_url)
                
                if not partidos:
                    st.warning("⚠️ No se encontraron partidos en los próximos 7 días.")
                else:
                    st.success(f"✅ Se encontraron {len(partidos)} partidos")
                    
                    # ========== RECOLECCIÓN DE DATOS PARA EXPORTACIÓN ==========
                    datos_para_excel = []
                    fecha_primer_partido = None
                    
                    # Procesar cada partido
                    for idx, partido in enumerate(partidos, 1):
                        local = partido['local']
                        visitante = partido['visitante']
                        fecha = partido['fecha']
                        if fecha_primer_partido is None:
                            fecha_primer_partido = fecha
                        
                        # Emparejar nombres
                        # Emparejar nombres (si no hay datos, solo mostrar fixture)
                        if not data_available:
                            st.write(f"📅 {fecha.strftime('%d/%m/%Y %H:%M')} - {local} vs {visitante}")
                            continue

                        local_emp, local_ok = emparejar_equipo(local, equipos_validos)
                        visitante_emp, visitante_ok = emparejar_equipo(visitante, equipos_validos)

                        if not local_ok or not visitante_ok:
                            st.warning(f"⚠️ No se pudo emparejar {local} vs {visitante}")
                            continue

                        # Calcular predicción
                        prediccion = predecir_partido(local_emp, visitante_emp, fuerzas, media_local, media_vis)

                        if prediccion:
                            with st.expander(f"📅 {fecha.strftime('%d/%m/%Y %H:%M')} | {local_emp.upper()} vs {visitante_emp.upper()}"):
                                mostrar_prediccion_streamlit(local_emp, visitante_emp, prediccion, fuerzas, df)
                            
                            # ========== AGREGAR DATOS AL EXCEL ==========
                            # Determinar predicción IA (resultado más probable)
                            prob_local = prediccion['Prob_Local']
                            prob_empate = prediccion['Prob_Empate']
                            prob_vis = prediccion['Prob_Vis']
                            
                            max_prob = max(prob_local, prob_empate, prob_vis)
                            if max_prob == prob_local:
                                prediccion_ia = "Local"
                            elif max_prob == prob_empate:
                                prediccion_ia = "Empate"
                            else:
                                prediccion_ia = "Visitante"
                            
                            # Obtener marcador exacto más probable
                            top_3 = prediccion.get('Top_3_Marcadores', [])
                            marcador_est = top_3[0]['marcador'] if top_3 else "N/A"
                            
                            # Agregar fila a datos_para_excel
                            datos_para_excel.append({
                                'Fecha': fecha.strftime('%Y-%m-%d %H:%M'),
                                'Liga': liga_nombre,
                                'Local': local_emp,
                                'Visitante': visitante_emp,
                                'Prob. Local (%)': f"{prob_local*100:.1f}",
                                'Prob. Empate (%)': f"{prob_empate*100:.1f}",
                                'Prob. Visita (%)': f"{prob_vis*100:.1f}",
                                'xG Local': f"{prediccion['Goles_Esp_Local']:.2f}",
                                'xG Visita': f"{prediccion['Goles_Esp_Vis']:.2f}",
                                'Predicción IA': prediccion_ia,
                                'Marcador Est. (Bola de Cristal)': marcador_est
                            })
                        else:
                            st.warning(f"❌ Error al calcular predicción para {local} vs {visitante}")
                    
                    # ========== EXPORTAR A EXCEL ==========
                    if datos_para_excel:
                        st.markdown("---")
                        st.subheader("📥 Descargar Reporte")
                        
                        # Crear DataFrame
                        df_export = pd.DataFrame(datos_para_excel)
                        
                        # Ordenar por fecha
                        df_export['Fecha'] = pd.to_datetime(df_export['Fecha'])
                        df_export = df_export.sort_values('Fecha').reset_index(drop=True)
                        
                        # Crear buffer en memoria
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_export.to_excel(writer, index=False, sheet_name='Predicciones')
                            
                            # Ajustar ancho de columnas
                            worksheet = writer.sheets['Predicciones']
                            for idx, col in enumerate(df_export.columns, 1):
                                max_length = max(df_export[col].astype(str).str.len().max(), len(col)) + 2
                                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length, 40)
                        
                        buffer.seek(0)
                        
                        # Botón de descarga
                        st.download_button(
                            label='📥 Descargar Reporte en Excel',
                            data=buffer.getvalue(),
                            file_name=f'Predicciones_Futbol_{fecha_primer_partido.strftime("%Y%m%d")}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            use_container_width=True
                        )
                        
                        st.success(f"✅ {len(datos_para_excel)} predicciones listas para exportar")

def mostrar_prediccion_streamlit(local, visitante, prediccion, fuerzas, df):
    """
    Muestra la predicción en componentes Streamlit (tabs, métricas, gráficos).
    """
    # ========== SECCIÓN 1: PROBABILIDADES ==========
    st.subheader("📊 Probabilidades y Cuotas")
    
    prob_local = prediccion['Prob_Local'] * 100
    prob_empate = prediccion['Prob_Empate'] * 100
    prob_vis = prediccion['Prob_Vis'] * 100
    
    cuota_justa_local = 1 / prediccion['Prob_Local'] if prediccion['Prob_Local'] > 0 else 0
    cuota_justa_empate = 1 / prediccion['Prob_Empate'] if prediccion['Prob_Empate'] > 0 else 0
    cuota_justa_vis = 1 / prediccion['Prob_Vis'] if prediccion['Prob_Vis'] > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"🏆 {local}",
            value=f"{prob_local:.1f}%",
            delta=f"Cuota: {cuota_justa_local:.2f}",
            delta_color="off"
        )
        st.progress(prob_local / 100, text=f"{prob_local:.1f}%")
    
    with col2:
        st.metric(
            label="🤝 EMPATE",
            value=f"{prob_empate:.1f}%",
            delta=f"Cuota: {cuota_justa_empate:.2f}",
            delta_color="off"
        )
        st.progress(prob_empate / 100, text=f"{prob_empate:.1f}%")
    
    with col3:
        st.metric(
            label=f"💥 {visitante}",
            value=f"{prob_vis:.1f}%",
            delta=f"Cuota: {cuota_justa_vis:.2f}",
            delta_color="off"
        )
        st.progress(prob_vis / 100, text=f"{prob_vis:.1f}%")
    
    # ========== SECCIÓN 2: GOLES ESPERADOS ==========
    st.subheader("⚡ Goles Esperados (xG)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label=f"🎯 {local}",
            value=f"{prediccion['Goles_Esp_Local']:.2f}",
            delta="Goles esperados",
            delta_color="off"
        )
        st.progress(min(prediccion['Goles_Esp_Local'] / 3, 1.0), 
                   text=f"{prediccion['Goles_Esp_Local']:.2f} goles")
    
    with col2:
        st.metric(
            label=f"🎯 {visitante}",
            value=f"{prediccion['Goles_Esp_Vis']:.2f}",
            delta="Goles esperados",
            delta_color="off"
        )
        st.progress(min(prediccion['Goles_Esp_Vis'] / 3, 1.0),
                   text=f"{prediccion['Goles_Esp_Vis']:.2f} goles")
    
    # ========== SECCIÓN 3: COMPARATIVA ATAQUE vs DEFENSA ==========
    st.subheader("🎯 Comparativa Ataque vs Defensa")
    
    ataque_local = fuerzas[local]['Ataque_Casa']
    defensa_local = fuerzas[local]['Defensa_Casa']
    ataque_vis = fuerzas[visitante]['Ataque_Fuera']
    defensa_vis = fuerzas[visitante]['Defensa_Fuera']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**{local}**")
        st.write(f"Ataque: {ataque_local:.2f}")
        st.progress(min(ataque_local, 2.0) / 2.0)
        st.write(f"Defensa: {defensa_local:.2f}")
        st.progress(min(defensa_local, 2.0) / 2.0)
    
    with col2:
        st.write(f"**{visitante}**")
        st.write(f"Ataque: {ataque_vis:.2f}")
        st.progress(min(ataque_vis, 2.0) / 2.0)
        st.write(f"Defensa: {defensa_vis:.2f}")
        st.progress(min(defensa_vis, 2.0) / 2.0)
    
    # ========== SECCIÓN 4: FORMA RECIENTE ==========
    st.subheader("📈 Forma Reciente (Últimos 5 Partidos)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**{local}**")
        st.metric("Goles Marcados", f"{prediccion['Goles_Favor_Local']:.2f}", delta_color="off")
        st.progress(min(prediccion['Goles_Favor_Local'] / 3, 1.0))
        st.metric("Goles Recibidos", f"{prediccion['Goles_Contra_Local']:.2f}", delta_color="off")
        st.progress(min(prediccion['Goles_Contra_Local'] / 3, 1.0))
    
    with col2:
        st.write(f"**{visitante}**")
        st.metric("Goles Marcados", f"{prediccion['Goles_Favor_Vis']:.2f}", delta_color="off")
        st.progress(min(prediccion['Goles_Favor_Vis'] / 3, 1.0))
        st.metric("Goles Recibidos", f"{prediccion['Goles_Contra_Vis']:.2f}", delta_color="off")
        st.progress(min(prediccion['Goles_Contra_Vis'] / 3, 1.0))
    
    # ========== SECCIÓN 5: TENDENCIAS ==========
    st.subheader("📊 Tendencias (Córners y Tarjetas)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Córners**")
        st.metric(local, f"{prediccion['Corners_Local']:.1f}", delta_color="off")
        st.metric(visitante, f"{prediccion['Corners_Vis']:.1f}", delta_color="off")
    
    with col2:
        st.write("**Tarjetas Amarillas**")
        st.metric(local, f"{prediccion['Tarjetas_Am_Local']:.1f}", delta_color="off")
        st.metric(visitante, f"{prediccion['Tarjetas_Am_Vis']:.1f}", delta_color="off")
    
    with col3:
        st.write("**Tarjetas Rojas**")
        st.metric(local, f"{prediccion['Tarjetas_Ro_Local']:.2f}", delta_color="off")
        st.metric(visitante, f"{prediccion['Tarjetas_Ro_Vis']:.2f}", delta_color="off")

    # ========== SECCIÓN 5b: EFICIENCIA Y MERCADOS DE GOLES ==========
    st.subheader("🔎 Eficiencia y Mercados de Goles (Histórico)")
    try:
        ef_local = fuerzas[local].get('Eficiencia_Tiro_Promedio_pct', 0)
        ef_vis = fuerzas[visitante].get('Eficiencia_Tiro_Promedio_pct', 0)
        btts_local = fuerzas[local].get('BTTS_pct', 0)
        btts_vis = fuerzas[visitante].get('BTTS_pct', 0)
        g2t_local = fuerzas[local].get('Goles_2T_Promedio', 0)
        g2t_vis = fuerzas[visitante].get('Goles_2T_Promedio', 0)

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(label="Eficiencia de Tiro (Local)", value=f"{ef_local:.1f}%")
            st.metric(label="Eficiencia de Tiro (Visitante)", value=f"{ef_vis:.1f}%")

        with col_b:
            # Mostrar BTTS histórico por equipo y promedio
            st.metric(label="BTTS Histórico (Local)", value=f"{btts_local:.1f}%")
            st.metric(label="BTTS Histórico (Visitante)", value=f"{btts_vis:.1f}%")
            st.write(f"**BTTS Promedio:** {(btts_local + btts_vis)/2:.1f}%")

        with col_c:
            # Goles esperados 2do tiempo (promedio por equipo y combinado)
            st.metric(label="Goles 2T (Local) - Hist.", value=f"{g2t_local:.2f}")
            st.metric(label="Goles 2T (Visitante) - Hist.", value=f"{g2t_vis:.2f}")
            st.write(f"**Goles 2T Esperados (Combinado):** {g2t_local + g2t_vis:.2f}")

        # Gráfica comparativa: Eficiencia, BTTS y Over2.5
        try:
            df_chart = pd.DataFrame({
                'Eficiencia_pct': [ef_local, ef_vis],
                'BTTS_pct': [btts_local, btts_vis],
                'Over25_pct': [fuerzas[local].get('Over25_pct', 0), fuerzas[visitante].get('Over25_pct', 0)]
            }, index=[local, visitante])
            st.bar_chart(df_chart)
        except Exception:
            pass
    except Exception:
        st.info("No hay datos de tiro/HT disponibles para estas ligas.")
    
    # ========== SECCIÓN 6: BOLA DE CRISTAL ==========
    st.subheader("🔮 Top 3 Marcadores Exactos")
    
    if prediccion['Top_3_Marcadores']:
        for idx, marcador_data in enumerate(prediccion['Top_3_Marcadores'], 1):
            marcador = marcador_data['marcador']
            prob = marcador_data['prob'] * 100
            st.write(f"**{idx}. {marcador}** → {prob:.2f}%")
            st.progress(prob / 100)
    
    # ========== SECCIÓN 7: H2H ==========
    st.subheader("🥊 Historial Directo (H2H)")
    
    h2h_data = obtener_h2h(local, visitante, df) if df is not None else []
    
    if h2h_data:
        st.write(f"**Últimos {min(5, len(h2h_data))} enfrentamientos:**")
        
        h2h_df = pd.DataFrame([
            {
                'Fecha': str(p['Fecha']).split()[0],
                'Local': p['Local'],
                'Visitante': p['Visitante'],
                'Resultado': f"{p['Goles_Local']}-{p['Goles_Visitante']}"
            }
            for p in h2h_data[:5]
        ])
        
        st.table(h2h_df)
        
        if len(h2h_data) > 5:
            st.info(f"ℹ️ Hay {len(h2h_data) - 5} encuentro(s) más en el historial.")
    else:
        st.info("📌 Sin historial directo previo entre estos equipos.")
    
    # ========== SECCIÓN 8: SEMÁFORO VISUAL ==========
    st.divider()
    mostrar_recomendaciones_semaforo(prediccion, umbral_alto=0.70, umbral_medio=0.55)
    
    st.info("💡 **Nota:** Ponderación 60% FORMA RECIENTE + 40% ESTADÍSTICAS GLOBALES")

if __name__ == "__main__":
    main()
