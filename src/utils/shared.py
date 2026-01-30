"""
Utilidades compartidas para normalización de datos y búsqueda de equipos.
"""

import pandas as pd
import io
import requests
from difflib import get_close_matches

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
    """Normaliza nombres de columnas de CSV heterogéneos."""
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
                continue
            df = normalizar_csv(df)
            return df, True
        except Exception:
            continue

    return None, False


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
    """Encuentra equipos similares usando fuzzy matching."""
    return get_close_matches(nombre, equipos_validos, n=5, cutoff=0.6)


def imprimir_barra(valor, maximo=100, ancho=25):
    """Genera una barra visual de progreso."""
    porcentaje = (valor / maximo) * 100 if maximo > 0 else 0
    bloques_llenos = int((porcentaje / 100) * ancho)
    barra = "█" * bloques_llenos + "░" * (ancho - bloques_llenos)
    return barra, porcentaje
