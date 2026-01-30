#!/usr/bin/env python3
"""
CLI para ejecutar ETL Pipeline
===============================

Script ejecutable para descargar, transformar y cargar datos de fútbol.

Uso:
    python etl_cli.py --help
    python etl_cli.py run                                    # Ejecutar con defaults
    python etl_cli.py run --ligas E0,SP1                    # Ligas específicas
    python etl_cli.py run --db-type postgresql               # PostgreSQL
    python etl_cli.py stats                                  # Ver estadísticas
    python etl_cli.py validate                               # Validar datos
    python etl_cli.py export --output report.xlsx            # Exportar a Excel

Autor: Data Engineering Team
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from etl_football_data import (
    FootballETLPipeline,
    FootballDataLoader,
    obtener_resumen_bd,
    logger
)
from etl_config import (
    DATABASE_CONFIG,
    ETL_CONFIG,
    DB_DIR,
    LOGS_DIR
)


class ETLCliManager:
    """Gestor de CLI para ETL"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def run(self, db_type: str, connection_string: str, ligas: str, 
            skip_create_tables: bool = False) -> bool:
        """Ejecuta el pipeline ETL completo"""
        
        print("\n" + "="*80)
        print("🚀 FOOTBALL DATA ETL PIPELINE")
        print("="*80 + "\n")
        
        # Validar entrada
        ligas_lista = [l.strip().upper() for l in ligas.split(',')]
        print(f"📊 Ligas a procesar: {', '.join(ligas_lista)}")
        print(f"💾 Base de datos: {db_type.upper()}")
        print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # Crear pipeline
            pipeline = FootballETLPipeline(db_type, connection_string)
            
            # Ejecutar
            exitoso = pipeline.ejecutar(ligas_lista, crear_tablas=not skip_create_tables)
            
            if exitoso:
                self._mostrar_tiempo_ejecucion()
                self._mostrar_estadisticas(db_type, connection_string)
                return True
            else:
                logger.error("❌ Pipeline falló")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error fatal: {str(e)}")
            return False
    
    def stats(self, db_type: str, connection_string: str):
        """Muestra estadísticas de datos cargados"""
        
        print("\n" + "="*80)
        print("📊 ESTADÍSTICAS DE DATOS CARGADOS")
        print("="*80 + "\n")
        
        try:
            df_stats = obtener_resumen_bd(db_type, connection_string)
            
            if df_stats.empty:
                print("⚠️  No hay datos en la base de datos")
                return
            
            print(df_stats.to_string(index=False))
            
            # Resumen
            print("\n" + "-"*80)
            total_registros = df_stats['total_matches'].sum()
            total_equipos = df_stats['unique_teams'].sum()
            print(f"\n✓ Total de registros: {total_registros:,}")
            print(f"✓ Total de equipos únicos: {total_equipos:,}")
            print(f"✓ Promedio goles por partido: {df_stats['avg_goles'].mean():.2f}")
            print(f"✓ % partidos Over 2.5: {df_stats['pct_over_25'].mean()*100:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {str(e)}")
    
    def validate(self, db_type: str, connection_string: str):
        """Valida integridad de datos"""
        
        print("\n" + "="*80)
        print("✅ VALIDACIÓN DE INTEGRIDAD DE DATOS")
        print("="*80 + "\n")
        
        try:
            loader = FootballDataLoader(db_type, connection_string)
            
            with loader.engine.connect() as conn:
                # Total de registros
                total = pd.read_sql("SELECT COUNT(*) as total FROM matches", conn)
                print(f"✓ Total de registros: {total['total'].values[0]:,}")
                
                # Valores NULL
                nulls = pd.read_sql("""
                    SELECT 
                        COUNT(CASE WHEN home_team IS NULL THEN 1 END) as null_home,
                        COUNT(CASE WHEN away_team IS NULL THEN 1 END) as null_away,
                        COUNT(CASE WHEN ftr IS NULL THEN 1 END) as null_ftr,
                        COUNT(CASE WHEN b365h IS NULL THEN 1 END) as null_cuotas
                    FROM matches
                """, conn)
                
                print(f"✓ NULL valores:")
                print(f"  - HomeTeam: {nulls['null_home'].values[0]}")
                print(f"  - AwayTeam: {nulls['null_away'].values[0]}")
                print(f"  - FTR: {nulls['null_ftr'].values[0]}")
                print(f"  - Cuotas: {nulls['null_cuotas'].values[0]}")
                
                # Duplicados
                duplicados = pd.read_sql("""
                    SELECT COUNT(*) as duplicados FROM (
                        SELECT date, home_team, away_team, fthg, ftag
                        FROM matches
                        GROUP BY date, home_team, away_team, fthg, ftag
                        HAVING COUNT(*) > 1
                    ) t
                """, conn)
                
                print(f"✓ Registros duplicados: {duplicados['duplicados'].values[0]}")
                
                # FTR válidos
                ftr_invalidos = pd.read_sql("""
                    SELECT COUNT(*) as invalidos FROM matches
                    WHERE ftr NOT IN ('1', 'D', '2')
                """, conn)
                
                print(f"✓ FTR inválidos: {ftr_invalidos['invalidos'].values[0]}")
                
                print("\n✅ Validación completada")
                
        except Exception as e:
            logger.error(f"❌ Error en validación: {str(e)}")
    
    def export(self, db_type: str, connection_string: str, output: str):
        """Exporta datos a Excel"""
        
        print(f"\n📥 Exportando datos a {output}...")
        
        try:
            loader = FootballDataLoader(db_type, connection_string)
            
            with loader.engine.connect() as conn:
                df = pd.read_sql("SELECT * FROM matches ORDER BY date DESC", conn)
                
                # Crear archivo Excel con múltiples sheets
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Sheet 1: Todos los datos
                    df.to_excel(writer, sheet_name='matches', index=False)
                    
                    # Sheet 2: Resumen por temporada
                    df_temp = pd.read_sql("""
                        SELECT 
                            temporada,
                            COUNT(*) as total_matches,
                            COUNT(DISTINCT home_team) as equipos,
                            ROUND(AVG(fthg + ftag), 2) as avg_goles
                        FROM matches
                        GROUP BY temporada
                        ORDER BY temporada DESC
                    """, conn)
                    df_temp.to_excel(writer, sheet_name='summary', index=False)
                
                print(f"✓ {len(df):,} registros exportados a {output}")
                
        except Exception as e:
            logger.error(f"❌ Error exportando: {str(e)}")
    
    def _mostrar_tiempo_ejecucion(self):
        """Muestra tiempo total de ejecución"""
        duracion = (datetime.now() - self.start_time).total_seconds()
        minutos = int(duracion // 60)
        segundos = int(duracion % 60)
        print(f"\n⏱️  Tiempo total: {minutos}m {segundos}s")
    
    def _mostrar_estadisticas(self, db_type: str, connection_string: str):
        """Muestra estadísticas finales"""
        print("\n" + "-"*80)
        print("📈 ESTADÍSTICAS FINALES\n")
        self.stats(db_type, connection_string)


def crear_parser() -> argparse.ArgumentParser:
    """Crea parser de argumentos"""
    
    parser = argparse.ArgumentParser(
        description='ETL Pipeline para Football Data (football-data.co.uk)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ejecutar pipeline completo
  %(prog)s run
  
  # Solo Premier League y La Liga
  %(prog)s run --ligas E0,SP1
  
  # Usar PostgreSQL
  %(prog)s run --db-type postgresql --connection "postgresql://user:pass@localhost/football"
  
  # Ver estadísticas
  %(prog)s stats
  
  # Validar datos
  %(prog)s validate
  
  # Exportar a Excel
  %(prog)s export --output datos.xlsx
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # Comando: run
    run_parser = subparsers.add_parser('run', help='Ejecutar ETL pipeline')
    run_parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgresql'],
        default='sqlite',
        help='Tipo de base de datos (default: sqlite)'
    )
    run_parser.add_argument(
        '--connection',
        type=str,
        default=None,
        help='String de conexión (default: auto-detectado)'
    )
    run_parser.add_argument(
        '--ligas',
        type=str,
        default='E0,SP1,D1',
        help='Códigos de ligas separados por coma (default: E0,SP1,D1)'
    )
    run_parser.add_argument(
        '--skip-create-tables',
        action='store_true',
        help='No crear/reinicializar tablas'
    )
    
    # Comando: stats
    stats_parser = subparsers.add_parser('stats', help='Ver estadísticas')
    stats_parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgresql'],
        default='sqlite',
        help='Tipo de base de datos'
    )
    stats_parser.add_argument(
        '--connection',
        type=str,
        default=None,
        help='String de conexión'
    )
    
    # Comando: validate
    validate_parser = subparsers.add_parser('validate', help='Validar datos')
    validate_parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgresql'],
        default='sqlite',
        help='Tipo de base de datos'
    )
    validate_parser.add_argument(
        '--connection',
        type=str,
        default=None,
        help='String de conexión'
    )
    
    # Comando: export
    export_parser = subparsers.add_parser('export', help='Exportar a Excel')
    export_parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgresql'],
        default='sqlite',
        help='Tipo de base de datos'
    )
    export_parser.add_argument(
        '--connection',
        type=str,
        default=None,
        help='String de conexión'
    )
    export_parser.add_argument(
        '--output',
        type=str,
        default='football_data_export.xlsx',
        help='Archivo de salida (default: football_data_export.xlsx)'
    )
    
    return parser


def obtener_connection_string(db_type: str, connection: Optional[str]) -> str:
    """Obtiene string de conexión automáticamente si no se proporciona"""
    if connection:
        return connection
    
    config = DATABASE_CONFIG[db_type]
    return config['connection_string']


def main():
    """Punto de entrada principal"""
    
    parser = crear_parser()
    args = parser.parse_args()
    
    # Si no hay comando, mostrar ayuda
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Obtener connection string
    connection_string = obtener_connection_string(args.db_type, args.connection)
    
    # Crear gestor CLI
    manager = ETLCliManager()
    
    # Ejecutar comando
    try:
        if args.command == 'run':
            exitoso = manager.run(
                args.db_type,
                connection_string,
                args.ligas,
                args.skip_create_tables
            )
            sys.exit(0 if exitoso else 1)
        
        elif args.command == 'stats':
            manager.stats(args.db_type, connection_string)
        
        elif args.command == 'validate':
            manager.validate(args.db_type, connection_string)
        
        elif args.command == 'export':
            manager.export(args.db_type, connection_string, args.output)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
