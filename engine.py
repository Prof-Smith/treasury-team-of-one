from __future__ import annotations
import numpy as np
import pandas as pd

DATES = pd.date_range('2026-08-31', periods=10, freq='D')
OPENING = 230_400.0
MINIMUM = 200_000.0
ORION = 620_000.0
BASE_FLOWS = np.array([-85_000,-65_000,0,-410_000,-115_000,-90_000,5_000,-145_000,35_000,-30_000],dtype=float)

STORMS = [
    {'name':'Opening cash uncertainty','effect':'Widen opening-position error','cash_shift':-20_000,'flow_vol':1.10,'receipt_probs':[.40,.35,.20,.05],'extra_payment':0},
    {'name':'Orion receipt challenged','effect':'Receipt timing becomes probabilistic','cash_shift':-20_000,'flow_vol':1.15,'receipt_probs':[.15,.35,.35,.15],'extra_payment':0},
    {'name':'Payment concentration','effect':'Payroll and supplier pressure increases','cash_shift':-20_000,'flow_vol':1.25,'receipt_probs':[.15,.35,.35,.15],'extra_payment':-90_000},
    {'name':'Funding capacity corrected','effect':'Local line reduced from $100K to $50K','cash_shift':-20_000,'flow_vol':1.25,'receipt_probs':[.15,.35,.35,.15],'extra_payment':-90_000},
    {'name':'Liquidity access constrained','effect':'Restricted and parent cash unavailable without approval','cash_shift':-20_000,'flow_vol':1.35,'receipt_probs':[.10,.30,.40,.20],'extra_payment':-90_000},
]

def historical_errors(seed=41, periods=180):
    rng=np.random.default_rng(seed)
    common=rng.standard_t(df=5,size=periods)*18_000
    receipt=rng.normal(0,30_000,periods)+common
    disb=rng.normal(0,22_000,periods)-.55*common
    opening=rng.normal(0,12_000,periods)
    return pd.DataFrame({'opening_error':opening,'receipt_error':receipt,'disbursement_error':disb})

def deterministic_path(receipt_index=2, funding=0, extra_payment=0, cash_shift=0):
    flows=BASE_FLOWS.copy(); flows[4]+=extra_payment
    path=[]; cash=OPENING+cash_shift
    for i,d in enumerate(DATES):
        cash += flows[i] + (ORION if i==receipt_index else 0) + (funding if i==3 else 0)
        path.append(cash)
    return np.array(path)

def simulate(stage=-1, n=5000, seed=77, funding=0):
    hist=historical_errors(); rng=np.random.default_rng(seed+stage+1)
    if stage<0:
        cash_shift=0; vol=.85; probs=np.array([.62,.25,.10,.03]); extra=0
    else:
        s=STORMS[stage]; cash_shift=s['cash_shift']; vol=s['flow_vol']; probs=np.array(s['receipt_probs']); extra=s['extra_payment']
    receipt_days=np.array([2,4,8,11])
    selected=rng.choice(receipt_days,size=n,p=probs)
    sims=np.zeros((n,len(DATES)))
    losses=np.zeros(n)
    expected=deterministic_path(2,funding=funding,extra_payment=extra,cash_shift=cash_shift)
    exp_trough=expected.min()
    for j in range(n):
        sample=hist.sample(len(DATES),replace=True,random_state=int(rng.integers(0,2**31-1)))
        errors=(sample.receipt_error.values+sample.disbursement_error.values)*vol
        cash=OPENING+cash_shift+float(rng.choice(hist.opening_error.values))*vol
        for i in range(len(DATES)):
            receipt=ORION if selected[j]==i else 0
            cash += BASE_FLOWS[i]+errors[i]+receipt+(extra if i==4 else 0)+(funding if i==3 else 0)
            sims[j,i]=cash
        losses[j]=max(0,exp_trough-sims[j].min())
    var=float(np.quantile(losses,.95)); tail=losses[losses>=var]; cvar=float(tail.mean()) if len(tail) else var
    return {
        'sims':sims,'expected':np.mean(sims,axis=0),'p025':np.quantile(sims,.025,axis=0),'p25':np.quantile(sims,.25,axis=0),
        'p75':np.quantile(sims,.75,axis=0),'p975':np.quantile(sims,.975,axis=0),'var95':var,'cvar95':cvar,
        'prob_below_min':float((sims.min(axis=1)<MINIMUM).mean()),'prob_negative':float((sims.min(axis=1)<0).mean()),
        'troughs':sims.min(axis=1),'receipt_days':selected
    }

def response_comparison(stage=4):
    rows=[]
    for name,funding in [('No action',0),('Local line',50_000),('Intercompany transfer',500_000),('Layered response',550_000)]:
        r=simulate(stage=stage,funding=funding)
        rows.append({'Response':name,'Funding':funding,'VaR 95%':r['var95'],'CVaR 95%':r['cvar95'],'P(Below Minimum)':r['prob_below_min'],'P(Negative)':r['prob_negative'],'Expected Trough':float(r['expected'].min())})
    return pd.DataFrame(rows)
