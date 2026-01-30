import io
import requests
import pandas as pd
import sys
import os
import json
from datetime import datetime
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(__file__))
from timba_core import (
    LIGAS, URLS_FIXTURE, normalizar_csv, emparejar_equipo,
    encontrar_equipo_similar, imprimir_barra, descargar_csv_safe,
    inicializar_timba_core
)

# Inicializar Timba Core
timba_core = inicializar_timba_core()

# ========== IMPORTAR TEAM NORMALIZATION ==========
try:
    from team_normalization import TeamNormalizer
    normalizer = TeamNormalizer()
    TEAM_NORMALIZATION_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Team normalization no disponible: {e}")
    normalizer = None
    TEAM_NORMALIZATION_AVAILABLE = False


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
        fuerzas, media_local, media_visitante = timba_core.calcular_fuerzas(df)
    url_fix = URLS_FIXTURE.get(id_liga, {}).get('url')
    if not url_fix:
        print('No hay URL de fixtures configurada para esta liga')
        return
    print('Descargando próximos partidos...')
    fixtures = timba_core.obtener_proximos_partidos(url_fix)
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
        pred = timba_core.predecir_partido(local_match, visita_match, fuerzas, media_local, media_visitante)
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
    fuerzas, media_local, media_visitante = timba_core.calcular_fuerzas(df)
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
    pred = timba_core.predecir_partido(local, visita, fuerzas, media_local, media_visitante)
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


def normalizar_equipo_cli():
    """Normaliza un nombre de equipo usando fuzzy matching."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    nombre = input("Ingresa el nombre del equipo a normalizar: ").strip()
    if not nombre:
        print("Nombre vacío")
        return
    
    try:
        resultado = normalizer.normalizar_nombre_equipo(nombre)
        
        print("\n" + "="*60)
        print("📊 RESULTADO DE NORMALIZACIÓN:")
        print("="*60)
        print(f"Entrada: {nombre}")
        print(f"Equipo oficial: {resultado['official_name']}")
        print(f"UUID: {resultado['team_uuid']}")
        print(f"País: {resultado['country']}")
        print(f"Liga: {resultado['league']}")
        print(f"Confianza: {resultado['confidence']:.1%}")
        
        # Mostrar aliased si es distinto al nombre oficial
        if resultado.get('is_alias') and resultado['alias'] != resultado['official_name']:
            print(f"Alias usado: {resultado['alias']}")
        
        # Mostrar mapeos externos
        external_mappings = resultado.get('external_mappings', [])
        if external_mappings:
            print("\n🔗 Mapeos externos:")
            for mapping in external_mappings:
                print(f"   • {mapping['source']}: {mapping['external_id']} (similitud: {mapping['similarity_score']:.1%})")
        
    except Exception as e:
        print(f"❌ Error al normalizar: {e}")


def mostrar_team_stats():
    """Muestra estadísticas del sistema de normalización."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    try:
        stats = normalizer.get_statistics()
        
        print("\n" + "="*60)
        print("📈 ESTADÍSTICAS DEL SISTEMA DE NORMALIZACIÓN:")
        print("="*60)
        print(f"Total de equipos únicos: {stats['total_teams']}")
        print(f"Total de mapeos externos: {stats['total_mappings']}")
        print(f"Total de aliases: {stats['total_aliases']}")
        print(f"Mapeos automáticos: {stats['automatic_mappings']}")
        print(f"Mapeos manuales: {stats['manual_mappings']}")
        print(f"Equipos sin mapeos: {stats['teams_without_mappings']}")
        print(f"Búsquedas caché: {stats['cache_hits']}")
        print(f"Búsquedas en BD: {stats['db_searches']}")
        print(f"Coincidencias fuzzy usadas: {stats['fuzzy_matches']}")
        
        if stats['top_sources']:
            print("\nFuentes de datos principales:")
            for source, count in stats['top_sources'].items():
                print(f"   • {source}: {count} mapeos")
        
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")


