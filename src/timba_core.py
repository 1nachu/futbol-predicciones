import pandas as pd
import io
import requests
from scipy.stats import poisson
import numpy as np
from difflib import get_close_matches
from datetime import datetime, timedelta

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

# ========== DICCIONARIO DE ALIAS DE EQUIPOS ==========
ALIAS_TEAMS = {
    # --- PREMIER LEAGUE ---
    "Manchester United": "Man United", "Man Utd": "Man United",
    "Manchester City": "Man City",
    "Tottenham Hotspur": "Tottenham", "Spurs": "Tottenham",
    "Wolverhampton Wanderers": "Wolves", "Wolverhampton": "Wolves",
    "Nottingham Forest": "Nott'm Forest",
    "Brighton & Hove Albion": "Brighton",
    "Newcastle United": "Newcastle",
    "West Ham United": "West Ham",
    "Sheffield United": "Sheffield United",

    # --- LA LIGA ---
    "Atletico Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao", "Athletic Bilbao": "Ath Bilbao",
    "Real Betis": "Betis",
    "Celta de Vigo": "Celta",
    "RCD Mallorca": "Mallorca",
    "Rayo Vallecano": "Vallecano",
    "Real Sociedad": "Sociedad",
    "Deportivo Alavés": "Alaves", "Alavés": "Alaves", "Deportivo Alaves": "Alaves",
    "RCD Espanyol de Barcelona": "Espanol", "Espanyol": "Espanol",

    # --- BUNDESLIGA ---
    "Bayer 04 Leverkusen": "Leverkusen", "Bayer Leverkusen": "Leverkusen",
    "Borussia Dortmund": "Dortmund",
    "Borussia Monchengladbach": "M'gladbach", "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "Bayern Munich": "Bayern Munich",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "Mainz 05": "Mainz", "1. FSV Mainz 05": "Mainz",
    "SV Werder Bremen": "Werder Bremen",
    "Sport-Club Freiburg": "Freiburg", "SC Freiburg": "Freiburg",

    # --- SERIE A ---
    "Internazionale": "Inter", "Inter Milan": "Inter",
    "AC Milan": "Milan",
    "AS Roma": "Roma",
    "Hellas Verona": "Verona",

    # --- LIGUE 1 ---
    "Paris Saint-Germain": "Paris SG", "Paris SG": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon",
    "AS Monaco": "Monaco",
    "Stade Rennais FC": "Rennes", "Stade Rennais": "Rennes",
    "RC Lens": "Lens",
    "Havre Athletic Club": "Le Havre",
    "Stade Brestois 29": "Brest",

    # --- BRASIL SÉRIE A ---
    "Flamengo": "Flamengo", "Clube de Regatas do Flamengo": "Flamengo", "Flamengo RJ": "Flamengo",
    "Palmeiras": "Palmeiras", "SE Palmeiras": "Palmeiras", "Palmeiras SP": "Palmeiras",
    "São Paulo": "Sao Paulo", "Sao Paulo": "Sao Paulo", "Sao Paulo FC": "Sao Paulo", "São Paulo FC": "Sao Paulo", "SPFC": "Sao Paulo",
    "Corinthians": "Corinthians", "SC Corinthians": "Corinthians", "Corinthians SP": "Corinthians",
    "Atlético Mineiro": "Ath Mineiro", "Atletico Mineiro": "Ath Mineiro", "ATLÉTICO PARANAENSE": "Ath Mineiro",
    "Internacional": "Internacional", "SC Internacional": "Internacional",
    "Fluminense": "Fluminense", "Fluminense FC": "Fluminense", "Fluminense RJ": "Fluminense",
    "Botafogo": "Botafogo", "Botafogo de Futebol e Regatas": "Botafogo",
    "Grêmio": "Gremio", "Gremio": "Gremio",
    "Cruzeiro": "Cruzeiro",
    "Santos": "Santos", "Santos FC": "Santos",
    "Vasco da Gama": "Vasco", "Clube de Regatas do Vasco da Gama": "Vasco",
    "Bahia": "Bahia", "Esporte Clube Bahia": "Bahia",
    "Cebolinha": "Cebolinha", "EC Vitória": "Vitoria",
    "Fortaleza": "Fortaleza", "Fortaleza EC": "Fortaleza",
    "Cuiabá": "Cuiaba", "Cuiaba": "Cuiaba",
    "Goiás": "Goias", "Goias": "Goias",
    "Atlético Goianiense": "Ath Goianiense", "Atletico Goianiense": "Ath Goianiense",
    "Coritiba": "Coritiba",
    "RB Bragantino": "Bragantino", "Red Bull Bragantino": "Bragantino",
    "Juventude": "Juventude",
    "Chapecoense": "Chapecoense",
    "América MG": "America-MG", "América Mineiro": "America-MG",
    "Avaí": "Avai", "Avai": "Avai",
    "Amazonas": "Amazonas",
    "Athletico Paranaense": "Athletico PR", "Atletico Paranaense": "Athletico PR",

    # --- ARGENTINA LIGA PROFESIONAL ---
    "Boca Juniors": "Boca Juniors", "Boca": "Boca Juniors",
    "River Plate": "River Plate", "Club Atletico River Plate": "River Plate",
    "Racing Club": "Racing", "Racing": "Racing",
    "Independiente": "Independiente", "CA Independiente": "Independiente",
    "San Lorenzo": "San Lorenzo", "San Lorenzo de Almagro": "San Lorenzo",
    "Estudiantes": "Estudiantes", "Estudiantes de la Plata": "Estudiantes",
    "Talleres": "Talleres", "Talleres de Córdoba": "Talleres",
    "Rosario Central": "Rosario Central", "Central Cordoba": "Central Cordoba",
    "Newell's Old Boys": "Newells", "Newells": "Newells",
    "Vélez": "Velez", "Velez Sarsfield": "Velez", "Vélez Sársfield": "Velez",
    "Argentinos": "Argentinos", "Argentinos Juniors": "Argentinos",
    "Huracán": "Huracan", "Huracan": "Huracan",
    "Boca Juniors": "Boca",
    "Godoy Cruz": "Godoy Cruz",
    "Deportivo Morón": "Moron", "Moron": "Moron",
    "Gimnasia y Esgrima": "Gimnasia", "Gimnasia La Plata": "Gimnasia",
    "Défensa y Justicia": "Defensa", "Defensa y Justicia": "Defensa",
    "Banfield": "Banfield",
    "Atlético Tucumán": "Ath Tucuman", "Atletico Tucuman": "Ath Tucuman",
    "Platense": "Platense",
    "Lanús": "Lanus", "Lanus": "Lanus",
    "Tigre": "Tigre",
    "Colón": "Colon", "Colon": "Colon",
    "Unión": "Union", "Union": "Union",
    "Arsenal": "Arsenal",
    "Quilmes": "Quilmes",
    "Barracas Central": "Barracas"
}


