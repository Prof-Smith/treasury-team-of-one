from pathlib import Path
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from engine import load_truth_set, calculate_forecast, scenario_summary, consolidated_snapshot, model_checks

st.set_page_config(page_title='Monday-Morning Liquidity Command Center', page_icon='💧', layout='wide')
BASE=Path(__file__).parent
DEFAULT=BASE/'data'/'Monday_Morning_Liquidity_Clean_Truth_Set.xlsx'

st.markdown('''<style>
.block-container{padding-top:1.4rem;max-width:1450px}.hero{background:linear-gradient(135deg,#17365D,#275D8C);padding:1.25rem 1.5rem;border-radius:16px;color:white;margin-bottom:1rem}.hero h1{margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;color:#DDEBF7}.status-ok{color:#107C10;font-weight:700}.status-warn{color:#B36B00;font-weight:700}.status-bad{color:#C00000;font-weight:700}.small{color:#666;font-size:.88rem}
</style>''',unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>Monday-Morning Liquidity Command Center</h1><p>The Treasury Team of One | Synthetic TBAFP demonstration</p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.header('Case controls')
    uploaded=st.file_uploader('Upload revised truth-set workbook',type=['xlsx'])
    page=st.radio('Workspace',['1. Monday Morning Inbox','2. Data Review','3. Liquidity Command Center','4. Scenario Laboratory','5. CFO Briefing','6. Model Controls'])
    st.caption('No uploaded data are transmitted by this app. Calculations are deterministic.')

source=uploaded if uploaded is not None else DEFAULT
try:
    ts=load_truth_set(source)
except Exception as e:
    st.error(f'The workbook could not be loaded: {e}')
    st.stop()
forecast=calculate_forecast(ts)
summary=scenario_summary(forecast,ts)
checks=model_checks(ts,forecast)

if page.startswith('1.'):
    st.subheader('Monday, 8:03 a.m.')
    st.info('CFO directive: Keep every account positive and advise me of any liquidity concerns before the morning briefing.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Files received','8')
    c2.metric('Control issues',len(ts.treatments))
    c3.metric('Items requiring review',int(ts.treatments['Human Review Required?'].astype(str).eq('Y').sum()))
    c4.metric('Forecast scenarios',len(ts.scenarios))
    st.markdown('### What arrived')
    inbox=pd.DataFrame([
        ['Bank balances','Received','Duplicates, stale balance, unit anomaly'],['Entity forecasts','Received','Six structures, missing flow, stale forecast'],
        ['AR expectations','Received','Duplicate invoice and timing risk'],['Disbursements','Received','Duplicate payroll, sign and date issues'],
        ['Facilities','Received','Availability mismatch and borrower constraints'],['FX rates','Received','Stale, reciprocal, and outlier rates'],
        ['Treasury policy','Received','Threshold and transfer rules'],['Account master','Received','Canonical account reference']],columns=['Submission','Status','Initial signal'])
    st.dataframe(inbox,use_container_width=True,hide_index=True)
    st.warning('Positive consolidated cash does not establish entity-level liquidity. The review must determine what is accurate, current, available, and decision-ready.')

elif page.startswith('2.'):
    st.subheader('Data Review and Accepted Treatments')
    q1,q2,q3=st.columns(3)
    q1.metric('Total issues',len(ts.treatments)); q2.metric('Human review',int(ts.treatments['Human Review Required?'].astype(str).eq('Y').sum())); q3.metric('Safe to automate',int(ts.treatments['Auto-Safe?'].astype(str).eq('Y').sum()))
    classes=['All']+sorted(ts.treatments['Classification'].dropna().astype(str).unique().tolist())
    chosen=st.selectbox('Filter by classification',classes)
    view=ts.treatments if chosen=='All' else ts.treatments[ts.treatments['Classification']==chosen]
    st.dataframe(view,use_container_width=True,hide_index=True,height=450)
    st.markdown('**Control principle:** Safe formatting standardization may be automated. Material financial corrections remain proposed until treasury accepts, rejects, or edits them.')

elif page.startswith('3.'):
    st.subheader('Liquidity Command Center')
    scenario=st.selectbox('Scenario',['Reported','Downside','Stress'])
    first=forecast['Date'].min(); snap=consolidated_snapshot(forecast,scenario,first)
    scsum=summary[summary['Scenario']==scenario].iloc[0]
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Consolidated available cash',f"${snap['available_usd']/1_000_000:,.2f}M")
    c2.metric('Entities below minimum',snap['entities_below_minimum'])
    c3.metric('Gulf liquidity trough',f"${scsum['Lowest Cash']:,.0f}")
    c4.metric('Gulf trough date',pd.Timestamp(scsum['Trough Date']).strftime('%b %d'))
    g=forecast[forecast['Scenario']==scenario]
    fig=px.line(g,x='Date',y='Ending Available (USD)',color='Entity',markers=True,title='Available cash by entity, translated to USD')
    fig.update_layout(legend_title_text='',hovermode='x unified')
    st.plotly_chart(fig,use_container_width=True)
    latest=g[g['Date']==g['Date'].min()][['Entity','Ending Available (LCY)','Currency','Policy Minimum (LCY)','Surplus / (Shortfall)','Status']]
    st.dataframe(latest,use_container_width=True,hide_index=True,column_config={'Ending Available (LCY)':st.column_config.NumberColumn(format='$%0.0f'),'Policy Minimum (LCY)':st.column_config.NumberColumn(format='$%0.0f'),'Surplus / (Shortfall)':st.column_config.NumberColumn(format='$%0.0f')})

elif page.startswith('4.'):
    st.subheader('Scenario Laboratory')
    st.caption('Adjust the Orion receipt timing and optional shock. The core arithmetic remains deterministic.')
    base=ts.scenarios.copy()
    scenario=st.selectbox('Scenario to test',base['Scenario'].astype(str).tolist(),index=1)
    row=base[base['Scenario'].astype(str)==scenario].iloc[0]
    c1,c2,c3=st.columns(3)
    receipt_date=c1.date_input('Orion receipt date',value=pd.Timestamp(row['Orion Receipt Date']).date())
    receipt_amount=c2.number_input('Orion receipt amount',min_value=0.0,value=float(row['Orion Receipt Amount']),step=10000.0)
    shock=c3.number_input('Additional Gulf payment',min_value=0.0,value=float(row['Unplanned Gulf Payment Amount']),step=10000.0)
    custom=ts.scenarios.copy()
    idx=custom['Scenario'].astype(str)==scenario
    custom.loc[idx,'Orion Receipt Date']=pd.Timestamp(receipt_date); custom.loc[idx,'Orion Receipt Amount']=receipt_amount
    custom.loc[idx,'Unplanned Gulf Payment Amount']=shock
    if shock>0 and custom.loc[idx,'Unplanned Gulf Payment Date'].isna().all(): custom.loc[idx,'Unplanned Gulf Payment Date']=pd.Timestamp('2026-09-04')
    original=ts.scenarios; ts.scenarios=custom; custom_fc=calculate_forecast(ts); ts.scenarios=original
    gulf=custom_fc[(custom_fc['Scenario']==scenario)&(custom_fc['Entity ID']=='E004')]
    fig=go.Figure(); fig.add_trace(go.Scatter(x=gulf['Date'],y=gulf['Ending Available (LCY)'],mode='lines+markers',name='Available cash'))
    fig.add_trace(go.Scatter(x=gulf['Date'],y=gulf['Policy Minimum (LCY)'],mode='lines',name='Policy minimum',line=dict(dash='dash',color='#B36B00')))
    fig.add_hline(y=0,line_color='#C00000',line_width=2)
    fig.update_layout(title=f'Gulf Components: {scenario}',yaxis_title='Cash (USD)',hovermode='x unified')
    st.plotly_chart(fig,use_container_width=True)
    trough=gulf.loc[gulf['Ending Available (LCY)'].idxmin()]
    a,b,c=st.columns(3); a.metric('Lowest cash',f"${trough['Ending Available (LCY)']:,.0f}"); b.metric('Trough date',trough['Date'].strftime('%b %d')); c.metric('Status',trough['Status'])
    st.dataframe(gulf[['Date','Opening Available (LCY)','Ledger Net Flow (LCY)','Scenario Receipt (LCY)','Stress Payment (LCY)','Ending Available (LCY)','Status']],use_container_width=True,hide_index=True)

elif page.startswith('5.'):
    st.subheader('9:30 a.m. CFO Briefing')
    scenario=st.selectbox('Briefing scenario',['Reported','Downside','Stress'],index=1)
    s=summary[summary['Scenario']==scenario].iloc[0]
    trough=pd.Timestamp(s['Trough Date']).strftime('%A, %B %d')
    if s['Lowest Cash']<0: condition=f"a negative balance of ${abs(s['Lowest Cash']):,.0f}"
    else: condition=f"a lowest available balance of ${s['Lowest Cash']:,.0f}"
    st.markdown(f'''### Current position
Consolidated liquidity remains positive, but Gulf Components is projected to reach **{condition} on {trough}** under the **{scenario}** scenario. The entity's operating-cash minimum is **$200,000**.

### Primary driver
The timing of the **$620,000 Orion Automotive receipt** determines whether the issue remains a policy-threshold breach or becomes a negative-balance event. Gulf Components also has concentrated payroll and supplier outflows during the forecast period.

### Available response
The reconciled Gulf Components local line provides **${s['Local Facility Available']:,.0f}** of availability. Additional company liquidity exists, but borrower, transfer, timing, and approval constraints must be considered before treating it as available to Gulf Components.

### Decision required
Authorize treasury to confirm the Orion receipt date and evaluate an approved funding action before the projected trough. Preserve all source assumptions and reviewer decisions in the audit trail.

### Control note
This briefing is generated from reviewed data and deterministic cash calculations. Forecast timing remains an assumption, and no transaction is executed by the tool.''')
    text=f'''CFO LIQUIDITY BRIEFING\nScenario: {scenario}\n\nCurrent position: Gulf Components reaches {condition} on {trough}. Policy minimum: $200,000.\nPrimary driver: Timing of the $620,000 Orion Automotive receipt and concentrated payroll and supplier outflows.\nAvailable response: Reconciled local-line availability is ${s['Local Facility Available']:,.0f}. Other liquidity is subject to borrower, transfer, timing, and approval constraints.\nDecision required: Confirm receipt timing and authorize treasury to evaluate a funding response before the projected trough.\nControl note: Reviewed inputs and deterministic calculations; no transaction execution.\n'''
    st.download_button('Download briefing as text',text,file_name=f'CFO_Liquidity_Briefing_{scenario}.txt')

else:
    st.subheader('Model Controls')
    passed=int(checks['Pass'].sum()); total=len(checks)
    c1,c2=st.columns(2); c1.metric('Checks passed',f'{passed} of {total}'); c2.metric('Workbook source','Uploaded revision' if uploaded else 'Bundled truth set')
    st.dataframe(checks,use_container_width=True,hide_index=True)
    with st.expander('Canonical entities'): st.dataframe(ts.entities,use_container_width=True,hide_index=True)
    with st.expander('Approved FX rates'): st.dataframe(ts.fx,use_container_width=True,hide_index=True)
    with st.expander('Facilities'): st.dataframe(ts.facilities,use_container_width=True,hide_index=True)
