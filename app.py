from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from engine import load_truth_set, calculate_forecast, scenario_summary, model_checks

st.set_page_config(page_title='Treasury Team of One',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
BASE=Path(__file__).parent; DEFAULT=BASE/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'
COLORS={'navy':'#102A43','blue':'#186FAF','teal':'#00A6A6','amber':'#F2A900','red':'#D64545','green':'#16866B','ink':'#243B53','muted':'#627D98','bg':'#F4F7FA'}
st.markdown(f'''<style>
.stApp{{background:{COLORS['bg']}}}.block-container{{padding:1.15rem 2rem 3rem;max-width:1500px}}
[data-testid="stSidebar"]{{background:#0F2740}}[data-testid="stSidebar"] *{{color:#F0F5FA!important}}
.hero{{background:linear-gradient(120deg,#102A43,#166A8F);padding:1.4rem 1.6rem;border-radius:18px;color:white;box-shadow:0 10px 28px rgba(16,42,67,.15)}}
.hero h1{{font-size:2.05rem;margin:0}}.hero p{{color:#D9EAF2;margin:.35rem 0 0}}
.eyebrow{{text-transform:uppercase;letter-spacing:.11em;font-size:.72rem;font-weight:800;color:#00C2C7}}
.card{{background:white;border:1px solid #D7E3EC;border-radius:14px;padding:1rem 1.15rem;box-shadow:0 3px 12px rgba(16,42,67,.06);height:100%}}
.card h3{{font-size:1rem;margin:.1rem 0 .45rem;color:#243B53}}.card p{{font-size:.88rem;color:#627D98;margin:0}}
.alert{{background:#FFF7E6;border-left:5px solid #F2A900;border-radius:10px;padding:.85rem 1rem;color:#243B53}}
.danger{{background:#FFF0F0;border-left:5px solid #D64545;border-radius:10px;padding:.85rem 1rem}}
.success{{background:#EAF8F4;border-left:5px solid #16866B;border-radius:10px;padding:.85rem 1rem}}
.step{{font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;color:#627D98;font-weight:800}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D7E3EC;padding:.75rem 1rem;border-radius:14px;box-shadow:0 3px 12px rgba(16,42,67,.05)}}
div[data-testid="stMetricValue"]{{font-size:1.65rem}}.stButton>button{{border-radius:10px;font-weight:700}}
</style>''',unsafe_allow_html=True)

for k,v in {'step':1,'decisions':{},'scenario':'Downside','funding':0.0}.items():
    if k not in st.session_state: st.session_state[k]=v

def hero(kicker,title,subtitle): st.markdown(f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)
def money(v): return f'${v:,.0f}' if abs(v)<1_000_000 else f'${v/1_000_000:,.2f}M'
def status_color(s): return COLORS['red'] if s=='NEGATIVE' else (COLORS['amber'] if s=='BELOW MINIMUM' else COLORS['green'])

with st.sidebar:
    st.markdown('## Treasury Team of One')
    st.caption('Monday-Morning Liquidity Problem')
    uploaded=st.file_uploader('Use revised truth-set workbook',type=['xlsx'])
    pages=['Inbox','Exception Review','Command Center','Scenario Lab','CFO Briefing','Controls']
    page=st.radio('Workflow',pages,index=max(0,min(st.session_state.step-1,5)))
    st.markdown('---'); st.caption('Synthetic case. Deterministic financial calculations. No transactions executed.')

try: ts=load_truth_set(uploaded if uploaded else DEFAULT)
except Exception as e: st.error(f'Workbook load error: {e}'); st.stop()

funding_actions={}
fc=calculate_forecast(ts); summaries=scenario_summary(fc,ts); checks=model_checks(ts,fc)

if page=='Inbox':
    hero('08:03 AM | Monday','The files arrived. The answer did not.','Six entities, three currencies, recent acquisitions, and one instruction from the CFO.')
    st.markdown('')
    st.markdown('<div class="alert"><b>CFO directive:</b> Keep every account positive and bring me any liquidity concerns before the 9:30 briefing.</div>',unsafe_allow_html=True)
    st.markdown('### Incoming treasury submissions')
    cards=[('BANK BALANCES','12 accounts','Duplicate, stale balance, unit anomaly'),('ENTITY FORECASTS','6 formats','Missing payroll, stale assumptions'),('RECEIVABLES','8 items','Receipt timing and duplicate risk'),('DISBURSEMENTS','11 items','Duplicate payroll and sign error'),('FACILITIES','4 sources','Availability and borrower constraints'),('FX RATES','3 currencies','Stale and inconsistent quotes')]
    cols=st.columns(3)
    for i,(k,n,d) in enumerate(cards): cols[i%3].markdown(f'<div class="card"><div class="eyebrow">{k}</div><h3>{n}</h3><p>{d}</p></div>',unsafe_allow_html=True)
    st.markdown('')
    c1,c2,c3,c4=st.columns(4); c1.metric('Reported cash','$6.16M'); c2.metric('Restricted cash','$499K'); c3.metric('Known issues',len(ts.treatments)); c4.metric('Time to briefing','87 min')
    st.markdown('<div class="card"><h3>The first question is not “How much cash do we have?”</h3><p>The first question is whether the submitted balances, forecasts, and funding sources are accurate, current, available, and decision-ready.</p></div>',unsafe_allow_html=True)
    if st.button('Begin treasury review →',type='primary',use_container_width=True): st.session_state.step=2; st.rerun()

elif page=='Exception Review':
    hero('STEP 1 | CONTROL THE INPUTS','Exception Review','Resolve the issues that can change the liquidity conclusion. Defer what still requires confirmation.')
    issues=ts.treatments.copy(); resolved=len(st.session_state.decisions); total=len(issues)
    c1,c2,c3,c4=st.columns(4); c1.metric('Resolved',f'{resolved}/{total}'); c2.metric('Human judgment',int(issues['Human Review Required?'].astype(str).eq('Y').sum())); c3.metric('Safe to automate',int(issues['Auto-Safe?'].astype(str).eq('Y').sum())); c4.metric('Control confidence',f'{55+int(40*resolved/max(total,1))}%')
    idx=min(resolved,total-1) if total else 0
    if total:
        r=issues.iloc[idx]; iid=str(r['Issue ID'])
        st.markdown(f'<div class="card"><div class="eyebrow">{r["Classification"]} | {iid}</div><h3>{r["Issue"]}</h3><p><b>Source:</b> {r["Source File"]}<br><b>Proposed treatment:</b> {r["Accepted Treatment"]}</p></div>',unsafe_allow_html=True)
        a,b,c=st.columns(3)
        if a.button('Accept treatment',type='primary',use_container_width=True): st.session_state.decisions[iid]='Accepted'; st.rerun()
        if b.button('Defer for confirmation',use_container_width=True): st.session_state.decisions[iid]='Deferred'; st.rerun()
        if c.button('Reject proposal',use_container_width=True): st.session_state.decisions[iid]='Rejected'; st.rerun()
        st.progress(resolved/max(total,1))
        with st.expander('View full issue register'):
            view=issues.copy(); view['Decision']=view['Issue ID'].astype(str).map(st.session_state.decisions).fillna('Pending'); st.dataframe(view,use_container_width=True,hide_index=True)
    if resolved>=min(4,total) and st.button('Continue to command center →',type='primary'): st.session_state.step=3; st.rerun()

elif page=='Command Center':
    hero('STEP 2 | CREATE VISIBILITY','Liquidity Command Center','Consolidated liquidity looks healthy. Entity-level liquidity tells a different story.')
    scenario=st.segmented_control('View scenario',['Reported','Downside','Stress'],default='Downside') or 'Downside'
    g=fc[fc.Scenario==scenario]; gulf=g[g['Entity ID']=='E004']; trough=gulf.loc[gulf['Ending Available (LCY)'].idxmin()]
    first=g[g.Date==g.Date.min()]
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('Available cash',money(first['Ending Available (USD)'].sum()))
    c2.metric('Restricted cash','$499K')
    c3.metric('Gulf trough',money(trough['Ending Available (LCY)']))
    c4.metric('Trough date',trough.Date.strftime('%b %d'))
    c5.metric('Status',trough.Status)
    st.markdown('<div class="danger"><b>Hidden exposure:</b> Consolidated liquidity remains positive while Gulf Components breaches policy and may become negative.</div>',unsafe_allow_html=True)
    left,right=st.columns([1.65,1])
    with left:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=gulf.Date,y=gulf['Ending Available (LCY)'],mode='lines+markers',line=dict(color=COLORS['teal'],width=4),marker=dict(size=8),name='Available cash',fill='tozeroy',fillcolor='rgba(0,166,166,.08)'))
        fig.add_trace(go.Scatter(x=gulf.Date,y=gulf['Policy Minimum (LCY)'],mode='lines',line=dict(color=COLORS['amber'],dash='dash',width=2),name='Policy minimum'))
        fig.add_hline(y=0,line_color=COLORS['red'],line_width=2); fig.add_annotation(x=trough.Date,y=trough['Ending Available (LCY)'],text=f'Trough: {money(trough["Ending Available (LCY)"])}',showarrow=True,arrowcolor=COLORS['red'])
        fig.update_layout(title='Gulf Components forecast',height=430,hovermode='x unified',paper_bgcolor='white',plot_bgcolor='white',legend_orientation='h',margin=dict(l=20,r=20,t=55,b=20),yaxis_tickprefix='$',yaxis_tickformat=',.0f')
        st.plotly_chart(fig,use_container_width=True)
    with right:
        ent=g.groupby(['Entity','Currency'],as_index=False).agg(Trough=('Ending Available (LCY)','min'),Minimum=('Policy Minimum (LCY)','first'))
        ent['Risk']=ent.apply(lambda x:'NEGATIVE' if x.Trough<0 else ('BELOW MINIMUM' if x.Trough<x.Minimum else 'OK'),axis=1)
        st.markdown('#### Entity risk map')
        for _,r in ent.iterrows(): st.markdown(f'<div class="card" style="margin-bottom:.45rem;border-left:5px solid {status_color(r.Risk)}"><b>{r.Entity}</b><br><span style="color:#627D98">Trough {money(r.Trough)} {r.Currency} | {r.Risk}</span></div>',unsafe_allow_html=True)
    if st.button('Open Scenario Laboratory →',type='primary'): st.session_state.step=4; st.rerun()

