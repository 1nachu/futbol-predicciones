"""
Team Normalization Integration Examples
========================================

Ejemplos prácticos de uso del sistema de normalización de equipos
integrado con el ETL existente del proyecto.

Requiere:
- src/team_normalization.py
- src/etl_team_integration.py
- src/etl_football_data.py (ETL existente)
- src/api_football_enricher.py (API-Football)
"""

from src.team_normalization import TeamNormalizer
from src.etl_team_integration import TeamETLIntegrator


# ============================================================================
# EJEMPLO 1: Setup Inicial - Crear Tabla Maestra
# ============================================================================

def ejemplo_1_setup_inicial():
    """
    Crea una tabla maestra con los principales equipos de las 
    tres ligas españolas.
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Setup Inicial - Tabla Maestra")
    print("="*70 + "\n")
    
    normalizer = TeamNormalizer()
    
    # Datos: (nombre, país, liga)
    teams = [
        # La Liga
        ("Real Madrid CF", "Spain", "La Liga"),
        ("FC Barcelona", "Spain", "La Liga"),
        ("Atlético Madrid", "Spain", "La Liga"),
        ("Valencia CF", "Spain", "La Liga"),
        ("Sevilla FC", "Spain", "La Liga"),
        ("Real Sociedad", "Spain", "La Liga"),
        ("Real Betis Balompié", "Spain", "La Liga"),
        ("Athletic Club", "Spain", "La Liga"),
        
        # Premier League
        ("Manchester United", "England", "Premier League"),
        ("Liverpool FC", "England", "Premier League"),
        ("Manchester City", "England", "Premier League"),
        ("Chelsea FC", "England", "Premier League"),
        ("Arsenal FC", "England", "Premier League"),
        ("Tottenham Hotspur", "England", "Premier League"),
        ("Newcastle United", "England", "Premier League"),
        
        # Ligue 1
        ("Paris Saint-Germain", "France", "Ligue 1"),
        ("AS Monaco", "France", "Ligue 1"),
        ("Olympique Lyonnais", "France", "Ligue 1"),
        ("Olympique de Marseille", "France", "Ligue 1"),
        ("RC Lens", "France", "Ligue 1"),
    ]
    
    print("Agregando equipos a tabla maestra...\n")
    for name, country, league in teams:
        uuid = normalizer.add_team(name, country, league)
        print(f"  ✓ {name:30} {country:15} {league:15}")
    
    # Estadísticas
    stats = normalizer.get_stats()
    print(f"\n✓ Total equipos en maestra: {stats['total_teams']}")


# ============================================================================
# EJEMPLO 2: Agregar Aliases (Apodos)
# ============================================================================

def ejemplo_2_aliases():
    """
    Agrega aliases para facilitar búsquedas con nombres cortos o apodos.
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Agregar Aliases (Apodos)")
    print("="*70 + "\n")
    
    normalizer = TeamNormalizer()
    
    # Obtener UUID de Manchester United
    uuid_mu, _ = normalizer.normalize_team("Manchester United")
    uuid_rm, _ = normalizer.normalize_team("Real Madrid CF")
    uuid_fcb, _ = normalizer.normalize_team("FC Barcelona")
    
    print("Agregando aliases...\n")
    
    normalizer.add_alias(uuid_mu, "Man United", priority=10)
    normalizer.add_alias(uuid_mu, "Manchester Utd", priority=9)
    normalizer.add_alias(uuid_mu, "MUFC", priority=8)
    print("  ✓ Manchester United: Man United, Manchester Utd, MUFC")
    
    normalizer.add_alias(uuid_rm, "Real Madrid", priority=10)
    normalizer.add_alias(uuid_rm, "RM", priority=9)
    print("  ✓ Real Madrid CF: Real Madrid, RM")
    
    normalizer.add_alias(uuid_fcb, "Barcelona", priority=10)
    normalizer.add_alias(uuid_fcb, "Barça", priority=9)
    normalizer.add_alias(uuid_fcb, "FCB", priority=8)
    print("  ✓ FC Barcelona: Barcelona, Barça, FCB")
    
    # Probar búsquedas
    print("\nProbando búsquedas con aliases:")
    names = ["Man United", "Real Madrid", "Barcelona", "Barça"]
    for name in names:
        uuid, sim = normalizer.normalize_team(name)
        status = "✓" if uuid else "✗"
        print(f"  {status} '{name}' → UUID encontrado (similitud: {sim:.0f}%)")


# ============================================================================
# EJEMPLO 3: Procesar Datos de API-Football
# ============================================================================

