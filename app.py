from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import load_truth_set,calculate_forecast,scenario_summary,checks
st.set_page_config(page_title='Treasury Mission Control',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
BASE=Path(__file__).parent; DEFAULT=BASE/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'
C={'navy':'#0B2239','blue':'#156A9C','cyan':'#00B8C4','amber':'#F2A900','red':'#D83B3E','green':'#17846D','ink':'#20364A','muted':'#687C8E','bg':'#EEF3F7'}
st.markdown(f'''<style>
.stApp{{background:{C['bg']}}}.block-container{{padding:1rem 1.7rem 2.5rem;max-width:1540px}}[data-testid="stSidebar"]{{background:#0B2239}}[data-testid="stSidebar"] *{{color:#EFF6FA!important}}
#MainMenu,footer{{visibility:hidden}}.hero{{background:radial-gradient(circle at 88% 10%,rgba(0,184,196,.28),transparent 30%),linear-gradient(118deg,#0B2239,#145B7F);color:white;border-radius:20px;padding:1.35rem 1.5rem;box-shadow:0 14px 35px rgba(11,34,57,.18)}}
.hero h1{{font-size:2.15rem;line-height:1.05;margin:.25rem 0}}.hero p{{color:#D9EAF2;margin:.35rem 0 0;font-size:1rem}}.eyebrow{{font-size:.7rem;letter-spacing:.13em;text-transform:uppercase;color:#42E4ED;font-weight:800}}
.panel{{background:white;border:1px solid #D6E1E8;border-radius:16px;padding:1rem 1.1rem;box-shadow:0 5px 16px rgba(11,34,57,.07)}}.panel h3{{font-size:1rem;margin:.05rem 0 .5rem;color:#20364A}}.muted{{color:#687C8E;font-size:.86rem}}
.directive{{background:#FFF8E8;border:1px solid #F4D58A;border-left:5px solid #F2A900;padding:.8rem 1rem;border-radius:12px;color:#20364A}}.risk{{background:#FFF1F1;border:1px solid #F2C7C8;border-left:5px solid #D83B3E;padding:.8rem 1rem;border-radius:12px}}
.queue{{display:flex;align-items:center;gap:.65rem;border-bottom:1px solid #E8EEF2;padding:.58rem 0}}.badge{{border-radius:999px;padding:.16rem .5rem;background:#FFF0D1;color:#8B5A00;font-size:.68rem;font-weight:800}}.impact{{margin-left:auto;color:#D83B3E;font-weight:800;font-size:.85rem}}
.entity{{display:grid;grid-template-columns:1fr auto;align-items:center;border-bottom:1px solid #E8EEF2;padding:.52rem 0}}.dot{{height:10px;width:10px;border-radius:50%;display:inline-block;margin-right:.45rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D6E1E8;border-radius:15px;padding:.65rem .9rem;box-shadow:0 4px 12px rgba(11,34,57,.05)}}div[data-testid="stMetricValue"]{{font-size:1.55rem}}.stButton>button{{border-radius:11px;font-weight:800;min-height:46px}}
</style>''',unsafe_allow_html=True)
for k,v in {'step':1,'decisions':{},'funding':0.}.items(): st.session_state.setdefault(k,v)
def hero(k,t,s): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)
def money(v): return f'${abs(v)/1e6:,.2f}M' if abs(v)>=1e6 else f'${abs(v):,.0f}'
def signmoney(v): return ('(' if v<0 else '')+money(v)+(')' if v<0 else '')
def color(s): return C['red'] if s=='NEGATIVE' else C['amber'] if s=='BELOW MINIMUM' else C['green']
with st.sidebar:
    st.markdown('## ◈ Treasury Mission Control'); st.caption('Monday-Morning Liquidity Problem')
    uploaded=st.file_uploader('Use revised truth set',type=['xlsx'])
    pages=['Mission Brief','Review Queue','Liquidity Network','Scenario Lab','CFO Decision Brief','Controls']; page=st.radio('Workflow',pages,index=max(0,min(st.session_state.step-1,5)))
    st.markdown('---'); st.caption('Synthetic case | Deterministic calculations | No transaction execution')
