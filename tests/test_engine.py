from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine import simulate,response_comparison,STORMS

def test_reproducible_and_ordered():
    f=simulate(-1); s=simulate(len(STORMS)-1)
    assert len(f['expected'])==10
    assert f['cvar95']>=f['var95']>=0
    assert s['prob_negative']>=f['prob_negative']

def test_funding_reduces_negative_probability():
    a=simulate(4,funding=0); b=simulate(4,funding=550000)
    assert b['prob_negative']<a['prob_negative']
    assert len(response_comparison())==4
