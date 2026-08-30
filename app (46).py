from pathlib import Path
import io, json, zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import DATES, MINIMUM, STORMS, load_history, simulate, process_inbox, compare_responses

st.set_page_config(page_title='The Treasury Team of One',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
BASE=Path(__file__).parent
def first_existing(*paths): return next((p for p in paths if p.exists()),paths[0])
SAMPLE=first_existing(BASE/'data'/'historical_forecast_errors.csv',BASE/'historical_forecast_errors.csv')
INBOX=first_existing(BASE/'data'/'monday_inbox',BASE)
INBOX_JSON=first_existing(BASE/'data'/'inbox.json',BASE/'inbox.json')
C={'navy':'#081F33','cyan':'#00BAC6','amber':'#F4AB00','red':'#D63F42','green':'#15836D','bg':'#EDF3F7'}

st.markdown(f'''<style>
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{{display:none!important}}.stApp{{background:{C['bg']}}}.block-container{{padding:1rem 1.05rem .9rem;max-width:1550px}}[data-testid="stSidebar"]{{background:#081F33}}[data-testid="stSidebar"] p,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{{color:#F1F7FA!important}}
.hero{{background:linear-gradient(120deg,#081F33,#145E7C);color:white;border-radius:14px;padding:.64rem .95rem;margin-bottom:.4rem}}.hero h1{{font-size:1.48rem;margin:.06rem 0}}.hero p{{font-size:.82rem;color:#D8E8EF;margin:0}}.eyebrow{{font-size:.6rem;letter-spacing:.12em;color:#43E6ED;font-weight:800;text-transform:uppercase}}.panel{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.68rem .8rem;box-shadow:0 3px 10px rgba(8,31,51,.06)}}.row{{display:flex;gap:.45rem;align-items:center;border-bottom:1px solid #E7EEF2;padding:.32rem 0;font-size:.81rem}}.grow{{flex:1}}.muted{{font-size:.73rem;color:#687C8E}}.badge{{font-size:.61rem;font-weight:800;border-radius:999px;padding:.1rem .38rem;background:#DFF7F7;color:#087680}}.warn{{background:#FFF7E3;border-left:4px solid #F4AB00;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.danger{{background:#FFF0F0;border-left:4px solid #D63F42;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}.success{{background:#EAF8F4;border-left:4px solid #15836D;padding:.48rem .65rem;border-radius:9px;font-size:.8rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #D5E1E8;border-radius:11px;padding:.36rem .56rem}}div[data-testid="stMetricLabel"]{{font-size:.68rem}}div[data-testid="stMetricValue"]{{font-size:1.16rem}}.stButton>button{{min-height:34px;border-radius:9px;font-weight:800}}.stButton>button[kind="primary"]{{background:#00A6B2!important;border-color:#00A6B2!important;color:#fff!important}}[data-testid="stSidebar"] .stButton>button{{background:#F8FAFC!important;color:#17324A!important}}[data-testid="stSidebar"] .stButton>button p{{color:#17324A!important}}
.clockbar{{display:grid;grid-template-columns:150px minmax(260px,1fr) 150px;align-items:center;gap:.85rem;background:#0B2C43;border:1px solid #164D68;border-radius:11px;padding:.48rem .75rem;margin:0 0 .48rem}}.clocktime{{font-size:1rem;font-weight:900;color:#fff}}.clocklabel{{font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:#D7E7EF;font-weight:900}}.clocktrack{{height:7px;background:#315266;border-radius:999px;overflow:hidden}}.clockfill{{height:100%;background:linear-gradient(90deg,#35D8DE,#F4AB00,#FF6467)}}.clockremain{{font-size:.78rem;font-weight:900;color:#FF8B8D;text-align:right}}
.titlehero{{position:relative;min-height:calc(100vh - 205px);overflow:hidden;display:grid;grid-template-columns:1.62fr .78fr;align-items:center;gap:1.6rem;background:linear-gradient(135deg,#061C2D 0%,#0B3E59 58%,#086B78 100%);color:white;border-radius:24px;padding:2.7rem 3rem;box-shadow:0 20px 48px rgba(8,31,51,.24)}}.titlehero:before{{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:38px 38px}}.titlecopy{{position:relative;z-index:2}}.titlehero h1{{font-size:clamp(2.45rem,3.15vw,3.35rem);line-height:1;margin:.45rem 0 .65rem;white-space:nowrap;letter-spacing:-.035em}}.titlehero h2{{font-size:1.42rem;color:#D9EDF2;margin:0 0 .8rem}}.titlehero p{{color:#C5DCE5;font-size:1.03rem}}.titlemeta{{font-size:.83rem;color:#C6DAE3;margin-top:1.35rem}}.casebadge{{display:inline-block;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.09);border-radius:999px;padding:.35rem .68rem;margin:.16rem;font-size:.76rem;font-weight:800}}.deadlinebadge{{border-color:#F4C24F;background:rgba(244,171,0,.2);color:#FFE49A}}.openingquestion{{margin:.75rem 0 .45rem;text-align:center;color:#17324A;font-weight:900;font-size:1rem}}
.agentvisual{{position:relative;z-index:2;height:330px;display:flex;align-items:center;justify-content:center}}.agentcore{{position:relative;width:138px;height:138px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;background:radial-gradient(circle at 35% 30%,#42E4ED,#008B99 62%,#005A67);box-shadow:0 0 0 14px rgba(66,228,237,.08),0 0 0 30px rgba(66,228,237,.045);font-size:.8rem;font-weight:900;animation:corePulse 2.8s ease-in-out infinite}}.agentorbit{{position:absolute;width:292px;height:292px;border:1px solid rgba(129,235,241,.35);border-radius:50%;animation:orbitSpin 26s linear infinite}}.agentnode{{position:absolute;width:90px;padding:.42rem .35rem;border-radius:10px;background:rgba(4,29,45,.9);border:1px solid rgba(104,226,234,.42);font-size:.64rem;text-align:center;font-weight:800;animation:counterSpin 26s linear infinite}}.source-agent{{border-top:3px solid #4AA8FF}}.transform-agent{{border-top:3px solid #35D8DE}}.risk-agent{{border-top:3px solid #F4AB00}}.control-agent{{border-top:3px solid #FF777A}}.n1{{top:0;left:101px}}.n2{{top:64px;right:-18px}}.n3{{bottom:54px;right:-12px}}.n4{{bottom:-4px;left:101px}}.n5{{bottom:54px;left:-12px}}.n6{{top:64px;left:-18px}}.dataorb{{position:absolute;left:50%;top:50%;border-radius:50%;z-index:5;offset-rotate:0deg;filter:drop-shadow(0 0 7px currentColor)}}.dataorb:after{{content:'';position:absolute;inset:-5px;border-radius:50%;border:1px solid currentColor;opacity:.25}}.orb1{{width:11px;height:11px;color:#FFE08A;background:#FFE08A;offset-path:path('M 0,-142 A 142,142 0 1,1 -1,-142');animation:dataOrbit 7.5s linear infinite}}.orb2{{width:8px;height:8px;color:#56ECF2;background:#56ECF2;offset-path:path('M 0,-112 A 112,112 0 1,0 -1,-112');animation:dataOrbit 5.8s linear infinite reverse}}.orb3{{width:14px;height:14px;color:#70AFFF;background:#70AFFF;offset-path:path('M 0,-156 A 156,156 0 1,1 -1,-156');animation:dataOrbit 11s linear infinite;animation-delay:-4s}}.orb4{{width:7px;height:7px;color:#FF8B8D;background:#FF8B8D;offset-path:path('M 0,-92 A 92,92 0 1,0 -1,-92');animation:dataOrbit 4.7s linear infinite;animation-delay:-1.5s}}.orb5{{width:9px;height:9px;color:#B2F7C8;background:#B2F7C8;offset-path:path('M 0,-130 A 130,130 0 1,1 -1,-130');animation:dataOrbit 8.8s linear infinite;animation-delay:-6s}}@keyframes orbitSpin{{to{{transform:rotate(360deg)}}}}@keyframes counterSpin{{to{{transform:rotate(-360deg)}}}}@keyframes corePulse{{50%{{transform:scale(1.035)}}}}@keyframes dataOrbit{{to{{offset-distance:100%}}}}@media(prefers-reduced-motion:reduce){{.agentcore,.agentorbit,.agentnode,.dataorb{{animation:none!important}}}}
.actflow{{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin:.65rem 0}}.actnode{{background:white;border:1px solid #D5E1E8;border-radius:12px;padding:.65rem;text-align:center;font-size:.8rem;font-weight:800;color:#17324A}}@media(max-width:1250px){{.titlehero h1{{font-size:2.55rem}}}}@media(max-width:1100px){{.titlehero{{grid-template-columns:1fr;min-height:calc(100vh - 185px);padding:2rem}}.titlehero h1{{white-space:normal}}.agentvisual{{display:none}}}}
</style>''',unsafe_allow_html=True)

PAGES=['Title','Treasury Team of One','Historical Baseline','Friday Snapshot','Organization Map','Monday Inbox','Agent Operations','Human Review','The Storm','Dilemma','Response Studio','CFO Brief','Audit & Downloads']
CLOCK={p:('Mon 8:00 AM',0,'Presentation ready') for p in PAGES}; CLOCK.update({'Historical Baseline':('Fri 4:20 PM',0,'Baseline preparation'),'Friday Snapshot':('Fri 4:30 PM',0,'Risk baseline approved'),'Monday Inbox':('Mon 8:03 AM',3,'New evidence arrives'),'Agent Operations':('Mon 8:08 AM',8,'Agents process files'),'Human Review':('Mon 8:15 AM',15,'Material judgments'),'The Storm':('Mon 8:28 AM',28,'Forecast deteriorates'),'Dilemma':('Mon 8:42 AM',42,'Decision required'),'Response Studio':('Mon 8:55 AM',55,'Responses tested'),'CFO Brief':('Mon 9:25 AM',85,'Brief ready'),'Audit & Downloads':('Mon 9:30 AM',90,'Briefing time')})
for k,v in {'page':0,'hist':None,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action','presentation_mode':True,'agent_step':0,'files_pulled':0,'selected_file':0}.items(): st.session_state.setdefault(k,v)
def hero(k,t,s): st.markdown(f'<div class="hero"><div class="eyebrow">{k}</div><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)
def money(v): return f'${abs(v)/1e6:.2f}M' if abs(v)>=1e6 else f'${abs(v):,.0f}'
def clock(page):
 t,e,phase=CLOCK[page]; rem=max(0,90-e); txt='Before Monday' if page in PAGES[2:4] else ('Briefing time' if rem==0 else f'{rem} min to CFO brief'); st.markdown(f'<div class="clockbar"><div><div class="clocklabel">Briefing Clock</div><div class="clocktime">{t}</div></div><div><div class="clocklabel">{phase}</div><div class="clocktrack"><div class="clockfill" style="width:{e/90*100:.0f}%"></div></div></div><div class="clockremain">{txt}</div></div>',unsafe_allow_html=True)
def fan(r,title,prior=None):
 f=go.Figure(); f.add_trace(go.Scatter(x=DATES,y=r['p975'],line_width=0,showlegend=False)); f.add_trace(go.Scatter(x=DATES,y=r['p025'],fill='tonexty',fillcolor='rgba(0,186,198,.11)',line_width=0,name='95% Range')); f.add_trace(go.Scatter(x=DATES,y=r['p75'],line_width=0,showlegend=False)); f.add_trace(go.Scatter(x=DATES,y=r['p25'],fill='tonexty',fillcolor='rgba(0,186,198,.24)',line_width=0,name='50% Range')); f.add_trace(go.Scatter(x=DATES,y=r['mean'],line=dict(color=C['cyan'],width=4),name='Current Expected'))
 if prior is not None:f.add_trace(go.Scatter(x=DATES,y=prior['mean'],line=dict(color='#7D8D99',dash='dot'),name='Friday Expected'))
 f.add_hline(y=MINIMUM,line_color=C['amber'],line_dash='dash'); f.add_hline(y=0,line_color=C['red']); f.update_layout(title=title,height=330,paper_bgcolor='white',plot_bgcolor='white',legend_orientation='h',margin=dict(l=15,r=10,t=38,b=10),yaxis_tickprefix='$',yaxis_tickformat=',.0f'); return f
def jump(label,target):
 if st.button(label,type='primary',use_container_width=True):st.session_state.page=target;st.rerun()
def find_attachment(name):
 for candidate in [INBOX/name,BASE/'data'/'monday_inbox'/name,BASE/name]:
  if candidate.exists(): return candidate
 return INBOX/name
def preview_file(name):
 path=find_attachment(name)
 if not path.exists(): return None
 try:
  return pd.read_csv(path) if path.suffix.lower()=='.csv' else pd.read_excel(path,engine='openpyxl')
 except Exception: return None
with st.sidebar:
 st.markdown('## ◈ Treasury Agent Operations');st.caption('Evidence to Decision');st.session_state.presentation_mode=st.toggle('Presentation Mode',value=st.session_state.presentation_mode);st.markdown(f'**Act {st.session_state.page+1} of {len(PAGES)}**');st.caption(PAGES[st.session_state.page]);a,b=st.columns(2)
 if a.button('←',use_container_width=True):st.session_state.page=max(0,st.session_state.page-1);st.rerun()
 if b.button('→',use_container_width=True):st.session_state.page=min(len(PAGES)-1,st.session_state.page+1);st.rerun()
 if st.button('Reset Demo',use_container_width=True):
  for k,v in {'page':0,'storm':0,'reviewed':0,'funding':0,'inspect':False,'audience_choice':'No action','agent_step':0,'files_pulled':0,'selected_file':0}.items():st.session_state[k]=v
  st.rerun()
if st.session_state.hist is None:
 try:st.session_state.hist=load_history(SAMPLE)
 except Exception as e:st.error(str(e));st.stop()
hist=st.session_state.hist;friday=simulate(hist,-1);page=PAGES[st.session_state.page]
if page not in PAGES[:2]:clock(page)

if page=='Title':
 st.markdown('''<div class="titlehero"><div class="titlecopy"><div class="eyebrow">TAMPA BAY AFP &nbsp;|&nbsp; SAINT LEO UNIVERSITY &nbsp;|&nbsp; SEPTEMBER 11, 2026</div><h1>The Treasury Team of One</h1><h2>Building AI-Powered Financial Solutions</h2><p>From fragmented evidence to a governed liquidity decision</p><div><span class="casebadge">6 Entities</span><span class="casebadge">3 Currencies</span><span class="casebadge">8 Messages</span><span class="casebadge">10 Attachments</span><span class="casebadge deadlinebadge">1 CFO Deadline</span></div><div class="titlemeta">Zachary A. Smith, Ph.D.<br>Associate Professor of Economics and Finance | Saint Leo University<br><span style="color:#9FC5D3">Former Financial Advisor and Quantitative Analyst | Finance Educator and Researcher</span></div></div><div class="agentvisual"><div class="agentorbit"><span class="dataorb orb1"></span><span class="dataorb orb2"></span><span class="dataorb orb3"></span><span class="dataorb orb4"></span><span class="dataorb orb5"></span><div class="agentnode n1 source-agent">INBOX<br>AGENT</div><div class="agentnode n2 source-agent">VERSION<br>AGENT</div><div class="agentnode n3 transform-agent">DOCUMENT<br>AGENT</div><div class="agentnode n4 transform-agent">MAPPING<br>AGENT</div><div class="agentnode n5 risk-agent">RISK<br>AGENT</div><div class="agentnode n6 control-agent">CONTROL<br>AGENT</div></div><div class="agentcore">TREASURY<br>CONTROL<br>CENTER</div></div></div>''',unsafe_allow_html=True)
 st.markdown('<div class="openingquestion">Can One Treasury Professional Turn Fragmented Evidence Into a Decision Before 9:30?</div>',unsafe_allow_html=True);a,b=st.columns([1.35,1])
 with a:jump('Launch the Liquidity Simulation →',1)
 with b:
  with st.popover('View Case Brief',use_container_width=True):st.markdown('**The Challenge**\n\nSix entities, three currencies, eight messages, and ten attachments must become a defensible recommendation before a 9:30 CFO briefing.\n\n**The Demonstration**\n\nHistorical Risk → Monday Inbox → Agent Operations → Human Control → Liquidity Storm → Treasury Response → CFO Decision.')
elif page=='Treasury Team of One':
 hero('ACT 1 | THE OPERATING THESIS','Treasury Is Surrounded by Information, Not Insight.','Agents connect fragmented evidence quickly enough to support a decision treasury can defend.');st.markdown('<div class="actflow">'+''.join(f'<div class="actnode">{x}</div>' for x in ['Historical Evidence','Friday Risk Baseline','Monday Inbox','Agent Operations','Human Judgment','Liquidity Storm','Treasury Response','CFO Decision'])+'</div>',unsafe_allow_html=True);jump('Establish the Friday Risk Baseline →',2)
elif page=='Historical Baseline':
 hero('T−2 | BEFORE MONDAY','Historical Forecast Performance Loaded','The Risk Agent reads the versioned historical-error file automatically.');a,b,c=st.columns(3);a.metric('Observations',len(hist));b.metric('Beginning',hist.date.min().strftime('%b %Y'));c.metric('Ending',hist.date.max().strftime('%b %Y'));st.dataframe(hist.head(6),use_container_width=True,hide_index=True,height=220);jump('Build the Friday Risk Baseline →',3)
elif page=='Friday Snapshot':
 hero('T−1 | FRIDAY','A Manageable 95% Baseline','The analyst enters the weekend with measured liquidity risk.');l,r=st.columns([2.2,1]);l.plotly_chart(fan(friday,'Friday Cash Distribution'),use_container_width=True)
 with r:a,b=st.columns(2);a.metric('VaR 95%',money(friday['var']));b.metric('CVaR 95%',money(friday['cvar']));c,d=st.columns(2);c.metric('P(Below $200K)',f"{friday['pmin']:.1%}");d.metric('P(Negative)',f"{friday['pneg']:.1%}");jump('Meet Meridian Components →',4)
elif page=='Organization Map':
 hero('ORGANIZATIONAL CONTEXT','One Treasury Function. Six Entities. No Common Reporting System.','Different functions, currencies, and constraints feed one central inbox.');a,b,c=st.columns(3);a.markdown('<div class="panel"><div class="eyebrow">SOURCES</div><div class="row">Corporate Controller</div><div class="row">Manufacturing Finance</div><div class="row">Acquisition Controller</div><div class="row">Shared Services</div><div class="row">International Controllers</div><div class="row">AR Operations + Bank Partner</div></div>',unsafe_allow_html=True);b.markdown('<div class="panel"><div class="eyebrow">ENTITIES</div><div class="row">Meridian Holdings</div><div class="row">Meridian Manufacturing</div><div class="row">Apex Distribution</div><div class="row">Gulf Components</div><div class="row">Meridian Canada</div><div class="row">Meridian Europe</div></div>',unsafe_allow_html=True);c.markdown('<div class="panel"><div class="eyebrow">CENTRAL TREASURY</div><h3>Treasury Team of One</h3><div class="row">8 Messages</div><div class="row">10 Attachments</div><div class="row">USD / CAD / EUR</div></div>',unsafe_allow_html=True);jump('Open the Monday Inbox →',5)
elif page=='Monday Inbox':
 hero('T0 | MONDAY 8:03 AM','The Inbox Agent Pulls Current Evidence','Manually advance the Inbox Agent through the mailbox. Each click retrieves one message and its attachments into the controlled intake queue.')
 inbox=json.loads(INBOX_JSON.read_text())
 attachment_rows=[]
 for message_index,message in enumerate(inbox):
  for attachment in message['attachments']:
   attachment_rows.append({'Time':message['time'],'Sender':message['sender'],'Entity':message['entity'],'Subject':message['subject'],'Attachment':attachment,'Message Index':message_index})
 pulled=min(st.session_state.files_pulled,len(attachment_rows))
 left,right=st.columns([1.65,1],gap='large')
 with left:
  register=[]
  for idx,row in enumerate(attachment_rows):
   state='PULLED' if idx<pulled else ('NEXT' if idx==pulled else 'WAITING')
   register.append([row['Time'],row['Sender'],row['Entity'],row['Attachment'],state])
  st.dataframe(pd.DataFrame(register,columns=['Time','Sender','Entity','Attachment','State']),use_container_width=True,hide_index=True,height=330)
 with right:
  st.metric('Messages Scanned',len(inbox));st.metric('Attachments Pulled',f'{pulled}/{len(attachment_rows)}');st.metric('Intake Queue',pulled)
  if pulled<len(attachment_rows):
   nxt=attachment_rows[pulled]
   st.markdown(f'<div class="panel"><div class="eyebrow">NEXT RETRIEVAL</div><h3>{nxt["Attachment"]}</h3><p><b>Sender:</b> {nxt["Sender"]}<br><b>Entity:</b> {nxt["Entity"]}<br><b>Subject:</b> {nxt["Subject"]}</p></div>',unsafe_allow_html=True)
   if st.button('Pull the Next Attachment →',type='primary',use_container_width=True):st.session_state.files_pulled+=1;st.rerun()
   if st.button('Pull All Remaining Attachments',use_container_width=True):st.session_state.files_pulled=len(attachment_rows);st.rerun()
  else:
   st.markdown('<div class="success"><b>Inbox retrieval complete:</b> Ten attachments and their email context are now available to the wrangling agents.</div>',unsafe_allow_html=True)
   jump('Begin Data Wrangling →',6)
elif page=='Agent Operations':
 hero('AGENT RUN 08-A','The Agents Wrangle the Retrieved Files','Advance the wrangling pipeline manually. The selected file moves from raw structure to mapped, reconciled, and review-ready data.')
 files=['Holdings_Balances.csv','Mfg_Weekly_View.xlsx','Gulf_Cash_Fcst.xlsx','Gulf_Cash_Fcst_v2.xlsx','Apex_Disbursements.csv','Canada_CAD.xlsx','Europe_EUR.xlsx','Europe_Reserve.csv','Facilities.xlsx','AR_Expectations.xlsx']
 selected=st.selectbox('File in the Wrangling Workbench',files,index=min(st.session_state.selected_file,len(files)-1))
 st.session_state.selected_file=files.index(selected)
 stages=[('Document Agent','Inspect workbook structure, sheets, headers, dates, and notes'),('Version Agent','Compare names, timestamps, and email instructions'),('Mapping Agent','Normalize entities, currencies, fields, signs, and dates'),('Reconciliation Agent','Test duplicates, balances, restrictions, facilities, and timing'),('Risk Agent','Translate approved evidence into forecast assumptions')]
 completed=min(st.session_state.agent_step,len(stages))
 m1,m2,m3,m4=st.columns(4);m1.metric('Files Retrieved',st.session_state.files_pulled);m2.metric('Wrangling Stage',f'{completed}/{len(stages)}');m3.metric('Mappings Proposed',27 if completed>=3 else 0);m4.metric('Exceptions Surfaced',6 if completed>=4 else 0)
 left,right=st.columns([1.18,1],gap='large')
 with left:
  work=[]
  for idx,(agent,action) in enumerate(stages):work.append([idx+1,agent,action,'COMPLETE' if idx<completed else 'READY' if idx==completed else 'WAITING'])
  st.dataframe(pd.DataFrame(work,columns=['Stage','Agent','Wrangling Work','State']),use_container_width=True,hide_index=True,height=250)
  a,b=st.columns(2)
  if completed<len(stages):
   if a.button('Run the Next Wrangling Step →',type='primary',use_container_width=True):st.session_state.agent_step+=1;st.rerun()
   if b.button('Complete All Wrangling Steps',use_container_width=True):st.session_state.agent_step=len(stages);st.rerun()
  else:st.markdown('<div class="success"><b>Wrangling complete:</b> Material exceptions are ready for treasury review.</div>',unsafe_allow_html=True)
 with right:
  st.markdown(f'### Source Preview: {selected}')
  preview=preview_file(selected)
  if preview is not None:st.dataframe(preview.head(8),use_container_width=True,hide_index=True,height=180)
  else:st.warning('The source file could not be previewed.')
  raw,clean=st.tabs(['Raw Evidence','Proposed Clean Record'])
  with raw:st.code(f'''File: {selected}
Structure: source-specific
Status: retrieved from inbox
Email context: preserved''')
  with clean:st.markdown('<div class="panel"><div class="row">Entity <span class="grow"></span><b>Canonicalized</b></div><div class="row">Dates <span class="grow"></span><b>Normalized</b></div><div class="row">Currency <span class="grow"></span><b>Validated</b></div><div class="row">Material Issues <span class="grow"></span><b style="color:#F4AB00">Awaiting Treasury</b></div></div>',unsafe_allow_html=True)
 if completed==len(stages):jump('Open the Human Control Gate →',7)
elif page=='Human Review':
 hero('HUMAN CONTROL GATE','Agents Propose. Treasury Decides.','Inspect the actual source context and rows before approving a material treatment.')
 evidence=[
  {'issue':'Duplicate Holdings Balance','impact':'$2.45M possible overstatement','proposal':'Retain one canonical record and quarantine the duplicate','entity':'Meridian Holdings','sender':'Corporate Controller','subject':'Friday balances, revised file may follow','file':'Holdings_Balances.csv','raw':'Accounts 00100442 and 100442 carry the same $2.45 million balance.','finding':'Likely duplicate after restoring the leading zero and matching the entity alias.','confidence':'98%'},
  {'issue':'Reserve Unit Anomaly','impact':'Material available-cash overstatement','proposal':'Interpret as EUR 425K after review and exclude as restricted','entity':'Meridian Europe','sender':'Europe Controller','subject':'Forecast and restricted reserve','file':'Europe_Reserve.csv','raw':'Account EU7799 reports 42,500,000 and Restricted = Y.','finding':'Likely cents-versus-units anomaly; the balance cannot be swept.','confidence':'94%'},
  {'issue':'Orion Timing','impact':'$620K timing dependency','proposal':'Retain one receivable and model settlement probabilistically','entity':'Gulf Components','sender':'AR Operations','subject':'Orion timing remains unconfirmed','file':'AR_Expectations.xlsx','raw':'INV-8812 appears twice; expected September 2; average delay is five days.','finding':'Duplicate receivable candidate and optimistic settlement date.','confidence':'96%'},
  {'issue':'Duplicate Payroll','impact':'$245K possible outflow duplication','proposal':'Retain one verified payment','entity':'Gulf Components','sender':'Shared Services','subject':'AP and payroll schedule','file':'Apex_Disbursements.csv','raw':'Gulf payroll of $245,000 appears under two entity aliases.','finding':'Potential duplicate payroll record.','confidence':'97%'},
  {'issue':'Facility Mismatch','impact':'$50K liquidity overstatement','proposal':'Use commitment less drawn: $50K available','entity':'Gulf Components','sender':'Bank Partner','subject':'Facility availability','file':'Facilities.xlsx','raw':'Commitment $500K; drawn $450K; reported availability $100K.','finding':'Reconciled availability is $50K.','confidence':'100%'},
  {'issue':'FX Inconsistencies','impact':'Translation variance','proposal':'Use the approved treasury rate','entity':'Meridian Canada','sender':'Canada Controller','subject':'CAD forecast using Friday FX','file':'Canada_CAD.xlsx','raw':'The entity forecast uses conversion rate 0.742.','finding':'The local rate requires comparison with the approved treasury feed.','confidence':'91%'}]
 i=min(st.session_state.reviewed,5);e=evidence[i]
 st.markdown(f'<div class="panel"><div class="eyebrow">REVIEW {i+1} OF 6</div><h3>{e["issue"]}</h3><p><b>Potential Impact:</b> {e["impact"]}<br><b>Agent Proposal:</b> {e["proposal"]}</p></div>',unsafe_allow_html=True)
 a,b,c=st.columns(3)
 if a.button('Accept',type='primary',use_container_width=True):st.session_state.reviewed=min(6,i+1);st.session_state.inspect=False;st.rerun()
 if b.button('Defer',use_container_width=True):st.session_state.reviewed=min(6,i+1);st.session_state.inspect=False;st.rerun()
 if c.button('Inspect Evidence',use_container_width=True):st.session_state.inspect=not st.session_state.inspect;st.rerun()
 if st.session_state.inspect:
  left,right=st.columns([1,1.2],gap='large')
  with left:st.markdown(f'<div class="panel" style="border-left:4px solid #00BAC6"><div class="eyebrow">SOURCE CONTEXT</div><div class="row"><b>Entity</b><span class="grow"></span>{e["entity"]}</div><div class="row"><b>Sender</b><span class="grow"></span>{e["sender"]}</div><div class="row"><b>Email</b><span class="grow"></span>{e["subject"]}</div><div class="row"><b>Attachment</b><span class="grow"></span>{e["file"]}</div><p><b>Raw Evidence</b><br>{e["raw"]}</p><p><b>Agent Finding</b><br>{e["finding"]}</p><p><b>Confidence:</b> {e["confidence"]}</p></div>',unsafe_allow_html=True)
  with right:
   st.markdown('### Attachment Preview')
   preview=preview_file(e['file'])
   if preview is not None:st.dataframe(preview.head(10),use_container_width=True,hide_index=True,height=255)
   else:st.warning(f'Attachment not found: {e["file"]}')
 approved=st.session_state.reviewed;h1,h2=st.columns(2);h1.metric('Approved for Model',approved);h2.metric('Unresolved',max(0,6-approved));st.progress(approved/6)
 if approved>=4:jump('Release the Approved Truth Set →',8)
elif page=='The Storm':
 stage=st.session_state.storm;r=simulate(hist,stage);hero(f'STORM {stage+1} OF 5',STORMS[stage][0],'New evidence changes the assumptions behind Friday’s forecast.');l,rgt=st.columns([2.1,1]);l.plotly_chart(fan(r,'Friday Baseline vs. Current Risk',friday),use_container_width=True)
 with rgt:st.metric('VaR 95%',money(r['var']));st.metric('CVaR 95%',money(r['cvar']));st.metric('P(Negative)',f"{r['pneg']:.1%}");st.markdown(f'<div class="panel"><div class="eyebrow">EVIDENCE CAUSING THE MOVE</div><h3>{STORMS[stage][0]}</h3><p>The approved evidence changes expected cash, uncertainty, funding capacity, or accessibility.</p></div>',unsafe_allow_html=True)
 if stage<4:
  if st.button('Release the Next Event →',type='primary',use_container_width=True):st.session_state.storm+=1;st.rerun()
 else:jump('Reveal the Liquidity Dilemma →',9)
elif page=='Dilemma':
 hero('AUDIENCE DECISION','What Would You Recommend Before the 9:30 Briefing?','Choose a response before viewing the modeled result.');opts=['Rely on Receipt','Local Line','Intercompany Transfer','Layered Response'];cols=st.columns(4)
 for col,opt in zip(cols,opts):
  if col.button(opt,use_container_width=True):st.session_state.audience_choice=opt;st.rerun()
 st.markdown(f'<div class="warn"><b>Audience Recommendation:</b> {st.session_state.audience_choice}</div>',unsafe_allow_html=True);jump('Test the Audience Recommendation →',10)
elif page=='Response Studio':
 fmap={'No action':0,'Rely on Receipt':0,'Local Line':50000,'Intercompany Transfer':500000,'Layered Response':550000};f=fmap.get(st.session_state.audience_choice,0);st.session_state.funding=f;r=simulate(hist,4,funding=f);hero('RESPONSE STUDIO',f'Testing: {st.session_state.audience_choice}','The model reruns the tail-risk distribution.');l,rgt=st.columns([2.1,1]);l.plotly_chart(fan(r,'Post-Response Distribution',friday),use_container_width=True);rgt.metric('Funding',money(f));rgt.metric('P(Negative)',f"{r['pneg']:.1%}");rgt.dataframe(compare_responses(hist),use_container_width=True,hide_index=True,height=200);jump('Create the CFO Decision Brief →',11)
elif page=='CFO Brief':
 r=simulate(hist,4,funding=st.session_state.funding);hero('9:25 AM','A Governed Liquidity Decision','The conclusion remains traceable to source evidence.');st.markdown(f'<div class="panel"><h3>Gulf Components Liquidity Exposure</h3><p><b>Situation:</b> P(Negative) is {r["pneg"]:.1%}; expected tail shortfall is {money(r["cvar"])}.</p><p><b>Selected Response:</b> {st.session_state.audience_choice}, {money(st.session_state.funding)}.</p><p><b>Decision:</b> Confirm receipt timing and approve funding before the trough.</p></div>',unsafe_allow_html=True);jump('Open Audit & Outputs →',12)
else:
 hero('9:30 AM','From Fragmented Evidence to a Controlled Decision','Source traceability, agent speed, human judgment, and probabilistic response.');a,b,c=st.columns(3);a.metric('Messages Connected',8);b.metric('Attachments Processed',10);c.metric('Material Exceptions',6);st.markdown('<div class="success"><b>Friday’s model was not wrong. Monday’s evidence changed the assumptions. The advantage was the ability to adapt before uncertainty became a liquidity crisis.</b></div>',unsafe_allow_html=True);r=simulate(hist,4,funding=st.session_state.funding);out=pd.DataFrame({'date':DATES,'expected_cash':r['mean'],'p2_5':r['p025'],'p97_5':r['p975']});mem=io.BytesIO()
 with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('forecast_percentiles.csv',out.to_csv(index=False));z.writestr('response_comparison.csv',compare_responses(hist).to_csv(index=False));z.writestr('attachment_profile.csv',process_inbox(INBOX).to_csv(index=False))
 st.download_button('Download Decision Package',mem.getvalue(),file_name='Treasury_Agent_Outputs.zip',type='primary',use_container_width=True)
