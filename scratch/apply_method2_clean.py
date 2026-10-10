import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace macro_z1 assignments with Method 2 dynamic calculation
pattern1 = r'macro_z1 = dca_targets\.get\(commodity, \{\}\)\.get\("zone1", "[^"]+"\)'

def replace_macro_logic(m):
    return """# DYNAMIC MACRO VALUATION (Cach 2)
        try:
            o_val = float(oil_live)
            d_val = float(dxy_live)
            if commodity == "ZW":
                fv = 550 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + 30
                macro_z1 = f"{fv-15:.0f} - {fv+15:.0f}¢"
            else:
                fv = 400 + (o_val - 70)*2.0 + (100 - d_val)*3.0 + 10
                macro_z1 = f"{fv-10:.0f} - {fv+10:.0f}¢"
        except:
            macro_z1 = dca_targets.get(commodity, {}).get("zone1", "550 - 580¢" if commodity == "ZW" else "400 - 420¢")"""

content = re.sub(pattern1, replace_macro_logic, content)

# Replace the text under the macro zone to explain the dynamic variables
pattern2 = r"Đáy cấu trúc Vĩ mô / Giá thành sản xuất \(Cấu hình tùy chỉnh\)"
replacement2 = "Trục Giá Trị Động. Tính toán tự động theo: Dầu thô ({oil_live}$) | DXY ({dxy_live})"

content = re.sub(pattern2, replacement2, content)

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied Method 2 cleanly!")