def normalizar_csv(df):
    rename_map = {
        'Team 1': 'HomeTeam', 'Team 2': 'AwayTeam', 'Team1': 'HomeTeam', 'Team2': 'AwayTeam',
        'Home Team': 'HomeTeam', 'Away Team': 'AwayTeam', 'Date': 'Date', 'Score': 'FT',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if 'FT' in df.columns and 'FTHG' not in df.columns:
        try:
            ft_split = df['FT'].astype(str).str.split('-', expand=True)
            if ft_split.shape[1] >= 2:
                df['FTHG'] = pd.to_numeric(ft_split[0], errors='coerce')
                df['FTAG'] = pd.to_numeric(ft_split[1], errors='coerce')
        except:
            pass
    required_cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col in ['FTHG', 'FTAG'] else ''
    return df


def descargar_csv_safe(url_or_list, timeout=10):
    """
    Intenta descargar un CSV desde una URL o una lista de URLs alternativas.
    Retorna (df, True) si tuvo éxito, o (None, False) si todas fallaron.
    """
    urls = []
    if isinstance(url_or_list, (list, tuple)):
        urls = list(url_or_list)
    elif isinstance(url_or_list, str):
        urls = [url_or_list]
    else:
        return None, False

    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            content = r.content
            # Try utf-8 then latin1
            text = None
            try:
                text = content.decode('utf-8')
            except Exception:
                try:
                    text = content.decode('latin1')
                except Exception:
                    text = content.decode('utf-8', errors='replace')

            df = pd.read_csv(io.StringIO(text))
            if df is None or df.empty:
                # treat as failure and try next
                continue
            df = normalizar_csv(df)
            return df, True
        except Exception:
            # try next URL
            continue

    return None, False


def obtener_proximos_partidos(url_fixture):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url_fixture, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        if isinstance(data, list):
            partidos_raw = data
        elif isinstance(data, dict) and 'fixtures' in data:
            partidos_raw = data['fixtures']
        else:
            return []
        fixtures = []
        hoy = datetime.now()
        fecha_limite = hoy + timedelta(days=10)
        for partido in partidos_raw:
            local = partido.get('HomeTeam') or partido.get('match_hometeam_name')
            visitante = partido.get('AwayTeam') or partido.get('match_awayteam_name')
            fecha_str = partido.get('DateUtc') or partido.get('match_date') or partido.get('Date')
            if local and visitante and fecha_str:
                try:
                    fecha_str_clean = fecha_str.replace('UTC', '').replace('Z', '').strip()
                    try:
                        fecha_partido = datetime.strptime(fecha_str_clean, '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        fecha_partido = datetime.strptime(fecha_str_clean, '%Y-%m-%d %H:%M:%S')
                    if hoy <= fecha_partido <= fecha_limite:
                        fixtures.append({'local': local, 'visitante': visitante, 'fecha': fecha_partido})
                except:
                    continue
        fixtures.sort(key=lambda x: x['fecha'])
        return fixtures
    except:
        return []


def emparejar_equipo(nombre_fixture, equipos_validos):
    """
    Empareja el nombre del equipo con el más similar.
    Primero intenta usar ALIAS_TEAMS, luego usa difflib con fuzzy matching.
    Retorna (nombre_normalizado, exito_bool).
    """
    # Paso 1: Buscar en ALIAS_TEAMS
    if nombre_fixture in ALIAS_TEAMS:
        nombre_normalizado = ALIAS_TEAMS[nombre_fixture]
        if nombre_normalizado in equipos_validos:
            return nombre_normalizado, True
    
    # Paso 2: Buscar alias de nombres ya normalizados
    for alias_key, alias_value in ALIAS_TEAMS.items():
        if nombre_fixture.lower() == alias_value.lower():
            if alias_value in equipos_validos:
                return alias_value, True
    
    # Paso 3: Usar difflib con fuzzy matching
    coincidencias = get_close_matches(nombre_fixture, equipos_validos, n=1, cutoff=0.6)
    if coincidencias:
        return coincidencias[0], True
    
    return None, False


def encontrar_equipo_similar(nombre, equipos_validos):
    return get_close_matches(nombre, equipos_validos, n=5, cutoff=0.6)


def imprimir_barra(valor, maximo=100, ancho=25):
    porcentaje = (valor / maximo) * 100 if maximo > 0 else 0
    bloques_llenos = int((porcentaje / 100) * ancho)
    barra = "█" * bloques_llenos + "░" * (ancho - bloques_llenos)
    return barra, porcentaje


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
