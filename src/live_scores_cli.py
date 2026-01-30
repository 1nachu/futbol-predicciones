#!/usr/bin/env python3
"""
Live Scores CLI
===============

Interfaz de línea de comandos para Live Scores.

Uso:
    python live_scores_cli.py monitor              # Monitorear en vivo
    python live_scores_cli.py status               # Ver estado actual
    python live_scores_cli.py export --output file # Exportar datos
    python live_scores_cli.py validate-key         # Validar API Key
    python live_scores_cli.py competitions         # Listar competiciones

Autor: Backend Integration Team
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# Configurar path
sys.path.insert(0, str(Path(__file__).parent))

from football_api_client import (
    FootballDataClient, validate_api_key,
    FootballAPIError, AuthenticationError
)
from live_scores import (
    LiveScoresManager, DefaultCallbacks, MatchEvent
)

# ========== CONFIGURACIÓN ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveScoresCLI:
    """CLI para Live Scores"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa CLI"""
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        self.client = None
        self.manager = None
    
    def validate_api_key(self) -> bool:
        """Valida API Key"""
        if not self.api_key:
            print("❌ API Key no configurada")
            print("   Configura: export FOOTBALL_DATA_API_KEY=tu_clave")
            return False
        
        if not validate_api_key(self.api_key):
            print("❌ API Key inválida (formato incorrecto)")
            return False
        
        return True
    
    def initialize_client(self) -> bool:
        """Inicializa cliente de API"""
        if not self.validate_api_key():
            return False
        
        try:
            self.client = FootballDataClient(self.api_key)
            print("✓ Cliente inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando cliente: {e}")
            return False
    
    def initialize_manager(self) -> bool:
        """Inicializa manager de live scores"""
        if not self.client:
            if not self.initialize_client():
                return False
        
        try:
            self.manager = LiveScoresManager(self.client)
            print("✓ Manager de live scores inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando manager: {e}")
            return False
    
    def cmd_validate_key(self) -> int:
        """Valida la API Key"""
        print("\n" + "="*70)
        print("🔑 VALIDAR API KEY")
        print("="*70 + "\n")
        
        if not self.validate_api_key():
            return 1
        
        print(f"✓ API Key válida")
        print(f"  Token: {self.api_key[:10]}...{self.api_key[-10:]}")
        
        # Intentar conexión
        try:
            if not self.initialize_client():
                return 1
            
            status = self.client.get_rate_limit_status()
            print(f"\n✓ Conexión a API exitosa")
            print(f"  Rate Limit: {status['capacity']} req/{status['refill_time']}s")
            print(f"  Tokens disponibles: {status['available_tokens']:.2f}")
            
            return 0
        except Exception as e:
            print(f"❌ Error conectando a API: {e}")
            return 1
    
    def cmd_competitions(self) -> int:
        """Lista competiciones disponibles"""
        print("\n" + "="*70)
        print("🏆 COMPETICIONES DISPONIBLES")
        print("="*70 + "\n")
        
        if not self.initialize_client():
            return 1
        
        try:
            competitions = self.client.get_competitions()
            
            print(f"{'Código':<8} {'Nombre':<40} {'Plan':<15}")
            print("-" * 70)
            
            for comp in competitions[:20]:  # Primeras 20
                code = comp.get('code', 'N/A')
                name = comp.get('name', 'N/A')[:38]
                plan = comp.get('plan', 'N/A')
                print(f"{code:<8} {name:<40} {plan:<15}")
            
            print(f"\n✓ Total: {len(competitions)} competiciones")
            
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    def cmd_monitor(self, duration: int = 300, interval: int = 30) -> int:
        """Monitorea live scores en tiempo real"""
        print("\n" + "="*70)
        print("⚽ MONITOREO DE LIVE SCORES EN TIEMPO REAL")
        print("="*70 + "\n")
        
        if not self.initialize_manager():
            return 1
        
        # Registrar callbacks
        self.manager.register_callback(DefaultCallbacks.console_callback)
        self.manager.register_callback(DefaultCallbacks.log_callback)
        
        # Iniciar polling
        self.manager.start_polling(interval=interval)
        
        print(f"✓ Polling iniciado (intervalo: {interval}s)")
        print(f"✓ Duración: {duration}s")
        print(f"✓ Presiona Ctrl+C para detener\n")
        
        try:
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Mostrar estado cada 30 segundos
                time.sleep(30)
                
                stats = self.manager.get_statistics()
                
                print(f"\n📊 Estado actual:")
                print(f"   Partidos totales: {stats['total_matches']}")
                print(f"   Partidos en vivo: {stats['live_matches']}")
                print(f"   Rate limit: {stats['rate_limit']['available_tokens']:.2f}/{stats['rate_limit']['capacity']} tokens")
                
                # Mostrar partidos en vivo
                live = self.manager.get_live_matches()
                if live:
                    print(f"\n   En vivo:")
                    for match in live:
                        print(
                            f"     ⚽ {match['home_team']} "
                            f"{match['home_score']}-{match['away_score']} "
                            f"{match['away_team']}"
                        )
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrumpido por usuario")
        finally:
            self.manager.stop_polling()
            print("✓ Polling detenido")
        
        return 0
    
    def cmd_status(self) -> int:
        """Muestra estado actual"""
        print("\n" + "="*70)
        print("📊 ESTADO ACTUAL DE LIVE SCORES")
        print("="*70 + "\n")
        
        if not self.initialize_manager():
            return 1
        
        # Realizar un poll único
        print("Actualizando datos...")
        for comp in self.manager.competitions:
            self.manager.poll_competition(comp)
        
        # Mostrar estadísticas
        stats = self.manager.get_statistics()
        
        print(f"\n✓ Total de partidos: {stats['total_matches']}")
        print(f"✓ Partidos en vivo: {stats['live_matches']}")
        
        print(f"\nPor estado:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status}: {count}")
        
        # Mostrar partidos en vivo
        live = self.manager.get_live_matches()
        if live:
            print(f"\n⚽ PARTIDOS EN VIVO:")
            for match in live:
                print(
                    f"  [{match['competition']}] "
                    f"{match['home_team']} "
                    f"{match['home_score']}-{match['away_score']} "
                    f"{match['away_team']}"
                )
        else:
            print(f"\nℹ️  No hay partidos en vivo en este momento")
        
        # Rate limit
        print(f"\n📡 Rate Limit:")
        rate = stats['rate_limit']
        print(f"  Tokens disponibles: {rate['available_tokens']:.2f}/{rate['capacity']}")
        print(f"  Tiempo de espera: {rate['wait_time']:.2f}s")
        print(f"  Entradas en caché: {rate['cache_entries']}")
        
        return 0
    
    def cmd_export(self, output_file: str) -> int:
        """Exporta datos a JSON"""
        print("\n" + "="*70)
        print("📥 EXPORTAR DATOS")
        print("="*70 + "\n")
        
        if not self.initialize_manager():
            return 1
        
        print(f"Exportando a {output_file}...")
        
        try:
            self.manager.export_to_json(output_file)
            print(f"✓ Exportado exitosamente")
            
            # Mostrar estadísticas
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n✓ Datos exportados:")
            print(f"  Timestamp: {data['timestamp']}")
            print(f"  Partidos en vivo: {len(data['live_matches'])}")
            
            return 0
        except Exception as e:
            print(f"❌ Error exportando: {e}")
            return 1
    
    def cmd_detailed_stats(self) -> int:
        """Muestra estadísticas detalladas"""
        print("\n" + "="*70)
        print("📈 ESTADÍSTICAS DETALLADAS")
        print("="*70 + "\n")
        
        if not self.initialize_manager():
            return 1
        
        for comp in self.manager.competitions:
            status = self.manager.get_competition_status(comp)
            
            print(f"\n🏆 {comp}")
            print(f"  Total: {status['total_matches']}")
            print(f"  En vivo: {status['live']}")
            print(f"  Programados: {status['scheduled']}")
            print(f"  Finalizados: {status['finished']}")
        
        return 0


