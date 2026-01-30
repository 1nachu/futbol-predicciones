#!/usr/bin/env python3
"""
Ejemplo de Integración ETL + Predicción
========================================

Este script muestra cómo integrar el pipeline ETL con el sistema de predicción.

Uso:
    python examples.py descargar_datos
    python examples.py analizar_equipo "Manchester City"
    python examples.py predecir_partido "Liverpool" "Manchester United"
    python examples.py exportar_entrenamiento

Autor: Data Engineering Team
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
from sqlalchemy import create_engine
from typing import Optional

from etl_football_data import FootballETLPipeline
from etl_data_analysis import FootballDataAnalyzer, FootballDataExporter
from etl_config import DATABASE_CONFIG


def ejemplo_1_descargar_datos():
    """
    Ejemplo 1: Descargar datos desde Football-Data.co.uk
    """
    print("\n" + "="*80)
    print("📥 EJEMPLO 1: Descargar Datos Históricos")
    print("="*80 + "\n")
    
    # Crear pipeline ETL
    pipeline = FootballETLPipeline(db_type='sqlite')
    
    # Ejecutar descarga y transformación
    print("Descargando data de 3 ligas (10 temporadas cada una)...")
    print("Esto puede tomar 5-10 minutos.\n")
    
    exitoso = pipeline.ejecutar(
        ligas=['E0', 'SP1', 'D1'],  # Premier, La Liga, Bundesliga
        crear_tablas=True
    )
    
    if exitoso:
        print("\n✅ Datos descargados y cargados exitosamente")
    else:
        print("\n❌ Error en la descarga")
    
    return exitoso


def ejemplo_2_analizar_equipo(nombre_equipo: str = "Liverpool"):
    """
    Ejemplo 2: Analizar estadísticas de un equipo
    """
    print("\n" + "="*80)
    print(f"🔍 EJEMPLO 2: Análisis de {nombre_equipo}")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    analyzer = FootballDataAnalyzer(engine)
    
    # Obtener estadísticas
    stats = analyzer.obtener_estadisticas_equipo(nombre_equipo)
    
    print(f"📊 Estadísticas de {nombre_equipo}\n")
    
    if stats['casa']:
        print("🏠 CASA:")
        casa = stats['casa']
        print(f"  Partidos: {casa['partidos']}")
        print(f"  Goles/partido: {casa['goles_marcados']}")
        print(f"  Goles recibidos: {casa['goles_recibidos']}")
        print(f"  Tiros/partido: {casa['tiros_promedio']}")
        print(f"  Tiros al arco: {casa['tiros_arco_promedio']}")
        print(f"  Victorias: {casa['victorias']} | Empates: {casa['empates']} | Derrotas: {casa['derrotas']}")
    
    if stats['fuera']:
        print("\n🛣️  FUERA:")
        fuera = stats['fuera']
        print(f"  Partidos: {fuera['partidos']}")
        print(f"  Goles/partido: {fuera['goles_marcados']}")
        print(f"  Goles recibidos: {fuera['goles_recibidos']}")
        print(f"  Tiros/partido: {fuera['tiros_promedio']}")
        print(f"  Tiros al arco: {fuera['tiros_arco_promedio']}")
        print(f"  Victorias: {fuera['victorias']} | Empates: {fuera['empates']} | Derrotas: {fuera['derrotas']}")


def ejemplo_3_historial_directo(equipo1: str = "Liverpool", equipo2: str = "Manchester United"):
    """
    Ejemplo 3: Ver historial directo (H2H)
    """
    print("\n" + "="*80)
    print(f"🥊 EJEMPLO 3: Historial Directo {equipo1} vs {equipo2}")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    analyzer = FootballDataAnalyzer(engine)
    
    # Obtener últimos 10 enfrentamientos
    h2h = analyzer.obtener_enfrentamientos_directos(equipo1, equipo2, limit=10)
    
    if h2h.empty:
        print(f"❌ No hay historial directo entre {equipo1} y {equipo2}")
        return
    
    print(f"Últimos {len(h2h)} enfrentamientos:\n")
    
    # Mostrar tabla
    h2h_display = h2h[['date', 'home_team', 'away_team', 'fthg', 'ftag', 'ftr']].copy()
    h2h_display.columns = ['Fecha', 'Local', 'Visitante', 'GF', 'GC', 'Resultado']
    
    print(h2h_display.to_string(index=False))
    
    # Estadísticas H2H
    print("\n📊 Estadísticas:")
    if equipo1 in h2h['home_team'].values:
        local_wins = len(h2h[(h2h['home_team'] == equipo1) & (h2h['ftr'] == '1')])
        print(f"{equipo1} gana en casa: {local_wins}")
    
    if equipo2 in h2h['home_team'].values:
        away_wins = len(h2h[(h2h['home_team'] == equipo2) & (h2h['ftr'] == '1')])
        print(f"{equipo2} gana en casa: {away_wins}")


def ejemplo_4_predecir_partido(home_team: str = "Liverpool", away_team: str = "Manchester City"):
    """
    Ejemplo 4: Calcular probabilidades de un partido
    """
    print("\n" + "="*80)
    print(f"🔮 EJEMPLO 4: Predicción {home_team} vs {away_team}")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    analyzer = FootballDataAnalyzer(engine)
    
    # Calcular probabilidades
    probs = analyzer.calcular_probabilidades_match(home_team, away_team)
    
    print(f"Probabilidades estimadas:\n")
    print(f"  🏆 {home_team} gana: {probs['local']:.1%}")
    print(f"  🤝 Empate: {probs['empate']:.1%}")
    print(f"  💥 {away_team} gana: {probs['visitante']:.1%}")
    
    print(f"\nGoles esperados:")
    print(f"  {home_team}: {probs['goles_esp_local']:.2f}")
    print(f"  {away_team}: {probs['goles_esp_visitante']:.2f}")
    
    # Cuota justa
    print(f"\nCuotas justas:")
    print(f"  1: {1/probs['local']:.2f}")
    print(f"  X: {1/probs['empate']:.2f}")
    print(f"  2: {1/probs['visitante']:.2f}")


def ejemplo_5_top_equipos():
    """
    Ejemplo 5: Listar top equipos
    """
    print("\n" + "="*80)
    print("🏆 EJEMPLO 5: Top Equipos por Métrica")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    analyzer = FootballDataAnalyzer(engine)
    
    # Top 10 por goles
    print("⚽ Top 10 equipos por goles promedio:\n")
    top_goles = analyzer.obtener_top_equipos('goles_promedio', limit=10)
    top_goles.columns = ['Equipo', 'Goles/Partido']
    print(top_goles.to_string(index=False))
    
    # Top 10 por victorias
    print("\n\n🏅 Top 10 equipos por victorias:\n")
    top_victorias = analyzer.obtener_top_equipos('victorias', limit=10)
    top_victorias.columns = ['Equipo', 'Victorias']
    print(top_victorias.to_string(index=False))
    
    # Top 10 por defensa
    print("\n\n🛡️  Top 10 equipos por mejor defensa (menos goles):\n")
    top_defensa = analyzer.obtener_top_equipos('defensa', limit=10)
    top_defensa.columns = ['Equipo', 'Goles Recibidos']
    print(top_defensa.to_string(index=False))


def ejemplo_6_tendencias():
    """
    Ejemplo 6: Análisis de tendencias de mercado
    """
    print("\n" + "="*80)
    print("📈 EJEMPLO 6: Tendencias de Mercado")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    analyzer = FootballDataAnalyzer(engine)
    
    # Últimos 30 días
    tendencias = analyzer.obtener_tendencias_mercado(dias=30)
    
    if not tendencias:
        print("No hay datos disponibles")
        return
    
    print(f"Últimos 30 días de datos:\n")
    print(f"  Partidos analizados: {tendencias['partidos_analizados']}")
    print(f"  Promedio de goles: {tendencias['promedio_goles']:.2f}")
    print(f"  % Over 2.5: {tendencias['over_25_pct']:.1f}%")
    print(f"  % Under 2.5: {100 - tendencias['over_25_pct']:.1f}%")


def ejemplo_7_exportar_entrenamiento():
    """
    Ejemplo 7: Exportar datos para entrenar modelo ML
    """
    print("\n" + "="*80)
    print("📦 EJEMPLO 7: Exportar Datos para Entrenamiento")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    
    print("Extrayendo datos para entrenamiento...\n")
    
    with engine.connect() as conn:
        # Seleccionar columnas relevantes para ML
        df = pd.read_sql("""
            SELECT 
                date,
                home_team,
                away_team,
                fthg,
                ftag,
                ftr,
                hs,
                as_shots,
                hst,
                ast,
                hf,
                af,
                hr,
                ar,
                hy,
                ay,
                b365h,
                b365d,
                b365a,
                total_goles,
                over_25
            FROM matches
            WHERE temporada IN ('2425', '2324', '2223', '2122')
            ORDER BY date DESC
        """, conn)
    
    print(f"✓ Extraídos {len(df)} registros")
    
    # Exportar en múltiples formatos
    exporter = FootballDataExporter()
    
    # CSV
    exporter.exportar_csv(df, 'datos_entrenamiento.csv')
    
    # Excel
    exporter.exportar_excel(df, 'datos_entrenamiento.xlsx')
    
    # Parquet (comprimido y eficiente)
    exporter.exportar_parquet(df, 'datos_entrenamiento.parquet')
    
    print("\n✅ Exportación completada:")
    print("  📄 datos_entrenamiento.csv")
    print("  📊 datos_entrenamiento.xlsx")
    print("  📦 datos_entrenamiento.parquet")


def ejemplo_8_validar_datos():
    """
    Ejemplo 8: Validar integridad de datos
    """
    print("\n" + "="*80)
    print("✅ EJEMPLO 8: Validación de Integridad")
    print("="*80 + "\n")
    
    engine = create_engine('sqlite:///football_data.db')
    
    with engine.connect() as conn:
        # Contar registros
        total = pd.read_sql("SELECT COUNT(*) as total FROM matches", conn)
        print(f"Total de registros: {total['total'].values[0]:,}")
        
        # Verificar NULL
        nulls = pd.read_sql("""
            SELECT 
                COUNT(CASE WHEN home_team IS NULL THEN 1 END) as null_home,
                COUNT(CASE WHEN away_team IS NULL THEN 1 END) as null_away,
                COUNT(CASE WHEN ftr IS NULL THEN 1 END) as null_ftr,
                COUNT(CASE WHEN b365h IS NULL THEN 1 END) as null_b365
            FROM matches
        """, conn)
        
        print(f"\nValores NULL:")
        print(f"  HomeTeam: {nulls['null_home'].values[0]}")
        print(f"  AwayTeam: {nulls['null_away'].values[0]}")
        print(f"  FTR: {nulls['null_ftr'].values[0]}")
        print(f"  Cuotas B365: {nulls['null_b365'].values[0]}")
        
        # Duplicados
        dupes = pd.read_sql("""
            SELECT COUNT(*) as dupes FROM (
                SELECT date, home_team, away_team, fthg, ftag
                FROM matches
                GROUP BY date, home_team, away_team, fthg, ftag
                HAVING COUNT(*) > 1
            )
        """, conn)
        
        print(f"\nDuplicados: {dupes['dupes'].values[0]}")
        
        # FTR inválidos
        ftr_bad = pd.read_sql("""
            SELECT COUNT(*) as invalidos FROM matches
            WHERE ftr NOT IN ('1', 'D', '2')
        """, conn)
        
        print(f"FTR inválidos: {ftr_bad['invalidos'].values[0]}")
        
        print("\n✅ Validación completada")


def main():
    """Función principal"""
    
    if len(sys.argv) < 2:
        print("Uso: python examples.py <comando> [argumentos]")
        print("\nComandos disponibles:")
        print("  descargar_datos              - Descargar 10 temporadas de 3 ligas")
        print("  analizar_equipo [equipo]     - Análisis detallado de un equipo")
        print("  h2h [equipo1] [equipo2]      - Historial directo entre equipos")
        print("  predecir [equipo1] [equipo2] - Predecir probabilidades")
        print("  top_equipos                  - Listar top equipos")
        print("  tendencias                   - Análisis de tendencias")
        print("  exportar                     - Exportar datos para ML")
        print("  validar                      - Validar integridad de datos")
        print("  todos                        - Ejecutar todos los ejemplos")
        sys.exit(1)
    
    comando = sys.argv[1].lower()
    
    try:
        if comando == "descargar_datos":
            ejemplo_1_descargar_datos()
        
        elif comando == "analizar_equipo":
            equipo = sys.argv[2] if len(sys.argv) > 2 else "Liverpool"
            ejemplo_2_analizar_equipo(equipo)
        
        elif comando == "h2h":
            equipo1 = sys.argv[2] if len(sys.argv) > 2 else "Liverpool"
            equipo2 = sys.argv[3] if len(sys.argv) > 3 else "Manchester United"
            ejemplo_3_historial_directo(equipo1, equipo2)
        
        elif comando == "predecir":
            equipo1 = sys.argv[2] if len(sys.argv) > 2 else "Liverpool"
            equipo2 = sys.argv[3] if len(sys.argv) > 3 else "Manchester City"
            ejemplo_4_predecir_partido(equipo1, equipo2)
        
        elif comando == "top_equipos":
            ejemplo_5_top_equipos()
        
        elif comando == "tendencias":
            ejemplo_6_tendencias()
        
        elif comando == "exportar":
            ejemplo_7_exportar_entrenamiento()
        
        elif comando == "validar":
            ejemplo_8_validar_datos()
        
        elif comando == "todos":
            print("Ejecutando todos los ejemplos...")
            ejemplo_1_descargar_datos()
            ejemplo_2_analizar_equipo()
            ejemplo_3_historial_directo()
            ejemplo_4_predecir_partido()
            ejemplo_5_top_equipos()
            ejemplo_6_tendencias()
            ejemplo_7_exportar_entrenamiento()
            ejemplo_8_validar_datos()
        
        else:
            print(f"Comando desconocido: {comando}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
