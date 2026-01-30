#!/bin/bash
# Setup Script para Timba Predictor
# Carga variables de ambiente y valida configuración
#
# Uso: source setup_env.sh
# o:   bash setup_env.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "════════════════════════════════════════════════════════════════"
echo "🔧 SETUP - Timba Predictor"
echo "════════════════════════════════════════════════════════════════"

# Cargar .env si existe
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
    echo "✓ Variables de ambiente cargadas desde .env"
else
    echo "⚠️  Archivo .env no encontrado"
fi

# Verificar API_FOOTBALL_KEY
if [ -z "$API_FOOTBALL_KEY" ]; then
    echo "✗ API_FOOTBALL_KEY no configurada"
    exit 1
else
    API_KEY_DISPLAY="${API_FOOTBALL_KEY:0:8}...${API_FOOTBALL_KEY: -8}"
    echo "✓ API_FOOTBALL_KEY: $API_KEY_DISPLAY"
fi

# Crear directorios necesarios
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data/databases"

echo "✓ Directorios creados/verificados"

# Agregar src a PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
echo "✓ PYTHONPATH actualizado"

echo "════════════════════════════════════════════════════════════════"
echo "✅ Setup completado"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Próximos pasos:"
echo "  1. python3 setup_api.py      (Validar configuración)"
echo "  2. streamlit run src/app.py   (Ejecutar app)"
echo "  3. python3 src/cli.py         (Ejecutar CLI)"
echo ""
