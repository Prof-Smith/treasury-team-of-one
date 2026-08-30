from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DATES=pd.date_range('2026-08-31',periods=10,freq='D')
OPENING=620000.0
MINIMUM=200000.0
ORION=620000.0
BASE=np.array([-35000,-45000,0,-155000,-65000,-50000,15000,-75000,45000,-25000],float)
REQUIRED_HISTORY=['date','opening_error','receipt_error','disbursement_error']
STORMS=[
('Opening cash revised',-25000,1.05,[.48,.32,.15,.05],0),
('Orion timing challenged',-25000,1.15,[.18,.37,.32,.13],0),
('Payments concentrate',-25000,1.25,[.18,.37,.32,.13],-90000),
('Local line corrected',-25000,1.28,[.18,.35,.33,.14],-90000),
('Transfer access constrained',-25000,1.38,[.10,.30,.40,.20],-90000)]

def load_history(source):
    name=getattr(source,'name',str(source)).lower()
    df=pd.read_excel(source,engine='openpyxl') if name.endswith(('.xlsx','.xls')) else pd.read_csv(source)
    missing=[c for c in REQUIRED_HISTORY if c not in df.columns]
    if missing: raise ValueError('Historical file is missing: '+', '.join(missing))
    df=df[REQUIRED_HISTORY].copy(); df['date']=pd.to_datetime(df.date,errors='coerce')
    for c in REQUIRED_HISTORY[1:]: df[c]=pd.to_numeric(df[c],errors='coerce')
    df=df.dropna()
    if len(df)<60: raise ValueError('At least 60 complete historical observations are required.')
    return df

def simulate(hist,stage=-1,n=3000,seed=77,funding=0):
    rng=np.random.default_rng(seed+stage+1)
    if stage<0: shift=0; vol=.62; probs=np.array([.72,.20,.07,.01]); extra=0
    else:
        _,shift,vol,probs,extra=STORMS[stage]; probs=np.array(probs)
    receipt_days=np.array([2,4,8,11]); selected=rng.choice(receipt_days,n,p=probs)
    vals=hist[REQUIRED_HISTORY[1:]].to_numpy(); sims=np.zeros((n,10))
    # deterministic reference trough for loss definition
    ref=[]; c=OPENING+shift
    for i in range(10): c+=BASE[i]+(ORION if i==2 else 0)+(extra if i==4 else 0)+(funding if i==3 else 0); ref.append(c)
    ref_trough=min(ref); losses=np.zeros(n)
    for j in range(n):
        idx=rng.integers(0,len(vals),10); sampled=vals[idx]; cash=OPENING+shift+sampled[0,0]*vol
        for i in range(10):
            err=(sampled[i,1]+sampled[i,2])*vol
            receipt=ORION if selected[j]==i else 0
            cash+=BASE[i]+err+receipt+(extra if i==4 else 0)+(funding if i==3 else 0); sims[j,i]=cash
        losses[j]=max(0,ref_trough-sims[j].min())
    var=float(np.quantile(losses,.95)); tail=losses[losses>=var]
    return {'sims':sims,'mean':sims.mean(0),'p025':np.quantile(sims,.025,0),'p25':np.quantile(sims,.25,0),'p75':np.quantile(sims,.75,0),'p975':np.quantile(sims,.975,0),'var':var,'cvar':float(tail.mean()),'pmin':float((sims.min(1)<MINIMUM).mean()),'pneg':float((sims.min(1)<0).mean())}

def profile_attachment(path):
    p=Path(path); out={'file':p.name,'type':p.suffix.lower(),'sheets':1,'rows':0,'columns':0,'notes':[]}
    try:
        if p.suffix.lower()=='.csv': df=pd.read_csv(p); frames={p.stem:df}
        else:
            x=pd.ExcelFile(p,engine='openpyxl'); frames={s:pd.read_excel(p,sheet_name=s,engine='openpyxl') for s in x.sheet_names}; out['sheets']=len(frames)
        out['rows']=sum(len(x) for x in frames.values()); out['columns']=max([len(x.columns) for x in frames.values()] or [0])
        cols=' '.join(str(c).lower() for f in frames.values() for c in f.columns)
        if 'currency' in cols: out['notes'].append('Currency field detected')
        if 'account' in cols: out['notes'].append('Account identifiers detected')
        if 'date' in cols or 'day' in cols: out['notes'].append('Date structure detected')
    except Exception as e: out['notes'].append('Parsing warning: '+str(e)[:60])
    return out

def process_inbox(folder):
    return pd.DataFrame([profile_attachment(p) for p in sorted(Path(folder).glob('*')) if p.suffix.lower() in ['.csv','.xlsx','.xls']])

def compare_responses(hist,stage=4):
    rows=[]
    for label,f in [('No action',0),('Local line',50000),('Intercompany transfer',500000),('Layered response',550000)]:
        r=simulate(hist,stage,funding=f); rows.append({'Response':label,'Funding':f,'VaR 95%':r['var'],'CVaR 95%':r['cvar'],'P(Below Minimum)':r['pmin'],'P(Negative)':r['pneg'],'Expected Trough':r['mean'].min()})
    return pd.DataFrame(rows)
