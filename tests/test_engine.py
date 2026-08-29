from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine import load_truth_set,calculate_forecast,scenario_summary,model_checks
P=Path(__file__).parents[1]/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'
def test_engine():
 ts=load_truth_set(P); fc=calculate_forecast(ts); assert len(fc)==180; assert model_checks(ts,fc).Pass.all()
def test_stress_is_worse():
 ts=load_truth_set(P); s=scenario_summary(calculate_forecast(ts),ts).set_index('Scenario'); assert s.loc['Stress','Lowest Cash']<s.loc['Downside','Lowest Cash']
