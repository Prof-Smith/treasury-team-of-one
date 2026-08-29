from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine import *
def test_engine():
 t=load_truth_set(Path(__file__).parents[1]/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'); f=calculate_forecast(t); assert len(f)==180; assert checks(t,f).Pass.all(); s=scenario_summary(f,t).set_index('Scenario'); assert s.loc['Stress','Trough']<s.loc['Downside','Trough']