try: ts=load_truth_set(uploaded if uploaded else DEFAULT)
except Exception as e: st.error(f'Workbook load error: {e}'); st.stop()
fc=calculate_forecast(ts); sums=scenario_summary(fc,ts); qa=checks(ts,fc)
if page=='Mission Brief':
    hero('08:03 AM | MONDAY','The company has cash. Does Treasury have visibility?','A positive consolidated balance can coexist with an entity-level liquidity failure.')
    st.markdown(''); st.markdown('<div class="directive"><b>CFO mandate:</b> Keep every account positive. Bring any liquidity concern and a recommended response to the 9:30 briefing.</div>',unsafe_allow_html=True)
    st.markdown(''); a,b,c=st.columns([1.05,1.45,1.25],gap='large')
    with a:
        st.markdown('<div class="panel"><div class="eyebrow">POSITION AT INTAKE</div><h3>$6.16M reported cash</h3><p class="muted">The aggregate figure appears reassuring, but has not passed treasury review.</p><br><div class="entity"><span>Restricted cash</span><b>$499K</b></div><div class="entity"><span>Forecast confidence</span><b style="color:#F2A900">LOW</b></div><div class="entity"><span>Priority exceptions</span><b style="color:#D83B3E">6</b></div><div class="entity"><span>Time to briefing</span><b>87 min</b></div></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel"><div class="eyebrow">LIQUIDITY NETWORK</div><h3>Entity status before review</h3><div class="entity"><span><i class="dot" style="background:#17846D"></i>Meridian Holdings</span><b>Healthy</b></div><div class="entity"><span><i class="dot" style="background:#17846D"></i>Meridian Manufacturing</span><b>Healthy</b></div><div class="entity"><span><i class="dot" style="background:#F2A900"></i>Apex Distribution</span><b>Review</b></div><div class="entity"><span><i class="dot" style="background:#D83B3E"></i>Gulf Components</span><b>Unknown</b></div><div class="entity"><span><i class="dot" style="background:#17846D"></i>Meridian Canada</span><b>Healthy</b></div><div class="entity"><span><i class="dot" style="background:#F2A900"></i>Meridian Europe</span><b>Restricted cash</b></div></div>',unsafe_allow_html=True)
    with c:
        q=[('Duplicate balance','$2.45M'),('Restricted reserve','Material'),('Orion receipt timing','$620K'),('Duplicate payroll','$245K'),('Facility mismatch','$50K'),('FX inconsistencies','Review')]
        html='<div class="panel"><div class="eyebrow">PRIORITY REVIEW QUEUE</div><h3>What can change the answer?</h3>'
        for i,(x,y) in enumerate(q,1): html+=f'<div class="queue"><span class="badge">{i}</span><span>{x}</span><span class="impact">{y}</span></div>'
        html+='</div>'; st.markdown(html,unsafe_allow_html=True)
    st.markdown(''); st.markdown('<div class="risk"><b>Decision tension:</b> One delayed receipt can turn a policy exception into a negative-balance event, even while consolidated cash remains positive.</div>',unsafe_allow_html=True)
    if st.button('Investigate the liquidity position →',type='primary',use_container_width=True): st.session_state.step=2; st.rerun()
elif page=='Review Queue':
    hero('STEP 1 | CONTROL THE INPUTS','Resolve the exceptions that can move cash','The goal is not to clean every cell. The goal is to separate safe standardization from financial judgment.')
    issues=ts.treatments.copy(); done=len(st.session_state.decisions); total=len(issues); c1,c2,c3=st.columns(3); c1.metric('Resolved',f'{done}/{total}'); c2.metric('Needs judgment',int(issues['Human Review Required?'].astype(str).eq('Y').sum())); c3.metric('Confidence',f'{50+round(45*done/max(total,1))}%')
    idx=min(done,total-1); r=issues.iloc[idx]; iid=str(r['Issue ID'])
    st.markdown(f'<div class="panel"><div class="eyebrow">{r["Classification"]} | {iid}</div><h3>{r["Issue"]}</h3><p><b>Source:</b> {r["Source File"]}</p><p><b>Proposed treatment:</b> {r["Accepted Treatment"]}</p></div>',unsafe_allow_html=True)
    x,y,z=st.columns(3)
    if x.button('Accept treatment',type='primary',use_container_width=True): st.session_state.decisions[iid]='Accepted'; st.rerun()
    if y.button('Defer for confirmation',use_container_width=True): st.session_state.decisions[iid]='Deferred'; st.rerun()
    if z.button('Reject proposal',use_container_width=True): st.session_state.decisions[iid]='Rejected'; st.rerun()
    st.progress(done/max(total,1)); view=issues.copy(); view['Decision']=view['Issue ID'].astype(str).map(st.session_state.decisions).fillna('Pending'); st.dataframe(view,use_container_width=True,hide_index=True)
    if done>=min(4,total) and st.button('Reveal the liquidity network →',type='primary'): st.session_state.step=3; st.rerun()
