#!/usr/bin/env python3
"""
Test rápido para validar cálculos de Córners (Over/Under y Ganador)
"""

import sys
sys.path.insert(0, '/home/nahuel/Documentos/projecto timba')

from timba_core import predecir_partido, calcular_fuerzas
import pandas as pd

# Datos de prueba con córners
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
    'HC': [8, 6, 9],      # Córners Local
    'AC': [4, 5, 7],      # Córners Visitante
    'HY': [1, 2, 1],
    'AY': [0, 1, 2],
    'HR': [0, 0, 1],
    'AR': [0, 0, 0],
}

df = pd.DataFrame(test_data)

print("=" * 70)
print("🧪 TEST: MERCADOS DE CÓRNERS")
print("=" * 70)

try:
    fuerzas, media_local, media_vis = calcular_fuerzas(df)
    print(f"\n✅ Fuerzas calculadas para {len(fuerzas)} equipos")
    
    # Mostrar métricas de córners
    print("\n📊 Métricas de Córners en Fuerzas:")
    for equipo, datos in fuerzas.items():
        print(f"\n  {equipo}:")
        print(f"    Corners_Casa: {datos.get('Corners_Casa', 0):.2f}")
        print(f"    Corners_Fuera: {datos.get('Corners_Fuera', 0):.2f}")
        print(f"    Corners_Casa_Contra: {datos.get('Corners_Casa_Contra', 0):.2f}")
        print(f"    Corners_Fuera_Contra: {datos.get('Corners_Fuera_Contra', 0):.2f}")
        print(f"    Corners_Promedio: {datos.get('Corners_Promedio', 0):.2f}")
    
    pred = predecir_partido('Team A', 'Team B', fuerzas, media_local, media_vis)
    
    if pred:
        print(f"\n✅ Predicción generada para Team A vs Team B")
        
        # Verificar claves de córners
        corners_keys = ['Corners_Lambda_Total', 'Over_85', 'Over_95', 'Under_105', 
                       'Prob_Local_Mas_Corners', 'Prob_Empate_Corners', 'Prob_Vis_Mas_Corners']
        
        print("\n🚩 Nuevas Claves de Córners:")
        for k in corners_keys:
            if k in pred:
                val = pred[k]
                if isinstance(val, float):
                    print(f"  ✅ {k}: {val:.4f}")
                else:
                    print(f"  ✅ {k}: {val}")
            else:
                print(f"  ❌ FALTA: {k}")
        
        # Mostrar probabilidades
        print(f"\n📈 Mercados de Córners:")
        print(f"  Lambda Total: {pred.get('Corners_Lambda_Total', 0):.2f}")
        print(f"  Over 8.5:  {pred.get('Over_85', 0)*100:.2f}%")
        print(f"  Over 9.5:  {pred.get('Over_95', 0)*100:.2f}%")
        print(f"  Under 10.5: {pred.get('Under_105', 0)*100:.2f}%")
        
        print(f"\n🥊 Ganador de Córners:")
        print(f"  Local saca más:  {pred.get('Prob_Local_Mas_Corners', 0)*100:.2f}%")
        print(f"  Empate técnico:  {pred.get('Prob_Empate_Corners', 0)*100:.2f}%")
        print(f"  Visitante saca más: {pred.get('Prob_Vis_Mas_Corners', 0)*100:.2f}%")
        
        # Validación
        total = pred.get('Prob_Local_Mas_Corners', 0) + pred.get('Prob_Empate_Corners', 0) + pred.get('Prob_Vis_Mas_Corners', 0)
        print(f"\n  ✅ Suma de probabilidades (debe ser ≈1.0): {total:.4f}")
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 70)
    else:
        print("❌ Error: No se pudo generar predicción")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
