from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

HEADER_ROW = 3
REQUIRED_SHEETS = {
    'Entities','Opening Balances','Approved FX','Facilities',
    'Scenario Assumptions','Cash Flow Ledger','Accepted Treatments'
}

@dataclass
class TruthSet:
    entities: pd.DataFrame
    balances: pd.DataFrame
    fx: pd.DataFrame
    facilities: pd.DataFrame
    scenarios: pd.DataFrame
    ledger: pd.DataFrame
    treatments: pd.DataFrame


def _read_sheet(source, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(source, sheet_name=sheet, header=HEADER_ROW, engine='openpyxl')
    return df.dropna(how='all').copy()


def load_truth_set(source) -> TruthSet:
    xls = pd.ExcelFile(source, engine='openpyxl')
    missing = sorted(REQUIRED_SHEETS - set(xls.sheet_names))
    if missing:
        raise ValueError('Missing required sheets: ' + ', '.join(missing))
    ts = TruthSet(
        entities=_read_sheet(source,'Entities'),
        balances=_read_sheet(source,'Opening Balances'),
        fx=_read_sheet(source,'Approved FX'),
        facilities=_read_sheet(source,'Facilities'),
        scenarios=_read_sheet(source,'Scenario Assumptions'),
        ledger=_read_sheet(source,'Cash Flow Ledger'),
        treatments=_read_sheet(source,'Accepted Treatments'),
    )
    normalize(ts)
    return ts


def normalize(ts: TruthSet) -> None:
    ts.entities['Entity ID'] = ts.entities['Entity ID'].astype(str).str.strip()
    ts.balances['Entity ID'] = ts.balances['Entity ID'].astype(str).str.strip()
    ts.ledger['Entity ID'] = ts.ledger['Entity ID'].astype(str).str.strip()
    for frame, cols in [(ts.balances,['Available Balance (LCY)']),
                        (ts.fx,['USD per LCY']),
                        (ts.facilities,['Commitment','Drawn','Minimum Draw']),
                        (ts.scenarios,['Orion Receipt Amount','Unplanned Gulf Payment Amount']),
                        (ts.ledger,['Amount (LCY)']),
                        (ts.entities,['Min Operating Cash (LCY)'])]:
        for c in cols:
            frame[c] = pd.to_numeric(frame[c], errors='coerce').fillna(0.0)
    for c in ['Orion Receipt Date','Unplanned Gulf Payment Date']:
        ts.scenarios[c] = pd.to_datetime(ts.scenarios[c], errors='coerce').dt.normalize()
    ts.ledger['Date'] = pd.to_datetime(ts.ledger['Date'], errors='coerce').dt.normalize()
    ts.facilities['Calculated Available'] = (ts.facilities['Commitment'] - ts.facilities['Drawn']).clip(lower=0)


def calculate_forecast(ts: TruthSet, funding_actions: Optional[Dict[str,float]]=None) -> pd.DataFrame:
    funding_actions = funding_actions or {}
    dates = pd.date_range(ts.ledger['Date'].min(), ts.ledger['Date'].max(), freq='D')
    ledger_net = ts.ledger.groupby(['Entity ID','Date'], as_index=False)['Amount (LCY)'].sum()
    opening = ts.balances.groupby('Entity ID')['Available Balance (LCY)'].sum().to_dict()
    ent = ts.entities.set_index('Entity ID')
    fx = ts.fx.set_index('Currency')['USD per LCY'].to_dict()
    rows=[]
    for _, sc in ts.scenarios.iterrows():
        scenario=str(sc['Scenario'])
        for eid, erow in ent.iterrows():
            bal=float(opening.get(eid,0.0))
            for d in dates:
                match=ledger_net[(ledger_net['Entity ID']==eid)&(ledger_net['Date']==d)]
                flow=float(match['Amount (LCY)'].sum())
                receipt=0.0
                if eid=='E004' and pd.notna(sc['Orion Receipt Date']) and d==sc['Orion Receipt Date']:
                    receipt=float(sc['Orion Receipt Amount'])
                stress=0.0
                if eid=='E004' and pd.notna(sc['Unplanned Gulf Payment Date']) and d==sc['Unplanned Gulf Payment Date']:
                    stress=-float(sc['Unplanned Gulf Payment Amount'])
                key=f'{scenario}|{eid}|{d.date().isoformat()}'
                funding=float(funding_actions.get(key,0.0))
                end=bal+flow+receipt+stress+funding
                minimum=float(erow['Min Operating Cash (LCY)'])
                status='NEGATIVE' if end<0 else ('BELOW MINIMUM' if end<minimum else 'OK')
                rows.append({
                    'Scenario':scenario,'Date':d,'Entity ID':eid,'Entity':erow['Canonical Entity'],
                    'Currency':erow['Currency'],'Opening Available (LCY)':bal,
                    'Ledger Net Flow (LCY)':flow,'Scenario Receipt (LCY)':receipt,
                    'Stress Payment (LCY)':stress,'Funding Action (LCY)':funding,
                    'Ending Available (LCY)':end,'Policy Minimum (LCY)':minimum,
                    'Surplus / (Shortfall)':end-minimum,
                    'Ending Available (USD)':end*float(fx.get(erow['Currency'],1.0)),
                    'Status':status
                })
                bal=end
    return pd.DataFrame(rows)


def scenario_summary(forecast: pd.DataFrame, ts: TruthSet, entity_id='E004') -> pd.DataFrame:
    local = ts.facilities.loc[ts.facilities['Borrower Entity ID'].astype(str)==entity_id,'Calculated Available'].sum()
    out=[]
    for sc,g in forecast[forecast['Entity ID']==entity_id].groupby('Scenario', sort=False):
        trough_idx=g['Ending Available (LCY)'].idxmin(); trough=g.loc[trough_idx]
        out.append({
            'Scenario':sc,'Lowest Cash':trough['Ending Available (LCY)'],'Trough Date':trough['Date'],
            'Lowest Surplus / (Shortfall)':trough['Surplus / (Shortfall)'],
            'Days Below Minimum':int((g['Status']!='OK').sum()),'Days Negative':int((g['Status']=='NEGATIVE').sum()),
            'Local Facility Available':float(local),'Unfunded After Local Facility':max(0.0,-float(trough['Ending Available (LCY)'])-float(local))
        })
    return pd.DataFrame(out)


def consolidated_snapshot(forecast: pd.DataFrame, scenario: str, as_of=None) -> dict:
    g=forecast[forecast['Scenario']==scenario]
    if as_of is None: as_of=g['Date'].min()
    d=g[g['Date']==pd.Timestamp(as_of)]
    return {
        'available_usd':float(d['Ending Available (USD)'].sum()),
        'entities_below_minimum':int((d['Status']!='OK').sum()),
        'entities_negative':int((d['Status']=='NEGATIVE').sum()),
    }


def model_checks(ts: TruthSet, forecast: pd.DataFrame) -> pd.DataFrame:
    checks=[]
    checks.append(('Unique account IDs', ts.balances['Account ID'].duplicated().sum()==0))
    checks.append(('Restricted accounts excluded from available cash', ts.balances.loc[ts.balances['Restricted?'].eq('Y'),'Available Balance (LCY)'].sum()==0))
    checks.append(('Facilities reconcile', ((ts.facilities['Commitment']-ts.facilities['Drawn']-ts.facilities['Calculated Available']).abs()<0.01).all()))
    for sc in ts.scenarios['Scenario'].astype(str):
        n=((forecast['Scenario']==sc)&(forecast['Entity ID']=='E004')&(forecast['Scenario Receipt (LCY)']>0)).sum()
        checks.append((f'One Orion receipt in {sc}',n==1))
    checks.append(('No missing forecast dates',forecast['Date'].notna().all()))
    return pd.DataFrame(checks,columns=['Check','Pass'])
