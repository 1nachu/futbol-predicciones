"""
ÍNDICE DE ARCHIVOS ETL
======================

Este archivo documenta todos los archivos creados para el ETL.
"""

# ESTRUCTURA COMPLETA DEL ETL
# ============================

ARCHIVOS_CREADOS = {
    
    # ====== CORE ETL ======
    "src/etl_football_data.py": {
        "descripción": "Pipeline ETL principal (3 clases principales)",
        "líneas": "~1200",
        "clases": [
            "FootballDataExtractor - Descarga desde Football-Data.co.uk",
            "FootballDataTransformer - Normaliza y enriquece datos",
            "FootballDataLoader - Carga en SQLite/PostgreSQL",
            "FootballETLPipeline - Orquesta todo el pipeline"
        ],
        "métodos_clave": [
            "ejecutar() - Run completo del pipeline",
            "descargar_csv() - Descarga un archivo CSV",
            "transformar() - Pipeline de transformación",
            "cargar_datos() - Inserta en BD"
        ]
    },
    
    # ====== CLI ======
    "src/etl_cli.py": {
        "descripción": "Interfaz CLI para ejecutar ETL",
        "líneas": "~500",
        "comandos": [
            "run - Ejecutar pipeline completo",
            "stats - Ver estadísticas de datos cargados",
            "validate - Validar integridad de BD",
            "export - Exportar datos a múltiples formatos"
        ],
        "usar": "python etl_cli.py run"
    },
    
    # ====== CONFIGURACIÓN ======
    "src/etl_config.py": {
        "descripción": "Configuración centralizada",
        "líneas": "~150",
        "contiene": [
            "DATABASE_CONFIG - Configs SQLite/PostgreSQL",
            "ETL_CONFIG - Parámetros de descarga",
            "LIGAS_CONFIG - Definición de ligas",
            "Validaciones automáticas"
        ]
    },
    
    # ====== ANÁLISIS ======
    "src/etl_data_analysis.py": {
        "descripción": "Análisis y queries sobre datos",
        "líneas": "~600",
        "clases": [
            "FootballDataAnalyzer - Queries y estadísticas",
            "FootballDataExporter - Exporta a varios formatos",
            "FootballDataValidator - Valida calidad de datos"
        ],
        "métodos": [
            "obtener_estadisticas_equipo() - Stats completas",
            "calcular_probabilidades_match() - Poisson",
            "obtener_enfrentamientos_directos() - H2H",
            "obtener_top_equipos() - Ranking por métrica"
        ]
    },
    
    # ====== EJEMPLOS ======
    "examples.py": {
        "descripción": "Ejemplos de uso de todos los módulos",
        "líneas": "~600",
        "ejemplos": [
            "1. Descargar datos",
            "2. Analizar equipo",
            "3. Historial directo (H2H)",
            "4. Predecir partido",
            "5. Top equipos",
            "6. Tendencias de mercado",
            "7. Exportar para ML",
            "8. Validar datos"
        ],
        "usar": "python examples.py descargar_datos"
    },
    
    # ====== DOCUMENTACIÓN ======
    "docs/ETL_FOOTBALL_DATA_GUIDE.md": {
        "descripción": "Guía completa (6000+ palabras)",
        "secciones": [
            "Descripción general",
            "Características principales",
            "Instalación",
            "Uso (CLI, Python, módulos)",
            "Configuración BD",
            "Esquema de BD",
            "Estructura de datos",
            "Casos de uso",
            "Troubleshooting",
            "Ejemplos completos"
        ]
    },
    
    "ETL_QUICKSTART.md": {
        "descripción": "Guía rápida (empezar en 5 minutos)",
        "contiene": [
            "TL;DR",
            "Comandos principales",
            "Ejemplos Python",
            "Troubleshooting básico",
            "Checklist"
        ]
    },
    
    # ====== MODIFICACIONES ======
    "requirements.txt": {
        "descripción": "Actualizado con todas las dependencias",
        "agregadas": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "python-dotenv>=1.0.0",
            "pyarrow>=12.0.0"
        ]
    }
}


# ARQUITECTURA DEL PIPELINE
# ==========================