def ejemplo_3_apifootball():
    """
    Procesa datos de API-Football v3 y los normaliza automáticamente.
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Procesar Datos de API-Football")
    print("="*70 + "\n")
    
    # Simular datos de API-Football
    apifootball_teams = [
        {
            'id': 33,
            'name': 'Manchester United',
            'country': 'England'
        },
        {
            'id': 40,
            'name': 'Liverpool',
            'country': 'England'
        },
        {
            'id': 541,
            'name': 'Real Madrid',
            'country': 'Spain'
        },
        {
            'id': 529,
            'name': 'Barcelona',
            'country': 'Spain'
        },
    ]
    
    integrator = TeamETLIntegrator()
    
    print("Procesando datos de API-Football...\n")
    processed, new = integrator.process_apifootball_teams(apifootball_teams)
    
    print(f"\n✓ Procesados: {processed}")
    print(f"✓ Nuevos: {new}")
    
    # Mostrar estadísticas
    stats = integrator.normalizer.get_stats()
    print(f"\n📊 Estadísticas:")
    print(f"  Total equipos: {stats['total_teams']}")
    print(f"  Total mapeos: {stats['total_mappings']}")
    print(f"  Auto-mapeados: {stats['auto_mappings']}")
    print(f"  Manual: {stats['manual_mappings']}")


# ============================================================================
# EJEMPLO 4: Procesar Múltiples Fuentes y Reconciliar
# ============================================================================

def ejemplo_4_reconciliacion_multisource():
    """
    Procesa datos de múltiples fuentes y genera un reporte de reconciliación.
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Reconciliación de Múltiples Fuentes")
    print("="*70 + "\n")
    
    integrator = TeamETLIntegrator()
    
    # Simular datos de Football-Data.org API
    print("1. Procesando Football-Data.org API...\n")
    footballdataorg = {
        'teams': [
            {
                'id': 66,
                'name': 'Manchester United',
                'area': {'name': 'England'}
            },
            {
                'id': 64,
                'name': 'Liverpool',
                'area': {'name': 'England'}
            },
            {
                'id': 541,
                'name': 'Real Madrid Club de Fútbol',
                'area': {'name': 'Spain'}
            },
        ]
    }
    p1, n1 = integrator.process_footballdataorg_api(footballdataorg)
    print(f"   Procesados: {p1}, Nuevos: {n1}\n")
    
    # Simular datos de API-Football
    print("2. Procesando API-Football...\n")
    apifootball = [
        {'id': 33, 'name': 'Manchester United', 'country': 'England'},
        {'id': 40, 'name': 'Liverpool', 'country': 'England'},
        {'id': 541, 'name': 'Real Madrid', 'country': 'Spain'},
    ]
    p2, n2 = integrator.process_apifootball_teams(apifootball)
    print(f"   Procesados: {p2}, Nuevos: {n2}\n")
    
    # Generar reporte
    print("3. Generando reporte de reconciliación...\n")
    report = integrator.get_mapping_report()
    
    print(f"   Equipos totales reconciliados: {report['summary']['total_teams']}")
    print(f"   Total mapeos: {report['summary']['total_mappings']}")
    print(f"   Auto-mapeados: {report['summary']['auto_mappings']}")
    print(f"   Manual: {report['summary']['manual_mappings']}")
    
    if report['summary']['total_mappings'] > 0:
        auto_pct = (report['summary']['auto_mappings'] / 
                   report['summary']['total_mappings']) * 100
        print(f"   Tasa de auto-mapeo: {auto_pct:.1f}%")
    
    print(f"\n   Conflictos detectados: {report['conflicts_count']}")
    
    for conflict in report['conflicts']:
        print(f"     ⚠️  {conflict['source']}/{conflict['external_id']} → "
              f"{conflict['conflicting_uuids']} UUIDs diferentes")


# ============================================================================
# EJEMPLO 5: Resolver Conflictos Manualmente
# ============================================================================

def ejemplo_5_resolver_conflictos():
    """
    Demuestra cómo resolver conflictos detectados entre mapeos.
    """
    print("\n" + "="*70)
    print("EJEMPLO 5: Resolver Conflictos")
    print("="*70 + "\n")
    
    integrator = TeamETLIntegrator()
    
    # Simular conflicto: mismo external_id mapeado a 2 UUIDs
    normalizer = integrator.normalizer
    
    # Crear 2 equipos con el mismo nombre pero ligeramente diferente
    uuid1 = normalizer.add_team("Manchester United FC", "England", "Premier League")
    uuid2 = normalizer.add_team("Manchester United", "England", "Premier League")
    
    # Agregar mapeos del mismo source/id a diferente UUID (conflicto)
    normalizer.add_external_mapping(
        team_uuid=uuid1,
        source="footballdata",
        external_id="66",
        external_name="Manchester United",
        similarity_score=100.0,
        is_automatic=False
    )
    
    # Generar reporte
    report = integrator.get_mapping_report()
    
    if report['conflicts_count'] > 0:
        print(f"Conflictos detectados: {report['conflicts_count']}\n")
        
        for conflict in report['conflicts']:
            print(f"Conflicto encontrado:")
            print(f"  Fuente: {conflict['source']}")
            print(f"  ID Externo: {conflict['external_id']}")
            print(f"  UUIDs conflictivos: {conflict['conflicting_uuids']}")
            print(f"  Mapeos: {conflict['team_uuids']}\n")
            
            print("Resolución (opción manual):")
            print(f"  1. Investigar cuál es el UUID correcto")
            print(f"  2. Remover el mapeo incorrecto")
            print(f"  3. Mergear los equipos duplicados en la tabla maestra")
    else:
        print("✓ No hay conflictos detectados")


