from pathlib import Path
import io
import json
import zipfile

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import DATES, MINIMUM, STORMS, load_history, simulate, process_inbox, compare_responses

st.set_page_config(page_title='Treasury Agent Operations', page_icon='◈', layout='wide')
BASE = Path(__file__).parent

def first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return paths[0]

SAMPLE = first_existing(BASE/'data'/'historical_forecast_errors.csv', BASE/'historical_forecast_errors.csv')
INBOX = first_existing(BASE/'data'/'monday_inbox', BASE)
INBOX_JSON = first_existing(BASE/'data'/'inbox.json', BASE/'inbox.json')
C = {'navy':'#081F33','cyan':'#00BAC6','amber':'#F4AB00','red':'#D63F42','green':'#15836D','bg':'#EDF3F7'}

st.markdown(f'''<style>
.stApp{{background:{C['bg']}}}.block-container{{padding:.55rem 1.15rem 1rem;max-width:1550px}}
[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] *{{color:#F1F7FA!important}}
header[data-testid="stHeader"]{{height:2rem}}
.hero{{background:linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:15px;padding:.7rem 1rem;margin-bottom:.45rem}}
.hero h1{{font-size:1.58rem;margin:.08rem 0}}.hero p{{font-size:.86rem;color:#D8E8EF;margin:0}}
.eyebrow{{font-size:.62rem;letter-spacing:.12em;color:#43E6ED;font-weight:800;text-transform:uppercase}}
.panel{{background:white;border:1px solid #D5E1E8;border-radius:13px;padding:.72rem .85rem;box-shadow:0 3px 10px rgba(8,31,51,.06)}}
.row{{display:flex;gap:.5rem;align-items:center;border-bottom:1px solid #E7EEF2;padding:.36rem 0;font-size:.84rem}}
.grow{{flex:1}}.muted{{font-size:.75rem;color:#687C8E}}.badge{{font-size:.64rem;font-weight:800;border-radius:999px;padding:.12rem .4rem;background:#DFF7F7;color:#087680}}
.warn{{background:#FFF7E3;border-left:4px solid #F4AB00;padding:.5rem .7rem;border-radius:9px;font-size:.82rem}}
.danger{{background:#FFF0F0;border-left:4px solid #D63F42;padding:.5rem .7rem;border-radius:9px;font-size:.82rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.4rem .65rem}}
div[data-testid="stMetricLabel"]{{font-size:.72rem}}div[data-testid="stMetricValue"]{{font-size:1.25rem}}
.stButton>button{{min-height:35px;border-radius:9px;font-weight:800}}h3{{margin:.3rem 0!important;font-size:1.05rem!important}}
</style>''', unsafe_allow_html=True)

for key, value in {'page':0,'hist':None,'storm':0,'reviewed':0,'funding':0,'inspect_evidence':False}.items():
    st.session_state.setdefault(key, value)

