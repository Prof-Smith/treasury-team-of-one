from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

HEADER_ROW = 3
REQUIRED_SHEETS = {'Entities','Opening Balances','Approved FX','Facilities','Scenario Assumptions','Cash Flow Ledger','Accepted Treatments'}

@dataclass
class TruthSet:
    entities: pd.DataFrame
    balances: pd.DataFrame
    fx: pd.DataFrame
    facilities: pd.DataFrame
    scenarios: pd.DataFrame
    ledger: pd.DataFrame
    treatments: pd.DataFrame

def _read(source, sheet):
    return pd.read_excel(source, sheet_name=sheet, header=HEADER_ROW, engine='openpyxl').dropna(how='all').copy()

def load_truth_set(source) -> TruthSet:
    xls = pd.ExcelFile(source, engine='openpyxl')
    missing = sorted(REQUIRED_SHEETS - set(xls.sheet_names))
    if missing: raise ValueError('Missing required sheets: ' + ', '.join(missing))
    ts = TruthSet(*[_read(source,s) for s in ['Entities','Opening Balances','Approved FX','Facilities','Scenario Assumptions','Cash Flow Ledger','Accepted Treatments']])
    for df,col in [(ts.entities,'Entity ID'),(ts.balances,'Entity ID'),(ts.ledger,'Entity ID')]: df[col]=df[col].astype(str).str.strip()
    for df,cols in [(ts.entities,['Min Operating Cash (LCY)']),(ts.balances,['Available Balance (LCY)','Ledger Balance (LCY)']),(ts.fx,['USD per LCY']),(ts.facilities,['Commitment','Drawn','Minimum Draw']),(ts.scenarios,['Orion Receipt Amount','Unplanned Gulf Payment Amount']),(ts.ledger,['Amount (LCY)'])]:
        for c in cols:
            if c in df.columns: df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0.0)
    ts.ledger['Date']=pd.to_datetime(ts.ledger['Date'],errors='coerce').dt.normalize()
    for c in ['Orion Receipt Date','Unplanned Gulf Payment Date']:
        ts.scenarios[c]=pd.to_datetime(ts.scenarios[c],errors='coerce').dt.normalize()
    ts.facilities['Calculated Available']=(ts.facilities['Commitment']-ts.facilities['Drawn']).clip(lower=0)
    return ts

def calculate_forecast(ts: TruthSet, scenario_overrides: Optional[dict]=None, funding_actions: Optional[Dict[str,float]]=None):
    scenario_overrides=scenario_overrides or {}; funding_actions=funding_actions or {}
    dates=pd.date_range(ts.ledger['Date'].min(),ts.ledger['Date'].max(),freq='D')
    net=ts.ledger.groupby(['Entity ID','Date'],as_index=False)['Amount (LCY)'].sum()
    opening=ts.balances.groupby('Entity ID')['Available Balance (LCY)'].sum().to_dict()
    entities=ts.entities.set_index('Entity ID'); fx=ts.fx.set_index('Currency')['USD per LCY'].to_dict()
    rows=[]
    for _,sc0 in ts.scenarios.iterrows():
        sc=sc0.copy(); name=str(sc['Scenario']); sc.update(scenario_overrides.get(name,{}))
        for eid,e in entities.iterrows():
            cash=float(opening.get(eid,0))
            for d in dates:
                flow=float(net.loc[(net['Entity ID']==eid)&(net['Date']==d),'Amount (LCY)'].sum())
                receipt=float(sc['Orion Receipt Amount']) if eid=='E004' and pd.notna(sc['Orion Receipt Date']) and d==pd.Timestamp(sc['Orion Receipt Date']) else 0.0
                shock=-float(sc['Unplanned Gulf Payment Amount']) if eid=='E004' and pd.notna(sc['Unplanned Gulf Payment Date']) and d==pd.Timestamp(sc['Unplanned Gulf Payment Date']) else 0.0
                key=f'{name}|{eid}|{d.date().isoformat()}'; funding=float(funding_actions.get(key,0))
                end=cash+flow+receipt+shock+funding; minimum=float(e['Min Operating Cash (LCY)'])
                status='NEGATIVE' if end<0 else ('BELOW MINIMUM' if end<minimum else 'OK')
                rows.append({'Scenario':name,'Date':d,'Entity ID':eid,'Entity':e['Canonical Entity'],'Currency':e['Currency'],'Opening Available (LCY)':cash,'Ledger Net Flow (LCY)':flow,'Scenario Receipt (LCY)':receipt,'Stress Payment (LCY)':shock,'Funding Action (LCY)':funding,'Ending Available (LCY)':end,'Policy Minimum (LCY)':minimum,'Surplus / (Shortfall)':end-minimum,'Ending Available (USD)':end*float(fx.get(e['Currency'],1)),'Status':status})
                cash=end
    return pd.DataFrame(rows)

def scenario_summary(fc,ts,entity_id='E004'):
    local=float(ts.facilities.loc[ts.facilities['Borrower Entity ID'].astype(str)==entity_id,'Calculated Available'].sum())
    out=[]
    for name,g in fc[fc['Entity ID']==entity_id].groupby('Scenario',sort=False):
        trough=g.loc[g['Ending Available (LCY)'].idxmin()]
        out.append({'Scenario':name,'Lowest Cash':float(trough['Ending Available (LCY)']),'Trough Date':trough['Date'],'Lowest Surplus / (Shortfall)':float(trough['Surplus / (Shortfall)']),'Days Below Minimum':int((g.Status!='OK').sum()),'Days Negative':int((g.Status=='NEGATIVE').sum()),'Local Facility Available':local,'Unfunded After Local Facility':max(0,-float(trough['Ending Available (LCY)'])-local)})
    return pd.DataFrame(out)

def model_checks(ts,fc):
    rows=[('Unique account IDs',not ts.balances['Account ID'].duplicated().any()),('Restricted cash excluded',float(ts.balances.loc[ts.balances['Restricted?'].eq('Y'),'Available Balance (LCY)'].sum())==0),('Facilities reconcile',((ts.facilities.Commitment-ts.facilities.Drawn-ts.facilities['Calculated Available']).abs()<.01).all()),('All forecast dates valid',fc.Date.notna().all())]
    for sc in ts.scenarios.Scenario.astype(str): rows.append((f'One Orion receipt in {sc}',int(((fc.Scenario==sc)&(fc['Entity ID']=='E004')&(fc['Scenario Receipt (LCY)']>0)).sum())==1))
    return pd.DataFrame(rows,columns=['Check','Pass'])