# ============================================================================
# EJEMPLO 6: Exportar Datos Normalizados
# ============================================================================

def ejemplo_6_exportar():
    """
    Exporta datos normalizados a diferentes formatos.
    """
    print("\n" + "="*70)
    print("EJEMPLO 6: Exportar Datos Normalizados")
    print("="*70 + "\n")
    
    integrator = TeamETLIntegrator()
    
    # Exportar a CSV
    print("1. Exportando a CSV...")
    csv_file = integrator.export_normalized_data(
        output_file="normalized_teams.csv"
    )
    print(f"   ✓ Exportado: {csv_file}\n")
    
    # Exportar mapeos a JSON
    print("2. Exportando mapeos a JSON...")
    integrator.normalizer.export_mappings(
        output_file="team_mappings.json"
    )
    print(f"   ✓ Exportado: team_mappings.json\n")
    
    print("Archivos generados:")
    print("  • normalized_teams.csv (equipos + mapeos)")
    print("  • team_mappings.json (mapeos detallados)")


# ============================================================================
# EJEMPLO 7: Validación de Integridad
# ============================================================================

def ejemplo_7_validacion():
    """
    Valida la integridad de la base de datos.
    """
    print("\n" + "="*70)
    print("EJEMPLO 7: Validación de Integridad")
    print("="*70 + "\n")
    
    integrator = TeamETLIntegrator()
    
    print("Ejecutando validación...\n")
    validation = integrator.validate_integrity()
    
    print("Resultados:")
    print(f"  Mapeos huérfanos: {validation['orphaned_mappings']}")
    print(f"  Aliases huérfanos: {validation['orphaned_aliases']}")
    print(f"  Aliases duplicados: {validation['duplicate_aliases']}")
    
    if (validation['orphaned_mappings'] == 0 and 
        validation['orphaned_aliases'] == 0 and 
        validation['duplicate_aliases'] == 0):
        print("\n✓ BD íntegra, sin errores detectados")
    else:
        print("\n⚠️  Errores detectados, revisar logs")


# ============================================================================
# EJEMPLO 8: Búsquedas Fuzzy en Tiempo Real
# ============================================================================

def ejemplo_8_fuzzy_search():
    """
    Demuestra búsquedas fuzzy matching en tiempo real.
    """
    print("\n" + "="*70)
    print("EJEMPLO 8: Búsquedas Fuzzy en Tiempo Real")
    print("="*70 + "\n")
    
    normalizer = TeamNormalizer()
    
    # Agregar algunos equipos primero
    normalizer.add_team("Manchester United FC", "England", "Premier League")
    normalizer.add_team("Liverpool FC", "England", "Premier League")
    normalizer.add_team("Real Madrid CF", "Spain", "La Liga")
    normalizer.add_team("FC Barcelona", "Spain", "La Liga")
    
    # Agregar aliases
    uuid_mu, _ = normalizer.normalize_team("Manchester United FC")
    normalizer.add_alias(uuid_mu, "Man United", priority=10)
    
    print("Probando búsquedas fuzzy:\n")
    
    test_cases = [
        ("Manchester United", "Nombre exacto"),
        ("manchester united", "Lowercase"),
        ("Man United", "Alias"),
        ("Manchester Utd", "Variante similar"),
        ("Manchester", "Parcial fuzzy"),
        ("Manchester City", "Similar pero diferente"),
        ("Real Madrid", "Fuzzy match España"),
        ("Liverpool FC", "Otro equipo"),
    ]
    
    for name, description in test_cases:
        uuid, similarity = normalizer.normalize_team(name)
        
        if uuid:
            team = normalizer.get_team(uuid)
            status = "✓"
            print(f"{status} '{name:25}' ({description:20}) "
                  f"→ {team['official_name']:25} ({similarity:.0f}%)")
        else:
            status = "✗"
            print(f"{status} '{name:25}' ({description:20}) "
                  f"→ NO ENCONTRADO")


# ============================================================================
# MAIN: Ejecutar todos los ejemplos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "TEAM NORMALIZATION - EJEMPLOS DE USO" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    ejemplos = [
        ("1", "Setup Inicial", ejemplo_1_setup_inicial),
        ("2", "Agregar Aliases", ejemplo_2_aliases),
        ("3", "Procesar API-Football", ejemplo_3_apifootball),
        ("4", "Reconciliación Multi-fuente", ejemplo_4_reconciliacion_multisource),
        ("5", "Resolver Conflictos", ejemplo_5_resolver_conflictos),
        ("6", "Exportar Datos", ejemplo_6_exportar),
        ("7", "Validación de Integridad", ejemplo_7_validacion),
        ("8", "Búsquedas Fuzzy", ejemplo_8_fuzzy_search),
    ]
    
    print("\nEjemplos disponibles:")
    for num, desc, _ in ejemplos:
        print(f"  {num}. {desc}")
    
    print("\nEjecutando todos los ejemplos...\n")
    
    for num, desc, func in ejemplos:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error en ejemplo {num}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✓ TODOS LOS EJEMPLOS COMPLETADOS")
    print("="*70 + "\n")
