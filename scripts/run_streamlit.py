#!/usr/bin/env python3
import os
import sys
import subprocess

# Configurar variables de entorno para Streamlit
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHERUSAGESTATS'] = 'false'

# Ejecutar streamlit
subprocess.run([
    sys.executable, '-m', 'streamlit', 'run',
    'app.py',
    '--server.port=8501',
    '--server.address=0.0.0.0'
], cwd='/home/nahuel/Documentos/projecto timba')
