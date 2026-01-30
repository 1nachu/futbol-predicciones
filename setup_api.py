#!/usr/bin/env python3
"""
Setup Script para Timba Predictor
Carga variables de ambiente y valida configuración

Autor: Backend Integration Team
Fecha: 30 de Enero de 2026
"""

import os
import sys
from pathlib import Path

# Cargar variables desde .env manualmente
def load_env_file(env_path):
    """Carga variables de ambiente desde archivo .env"""
    if not env_path.exists():
        return False
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith('#'):
                continue
            # Parsear KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    
    return True

env_path = Path(__file__).parent / '.env'
load_env_file(env_path)

def validar_configuracion():
    """Valida que todas las variables de ambiente estén configuradas"""
    
    print("="*70)
    print("🔧 VALIDANDO CONFIGURACIÓN")
    print("="*70)
    
    # Verificar API-Football
    api_key = os.getenv("API_FOOTBALL_KEY")
    if api_key:
        # Mostrar solo los primeros y últimos 8 caracteres por seguridad
        api_display = f"{api_key[:8]}...{api_key[-8:]}"
        print(f"✓ API_FOOTBALL_KEY: {api_display}")
        
        # Validar que la clave tenga longitud correcta (usualmente 32 hex chars)
        if len(api_key) == 32:
            print("  → Longitud de clave válida (32 caracteres)")
        else:
            print(f"  ⚠️  Longitud inesperada: {len(api_key)} caracteres")
    else:
        print("✗ API_FOOTBALL_KEY no configurada")
        return False
    
    # Verificar directorio de base de datos
    db_path = os.getenv("API_FOOTBALL_DB_PATH", "data/databases/api_football_cache.db")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ API_FOOTBALL_DB_PATH: {db_path}")
    
    # Verificar directorio de logs
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directorio de logs: logs/")
    
    print("="*70)
    print("✅ Configuración validada correctamente")
    print("="*70)
    
    return True


def inicializar_timba_core():
    """Inicializa Timba Core con la configuración cargada"""
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from timba_core import inicializar_timba_core as init_core
        
        timba_core = init_core()
        
        print("\n" + "="*70)
        print("🚀 TIMBA CORE INICIALIZADO")
        print("="*70)
        
        # Probar conectividad con API
        if timba_core.client:
            print("✓ Cliente API-Football conectado")
            
            try:
                quota = timba_core.get_quota_status()
                print(f"✓ Cuota de API disponible: {quota.requests_available}/{quota.requests_available + quota.requests_used}")
                print(f"  - Plan: {quota.plan_name}")
                print(f"  - Reset: {quota.reset_date}")
            except Exception as e:
                print(f"⚠️  No se pudo verificar cuota: {e}")
        else:
            print("⚠️  Cliente API-Football no configurado")
        
        print("="*70 + "\n")
        
        return timba_core
    
    except Exception as e:
        print(f"✗ Error inicializando Timba Core: {e}")
        return None


if __name__ == "__main__":
    # Validar configuración
    if not validar_configuracion():
        sys.exit(1)
    
    # Inicializar Timba Core
    timba_core = inicializar_timba_core()
    
    if timba_core:
        print("\n✅ Sistema listo para usar")
        print("\nEjemplo de uso:")
        print("  from timba_core import obtener_timba_core")
        print("  timba_core = obtener_timba_core()")
        print("  fixtures = timba_core.fetch_daily_fixtures()")
    else:
        print("\n✗ Error inicializando sistema")
        sys.exit(1)
