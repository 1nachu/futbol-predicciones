"""
Core de análisis y predicción de partidos de fútbol - v2.0
Integración con team_normalization y utilidades compartidas.
Centralización de funcionalidades de API-Football v3.
"""

import pandas as pd
import io
import requests
from scipy.stats import poisson
import numpy as np
from difflib import get_close_matches
from datetime import datetime, timedelta, timezone
import os
import sys
import json
import logging
import time
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== IMPORTAR UTILIDADES COMPARTIDAS ==========
try:
    from utils.shared import (
        normalizar_csv,
        descargar_csv_safe,
        emparejar_equipo,
        encontrar_equipo_similar,
        imprimir_barra,
        ALIAS_TEAMS,
    )
except ImportError:
    # Fallback si no está disponible utils.shared
    print("⚠️  utils.shared no disponible, usando funciones locales")
    ALIAS_TEAMS = {}  # Se definirá más adelante si es necesario

# ========== DICCIONARIO DE LIGAS ==========
LIGAS = {
    1: {
        'nombre': 'Premier League (Inglaterra) - Temporada 25/26',
        'url': 'https://www.football-data.co.uk/mmz4281/2526/E0.csv',
        'codigo': 'E0'
    },
    2: {
        'nombre': 'La Liga (España) - Temporada 25/26',
        'url': 'https://www.football-data.co.uk/mmz4281/2526/SP1.csv',
        'codigo': 'SP1'
    },
    3: {
        'nombre': 'Serie A (Italia) - Temporada 25/26',
        'url': 'https://www.football-data.co.uk/mmz4281/2526/I1.csv',
        'codigo': 'I1'
    },
    4: {
        'nombre': 'Bundesliga (Alemania) - Temporada 25/26',
        'url': 'https://www.football-data.co.uk/mmz4281/2526/D1.csv',
        'codigo': 'D1'
    },
    5: {
        'nombre': 'Ligue 1 (Francia) - Temporada 25/26',
        'url': 'https://www.football-data.co.uk/mmz4281/2526/F1.csv',
        'codigo': 'F1'
    },
    6: {
        'nombre': '🇪🇺 Champions League - Temporada 25/26',
        'url': 'https://raw.githubusercontent.com/footballcsv/europe-champions-league/master/2025-26/cl.csv',
        'alternativas': [
            'https://raw.githubusercontent.com/footballcsv/europe-champions-league/master/2025-26/cl.csv',
            'https://raw.githubusercontent.com/footballcsv/europe-champions-league/gh-pages/2025-26/cl.csv'
        ],
        'codigo': 'CL',
        'formato': 'github'
    },
    7: {
        'nombre': '🇪🇺 Europa League - Temporada 25/26',
        'url': 'https://raw.githubusercontent.com/footballcsv/europe-champions-league/master/2025-26/el.csv',
        'alternativas': [
            'https://raw.githubusercontent.com/footballcsv/europe-europa-league/master/2025-26/el.csv',
            'https://raw.githubusercontent.com/footballcsv/europe-champions-league/master/2025-26/el.csv'
        ],
        'codigo': 'EL',
        'formato': 'github'
    },
    11: {
        'nombre': '🇧🇷 Brasileirão Série A - Temporada 2025',
        'url': 'https://raw.githubusercontent.com/footballcsv/brazil/master/2025/a.csv',
        'alternativas': [
            'https://raw.githubusercontent.com/footballcsv/brazil/master/2025/a.csv',
            'https://raw.githubusercontent.com/footballcsv/brazil/gh-pages/2025/a.csv'
        ],
        'codigo': 'BRA',
        'formato': 'github'
    },
    12: {
        'nombre': '🇦🇷 Liga Profesional Argentina - Temporada 2025',
        'url': 'https://raw.githubusercontent.com/footballcsv/argentina/master/2025/1-primera.csv',
        'alternativas': [
            'https://raw.githubusercontent.com/footballcsv/argentina/master/2025/1-primera.csv',
            'https://raw.githubusercontent.com/footballcsv/argentina/gh-pages/2025/1-primera.csv'
        ],
        'codigo': 'ARG',
        'formato': 'github'
    }
}

# ========== DICCIONARIO DE FIXTURES (CALENDARIOS) ==========
URLS_FIXTURE = {
    1: {'url': 'https://fixturedownload.com/feed/json/epl-2025', 'liga': 'Premier League'},
    2: {'url': 'https://fixturedownload.com/feed/json/la-liga-2025', 'liga': 'La Liga'},
    3: {'url': 'https://fixturedownload.com/feed/json/serie-a-2025', 'liga': 'Serie A'},
    4: {'url': 'https://fixturedownload.com/feed/json/bundesliga-2025', 'liga': 'Bundesliga'},
    5: {'url': 'https://fixturedownload.com/feed/json/ligue-1-2025', 'liga': 'Ligue 1'},
    6: {'url': 'https://fixturedownload.com/feed/json/champions-league-2025', 'liga': 'Champions League'},
    7: {'url': 'https://fixturedownload.com/feed/json/europa-league-2025', 'liga': 'Europa League'},
    11: {'url': 'https://fixturedownload.com/feed/json/cbf-campeonato-brasileiro-2025', 'liga': 'Brasileirão'},
    12: {'url': 'https://fixturedownload.com/feed/json/argentina-primera-division-2025', 'liga': 'Liga Argentina'}
}


def normalizar_csv(df):
    """Normaliza nombres de columnas de CSV heterogéneos. (Delegado a utils.shared)"""
    from utils.shared import normalizar_csv as norm
    return norm(df)


def descargar_csv_safe(url_or_list, timeout=10):
    """Descarga CSV de forma segura. (Delegado a utils.shared)"""
    from utils.shared import descargar_csv_safe as download
    return download(url_or_list, timeout)


def emparejar_equipo(nombre_fixture, equipos_validos):
    """Empareja nombre de equipo. (Delegado a utils.shared)"""
    from utils.shared import emparejar_equipo as match
    return match(nombre_fixture, equipos_validos)


