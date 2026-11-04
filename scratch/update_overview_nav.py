import re
from pathlib import Path

p = Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/1_Overview.py')
txt = p.read_text(encoding='utf-8')
txt = re.sub(
    r'st\.sidebar\.page_link\("pages/7_System_Logs\.py",\s*label="⚙️ System Logs"\)',
    'st.sidebar.page_link("pages/7_Live_Signal.py",  label="🎯 Live Signal & Hiệu Suất")\n    st.sidebar.page_link("pages/8_System_Logs.py",  label="⚙️ System Logs")',
    txt
)
p.write_text(txt, encoding='utf-8')
print('Updated 1_Overview.py successfully!')
