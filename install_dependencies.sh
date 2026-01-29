#!/usr/bin/env bash

# Script de instalación de dependencias para TIMBA PREDICTOR

echo "🚀 Instalando dependencias de TIMBA PREDICTOR..."

# Activar virtual environment
source .venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment no encontrado"

# Instalar paquetes requeridos
pip install --upgrade pip
pip install pandas requests scipy numpy streamlit

echo "✅ Dependencias instaladas correctamente"
echo ""
echo "Para ejecutar la aplicación Streamlit:"
echo "  streamlit run app.py"
echo ""
echo "Abre tu navegador en: http://localhost:8502"