elif page=='Scenario Lab':
    hero('STEP 3 | TEST THE RESPONSE','Scenario Laboratory','Change the receipt timing, apply funding, and observe the liquidity consequence immediately.')
    row=ts.scenarios.set_index('Scenario').loc['Downside']
    c1,c2,c3=st.columns(3)
    receipt_date=c1.date_input('Orion receipt date',pd.Timestamp(row['Orion Receipt Date']).date())
    shock=c2.number_input('Additional unplanned payment',0.0,500000.0,float(row['Unplanned Gulf Payment Amount']),10000.0)
    funding=c3.number_input('Approved funding action',0.0,1000000.0,float(st.session_state.funding),50000.0)
    st.session_state.funding=funding
    overrides={'Custom':{}}; temp=ts.scenarios.copy(); temp.loc[temp.Scenario=='Downside','Scenario']='Custom'; temp.loc[temp.Scenario=='Custom','Orion Receipt Date']=pd.Timestamp(receipt_date); temp.loc[temp.Scenario=='Custom','Unplanned Gulf Payment Date']=pd.Timestamp('2026-09-04') if shock>0 else pd.NaT; temp.loc[temp.Scenario=='Custom','Unplanned Gulf Payment Amount']=shock
    old=ts.scenarios; ts.scenarios=temp
    base_fc=calculate_forecast(ts)
    gulf0=base_fc[(base_fc.Scenario=='Custom')&(base_fc['Entity ID']=='E004')]
    trough0=gulf0.loc[gulf0['Ending Available (LCY)'].idxmin()]
    if funding>0:
        fund_date=trough0.Date; actions={f'Custom|E004|{fund_date.date().isoformat()}':funding}; custom_fc=calculate_forecast(ts,funding_actions=actions)
    else: custom_fc=base_fc
    ts.scenarios=old; gulf=custom_fc[(custom_fc.Scenario=='Custom')&(custom_fc['Entity ID']=='E004')]; trough=gulf.loc[gulf['Ending Available (LCY)'].idxmin()]
    a,b,c,d=st.columns(4); a.metric('Liquidity trough',money(trough['Ending Available (LCY)'])); b.metric('Policy shortfall',money(min(0,trough['Surplus / (Shortfall)']))); c.metric('Local line available','$50,000'); d.metric('Remaining negative exposure',money(max(0,-trough['Ending Available (LCY)'])))
    fig=go.Figure(); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf['Ending Available (LCY)'],mode='lines+markers',line=dict(color=COLORS['blue'],width=4),name='Cash after action')); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf['Policy Minimum (LCY)'],mode='lines',line=dict(color=COLORS['amber'],dash='dash'),name='Policy minimum')); fig.add_hline(y=0,line_color=COLORS['red'],line_width=2); fig.update_layout(height=430,hovermode='x unified',paper_bgcolor='white',plot_bgcolor='white',legend_orientation='h',yaxis_tickprefix='$',yaxis_tickformat=',.0f'); st.plotly_chart(fig,use_container_width=True)
    st.markdown('#### Response choices')
    x,y,z=st.columns(3)
    if x.button('Use $50K local line',use_container_width=True): st.session_state.funding=50000; st.rerun()
    if y.button('Request $500K intercompany transfer',use_container_width=True): st.session_state.funding=500000; st.rerun()
    if z.button('Reset response',use_container_width=True): st.session_state.funding=0; st.rerun()
    if st.button('Prepare CFO briefing →',type='primary'): st.session_state.step=5; st.rerun()