"""
┌─────────────────────────────────────────────────────────────┐
│                    FOOTBALL DATA ETL                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENTRADA: Football-Data.co.uk (CSV)                        │
│           ↓                                                 │
│  ┌──────────────────────────────────────┐                 │
│  │  FASE 1: EXTRACCIÓN                  │                 │
│  │  FootballDataExtractor               │                 │
│  │  • 3 ligas × 10 temporadas           │                 │
│  │  • Reintentos automáticos            │                 │
│  │  • Rate limiting                     │                 │
│  │  • ~30 archivos CSV                  │                 │
│  └──────────────────────────────────────┘                 │
│           ↓                                                 │
│  ┌──────────────────────────────────────┐                 │
│  │  FASE 2: TRANSFORMACIÓN              │                 │
│  │  FootballDataTransformer             │                 │
│  │  • Normalización de fechas (ISO)     │                 │
│  │  • Selección de columnas críticas    │                 │
│  │  • Validación y limpieza             │                 │
│  │  • Enriquecimiento (derived cols)    │                 │
│  │  • ~10,500 registros                 │                 │
│  └──────────────────────────────────────┘                 │
│           ↓                                                 │
│  ┌──────────────────────────────────────┐                 │
│  │  FASE 3: CARGA                       │                 │
│  │  FootballDataLoader                  │                 │
│  │  • SQLite (desarrollo)               │                 │
│  │  • PostgreSQL (producción)           │                 │
│  │  • Inserción masiva en chunks        │                 │
│  │  • Índices automáticos               │                 │
│  └──────────────────────────────────────┘                 │
│           ↓                                                 │
│  SALIDA: Base de Datos Limpia y Normalizada               │
│          • Listo para predicción                          │
│          • Listo para análisis                            │
│          • Listo para entrenamiento ML                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
"""


# FLUJO DE DATOS
# ==============

"""
ANTES (Sin ETL):
├── Datos crudos de API
├── Formatos inconsistentes
├── Fechas en múltiples formatos
├── Columnas faltantes
└── ❌ No apto para predicción

DESPUÉS (Con ETL):
├── Datos descargados automáticamente
├── Formato normalizado (ISO 8601)
├── Columnas críticas preservadas
├── Valores enriquecidos
├── Validación automática
└── ✅ Listo para predicción + ML
"""


# CASOS DE USO
# ============

CASOS_USO = {
    
    "1. PREDICCIÓN": {
        "descripción": "Usar datos históricos para predicción",
        "pasos": [
            "1. python etl_cli.py run",
            "2. from src.etl_data_analysis import FootballDataAnalyzer",
            "3. analyzer.calcular_probabilidades_match('team1', 'team2')",
            "4. Ver probabilidades en Streamlit"
        ]
    },
    
    "2. MACHINE LEARNING": {
        "descripción": "Crear dataset para entrenar modelos",
        "pasos": [
            "1. python etl_cli.py run",
            "2. python etl_cli.py export --output training_data.parquet",
            "3. Importar en scikit-learn/XGBoost/TensorFlow",
            "4. Entrenar modelo predictivo"
        ]
    },
    
    "3. ANÁLISIS EXPLORATORIO": {
        "descripción": "Analizar equipos y tendencias",
        "pasos": [
            "1. python etl_cli.py run",
            "2. python examples.py analizar_equipo 'Liverpool'",
            "3. python examples.py top_equipos",
            "4. python examples.py h2h 'team1' 'team2'"
        ]
    },
    
    "4. DASHBOARD": {
        "descripción": "Visualizar datos en Streamlit",
        "pasos": [
            "1. python etl_cli.py run",
            "2. Importar FootballDataAnalyzer en app.py",
            "3. Mostrar gráficos y estadísticas",
            "4. streamlit run src/app.py"
        ]
    },
    
    "5. SISTEMA EN PRODUCCIÓN": {
        "descripción": "Desplegar con datos actualizados",
        "pasos": [
            "1. Usar PostgreSQL (no SQLite)",
            "2. Ejecutar ETL en schedule (cron)",
            "3. Validar datos automáticamente",
            "4. Entrenar modelos con nuevos datos"
        ]
    }
}


# LIGAS SOPORTADAS
# ================