def encontrar_equipo_similar(nombre, equipos_validos):
    """Busca equipos similares. (Delegado a utils.shared)"""
    from utils.shared import encontrar_equipo_similar as similar
    return similar(nombre, equipos_validos)


def imprimir_barra(valor, maximo=100, ancho=25):
    """Crea barra visual. (Delegado a utils.shared)"""
    from utils.shared import imprimir_barra as barra
    return barra(valor, maximo, ancho)


# ========== DICCIONARIO DE ALIAS DE EQUIPOS ==========
# Mantenido aquí para compatibilidad hacia atrás
# La fuente única está en utils.shared.ALIAS_TEAMS


def calcular_fuerzas(df):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.sort_values('Date').reset_index(drop=True)
    promedio_goles_local_liga = df['FTHG'].mean()
    promedio_goles_visitante_liga = df['FTAG'].mean()
    fuerzas = {}
    equipos = sorted(df['HomeTeam'].unique())
    for equipo in equipos:
        partidos_casa_global = df[df['HomeTeam'] == equipo]
        partidos_fuera_global = df[df['AwayTeam'] == equipo]
        goles_a_favor_casa_global = partidos_casa_global['FTHG'].mean() if len(partidos_casa_global) > 0 else 0
        goles_en_contra_casa_global = partidos_casa_global['FTAG'].mean() if len(partidos_casa_global) > 0 else 0
        goles_a_favor_fuera_global = partidos_fuera_global['FTAG'].mean() if len(partidos_fuera_global) > 0 else 0
        goles_en_contra_fuera_global = partidos_fuera_global['FTHG'].mean() if len(partidos_fuera_global) > 0 else 0
        ataque_casa_global = goles_a_favor_casa_global / promedio_goles_local_liga if promedio_goles_local_liga > 0 else 0
        defensa_casa_global = goles_en_contra_casa_global / promedio_goles_visitante_liga if promedio_goles_visitante_liga > 0 else 0
        ataque_fuera_global = goles_a_favor_fuera_global / promedio_goles_visitante_liga if promedio_goles_visitante_liga > 0 else 0
        defensa_fuera_global = goles_en_contra_fuera_global / promedio_goles_local_liga if promedio_goles_local_liga > 0 else 0
        todos_partidos = []
        for _, row in partidos_casa_global.iterrows():
            todos_partidos.append({'Fecha': row['Date'], 'Tipo': 'Casa', 'GF': row['FTHG'], 'GC': row['FTAG']})
        for _, row in partidos_fuera_global.iterrows():
            todos_partidos.append({'Fecha': row['Date'], 'Tipo': 'Fuera', 'GF': row['FTAG'], 'GC': row['FTHG']})
        todos_partidos_sorted = sorted(todos_partidos, key=lambda x: x['Fecha'])
        ultimos_5 = todos_partidos_sorted[-5:] if len(todos_partidos_sorted) >= 5 else todos_partidos_sorted
        if len(ultimos_5) > 0:
            goles_favor_reciente = sum(p['GF'] for p in ultimos_5) / len(ultimos_5)
            goles_contra_reciente = sum(p['GC'] for p in ultimos_5) / len(ultimos_5)
        else:
            goles_favor_reciente = goles_contra_reciente = 0
        ataque_reciente = goles_favor_reciente / promedio_goles_local_liga if promedio_goles_local_liga > 0 else 0
        defensa_reciente = goles_contra_reciente / promedio_goles_visitante_liga if promedio_goles_visitante_liga > 0 else 0
        ataque_casa_final = (ataque_reciente * 0.6) + (ataque_casa_global * 0.4)
        defensa_casa_final = (defensa_reciente * 0.6) + (defensa_casa_global * 0.4)
        ataque_fuera_final = (ataque_reciente * 0.6) + (ataque_fuera_global * 0.4)
        defensa_fuera_final = (defensa_reciente * 0.6) + (defensa_fuera_global * 0.4)
        # Cálculo de CÓRNERS (ponderado 75% reciente + 25% histórico)
        # DEFENSIVA: Verificar disponibilidad de columnas HC y AC
        tiene_datos_corners = 'HC' in df.columns and 'AC' in df.columns
        
        if tiene_datos_corners:
            corners_casa_global = partidos_casa_global['HC'].mean() if len(partidos_casa_global) > 0 else 0
            corners_fuera_global = partidos_fuera_global['AC'].mean() if len(partidos_fuera_global) > 0 else 0
            corners_casa_contra = partidos_casa_global['AC'].mean() if len(partidos_casa_global) > 0 else 0
            corners_fuera_contra = partidos_fuera_global['HC'].mean() if len(partidos_fuera_global) > 0 else 0
        else:
            corners_casa_global = corners_fuera_global = corners_casa_contra = corners_fuera_contra = 0
        
        # Cálculo reciente de córners (si hay datos disponibles)
        if len(ultimos_5) > 0 and tiene_datos_corners:
            corners_casa_reciente = corners_casa_global  # Use historical as proxy for recent
            corners_fuera_reciente = corners_fuera_global
        else:
            corners_casa_reciente = corners_casa_global
            corners_fuera_reciente = corners_fuera_global
        
        # Ponderar: 75% reciente + 25% histórico
        corners_casa_ponderado = (corners_casa_reciente * 0.75) + (corners_casa_global * 0.25)
        corners_fuera_ponderado = (corners_fuera_reciente * 0.75) + (corners_fuera_global * 0.25)
        
        corners_casa = corners_casa_ponderado
        corners_fuera = corners_fuera_ponderado
        tarjetas_am_casa = partidos_casa_global['HY'].mean() if 'HY' in df.columns and len(partidos_casa_global) > 0 else 0
        tarjetas_am_fuera = partidos_fuera_global['AY'].mean() if 'AY' in df.columns and len(partidos_fuera_global) > 0 else 0
        tarjetas_ro_casa = partidos_casa_global['HR'].mean() if 'HR' in df.columns and len(partidos_casa_global) > 0 else 0
        tarjetas_ro_fuera = partidos_fuera_global['AR'].mean() if 'AR' in df.columns and len(partidos_fuera_global) > 0 else 0
        fuerzas[equipo] = {
            'Ataque_Casa': ataque_casa_final,
            'Defensa_Casa': defensa_casa_final,
            'Ataque_Fuera': ataque_fuera_final,
            'Defensa_Fuera': defensa_fuera_final,
            'Ataque_Casa_Global': ataque_casa_global,
            'Defensa_Casa_Global': defensa_casa_global,
            'Ataque_Fuera_Global': ataque_fuera_global,
            'Defensa_Fuera_Global': defensa_fuera_global,
            'Ataque_Reciente': ataque_reciente,
            'Defensa_Reciente': defensa_reciente,
            'Goles_Favor_Reciente': goles_favor_reciente,
            'Goles_Contra_Reciente': goles_contra_reciente,
            'Corners_Casa': corners_casa,
            'Corners_Fuera': corners_fuera,
            'Corners_Casa_Contra': corners_casa_contra,
            'Corners_Fuera_Contra': corners_fuera_contra,
            'Corners_Promedio': (corners_casa + corners_fuera) / 2,
            'Tarjetas_Am_Casa': tarjetas_am_casa,
            'Tarjetas_Am_Fuera': tarjetas_am_fuera,
            'Tarjetas_Am_Promedio': (tarjetas_am_casa + tarjetas_am_fuera) / 2,
            'Tarjetas_Ro_Casa': tarjetas_ro_casa,
            'Tarjetas_Ro_Fuera': tarjetas_ro_fuera,
            'Tarjetas_Ro_Promedio': (tarjetas_ro_casa + tarjetas_ro_fuera) / 2,
        }
        # métricas adicionales
        try:
            hst_media_casa = partidos_casa_global['HST'].mean() if 'HST' in df.columns and len(partidos_casa_global) > 0 else 0
            ast_media_fuera = partidos_fuera_global['AST'].mean() if 'AST' in df.columns and len(partidos_fuera_global) > 0 else 0
            eficiencia_casa = (goles_a_favor_casa_global / hst_media_casa) * 100 if hst_media_casa > 0 else 0
            eficiencia_fuera = (goles_a_favor_fuera_global / ast_media_fuera) * 100 if ast_media_fuera > 0 else 0
            eficiencia_promedio = (eficiencia_casa + eficiencia_fuera) / 2
        except Exception:
            eficiencia_casa = eficiencia_fuera = eficiencia_promedio = 0
        try:
            partidos_equipo = pd.concat([partidos_casa_global, partidos_fuera_global], ignore_index=True)
            total_partidos_equipo = len(partidos_equipo)
            if total_partidos_equipo > 0:
                btts_count = ((partidos_equipo['FTHG'] > 0) & (partidos_equipo['FTAG'] > 0)).sum()
                over25_count = ((partidos_equipo['FTHG'] + partidos_equipo['FTAG']) > 2.5).sum()
                btts_pct = (btts_count / total_partidos_equipo) * 100
                over25_pct = (over25_count / total_partidos_equipo) * 100
            else:
                btts_pct = 0
                over25_pct = 0
        except Exception:
            btts_pct = 0
            over25_pct = 0
        try:
            goles_2t_list = []
            if len(partidos_casa_global) > 0 and 'HTHG' in df.columns:
                goles_2t_casa = (partidos_casa_global['FTHG'] - partidos_casa_global['HTHG']).dropna()
                goles_2t_list.extend(goles_2t_casa.tolist())
            if len(partidos_fuera_global) > 0 and 'HTAG' in df.columns:
                goles_2t_fuera = (partidos_fuera_global['FTAG'] - partidos_fuera_global['HTAG']).dropna()
                goles_2t_list.extend(goles_2t_fuera.tolist())
            goles_2t_promedio = float(np.mean(goles_2t_list)) if len(goles_2t_list) > 0 else 0.0
        except Exception:
            goles_2t_promedio = 0.0
        fuerzas[equipo].update({
            'Eficiencia_Tiro_Casa_pct': eficiencia_casa,
            'Eficiencia_Tiro_Fuera_pct': eficiencia_fuera,
            'Eficiencia_Tiro_Promedio_pct': eficiencia_promedio,
            'BTTS_pct': btts_pct,
            'Over25_pct': over25_pct,
            'Goles_2T_Promedio': goles_2t_promedio,
        })
    return fuerzas, promedio_goles_local_liga, promedio_goles_visitante_liga


