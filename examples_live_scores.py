#!/usr/bin/env python3
"""
Live Scores Module - Ejemplos Prácticos
========================================

Ejemplos de uso del módulo de Live Scores con Football-Data.org API.

Ejecución:
    python3 examples_live_scores.py

Nota: Requiere FOOTBALL_DATA_API_KEY configurada como variable de entorno
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configurar path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from football_api_client import FootballDataClient, validate_api_key
from live_scores import LiveScoresManager, DefaultCallbacks, MatchEvent


# ========== UTILIDADES ==========

def print_header(title: str):
    """Imprime un encabezado formateado"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_section(title: str):
    """Imprime un encabezado de sección"""
    print(f"\n📌 {title}")
    print("-" * 70)


def get_api_key() -> str:
    """Obtiene API Key de variable de entorno"""
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        print("❌ Error: FOOTBALL_DATA_API_KEY no está configurada")
        print("   Ejecuta: export FOOTBALL_DATA_API_KEY='tu_clave'")
        sys.exit(1)
    
    if not validate_api_key(api_key):
        print("❌ Error: Formato de API Key inválido")
        sys.exit(1)
    
    return api_key


# ========== EJEMPLO 1: VALIDACIÓN Y ESTADO INICIAL ==========

def example_1_validation_and_status():
    """Ejemplo 1: Validar API Key y ver estado inicial"""
    print_header("EJEMPLO 1: Validación y Estado Inicial")
    
    api_key = get_api_key()
    print(f"✓ API Key válida: {api_key[:10]}...{api_key[-10:]}\n")
    
    # Crear cliente
    client = FootballDataClient(api_key)
    print("✓ Cliente inicializado\n")
    
    # Obtener estado de rate limit
    print_section("Rate Limit Status")
    status = client.get_rate_limit_status()
    
    print(f"Capacidad: {status['capacity']} requests")
    print(f"Refill time: {status['refill_time']} segundos")
    print(f"Tokens disponibles: {status['available_tokens']:.2f}")
    print(f"Tiempo de espera: {status['wait_time']:.2f}s")
    print(f"Entradas en caché: {status['cache_entries']}")


# ========== EJEMPLO 2: LISTAR COMPETICIONES ==========

def example_2_list_competitions():
    """Ejemplo 2: Listar todas las competiciones disponibles"""
    print_header("EJEMPLO 2: Listar Competiciones")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    
    print("Obteniendo competiciones...\n")
    
    competitions = client.get_competitions()
    
    print_section("Competiciones Disponibles")
    print(f"{'Código':<8} {'Nombre':<40} {'Plan':<15} {'Área':<15}")
    print("-" * 80)
    
    for comp in competitions[:15]:  # Primeras 15
        code = comp.get('code', 'N/A')
        name = comp.get('name', 'N/A')[:38]
        plan = comp.get('plan', 'N/A')
        area = comp.get('area', {}).get('name', 'N/A')[:13]
        
        print(f"{code:<8} {name:<40} {plan:<15} {area:<15}")
    
    print(f"\n✓ Total: {len(competitions)} competiciones")


# ========== EJEMPLO 3: ESTADO ACTUAL DE PARTIDOS ==========

def example_3_current_matches_status():
    """Ejemplo 3: Ver estado actual de partidos sin polling continuo"""
    print_header("EJEMPLO 3: Estado Actual de Partidos")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    manager = LiveScoresManager(client)
    
    print("Obteniendo partidos actuales...\n")
    
    # Hacer un poll único para cada competición
    for comp in ['PL', 'CL', 'PD']:
        try:
            manager.poll_competition(comp)
        except Exception as e:
            print(f"⚠️  No se pudo obtener {comp}: {e}")
    
    # Mostrar resultados
    print_section("Partidos Actuales")
    
    live = manager.get_live_matches()
    scheduled = [m for m in manager.match_snapshots.values() 
                 if m.status == 'SCHEDULED']
    finished = [m for m in manager.match_snapshots.values() 
                if m.status == 'FINISHED']
    
    print(f"Total de partidos: {len(manager.match_snapshots)}")
    print(f"  En vivo: {len(live)}")
    print(f"  Programados: {len(scheduled)}")
    print(f"  Finalizados: {len(finished)}\n")
    
    if live:
        print("⚽ PARTIDOS EN VIVO:")
        for match in live:
            print(f"  [{match['competition']}] "
                  f"{match['home_team']:<20} "
                  f"{match['home_score']}-{match['away_score']} "
                  f"{match['away_team']:<20} "
                  f"({match['minute']}' minuto)")
    
    if scheduled:
        print("\n📅 PRÓXIMOS PARTIDOS (Primeros 5):")
        for match in scheduled[:5]:
            print(f"  [{match['competition']}] "
                  f"{match['home_team']:<20} vs "
                  f"{match['away_team']:<20}")
    
    if finished:
        print("\n✅ RESULTADOS FINALES (Últimos 5):")
        for match in finished[-5:]:
            print(f"  [{match['competition']}] "
                  f"{match['home_team']:<20} "
                  f"{match['home_score']}-{match['away_score']} "
                  f"{match['away_team']:<20}")


