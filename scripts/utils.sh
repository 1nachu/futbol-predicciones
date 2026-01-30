#!/bin/bash

# 🎯 SCRIPT PRINCIPAL DE UTILIDADES DEL PROYECTO TIMBA PREDICTOR

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/.venv"
SRC_PATH="$PROJECT_DIR/src"
CONFIG_PATH="$PROJECT_DIR/config"

# Funciones de utilidad
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Verificar virtualenv
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtualenv no encontrado en $VENV_PATH"
        print_warning "Ejecuta primero: $0 init"
        exit 1
    fi
}

# Activar virtualenv
activate_venv() {
    check_venv
    source "$VENV_PATH/bin/activate"
}

# COMANDO: init - Inicializar proyecto
cmd_init() {
    print_header "🚀 INICIALIZANDO PROYECTO TIMBA PREDICTOR"
    
    if [ -d "$VENV_PATH" ]; then
        print_warning "Virtualenv ya existe. Saltando..."
    else
        print_warning "Creando virtualenv..."
        python3 -m venv "$VENV_PATH"
        print_success "Virtualenv creado"
    fi
    
    activate_venv
    print_warning "Instalando dependencias..."
    pip install --upgrade pip setuptools wheel
    pip install -r "$CONFIG_PATH/requirements.txt"
    print_success "Dependencias instaladas"
    
    print_header "✨ PROYECTO INICIALIZADO CORRECTAMENTE"
}

# COMANDO: app - Ejecutar Streamlit
cmd_app() {
    print_header "🌐 INICIANDO APP WEB (STREAMLIT)"
    activate_venv
    cd "$SRC_PATH"
    streamlit run app.py
}

# COMANDO: cli - Ejecutar CLI
cmd_cli() {
    print_header "💻 INICIANDO INTERFAZ CLI"
    activate_venv
    cd "$SRC_PATH"
    python cli.py
}

# COMANDO: test - Ejecutar tests
cmd_test() {
    print_header "🧪 EJECUTANDO TESTS"
    activate_venv
    
    if [ -z "$1" ]; then
        print_warning "Ejecutando todos los tests..."
        python -m pytest "$PROJECT_DIR/tests/" -v --tb=short
    else
        print_warning "Ejecutando test: $1"
        python "$PROJECT_DIR/tests/$1"
    fi
}

# COMANDO: clean - Limpiar archivos temporales
cmd_clean() {
    print_header "🧹 LIMPIANDO ARCHIVOS TEMPORALES"
    
    print_warning "Eliminando __pycache__..."
    find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    print_warning "Eliminando archivos de caché..."
    rm -rf "$PROJECT_DIR/.pytest_cache" 2>/dev/null || true
    rm -rf "$PROJECT_DIR/.coverage" 2>/dev/null || true
    
    print_warning "Eliminando archivos Excel temporales..."
    find "$PROJECT_DIR" -type f -name "*.xlsx" -delete 2>/dev/null || true
    
    print_success "Archivos temporales eliminados"
}

# COMANDO: deps - Actualizar dependencias
cmd_deps() {
    print_header "📦 ACTUALIZANDO DEPENDENCIAS"
    activate_venv
    print_warning "Instalando dependencias..."
    pip install -r "$CONFIG_PATH/requirements.txt" --upgrade
    print_warning "Generando requirements.txt..."
    pip freeze > "$CONFIG_PATH/requirements.txt"
    print_success "Dependencias actualizadas"
}

# COMANDO: status - Mostrar estado del proyecto
cmd_status() {
    print_header "📊 ESTADO DEL PROYECTO"
    
    echo -e "${YELLOW}Directorio:${NC} $PROJECT_DIR"
    echo -e "${YELLOW}Python:${NC} $(python3 --version 2>&1)"
    
    if [ -d "$VENV_PATH" ]; then
        echo -e "${GREEN}✓ Virtualenv${NC}: $VENV_PATH"
    else
        echo -e "${RED}✗ Virtualenv${NC}: No encontrado"
    fi
    
    echo -e "\n${YELLOW}Estructura de directorios:${NC}"
    ls -lah "$PROJECT_DIR" | grep "^d" | awk '{print "  " $NF}'
    
    echo -e "\n${YELLOW}Archivos principales:${NC}"
    echo "  📄 $(ls -1 $SRC_PATH/*.py 2>/dev/null | wc -l) archivos Python en src/"
    echo "  🧪 $(ls -1 $PROJECT_DIR/tests/*.py 2>/dev/null | wc -l) archivos de test"
    echo "  📚 $(ls -1 $PROJECT_DIR/docs/*.md 2>/dev/null | wc -l) documentos en docs/"
}

# COMANDO: help - Mostrar ayuda
cmd_help() {
    print_header "📖 AYUDA - COMANDOS DISPONIBLES"
    
    cat << EOF
${BLUE}COMANDOS DISPONIBLES:${NC}

  ${GREEN}init${NC}              Inicializar proyecto (crear virtualenv e instalar deps)
  ${GREEN}app${NC}               Ejecutar app web con Streamlit
  ${GREEN}cli${NC}               Ejecutar interfaz CLI
  ${GREEN}test${NC}   [test]     Ejecutar tests (opcional: test específico)
  ${GREEN}clean${NC}              Limpiar archivos temporales
  ${GREEN}deps${NC}               Actualizar dependencias
  ${GREEN}status${NC}             Mostrar estado del proyecto
  ${GREEN}help${NC}               Mostrar esta ayuda

${BLUE}EJEMPLOS:${NC}

  ./utils.sh init                 # Inicializar proyecto
  ./utils.sh app                  # Ejecutar web
  ./utils.sh cli                  # Ejecutar CLI
  ./utils.sh test                 # Ejecutar todos los tests
  ./utils.sh test test_corners.py # Ejecutar test específico
  ./utils.sh clean                # Limpiar temporales

${BLUE}ESTRUCTURA DEL PROYECTO:${NC}

  src/              Código fuente (app.py, cli.py, timba_core.py)
  tests/            Tests unitarios
  docs/             Documentación
  scripts/          Scripts auxiliares
  config/           Configuración (requirements.txt)
  logs/             Registros

EOF
}

# MAIN
main() {
    if [ $# -eq 0 ]; then
        cmd_help
        exit 0
    fi
    
    COMMAND=$1
    shift
    
    case $COMMAND in
        init)    cmd_init ;;
        app)     cmd_app ;;
        cli)     cmd_cli ;;
        test)    cmd_test "$@" ;;
        clean)   cmd_clean ;;
        deps)    cmd_deps ;;
        status)  cmd_status ;;
        help)    cmd_help ;;
        *)       
            print_error "Comando desconocido: $COMMAND"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