def predecir_partido(local, visitante, fuerzas, media_liga_local, media_liga_visitante):
    if local not in fuerzas or visitante not in fuerzas:
        return None
    fuerza_ataque_local = fuerzas[local]['Ataque_Casa']
    fuerza_defensa_visitante = fuerzas[visitante]['Defensa_Fuera']
    lambda_local = fuerza_ataque_local * fuerza_defensa_visitante * media_liga_local
    fuerza_ataque_visitante = fuerzas[visitante]['Ataque_Fuera']
    fuerza_defensa_local = fuerzas[local]['Defensa_Casa']
    lambda_visitante = fuerza_ataque_visitante * fuerza_defensa_local * media_liga_visitante
    prob_local = [poisson.pmf(i, lambda_local) for i in range(6)]
    prob_visitante = [poisson.pmf(i, lambda_visitante) for i in range(6)]
    victoria_local = empate = victoria_visitante = 0
    marcadores_exactos = []
    for goles_l in range(6):
        for goles_v in range(6):
            prob = prob_local[goles_l] * prob_visitante[goles_v]
            if goles_l > goles_v:
                victoria_local += prob
            elif goles_l == goles_v:
                empate += prob
            else:
                victoria_visitante += prob
            marcadores_exactos.append({'marcador': f'{goles_l}-{goles_v}', 'prob': prob})
    marcadores_exactos.sort(key=lambda x: x['prob'], reverse=True)
    top_3_marcadores = marcadores_exactos[:3]
    
    # ========== MERCADOS DE GOLES (Over/Under) ==========
    # λ_total = λ_local + λ_visitante (suma de Poisson es Poisson)
    lambda_total = lambda_local + lambda_visitante
    
    # Over/Under usando Poisson CDF (probabilidad acumulada)
    # P(X > n) = 1 - P(X <= n)
    over_15 = 1 - poisson.cdf(1, lambda_total)  # P(goles > 1.5) = P(goles >= 2)
    over_25 = 1 - poisson.cdf(2, lambda_total)  # P(goles > 2.5) = P(goles >= 3)
    under_35 = poisson.cdf(3, lambda_total)     # P(goles <= 3.5) = P(goles < 3.5)
    
    # ========== DOBLE OPORTUNIDAD ==========
    prob_1x = victoria_local + empate  # Local o Empate
    prob_x2 = empate + victoria_visitante  # Empate o Visitante
    prob_12 = victoria_local + victoria_visitante  # Sin Empate (1 o 2)
    
    # ========== MERCADOS DE CÓRNERS (Corners Expected) ==========
    # Calculamos lambdas de córners para cada equipo
    # Córners Local: promedio de córners que saca en casa
    # Córners Visitante: promedio de córners que saca fuera
    # Esperamos que córners siga una distribución de Poisson
    
    corners_lambda_local = fuerzas[local]['Corners_Casa']  # Córners que saca local en casa
    corners_lambda_vis = fuerzas[visitante]['Corners_Fuera']  # Córners que saca visitante fuera
    
    # Ajuste por capacidad defensiva (defensa que recibe córners)
    # Si la defensa es fuerte, menos córners pueden llegar a ella
    # Aplicamos factor defensivo simple (no es predicción perfecta, pero ayuda)
    corners_lambda_total = corners_lambda_local + corners_lambda_vis
    
    # Mercados Over/Under usando Poisson CDF
    over_85 = 1 - poisson.cdf(8, corners_lambda_total)    # P(córners > 8.5) = P(córners >= 9)
    over_95 = 1 - poisson.cdf(9, corners_lambda_total)    # P(córners > 9.5) = P(córners >= 10)
    under_105 = poisson.cdf(10, corners_lambda_total)      # P(córners <= 10.5) = P(córners < 10.5)
    
    # ========== GANADOR DE CÓRNERS (1X2 Corners) ==========
    # Comparar lambdas para estimar quién saca más córners
    # Calculamos probabilidad de que local saque más, empate, o visitante saque más
    # Simplificación: si lambda_local > lambda_vis, hay más probabilidad de que local saque más
    
    # Para una aproximación simple, usamos la razón de lambdas
    if corners_lambda_local > 0 and corners_lambda_vis > 0:
        ratio_corners = corners_lambda_local / corners_lambda_vis
        # Si ratio > 1.2, local saca más córners con alta probabilidad
        # Si ratio < 0.83, visitante saca más córners
        # Si 0.83 <= ratio <= 1.2, es más probable un empate técnico
        
        if ratio_corners > 1.2:
            prob_local_mas_corners = 0.65
            prob_empate_corners = 0.25
            prob_vis_mas_corners = 0.10
        elif ratio_corners < 0.83:
            prob_local_mas_corners = 0.10
            prob_empate_corners = 0.25
            prob_vis_mas_corners = 0.65
        else:
            prob_local_mas_corners = 0.35
            prob_empate_corners = 0.40
            prob_vis_mas_corners = 0.25
    else:
        # Si no hay datos de córners, asumimos equilibrio
        prob_local_mas_corners = 0.33
        prob_empate_corners = 0.34
        prob_vis_mas_corners = 0.33
    
    return {
        'Goles_Esp_Local': lambda_local,
        'Goles_Esp_Vis': lambda_visitante,
        'Prob_Local': victoria_local,
        'Prob_Empate': empate,
        'Prob_Vis': victoria_visitante,
        'Goles_Favor_Local': fuerzas[local]['Goles_Favor_Reciente'],
        'Goles_Contra_Local': fuerzas[local]['Goles_Contra_Reciente'],
        'Goles_Favor_Vis': fuerzas[visitante]['Goles_Favor_Reciente'],
        'Goles_Contra_Vis': fuerzas[visitante]['Goles_Contra_Reciente'],
        'Corners_Local': fuerzas[local]['Corners_Promedio'],
        'Corners_Vis': fuerzas[visitante]['Corners_Promedio'],
        'Tarjetas_Am_Local': fuerzas[local]['Tarjetas_Am_Promedio'],
        'Tarjetas_Am_Vis': fuerzas[visitante]['Tarjetas_Am_Promedio'],
        'Tarjetas_Ro_Local': fuerzas[local]['Tarjetas_Ro_Promedio'],
        'Tarjetas_Ro_Vis': fuerzas[visitante]['Tarjetas_Ro_Promedio'],
        'Eficiencia_Tiro_Local_pct': fuerzas[local].get('Eficiencia_Tiro_Promedio_pct', 0),
        'Eficiencia_Tiro_Vis_pct': fuerzas[visitante].get('Eficiencia_Tiro_Promedio_pct', 0),
        'BTTS_Local_pct': fuerzas[local].get('BTTS_pct', 0),
        'BTTS_Vis_pct': fuerzas[visitante].get('BTTS_pct', 0),
        'Over25_Local_pct': fuerzas[local].get('Over25_pct', 0),
        'Over25_Vis_pct': fuerzas[visitante].get('Over25_pct', 0),
        'Goles_2T_Local': fuerzas[local].get('Goles_2T_Promedio', 0),
        'Goles_2T_Vis': fuerzas[visitante].get('Goles_2T_Promedio', 0),
        'Top_3_Marcadores': top_3_marcadores,
        # Mercados de goles
        'Over_15': over_15,
        'Over_25': over_25,
        'Under_35': under_35,
        # Doble oportunidad
        'Prob_1X': prob_1x,
        'Prob_X2': prob_x2,
        'Prob_12': prob_12,
        # Mercados de córners
        'Corners_Lambda_Total': corners_lambda_total,
        'Over_85': over_85,
        'Over_95': over_95,
        'Under_105': under_105,
        'Prob_Local_Mas_Corners': prob_local_mas_corners,
        'Prob_Empate_Corners': prob_empate_corners,
        'Prob_Vis_Mas_Corners': prob_vis_mas_corners,
    }