# ========== EJEMPLO 4: MONITOREO CON CALLBACKS ==========

def example_4_monitoring_with_callbacks():
    """Ejemplo 4: Monitorear con callbacks personalizados"""
    print_header("EJEMPLO 4: Monitoreo con Callbacks")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    manager = LiveScoresManager(client)
    
    # Callbacks personalizados
    def goal_alert(event):
        """Alerta de gol"""
        if event['type'] == MatchEvent.GOAL_HOME:
            print(f"\n🎯 ¡GOL! {event['home_team']} marca a los {event['minute']}' min")
        elif event['type'] == MatchEvent.GOAL_AWAY:
            print(f"\n🎯 ¡GOL! {event['away_team']} marca a los {event['minute']}' min")
    
    def match_started(event):
        """Alerta de inicio de partido"""
        if event['type'] == MatchEvent.MATCH_STARTED:
            print(f"\n🔔 ¡Comenzó! {event['home_team']} vs {event['away_team']}")
    
    def match_finished(event):
        """Alerta de fin de partido"""
        if event['type'] == MatchEvent.FULLTIME:
            print(f"\n🏁 ¡Final! {event['home_team']} "
                  f"{event['home_score']}-{event['away_score']} "
                  f"{event['away_team']}")
    
    # Registrar callbacks
    manager.register_callback(goal_alert)
    manager.register_callback(match_started)
    manager.register_callback(match_finished)
    
    print("Iniciando monitoreo durante 60 segundos...\n")
    print("(En una sesión real, esto continuaría indefinidamente)")
    print("(Presiona Ctrl+C para detener)\n")
    
    # Iniciar polling
    manager.start_polling(interval=15)
    
    try:
        # Monitorear 60 segundos
        for i in range(4):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Poll #{i+1}")
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")
    finally:
        manager.stop_polling()
        print("✓ Monitoreo detenido")


# ========== EJEMPLO 5: ESTADÍSTICAS DETALLADAS ==========

def example_5_detailed_statistics():
    """Ejemplo 5: Obtener estadísticas detalladas"""
    print_header("EJEMPLO 5: Estadísticas Detalladas")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    manager = LiveScoresManager(client)
    
    # Hacer un poll
    print("Obteniendo datos de competiciones principales...\n")
    for comp in manager.competitions[:5]:  # Primeras 5
        try:
            manager.poll_competition(comp)
        except Exception as e:
            print(f"⚠️  {comp}: {e}")
    
    # Estadísticas generales
    print_section("Estadísticas Generales")
    stats = manager.get_statistics()
    
    print(f"Total de partidos: {stats['total_matches']}")
    print(f"Partidos en vivo: {stats['live_matches']}")
    print(f"Eventos detectados: {stats['total_events']}\n")
    
    # Por estado
    print_section("Partidos por Estado")
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}")
    
    # Por competición
    print_section("Partidos por Competición")
    for comp, count in sorted(stats['by_competition'].items()):
        if count > 0:
            print(f"  {comp}: {count}")


# ========== EJEMPLO 6: EXPORTAR DATOS ==========

def example_6_export_data():
    """Ejemplo 6: Exportar datos a JSON"""
    print_header("EJEMPLO 6: Exportar Datos")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    manager = LiveScoresManager(client)
    
    print("Obteniendo datos actuales...\n")
    
    # Hacer polls
    for comp in manager.competitions[:3]:
        try:
            manager.poll_competition(comp)
        except Exception as e:
            pass
    
    # Exportar
    output_file = 'live_scores_export.json'
    print(f"Exportando a {output_file}...\n")
    
    manager.export_to_json(output_file)
    
    # Mostrar contenido
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    print_section("Datos Exportados")
    print(f"Timestamp: {data['timestamp']}")
    print(f"Partidos en vivo: {len(data['live_matches'])}")
    print(f"Partidos totales: {len(data.get('all_matches', []))}\n")
    
    # Muestra de partidos en vivo
    if data['live_matches']:
        print("Ejemplo de partidos en vivo:")
        for match in data['live_matches'][:3]:
            print(f"  {match['home_team']} {match['home_score']}-"
                  f"{match['away_score']} {match['away_team']}")
    
    print(f"\n✓ Datos exportados a {output_file}")


# ========== EJEMPLO 7: ANÁLISIS DE DATOS ==========

