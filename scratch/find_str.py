with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
match = re.search(r"Cơ sở định giá \(Cố định\).*?DXY", content)
if match:
    print("Found:", match.group(0))
else:
    print("NOT FOUND!")