def listar_equipos_cli():
    """Lista los equipos en la tabla maestra con opción de filtrado."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    try:
        # Opción de filtrado
        filtro = input("Filtrar por país (dejar vacío para ver todos): ").strip()
        
        equipos = normalizer.list_all_teams(country_filter=filtro if filtro else None)
        
        if not equipos:
            print("No hay equipos que coincidan con el filtro")
            return
        
        # Preparar tabla
        data = []
        for eq in equipos:
            data.append([
                eq['team_uuid'][:8],  # UUID truncado
                eq['official_name'],
                eq['country'],
                eq['league'] or '-',
                len(eq.get('aliases', [])),
                len(eq.get('external_mappings', []))
            ])
        
        headers = ["UUID", "Nombre oficial", "País", "Liga", "Aliases", "Mapeos"]
        print("\n" + "="*100)
        print(f"EQUIPOS EN TABLA MAESTRA ({len(equipos)} total)")
        print("="*100)
        print(tabulate(data, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        print(f"❌ Error al listar equipos: {e}")


def agregar_equipo_cli():
    """Agrega un nuevo equipo a la tabla maestra."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    try:
        print("\n--- Agregar equipo a tabla maestra ---")
        nombre_oficial = input("Nombre oficial del equipo: ").strip()
        pais = input("País (código ISO, ej: AR, BR, MX): ").strip().upper()
        liga = input("Liga (opcional): ").strip() or None
        
        if not nombre_oficial or not pais:
            print("❌ Nombre oficial y país son obligatorios")
            return
        
        equipo = normalizer.add_master_team(
            official_name=nombre_oficial,
            country=pais,
            league=liga
        )
        
        print(f"\n✅ Equipo agregado exitosamente")
        print(f"   UUID: {equipo['team_uuid']}")
        print(f"   Nombre: {equipo['official_name']}")
        print(f"   País: {equipo['country']}")
        print(f"   Liga: {equipo['league'] or '-'}")
        
    except Exception as e:
        print(f"❌ Error al agregar equipo: {e}")


def exportar_equipos_cli():
    """Exporta los equipos a un archivo JSON."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    try:
        archivo = input("Nombre del archivo (sin extensión): ").strip()
        if not archivo:
            archivo = f"equipos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not archivo.endswith('.json'):
            archivo += '.json'
        
        equipos = normalizer.list_all_teams()
        
        # Preparar datos para exportación
        datos_export = {
            'export_date': datetime.now().isoformat(),
            'total_teams': len(equipos),
            'teams': equipos
        }
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_export, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Equipos exportados a {archivo}")
        print(f"   Total de equipos: {len(equipos)}")
        
    except Exception as e:
        print(f"❌ Error al exportar: {e}")


def team_management_menu():
    """Menú para gestión de equipos con normalización."""
    if not TEAM_NORMALIZATION_AVAILABLE:
        print("❌ Team normalization no está disponible")
        return
    
    while True:
        print("\n" + "="*60)
        print("🎯 GESTIÓN DE EQUIPOS - NORMALIZACIÓN")
        print("="*60)
        print("1. Normalizar nombre de equipo")
        print("2. Ver estadísticas del sistema")
        print("3. Listar todos los equipos")
        print("4. Agregar nuevo equipo a tabla maestra")
        print("5. Exportar equipos a JSON")
        print("0. Volver al menú principal")
        
        opcion = input("\nElige opción: ").strip()
        
        if opcion == '0':
            break
        elif opcion == '1':
            normalizar_equipo_cli()
        elif opcion == '2':
            mostrar_team_stats()
        elif opcion == '3':
            listar_equipos_cli()
        elif opcion == '4':
            agregar_equipo_cli()
        elif opcion == '5':
            exportar_equipos_cli()
        else:
            print("❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")


def main():
    while True:
        print('\n=== MENU PRINCIPAL ===')
        for k, v in LIGAS.items():
            print(f"{k}. {v['nombre']}")
        if TEAM_NORMALIZATION_AVAILABLE:
            print('99. Gestión de equipos (normalización)')
        print('0. Salir')
        try:
            opt = input('Elige liga (numero): ').strip()
        except (EOFError, KeyboardInterrupt):
            return
        if opt == '0' or opt.lower() == 'q':
            print('Saliendo...')
            break
        if opt == '99' and TEAM_NORMALIZATION_AVAILABLE:
            team_management_menu()
            continue
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
            print('3. Normalizar nombre de equipo')
            print('0. Volver')
            sub = input('Elige opción: ').strip()
            if sub == '0':
                break
            if sub == '1':
                predict_manual(id_liga)
            elif sub == '2':
                analizar_proxima_fecha_liga(id_liga)
            elif sub == '3':
                if TEAM_NORMALIZATION_AVAILABLE:
                    normalizar_equipo_cli()
                else:
                    print("❌ Team normalization no disponible")
            else:
                print('Opción inválida')


if __name__ == '__main__':
    main()
