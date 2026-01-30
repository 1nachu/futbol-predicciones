import io
import requests
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from timba_core import LIGAS, URLS_FIXTURE, normalizar_csv, calcular_fuerzas, predecir_partido, obtener_proximos_partidos, emparejar_equipo, encontrar_equipo_similar, imprimir_barra, descargar_csv_safe


def descargar_csv(url_or_list):
    """Descarga CSV usando la lógica segura de timba_core.
    Retorna (df, datos_disponibles_bool).
    """
    try:
        df, ok = descargar_csv_safe(url_or_list)
    except Exception:
        # fallback: try direct simple get
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = requests.get(url_or_list, headers=headers, timeout=15)
            r.raise_for_status()
            txt = r.content.decode('latin1')
            df = pd.read_csv(io.StringIO(txt))
            df = normalizar_csv(df)
            return df, True
        except Exception:
            return None, False
    return df, ok


def mostrar_recomendaciones_semaforo_cli(prediccion, umbral_alto=0.70, umbral_medio=0.55):
    """Muestra recomendaciones en consola con umbrales de confianza."""
    recomendaciones = []
    tiene_datos_corners = prediccion.get('Corners_Lambda_Total', 0) > 0
    
    # Doble Oportunidad
    if prediccion['Prob_1X'] >= umbral_alto:
        recomendaciones.append(f"🔥 DOBLE OPORTUNIDAD 1X: {prediccion['Prob_1X']*100:.1f}%")
    elif prediccion['Prob_1X'] >= umbral_medio:
        recomendaciones.append(f"⚠️  DOBLE OPORTUNIDAD 1X: {prediccion['Prob_1X']*100:.1f}%")
    
    if prediccion['Prob_X2'] >= umbral_alto:
        recomendaciones.append(f"🔥 DOBLE OPORTUNIDAD X2: {prediccion['Prob_X2']*100:.1f}%")
    elif prediccion['Prob_X2'] >= umbral_medio:
        recomendaciones.append(f"⚠️  DOBLE OPORTUNIDAD X2: {prediccion['Prob_X2']*100:.1f}%")
    
    if prediccion['Prob_12'] >= umbral_alto:
        recomendaciones.append(f"🔥 SIN EMPATE (12): {prediccion['Prob_12']*100:.1f}%")
    elif prediccion['Prob_12'] >= umbral_medio:
        recomendaciones.append(f"⚠️  SIN EMPATE (12): {prediccion['Prob_12']*100:.1f}%")
    
    # Mercados de goles
    if prediccion['Over_15'] >= umbral_alto:
        recomendaciones.append(f"⚽ GOLES +1.5: {prediccion['Over_15']*100:.1f}%")
    elif prediccion['Over_15'] >= umbral_medio:
        recomendaciones.append(f"⚽ GOLES +1.5: {prediccion['Over_15']*100:.1f}%")
    
    if prediccion['Over_25'] >= umbral_alto:
        recomendaciones.append(f"⚽ GOLES +2.5: {prediccion['Over_25']*100:.1f}%")
    elif prediccion['Over_25'] >= umbral_medio:
        recomendaciones.append(f"⚽ GOLES +2.5: {prediccion['Over_25']*100:.1f}%")
    
    if prediccion['Under_35'] >= umbral_alto:
        recomendaciones.append(f"🛡️  SEGURIDAD -3.5: {prediccion['Under_35']*100:.1f}%")
    elif prediccion['Under_35'] >= umbral_medio:
        recomendaciones.append(f"🛡️  SEGURIDAD -3.5: {prediccion['Under_35']*100:.1f}%")
    
    # Mercados de córners (solo si hay datos disponibles)
    if tiene_datos_corners:
        if prediccion.get('Over_85', 0) >= umbral_alto:
            recomendaciones.append(f"🚩 CÓRNERS +8.5: {prediccion['Over_85']*100:.1f}%")
        elif prediccion.get('Over_85', 0) >= umbral_medio:
            recomendaciones.append(f"🚩 CÓRNERS +8.5: {prediccion['Over_85']*100:.1f}%")
        
        if prediccion.get('Over_95', 0) >= umbral_alto:
            recomendaciones.append(f"🚩 CÓRNERS +9.5: {prediccion['Over_95']*100:.1f}%")
        elif prediccion.get('Over_95', 0) >= umbral_medio:
            recomendaciones.append(f"🚩 CÓRNERS +9.5: {prediccion['Over_95']*100:.1f}%")
        
        if prediccion.get('Under_105', 0) >= umbral_alto:
            recomendaciones.append(f"🛡️  SEGURIDAD -10.5 CÓRNERS: {prediccion['Under_105']*100:.1f}%")
        elif prediccion.get('Under_105', 0) >= umbral_medio:
            recomendaciones.append(f"🛡️  SEGURIDAD -10.5 CÓRNERS: {prediccion['Under_105']*100:.1f}%")
        
        # Ganador de córners
        if prediccion.get('Prob_Local_Mas_Corners', 0) >= umbral_alto:
            recomendaciones.append(f"🚩 GANADOR CÓRNERS: LOCAL {prediccion['Prob_Local_Mas_Corners']*100:.1f}%")
        elif prediccion.get('Prob_Local_Mas_Corners', 0) >= umbral_medio:
            recomendaciones.append(f"🚩 GANADOR CÓRNERS: LOCAL {prediccion['Prob_Local_Mas_Corners']*100:.1f}%")
        
        if prediccion.get('Prob_Vis_Mas_Corners', 0) >= umbral_alto:
            recomendaciones.append(f"🚩 GANADOR CÓRNERS: VISITANTE {prediccion['Prob_Vis_Mas_Corners']*100:.1f}%")
        elif prediccion.get('Prob_Vis_Mas_Corners', 0) >= umbral_medio:
            recomendaciones.append(f"🚩 GANADOR CÓRNERS: VISITANTE {prediccion['Prob_Vis_Mas_Corners']*100:.1f}%")
    
    if recomendaciones:
        print("\n💡 SUGERENCIAS DEL ALGORITMO:")
        for rec in recomendaciones:
            print(f"   {rec}")
    else:
        print("\n💡 SUGERENCIAS DEL ALGORITMO: No hay recomendaciones claras (confianza < 55%)")


