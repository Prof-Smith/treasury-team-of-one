from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import DATES,MINIMUM,STORMS,simulate,response_comparison

st.set_page_config(page_title='Treasury Agent Operations',page_icon='◈',layout='wide')
C={'navy':'#081F33','blue':'#16658A','cyan':'#00BAC6','amber':'#F4AB00','red':'#D63F42','green':'#15836D','ink':'#1F3547','muted':'#64798A','bg':'#EDF3F7'}
st.markdown(f'''<style>
.stApp{{background:{C['bg']}}}.block-container{{padding:1rem 1.6rem 2.5rem;max-width:1540px}}[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] *{{color:#F1F7FA!important}}
.hero{{background:radial-gradient(circle at 87% 5%,rgba(0,186,198,.28),transparent 32%),linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:20px;padding:1.25rem 1.5rem;box-shadow:0 14px 36px rgba(8,31,51,.18)}}.hero h1{{font-size:2.12rem;margin:.2rem 0}}.hero p{{color:#D8E8EF;margin:0}}.eyebrow{{font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;color:#43E6ED;font-weight:800}}
.panel{{background:white;border:1px solid #D5E1E8;border-radius:16px;padding:1rem 1.1rem;box-shadow:0 5px 16px rgba(8,31,51,.07)}}.panel h3{{font-size:1rem;margin:.05rem 0 .55rem}}.muted{{color:#64798A;font-size:.86rem}}.row{{display:flex;align-items:center;gap:.6rem;border-bottom:1px solid #E8EEF2;padding:.56rem 0}}.grow{{flex:1}}.badge{{border-radius:999px;padding:.14rem .48rem;background:#DFF7F7;color:#087680;font-size:.68rem;font-weight:800}}.warn{{background:#FFF7E3;border-left:5px solid #F4AB00;padding:.78rem 1rem;border-radius:11px}}.danger{{background:#FFF0F0;border-left:5px solid #D63F42;padding:.78rem 1rem;border-radius:11px}}.success{{background:#EAF8F4;border-left:5px solid #15836D;padding:.78rem 1rem;border-radius:11px}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:15px;padding:.68rem .9rem;box-shadow:0 4px 12px rgba(8,31,51,.05)}}div[data-testid="stMetricValue"]{{font-size:1.5rem}}.stButton>button{{border-radius:11px;font-weight:800;min-height:44px}}
</style>''',unsafe_allow_html=True)
for k,v in {'step':0,'agent_run':False,'reviewed':0,'storm':-1,'funding':0}.items(): st.session_state.setdefault(k,v)
def hero(k,t,s): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)
def money(v): return f'${abs(v)/1e6:,.2f}M' if abs(v)>=1e6 else f'${abs(v):,.0f}'
def fan(result,title):
    fig=go.Figure(); fig.add_trace(go.Scatter(x=DATES,y=result['p975'],line=dict(width=0),showlegend=False,hoverinfo='skip')); fig.add_trace(go.Scatter(x=DATES,y=result['p025'],fill='tonexty',fillcolor='rgba(0,186,198,.12)',line=dict(width=0),name='95% range')); fig.add_trace(go.Scatter(x=DATES,y=result['p75'],line=dict(width=0),showlegend=False,hoverinfo='skip')); fig.add_trace(go.Scatter(x=DATES,y=result['p25'],fill='tonexty',fillcolor='rgba(0,186,198,.25)',line=dict(width=0),name='50% range')); fig.add_trace(go.Scatter(x=DATES,y=result['expected'],mode='lines+markers',line=dict(color=C['cyan'],width=4),name='Expected cash')); fig.add_hline(y=MINIMUM,line_color=C['amber'],line_dash='dash',annotation_text='$200K policy minimum'); fig.add_hline(y=0,line_color=C['red'],line_width=2,annotation_text='Zero cash'); fig.update_layout(title=title,height=445,paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',legend_orientation='h',margin=dict(l=25,r=20,t=50,b=20),yaxis_tickprefix='$',yaxis_tickformat=',.0f'); return fig
with st.sidebar:
    st.markdown('## ◈ Treasury Agent Operations'); st.caption('From inbox evidence to liquidity decision')
    pages=['Friday Risk Snapshot','Treasury Inbox','Agent Operations','Human Control Gate','The Storm','Liquidity Dilemma','Response Studio','CFO Decision Brief','Audit Trail']; page=st.radio('Narrative',pages,index=st.session_state.step)
    st.markdown('---'); st.caption('All messages and data are synthetic. Simulations use a fixed seed for reproducibility.')
if page=='Friday Risk Snapshot':
    hero('T−1 | FRIDAY 4:30 PM','Prepared for 95% of expected outcomes','Historical forecast variances define the starting liquidity distribution before Monday evidence arrives.')
    r=simulate(-1); a,b,c,d=st.columns(4); a.metric('Cash-Flow VaR | 95%',money(r['var95'])); b.metric('Cash-Flow CVaR | 95%',money(r['cvar95'])); c.metric('P(Below Minimum)',f"{r['prob_below_min']:.1%}"); d.metric('P(Negative)',f"{r['prob_negative']:.1%}")
    st.plotly_chart(fan(r,'Friday forecast: 50% and 95% simulated cash ranges'),use_container_width=True)
    st.markdown('<div class="success"><b>Friday assessment:</b> downside risk is visible but remains within the anticipated response capacity. VaR marks the 95% adverse-variance threshold; CVaR measures average severity beyond that threshold.</div>',unsafe_allow_html=True)
    if st.button('Advance to Monday morning →',type='primary',use_container_width=True): st.session_state.step=1; st.rerun()
elif page=='Treasury Inbox':
    hero('T0 | MONDAY 8:03 AM','Eight messages. Ten attachments. No common format.','The CFO briefing begins at 9:30. New evidence requires a full forecast refresh.')
    inbox=json.loads((Path(__file__).parent/'data'/'inbox.json').read_text())
    l,r=st.columns([1.3,1],gap='large')
    with l:
        for m in inbox:
            st.markdown(f'<div class="panel" style="margin-bottom:.55rem"><div class="row"><span class="badge">{m["time"]}</span><b>{m["subject"]}</b><span class="grow"></span><span>{len(m["attachments"])} file(s)</span></div><div class="muted">{m["sender"]} | {m["entity"]}</div><p>{m["body"]}</p><div class="muted">Attachments: {", ".join(m["attachments"])}</div></div>',unsafe_allow_html=True)
    with r:
        st.markdown('<div class="panel"><div class="eyebrow">INTAKE STATUS</div><h3>Agent-ready evidence</h3><div class="row"><span>Messages found</span><span class="grow"></span><b>8</b></div><div class="row"><span>Attachments identified</span><span class="grow"></span><b>10</b></div><div class="row"><span>Entities represented</span><span class="grow"></span><b>6</b></div><div class="row"><span>Revised versions</span><span class="grow"></span><b>2</b></div><div class="row"><span>Common schema</span><span class="grow"></span><b style="color:#D63F42">None</b></div></div>',unsafe_allow_html=True)
        st.markdown('<br><div class="warn"><b>Human context matters:</b> several email bodies contain instructions that are not present in the attached spreadsheets.</div>',unsafe_allow_html=True)
    if st.button('Deploy agent team →',type='primary',use_container_width=True): st.session_state.agent_run=True; st.session_state.step=2; st.rerun()
elif page=='Agent Operations':
    hero('AGENT RUN 07-A','The agents build the evidence pipeline','Mailbox context, files, and policy controls are converted into a proposed treasury truth set.')
    agents=[('Inbox Agent','8 messages linked to 10 attachments','Complete'),('Document Intelligence Agent','Sheets, headers, dates, notes, and currencies parsed','Complete'),('Schema Mapping Agent','27 fields mapped; 5 low-confidence mappings','Complete'),('Reconciliation Agent','6 material exceptions surfaced','Complete'),('Forecast Risk Agent','Friday simulation queued for refresh','Waiting on review')]
    for name,detail,status in agents:
        col=C['green'] if status=='Complete' else C['amber']; st.markdown(f'<div class="panel" style="margin-bottom:.55rem"><div class="row"><span style="width:12px;height:12px;border-radius:50%;background:{col}"></span><b>{name}</b><span class="grow"></span><span class="badge">{status}</span></div><div class="muted">{detail}</div></div>',unsafe_allow_html=True)
    st.markdown('### Live parsing trace')
    st.code('''08:04:09  Inbox Agent      Linked “use corrected version” to Gulf_Cash_Fcst_v2.xlsx
08:04:12  Document Agent   Detected dates across columns in Mfg_Weekly_View.xlsx
08:04:13  Document Agent   Extracted note: “Payroll handled centrally; excluded”
08:04:18  Mapping Agent    “Interco Revenue” → proposed Intercompany Funding [78%]
08:04:21  Reconciliation   Duplicate account candidate; possible $2.45M overstatement
08:04:27  Risk Agent       Forecast refresh paused pending material decisions''')
    if st.button('Open human control gate →',type='primary'): st.session_state.step=3; st.rerun()
elif page=='Human Control Gate':
    hero('HUMAN-IN-THE-LOOP','Approve the judgments that can change the answer','Agents propose. Treasury validates material corrections and owns the decision.')
    issues=[('Duplicate Holdings balance','$2.45M','Retain one record and quarantine duplicate'),('European reserve unit anomaly','Material','Interpret as €425K only after review; exclude from available cash'),('Orion receipt timing','$620K','Convert fixed date into a probability distribution'),('Duplicate Gulf payroll','$245K','Retain one verified payroll payment'),('Facility availability','$50K','Use commitment less drawn: $50K, not $100K'),('FX quote inconsistencies','Review','Use approved treasury-feed rates only')]
    idx=min(st.session_state.reviewed,len(issues)-1); issue,impact,treatment=issues[idx]
    st.markdown(f'<div class="panel"><div class="eyebrow">MATERIAL REVIEW {idx+1} OF {len(issues)}</div><h3>{issue}</h3><p><b>Financial relevance:</b> {impact}</p><p><b>Agent recommendation:</b> {treatment}</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    if a.button('Accept recommendation',type='primary',use_container_width=True): st.session_state.reviewed=min(len(issues),st.session_state.reviewed+1); st.rerun()
    if b.button('Defer for confirmation',use_container_width=True): st.session_state.reviewed=min(len(issues),st.session_state.reviewed+1); st.rerun()
    if c.button('Inspect source evidence',use_container_width=True): st.info('Source evidence retained: email context, attachment name, raw value, proposed value, confidence, and materiality.')
    st.progress(st.session_state.reviewed/len(issues))
    if st.session_state.reviewed>=4 and st.button('Release approved truth set to Risk Agent →',type='primary'): st.session_state.step=4; st.session_state.storm=0; st.rerun()
elif page=='The Storm':
    stage=max(0,st.session_state.storm); s=STORMS[stage]; r=simulate(stage)
    hero(f'STORM EVENT {stage+1} OF {len(STORMS)}',s['name'],s['effect'])
    a,b,c,d=st.columns(4); a.metric('VaR | 95%',money(r['var95'])); b.metric('CVaR | 95%',money(r['cvar95'])); c.metric('P(Below Minimum)',f"{r['prob_below_min']:.1%}"); d.metric('P(Negative)',f"{r['prob_negative']:.1%}")
    st.plotly_chart(fan(r,f'Revised distribution after: {s["name"]}'),use_container_width=True)
    st.markdown(f'<div class="danger"><b>Risk update:</b> the distribution has shifted as new evidence changed the assumptions supporting Friday’s 95% confidence statement.</div>',unsafe_allow_html=True)
    if stage<len(STORMS)-1:
        if st.button('Release next storm event →',type='primary',use_container_width=True): st.session_state.storm+=1; st.rerun()
    elif st.button('Freeze the forecast and reveal the dilemma →',type='primary',use_container_width=True): st.session_state.step=5; st.rerun()
elif page=='Liquidity Dilemma':
    hero('DECISION POINT','The company has cash. Gulf Components may not.','The local safety net is smaller than reported, and cash elsewhere is not automatically accessible.')
    r=simulate(4); a,b,c,d=st.columns(4); a.metric('Cash-Flow VaR | 95%',money(r['var95'])); b.metric('Cash-Flow CVaR | 95%',money(r['cvar95'])); c.metric('Local line','$50,000'); d.metric('P(Negative)',f"{r['prob_negative']:.1%}")
    st.markdown('<div class="danger"><b>Dilemma:</b> rely on the Orion receipt, draw the local line, request intercompany funding, or layer the response?</div>',unsafe_allow_html=True)
    st.plotly_chart(fan(r,'Final pre-response liquidity distribution'),use_container_width=True)
    if st.button('Evaluate response alternatives →',type='primary'): st.session_state.step=6; st.rerun()
elif page=='Response Studio':
    hero('RESPONSE STUDIO','Manage the tail, not just the expected case','Each response reruns the full simulation and updates VaR, CVaR, breach probability, and negative-cash probability.')
    options={'No action':0,'Local line':50_000,'Intercompany transfer':500_000,'Layered response':550_000}; choice=st.segmented_control('Treasury response',list(options),default='No action') or 'No action'; funding=options[choice]; r=simulate(4,funding=funding)
    a,b,c,d=st.columns(4); a.metric('Funding action',money(funding)); b.metric('VaR | 95%',money(r['var95'])); c.metric('CVaR | 95%',money(r['cvar95'])); d.metric('P(Negative)',f"{r['prob_negative']:.1%}")
    st.plotly_chart(fan(r,f'Post-response distribution: {choice}'),use_container_width=True)
    comp=response_comparison(); st.dataframe(comp,use_container_width=True,hide_index=True,column_config={'Funding':st.column_config.NumberColumn(format='$%0.0f'),'VaR 95%':st.column_config.NumberColumn(format='$%0.0f'),'CVaR 95%':st.column_config.NumberColumn(format='$%0.0f'),'P(Below Minimum)':st.column_config.ProgressColumn(format='percent',min_value=0,max_value=1),'P(Negative)':st.column_config.ProgressColumn(format='percent',min_value=0,max_value=1),'Expected Trough':st.column_config.NumberColumn(format='$%0.0f')})
    st.session_state.funding=funding
    if st.button('Generate CFO decision brief →',type='primary'): st.session_state.step=7; st.rerun()
elif page=='CFO Decision Brief':
    funding=st.session_state.funding; r=simulate(4,funding=funding); response='Layered response' if funding>=550000 else 'Intercompany transfer' if funding>=500000 else 'Local line' if funding else 'No action'
    hero('9:30 AM | DECISION BRIEF','From inbox evidence to a governed liquidity response','Agents accelerated retrieval, parsing, reconciliation, and simulation. Treasury retained judgment and accountability.')
    st.markdown(f'''<div class="panel"><div class="eyebrow">EXECUTIVE DECISION BRIEF</div><h3>Gulf Components liquidity exposure</h3><p><b>Situation.</b> Monday evidence invalidated assumptions underlying Friday’s forecast. The refreshed ten-day simulation shows a {r['prob_negative']:.1%} probability of negative cash and a 95% expected tail shortfall of {money(r['cvar95'])}.</p><p><b>Primary driver.</b> The $620,000 Orion receipt is timing-dependent while payroll and supplier payments occur earlier in the horizon.</p><p><b>Constraint.</b> Reconciled local-line availability is $50,000. Restricted and parent liquidity require separate authority before use.</p><p><b>Selected response.</b> {response}, totaling {money(funding)}.</p><p><b>Decision requested.</b> Confirm receipt timing and approve the selected funding response before the projected liquidity trough.</p></div>''',unsafe_allow_html=True)
    brief=f'''CFO DECISION BRIEF\nConfidence level: 95%\nHorizon: 10 days\nCash-Flow VaR: {money(r['var95'])}\nCash-Flow CVaR / Expected Tail Shortfall: {money(r['cvar95'])}\nProbability below policy minimum: {r['prob_below_min']:.1%}\nProbability negative: {r['prob_negative']:.1%}\nSelected response: {response}, {money(funding)}\nDecision requested: confirm Orion receipt timing and approve funding before the trough.\n'''; st.download_button('Download CFO decision brief',brief,file_name='CFO_Decision_Brief.txt',type='primary')
    if st.button('View audit trail →'): st.session_state.step=8; st.rerun()
else:
    hero('AUDIT TRAIL','Every transformation has an owner','Source context, agent proposals, human decisions, model version, assumptions, and outputs remain traceable.')
    audit=pd.DataFrame([['08:03','Inbox Agent','Linked 8 messages to 10 attachments','Automated'],['08:04','Document Agent','Parsed structures and spreadsheet notes','Automated'],['08:05','Mapping Agent','Proposed 27 canonical mappings','Human review for low confidence'],['08:06','Reconciliation Agent','Surfaced 6 material exceptions','Human approval'],['08:09','Forecast Risk Agent','Reran 5,000 historical-bootstrap paths','Deterministic seed 77'],['08:12','Treasury analyst','Approved truth set and stress assumptions','Accountable owner'],['08:18','Scenario Agent','Compared four funding responses','Decision support'],['09:25','Communications Agent','Drafted CFO decision brief','Treasury approval required']],columns=['Time','Actor','Action','Control'])
    st.dataframe(audit,use_container_width=True,hide_index=True)
    if st.button('Reset complete demonstration'): st.session_state.clear(); st.rerun()