LIGAS = {
    "E0": {
        "nombre": "Premier League",
        "país": "Inglaterra",
        "partidos/temporada": 380,
        "temporadas": 10
    },
    "SP1": {
        "nombre": "La Liga",
        "país": "España",
        "partidos/temporada": 380,
        "temporadas": 10
    },
    "D1": {
        "nombre": "Bundesliga",
        "país": "Alemania",
        "partidos/temporada": 306,
        "temporadas": 10
    }
}

# Total: ~10,500 partidos históricos


# COLUMNAS DE BD
# ==============

COLUMNAS = {
    "temporales": ["date", "temporada"],
    "equipos": ["home_team", "away_team"],
    "resultado": ["fthg", "ftag", "ftr", "total_goles"],
    "tiros": ["hs", "as_shots", "hst", "ast", "diff_tiros"],
    "disciplina": ["hf", "af", "hr", "ar", "hy", "ay"],
    "cuotas": ["b365h", "b365d", "b365a"],
    "derivadas": ["over_25", "efectividad_local"],
    "metadata": ["created_at"]
}


# PERMISOS Y REQUIERE
# ===================

REQUISITOS = {
    "extracción": {
        "internet": "✓ Necesaria (descarga de datos)",
        "api_key": "✗ No necesaria (datos públicos)",
        "limite": "Respetuoso con rate limits (1s entre descargas)"
    },
    
    "transformación": {
        "ram": "~2GB para 10,500 registros",
        "cpu": "Bajo (operaciones simples)",
        "tiempo": "~5-10 minutos (incluye descargas)"
    },
    
    "carga": {
        "sqlite": "✓ Automático (no instalación)",
        "postgresql": "Requiere instalación + credenciales"
    }
}


# VENTAJAS vs DESVENTAJAS
# =======================

VENTAJAS = [
    "✅ Descarga automatizada (sin APIKey)",
    "✅ Datos limpios y validados",
    "✅ 10 años de histórico",
    "✅ Múltiples ligas",
    "✅ Columnas críticas para predicción",
    "✅ Flexible (SQLite/PostgreSQL)",
    "✅ Análisis integrado",
    "✅ Exportación múltiple",
    "✅ Logging completo",
    "✅ Ejemplos de uso"
]

LIMITACIONES = [
    "⚠️ Descarga inicial: 5-10 minutos",
    "⚠️ Datos históricos (no en vivo)",
    "⚠️ 10 temporadas máximo (Football-Data)",
    "⚠️ Requiere almacenamiento (~200MB SQLite)"
]


# ROADMAP FUTURO
# ==============

ROADMAP = [
    "[ ] Descarga incremental (solo nuevos partidos)",
    "[ ] Caché de descargas",
    "[ ] Integración con API en vivo",
    "[ ] Más ligas (Serie A, Ligue 1, etc)",
    "[ ] Predicciones en tiempo real",
    "[ ] Dashboard web (Flask/FastAPI)",
    "[ ] Alertas de cambios en cuotas",
    "[ ] Exportación a Cloud (BigQuery, Redshift)"
]


# CONTACTO Y SOPORTE
# ==================

SOPORTE = {
    "documentación": "docs/ETL_FOOTBALL_DATA_GUIDE.md",
    "quick_start": "ETL_QUICKSTART.md",
    "ejemplos": "examples.py",
    "logs": "logs/etl_football_data.log",
    "issues": "GitHub Issues (proyectotimba)"
}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("📋 ÍNDICE ETL FOOTBALL DATA")
    print("="*70)
    
    print("\n📁 ARCHIVOS PRINCIPALES:")
    for archivo, info in ARCHIVOS_CREADOS.items():
        print(f"\n  {archivo}")
        print(f"    📝 {info.get('descripción', 'N/A')}")
        print(f"    📊 {info.get('líneas', 'N/A')} líneas")
    
    print("\n\n📋 CASOS DE USO:")
    for caso, detalles in CASOS_USO.items():
        print(f"\n  {caso}")
        print(f"    {detalles['descripción']}")
    
    print("\n\n✅ VENTAJAS:")
    for v in VENTAJAS:
        print(f"  {v}")
    
    print("\n\n⚠️ LIMITACIONES:")
    for l in LIMITACIONES:
        print(f"  {l}")
    
    print("\n" + "="*70)
    print("✨ ETL listo para usar!")
    print("="*70 + "\n")
