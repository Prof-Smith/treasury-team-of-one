from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine import *
ROOT=Path(__file__).parents[1]
def test_baseline_and_storm():
 h=load_history(ROOT/'data/historical_forecast_errors.csv'); f=simulate(h,-1,n=1000); s=simulate(h,4,n=1000)
 assert f['pneg']<.15
 assert s['pneg']>f['pneg']
 assert f['cvar']>=f['var']
def test_inbox_actual_files():
 p=process_inbox(ROOT/'data/monday_inbox'); assert len(p)==10; assert p.rows.sum()>10
def test_funding_helps():
 h=load_history(ROOT/'data/historical_forecast_errors.csv'); assert simulate(h,4,n=1000,funding=550000)['pneg']<simulate(h,4,n=1000)['pneg']
