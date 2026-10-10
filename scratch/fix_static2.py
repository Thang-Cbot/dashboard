import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# find the div inside col_b under macro_z1
pattern = r"<div style='font-size:11px;color:#94a3b8;'>.*?War Premium.*?</div>"
replacement = "<div style='font-size:11px;color:#94a3b8;'>Cơ sở định giá (Cố định): Tồn kho hụt 18.5% YoY | Dầu > 90$ | DXY ~ 102</div>"

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
if new_content != content:
    with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced!")
else:
    print("Not found")
