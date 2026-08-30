from pathlib import Path
import json,io,zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import *

st.set_page_config(page_title='Treasury Agent Operations',page_icon='◈',layout='wide')
BASE=Path(__file__).parent; SAMPLE=BASE/'data'/'historical_forecast_errors.csv'; INBOX=BASE/'data'/'monday_inbox'
C={'navy':'#081F33','cyan':'#00BAC6','amber':'#F4AB00','red':'#D63F42','green':'#15836D','bg':'#EDF3F7','ink':'#1F3547'}
st.markdown(f'''<style>
.stApp{{background:{C['bg']}}}.block-container{{padding:.55rem 1.15rem 1rem;max-width:1550px}}[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] *{{color:#F1F7FA!important}}header[data-testid="stHeader"]{{height:2rem}}
.hero{{background:linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:15px;padding:.7rem 1rem;margin-bottom:.45rem}}.hero h1{{font-size:1.58rem;margin:.08rem 0}}.hero p{{font-size:.86rem;color:#D8E8EF;margin:0}}.eyebrow{{font-size:.62rem;letter-spacing:.12em;color:#43E6ED;font-weight:800}}
.panel{{background:white;border:1px solid #D5E1E8;border-radius:13px;padding:.72rem .85rem;box-shadow:0 3px 10px rgba(8,31,51,.06)}}.row{{display:flex;gap:.5rem;align-items:center;border-bottom:1px solid #E7EEF2;padding:.36rem 0;font-size:.84rem}}.grow{{flex:1}}.muted{{font-size:.75rem;color:#687C8E}}.badge{{font-size:.64rem;font-weight:800;border-radius:999px;padding:.12rem .4rem;background:#DFF7F7;color:#087680}}.warn{{background:#FFF7E3;border-left:4px solid #F4AB00;padding:.5rem .7rem;border-radius:9px;font-size:.82rem}}.danger{{background:#FFF0F0;border-left:4px solid #D63F42;padding:.5rem .7rem;border-radius:9px;font-size:.82rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.4rem .65rem}}div[data-testid="stMetricLabel"]{{font-size:.72rem}}div[data-testid="stMetricValue"]{{font-size:1.25rem}}.stButton>button{{min-height:35px;border-radius:9px;font-weight:800}}h3{{margin:.3rem 0!important;font-size:1.05rem!important}}
</style>''',unsafe_allow_html=True)
for k,v in {'page':0,'hist':None,'storm':0,'reviewed':0,'funding':0}.items(): st.session_state.setdefault(k,v)
def hero(k,t,s): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)
def money(v): return f'${abs(v)/1e6:.2f}M' if abs(v)>=1e6 else f'${abs(v):,.0f}'
def fan(r,title,prior=None):
 fig=go.Figure(); fig.add_trace(go.Scatter(x=DATES,y=r['p975'],line_width=0,showlegend=False,hoverinfo='skip')); fig.add_trace(go.Scatter(x=DATES,y=r['p025'],fill='tonexty',fillcolor='rgba(0,186,198,.11)',line_width=0,name='95% range')); fig.add_trace(go.Scatter(x=DATES,y=r['p75'],line_width=0,showlegend=False,hoverinfo='skip')); fig.add_trace(go.Scatter(x=DATES,y=r['p25'],fill='tonexty',fillcolor='rgba(0,186,198,.24)',line_width=0,name='50% range')); fig.add_trace(go.Scatter(x=DATES,y=r['mean'],line=dict(color=C['cyan'],width=4),mode='lines+markers',name='Current expected'))
 if prior is not None: fig.add_trace(go.Scatter(x=DATES,y=prior['mean'],line=dict(color='#7D8D99',dash='dot',width=2),name='Friday expected'))
 fig.add_hline(y=MINIMUM,line_color=C['amber'],line_dash='dash'); fig.add_hline(y=0,line_color=C['red'],line_width=2); fig.update_layout(title=title,height=340,paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',legend_orientation='h',margin=dict(l=18,r=12,t=40,b=12),yaxis_tickprefix='$',yaxis_tickformat=',.0f'); return fig
pages=['Historical Baseline','Friday Snapshot','Monday Inbox','Agent Operations','Human Review','The Storm','Dilemma','Response Studio','CFO Brief','Audit & Downloads']
with st.sidebar:
 st.markdown('## ◈ Treasury Agent Operations'); st.caption('GitHub data loads automatically. Monday agents take over.')
 page=st.radio('Narrative',pages,index=st.session_state.page)
 st.markdown('---'); st.caption('Synthetic evidence. Reproducible simulation. No transaction execution.')
if page=='Historical Baseline':
 if st.session_state.hist is None: st.session_state.hist=load_history(SAMPLE)
 h=st.session_state.hist
 hero('T−2 | BEFORE MONDAY','Historical forecast performance loaded','The Risk Agent automatically reads the historical forecast-error file stored with the GitHub application. No manual upload is required.')
 left,right=st.columns([1.55,1],gap='large')
 with left:
  st.markdown('<div class="panel"><div class="eyebrow">AUTOMATIC DATA SOURCE</div><h3>data/historical_forecast_errors.csv</h3><p>The file is versioned with the application in GitHub and loaded when Streamlit starts.</p><div class="row"><span>Load status</span><span class="grow"></span><b style="color:#15836D">READY</b></div><div class="row"><span>Minimum observations</span><span class="grow"></span><b>60</b></div><div class="row"><span>Current observations</span><span class="grow"></span><b>'+str(len(h))+'</b></div></div>',unsafe_allow_html=True)
 with right:
  st.markdown('<div class="panel"><div class="eyebrow">FIELDS DETECTED</div><div class="row"><b>date</b><span class="grow"></span><span>observation date</span></div><div class="row"><b>opening_error</b><span class="grow"></span><span>opening variance</span></div><div class="row"><b>receipt_error</b><span class="grow"></span><span>receipt variance</span></div><div class="row"><b>disbursement_error</b><span class="grow"></span><span>payment variance</span></div></div>',unsafe_allow_html=True)
 a,b,c=st.columns(3); a.metric('Observations',len(h)); b.metric('Beginning',h.date.min().strftime('%b %Y')); c.metric('Ending',h.date.max().strftime('%b %Y'))
 if st.button('Build Friday risk baseline →',type='primary',use_container_width=True): st.session_state.page=1; st.rerun()
else:
 if st.session_state.hist is None: st.session_state.hist=load_history(SAMPLE)
 hist=st.session_state.hist; friday=simulate(hist,-1)
 if page=='Friday Snapshot':
  hero('T−1 | FRIDAY 4:30 PM','A manageable 95% risk baseline','Historical variance is translated into a ten-day probabilistic cash forecast before Monday evidence arrives.')
  left,right=st.columns([2.25,1],gap='large')
  with left: st.plotly_chart(fan(friday,'Friday cash distribution'),use_container_width=True)
  with right:
   a,b=st.columns(2); a.metric('VaR 95%',money(friday['var'])); b.metric('CVaR 95%',money(friday['cvar'])); c,d=st.columns(2); c.metric('P(Below Min)',f"{friday['pmin']:.1%}"); d.metric('P(Negative)',f"{friday['pneg']:.1%}")
   st.markdown('<div class="panel"><div class="eyebrow">RISK STATEMENT</div><p style="font-size:.82rem">At 95% confidence over ten days, modeled adverse cash variance is bounded by VaR. CVaR describes average severity in the worst 5% of outcomes.</p></div>',unsafe_allow_html=True)
   if st.button('Open Monday inbox →',type='primary',use_container_width=True): st.session_state.page=2; st.rerun()
 elif page=='Monday Inbox':
  hero('T0 | MONDAY 8:03 AM','The agents retrieve current evidence','No second upload. The simulated Inbox Agent pulls messages and attachments from the staged treasury mailbox.')
  inbox=json.loads((BASE/'data'/'inbox.json').read_text()); l,r=st.columns([1.65,1],gap='large')
  with l:
   for m in inbox:
    st.markdown(f'<div class="panel" style="margin-bottom:.3rem"><div class="row"><span class="badge">{m["time"]}</span><b>{m["subject"]}</b><span class="grow"></span><span>{len(m["attachments"])} file</span></div><div class="muted">{m["sender"]} | {m["entity"]} | {", ".join(m["attachments"])}</div></div>',unsafe_allow_html=True)
  with r:
   st.markdown('<div class="panel"><div class="eyebrow">MAILBOX SCAN</div><div class="row"><span>Messages</span><span class="grow"></span><b>8</b></div><div class="row"><span>Attachments</span><span class="grow"></span><b>10</b></div><div class="row"><span>Entities</span><span class="grow"></span><b>6</b></div><div class="row"><span>Revisions</span><span class="grow"></span><b>2</b></div><div class="row"><span>Common format</span><span class="grow"></span><b style="color:#D63F42">None</b></div></div>',unsafe_allow_html=True)
   if st.button('Authorize agent retrieval →',type='primary',use_container_width=True): st.session_state.page=3; st.rerun()
 elif page=='Agent Operations':
  hero('AGENT RUN 08-A','Watch current files become decision-ready data','The app profiles actual bundled attachments, maps fields, reconciles controls, and prepares the forecast refresh.')
  prof=process_inbox(INBOX); a,b,c,d=st.columns(4); a.metric('Files parsed',len(prof)); b.metric('Rows read',int(prof.rows.sum())); c.metric('Sheets opened',int(prof.sheets.sum())); d.metric('Warnings',6)
  l,r=st.columns([1.4,1],gap='large')
  with l: st.dataframe(prof[['file','type','sheets','rows','columns']],use_container_width=True,hide_index=True,height=255)
  with r:
   agents=[('Inbox Agent','Complete'),('Document Agent','Complete'),('Mapping Agent','Complete'),('Reconciliation Agent','6 reviews'),('Risk Agent','Waiting')]
   html='<div class="panel">'
   for n,s in agents: html+=f'<div class="row"><span>{n}</span><span class="grow"></span><span class="badge">{s}</span></div>'
   html+='</div>'; st.markdown(html,unsafe_allow_html=True)
   st.code('''7:26  Revised Gulf file selected\n7:27  Horizontal date layout parsed\n7:27  Note extracted: payroll excluded\n7:28  Duplicate balance: $2.45M impact\n7:28  Risk refresh paused for review''')
   if st.button('Open human review →',type='primary',use_container_width=True): st.session_state.page=4; st.rerun()
 elif page=='Human Review':
  hero('HUMAN CONTROL GATE','Agents propose. Treasury decides.','Approve only the material treatments needed to release the current forecast.')
  issues=[('Duplicate Holdings balance','$2.45M','Retain one record'),('Reserve unit anomaly','Material','Correct to €425K; exclude as restricted'),('Orion timing','$620K','Model settlement as a distribution'),('Duplicate payroll','$245K','Retain one verified payment'),('Facility mismatch','$50K','Recalculate commitment less drawn'),('FX inconsistencies','Review','Use approved feed')]
  i=min(st.session_state.reviewed,5); x=issues[i]; st.markdown(f'<div class="panel"><div class="eyebrow">REVIEW {i+1} OF 6</div><h3>{x[0]}</h3><p><b>Impact:</b> {x[1]} &nbsp; | &nbsp; <b>Agent proposal:</b> {x[2]}</p></div>',unsafe_allow_html=True)
  a,b,c=st.columns(3)
  if a.button('Accept',type='primary',use_container_width=True): st.session_state.reviewed=min(6,st.session_state.reviewed+1); st.rerun()
  if b.button('Defer',use_container_width=True): st.session_state.reviewed=min(6,st.session_state.reviewed+1); st.rerun()
  if c.button('Inspect evidence',use_container_width=True): st.info('Raw message, attachment, value, mapping confidence, and proposed treatment are retained in the audit trail.')
  st.progress(st.session_state.reviewed/6)
  if st.session_state.reviewed>=4 and st.button('Release current data to Risk Agent →',type='primary',use_container_width=True): st.session_state.page=5; st.session_state.storm=0; st.rerun()
 elif page=='The Storm':
  stage=st.session_state.storm; name,*_=STORMS[stage]; r=simulate(hist,stage)
  hero(f'STORM {stage+1} OF 5',name,'New evidence revises the assumptions behind Friday’s 95% forecast.')
  left,right=st.columns([2.25,1],gap='large')
  with left: st.plotly_chart(fan(r,'Friday baseline vs. current risk',friday),use_container_width=True)
  with right:
   st.markdown('<div class="panel"><div class="eyebrow">FRIDAY → CURRENT</div>'); a,b=st.columns(2); a.metric('VaR 95%',money(r['var']),delta=money(r['var']-friday['var'])); b.metric('CVaR 95%',money(r['cvar']),delta=money(r['cvar']-friday['cvar'])); c,d=st.columns(2); c.metric('P(Below)',f"{r['pmin']:.1%}",delta=f"{r['pmin']-friday['pmin']:.1%}"); d.metric('P(Negative)',f"{r['pneg']:.1%}",delta=f"{r['pneg']-friday['pneg']:.1%}")
   st.markdown('</div>',unsafe_allow_html=True)
   if stage<4:
    if st.button('Release next event →',type='primary',use_container_width=True): st.session_state.storm+=1; st.rerun()
   elif st.button('Reveal liquidity dilemma →',type='primary',use_container_width=True): st.session_state.page=6; st.rerun()
 elif page=='Dilemma':
  r=simulate(hist,4); hero('DECISION POINT','Risk now exceeds immediately available local capacity','The company has cash, but entity, restriction, timing, and approval constraints prevent frictionless access.')
  left,right=st.columns([2.2,1],gap='large');
  with left: st.plotly_chart(fan(r,'Pre-response liquidity distribution',friday),use_container_width=True)
  with right:
   a,b=st.columns(2); a.metric('VaR 95%',money(r['var'])); b.metric('CVaR 95%',money(r['cvar'])); c,d=st.columns(2); c.metric('Local line','$50K'); d.metric('P(Negative)',f"{r['pneg']:.1%}")
   st.markdown('<div class="danger"><b>Dilemma:</b> rely on the receipt, use the local line, request an intercompany transfer, or layer the response?</div>',unsafe_allow_html=True)
   if st.button('Compare responses →',type='primary',use_container_width=True): st.session_state.page=7; st.rerun()
 elif page=='Response Studio':
  hero('RESPONSE STUDIO','Manage the tail, not only the expected path','Every response reruns the simulation and updates the risk profile.')
  opts={'No action':0,'Local line':50000,'Intercompany transfer':500000,'Layered response':550000}; choice=st.segmented_control('Response',list(opts),default='No action') or 'No action'; f=opts[choice]; r=simulate(hist,4,funding=f); st.session_state.funding=f
  left,right=st.columns([2.15,1],gap='large')
  with left: st.plotly_chart(fan(r,f'Post-response: {choice}',friday),use_container_width=True)
  with right:
   a,b=st.columns(2); a.metric('Funding',money(f)); b.metric('P(Negative)',f"{r['pneg']:.1%}"); c,d=st.columns(2); c.metric('VaR 95%',money(r['var'])); d.metric('CVaR 95%',money(r['cvar']))
   st.dataframe(compare_responses(hist)[['Response','Funding','P(Negative)']],use_container_width=True,hide_index=True,height=175)
   if st.button('Create CFO brief →',type='primary',use_container_width=True): st.session_state.page=8; st.rerun()
 elif page=='CFO Brief':
  f=st.session_state.funding; r=simulate(hist,4,funding=f); hero('9:30 AM','A governed liquidity decision','Evidence, transformations, probabilities, and the selected response are now decision-ready.')
  l,rcol=st.columns([1.55,1],gap='large')
  with l: st.markdown(f'<div class="panel"><div class="eyebrow">EXECUTIVE DECISION BRIEF</div><h3>Gulf Components liquidity exposure</h3><p><b>Situation:</b> Monday evidence invalidated assumptions behind Friday’s forecast. Current P(Negative) is {r["pneg"]:.1%}; 95% expected tail shortfall is {money(r["cvar"])}.</p><p><b>Driver:</b> The $620,000 Orion receipt may settle after payroll and supplier obligations.</p><p><b>Constraint:</b> Local-line capacity is $50,000; additional liquidity requires authorization.</p><p><b>Selected funding:</b> {money(f)}.</p><p><b>Decision:</b> confirm receipt timing and approve funding before the projected trough.</p></div>',unsafe_allow_html=True)
  with rcol:
   a,b=st.columns(2); a.metric('Confidence','95%'); b.metric('Horizon','10 days'); c,d=st.columns(2); c.metric('VaR',money(r['var'])); d.metric('CVaR',money(r['cvar']))
   brief=f'''CFO DECISION BRIEF\nConfidence: 95%\nHorizon: 10 days\nVaR: {money(r['var'])}\nCVaR: {money(r['cvar'])}\nP(Negative): {r['pneg']:.1%}\nSelected funding: {money(f)}\nDecision: confirm receipt timing and approve funding before the trough.\n'''; st.download_button('Download brief',brief,file_name='CFO_Decision_Brief.txt',type='primary',use_container_width=True)
   if st.button('Open audit and downloads →',use_container_width=True): st.session_state.page=9; st.rerun()
 else:
  hero('AUDIT & OUTPUTS','Download what the agents produced','Cleaned current data, simulation outputs, issue decisions, and the source trail remain available.')
  final=simulate(hist,4,funding=st.session_state.funding); output=pd.DataFrame({'date':DATES,'expected_cash':final['mean'],'p2_5':final['p025'],'p25':final['p25'],'p75':final['p75'],'p97_5':final['p975']})
  audit=pd.DataFrame([['Inbox Agent','Retrieved staged Monday evidence','Automated'],['Document Agent','Profiled actual attachments','Automated'],['Mapping Agent','Mapped fields and aliases','Proposed'],['Treasury analyst','Approved material treatments','Human'],['Risk Agent','Reran historical simulation','Deterministic'],['Scenario Agent','Compared funding responses','Decision support']],columns=['Actor','Activity','Control'])
  l,r=st.columns(2); l.dataframe(audit,use_container_width=True,hide_index=True,height=250); r.dataframe(output,use_container_width=True,hide_index=True,height=250)
  mem=io.BytesIO()
  with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('forecast_percentiles.csv',output.to_csv(index=False)); z.writestr('response_comparison.csv',compare_responses(hist).to_csv(index=False)); z.writestr('historical_profile.csv',hist.describe(include='all').to_csv()); z.writestr('audit_trail.csv',audit.to_csv(index=False)); z.writestr('attachment_profile.csv',process_inbox(INBOX).to_csv(index=False))
  st.download_button('Download agent output package',mem.getvalue(),file_name='Treasury_Agent_Outputs.zip',type='primary')
  if st.button('Reset demonstration'): st.session_state.clear(); st.rerun()
