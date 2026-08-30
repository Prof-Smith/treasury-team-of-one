from pathlib import Path

p = Path('app.py')
if not p.exists():
    raise SystemExit('Place this file beside app.py, then run: python apply_branding_update.py')
s = p.read_text(encoding='utf-8')

# 1. Slow the orbit and preserve upright labels.
s = s.replace('animation:orbitSpin 18s linear infinite', 'animation:orbitSpin 26s linear infinite')
s = s.replace('animation:counterSpin 18s linear infinite', 'animation:counterSpin 26s linear infinite')

# 2. Rename the machine-centered core to the human-centered control center.
s = s.replace('TREASURY<br>DECISION<br>ENGINE', 'TREASURY<br>CONTROL<br>CENTER')

# 3. Add restrained co-branding and category accents.
s = s.replace(
    '<div class="eyebrow">TAMPA BAY AFP | SEPTEMBER 11, 2026</div>',
    '<div class="eyebrow">TAMPA BAY AFP &nbsp;|&nbsp; SAINT LEO UNIVERSITY &nbsp;|&nbsp; SEPTEMBER 11, 2026</div>'
)
s = s.replace('class="agentnode n1"', 'class="agentnode n1 source-agent"')
s = s.replace('class="agentnode n2"', 'class="agentnode n2 source-agent"')
s = s.replace('class="agentnode n3"', 'class="agentnode n3 transform-agent"')
s = s.replace('class="agentnode n4"', 'class="agentnode n4 transform-agent"')
s = s.replace('class="agentnode n5"', 'class="agentnode n5 risk-agent"')
s = s.replace('class="agentnode n6"', 'class="agentnode n6 control-agent"')
s = s.replace(
    '.n1{{top:0;left:101px}}',
    '.source-agent{{border-top:3px solid #4AA8FF}}.transform-agent{{border-top:3px solid #35D8DE}}.risk-agent{{border-top:3px solid #F4AB00}}.control-agent{{border-top:3px solid #FF777A}}.n1{{top:0;left:101px}}'
)

# 4. Make the deadline visually distinct.
s = s.replace(
    '<span class="casebadge">1 CFO Deadline</span>',
    '<span class="casebadge deadlinebadge">1 CFO Deadline</span>'
)
s = s.replace(
    '.casebadge{{display:inline-block;',
    '.deadlinebadge{{border-color:#F4C24F!important;background:rgba(244,171,0,.2)!important;color:#FFE49A!important}}.casebadge{{display:inline-block;'
)

# 5. Add a concise opening question above the actions.
question = '<div class="openingquestion">Can One Treasury Professional Turn Fragmented Evidence Into a Decision Before 9:30?</div>'
s = s.replace("    st.markdown('<div class=\"titleactions\">',unsafe_allow_html=True)", f"    st.markdown('{question}<div class=\"titleactions\">',unsafe_allow_html=True)")
s = s.replace(
    '.titleactions div[data-testid="stButton"] button{{min-height:48px;font-size:1rem}}',
    '.openingquestion{{margin:.75rem 0 .45rem;text-align:center;color:#17324A;font-weight:900;font-size:1rem}}.titleactions div[data-testid="stButton"] button{{min-height:48px;font-size:1rem}}'
)

# 6. Shorten and rebalance the actions.
s = s.replace('Run the Monday-Morning Liquidity Simulation →', 'Launch the Liquidity Simulation →')
s = s.replace('Preview the Case', 'View Case Brief')

# 7. Expand identity without over-branding.
s = s.replace(
    'Associate Professor of Economics and Finance | Saint Leo University',
    'Associate Professor of Economics and Finance | Saint Leo University<br><span style="color:#9FC5D3">Former Financial Advisor and Quantitative Analyst | Applied Decision Sciences Educator</span>'
)

# 8. Add restrained signal flow along the orbit.
s = s.replace(
    '<div class="agentorbit">',
    '<div class="agentorbit"><span class="flowdot fd1"></span><span class="flowdot fd2"></span><span class="flowdot fd3"></span>'
)
s = s.replace(
    '.agentnode{{position:absolute;',
    '.flowdot{{position:absolute;width:8px;height:8px;border-radius:50%;background:#FFE08A;box-shadow:0 0 14px #FFE08A;z-index:4;animation:flowPulse 2.4s ease-in-out infinite}}.fd1{{top:25px;left:53px}}.fd2{{right:17px;top:137px;animation-delay:.8s}}.fd3{{bottom:24px;left:143px;animation-delay:1.6s}}@keyframes flowPulse{{0%,100%{{opacity:.18;transform:scale(.65)}}50%{{opacity:1;transform:scale(1.25)}}}}.agentnode{{position:absolute;'
)
s = s.replace(
    '.agentcore,.agentorbit,.agentnode,.signal{{animation:none!important}}',
    '.agentcore,.agentorbit,.agentnode,.signal,.flowdot{{animation:none!important}}'
)

p.write_text(s, encoding='utf-8')
compile(s, 'app.py', 'exec')
print('Branding and title-page appeal update applied successfully.')
