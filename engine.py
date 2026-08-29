from dataclasses import dataclass
import pandas as pd

HEADER_ROW=3
SHEETS=['Entities','Opening Balances','Approved FX','Facilities','Scenario Assumptions','Cash Flow Ledger','Accepted Treatments']
@dataclass
class TruthSet:
    entities:pd.DataFrame; balances:pd.DataFrame; fx:pd.DataFrame; facilities:pd.DataFrame; scenarios:pd.DataFrame; ledger:pd.DataFrame; treatments:pd.DataFrame

def load_truth_set(source):
    xls=pd.ExcelFile(source,engine='openpyxl'); missing=[s for s in SHEETS if s not in xls.sheet_names]
    if missing: raise ValueError('Missing required sheets: '+', '.join(missing))
    frames=[pd.read_excel(source,sheet_name=s,header=HEADER_ROW,engine='openpyxl').dropna(how='all') for s in SHEETS]
    ts=TruthSet(*frames)
    for d in [ts.entities,ts.balances,ts.ledger]: d['Entity ID']=d['Entity ID'].astype(str).str.strip()
    for d,cols in [(ts.entities,['Min Operating Cash (LCY)']),(ts.balances,['Ledger Balance (LCY)','Available Balance (LCY)']),(ts.fx,['USD per LCY']),(ts.facilities,['Commitment','Drawn','Minimum Draw']),(ts.scenarios,['Orion Receipt Amount','Unplanned Gulf Payment Amount']),(ts.ledger,['Amount (LCY)'])]:
        for c in cols:
            if c in d: d[c]=pd.to_numeric(d[c],errors='coerce').fillna(0.)
    ts.ledger['Date']=pd.to_datetime(ts.ledger['Date'],errors='coerce').dt.normalize()
    for c in ['Orion Receipt Date','Unplanned Gulf Payment Date']: ts.scenarios[c]=pd.to_datetime(ts.scenarios[c],errors='coerce').dt.normalize()
    ts.facilities['Calculated Available']=(ts.facilities.Commitment-ts.facilities.Drawn).clip(lower=0)
    return ts

def calculate_forecast(ts,funding_actions=None,custom=None):
    funding_actions=funding_actions or {}; custom=custom or {}
    dates=pd.date_range(ts.ledger.Date.min(),ts.ledger.Date.max(),freq='D')
    net=ts.ledger.groupby(['Entity ID','Date'])['Amount (LCY)'].sum()
    opening=ts.balances.groupby('Entity ID')['Available Balance (LCY)'].sum().to_dict()
    entities=ts.entities.set_index('Entity ID'); fx=ts.fx.set_index('Currency')['USD per LCY'].to_dict(); rows=[]
    for _,src in ts.scenarios.iterrows():
        sc=src.copy(); name=str(sc.Scenario)
        if name in custom:
            for k,v in custom[name].items(): sc[k]=v
        for eid,e in entities.iterrows():
            cash=float(opening.get(eid,0))
            for d in dates:
                flow=float(net.get((eid,d),0)); receipt=0.; shock=0.
                if eid=='E004' and pd.notna(sc['Orion Receipt Date']) and d==pd.Timestamp(sc['Orion Receipt Date']): receipt=float(sc['Orion Receipt Amount'])
                if eid=='E004' and pd.notna(sc['Unplanned Gulf Payment Date']) and d==pd.Timestamp(sc['Unplanned Gulf Payment Date']): shock=-float(sc['Unplanned Gulf Payment Amount'])
                fund=float(funding_actions.get(f'{name}|{eid}|{d.date().isoformat()}',0)); end=cash+flow+receipt+shock+fund; minimum=float(e['Min Operating Cash (LCY)'])
                status='NEGATIVE' if end<0 else ('BELOW MINIMUM' if end<minimum else 'OK')
                rows.append({'Scenario':name,'Date':d,'Entity ID':eid,'Entity':e['Canonical Entity'],'Currency':e.Currency,'Opening':cash,'Net Flow':flow,'Receipt':receipt,'Shock':shock,'Funding':fund,'Ending':end,'Minimum':minimum,'Surplus':end-minimum,'Ending USD':end*float(fx.get(e.Currency,1)),'Status':status}); cash=end
    return pd.DataFrame(rows)

def scenario_summary(fc,ts):
    local=float(ts.facilities.loc[ts.facilities['Borrower Entity ID'].astype(str)=='E004','Calculated Available'].sum()); out=[]
    for name,g in fc[fc['Entity ID']=='E004'].groupby('Scenario',sort=False):
        r=g.loc[g.Ending.idxmin()]; out.append({'Scenario':name,'Trough':float(r.Ending),'Date':r.Date,'Status':r.Status,'Policy Gap':float(r.Surplus),'Local Line':local,'Days At Risk':int((g.Status!='OK').sum())})
    return pd.DataFrame(out)

def checks(ts,fc):
    vals=[('Unique account IDs',not ts.balances['Account ID'].duplicated().any()),('Restricted cash excluded',ts.balances.loc[ts.balances['Restricted?'].eq('Y'),'Available Balance (LCY)'].sum()==0),('Facilities reconcile',((ts.facilities.Commitment-ts.facilities.Drawn-ts.facilities['Calculated Available']).abs()<.01).all()),('Forecast dates complete',fc.Date.notna().all())]
    return pd.DataFrame(vals,columns=['Control','Pass'])
