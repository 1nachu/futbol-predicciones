"""
Team Normalization CLI
======================

Interfaz de línea de comandos para gestionar la normalización de equipos.

Usage:
    python3 src/team_normalization_cli.py add-team "Manchester United" England "Premier League"
    python3 src/team_normalization_cli.py normalize "Man United"
    python3 src/team_normalization_cli.py stats
    python3 src/team_normalization_cli.py export-mappings
    python3 src/team_normalization_cli.py validate
"""

import click
import json
from pathlib import Path
from src.team_normalization import TeamNormalizer
from src.etl_team_integration import TeamETLIntegrator
from tabulate import tabulate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Team Normalization System CLI"""
    pass


# ============================================================================
# COMANDOS: EQUIPOS
# ============================================================================

@cli.command('add-team')
@click.argument('name')
@click.argument('country')
@click.option('--league', default=None, help='Liga')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def add_team(name, country, league, db):
    """Agrega un nuevo equipo a la tabla maestra."""
    normalizer = TeamNormalizer(db_path=db)
    uuid = normalizer.add_team(name, country, league)
    click.secho(f"✓ Equipo agregado: {uuid}", fg='green')
    click.echo(f"  Nombre: {name}")
    click.echo(f"  País: {country}")
    if league:
        click.echo(f"  Liga: {league}")


@cli.command('get-team')
@click.argument('uuid')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def get_team(uuid, db):
    """Muestra información detallada de un equipo."""
    normalizer = TeamNormalizer(db_path=db)
    team = normalizer.get_team(uuid)
    
    if not team:
        click.secho(f"✗ Equipo no encontrado: {uuid}", fg='red')
        return
    
    click.echo("\n" + "="*70)
    click.secho(f"EQUIPO: {team['official_name']}", fg='cyan', bold=True)
    click.echo("="*70)
    click.echo(f"UUID:     {team['team_uuid']}")
    click.echo(f"País:     {team['country']}")
    click.echo(f"Liga:     {team.get('league', 'N/A')}")
    click.echo(f"Creado:   {team['created_at']}")
    click.echo(f"Actualiz: {team['updated_at']}")
    
    if team['mappings']:
        click.echo(f"\n📌 MAPEOS EXTERNOS ({len(team['mappings'])}):")
        mappings_data = []
        for m in team['mappings']:
            mappings_data.append([
                m['source'],
                m['external_id'],
                m['external_name'],
                f"{m['similarity_score']:.0f}%",
                "Auto" if m['is_automatic'] else "Manual"
            ])
        click.echo(tabulate(
            mappings_data,
            headers=['Fuente', 'ID Ext', 'Nombre Ext', 'Similitud', 'Tipo'],
            tablefmt='grid'
        ))
    
    if team['aliases']:
        click.echo(f"\n📝 ALIASES ({len(team['aliases'])}):")
        aliases_data = []
        for a in team['aliases']:
            aliases_data.append([
                a['alias_name'],
                a['priority'],
                a.get('source', 'N/A')
            ])
        click.echo(tabulate(
            aliases_data,
            headers=['Nombre', 'Prioridad', 'Fuente'],
            tablefmt='grid'
        ))
    
    click.echo()


@cli.command('list-teams')
@click.option('--country', default=None, help='Filtrar por país')
@click.option('--league', default=None, help='Filtrar por liga')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def list_teams(country, league, db):
    """Lista todos los equipos en la tabla maestra."""
    normalizer = TeamNormalizer(db_path=db)
    teams = normalizer.get_all_teams()
    
    # Filtrar
    if country:
        teams = [t for t in teams if t['country'].lower() == country.lower()]
    if league:
        teams = [t for t in teams if t.get('league', '').lower() == league.lower()]
    
    if not teams:
        click.secho("No se encontraron equipos", fg='yellow')
        return
    
    teams_data = []
    for t in teams:
        teams_data.append([
            t['official_name'][:30],
            t['country'],
            t.get('league', 'N/A'),
            t['team_uuid'][:8] + '...'
        ])
    
    click.echo("\n" + tabulate(
        teams_data,
        headers=['Nombre', 'País', 'Liga', 'UUID'],
        tablefmt='grid'
    ))
    click.echo(f"\nTotal: {len(teams)} equipos\n")


# ============================================================================
# COMANDOS: NORMALIZACIÓN
# ============================================================================

@cli.command('normalize')
@click.argument('team-name')
@click.option('--source', default=None, help='Fuente de datos')
@click.option('--id', default=None, help='ID externo')
@click.option('--create', is_flag=True, default=True, help='Crear si no existe')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def normalize(team_name, source, id, create, db):
    """Normaliza un nombre de equipo a UUID interno."""
    normalizer = TeamNormalizer(db_path=db)
    uuid, similarity = normalizer.normalize_team(
        team_name=team_name,
        source=source,
        external_id=id,
        create_if_missing=create
    )
    
    if uuid:
        click.secho(f"✓ Normalizado exitosamente", fg='green')
        click.echo(f"  Nombre entrada: {team_name}")
        click.echo(f"  UUID interno:   {uuid}")
        click.echo(f"  Similitud:      {similarity:.1f}%")
        
        # Mostrar equipo encontrado
        team = normalizer.get_team(uuid)
        click.echo(f"  Equipo official: {team['official_name']}")
    else:
        click.secho(f"✗ No se pudo normalizar", fg='red')


@cli.command('add-alias')
@click.argument('uuid')
@click.argument('alias-name')
@click.option('--priority', default=0, type=int, help='Prioridad')
@click.option('--source', default=None, help='Fuente')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def add_alias(uuid, alias_name, priority, source, db):
    """Agrega un alias para un equipo."""
    normalizer = TeamNormalizer(db_path=db)
    alias_id = normalizer.add_alias(uuid, alias_name, priority, source)
    click.secho(f"✓ Alias agregado: {alias_id}", fg='green')
    click.echo(f"  UUID:       {uuid}")
    click.echo(f"  Alias:      {alias_name}")
    click.echo(f"  Prioridad:  {priority}")


@cli.command('add-mapping')
@click.argument('uuid')
@click.argument('source')
@click.argument('external-id')
@click.option('--name', default='', help='Nombre en fuente')
@click.option('--similarity', default=100.0, type=float, help='Similitud')
@click.option('--manual', is_flag=True, help='Mapeo manual (no automático)')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def add_mapping(uuid, source, external_id, name, similarity, manual, db):
    """Agrega un mapeo externo."""
    normalizer = TeamNormalizer(db_path=db)
    mapping_id = normalizer.add_external_mapping(
        team_uuid=uuid,
        source=source,
        external_id=external_id,
        external_name=name or external_id,
        similarity_score=similarity,
        is_automatic=not manual
    )
    click.secho(f"✓ Mapeo agregado: {mapping_id}", fg='green')
    click.echo(f"  UUID:           {uuid}")
    click.echo(f"  Fuente:         {source}")
    click.echo(f"  ID Externo:     {external_id}")
    click.echo(f"  Similitud:      {similarity:.1f}%")


# ============================================================================
# COMANDOS: ESTADÍSTICAS
# ============================================================================

@cli.command('stats')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def stats(db):
    """Muestra estadísticas del sistema."""
    normalizer = TeamNormalizer(db_path=db)
    s = normalizer.get_stats()
    
    click.echo("\n" + "="*60)
    click.secho("📊 ESTADÍSTICAS DEL SISTEMA", fg='cyan', bold=True)
    click.echo("="*60)
    click.echo(f"Total equipos:       {s['total_teams']:>6}")
    click.echo(f"Total mapeos:        {s['total_mappings']:>6}")
    click.echo(f"  Auto-mapeados:     {s['auto_mappings']:>6}")
    click.echo(f"  Manual:            {s['manual_mappings']:>6}")
    click.echo(f"Total aliases:       {s['total_aliases']:>6}")
    click.echo(f"Tamaño caché:        {s['cache_size']:>6}")
    
    if s['mappings_by_source']:
        click.echo("\nMAPEOS POR FUENTE:")
        for source, count in s['mappings_by_source'].items():
            click.echo(f"  {source:20} {count:>6}")
    
    click.echo()


# ============================================================================
# COMANDOS: VALIDACIÓN E INTEGRIDAD
# ============================================================================

@cli.command('validate')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def validate(db):
    """Valida integridad de la base de datos."""
    integrator = TeamETLIntegrator(db_path=db)
    validation = integrator.validate_integrity()
    
    click.echo("\n" + "="*60)
    click.secho("✓ VALIDACIÓN DE INTEGRIDAD", fg='cyan', bold=True)
    click.echo("="*60)
    
    status = '✓' if validation['orphaned_mappings'] == 0 else '✗'
    click.echo(f"{status} Mapeos huérfanos:    {validation['orphaned_mappings']}")
    
    status = '✓' if validation['orphaned_aliases'] == 0 else '✗'
    click.echo(f"{status} Aliases huérfanos:    {validation['orphaned_aliases']}")
    
    status = '✓' if validation['duplicate_aliases'] == 0 else '✗'
    click.echo(f"{status} Duplicados alias:    {validation['duplicate_aliases']}")
    
    click.echo()


@cli.command('report')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def report(db):
    """Genera reporte detallado de mapeos."""
    integrator = TeamETLIntegrator(db_path=db)
    rep = integrator.get_mapping_report()
    
    click.echo("\n" + "="*70)
    click.secho("📋 REPORTE DE MAPEOS", fg='cyan', bold=True)
    click.echo("="*70)
    
    summary = rep['summary']
    click.echo(f"Timestamp:           {rep['timestamp']}")
    click.echo(f"Total equipos:       {summary['total_teams']}")
    click.echo(f"Total mapeos:        {summary['total_mappings']}")
    click.echo(f"Auto-mapeados:       {summary['auto_mappings']}")
    click.echo(f"Manual:              {summary['manual_mappings']}")
    
    if summary['total_mappings'] > 0:
        auto_pct = (summary['auto_mappings'] / summary['total_mappings']) * 100
        click.echo(f"Tasa auto-mapeo:     {auto_pct:.1f}%")
    
    if rep['mappings_by_source']:
        click.echo("\nMAPEOS POR FUENTE:")
        for m in rep['mappings_by_source']:
            click.echo(f"  {m['source']:20} {m['count']:>4} equipos "
                      f"(similitud promedio: {m['avg_similarity']:.1f}%)")
    
    if rep['conflicts_count'] > 0:
        click.secho(f"\n⚠️  CONFLICTOS DETECTADOS: {rep['conflicts_count']}", fg='red')
        for c in rep['conflicts']:
            click.echo(f"  Fuente: {c['source']}")
            click.echo(f"  ID Externo: {c['external_id']}")
            click.echo(f"  UUIDs conflictivos: {c['conflicting_uuids']}")
    else:
        click.secho("\n✓ No hay conflictos detectados", fg='green')
    
    click.echo()


# ============================================================================
# COMANDOS: EXPORTACIÓN
# ============================================================================

@cli.command('export-mappings')
@click.option('--output', default='team_mappings.json', help='Archivo de salida')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def export_mappings(output, db):
    """Exporta mapeos a JSON."""
    normalizer = TeamNormalizer(db_path=db)
    normalizer.export_mappings(output_file=output)
    click.secho(f"✓ Mapeos exportados a {output}", fg='green')


@cli.command('export-teams')
@click.option('--output', default='normalized_teams.csv', help='Archivo de salida')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def export_teams(output, db):
    """Exporta equipos normalizados a CSV."""
    integrator = TeamETLIntegrator(db_path=db)
    integrator.export_normalized_data(output_file=output)
    click.secho(f"✓ Equipos exportados a {output}", fg='green')


# ============================================================================
# COMANDOS: BATCH
# ============================================================================

@cli.command('process-apifootball')
@click.argument('json-file')
@click.option('--season', default=2026, type=int, help='Temporada')
@click.option('--league-id', default=None, type=int, help='ID de liga')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def process_apifootball(json_file, season, league_id, db):
    """Procesa datos de API-Football desde archivo JSON."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    integrator = TeamETLIntegrator(db_path=db)
    processed, new = integrator.process_apifootball_teams(
        teams_data=data,
        season=season,
        league_id=league_id
    )
    
    click.secho(f"✓ Procesamiento completado", fg='green')
    click.echo(f"  Procesados: {processed}")
    click.echo(f"  Nuevos:     {new}\n")


@cli.command('process-footballdata')
@click.argument('csv-file')
@click.option('--league', default='Unknown', help='Liga')
@click.option('--db', default='data/databases/football_data.db', help='Ruta BD')
def process_footballdata(csv_file, league, db):
    """Procesa datos de Football-Data desde CSV."""
    integrator = TeamETLIntegrator(db_path=db)
    processed, new = integrator.process_footballdata_teams(
        csv_file=csv_file,
        league=league
    )
    
    click.secho(f"✓ Procesamiento completado", fg='green')
    click.echo(f"  Procesados: {processed}")
    click.echo(f"  Nuevos:     {new}\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    cli()
