from pathlib import Path

files = [
    Path('D:/0_Thang_Drive/Antigravity/Cbot/app.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/1_Overview.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/2_Profiles.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/3_News.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/4_Weather_Map.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/5_Macro_Matrix.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/6_MuaVu.py'),
    Path('D:/0_Thang_Drive/Antigravity/Cbot/pages/8_System_Logs.py')
]

for f in files:
    if not f.exists():
        print('Not found:', f)
        continue
    txt = f.read_text(encoding='utf-8')
    orig = txt
    
    # Check if 7_Live_Signal is already in it
    if '7_Live_Signal.py' not in txt:
        if 'pages/7_System_Logs.py' in txt:
            txt = txt.replace(
                'st.sidebar.page_link("pages/7_System_Logs.py", label="⚙️ System Logs")',
                'st.sidebar.page_link("pages/7_Live_Signal.py",  label="🎯 Live Signal & Hiệu Suất")\n    st.sidebar.page_link("pages/8_System_Logs.py",  label="⚙️ System Logs")'
            )
        elif 'pages/6_MuaVu.py' in txt:
            # find where 6_MuaVu is
            target_line = [l for l in txt.splitlines() if 'pages/6_MuaVu.py' in l]
            if target_line:
                t = target_line[0]
                indent = t[:len(t) - len(t.lstrip())]
                new_lines = t + '\n' + indent + 'st.sidebar.page_link("pages/7_Live_Signal.py",  label="🎯 Live Signal & Hiệu Suất")\n' + indent + 'st.sidebar.page_link("pages/8_System_Logs.py",  label="⚙️ System Logs")'
                txt = txt.replace(t, new_lines)
                
    if txt != orig:
        f.write_text(txt, encoding='utf-8')
        print('Updated:', f.name)
    else:
        print('No change or already updated:', f.name)
