#!/usr/bin/env python3
"""
Setup & Validation Script
===========================

Script para validar la instalación y configuración del ETL.
Asegura que todas las dependencias estén disponibles.

Uso:
    python setup_etl.py
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verifica que Python sea >= 3.8"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ requerido (tienes {sys.version_info.major}.{sys.version_info.minor})")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_required_packages():
    """Verifica que los paquetes requeridos estén instalados"""
    required = [
        'pandas',
        'numpy',
        'requests',
        'sqlalchemy',
        'streamlit'
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_file_structure():
    """Verifica la estructura de directorios"""
    base_dir = Path(__file__).parent
    
    required_dirs = [
        'src',
        'data',
        'logs',
        'docs'
    ]
    
    required_files = [
        'src/etl_football_data.py',
        'src/etl_cli.py',
        'src/etl_config.py',
        'src/etl_data_analysis.py',
        'requirements.txt',
        'ETL_QUICKSTART.md'
    ]
    
    all_ok = True
    
    print("\n📁 Estructura de directorios:")
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (crear con: mkdir {dir_name})")
            all_ok = False
    
    print("\n📄 Archivos principales:")
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file_name} ({size:,} bytes)")
        else:
            print(f"❌ {file_name}")
            all_ok = False
    
    return all_ok


def test_import():
    """Prueba que los módulos ETL se pueden importar"""
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    
    modules = [
        'etl_football_data',
        'etl_cli',
        'etl_config',
        'etl_data_analysis'
    ]
    
    print("\n🔧 Módulos ETL:")
    all_ok = True
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {str(e)}")
            all_ok = False
    
    return all_ok


def main():
    """Función principal"""
    
    print("\n" + "="*70)
    print("🔧 SETUP & VALIDACIÓN - ETL FOOTBALL DATA")
    print("="*70 + "\n")
    
    # 1. Python version
    print("📌 Python Version:")
    py_ok = check_python_version()
    
    # 2. Paquetes
    print("\n📦 Paquetes Requeridos:")
    pkg_ok, missing = check_required_packages()
    
    if not pkg_ok:
        print(f"\n⚠️  Instalar paquetes faltantes:")
        print(f"   pip install {' '.join(missing)}")
        print(f"\n   O usar:")
        print(f"   pip install -r requirements.txt")
    
    # 3. Estructura
    struct_ok = check_file_structure()
    
    # 4. Imports
    print("\n")
    import_ok = test_import()
    
    # Resumen
    print("\n" + "="*70)
    
    if py_ok and pkg_ok and struct_ok and import_ok:
        print("✅ TODO OK - ETL listo para usar")
        print("\n🚀 Siguiente paso:")
        print("   cd src")
        print("   python etl_cli.py run")
        print("="*70 + "\n")
        return 0
    else:
        print("❌ Hay problemas a resolver")
        print("\n💡 Recomendaciones:")
        if not py_ok:
            print("   • Actualizar Python a 3.8+")
        if not pkg_ok:
            print(f"   • Instalar: pip install -r requirements.txt")
        if not struct_ok:
            print("   • Crear directorios faltantes")
        if not import_ok:
            print("   • Reinstalar paquetes: pip install --upgrade -r requirements.txt")
        print("="*70 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