def obtener_h2h(local, visitante, df):
    if df is None or df.empty:
        return []
    h2h = []
    partidos_1 = df[(df['HomeTeam'] == local) & (df['AwayTeam'] == visitante)]
    for _, fila in partidos_1.iterrows():
        try:
            fecha = fila['Date']
            goles_l = int(fila['FTHG'])
            goles_v = int(fila['FTAG'])
            h2h.append({'Fecha': fecha, 'Local': local, 'Visitante': visitante, 'Goles_Local': goles_l, 'Goles_Visitante': goles_v})
        except:
            pass
    partidos_2 = df[(df['HomeTeam'] == visitante) & (df['AwayTeam'] == local)]
    for _, fila in partidos_2.iterrows():
        try:
            fecha = fila['Date']
            goles_l = int(fila['FTAG'])
            goles_v = int(fila['FTHG'])
            h2h.append({'Fecha': fecha, 'Local': local, 'Visitante': visitante, 'Goles_Local': goles_l, 'Goles_Visitante': goles_v})
        except:
            pass
    try:
        h2h.sort(key=lambda x: pd.to_datetime(x['Fecha']), reverse=True)
    except:
        pass
    return h2h


def obtener_proximos_partidos(fixture_url):
    """
    Obtiene los próximos partidos desde una URL de fixtures.
    Retorna lista de dicts con 'local', 'visitante', 'fecha'.
    """
    partidos = []
    try:
        # Intentar descargar el fixture
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(fixture_url, headers=headers, timeout=15)
        r.raise_for_status()
        
        # Parsear como CSV
        txt = r.content.decode('utf-8', errors='ignore')
        df = pd.read_csv(io.StringIO(txt))
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Buscar columnas de equipos y fecha
        col_local = None
        col_visita = None
        col_fecha = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'home' in col_lower or 'local' in col_lower:
                col_local = col
            elif 'away' in col_lower or 'visitante' in col_lower or 'away_team' in col_lower:
                col_visita = col
            elif 'date' in col_lower or 'fecha' in col_lower:
                col_fecha = col
        
        if not col_local or not col_visita:
            return []
        
        # Filtrar futuros (si hay fecha)
        ahora = datetime.now()
        ahora_plus_7 = ahora + timedelta(days=7)
        
        for _, fila in df.iterrows():
            try:
                local = str(fila[col_local]).strip() if col_local else ''
                visita = str(fila[col_visita]).strip() if col_visita else ''
                
                if not local or not visita or local == 'nan' or visita == 'nan':
                    continue
                
                # Intentar obtener fecha
                fecha = 'Próximo'
                if col_fecha:
                    try:
                        fecha_dt = pd.to_datetime(fila[col_fecha])
                        if fecha_dt > ahora and fecha_dt < ahora_plus_7:
                            fecha = fecha_dt.strftime('%Y-%m-%d')
                            partidos.append({'local': local, 'visitante': visita, 'fecha': fecha})
                    except:
                        partidos.append({'local': local, 'visitante': visita, 'fecha': fecha})
                else:
                    partidos.append({'local': local, 'visitante': visita, 'fecha': fecha})
                    
            except Exception:
                continue
        
        return partidos[:20]  # Limitar a 20 partidos máximo
        
    except Exception as e:
        print(f"⚠️  Error descargando fixtures: {e}")
        return []


