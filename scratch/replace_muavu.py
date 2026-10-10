import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "Đáy cấu trúc Vĩ mô / Giá thành sản xuất (Cấu hình tùy chỉnh)"
replacement = "Hỗ trợ cấu trúc dài hạn. Đã phản ánh: War Premium | Dầu thô: {oil_live}$ | DXY: {dxy_live}"

if target in content:
    content = content.replace(target, replacement)
    with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully!")
else:
    print("Target string not found in UTF-8. Trying fallback...")
    # Maybe it's stored weirdly?
