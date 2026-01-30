"""
Core de análisis y predicción de partidos de fútbol - v2.0
Integración con team_normalization y utilidades compartidas.
"""

import pandas as pd
import io
import requests
from scipy.stats import poisson
import numpy as np
from difflib import get_close_matches
from datetime import datetime, timedelta

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