# ========== CONFIGURACIÓN DE API-FOOTBALL ==========

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/timba_core_api.log'),
        logging.StreamHandler()
    ]
)

API_BASE_URL = "https://v3.football.data-api.com"
DB_PATH = "data/databases/api_football_cache.db"
DAILY_LIMIT = 100
FIXTURE_REQUEST_COST = 1
PREDICTION_REQUEST_COST = 1
STATUS_REQUEST_COST = 0


# ========== ENUMS PARA API ==========

class MatchStatus(Enum):
    """Estado del partido"""
    SCHEDULED = "Scheduled"
    LIVE = "Live"
    FINISHED = "Finished"
    POSTPONED = "Postponed"
    CANCELLED = "Cancelled"


class PredictionType(Enum):
    """Tipos de predicción disponibles"""
    FULL_TIME = "full_time"
    UNDER_OVER = "under_over"
    DOUBLE_CHANCE = "double_chance"


# ========== DATACLASSES PARA API ==========

@dataclass
class APIQuotaStatus:
    """Estado de cuota diaria"""
    requests_used: int
    requests_available: int
    requests_remaining: int
    reset_date: str
    plan_name: str
    
    @property
    def is_exhausted(self) -> bool:
        """Verifica si la cuota está agotada"""
        return self.requests_available <= 0
    
    @property
    def can_request(self, cost: int = 1) -> bool:
        """Verifica si se puede hacer una solicitud"""
        return self.requests_available >= cost