def create_parser() -> argparse.ArgumentParser:
    """Crea parser de argumentos"""
    parser = argparse.ArgumentParser(
        description='Live Scores CLI - Monitoreo de marcadores en tiempo real',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Validar API Key
  %(prog)s validate-key
  
  # Listar competiciones
  %(prog)s competitions
  
  # Ver estado actual
  %(prog)s status
  
  # Monitorear 5 minutos
  %(prog)s monitor --duration 300
  
  # Exportar datos
  %(prog)s export --output live_scores.json
  
  # Estadísticas detalladas
  %(prog)s detailed-stats
        """
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Football-Data.org API Key (o usar FOOTBALL_DATA_API_KEY env)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # validate-key
    subparsers.add_parser('validate-key', help='Validar API Key')
    
    # competitions
    subparsers.add_parser('competitions', help='Listar competiciones')
    
    # status
    subparsers.add_parser('status', help='Ver estado actual')
    
    # monitor
    monitor_parser = subparsers.add_parser('monitor', help='Monitorear live scores')
    monitor_parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='Duración del monitoreo en segundos (default: 300)'
    )
    monitor_parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Intervalo entre polls en segundos (default: 30)'
    )
    
    # export
    export_parser = subparsers.add_parser('export', help='Exportar datos')
    export_parser.add_argument(
        '--output',
        type=str,
        default='live_scores.json',
        help='Archivo de salida (default: live_scores.json)'
    )
    
    # detailed-stats
    subparsers.add_parser('detailed-stats', help='Estadísticas detalladas')
    
    return parser


def main():
    """Función principal"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cli = LiveScoresCLI(api_key=args.api_key)
    
    try:
        if args.command == 'validate-key':
            return cli.cmd_validate_key()
        
        elif args.command == 'competitions':
            return cli.cmd_competitions()
        
        elif args.command == 'status':
            return cli.cmd_status()
        
        elif args.command == 'monitor':
            return cli.cmd_monitor(
                duration=args.duration,
                interval=args.interval
            )
        
        elif args.command == 'export':
            return cli.cmd_export(args.output)
        
        elif args.command == 'detailed-stats':
            return cli.cmd_detailed_stats()
        
        else:
            print(f"Comando desconocido: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por usuario")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
