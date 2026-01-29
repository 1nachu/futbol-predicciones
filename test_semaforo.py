#!/usr/bin/env python3
"""
Script de prueba para validar que los cálculos de Over/Under,
Doble Oportunidad y Semáforo funcionan correctamente.
"""

import sys
sys.path.insert(0, '/home/nahuel/Documentos/projecto timba')

from timba_core import predecir_partido, calcular_fuerzas
import pandas as pd

# Simulamos datos mínimos para una prueba
test_data = {
    'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
    'HomeTeam': ['Team A', 'Team A', 'Team B'],
    'AwayTeam': ['Team B', 'Team C', 'Team C'],
    'FTHG': [2, 1, 3],
    'FTAG': [1, 0, 2],
    'HS': [10, 8, 12],
    'AS': [5, 6, 8],
    'HST': [5, 4, 6],
    'AST': [2, 3, 4],
    'HC': [8, 6, 9],
    'AC': [4, 5, 7],
    'HY': [1, 2, 1],
    'AY': [0, 1, 2],
    'HR': [0, 0, 1],
    'AR': [0, 0, 0],
}

df = pd.DataFrame(test_data)

print("=" * 60)
print("PRUEBA DE CÁLCULOS: Over/Under, Doble Oportunidad y Semáforo")
print("=" * 60)

try:
    fuerzas, media_local, media_vis = calcular_fuerzas(df)
    print(f"✅ Fuerzas calculadas para {len(fuerzas)} equipos")
    
    pred = predecir_partido('Team A', 'Team B', fuerzas, media_local, media_vis)
    
    if pred:
        print(f"\n✅ Predicción obtenida: Team A vs Team B")
        
        # Validar nuevas claves
        required_keys = ['Over_15', 'Over_25', 'Under_35', 'Prob_1X', 'Prob_X2', 'Prob_12']
        missing = [k for k in required_keys if k not in pred]
        
        if missing:
            print(f"❌ Claves faltantes: {missing}")
        else:
            print(f"✅ Todas las claves de mercado están presentes")
        
        # Mostrar valores
        print(f"\n📊 Mercados de Goles:")
        print(f"   Over 1.5: {pred['Over_15']*100:.2f}%")
        print(f"   Over 2.5: {pred['Over_25']*100:.2f}%")
        print(f"   Under 3.5: {pred['Under_35']*100:.2f}%")
        
        print(f"\n📊 Doble Oportunidad:")
        print(f"   1X (Local o Empate): {pred['Prob_1X']*100:.2f}%")
        print(f"   X2 (Empate o Visitante): {pred['Prob_X2']*100:.2f}%")
        print(f"   12 (Sin empate): {pred['Prob_12']*100:.2f}%")
        
        # Simular semáforo
        print(f"\n💡 Semáforo Visual (Recomendaciones):")
        umbral_alto = 0.70
        umbral_medio = 0.55
        
        recs = []
        if pred['Prob_1X'] >= umbral_alto:
            recs.append(f"🔥 DOBLE OPORTUNIDAD 1X: {pred['Prob_1X']*100:.1f}%")
        if pred['Over_25'] >= umbral_alto:
            recs.append(f"⚽ GOLES +2.5: {pred['Over_25']*100:.1f}%")
        if pred['Under_35'] >= umbral_medio and pred['Under_35'] < umbral_alto:
            recs.append(f"🛡️  SEGURIDAD -3.5: {pred['Under_35']*100:.1f}%")
        
        if recs:
            for rec in recs:
                print(f"   {rec}")
        else:
            print("   (Sin recomendaciones claras > 55%)")
        
        print("\n✅ Test completado exitosamente")
    else:
        print("❌ No se pudo generar predicción")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
