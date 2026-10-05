import re

# 1. Update Macro Engine for F8 and F12
with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    me_code = f.read()

def inject_at_start(func_name, injection, code):
    pattern = r'(def ' + func_name + r'\(.*?\):)'
    def repl(m):
        return m.group(1) + '\n' + injection
    return re.sub(pattern, repl, code)

me_code = inject_at_start('score_f8_geopolitics', '    if commodity == "ZC": return {"score": 5, "raw_value": "Logistics & Biển Đen", "raw_detail": "Chiến sự Biển Đen giảm nhiệt, tắc nghẽn vận tải không còn là điểm nóng.", "last_updated": "Hiện tại", "status": "manual"}', me_code)

me_code = inject_at_start('score_f12_global_demand', '    if commodity == "ZC": return {"score": 4, "raw_value": "Nhu cầu suy yếu", "raw_detail": "Nhu cầu thức ăn chăn nuôi toàn cầu yếu do lo ngại kinh tế và dịch bệnh.", "last_updated": "Hiện tại", "status": "manual"}', me_code)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(me_code)

# 2. Update 6_MuaVu.py
with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Part 1: Replace hardcoded DXY, Oil, COT descriptions
dxy_html_old = "DXY cao → lúa mì Mỹ đắt → Bearish XK"
dxy_html_new = "{'DXY cao → lúa mì Mỹ đắt → Bearish XK' if commodity == 'ZW' else 'DXY cao → Ngô Mỹ đắt → Bearish XK'}"
content = content.replace(dxy_html_old, dxy_html_new)

oil_html_old = "Dầu ảnh hưởng cước tàu & phân bón"
oil_html_new = "{'Dầu ảnh hưởng cước tàu & phân bón' if commodity == 'ZW' else 'Ngô chạy theo Dầu (40% SP nấu Ethanol)'}"
content = content.replace(oil_html_old, oil_html_new)

cot_html_old = "DÒNG TIỀN COT - ZW"
cot_html_new = "DÒNG TIỀN COT - {commodity}"
content = content.replace(cot_html_old, cot_html_new)


# Part 3: DCA Box calculation
# Find the DCA box variables section
dca_var_start = '    pct_1m = ((close - low1m) / (high1m - low1m) * 100)'
dca_var_replacement = """    pct_1m = ((close - low1m) / (high1m - low1m) * 100) if isinstance(close,(int,float)) and isinstance(high1m,(int,float)) and high1m!=low1m else None

    if commodity == "ZW":
        sym_text = f"THÔNG SỐ GIÁ ZW (ZWZ26) - Cập nhật: {zw_date}"
        dca_time = "Cuối T11 - Giữa T12/2026"
        dca_reason = "Khi áp lực xả hàng Úc+Argentina đạt đỉnh, El Niño bắt đầu ảnh hưởng Q1/2027"
        z1_price = f"{s1:.0f} - 680¢"
        z2_price = f"{s2:.0f} - 620¢"
    else:
        sym_text = f"THÔNG SỐ GIÁ ZC (ZCZ26) - Cập nhật: {zw_date}"
        dca_time = "Giai đoạn T10 - T11/2026"
        dca_reason = "Khi áp lực mùa vụ thu hoạch tại Mỹ đạt đỉnh điểm (Nguồn cung bung ra mạnh nhất)"
        s1_val = s1 if isinstance(s1, (int,float)) else 400
        s2_val = s2 if isinstance(s2, (int,float)) else 380
        z1_price = f"{s1_val:.0f} - {s1_val+10:.0f}¢"
        z2_price = f"{s2_val:.0f} - {s2_val+10:.0f}¢"

"""

content = re.sub(r'    pct_1m = .*? else None\n', dca_var_replacement, content)

# Now replace the hardcoded HTML parts in DCA Box
content = content.replace("THÔNG SỐ GIÁ ZW (ZWZ26) - Cập nhật: {zw_date}", "{sym_text}")
content = content.replace("Cuối T11 - Giữa T12/2026", "{dca_time}")
content = content.replace("Khi áp lực xả hàng Úc+Argentina đạt đỉnh, El Niño bắt đầu ảnh hưởng Q1/2027", "{dca_reason}")
content = content.replace("{s1:.0f} - 680¢", "{z1_price}")
content = content.replace("{s2:.0f} - 620¢", "{z2_price}")
# Note: 'THONG S? GIA ZW (ZWZ26)' - wait, the file has no accents in some places?
# Ah, looking at my cat output: '?? THONG S? GIA ZW (ZWZ26) - C?p nh?t: {zw_date}'
# Let's use regex to replace it safely because of encoding.

content = re.sub(r'THONG S\? GIA ZW \(ZWZ26\) - C\?p nh\?t: \{zw_date\}', '{sym_text}', content)
content = re.sub(r'Cu\?i T11 - Gi\?a T12/2026', '{dca_time}', content)
content = re.sub(r'Khi p l\?c x\? hng Uc\+Argentina d\?t d\?nh, El Nio b\?t d\?u \?nh hu\?ng Q1/2027', '{dca_reason}', content)
# Since `cat` output showed corrupted characters, it's safer to use python `f.read()` string matching directly since it reads actual utf-8 characters correctly.
# But wait, my manual replacements were using actual UTF-8:
# content = content.replace("THÔNG SỐ GIÁ ZW (ZWZ26) - Cập nhật: {zw_date}", "{sym_text}")
# This will work because the file actually has "THÔNG SỐ GIÁ" inside it. It only printed wrong in powershell due to console encoding.

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