elif page=='Liquidity Network':
    hero('STEP 2 | CREATE VISIBILITY','The aggregate is healthy. Gulf Components is not.','Move from consolidated cash to the entity, timing, and accessibility of liquidity.')
    scenario=st.segmented_control('Scenario',['Reported','Downside','Stress'],default='Downside') or 'Downside'; g=fc[fc.Scenario==scenario]; gulf=g[g['Entity ID']=='E004']; tr=gulf.loc[gulf.Ending.idxmin()]; first=g[g.Date==g.Date.min()]
    c1,c2,c3,c4=st.columns(4); c1.metric('Consolidated available',money(first['Ending USD'].sum())); c2.metric('Gulf trough',signmoney(tr.Ending)); c3.metric('Policy minimum','$200,000'); c4.metric('Local line','$50,000')
    st.markdown('<div class="risk"><b>Hidden exposure found:</b> Gulf Components crosses below policy and can move below zero before the assumed customer receipt arrives.</div>',unsafe_allow_html=True)
    left,right=st.columns([1.8,1],gap='large')
    with left:
        fig=go.Figure(); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf.Ending,mode='lines+markers',line=dict(color=C['cyan'],width=5),marker=dict(size=9),fill='tozeroy',fillcolor='rgba(0,184,196,.10)',name='Available cash')); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf.Minimum,mode='lines',line=dict(color=C['amber'],width=3,dash='dash'),name='Policy minimum')); fig.add_hline(y=0,line_color=C['red'],line_width=2); fig.add_annotation(x=tr.Date,y=tr.Ending,text=f'Trough {signmoney(tr.Ending)}',showarrow=True,bgcolor='white',bordercolor=C['red']); fig.update_layout(height=470,paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',legend_orientation='h',margin=dict(l=25,r=20,t=35,b=20),yaxis_tickprefix='$',yaxis_tickformat=',.0f'); st.plotly_chart(fig,use_container_width=True)
    with right:
        st.markdown('<div class="panel"><div class="eyebrow">DRIVER BRIDGE</div><h3>Why the trough occurs</h3><div class="entity"><span>Opening available cash</span><b>$230K</b></div><div class="entity"><span>Early operating flows</span><b style="color:#D83B3E">($150K)</b></div><div class="entity"><span>Payroll + suppliers</span><b style="color:#D83B3E">($410K)</b></div><div class="entity"><span>Orion receipt</span><b style="color:#17846D">+$620K</b></div><div class="entity"><span>Timing dependence</span><b style="color:#F2A900">HIGH</b></div></div>',unsafe_allow_html=True)
        st.markdown('<br><div class="panel"><div class="eyebrow">ACCESSIBILITY</div><h3>Cash is not freely transferable</h3><p class="muted">Restricted accounts, borrower limitations, approval thresholds, and notice periods constrain the response.</p></div>',unsafe_allow_html=True)
    if st.button('Test treasury responses →',type='primary'): st.session_state.step=4; st.rerun()
elif page=='Scenario Lab':
    hero('STEP 3 | TEST THE RESPONSE','What action keeps Gulf Components liquid?','Change the receipt timing and funding response. Watch the policy breach and negative exposure change.')
    base=ts.scenarios.set_index('Scenario').loc['Downside']; a,b,c=st.columns(3); receipt=a.date_input('Orion receipt date',pd.Timestamp(base['Orion Receipt Date']).date()); shock=b.number_input('Unexpected payment',0.,500000.,0.,10000.); funding=c.number_input('Approved funding',0.,1000000.,float(st.session_state.funding),50000.)
    custom={'Downside':{'Orion Receipt Date':pd.Timestamp(receipt),'Unplanned Gulf Payment Date':pd.Timestamp('2026-09-04') if shock else pd.NaT,'Unplanned Gulf Payment Amount':shock}}; raw=calculate_forecast(ts,custom=custom); rg=raw[(raw.Scenario=='Downside')&(raw['Entity ID']=='E004')]; rawtr=rg.loc[rg.Ending.idxmin()]
    actions={f'Downside|E004|{rawtr.Date.date().isoformat()}':funding} if funding else {}; out=calculate_forecast(ts,funding_actions=actions,custom=custom); gulf=out[(out.Scenario=='Downside')&(out['Entity ID']=='E004')]; tr=gulf.loc[gulf.Ending.idxmin()]
    c1,c2,c3,c4=st.columns(4); c1.metric('Trough',signmoney(tr.Ending)); c2.metric('Policy gap',signmoney(tr.Surplus)); c3.metric('Days at risk',int((gulf.Status!='OK').sum())); c4.metric('Residual negative',money(max(0,-tr.Ending)))
    fig=go.Figure(); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf.Ending,mode='lines+markers',line=dict(color=C['blue'],width=5),name='Cash after action')); fig.add_trace(go.Scatter(x=gulf.Date,y=gulf.Minimum,mode='lines',line=dict(color=C['amber'],dash='dash',width=3),name='Policy minimum')); fig.add_hline(y=0,line_color=C['red'],line_width=2); fig.update_layout(height=440,paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',legend_orientation='h',yaxis_tickprefix='$',yaxis_tickformat=',.0f'); st.plotly_chart(fig,use_container_width=True)
    x,y,z=st.columns(3)
    if x.button('Use $50K local line',use_container_width=True): st.session_state.funding=50000.; st.rerun()
    if y.button('Request $500K transfer',type='primary',use_container_width=True): st.session_state.funding=500000.; st.rerun()
    if z.button('Reset action',use_container_width=True): st.session_state.funding=0.; st.rerun()
    if st.button('Prepare CFO decision brief →',type='primary'): st.session_state.step=5; st.rerun()
elif page=='CFO Decision Brief':
    hero('STEP 4 | COMMUNICATE THE DECISION','From fragmented files to an executive decision','The analytical workflow now produces a concise, governed request for action.')
    sc=st.selectbox('Briefing basis',['Reported','Downside','Stress'],index=1); s=sums.set_index('Scenario').loc[sc]
    st.markdown(f'<div class="panel"><div class="eyebrow">EXECUTIVE DECISION BRIEF</div><h3>Gulf Components liquidity exposure</h3><p><b>Situation.</b> Consolidated liquidity remains positive, but Gulf Components reaches {signmoney(s.Trough)} on {pd.Timestamp(s.Date).strftime("%A, %B %d")} under the {sc} scenario, against a $200,000 operating minimum.</p><p><b>Driver.</b> The timing of the $620,000 Orion Automotive receipt determines whether the issue remains a policy exception or becomes a negative-balance event.</p><p><b>Available response.</b> The reconciled local line provides $50,000. Additional support is subject to transfer, borrower, timing, and approval constraints.</p><p><b>Decision requested.</b> Confirm receipt timing and authorize sufficient funding before the projected trough.</p></div>',unsafe_allow_html=True)
    st.markdown('### What changed after treasury review'); st.dataframe(pd.DataFrame({'At intake':['$6.16M reported cash','$100K local availability','Receipt fixed at Sept. 2','Restricted reserve included','No explicit action'],'Decision-ready':['Entity exposure identified','$50K reconciled availability','Receipt timing scenario-tested','Restricted cash excluded','Funding approval requested']}),use_container_width=True,hide_index=True)
    brief=f'''CFO DECISION BRIEF\nScenario: {sc}\nGulf Components trough: {signmoney(s.Trough)} on {pd.Timestamp(s.Date).strftime('%B %d')}.\nPolicy minimum: $200,000.\nPrimary driver: timing of the $620,000 Orion Automotive receipt.\nLocal-line capacity: $50,000.\nDecision: confirm receipt timing and authorize sufficient funding before the trough.\n'''; st.download_button('Download decision brief',brief,file_name=f'CFO_Decision_Brief_{sc}.txt',type='primary')
else:
    hero('CONTROL LAYER','Trust the process, not the animation','The app separates deterministic financial calculations from assisted interpretation and narrative.')
    a,b,c=st.columns(3); a.metric('Controls passed',f'{int(qa.Pass.sum())}/{len(qa)}'); b.metric('Calculation engine','Deterministic'); c.metric('Transactions executed','None'); st.dataframe(qa,use_container_width=True,hide_index=True)
    if st.button('Reset presentation'): st.session_state.clear(); st.rerun()