def analizar_proxima_fecha_liga(id_liga):
    liga = LIGAS.get(id_liga)
    if not liga:
        print('Liga no encontrada')
        return
    print(f"Descargando datos históricos para {liga['nombre']}")
    df, ok = descargar_csv(liga.get('alternativas', liga.get('url')))
    if not ok or df is None:
        print('⚠️ No se encontraron estadísticas históricas para esta competición. Solo se mostrará el calendario.')
        fuerzas = {}
        media_local = media_visitante = 0
    else:
        fuerzas, media_local, media_visitante = calcular_fuerzas(df)
    url_fix = URLS_FIXTURE.get(id_liga, {}).get('url')
    if not url_fix:
        print('No hay URL de fixtures configurada para esta liga')
        return
    print('Descargando próximos partidos...')
    fixtures = obtener_proximos_partidos(url_fix)
    if not fixtures:
        print('No se encontraron próximos partidos (o error al descargar fixtures)')
        return
    equipos = list(fuerzas.keys())
    for partido in fixtures:
        local_raw = partido['local']
        visita_raw = partido['visitante']
        fecha = partido.get('fecha')
        if not fuerzas:
            # No hay datos históricos: mostrar solo fixture
            print(f"📅 {fecha} - {local_raw} vs {visita_raw}")
            continue

        local_match, ok_local = emparejar_equipo(local_raw, equipos)
        visita_match, ok_visita = emparejar_equipo(visita_raw, equipos)
        if not ok_local or not ok_visita:
            print(f"No se pudo emparejar: {local_raw} vs {visita_raw}")
            continue
        pred = predecir_partido(local_match, visita_match, fuerzas, media_local, media_visitante)
        if not pred:
            print('No se pudo predecir para:', local_match, visita_match)
            continue
        print('---------------------------------------------')
        print(f"{local_match} vs {visita_match}  —  {fecha}")
        print(f"Prob Local: {pred['Prob_Local']:.2%}  Empate: {pred['Prob_Empate']:.2%}  Prob Visita: {pred['Prob_Vis']:.2%}")
        print(f"Goles esperados Local: {pred['Goles_Esp_Local']:.2f}  Visita: {pred['Goles_Esp_Vis']:.2f}")
        barra_local, p_local = imprimir_barra(pred['Goles_Esp_Local'], maximo=5)
        barra_vis, p_vis = imprimir_barra(pred['Goles_Esp_Vis'], maximo=5)
        print(f"Goles esperados barras -> {local_match}: {barra_local}  {visita_match}: {barra_vis}")
        top = pred.get('Top_3_Marcadores', [])
        print('Top 3 marcadores probables:')
        for m in top:
            print(f"  {m['marcador']}  ({m['prob']:.2%})")
        mostrar_recomendaciones_semaforo_cli(pred)