elif page=='CFO Briefing':
    hero('STEP 4 | COMMUNICATE THE DECISION','9:30 CFO Briefing','A concise decision memo grounded in reviewed inputs and deterministic calculations.')
    scenario=st.selectbox('Briefing basis',['Reported','Downside','Stress'],index=1); s=summaries.set_index('Scenario').loc[scenario]; trough=pd.Timestamp(s['Trough Date']).strftime('%A, %B %d')
    st.markdown(f'''<div class="card"><div class="eyebrow">EXECUTIVE DECISION BRIEF</div><h3>Gulf Components liquidity exposure</h3><p><b>Situation.</b> Consolidated liquidity remains positive, but Gulf Components reaches {money(s['Lowest Cash'])} on {trough} under the {scenario} scenario, against a $200,000 operating minimum.</p><br><p><b>Primary driver.</b> The timing of the $620,000 Orion Automotive receipt determines whether the issue remains a policy breach or becomes a negative-balance event.</p><br><p><b>Available response.</b> Reconciled local-line capacity is {money(s['Local Facility Available'])}. Other available liquidity is subject to borrower, transfer, timing, and approval constraints.</p><br><p><b>Decision required.</b> Confirm the Orion receipt date and authorize treasury to arrange sufficient funding before the projected trough.</p></div>''',unsafe_allow_html=True)
    st.markdown('### Before review vs. after review')
    compare=pd.DataFrame({'Before treasury review':['Positive consolidated cash','$100,000 reported local availability','Orion receipt assumed on September 2','Restricted cash included','No explicit decision request'],'After treasury review':['Entity-level exposure identified','$50,000 reconciled local availability','Receipt timing treated as a scenario','Restricted cash excluded','Funding decision and approval identified']})
    st.dataframe(compare,use_container_width=True,hide_index=True)
    text=f'''CFO LIQUIDITY BRIEFING\nScenario: {scenario}\nGulf Components trough: {money(s['Lowest Cash'])} on {trough}.\nPolicy minimum: $200,000.\nPrimary driver: timing of the $620,000 Orion Automotive receipt.\nReconciled local-line availability: {money(s['Local Facility Available'])}.\nDecision: confirm receipt timing and authorize sufficient funding before the trough.\nControl: reviewed inputs and deterministic calculations; no transaction execution.\n'''
    st.download_button('Download CFO briefing',text,file_name=f'CFO_Briefing_{scenario}.txt',type='primary')

else:
    hero('CONTROL LAYER','Model Controls','Transparent checks separating financial calculation from AI-assisted interpretation.')
    passed=int(checks.Pass.sum()); total=len(checks); a,b,c=st.columns(3); a.metric('Checks passed',f'{passed}/{total}'); b.metric('Calculation method','Deterministic'); c.metric('Transactions executed','None')
    st.dataframe(checks,use_container_width=True,hide_index=True)
    with st.expander('Approved FX rates'): st.dataframe(ts.fx,use_container_width=True,hide_index=True)
    with st.expander('Liquidity facilities'): st.dataframe(ts.facilities,use_container_width=True,hide_index=True)
    if st.button('Reset presentation'): st.session_state.clear(); st.rerun()