@dataclass
class MatchPrediction:
    """Predicción de partido"""
    match_id: int
    home_team: str
    away_team: str
    match_date: str
    probability_home_win: float
    probability_draw: float
    probability_away_win: float
    under_2_5_probability: float
    over_2_5_probability: float
    expected_goals_home: float
    expected_goals_away: float
    prediction: str
    confidence: float
    comparison: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MatchFixture:
    """Fixture de partido"""
    match_id: int
    league_id: int
    season: int
    round: int
    date: str
    home_team_id: int
    home_team: str
    away_team_id: int
    away_team: str
    status: str
    venue: str
    referee: Optional[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MLFeatures:
    """Features para modelo ML"""
    match_id: int
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    over_2_5_prob: float
    under_2_5_prob: float
    xg_home: float
    xg_away: float
    xg_diff: float
    prediction_label: str
    prediction_confidence: float
    last_updated: str


# ========== CACHÉ Y PERSISTENCIA ==========

class APIFootballCache:
    """Gestor de caché SQLite para API-Football"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Inicializa caché"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa base de datos"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de fixtures
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixtures (
                match_id INTEGER PRIMARY KEY,
                league_id INTEGER,
                season INTEGER,
                round INTEGER,
                date TEXT,
                home_team_id INTEGER,
                home_team TEXT,
                away_team_id INTEGER,
                away_team TEXT,
                status TEXT,
                venue TEXT,
                referee TEXT,
                cached_at DATETIME,
                UNIQUE(match_id, league_id, season)
            )
        """)
        
        # Tabla de predicciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                match_id INTEGER PRIMARY KEY,
                home_team TEXT,
                away_team TEXT,
                match_date TEXT,
                prob_home_win REAL,
                prob_draw REAL,
                prob_away_win REAL,
                prob_under_2_5 REAL,
                prob_over_2_5 REAL,
                xg_home REAL,
                xg_away REAL,
                prediction TEXT,
                confidence REAL,
                cached_at DATETIME,
                FOREIGN KEY(match_id) REFERENCES fixtures(match_id)
            )
        """)
        
        # Tabla de uso de API
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                cost INTEGER,
                success BOOLEAN,
                response_time REAL,
                timestamp DATETIME,
                quota_remaining INTEGER
            )
        """)
        
        # Tabla de cuota diaria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_quota (
                date DATE PRIMARY KEY,
                requests_used INTEGER,
                reset_time TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_fixture(self, match_id: int) -> Optional[MatchFixture]:
        """Obtiene fixture del caché"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM fixtures WHERE match_id = ?", (match_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MatchFixture(**dict(row))
    
    def save_fixture(self, fixture: MatchFixture):
        """Guarda fixture en caché"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO fixtures
            (match_id, league_id, season, round, date, home_team_id, home_team,
             away_team_id, away_team, status, venue, referee, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fixture.match_id, fixture.league_id, fixture.season, fixture.round,
            fixture.date, fixture.home_team_id, fixture.home_team,
            fixture.away_team_id, fixture.away_team, fixture.status,
            fixture.venue, fixture.referee, datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def get_prediction(self, match_id: int) -> Optional[MatchPrediction]:
        """Obtiene predicción del caché"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM predictions WHERE match_id = ?", (match_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MatchPrediction(**dict(row))
    
    def save_prediction(self, prediction: MatchPrediction):
        """Guarda predicción en caché"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO predictions
            (match_id, home_team, away_team, match_date, prob_home_win,
             prob_draw, prob_away_win, prob_under_2_5, prob_over_2_5,
             xg_home, xg_away, prediction, confidence, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.match_id, prediction.home_team, prediction.away_team,
            prediction.match_date, prediction.probability_home_win,
            prediction.probability_draw, prediction.probability_away_win,
            prediction.under_2_5_probability, prediction.over_2_5_probability,
            prediction.expected_goals_home, prediction.expected_goals_away,
            prediction.prediction, prediction.confidence, datetime.now(timezone.utc)
        ))
        
        conn.commit()
        conn.close()
    
    def log_api_usage(self, endpoint: str, cost: int, success: bool,
                     response_time: float, quota_remaining: int):
        """Registra uso de API"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_usage_log
            (endpoint, cost, success, response_time, timestamp, quota_remaining)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (endpoint, cost, success, response_time, datetime.now(timezone.utc), quota_remaining))
        
        conn.commit()
        conn.close()
    
    def get_today_usage(self) -> int:
        """Obtiene consumo de hoy"""
        today = datetime.now(timezone.utc).date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(cost) as total FROM api_usage_log
            WHERE DATE(timestamp) = ? AND success = 1
        """, (today,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] or 0


# ========== CLIENTE API-FOOTBALL ==========

