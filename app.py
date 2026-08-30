from pathlib import Path
import io, json, zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import DATES, MINIMUM, STORMS, load_history, simulate, process_inbox, compare_responses

st.set_page_config(page_title='Treasury Agent Operations',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
BASE=Path(__file__).parent
def first_existing(*paths):
    return next((p for p in paths if p.exists()),paths[0])
SAMPLE=first_existing(BASE/'data'/'historical_forecast_errors.csv',BASE/'historical_forecast_errors.csv')
INBOX=first_existing(BASE/'data'/'monday_inbox',BASE)
INBOX_JSON=first_existing(BASE/'data'/'inbox.json',BASE/'inbox.json')
C={'navy':'#081F33','cyan':'#00BAC6','amber':'#F4AB00','red':'#D63F42','green':'#15836D','bg':'#EDF3F7'}
st.markdown(f'''<style>
.stApp{{background:{C['bg']}}}.block-container{{padding:1.15rem 1.05rem .9rem;max-width:1550px}}[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] p,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{{color:#F1F7FA!important}}header[data-testid="stHeader"]{{height:2.5rem;background:rgba(255,255,255,.96)}}
.hero{{background:linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:14px;padding:.64rem .95rem;margin-bottom:.4rem}}.hero h1{{font-size:1.48rem;margin:.06rem 0}}.hero p{{font-size:.82rem;color:#D8E8EF;margin:0}}.eyebrow{{font-size:.6rem;letter-spacing:.12em;color:#43E6ED;font-weight:800;text-transform:uppercase}}
.panel{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.68rem .8rem;box-shadow:0 3px 10px rgba(8,31,51,.06)}}.row{{display:flex;gap:.45rem;align-items:center;border-bottom:1px solid #E7EEF2;padding:.32rem 0;font-size:.81rem}}.grow{{flex:1}}.muted{{font-size:.73rem;color:#687C8E}}.badge{{font-size:.61rem;font-weight:800;border-radius:999px;padding:.1rem .38rem;background:#DFF7F7;color:#087680}}
.warn{{background:#FFF7E3;border-left:4px solid #F4AB00;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.danger{{background:#FFF0F0;border-left:4px solid #D63F42;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.success{{background:#EAF8F4;border-left:4px solid #15836D;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:11px;padding:.36rem .56rem}}div[data-testid="stMetricLabel"]{{font-size:.68rem}}div[data-testid="stMetricValue"]{{font-size:1.16rem}}.stButton>button{{min-height:34px;border-radius:9px;font-weight:800}}.stButton>button[kind="primary"]{{background:#00A6B2!important;border-color:#00A6B2!important;color:#FFFFFF!important}}.stButton>button[kind="primary"]:hover{{background:#087F89!important;border-color:#087F89!important}}[data-testid="stSidebar"] .stButton>button{{background:#F8FAFC!important;border:1px solid #D5E1E8!important;color:#17324A!important}}[data-testid="stSidebar"] .stButton>button p{{color:#17324A!important}}[data-testid="stSidebar"] .stButton>button:hover{{background:#E7F6F7!important;border-color:#00A6B2!important}}h3{{margin:.25rem 0!important;font-size:1rem!important}}
.clockbar{{display:grid;grid-template-columns:150px minmax(260px,1fr) 150px;align-items:center;gap:.85rem;background:#0B2C43;border:1px solid #164D68;border-radius:11px;padding:.48rem .75rem;margin:.15rem 0 .48rem;box-shadow:0 3px 10px rgba(8,31,51,.12)}}.clocktime{{font-size:1rem;font-weight:900;color:#FFFFFF!important;line-height:1.15}}.clocklabel{{font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:#D7E7EF!important;font-weight:900;line-height:1.1;margin-bottom:.2rem}}.clockphase{{font-size:.75rem;color:#FFFFFF!important;font-weight:800;line-height:1.1;margin-bottom:.3rem}}.clocktrack{{height:7px;background:#315266;border-radius:999px;overflow:hidden;border:1px solid rgba(255,255,255,.14)}}.clockfill{{height:100%;background:linear-gradient(90deg,#35D8DE,#F4AB00,#FF6467);border-radius:999px}}.clockremain{{font-size:.78rem;font-weight:900;color:#FF8B8D!important;white-space:nowrap;text-align:right}}
@media (max-width:1100px){{.clockbar{{grid-template-columns:130px 1fr 130px;gap:.55rem}}.clockremain{{font-size:.7rem}}}}
</style>''',unsafe_allow_html=True)

PAGES=['Historical Baseline','Friday Snapshot','Organization Map','Monday Inbox','Agent Operations','Human Review','The Storm','Dilemma','Response Studio','CFO Brief','Audit & Downloads']
CLOCK={'Historical Baseline':('Fri 4:20 PM',0,'Baseline preparation'),'Friday Snapshot':('Fri 4:30 PM',0,'Risk baseline approved'),'Organization Map':('Mon 8:00 AM',0,'Operating context'),'Monday Inbox':('Mon 8:03 AM',3,'New evidence arrives'),'Agent Operations':('Mon 8:08 AM',8,'Agents process files'),'Human Review':('Mon 8:15 AM',15,'Material judgments'),'The Storm':('Mon 8:28 AM',28,'Forecast deteriorates'),'Dilemma':('Mon 8:42 AM',42,'Decision required'),'Response Studio':('Mon 8:55 AM',55,'Responses tested'),'CFO Brief':('Mon 9:25 AM',85,'Brief ready'),'Audit & Downloads':('Mon 9:30 AM',90,'Briefing time')}
for k,v in {'page':0,'hist':None,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action','presentation_mode':True}.items(): st.session_state.setdefault(k,v)

def hero(k,t,s): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)
def money(v): return f'${abs(v)/1e6:.2f}M' if abs(v)>=1e6 else f'${abs(v):,.0f}'
def clock(page):
    t,e,phase=CLOCK[page]; rem=max(0,90-e); text='Before Monday' if page in PAGES[:2] else ('Briefing time' if rem==0 else f'{rem} min to CFO brief')
    st.markdown(f'<div class="clockbar"><div><div class="clocklabel">Briefing clock</div><div class="clocktime">{t}</div></div><div><div class="clockphase">{phase}</div><div class="clocktrack"><div class="clockfill" style="width:{min(100,e/90*100):.0f}%"></div></div></div><div class="clockremain">{text}</div></div>',unsafe_allow_html=True)
def fan(r,title,prior=None,events=False):
    f=go.Figure(); f.add_trace(go.Scatter(x=DATES,y=r['p975'],line_width=0,showlegend=False,hoverinfo='skip')); f.add_trace(go.Scatter(x=DATES,y=r['p025'],fill='tonexty',fillcolor='rgba(0,186,198,.11)',line_width=0,name='95% range')); f.add_trace(go.Scatter(x=DATES,y=r['p75'],line_width=0,showlegend=False,hoverinfo='skip')); f.add_trace(go.Scatter(x=DATES,y=r['p25'],fill='tonexty',fillcolor='rgba(0,186,198,.24)',line_width=0,name='50% range')); f.add_trace(go.Scatter(x=DATES,y=r['mean'],line=dict(color=C['cyan'],width=4),mode='lines+markers',name='Current expected'))
    if prior is not None: f.add_trace(go.Scatter(x=DATES,y=prior['mean'],line=dict(color='#7D8D99',dash='dot',width=2),name='Friday expected'))
    f.add_hline(y=MINIMUM,line_color=C['amber'],line_dash='dash'); f.add_hline(y=0,line_color=C['red'],line_width=2)
    if events:
        for idx,text,color in [(2,'Orion expected',C['green']),(3,'Payroll + suppliers',C['red']),(4,'Potential shock',C['amber'])]: f.add_annotation(x=DATES[idx],y=r['mean'][idx],text=text,showarrow=True,arrowcolor=color,bgcolor='white',font_size=10)
    f.update_layout(title=title,height=330,paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',legend_orientation='h',margin=dict(l=15,r=10,t=38,b=10),yaxis_tickprefix='$',yaxis_tickformat=',.0f'); return f

def jump_button(label,target,primary=True):
    if st.button(label,type='primary' if primary else 'secondary',use_container_width=True): st.session_state.page=target; st.rerun()

STORM_EVIDENCE=[
('EXPECTED CASH','Opening cash revised','Updated forecast, use version 2','Gulf_Cash_Fcst_v2.xlsx','Opening cash is $25,000 below Friday.','Opening shift −$25,000; volatility 0.62× → 1.05×.','Expected path moves down; ranges widen.'),
('UNCERTAINTY','Orion timing challenged','Orion timing remains unconfirmed','AR_Expectations.xlsx','$620,000 expected Sep 2; average delay five days.','Receipt-date probabilities move later.','Pre-settlement cash falls; left tail deepens.'),
('EXPECTED CASH + UNCERTAINTY','Payments concentrate','AP and payroll schedule','Apex_Disbursements.csv','An additional $90,000 payment lands Sep 4.','Sep 4 flow −$90,000; volatility 1.15× → 1.25×.','Expected path falls; lower 95% range approaches zero.'),
('FUNDING CAPACITY','Local line corrected','Facility availability','Facilities.xlsx','$500,000 commitment less $450,000 drawn.','$100,000 reported availability → $50,000 reconciled.','Forecast unchanged; safety net falls by $50,000.'),
('CONTROL QUALITY','Transfer access constrained','Forecast and restricted reserve','Europe_Reserve.csv + Facilities.xlsx','Reserve is restricted and parent funding requires approval.','Unapproved liquidity excluded; volatility 1.28× → 1.38×.','No automatic Gulf cash injection; tail remains exposed.')]
EVIDENCE=[('Meridian Holdings','Corporate Controller','Holdings_Balances.csv','Accounts 00100442 and 100442 share $2.45M','Likely duplicate','98%','$2.45M'),('Meridian Europe','Europe Controller','Europe_Reserve.csv','EU7799 reports 42.5M EUR and restricted=Y','Likely cents/units anomaly; exclude from available','94%','Material'),('Gulf Components','AR Operations','AR_Expectations.xlsx','INV-8812 duplicated; Sep 2 expected; 5 days late','Duplicate and timing risk','96%','$620K'),('Apex + Gulf','Shared Services','Apex_Disbursements.csv','Gulf payroll $245K appears twice','Potential duplicate payroll','97%','$245K'),('Gulf Components','Bank Partner','Facilities.xlsx','$500K commitment; $450K drawn; $100K reported','Availability is $50K','100%','$50K'),('Meridian Canada','Canada Controller','Canada_CAD.xlsx','Forecast uses Friday FX 0.742','Compare with approved rate','91%','Translation')]

with st.sidebar:
    st.markdown('## ◈ Treasury Agent Operations'); st.caption('Evidence to decision')
    st.session_state.presentation_mode=st.toggle('Presentation mode',value=st.session_state.presentation_mode)
    if st.session_state.presentation_mode:
        st.markdown(f'**Act {st.session_state.page+1} of {len(PAGES)}**'); st.caption(PAGES[st.session_state.page])
        a,b=st.columns(2)
        if a.button('←',use_container_width=True): st.session_state.page=max(0,st.session_state.page-1); st.rerun()
        if b.button('→',use_container_width=True): st.session_state.page=min(len(PAGES)-1,st.session_state.page+1); st.rerun()
    else:
        selected=st.radio('Narrative',PAGES,index=st.session_state.page)
        st.session_state.page=PAGES.index(selected)
    if st.button('Reset demo',use_container_width=True):
        for k in ['page','storm','reviewed','funding','inspect','audience_choice']: st.session_state[k]={'page':0,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action'}[k]
        st.rerun()

if st.session_state.hist is None:
    try: st.session_state.hist=load_history(SAMPLE)
    except Exception as e: st.error(f'Historical data load failed: {e}'); st.stop()
hist=st.session_state.hist; friday=simulate(hist,-1); page=PAGES[st.session_state.page]; clock(page)

if page=='Historical Baseline':
    hero('T−2 | BEFORE MONDAY','Historical forecast performance loaded','The Risk Agent reads the versioned historical-error file automatically and validates the baseline before Monday begins.')
    preview=hist.head(5).copy()
    preview['date']=preview['date'].dt.strftime('%b %d, %Y')
    for column in ['opening_error','receipt_error','disbursement_error']:
        preview[column]=preview[column].round(0).astype(int)
    l,r=st.columns([.92,1.35],gap='large')
    with l:
        st.markdown(f'''<div class="panel"><div class="eyebrow">AUTOMATIC SOURCE</div><h3>{SAMPLE.name}</h3><p class="muted">Version-controlled historical forecast errors used to calibrate the Friday liquidity distribution.</p><div class="row"><span>Load status</span><span class="grow"></span><b style="color:#15836D">READY</b></div><div class="row"><span>Observations</span><span class="grow"></span><b>{len(hist)}</b></div><div class="row"><span>Coverage</span><span class="grow"></span><b>{hist.date.min().strftime('%b %Y')} to {hist.date.max().strftime('%b %Y')}</b></div><div class="row"><span>Required fields</span><span class="grow"></span><b>4 of 4</b></div><div class="row"><span>Validation</span><span class="grow"></span><b style="color:#15836D">PASSED</b></div></div>''',unsafe_allow_html=True)
    with r:
        st.markdown('<div class="eyebrow" style="color:#087F89;margin:.15rem 0 .3rem">HISTORICAL SAMPLE</div>',unsafe_allow_html=True)
        st.dataframe(preview,use_container_width=True,hide_index=True,height=228,column_config={'date':st.column_config.TextColumn('Date'),'opening_error':st.column_config.NumberColumn('Opening error',format='$%d'),'receipt_error':st.column_config.NumberColumn('Receipt error',format='$%d'),'disbursement_error':st.column_config.NumberColumn('Disbursement error',format='$%d')})
    st.markdown('<div class="success"><b>Baseline ready:</b> The historical series is complete enough to estimate a reproducible 95% liquidity-risk distribution.</div>',unsafe_allow_html=True)
    jump_button('Build Friday risk baseline →',1)
elif page=='Friday Snapshot':
    hero('T−1 | FRIDAY','A manageable 95% baseline','The analyst enters the weekend with measured, not zero, liquidity risk.')
    l,r=st.columns([2.2,1]); l.plotly_chart(fan(friday,'Friday cash distribution'),use_container_width=True)
    with r:
        a,b=st.columns(2); a.metric('VaR 95%',money(friday['var'])); b.metric('CVaR 95%',money(friday['cvar'])); c,d=st.columns(2); c.metric('P(Below $200K)',f"{friday['pmin']:.1%}"); d.metric('P(Negative)',f"{friday['pneg']:.1%}")
        st.markdown('<div class="success"><b>Interpretation:</b> Known downside remains within anticipated response capacity.</div>',unsafe_allow_html=True); jump_button('Meet Meridian Components →',2)
elif page=='Organization Map':
    hero('ORGANIZATIONAL CONTEXT','One treasury function. Six entities. No common reporting system.','Different functions, currencies, and constraints feed one central inbox.')
    a,b,c=st.columns(3)
    a.markdown('<div class="panel"><div class="eyebrow">SOURCES</div><div class="row">Corporate Controller</div><div class="row">Manufacturing Finance</div><div class="row">Acquisition Controller</div><div class="row">Shared Services</div><div class="row">International Controllers</div><div class="row">AR Operations + Bank Partner</div></div>',unsafe_allow_html=True)
    b.markdown('<div class="panel"><div class="eyebrow">ENTITIES</div><div class="row">Meridian Holdings</div><div class="row">Meridian Manufacturing</div><div class="row">Apex Distribution</div><div class="row">Gulf Components</div><div class="row">Meridian Canada</div><div class="row">Meridian Europe</div></div>',unsafe_allow_html=True)
    c.markdown('<div class="panel"><div class="eyebrow">CENTRAL TREASURY</div><h3>Treasury Team of One</h3><div class="row">8 messages</div><div class="row">10 attachments</div><div class="row">USD / CAD / EUR</div><div class="row">Central and local facilities</div><div class="warn">Agents connect fragmented evidence to one governed decision.</div></div>',unsafe_allow_html=True); jump_button('Open Monday inbox →',3)
elif page=='Monday Inbox':
    hero('T0 | MONDAY 8:03 AM','The agents retrieve current evidence','No upload. The staged inbox preserves message context and file versions.')
    inbox=json.loads(INBOX_JSON.read_text()); l,r=st.columns([1.7,1])
    with l:
        for m in inbox: st.markdown(f'<div class="panel" style="margin-bottom:.25rem"><div class="row"><span class="badge">{m["time"]}</span><b>{m["subject"]}</b><span class="grow"></span>{len(m["attachments"])} file</div><div class="muted">{m["sender"]} | {m["entity"]} | {", ".join(m["attachments"])}</div></div>',unsafe_allow_html=True)
    with r: st.metric('Messages',8); st.metric('Attachments',10); st.metric('Revisions',2); jump_button('Authorize retrieval →',4)
elif page=='Agent Operations':
    hero('AGENT RUN 08-A','Watch an unstructured submission become decision-ready','The demonstration now shows one full raw-to-approved transformation.')
    raw,agent,approved=st.columns(3)
    raw.markdown('<div class="panel"><div class="eyebrow">RAW SUBMISSION</div><h3>Gulf_Cash_Fcst_v2.xlsx</h3><div class="row">Entity: Gulf Comp.</div><div class="row">Cash In: 620000</div><div class="row">Day: Wed</div><div class="row">Note: confirmation pending</div></div>',unsafe_allow_html=True)
    agent.markdown('<div class="panel"><div class="eyebrow">AGENT INTERPRETATION</div><h3>Confidence 96%</h3><div class="row">Entity → Gulf Components</div><div class="row">Flow → Customer receipt</div><div class="row">Customer → Orion Automotive</div><div class="row">Trigger → historical timing conflict</div></div>',unsafe_allow_html=True)
    approved.markdown('<div class="panel"><div class="eyebrow">PROPOSED RECORD</div><h3>Human review required</h3><div class="row">Amount: $620,000</div><div class="row">Date: probabilistic</div><div class="row">Materiality: High</div><div class="row">Action: inspect source</div></div>',unsafe_allow_html=True)
    prof=process_inbox(INBOX); st.dataframe(prof[['file','type','sheets','rows','columns']],use_container_width=True,hide_index=True,height=190); jump_button('Open human control gate →',5)
elif page=='Human Review':
    hero('HUMAN CONTROL GATE','Agents propose. Treasury decides.','Every material correction remains traceable to source evidence.')
    issues=[('Duplicate Holdings balance','$2.45M','Retain one record'),('Reserve unit anomaly','Material','Correct and exclude restricted cash'),('Orion timing','$620K','Model settlement as a distribution'),('Duplicate payroll','$245K','Retain one verified payment'),('Facility mismatch','$50K','Recalculate availability'),('FX inconsistencies','Review','Use approved feed')]
    i=min(st.session_state.reviewed,5); x=issues[i]; st.markdown(f'<div class="panel"><div class="eyebrow">REVIEW {i+1} OF 6</div><h3>{x[0]}</h3><p><b>Impact:</b> {x[1]} | <b>Proposal:</b> {x[2]}</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    if a.button('Accept',type='primary',use_container_width=True): st.session_state.reviewed=min(6,i+1); st.session_state.inspect=False; st.rerun()
    if b.button('Defer',use_container_width=True): st.session_state.reviewed=min(6,i+1); st.session_state.inspect=False; st.rerun()
    if c.button('Inspect evidence',use_container_width=True): st.session_state.inspect=not st.session_state.inspect
    if st.session_state.inspect:
        e=EVIDENCE[i]; st.markdown(f'<div class="panel"><div class="eyebrow">SOURCE EVIDENCE</div><div class="row"><b>Entity</b><span class="grow"></span>{e[0]}</div><div class="row"><b>Sender</b><span class="grow"></span>{e[1]}</div><div class="row"><b>Attachment</b><span class="grow"></span>{e[2]}</div><p><b>Raw:</b> {e[3]}</p><p><b>Finding:</b> {e[4]} | <b>Confidence:</b> {e[5]} | <b>Impact:</b> {e[6]}</p></div>',unsafe_allow_html=True)
    st.progress(st.session_state.reviewed/6)
    if st.session_state.reviewed>=4: jump_button('Release approved truth set →',6)
elif page=='The Storm':
    stage=st.session_state.storm; r=simulate(hist,stage); prev=friday if stage==0 else simulate(hist,stage-1); e=STORM_EVIDENCE[stage]
    hero(f'STORM {stage+1} OF 5',e[1],'New evidence changes the assumptions behind Friday’s 95% forecast.')
    l,side=st.columns([2.05,1.15])
    with l:
        st.plotly_chart(fan(r,'Friday baseline vs. current risk',friday,events=True),use_container_width=True)
        a,b,c,d=st.columns(4); a.metric('VaR 95%',money(r['var']),delta=money(r['var']-prev['var'])); b.metric('CVaR 95%',money(r['cvar']),delta=money(r['cvar']-prev['cvar'])); c.metric('P(Below $200K)',f"{r['pmin']:.1%}",delta=f"{r['pmin']-prev['pmin']:+.1%}"); d.metric('P(Negative)',f"{r['pneg']:.1%}",delta=f"{r['pneg']-prev['pneg']:+.1%}")
    with side:
        st.markdown(f'<div class="panel"><span class="badge">{e[0]}</span><h3>{e[1]}</h3><div class="row"><b>Email</b><span class="grow"></span>{e[2]}</div><div class="row"><b>File</b><span class="grow"></span>{e[3]}</div><p><b>Observed</b><br>{e[4]}</p><p><b>Model update</b><br>{e[5]}</p><p><b>Decision implication</b><br>{e[6]}</p></div>',unsafe_allow_html=True)
        if stage<4:
            if st.button('Release next event →',type='primary',use_container_width=True): st.session_state.storm+=1; st.rerun()
        else: jump_button('Reveal the dilemma →',7)
elif page=='Dilemma':
    r=simulate(hist,4); hero('AUDIENCE DECISION','What would you recommend before the 9:30 briefing?','Choose first. Then the simulation reveals the residual risk and control implications.')
    st.plotly_chart(fan(r,'Pre-response distribution',friday,events=True),use_container_width=True)
    options=['Rely on receipt','Local line','Intercompany transfer','Layered response']; cols=st.columns(4)
    for col,opt in zip(cols,options):
        if col.button(opt,use_container_width=True,type='primary' if st.session_state.audience_choice==opt else 'secondary'): st.session_state.audience_choice=opt; st.rerun()
    st.markdown(f'<div class="warn"><b>Audience recommendation:</b> {st.session_state.audience_choice}. The next screen tests whether that response controls the tail.</div>',unsafe_allow_html=True); jump_button('Test the audience recommendation →',8)
elif page=='Response Studio':
    mapf={'Rely on receipt':0,'No action':0,'Local line':50000,'Intercompany transfer':500000,'Layered response':550000}; choice=st.session_state.audience_choice; funding=mapf.get(choice,0); st.session_state.funding=funding; r=simulate(hist,4,funding=funding)
    hero('RESPONSE STUDIO',f'Testing: {choice}','A good response balances protection, accessibility, approval, and residual tail risk.')
    l,side=st.columns([2.05,1.15]); l.plotly_chart(fan(r,f'Post-response: {choice}',friday,events=True),use_container_width=True)
    with side:
        st.metric('Funding action',money(funding)); st.metric('P(Negative)',f"{r['pneg']:.1%}")
        rationale={'Rely on receipt':('No funding cost','Timing risk remains','None','Not recommended'), 'Local line':('Local and accessible','Insufficient tail protection','Facility rules','Partial response'), 'Intercompany transfer':('Restores material liquidity','Requires approval','CFO/authorized approver','Viable'), 'Layered response':('Uses local capacity and preserves flexibility','More coordination','Multiple controls','Recommended')}[choice]
        st.markdown(f'<div class="panel"><div class="eyebrow">RESPONSE RATIONALE</div><p><b>Benefit:</b> {rationale[0]}</p><p><b>Limitation:</b> {rationale[1]}</p><p><b>Approval:</b> {rationale[2]}</p><p><b>Assessment:</b> {rationale[3]}</p></div>',unsafe_allow_html=True)
        if choice=='Local line': st.markdown('<div class="danger"><b>Insufficient:</b> Funding helps, but the local line does not restore the policy cushion across the 95% distribution.</div>',unsafe_allow_html=True)
        jump_button('Create CFO decision brief →',9)
elif page=='CFO Brief':
    f=st.session_state.funding; r=simulate(hist,4,funding=f); hero('9:25 AM','A governed liquidity decision','The conclusion remains traceable from executive statement back to source evidence.')
    l,side=st.columns([1.55,1])
    l.markdown(f'<div class="panel"><div class="eyebrow">EXECUTIVE DECISION BRIEF</div><h3>Gulf Components liquidity exposure</h3><p><b>Situation:</b> Current P(Negative) is {r["pneg"]:.1%}; expected tail shortfall is {money(r["cvar"])} at 95% confidence over ten days.</p><p><b>Driver:</b> Orion may settle after payroll and suppliers.</p><p><b>Selected response:</b> {st.session_state.audience_choice}, {money(f)}.</p><p><b>Decision:</b> confirm receipt timing and approve funding before the trough.</p></div>',unsafe_allow_html=True)
    with side:
        st.markdown('<div class="panel"><div class="eyebrow">MODEL DISCLOSURE</div><div class="row">Confidence <span class="grow"></span><b>95%</b></div><div class="row">Horizon <span class="grow"></span><b>10 days</b></div><div class="row">Method <span class="grow"></span><b>Historical bootstrap</b></div><div class="row">Paths <span class="grow"></span><b>3,000</b></div><div class="row">Risk variable <span class="grow"></span><b>Liquidity-trough variance</b></div></div>',unsafe_allow_html=True)
        with st.expander('Trace this conclusion'):
            st.markdown('**Statement → Simulation → Assumptions → Evidence → Approval**')
            st.write('P(Negative) derives from simulated troughs using historical errors, Orion timing probabilities, accepted Monday cash flows, and selected funding.')
            st.write('Primary sources: `AR_Expectations.xlsx`, `Gulf_Cash_Fcst_v2.xlsx`, `Apex_Disbursements.csv`, and `Facilities.xlsx`.')
        jump_button('Open audit & outputs →',10)
else:
    hero('9:30 AM','From fragmented evidence to a controlled decision','The value is adaptation: source traceability, agent speed, human judgment, and probabilistic response.')
    a,b,c=st.columns(3)
    a.markdown('<div class="panel"><div class="eyebrow">BEFORE AGENTS</div><div class="row">8 messages</div><div class="row">10 attachments</div><div class="row">No common schema</div><div class="row">Apparently adequate cash</div></div>',unsafe_allow_html=True)
    b.markdown('<div class="panel"><div class="eyebrow">WHAT CHANGED</div><div class="row">Duplicates isolated</div><div class="row">Restricted cash excluded</div><div class="row">Timing made probabilistic</div><div class="row">Tail exposure quantified</div></div>',unsafe_allow_html=True)
    c.markdown(f'<div class="panel"><div class="eyebrow">DECISION PRODUCED</div><div class="row">Response: {st.session_state.audience_choice}</div><div class="row">Funding: {money(st.session_state.funding)}</div><div class="row">Approval required</div><div class="row">Audit trail preserved</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="success"><b>Friday’s model was not wrong. Monday’s evidence changed the assumptions. The advantage was not perfect prediction. It was the ability to adapt before uncertainty became a liquidity crisis.</b></div>',unsafe_allow_html=True)
    r=simulate(hist,4,funding=st.session_state.funding); out=pd.DataFrame({'date':DATES,'expected_cash':r['mean'],'p2_5':r['p025'],'p25':r['p25'],'p75':r['p75'],'p97_5':r['p975']}); mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z: z.writestr('forecast_percentiles.csv',out.to_csv(index=False)); z.writestr('response_comparison.csv',compare_responses(hist).to_csv(index=False)); z.writestr('attachment_profile.csv',process_inbox(INBOX).to_csv(index=False))
    st.download_button('Download decision package',mem.getvalue(),file_name='Treasury_Agent_Outputs.zip',type='primary',use_container_width=True)
