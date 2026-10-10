import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the dynamic f-string back to a static string
pattern = r"Hỗ trợ cấu trúc dài hạn. Đã phản ánh: War Premium \| Dầu thô: \{oil_live\}\$ \| DXY: \{dxy_live\}"
replacement = "Cơ sở định giá (Cố định): Tồn kho hụt 18.5% YoY | Dầu > 90$ | DXY ~ 102"

content = re.sub(pattern, replacement, content)

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated to static assumptions.")