class APIFootballClient:
    """Cliente para API-Football v3"""
    
    def __init__(self, api_key: str):
        """Inicializa cliente"""
        if not api_key or len(api_key) < 10:
            raise ValueError("API Key inválida para API-Football")
        
        self.api_key = api_key
        self.session = self._create_session()
        self.cache = APIFootballCache()
        self.lock = threading.RLock()
        
        logger.info("Cliente API-Football inicializado")
    
    def _create_session(self) -> requests.Session:
        """Crea sesión con retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def check_quota_status(self) -> APIQuotaStatus:
        """Verifica estado de cuota (gratuito)"""
        logger.info("Verificando estado de cuota...")
        
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{API_BASE_URL}/status",
                headers={"x-apisports-key": self.api_key},
                timeout=10
            )
            
            response_time = time.time() - start_time
            response.raise_for_status()
            
            data = response.json().get("response", {})
            
            status = APIQuotaStatus(
                requests_used=data.get("requests", 0),
                requests_available=data.get("requests_remaining", 0),
                requests_remaining=data.get("requests_remaining", 0),
                reset_date=data.get("results", ""),
                plan_name=data.get("plan", "STARTER")
            )
            
            logger.info(f"Cuota: {status.requests_available} llamadas disponibles")
            
            return status
        
        except Exception as e:
            logger.error(f"Error verificando cuota: {e}")
            raise
    
    def request(self, endpoint: str, params: Dict[str, Any],
                cost: int = 1) -> Dict[str, Any]:
        """Hace request a API con verificación de cuota"""
        with self.lock:
            # Verificar cuota
            quota = self.check_quota_status()
            
            if quota.is_exhausted:
                raise Exception("Cuota diaria agotada (100 llamadas/día)")
            
            if quota.requests_available < cost:
                logger.warning(
                    f"Cuota insuficiente: disponibles {quota.requests_available}, "
                    f"necesarias {cost}"
                )
                raise Exception("Cuota insuficiente para esta solicitud")
            
            # Hacer request
            logger.info(f"Solicitando {endpoint} (costo: {cost})")
            
            try:
                start_time = time.time()
                
                response = self.session.get(
                    f"{API_BASE_URL}{endpoint}",
                    params=params,
                    headers={"x-apisports-key": self.api_key},
                    timeout=30
                )
                
                response_time = time.time() - start_time
                response.raise_for_status()
                
                data = response.json()
                
                # Log de uso
                self.cache.log_api_usage(
                    endpoint=endpoint,
                    cost=cost,
                    success=True,
                    response_time=response_time,
                    quota_remaining=quota.requests_available - cost
                )
                
                logger.info(
                    f"✓ {endpoint} - Tiempo: {response_time:.2f}s "
                    f"- Cuota restante: {quota.requests_available - cost}"
                )
                
                return data
            
            except Exception as e:
                logger.error(f"Error en request: {e}")
                
                self.cache.log_api_usage(
                    endpoint=endpoint,
                    cost=0,
                    success=False,
                    response_time=time.time() - start_time,
                    quota_remaining=quota.requests_available
                )
                
                raise


# ========== ESTRATEGIA DE BATCHING ==========

class BatchFetcher:
    """Fetch batch de fixtures una vez al día"""
    
    def __init__(self, client: APIFootballClient):
        """Inicializa fetcher"""
        self.client = client
        self.cache = client.cache
        self.last_fetch = None
    
    def should_fetch_today(self) -> bool:
        """Verifica si ya se ejecutó hoy"""
        if self.last_fetch is None:
            return True
        
        today_utc = datetime.now(timezone.utc).date()
        fetch_date = self.last_fetch.date()
        
        return today_utc > fetch_date
    
    def fetch_daily_fixtures(self, league_id: int = 39, season: int = 2026) -> List[MatchFixture]:
        """Fetch batch una sola vez al día (00:00 UTC)"""
        logger.info("="*70)
        logger.info("BATCH FETCH: Obteniendo fixtures del día")
        logger.info("="*70)
        
        if not self.should_fetch_today():
            logger.info("✓ Ya se ejecutó batch hoy, usando caché")
            return []
        
        try:
            data = self.client.request(
                endpoint="/fixtures",
                params={
                    "league": league_id,
                    "season": season,
                    "timezone": "UTC"
                },
                cost=FIXTURE_REQUEST_COST
            )
            
            fixtures = []
            
            for match_data in data.get("response", []):
                fixture = self._parse_fixture(match_data)
                self.cache.save_fixture(fixture)
                fixtures.append(fixture)
            
            self.last_fetch = datetime.now(timezone.utc)
            
            logger.info(f"✓ Batch completado: {len(fixtures)} fixtures obtenidos")
            
            return fixtures
        
        except Exception as e:
            logger.error(f"Error en batch fetch: {e}")
            return []
    
    def _parse_fixture(self, data: Dict[str, Any]) -> MatchFixture:
        """Parsea dato de fixture desde API"""
        fixture = data.get("fixture", {})
        league = data.get("league", {})
        teams = data.get("teams", {})
        
        return MatchFixture(
            match_id=fixture.get("id"),
            league_id=league.get("id"),
            season=league.get("season"),
            round=int(league.get("round", "1").split()[-1]),
            date=fixture.get("date"),
            home_team_id=teams.get("home", {}).get("id"),
            home_team=teams.get("home", {}).get("name"),
            away_team_id=teams.get("away", {}).get("id"),
            away_team=teams.get("away", {}).get("name"),
            status=fixture.get("status"),
            venue=fixture.get("venue", {}).get("name", ""),
            referee=data.get("league", {}).get("referee")
        )


# ========== ESTRATEGIA DE PREDICCIONES ==========

class PredictionFetcher:
    """Fetch predicciones 30 minutos antes del inicio"""
    
    def __init__(self, client: APIFootballClient):
        """Inicializa fetcher"""
        self.client = client
        self.cache = client.cache
        self.scheduled_matches = {}
    
    def schedule_prediction_fetch(self, match_id: int, match_date: str,
                                  home_team: str, away_team: str):
        """Agenda fetch de predicción para 30 min antes"""
        match_dt = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        fetch_time = match_dt - timedelta(minutes=30)
        
        self.scheduled_matches[match_id] = {
            'fetch_time': fetch_time,
            'match_date': match_date,
            'home_team': home_team,
            'away_team': away_team
        }
        
        logger.info(f"Predicción agendada para {home_team} vs {away_team}")
        logger.info(f"  Hora partido: {match_dt.isoformat()}")
        logger.info(f"  Hora fetch: {fetch_time.isoformat()}")
    
    def get_pending_predictions(self) -> List[int]:
        """Obtiene IDs de partidos listos para fetch"""
        now_utc = datetime.now(timezone.utc)
        pending = []
        
        for match_id, data in self.scheduled_matches.items():
            fetch_time = data['fetch_time']
            
            if now_utc >= fetch_time and now_utc < fetch_time + timedelta(minutes=1):
                pending.append(match_id)
        
        return pending
    
    def fetch_prediction(self, match_id: int) -> Optional[MatchPrediction]:
        """Fetch predicción para un partido específico"""
        cached = self.cache.get_prediction(match_id)
        if cached:
            logger.info(f"✓ Predicción en caché para match {match_id}")
            return cached
        
        try:
            logger.info(f"Fetch predicción para match {match_id}...")
            
            data = self.client.request(
                endpoint="/predictions",
                params={"fixture": match_id},
                cost=PREDICTION_REQUEST_COST
            )
            
            predictions = data.get("response", [])
            
            if not predictions:
                logger.warning(f"No predictions available for match {match_id}")
                return None
            
            prediction = self._parse_prediction(match_id, predictions[0])
            self.cache.save_prediction(prediction)
            
            logger.info(f"✓ Predicción obtenida para {prediction.home_team} vs {prediction.away_team}")
            
            return prediction
        
        except Exception as e:
            logger.error(f"Error fetching prediction: {e}")
            return None
    
    def _parse_prediction(self, match_id: int, data: Dict[str, Any]) -> MatchPrediction:
        """Parsea predicción desde API"""
        predictions = data.get("predictions", {})
        teams = data.get("teams", {})
        fixture = data.get("fixture", {})
        
        prob_home = predictions.get("win", {}).get("home", 0)
        prob_draw = predictions.get("draw", 0)
        prob_away = predictions.get("win", {}).get("away", 0)
        
        total = prob_home + prob_draw + prob_away
        if total > 0:
            prob_home /= total
            prob_draw /= total
            prob_away /= total
        
        probs = {'HOME_WIN': prob_home, 'DRAW': prob_draw, 'AWAY_WIN': prob_away}
        prediction_label = max(probs, key=probs.get)
        confidence = probs[prediction_label]
        
        return MatchPrediction(
            match_id=match_id,
            home_team=teams.get("home", {}).get("name", ""),
            away_team=teams.get("away", {}).get("name", ""),
            match_date=fixture.get("date", ""),
            probability_home_win=prob_home,
            probability_draw=prob_draw,
            probability_away_win=prob_away,
            under_2_5_probability=predictions.get("under_over", {}).get("under", 0),
            over_2_5_probability=predictions.get("under_over", {}).get("over", 0),
            expected_goals_home=predictions.get("goals", {}).get("home", 0),
            expected_goals_away=predictions.get("goals", {}).get("away", 0),
            prediction=prediction_label,
            confidence=confidence,
            comparison=data.get("comparison", "")
        )


# ========== EXTRACCIÓN DE FEATURES ==========

class MLFeatureExtractor:
    """Extrae features para modelo ML"""
    
    @staticmethod
    def extract_features(match_id: int, prediction: MatchPrediction) -> MLFeatures:
        """Extrae features matemáticas para modelo ML"""
        xg_diff = prediction.expected_goals_home - prediction.expected_goals_away
        
        if prediction.probability_home_win > max(prediction.probability_draw, prediction.probability_away_win):
            label = "HOME_WIN"
        elif prediction.probability_away_win > max(prediction.probability_draw, prediction.probability_home_win):
            label = "AWAY_WIN"
        else:
            label = "DRAW"
        
        return MLFeatures(
            match_id=match_id,
            home_win_prob=prediction.probability_home_win,
            draw_prob=prediction.probability_draw,
            away_win_prob=prediction.probability_away_win,
            over_2_5_prob=prediction.over_2_5_probability,
            under_2_5_prob=prediction.under_2_5_probability,
            xg_home=prediction.expected_goals_home,
            xg_away=prediction.expected_goals_away,
            xg_diff=xg_diff,
            prediction_label=label,
            prediction_confidence=prediction.confidence,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def features_to_dict(features: MLFeatures) -> Dict[str, Any]:
        """Convierte features a diccionario"""
        return asdict(features)


# ========== CLASE PRINCIPAL DE TIMBA CORE CON API ==========

class TimbaCoreAPI:
    """Clase principal que centraliza el cálculo con datos de API-Football"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa Timba Core con soporte de API"""
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        self.client = None
        self.batch_fetcher = None
        self.prediction_fetcher = None
        self.feature_extractor = MLFeatureExtractor()
        
        if self.api_key:
            try:
                self.client = APIFootballClient(self.api_key)
                self.batch_fetcher = BatchFetcher(self.client)
                self.prediction_fetcher = PredictionFetcher(self.client)
                logger.info("✓ Timba Core API inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando API: {e}")
        else:
            logger.warning("⚠️  API_FOOTBALL_KEY no configurada, API-Football deshabilitado")
    
    # ========== FUNCIONALIDADES DE API ==========
    
    def fetch_daily_fixtures(self, league_id: int = 39, season: int = 2026) -> List[MatchFixture]:
        """Obtiene fixtures diarios desde API"""
        if not self.batch_fetcher:
            raise Exception("API-Football no está configurada")
        
        return self.batch_fetcher.fetch_daily_fixtures(league_id, season)
    
    def fetch_prediction(self, match_id: int) -> Optional[MatchPrediction]:
        """Obtiene predicción de un partido"""
        if not self.prediction_fetcher:
            raise Exception("API-Football no está configurada")
        
        return self.prediction_fetcher.fetch_prediction(match_id)
    
    def schedule_predictions(self, fixtures: List[MatchFixture]):
        """Agenda predicciones para una lista de fixtures"""
        if not self.prediction_fetcher:
            raise Exception("API-Football no está configurada")
        
        for fixture in fixtures:
            self.prediction_fetcher.schedule_prediction_fetch(
                match_id=fixture.match_id,
                match_date=fixture.date,
                home_team=fixture.home_team,
                away_team=fixture.away_team
            )
    
    def extract_ml_features(self, match_id: int, prediction: MatchPrediction) -> MLFeatures:
        """Extrae features ML de una predicción"""
        return self.feature_extractor.extract_features(match_id, prediction)
    
    def get_quota_status(self) -> Optional[APIQuotaStatus]:
        """Obtiene estado de cuota de API"""
        if not self.client:
            return None
        
        return self.client.check_quota_status()
    
    def get_usage_today(self) -> int:
        """Obtiene uso de API de hoy"""
        if not self.client:
            return 0
        
        return self.client.cache.get_today_usage()
    
    # ========== FUNCIONALIDADES DE CÁLCULO PRINCIPALES ==========
    
    def calcular_fuerzas(self, df) -> tuple:
        """Calcula fuerzas de equipos usando datos históricos"""
        return calcular_fuerzas(df)
    
    def predecir_partido(self, local: str, visitante: str, fuerzas: dict, 
                        media_liga_local: float, media_liga_visitante: float) -> dict:
        """Predice resultado de un partido combinando fuerzas históricas"""
        return predecir_partido(local, visitante, fuerzas, media_liga_local, media_liga_visitante)
    
    def obtener_h2h(self, local: str, visitante: str, df) -> List[dict]:
        """Obtiene histórico de encuentros entre dos equipos"""
        return obtener_h2h(local, visitante, df)
    
    def obtener_proximos_partidos(self, fixture_url: str) -> List[dict]:
        """Obtiene próximos partidos desde URL de fixture"""
        return obtener_proximos_partidos(fixture_url)


# ========== INSTANCIA GLOBAL ==========

# Esta instancia global será usada por app.py, cli.py y otros módulos
timba_api = None

def inicializar_timba_core():
    """Inicializa la instancia global de Timba Core"""
    global timba_api
    timba_api = TimbaCoreAPI()
    return timba_api

def obtener_timba_core() -> TimbaCoreAPI:
    """Obtiene la instancia global de Timba Core"""
    global timba_api
    if timba_api is None:
        timba_api = inicializar_timba_core()
    return timba_api
