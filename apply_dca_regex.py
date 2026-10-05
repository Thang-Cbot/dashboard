import re
with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'(<div.*?margin-bottom:12px;\'>\s*).*?THÔNG SỐ GIÁ.*?(</div>)', r'\g<1>📊 {sym_text}\g<2>', content)
content = re.sub(r'(<div.*?THỜI GIAN GOM TỐI ƯU</div>\s*<div.*?>).*?(</div>\s*<div.*?>).*?(</div>)', r'\g<1>{dca_time}\g<2>{dca_reason}\g<3>', content)
content = re.sub(r'(<div.*?VÙNG GOM ZONE 1.*?</div>\s*<div.*?>).*?(</div>)', r'\g<1>{z1_price}\g<2>', content)
content = re.sub(r'(<div.*?VÙNG GOM ZONE 2.*?</div>\s*<div.*?>).*?(</div>)', r'\g<1>{z2_price}\g<2>', content)

fix_logic = """    if commodity == "ZW":
        sym_text = f"THÔNG SỐ GIÁ ZW (ZWZ26) - Cập nhật: {zw_date}"
        dca_time = "Cuối T11 - Giữa T12/2026"
        dca_reason = "Khi áp lực xả hàng Úc+Argentina đạt đỉnh, El Niño bắt đầu ảnh hưởng Q1/2027"
        z1_price = f"{s1:.0f} - 680¢"
        z2_price = f"{s2:.0f} - 620¢"
    else:"""

content = re.sub(r'    if commodity == "ZW":\n        sym_text = f"\{sym_text\}".*?    else:', fix_logic, content, flags=re.DOTALL)

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
