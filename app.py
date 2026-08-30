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
.stApp{{background:{C['bg']}}}.block-container{{padding:1rem 1.05rem .9rem;max-width:1550px}}[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] p,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{{color:#F1F7FA!important}}header[data-testid="stHeader"]{{display:none!important}}[data-testid="stToolbar"]{{display:none!important}}[data-testid="stDecoration"]{{display:none!important}}#MainMenu{{visibility:hidden!important}}
.hero{{background:linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:14px;padding:.64rem .95rem;margin-bottom:.4rem}}.hero h1{{font-size:1.48rem;margin:.06rem 0}}.hero p{{font-size:.82rem;color:#D8E8EF;margin:0}}.eyebrow{{font-size:.6rem;letter-spacing:.12em;color:#43E6ED;font-weight:800;text-transform:uppercase}}
.panel{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.68rem .8rem;box-shadow:0 3px 10px rgba(8,31,51,.06)}}.row{{display:flex;gap:.45rem;align-items:center;border-bottom:1px solid #E7EEF2;padding:.32rem 0;font-size:.81rem}}.grow{{flex:1}}.muted{{font-size:.73rem;color:#687C8E}}.badge{{font-size:.61rem;font-weight:800;border-radius:999px;padding:.1rem .38rem;background:#DFF7F7;color:#087680}}
.warn{{background:#FFF7E3;border-left:4px solid #F4AB00;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.danger{{background:#FFF0F0;border-left:4px solid #D63F42;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.success{{background:#EAF8F4;border-left:4px solid #15836D;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:11px;padding:.36rem .56rem}}div[data-testid="stMetricLabel"]{{font-size:.68rem}}div[data-testid="stMetricValue"]{{font-size:1.16rem}}.stButton>button{{min-height:34px;border-radius:9px;font-weight:800}}.stButton>button[kind="primary"]{{background:#00A6B2!important;border-color:#00A6B2!important;color:#FFFFFF!important}}.stButton>button[kind="primary"]:hover{{background:#087F89!important;border-color:#087F89!important}}[data-testid="stSidebar"] .stButton>button{{background:#F8FAFC!important;border:1px solid #D5E1E8!important;color:#17324A!important}}[data-testid="stSidebar"] .stButton>button p{{color:#17324A!important}}[data-testid="stSidebar"] .stButton>button:hover{{background:#E7F6F7!important;border-color:#00A6B2!important}}h3{{margin:.25rem 0!important;font-size:1rem!important}}
.titlehero{{min-height:540px;display:flex;align-items:center;justify-content:center;text-align:center;background:radial-gradient(circle at 75% 22%,rgba(0,186,198,.28),transparent 30%),linear-gradient(135deg,#061C2D,#0D4967);color:white;border-radius:22px;padding:2.2rem;box-shadow:0 18px 45px rgba(8,31,51,.22)}}.titlehero h1{{font-size:3.35rem;line-height:1;margin:.35rem 0 .55rem}}.titlehero h2{{font-size:1.45rem;font-weight:500;color:#D9EDF2;margin:0 0 1rem}}.titlehero p{{color:#C5DCE5;font-size:1rem;line-height:1.45}}.titlemeta{{font-size:.82rem;letter-spacing:.04em;color:#B8D2DC;margin-top:1.4rem}}.casebadge{{display:inline-block;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08);border-radius:999px;padding:.35rem .7rem;margin:.18rem;font-size:.78rem;font-weight:800}}.actflow{{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin:.65rem 0}}.actnode{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.65rem;text-align:center;font-size:.8rem;font-weight:800;color:#17324A}}.titleactions div[data-testid="stButton"] button{{min-height:48px;font-size:1rem}}
.clockbar{{display:grid;grid-template-columns:150px minmax(260px,1fr) 150px;align-items:center;gap:.85rem;background:#0B2C43;border:1px solid #164D68;border-radius:11px;padding:.48rem .75rem;margin:0 0 .48rem;box-shadow:0 3px 10px rgba(8,31,51,.12)}}.clocktime{{font-size:1rem;font-weight:900;color:#FFFFFF!important;line-height:1.15}}.clocklabel{{font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:#D7E7EF!important;font-weight:900;line-height:1.1;margin-bottom:.2rem}}.clockphase{{font-size:.75rem;color:#FFFFFF!important;font-weight:800;line-height:1.1;margin-bottom:.3rem}}.clocktrack{{height:7px;background:#315266;border-radius:999px;overflow:hidden;border:1px solid rgba(255,255,255,.14)}}.clockfill{{height:100%;background:linear-gradient(90deg,#35D8DE,#F4AB00,#FF6467);border-radius:999px}}.clockremain{{font-size:.78rem;font-weight:900;color:#FF8B8D!important;white-space:nowrap;text-align:right}}
@media (max-width:1100px){{.clockbar{{grid-template-columns:130px 1fr 130px;gap:.55rem}}.clockremain{{font-size:.7rem}}}}
</style>''',unsafe_allow_html=True)

PAGES=['Title','Treasury Team of One','Historical Baseline','Friday Snapshot','Organization Map','Monday Inbox','Agent Operations','Human Review','The Storm','Dilemma','Response Studio','CFO Brief','Audit & Downloads']
CLOCK={'Title':('Session opening',0,'Presentation ready'),'Treasury Team of One':('Session opening',0,'Operating model'),'Historical Baseline':('Fri 4:20 PM',0,'Baseline preparation'),'Friday Snapshot':('Fri 4:30 PM',0,'Risk baseline approved'),'Organization Map':('Mon 8:00 AM',0,'Operating context'),'Monday Inbox':('Mon 8:03 AM',3,'New evidence arrives'),'Agent Operations':('Mon 8:08 AM',8,'Agents process files'),'Human Review':('Mon 8:15 AM',15,'Material judgments'),'The Storm':('Mon 8:28 AM',28,'Forecast deteriorates'),'Dilemma':('Mon 8:42 AM',42,'Decision required'),'Response Studio':('Mon 8:55 AM',55,'Responses tested'),'CFO Brief':('Mon 9:25 AM',85,'Brief ready'),'Audit & Downloads':('Mon 9:30 AM',90,'Briefing time')}
for k,v in {'page':0,'hist':None,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action','presentation_mode':True,'agent_step':0,'decisions':[]}.items(): st.session_state.setdefault(k,v)

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
        for k in ['page','storm','reviewed','funding','inspect','audience_choice','agent_step']: st.session_state[k]={'page':0,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action','agent_step':0}[k]
        st.rerun()

if st.session_state.hist is None:
    try: st.session_state.hist=load_history(SAMPLE)
    except Exception as e: st.error(f'Historical data load failed: {e}'); st.stop()
hist=st.session_state.hist; friday=simulate(hist,-1); page=PAGES[st.session_state.page]
if page not in ('Title','Treasury Team of One'): clock(page)

if page=='Title':
    st.markdown('''<div class="titlehero"><div><div class="eyebrow">TAMPA BAY AFP | SEPTEMBER 11, 2026</div><h1>The Treasury Team of One</h1><h2>Building AI-Powered Financial Solutions</h2><p>From fragmented evidence to a governed liquidity decision</p><div><span class="casebadge">6 entities</span><span class="casebadge">3 currencies</span><span class="casebadge">8 messages</span><span class="casebadge">10 attachments</span><span class="casebadge">1 CFO deadline</span></div><div class="titlemeta">Zachary A. Smith, Ph.D.<br>Associate Professor of Economics and Finance | Saint Leo University</div></div></div>''',unsafe_allow_html=True)
    st.markdown('<div class="titleactions">',unsafe_allow_html=True)
    a,b=st.columns([1.35,1])
    with a: jump_button('Run the Monday-Morning Liquidity Simulation →',1)
    with b:
        with st.popover('Preview the case',use_container_width=True):
            st.markdown('''**The challenge**

One treasury professional must reconcile six entities, three currencies, eight messages, and ten attachments before a 9:30 CFO briefing.

**The demonstration**

Historical risk → Monday inbox → agent operations → human control → liquidity storm → treasury response → CFO decision.''')
    st.markdown('</div>',unsafe_allow_html=True)
elif page=='Treasury Team of One':
    hero('ACT 1 | THE OPERATING THESIS','Treasury is surrounded by information, not insight.','The challenge is connecting fragmented evidence quickly enough to support a decision that treasury can defend.')
    st.markdown('<div class="actflow"><div class="actnode">Historical evidence</div><div class="actnode">Friday risk baseline</div><div class="actnode">Monday inbox</div><div class="actnode">Agent operations</div><div class="actnode">Human judgment</div><div class="actnode">Liquidity storm</div><div class="actnode">Treasury response</div><div class="actnode">CFO decision</div></div>',unsafe_allow_html=True)
    left,right=st.columns([1.3,1],gap='large')
    left.markdown('''<div class="panel"><div class="eyebrow">THE PROBLEM</div><h3>One analyst. Many systems. One deadline.</h3><p>Balances, forecasts, receivables, payments, facilities, and email context arrive through different people, formats, currencies, and assumptions.</p></div>''',unsafe_allow_html=True)
    right.markdown('''<div class="panel"><div class="eyebrow">THE CONTROL MODEL</div><h3>Agents accelerate. Treasury remains accountable.</h3><p>Agents retrieve, interpret, reconcile, and propose. Treasury approves material corrections, funding actions, and executive communication.</p></div>''',unsafe_allow_html=True)
    st.markdown('<div class="warn"><b>Opening question:</b> Can a Treasury Team of One convert fragmented Monday evidence into a governed liquidity decision before the 9:30 CFO briefing?</div>',unsafe_allow_html=True)
    jump_button('Establish the Friday risk baseline →',2)
elif page=='Historical Baseline':
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
    jump_button('Build Friday risk baseline →',3)
elif page=='Friday Snapshot':
    hero('T−1 | FRIDAY','A manageable 95% baseline','The analyst enters the weekend with measured, not zero, liquidity risk.')
    l,r=st.columns([2.2,1]); l.plotly_chart(fan(friday,'Friday cash distribution'),use_container_width=True)
    with r:
        a,b=st.columns(2); a.metric('VaR 95%',money(friday['var'])); b.metric('CVaR 95%',money(friday['cvar'])); c,d=st.columns(2); c.metric('P(Below $200K)',f"{friday['pmin']:.1%}"); d.metric('P(Negative)',f"{friday['pneg']:.1%}")
        st.markdown('<div class="success"><b>Interpretation:</b> Known downside remains within anticipated response capacity.</div>',unsafe_allow_html=True); jump_button('Meet Meridian Components →',4)
elif page=='Organization Map':
    hero('ORGANIZATIONAL CONTEXT','One treasury function. Six entities. No common reporting system.','Different functions, currencies, and constraints feed one central inbox.')
    a,b,c=st.columns(3)
    a.markdown('<div class="panel"><div class="eyebrow">SOURCES</div><div class="row">Corporate Controller</div><div class="row">Manufacturing Finance</div><div class="row">Acquisition Controller</div><div class="row">Shared Services</div><div class="row">International Controllers</div><div class="row">AR Operations + Bank Partner</div></div>',unsafe_allow_html=True)
    b.markdown('<div class="panel"><div class="eyebrow">ENTITIES</div><div class="row">Meridian Holdings</div><div class="row">Meridian Manufacturing</div><div class="row">Apex Distribution</div><div class="row">Gulf Components</div><div class="row">Meridian Canada</div><div class="row">Meridian Europe</div></div>',unsafe_allow_html=True)
    c.markdown('<div class="panel"><div class="eyebrow">CENTRAL TREASURY</div><h3>Treasury Team of One</h3><div class="row">8 messages</div><div class="row">10 attachments</div><div class="row">USD / CAD / EUR</div><div class="row">Central and local facilities</div><div class="warn">Agents connect fragmented evidence to one governed decision.</div></div>',unsafe_allow_html=True); jump_button('Open Monday inbox →',5)
elif page=='Monday Inbox':
    hero('T0 | MONDAY 8:03 AM','The agents retrieve current evidence','No upload. The staged inbox preserves message context and file versions.')
    inbox=json.loads(INBOX_JSON.read_text()); l,r=st.columns([1.7,1])
    with l:
        for m in inbox: st.markdown(f'<div class="panel" style="margin-bottom:.25rem"><div class="row"><span class="badge">{m["time"]}</span><b>{m["subject"]}</b><span class="grow"></span>{len(m["attachments"])} file</div><div class="muted">{m["sender"]} | {m["entity"]} | {", ".join(m["attachments"])}</div></div>',unsafe_allow_html=True)
    with r: st.metric('Messages',10); st.metric('Attachments',12); st.metric('Revisions',4); jump_button('Authorize retrieval →',6)
elif page=='Agent Operations':
    hero('AGENT RUN 08-A','Watch the agents build the evidence pipeline','Advance the console one controlled step at a time. Each agent produces an artifact that becomes input to the next agent.')
    steps=[
        ('Inbox Agent','Linked 8 messages to 10 attachments','message_attachment_register.csv'),
        ('Version Agent','Selected Gulf_Cash_Fcst_v2.xlsx; marked original as superseded','version_decisions.csv'),
        ('Document Agent','Detected 12 sheets, horizontal dates, currencies, and worksheet notes','file_profile.csv'),
        ('Mapping Agent','Proposed 27 raw-to-canonical mappings; 5 require review','schema_mapping.csv'),
        ('Reconciliation Agent','Surfaced 6 material exceptions with financial impact','exception_register.csv'),
        ('Risk Agent','Paused forecast refresh until treasury approves material treatments','assumption_change_ledger.csv')]
    completed=min(st.session_state.agent_step,len(steps))
    m1,m2,m3,m4=st.columns(4); m1.metric('Attachments connected',10 if completed>0 else 0); m2.metric('Structures interpreted',7 if completed>2 else 0); m3.metric('Mappings proposed',27 if completed>3 else 0); m4.metric('Material reviews',6 if completed>4 else 0)
    left,right=st.columns([1.18,1],gap='large')
    with left:
        st.markdown('### Agent activity console')
        console=[]
        times=['08:08:03','08:08:07','08:08:12','08:08:18','08:08:24','08:08:31']
        for idx,(name,action,artifact) in enumerate(steps):
            state='COMPLETE' if idx<completed else ('READY' if idx==completed else 'WAITING')
            console.append([times[idx],name,action,artifact,state])
        st.dataframe(pd.DataFrame(console,columns=['Time','Agent','Observable work','Produced artifact','State']),use_container_width=True,hide_index=True,height=255)
        a,b=st.columns(2)
        if completed<len(steps):
            if a.button('Run next agent step →',type='primary',use_container_width=True): st.session_state.agent_step+=1; st.rerun()
            if b.button('Run all remaining',use_container_width=True): st.session_state.agent_step=len(steps); st.rerun()
        else:
            st.markdown('<div class="success"><b>Agent run complete:</b> The Risk Agent is waiting for treasury approval of material exceptions.</div>',unsafe_allow_html=True)
    with right:
        st.markdown('### Raw → interpreted → proposed')
        raw,interpreted,proposed=st.tabs(['Raw','Agent interpretation','Proposed record'])
        with raw:
            st.code('''File: Gulf_Cash_Fcst_v2.xlsx
Entity: Gulf Comp.
Cash In: 620000
Day: Wed
Note: Orion confirmation pending''')
        with interpreted:
            st.markdown('<div class="panel"><div class="row">Entity <span class="grow"></span><b>Gulf Components</b></div><div class="row">Flow <span class="grow"></span><b>Customer receipt</b></div><div class="row">Customer <span class="grow"></span><b>Orion Automotive</b></div><div class="row">Confidence <span class="grow"></span><b>96%</b></div><div class="row">Trigger <span class="grow"></span><b>Timing conflict</b></div></div>',unsafe_allow_html=True)
        with proposed:
            st.markdown('<div class="panel"><div class="row">Amount <span class="grow"></span><b>$620,000</b></div><div class="row">Settlement date <span class="grow"></span><b>Probabilistic</b></div><div class="row">Materiality <span class="grow"></span><b>High</b></div><div class="row">Status <span class="grow"></span><b style="color:#F4AB00">AWAITING TREASURY</b></div></div>',unsafe_allow_html=True)
        with st.expander('Agent permissions and boundaries'):
            p1,p2=st.columns(2)
            p1.markdown('''**Agents may**

✓ Retrieve and classify

✓ Parse and normalize

✓ Identify inconsistencies

✓ Propose treatments

✓ Rerun approved scenarios''')
            p2.markdown('''**Agents may not**

✕ Approve corrections

✕ Move cash

✕ Draw facilities

✕ Release payments

✕ Override policy''')
    if completed==len(steps): jump_button('Open human control gate →',7)
elif page=='Human Review':
    hero('HUMAN CONTROL GATE','Agents propose. Treasury decides.','Every material correction remains traceable to source evidence.')
    issues=[('Duplicate Holdings balance','$2.45M','Retain one record'),('Reserve unit anomaly','Material','Correct and exclude restricted cash'),('Orion timing','$620K','Model settlement as a distribution'),('Duplicate payroll','$245K','Retain one verified payment'),('Facility mismatch','$50K','Recalculate availability'),('FX inconsistencies','Review','Use approved feed')]
    i=min(st.session_state.reviewed,7); x=issues[i]; st.markdown(f'<div class="panel"><div class="eyebrow">REVIEW {i+1} OF 6</div><h3>{x[0]}</h3><p><b>Impact:</b> {x[1]} | <b>Proposal:</b> {x[2]}</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    if a.button('Accept',type='primary',use_container_width=True): st.session_state.reviewed=min(6,i+1); st.session_state.inspect=False; st.rerun()
    if b.button('Defer',use_container_width=True): st.session_state.reviewed=min(6,i+1); st.session_state.inspect=False; st.rerun()
    if c.button('Inspect evidence',use_container_width=True): st.session_state.inspect=not st.session_state.inspect
    if st.session_state.inspect:
        e=EVIDENCE[i]; st.markdown(f'<div class="panel"><div class="eyebrow">SOURCE EVIDENCE</div><div class="row"><b>Entity</b><span class="grow"></span>{e[0]}</div><div class="row"><b>Sender</b><span class="grow"></span>{e[1]}</div><div class="row"><b>Attachment</b><span class="grow"></span>{e[2]}</div><p><b>Raw:</b> {e[3]}</p><p><b>Finding:</b> {e[4]} | <b>Confidence:</b> {e[5]} | <b>Impact:</b> {e[6]}</p></div>',unsafe_allow_html=True)
    accepted=st.session_state.reviewed
    h1,h2,h3,h4=st.columns(4); h1.metric('Approved for model',accepted); h2.metric('Deferred',0); h3.metric('Rejected',0); h4.metric('Unresolved',max(0,6-accepted))
    handoff=['DETECTED','PROPOSED','AWAITING TREASURY','APPROVED','RELEASED TO MODEL']
    active=3 if accepted<4 else 4
    st.markdown('<div class="panel"><div class="eyebrow">HUMAN HANDOFF</div><div class="row">'+''.join(f'<span class="badge" style="opacity:{1 if j<=active else .35}">{label}</span>' for j,label in enumerate(handoff))+'</div></div>',unsafe_allow_html=True)
    st.progress(st.session_state.reviewed/6)
    if st.session_state.reviewed>=4: jump_button('Release approved truth set →',8)
elif page=='The Storm':
    stage=st.session_state.storm; r=simulate(hist,stage); prev=friday if stage==0 else simulate(hist,stage-1); e=STORM_EVIDENCE[stage]
    hero(f'STORM {stage+1} OF 5',e[1],'New evidence changes the assumptions behind Friday’s 95% forecast.')
    assumption_rows=[['Opening cash','$620K','$595K','Revised Gulf forecast','Expected cash'],['Orion on-time probability','72%','18%','AR history + email','Uncertainty'],['Additional Sep 4 payment','$0','$90K','Disbursement file','Expected cash'],['Local line','$100K','$50K','Facility reconciliation','Funding capacity'],['Parent/restricted cash','Assumed available','Approval required','Policy + facilities','Accessibility']]
    with st.expander('Assumption change ledger',expanded=False): st.dataframe(pd.DataFrame(assumption_rows[:stage+1],columns=['Parameter','Friday','Current','Evidence','Effect']),use_container_width=True,hide_index=True)
    l,side=st.columns([2.05,1.15])
    with l:
        st.plotly_chart(fan(r,'Friday baseline vs. current risk',friday,events=True),use_container_width=True)
        a,b,c,d=st.columns(4); a.metric('VaR 95%',money(r['var']),delta=money(r['var']-prev['var'])); b.metric('CVaR 95%',money(r['cvar']),delta=money(r['cvar']-prev['cvar'])); c.metric('P(Below $200K)',f"{r['pmin']:.1%}",delta=f"{r['pmin']-prev['pmin']:+.1%}"); d.metric('P(Negative)',f"{r['pneg']:.1%}",delta=f"{r['pneg']-prev['pneg']:+.1%}")
    with side:
        st.markdown(f'<div class="panel"><span class="badge">{e[0]}</span><h3>{e[1]}</h3><div class="row"><b>Email</b><span class="grow"></span>{e[2]}</div><div class="row"><b>File</b><span class="grow"></span>{e[3]}</div><p><b>Observed</b><br>{e[4]}</p><p><b>Model update</b><br>{e[5]}</p><p><b>Decision implication</b><br>{e[6]}</p></div>',unsafe_allow_html=True)
        if stage<4:
            if st.button('Release next event →',type='primary',use_container_width=True): st.session_state.storm+=1; st.rerun()
        else: jump_button('Reveal the dilemma →',9)
elif page=='Dilemma':
    r=simulate(hist,6); hero('AUDIENCE DECISION','What would you recommend before the 9:30 briefing?','Choose first. Then the simulation reveals the residual risk and control implications.')
    st.plotly_chart(fan(r,'Pre-response distribution',friday,events=True),use_container_width=True)
    options=['Rely on receipt','Local line','Intercompany transfer','Layered response']; cols=st.columns(4)
    for col,opt in zip(cols,options):
        if col.button(opt,use_container_width=True,type='primary' if st.session_state.audience_choice==opt else 'secondary'): st.session_state.audience_choice=opt; st.rerun()
    st.markdown(f'<div class="warn"><b>Audience recommendation:</b> {st.session_state.audience_choice}. The next screen tests whether that response controls the tail.</div>',unsafe_allow_html=True); jump_button('Test the audience recommendation →',10)
elif page=='Response Studio':
    mapf={'Rely on receipt':0,'No action':0,'Local line':50000,'Intercompany transfer':500000,'Layered response':550000}; choice=st.session_state.audience_choice; funding=mapf.get(choice,0); st.session_state.funding=funding; r=simulate(hist,4,funding=funding)
    hero('RESPONSE STUDIO',f'Testing: {choice}','A good response balances protection, accessibility, approval, and residual tail risk.')
    l,side=st.columns([2.05,1.15]); l.plotly_chart(fan(r,f'Post-response: {choice}',friday,events=True),use_container_width=True)
    with side:
        st.metric('Funding action',money(funding)); st.metric('P(Negative)',f"{r['pneg']:.1%}")
        rationale={'Rely on receipt':('No funding cost','Timing risk remains','None','Not recommended'), 'Local line':('Local and accessible','Insufficient tail protection','Facility rules','Partial response'), 'Intercompany transfer':('Restores material liquidity','Requires approval','CFO/authorized approver','Viable'), 'Layered response':('Uses local capacity and preserves flexibility','More coordination','Multiple controls','Recommended')}[choice]
        st.markdown(f'<div class="panel"><div class="eyebrow">RESPONSE RATIONALE</div><p><b>Benefit:</b> {rationale[0]}</p><p><b>Limitation:</b> {rationale[1]}</p><p><b>Approval:</b> {rationale[2]}</p><p><b>Assessment:</b> {rationale[3]}</p></div>',unsafe_allow_html=True)
        if choice=='Local line': st.markdown('<div class="danger"><b>Insufficient:</b> Funding helps, but the local line does not restore the policy cushion across the 95% distribution.</div>',unsafe_allow_html=True)
        jump_button('Create CFO decision brief →',11)
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
        jump_button('Open audit & outputs →',12)
else:
    hero('9:30 AM','From fragmented evidence to a controlled decision','The value is adaptation: source traceability, agent speed, human judgment, and probabilistic response.')
    a,b,c=st.columns(3)
    a.markdown('<div class="panel"><div class="eyebrow">BEFORE AGENTS</div><div class="row">8 messages</div><div class="row">10 attachments</div><div class="row">No common schema</div><div class="row">Apparently adequate cash</div></div>',unsafe_allow_html=True)
    b.markdown('<div class="panel"><div class="eyebrow">WHAT CHANGED</div><div class="row">Duplicates isolated</div><div class="row">Restricted cash excluded</div><div class="row">Timing made probabilistic</div><div class="row">Tail exposure quantified</div></div>',unsafe_allow_html=True)
    c.markdown(f'<div class="panel"><div class="eyebrow">DECISION PRODUCED</div><div class="row">Response: {st.session_state.audience_choice}</div><div class="row">Funding: {money(st.session_state.funding)}</div><div class="row">Approval required</div><div class="row">Audit trail preserved</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="success"><b>Friday’s model was not wrong. Monday’s evidence changed the assumptions. The advantage was not perfect prediction. It was the ability to adapt before uncertainty became a liquidity crisis.</b></div>',unsafe_allow_html=True)
    st.markdown('### Observable agent work produced')
    w1,w2,w3,w4=st.columns(4); w1.metric('Messages connected',10); w2.metric('Attachments processed',12); w3.metric('Mappings proposed',27); w4.metric('Material exceptions',8)
    r=simulate(hist,4,funding=st.session_state.funding); out=pd.DataFrame({'date':DATES,'expected_cash':r['mean'],'p2_5':r['p025'],'p25':r['p25'],'p75':r['p75'],'p97_5':r['p975']}); mem=io.BytesIO()
    mapping=pd.DataFrame([['Gulf Comp.','Gulf Components','96%','Review'],['Orion Auto','Orion Automotive','96%','Review'],['Cash In','Customer receipt','99%','Approved'],['US$','USD','100%','Approved']],columns=['Raw value','Canonical value','Confidence','Status'])
    decisions=pd.DataFrame([['Duplicate balance','Retain one record','Approved'],['Reserve anomaly','Exclude restricted cash','Approved'],['Orion timing','Use probability distribution','Approved'],['Facility availability','Use $50K','Approved']],columns=['Issue','Treatment','Decision'])
    ledger=pd.DataFrame([['Opening cash','$620K','$595K','Gulf revised forecast'],['Orion on-time probability','72%','18%','AR history + email'],['Additional payment','$0','$90K','Disbursement file'],['Local line','$100K','$50K','Facility reconciliation']],columns=['Parameter','Friday','Monday','Evidence'])
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('01_message_attachment_register.csv',pd.DataFrame(json.loads(INBOX_JSON.read_text())).to_csv(index=False))
        z.writestr('02_attachment_profile.csv',process_inbox(INBOX).to_csv(index=False))
        z.writestr('03_schema_mapping.csv',mapping.to_csv(index=False))
        z.writestr('04_human_decisions.csv',decisions.to_csv(index=False))
        z.writestr('05_assumption_change_ledger.csv',ledger.to_csv(index=False))
        z.writestr('06_forecast_percentiles.csv',out.to_csv(index=False))
        z.writestr('07_response_comparison.csv',compare_responses(hist).to_csv(index=False))
        z.writestr('08_cfo_decision_brief.txt',f'Response: {st.session_state.audience_choice}\nFunding: {money(st.session_state.funding)}\nConfidence: 95%\nHorizon: 10 days\n')
    st.download_button('Download decision package',mem.getvalue(),file_name='Treasury_Agent_Outputs.zip',type='primary',use_container_width=True)