def example_7_data_analysis():
    """Ejemplo 7: Análisis de datos compilados"""
    print_header("EJEMPLO 7: Análisis de Datos")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    manager = LiveScoresManager(client)
    
    print("Compilando datos de múltiples competiciones...\n")
    
    # Recopilar datos
    total_goals = 0
    matches_by_status = {'LIVE': 0, 'SCHEDULED': 0, 'FINISHED': 0, 'PAUSED': 0}
    
    for comp in manager.competitions[:6]:
        try:
            manager.poll_competition(comp)
        except Exception as e:
            pass
    
    # Analizar
    print_section("Análisis de Datos Compilados")
    
    for match in manager.match_snapshots.values():
        # Contar goles
        total_goals += match.home_score + match.away_score
        # Contar por estado
        if match.status in matches_by_status:
            matches_by_status[match.status] += 1
    
    print(f"Total de partidos analizados: {len(manager.match_snapshots)}")
    print(f"Total de goles: {total_goals}")
    print(f"Promedio de goles por partido: "
          f"{total_goals/max(len(manager.match_snapshots), 1):.2f}\n")
    
    print("Por estado:")
    for status, count in matches_by_status.items():
        if count > 0:
            print(f"  {status}: {count} partidos")
    
    # Top equipos goleadores
    print_section("Top 10 Equipos Goleadores")
    
    teams_goals = {}
    for match in manager.match_snapshots.values():
        teams_goals[match.home_team] = teams_goals.get(match.home_team, 0) + match.home_score
        teams_goals[match.away_team] = teams_goals.get(match.away_team, 0) + match.away_score
    
    sorted_teams = sorted(teams_goals.items(), key=lambda x: x[1], reverse=True)
    
    for i, (team, goals) in enumerate(sorted_teams[:10], 1):
        print(f"  {i:2d}. {team:<25} {goals:3d} goles")


# ========== EJEMPLO 8: MANEJO DE ERRORES ==========

def example_8_error_handling():
    """Ejemplo 8: Manejo robusto de errores"""
    print_header("EJEMPLO 8: Manejo de Errores")
    
    api_key = get_api_key()
    client = FootballDataClient(api_key)
    
    from football_api_client import (
        RateLimitError,
        AuthenticationError,
        NotFoundError,
        FootballAPIError
    )
    
    print_section("Manejando Diferentes Tipos de Errores")
    
    # 1. Verificar autenticación
    print("\n1️⃣  Verificando autenticación...")
    try:
        competitions = client.get_competitions()
        print("   ✓ Autenticación exitosa")
    except AuthenticationError as e:
        print(f"   ❌ Error de autenticación: {e}")
    
    # 2. Verificar rate limiting
    print("\n2️⃣  Verificando rate limiting...")
    try:
        status = client.get_rate_limit_status()
        if status['available_tokens'] < 1:
            print(f"   ⚠️  Rate limit casi alcanzado")
            print(f"      Espera recomendada: {status['wait_time']:.2f}s")
        else:
            print(f"   ✓ Rate limit OK ({status['available_tokens']:.1f} tokens)")
    except RateLimitError as e:
        print(f"   ❌ Rate limit excedido: {e}")
    
    # 3. Manejar competiciones no encontradas
    print("\n3️⃣  Buscando competición inexistente...")
    try:
        matches = client.get_matches('INVALID')
        print("   ✓ Competición encontrada")
    except NotFoundError as e:
        print(f"   ✓ Error capturado correctamente: Competición no existe")
    except FootballAPIError as e:
        print(f"   ✓ Error capturado: {e}")
    
    print("\n✓ Todos los errores fueron manejados correctamente")


# ========== MENÚ PRINCIPAL ==========

def main_menu():
    """Menú principal de ejemplos"""
    print("\n" + "="*70)
    print("  LIVE SCORES MODULE - EJEMPLOS PRÁCTICOS")
    print("="*70 + "\n")
    
    ejemplos = [
        ("1", "Validación y Estado Inicial", example_1_validation_and_status),
        ("2", "Listar Competiciones", example_2_list_competitions),
        ("3", "Estado Actual de Partidos", example_3_current_matches_status),
        ("4", "Monitoreo con Callbacks", example_4_monitoring_with_callbacks),
        ("5", "Estadísticas Detalladas", example_5_detailed_statistics),
        ("6", "Exportar Datos", example_6_export_data),
        ("7", "Análisis de Datos", example_7_data_analysis),
        ("8", "Manejo de Errores", example_8_error_handling),
    ]
    
    print("Ejemplos disponibles:\n")
    
    for num, title, _ in ejemplos:
        print(f"  {num}. {title}")
    
    print("\n  0. Ejecutar todos")
    print("  q. Salir\n")
    
    choice = input("Selecciona un ejemplo (0-8, q): ").strip().lower()
    
    if choice == 'q':
        print("Hasta luego!")
        return
    
    if choice == '0':
        for _, _, func in ejemplos:
            try:
                func()
                time.sleep(2)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(1)
    else:
        for num, _, func in ejemplos:
            if num == choice:
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                return
        
        print("Opción inválida")


if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error no manejado: {e}")
        sys.exit(1)