def predict_manual(id_liga):
    liga = LIGAS.get(id_liga)
    if not liga:
        print('Liga no encontrada')
        return
    df, ok = descargar_csv(liga.get('alternativas', liga.get('url')))
    if not ok or df is None:
        print('⚠️ No se encontraron estadísticas históricas para esta competición. No puedes hacer predicciones manuales.')
        return
    fuerzas, media_local, media_visitante = calcular_fuerzas(df)
    equipos = list(fuerzas.keys())
    print('Equipos detectados en datos:', len(equipos))
    local = input('Equipo local: ').strip()
    visita = input('Equipo visitante: ').strip()
    if local not in equipos:
        candidatos = encontrar_equipo_similar(local, equipos)
        if candidatos:
            print('Sugerencias para local:', candidatos)
            local = candidatos[0]
        else:
            print('Equipo local no encontrado')
            return
    if visita not in equipos:
        candidatos = encontrar_equipo_similar(visita, equipos)
        if candidatos:
            print('Sugerencias para visitante:', candidatos)
            visita = candidatos[0]
        else:
            print('Equipo visitante no encontrado')
            return
    pred = predecir_partido(local, visita, fuerzas, media_local, media_visitante)
    if not pred:
        print('No se pudo predecir')
        return
    print('---------------------------------------------')
    print(f"Predicción {local} vs {visita}")
    print(f"Prob Local: {pred['Prob_Local']:.2%}  Empate: {pred['Prob_Empate']:.2%}  Prob Visita: {pred['Prob_Vis']:.2%}")
    print(f"Goles esperados Local: {pred['Goles_Esp_Local']:.2f}  Visita: {pred['Goles_Esp_Vis']:.2f}")
    top = pred.get('Top_3_Marcadores', [])
    print('Top 3 marcadores probables:')
    for m in top:
        print(f"  {m['marcador']}  ({m['prob']:.2%})")
    mostrar_recomendaciones_semaforo_cli(pred)


def main():
    while True:
        print('\n=== MENU PRINCIPAL ===')
        for k, v in LIGAS.items():
            print(f"{k}. {v['nombre']}")
        print('0. Salir')
        try:
            opt = input('Elige liga (numero): ').strip()
        except (EOFError, KeyboardInterrupt):
            return
        if opt == '0' or opt.lower() == 'q':
            print('Saliendo...')
            break
        try:
            id_liga = int(opt)
        except:
            print('Opción inválida')
            continue
        if id_liga not in LIGAS:
            print('Liga no configurada')
            continue
        while True:
            print(f"\n--- {LIGAS[id_liga]['nombre']} ---")
            print('1. Predecir partido manual')
            print('2. Analizar próximos partidos (fixtures) para esta liga')
            print('0. Volver')
            sub = input('Elige opción: ').strip()
            if sub == '0':
                break
            if sub == '1':
                predict_manual(id_liga)
            elif sub == '2':
                analizar_proxima_fecha_liga(id_liga)
            else:
                print('Opción inválida')


if __name__ == '__main__':
    main()
