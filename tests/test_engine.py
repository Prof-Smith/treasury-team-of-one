from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine import load_truth_set, calculate_forecast, scenario_summary, model_checks

P=Path(__file__).parents[1]/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'

def test_load_and_forecast():
    ts=load_truth_set(P); fc=calculate_forecast(ts)
    assert len(fc)==3*6*10
    assert set(fc['Scenario'])=={'Reported','Downside','Stress'}

def test_receipt_once_per_scenario():
    ts=load_truth_set(P); fc=calculate_forecast(ts)
    for sc in ['Reported','Downside','Stress']:
        g=fc[(fc['Scenario']==sc)&(fc['Entity ID']=='E004')]
        assert (g['Scenario Receipt (LCY)']>0).sum()==1

def test_model_checks():
    ts=load_truth_set(P); fc=calculate_forecast(ts)
    assert model_checks(ts,fc)['Pass'].all()

def test_scenario_ordering():
    ts=load_truth_set(P); fc=calculate_forecast(ts); s=scenario_summary(fc,ts).set_index('Scenario')
    assert s.loc['Stress','Lowest Cash'] < s.loc['Downside','Lowest Cash']