def hero(kicker, title, subtitle):
    st.markdown(f'<div class="hero"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def money(value):
    return f'${abs(value)/1e6:.2f}M' if abs(value) >= 1e6 else f'${abs(value):,.0f}'

def fan(result, title, prior=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=DATES, y=result['p975'], line_width=0, showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=DATES, y=result['p025'], fill='tonexty', fillcolor='rgba(0,186,198,.11)', line_width=0, name='95% range'))
    fig.add_trace(go.Scatter(x=DATES, y=result['p75'], line_width=0, showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=DATES, y=result['p25'], fill='tonexty', fillcolor='rgba(0,186,198,.24)', line_width=0, name='50% range'))
    fig.add_trace(go.Scatter(x=DATES, y=result['mean'], line=dict(color=C['cyan'], width=4), mode='lines+markers', name='Current expected'))
    if prior is not None:
        fig.add_trace(go.Scatter(x=DATES, y=prior['mean'], line=dict(color='#7D8D99', dash='dot', width=2), name='Friday expected'))
    fig.add_hline(y=MINIMUM, line_color=C['amber'], line_dash='dash')
    fig.add_hline(y=0, line_color=C['red'], line_width=2)
    fig.update_layout(title=title, height=340, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified', legend_orientation='h', margin=dict(l=18,r=12,t=40,b=12), yaxis_tickprefix='$', yaxis_tickformat=',.0f')
    return fig

STORM_EVIDENCE = [
    {
        'title':'Opening cash revised',
        'email':'Updated forecast, use version 2',
        'attachment':'Gulf_Cash_Fcst_v2.xlsx',
        'raw':'Revised Gulf opening cash is $25,000 below the Friday baseline.',
        'model_change':'Opening cash shift: −$25,000; forecast-error volatility: 0.62× → 1.05×.',
        'cash_effect':'Direct expected-path effect: −$25,000 on every forecast date.',
        'uncertainty_effect':'The 50% and 95% bands widen because opening-position confidence declined.'
    },
    {
        'title':'Orion timing challenged',
        'email':'Orion timing remains unconfirmed',
        'attachment':'AR_Expectations.xlsx',
        'raw':'The $620,000 Orion receipt is expected September 2, but the file shows a five-day average delay and a duplicate invoice candidate.',
        'model_change':'Receipt-date probabilities changed from 72% / 20% / 7% / 1% to 18% / 37% / 32% / 13% across Sep 2, Sep 4, Sep 8, and outside the horizon.',
        'cash_effect':'No change to receipt amount; expected receipt timing moves later.',
        'uncertainty_effect':'The path shifts downward before settlement and develops a larger left tail.'
    },
    {
        'title':'Payments concentrate',
        'email':'AP and payroll schedule',
        'attachment':'Apex_Disbursements.csv',
        'raw':'Current evidence places an additional $90,000 payment on September 4 while payroll and supplier obligations already cluster early in the horizon.',
        'model_change':'September 4 cash flow: −$90,000; forecast-error volatility: 1.15× → 1.25×.',
        'cash_effect':'Direct expected-path effect: −$90,000 from September 4 forward.',
        'uncertainty_effect':'The lower 95% band approaches or crosses zero because payment timing is concentrated before the uncertain receipt.'
    },
    {
        'title':'Local line corrected',
        'email':'Facility availability',
        'attachment':'Facilities.xlsx',
        'raw':'Commitment is $500,000 and amount drawn is $450,000; reported availability of $100,000 does not reconcile.',
        'model_change':'Immediately available local capacity: $100,000 → $50,000.',
        'cash_effect':'The pre-funding expected cash path does not move; response capacity falls by $50,000.',
        'uncertainty_effect':'Residual exposure after using the local line increases by $50,000. This event changes the safety net, not the underlying forecast.'
    },
    {
        'title':'Transfer access constrained',
        'email':'Forecast and restricted reserve',
        'attachment':'Europe_Reserve.csv + Facilities.xlsx',
        'raw':'European reserve cash is restricted, the central revolver belongs to Holdings, and intercompany support requires authorization.',
        'model_change':'Unapproved parent and restricted liquidity are excluded from immediately available funding; volatility: 1.28× → 1.38×.',
        'cash_effect':'No automatic cash injection is added to Gulf Components.',
        'uncertainty_effect':'The actionable tail remains exposed until treasury selects and obtains approval for a funding response.'
    },
]

EVIDENCE = [
    {'email':'Friday balances, revised file may follow','attachment':'Holdings_Balances.csv','raw':'Accounts 00100442 and 100442 report the same $2.45 million balance.','finding':'Likely duplicate after restoring leading zeros and mapping the entity alias.','confidence':'98%','impact':'$2.45 million potential cash overstatement'},
    {'email':'Forecast and restricted reserve','attachment':'Europe_Reserve.csv','raw':'Account EU7799 reports 42,500,000 EUR and is identified as restricted.','finding':'Likely cents-versus-units anomaly; the account cannot be treated as available liquidity.','confidence':'94%','impact':'Material overstatement of available cash'},
    {'email':'Orion timing remains unconfirmed','attachment':'AR_Expectations.xlsx','raw':'INV-8812 appears twice; expected receipt is September 2; average delay is five days.','finding':'Duplicate receivable and optimistic settlement assumption.','confidence':'96%','impact':'$620,000 timing dependency'},
    {'email':'AP and payroll schedule','attachment':'Apex_Disbursements.csv','raw':'Gulf payroll of $245,000 appears under two entity name variations.','finding':'Potential duplicate payroll record.','confidence':'97%','impact':'$245,000 potential outflow duplication'},
    {'email':'Facility availability','attachment':'Facilities.xlsx','raw':'Commitment is $500,000, amount drawn is $450,000, and reported availability is $100,000.','finding':'Arithmetic availability is $50,000.','confidence':'100%','impact':'$50,000 liquidity overstatement'},
    {'email':'CAD forecast using Friday FX','attachment':'Canada_CAD.xlsx','raw':'The entity forecast uses a 0.742 conversion rate.','finding':'The entity rate should be compared with the approved treasury rate.','confidence':'91%','impact':'Potential translation variance'},
]

def find_attachment(name):
    candidates = [INBOX/name, BASE/'data'/'monday_inbox'/name, BASE/name]
    return first_existing(*candidates)

pages = ['Historical Baseline','Friday Snapshot','Organization Map','Monday Inbox','Agent Operations','Human Review','The Storm','Dilemma','Response Studio','CFO Brief','Audit & Downloads']
if not isinstance(st.session_state.page, int) or not 0 <= st.session_state.page < len(pages):
    st.session_state.page = 0
with st.sidebar:
    st.markdown('## ◈ Treasury Agent Operations')
    st.caption('GitHub data loads automatically. Monday agents take over.')
    page = st.radio('Narrative', pages, index=st.session_state.page)
    st.markdown('---')
    st.caption('Synthetic evidence. Reproducible simulation. No transaction execution.')

if st.session_state.hist is None:
    try:
        st.session_state.hist = load_history(SAMPLE)
    except Exception as exc:
        st.error(f'Historical data could not be loaded from {SAMPLE}: {exc}')
        st.stop()

hist = st.session_state.hist
friday = simulate(hist, -1)

if page == 'Historical Baseline':
    hero('T−2 | BEFORE MONDAY','Historical forecast performance loaded','The Risk Agent automatically reads the historical forecast-error file stored with the GitHub application.')
    left, right = st.columns([1.55,1], gap='large')
    with left:
        st.markdown(f'<div class="panel"><div class="eyebrow">AUTOMATIC DATA SOURCE</div><h3>{SAMPLE.name}</h3><p>The file is versioned with the application and loaded when Streamlit starts.</p><div class="row"><span>Load status</span><span class="grow"></span><b style="color:#15836D">READY</b></div><div class="row"><span>Current observations</span><span class="grow"></span><b>{len(hist)}</b></div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="eyebrow">FIELDS DETECTED</div><div class="row"><b>date</b><span class="grow"></span><span>observation date</span></div><div class="row"><b>opening_error</b><span class="grow"></span><span>opening variance</span></div><div class="row"><b>receipt_error</b><span class="grow"></span><span>receipt variance</span></div><div class="row"><b>disbursement_error</b><span class="grow"></span><span>payment variance</span></div></div>', unsafe_allow_html=True)
    a,b,c = st.columns(3); a.metric('Observations',len(hist)); b.metric('Beginning',hist.date.min().strftime('%b %Y')); c.metric('Ending',hist.date.max().strftime('%b %Y'))
    if st.button('Build Friday risk baseline →', type='primary', use_container_width=True): st.session_state.page=1; st.rerun()

elif page == 'Friday Snapshot':
    hero('T−1 | FRIDAY 4:30 PM','A manageable 95% risk baseline','Historical variance becomes a ten-day probabilistic cash forecast before Monday evidence arrives.')
    left,right=st.columns([2.25,1],gap='large')
    with left: st.plotly_chart(fan(friday,'Friday cash distribution'),use_container_width=True)
    with right:
        a,b=st.columns(2); a.metric('VaR 95%',money(friday['var'])); b.metric('CVaR 95%',money(friday['cvar']))
        c,d=st.columns(2); c.metric('P(Below Min)',f"{friday['pmin']:.1%}"); d.metric('P(Negative)',f"{friday['pneg']:.1%}")
        if st.button('Meet Meridian Components →',type='primary',use_container_width=True): st.session_state.page=2; st.rerun()

elif page == 'Organization Map':
    hero('ORGANIZATIONAL CONTEXT','One Treasury Function. Six Entities. No Common Reporting System.','The audience can see who produces each file, which entity it represents, and why central treasury needs agents.')
    left, center, right = st.columns([1.05,1.2,1.15], gap='large')
    with left:
        st.markdown('<div class="panel"><div class="eyebrow">INFORMATION SOURCES</div><div class="row"><b>Corporate Controller</b><span class="grow"></span><span>Balances</span></div><div class="row"><b>Manufacturing Finance</b><span class="grow"></span><span>Forecast</span></div><div class="row"><b>Acquisition Controller</b><span class="grow"></span><span>Gulf forecast</span></div><div class="row"><b>Shared Services</b><span class="grow"></span><span>AP + payroll</span></div><div class="row"><b>International Controllers</b><span class="grow"></span><span>CAD + EUR</span></div><div class="row"><b>AR Operations</b><span class="grow"></span><span>Receipts</span></div><div class="row"><b>Bank Partner</b><span class="grow"></span><span>Facilities</span></div></div>', unsafe_allow_html=True)
    with center:
        st.markdown('<div class="panel"><div class="eyebrow">MERIDIAN COMPONENTS GROUP</div><h3>Six-entity liquidity network</h3><div class="row"><span>Meridian Holdings</span><span class="grow"></span><span class="badge">CORPORATE</span></div><div class="row"><span>Meridian Manufacturing</span><span class="grow"></span><span class="badge">CORE</span></div><div class="row"><span>Apex Distribution</span><span class="grow"></span><span class="badge">ACQUIRED</span></div><div class="row"><span>Gulf Components</span><span class="grow"></span><span class="badge">ACQUIRED</span></div><div class="row"><span>Meridian Canada</span><span class="grow"></span><span class="badge">CAD</span></div><div class="row"><span>Meridian Europe</span><span class="grow"></span><span class="badge">EUR</span></div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="eyebrow">CENTRAL TREASURY</div><h3>Treasury Team of One</h3><div class="row"><span>Central inbox</span><span class="grow"></span><b>8 messages</b></div><div class="row"><span>Attachments</span><span class="grow"></span><b>10 files</b></div><div class="row"><span>Currencies</span><span class="grow"></span><b>USD / CAD / EUR</b></div><div class="row"><span>Central revolver</span><span class="grow"></span><b>Holdings</b></div><div class="row"><span>Local Gulf line</span><span class="grow"></span><b>$50K</b></div><br><div class="warn"><b>Why agents matter:</b> different senders use different systems, definitions, timing assumptions, and formats.</div></div>', unsafe_allow_html=True)
    flow = pd.DataFrame([
        ['Corporate Controller','Meridian Holdings','Holdings_Balances.csv','USD'],
        ['Manufacturing Finance','Meridian Manufacturing','Mfg_Weekly_View.xlsx','USD'],
        ['Acquisition Controller','Gulf Components','Gulf_Cash_Fcst.xlsx + v2','USD'],
        ['Shared Services','Apex + Gulf','Apex_Disbursements.csv','USD'],
        ['Canada Controller','Meridian Canada','Canada_CAD.xlsx','CAD'],
        ['Europe Controller','Meridian Europe','Europe_EUR.xlsx + Reserve.csv','EUR'],
        ['AR Operations','Gulf Components','AR_Expectations.xlsx','USD'],
        ['Bank Partner','Corporate + Gulf','Facilities.xlsx','USD/EUR'],
    ], columns=['Sender function','Related entity','File sent','Currency'])
    st.dataframe(flow, use_container_width=True, hide_index=True, height=248)
    if st.button('Open Monday treasury inbox →', type='primary', use_container_width=True):
        st.session_state.page=3
        st.rerun()

elif page == 'Monday Inbox':
    hero('T0 | MONDAY 8:03 AM','The agents retrieve current evidence','No upload. The simulated Inbox Agent pulls messages and attachments from the staged treasury mailbox.')
    inbox=json.loads(INBOX_JSON.read_text()); left,right=st.columns([1.65,1],gap='large')
    with left:
        for m in inbox:
            st.markdown(f'<div class="panel" style="margin-bottom:.3rem"><div class="row"><span class="badge">{m["time"]}</span><b>{m["subject"]}</b><span class="grow"></span><span>{len(m["attachments"])} file</span></div><div class="muted">{m["sender"]} | {m["entity"]} | {", ".join(m["attachments"])}</div></div>',unsafe_allow_html=True)
    with right:
        st.metric('Messages',8); st.metric('Attachments',10); st.metric('Entities',6)
        if st.button('Authorize agent retrieval →',type='primary',use_container_width=True): st.session_state.page=4; st.rerun()

elif page == 'Agent Operations':
    hero('AGENT RUN 08-A','Watch current files become decision-ready data','Agents profile attachments, map fields, reconcile controls, and prepare the forecast refresh.')
    prof=process_inbox(INBOX); a,b,c,d=st.columns(4); a.metric('Files parsed',len(prof)); b.metric('Rows read',int(prof.rows.sum())); c.metric('Sheets opened',int(prof.sheets.sum())); d.metric('Warnings',6)
    left,right=st.columns([1.4,1],gap='large')
    with left: st.dataframe(prof[['file','type','sheets','rows','columns']],use_container_width=True,hide_index=True,height=255)
    with right:
        st.code('7:26  Revised Gulf file selected\n7:27  Horizontal layout parsed\n7:27  Note extracted: payroll excluded\n7:28  Duplicate balance: $2.45M impact\n7:28  Risk refresh paused for review')
        if st.button('Open human review →',type='primary',use_container_width=True): st.session_state.page=5; st.rerun()

elif page == 'Human Review':
    hero('HUMAN CONTROL GATE','Agents propose. Treasury decides.','Inspect underlying evidence before accepting any material treatment.')
    issues=[('Duplicate Holdings balance','$2.45M','Retain one record'),('Reserve unit anomaly','Material','Correct to €425K; exclude as restricted'),('Orion timing','$620K','Model settlement as a distribution'),('Duplicate payroll','$245K','Retain one verified payment'),('Facility mismatch','$50K','Recalculate commitment less drawn'),('FX inconsistencies','Review','Use approved feed')]
    i=min(st.session_state.reviewed,5); issue=issues[i]
    st.markdown(f'<div class="panel"><div class="eyebrow">REVIEW {i+1} OF 6</div><h3>{issue[0]}</h3><p><b>Impact:</b> {issue[1]} &nbsp; | &nbsp; <b>Agent proposal:</b> {issue[2]}</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    if a.button('Accept',type='primary',use_container_width=True):
        st.session_state.reviewed=min(6,st.session_state.reviewed+1); st.session_state.inspect_evidence=False; st.rerun()
    if b.button('Defer',use_container_width=True):
        st.session_state.reviewed=min(6,st.session_state.reviewed+1); st.session_state.inspect_evidence=False; st.rerun()
    if c.button('Inspect evidence',use_container_width=True):
        st.session_state.inspect_evidence=not st.session_state.inspect_evidence
    if st.session_state.inspect_evidence:
        ev=EVIDENCE[i]
        st.markdown(f'<div class="panel" style="margin-top:.45rem;border-left:4px solid #00BAC6"><div class="eyebrow">SOURCE EVIDENCE</div><div class="row"><b>Email</b><span class="grow"></span><span>{ev["email"]}</span></div><div class="row"><b>Attachment</b><span class="grow"></span><span>{ev["attachment"]}</span></div><div class="row"><b>Raw evidence</b><span class="grow"></span><span>{ev["raw"]}</span></div><div class="row"><b>Agent finding</b><span class="grow"></span><span>{ev["finding"]}</span></div><div class="row"><b>Confidence</b><span class="grow"></span><span>{ev["confidence"]}</span></div><div class="row"><b>Potential impact</b><span class="grow"></span><span style="color:#D63F42;font-weight:800">{ev["impact"]}</span></div></div>',unsafe_allow_html=True)
        source=find_attachment(ev['attachment'])
        if source.exists():
            try:
                preview=pd.read_csv(source) if source.suffix.lower()=='.csv' else pd.read_excel(source,engine='openpyxl')
                st.dataframe(preview,use_container_width=True,hide_index=True,height=145)
            except Exception as exc: st.warning(f'The source file was found but could not be previewed: {exc}')
        else: st.warning(f'Source attachment not found: {ev["attachment"]}')
    st.progress(st.session_state.reviewed/6)
    if st.session_state.reviewed>=4 and st.button('Release current data to Risk Agent →',type='primary',use_container_width=True): st.session_state.page=6; st.session_state.storm=0; st.rerun()

elif page == 'The Storm':
    stage=st.session_state.storm; name,*_=STORMS[stage]; result=simulate(hist,stage)
    hero(f'STORM {stage+1} OF 5',name,'New evidence revises the assumptions behind Friday’s 95% forecast.')
    previous = friday if stage == 0 else simulate(hist, stage-1)
    ev = STORM_EVIDENCE[stage]
    left,right=st.columns([2.05,1.15],gap='large')
    with left:
        st.plotly_chart(fan(result,'Friday baseline vs. current risk',friday),use_container_width=True)
        a,b,c,d=st.columns(4)
        a.metric('VaR 95%',money(result['var']),delta=money(result['var']-previous['var']))
        b.metric('CVaR 95%',money(result['cvar']),delta=money(result['cvar']-previous['cvar']))
        c.metric('P(Below)',f"{result['pmin']:.1%}",delta=f"{result['pmin']-previous['pmin']:+.1%}")
        d.metric('P(Negative)',f"{result['pneg']:.1%}",delta=f"{result['pneg']-previous['pneg']:+.1%}")
    with right:
        st.markdown(f'''<div class="panel" style="font-size:.88rem;line-height:1.35"><div class="eyebrow">EVIDENCE CAUSING THIS MOVE</div><h3 style="margin:.24rem 0 .4rem!important">{ev['title']}</h3><div class="row"><b>Email</b><span class="grow"></span><span>{ev['email']}</span></div><div class="row"><b>Attachment</b><span class="grow"></span><span>{ev['attachment']}</span></div><p style="margin:.55rem 0"><b>Observed</b><br>{ev['raw']}</p><p style="margin:.55rem 0"><b>Model update</b><br>{ev['model_change']}</p><p style="margin:.55rem 0"><b>Cash-path effect</b><br>{ev['cash_effect']}</p><p style="margin:.55rem 0 0"><b>Risk-band effect</b><br>{ev['uncertainty_effect']}</p></div>''',unsafe_allow_html=True)
        with st.expander('Stage-to-stage metric bridge'):
            bridge = pd.DataFrame([
                ['VaR 95%', previous['var'], result['var'], result['var']-previous['var']],
                ['CVaR 95%', previous['cvar'], result['cvar'], result['cvar']-previous['cvar']],
                ['P(Below Minimum)', previous['pmin'], result['pmin'], result['pmin']-previous['pmin']],
                ['P(Negative)', previous['pneg'], result['pneg'], result['pneg']-previous['pneg']],
            ], columns=['Metric','Before','After','Change'])
            st.dataframe(bridge,use_container_width=True,hide_index=True,height=176)
        if stage<4:
            if st.button('Release next event →',type='primary',use_container_width=True): st.session_state.storm+=1; st.rerun()
        elif st.button('Reveal liquidity dilemma →',type='primary',use_container_width=True): st.session_state.page=7; st.rerun()

elif page == 'Dilemma':
    result=simulate(hist,4); hero('DECISION POINT','Risk exceeds immediately available local capacity','The company has cash, but restrictions, timing, and approvals prevent frictionless access.')
    left,right=st.columns([2.2,1],gap='large')
    with left: st.plotly_chart(fan(result,'Pre-response liquidity distribution',friday),use_container_width=True)
    with right:
        st.metric('VaR 95%',money(result['var'])); st.metric('CVaR 95%',money(result['cvar'])); st.metric('Local line','$50K'); st.metric('P(Negative)',f"{result['pneg']:.1%}")
        if st.button('Compare responses →',type='primary',use_container_width=True): st.session_state.page=8; st.rerun()

elif page == 'Response Studio':
    hero('RESPONSE STUDIO','Manage the tail, not only the expected path','Every response reruns the simulation and updates the risk profile.')
    options={'No action':0,'Local line':50000,'Intercompany transfer':500000,'Layered response':550000}; choice=st.segmented_control('Response',list(options),default='No action') or 'No action'; funding=options[choice]; result=simulate(hist,4,funding=funding); st.session_state.funding=funding
    left,right=st.columns([2.15,1],gap='large')
    with left: st.plotly_chart(fan(result,f'Post-response: {choice}',friday),use_container_width=True)
    with right:
        st.metric('Funding',money(funding)); st.metric('P(Negative)',f"{result['pneg']:.1%}")
        st.dataframe(compare_responses(hist)[['Response','Funding','P(Negative)']],use_container_width=True,hide_index=True,height=175)
        if st.button('Create CFO brief →',type='primary',use_container_width=True): st.session_state.page=9; st.rerun()

elif page == 'CFO Brief':
    funding=st.session_state.funding; result=simulate(hist,4,funding=funding); hero('9:30 AM','A governed liquidity decision','Evidence, transformations, probabilities, and the response are decision-ready.')
    st.markdown(f'<div class="panel"><h3>Gulf Components liquidity exposure</h3><p><b>Situation:</b> Current P(Negative) is {result["pneg"]:.1%}; 95% expected tail shortfall is {money(result["cvar"])}.</p><p><b>Driver:</b> The $620,000 Orion receipt may settle after payroll and supplier obligations.</p><p><b>Constraint:</b> Local capacity is $50,000; additional liquidity requires authorization.</p><p><b>Selected funding:</b> {money(funding)}.</p></div>',unsafe_allow_html=True)
    if st.button('Open audit and downloads →',type='primary'): st.session_state.page=10; st.rerun()

else:
    hero('AUDIT & OUTPUTS','Download what the agents produced','Forecasts, response comparison, attachment profiles, and the source trail remain available.')
    result=simulate(hist,4,funding=st.session_state.funding); output=pd.DataFrame({'date':DATES,'expected_cash':result['mean'],'p2_5':result['p025'],'p25':result['p25'],'p75':result['p75'],'p97_5':result['p975']})
    st.dataframe(output,use_container_width=True,hide_index=True,height=250)
    package=io.BytesIO()
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('forecast_percentiles.csv',output.to_csv(index=False)); z.writestr('response_comparison.csv',compare_responses(hist).to_csv(index=False)); z.writestr('attachment_profile.csv',process_inbox(INBOX).to_csv(index=False))
    st.download_button('Download agent output package',package.getvalue(),file_name='Treasury_Agent_Outputs.zip',type='primary')
    if st.button('Reset demonstration'): st.session_state.clear(); st.rerun()
