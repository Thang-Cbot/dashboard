import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the DYNAMIC MACRO VALUATION block
pattern1 = r'# DYNAMIC MACRO VALUATION \(Cach 2\).*?except:.*?\)'

def replace_macro_logic(m):
    return """# DYNAMIC MACRO VALUATION (Cach 2 + War Premium)
        try:
            o_val = float(oil_live)
            d_val = float(dxy_live)
            try: f8_val = float(f8_s.get("score_1_to_10", 5))
            except: f8_val = 5.0
            
            if commodity == "ZW":
                war_premium = f8_val * 5.0
                fv = 520 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + war_premium
                macro_z1 = f"{fv-15:.0f} - {fv+15:.0f}¢"
                macro_text = f"Biến thiên Real-time: Hụt cung 18.5% | War Premium (F8={f8_val:.0f}): +{war_premium:.0f}¢ | Dầu: {o_val:.1f}$ | DXY: {d_val:.1f}"
            else:
                fv = 400 + (o_val - 70)*2.0 + (100 - d_val)*3.0 + 10
                macro_z1 = f"{fv-10:.0f} - {fv+10:.0f}¢"
                macro_text = f"Biến thiên Real-time: Dầu: {o_val:.1f}$ | DXY: {d_val:.1f}"
        except:
            macro_z1 = dca_targets.get(commodity, {}).get("zone1", "550 - 580¢" if commodity == "ZW" else "400 - 420¢")
            macro_text = "Cơ sở định giá: Lỗi tải dữ liệu động" """

content = re.sub(pattern1, replace_macro_logic, content, flags=re.DOTALL)

# 2. Update the HTML text below it to use {macro_text}
# Currently it is: <div style='font-size:11px;color:#94a3b8;'>Cơ sở định giá (Cố định): War Premium | Dầu thô | DXY</div>
pattern2 = r"<div style='font-size:11px;color:#94a3b8;'>Cơ sở định giá \(Cố định\): War Premium \| Dầu thô \| DXY</div>"
replacement2 = "<div style='font-size:11px;color:#94a3b8;'>{macro_text}</div>"
content = re.sub(pattern2, replacement2, content)

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied Dynamic War Premium successfully!")
