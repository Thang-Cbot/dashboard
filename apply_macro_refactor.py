import re

with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. F1 Blacksea
f1_pattern = r'def score_f1_blacksea\(manual_overrides, bs_data, commodity="ZW"\):\n    """F1: Nga/Ukraine Black Sea supply via manual override \+ blacksea data\."""\n    if commodity == "ZC": return \{"score": 3, "raw_value": "Ukraine XK \(F1\)", "raw_detail": "Ukraine duy trì tiến độ xuất khẩu Ngô an toàn. Nga không phải yếu tố Ngô trọng điểm.", "last_updated": "Hiện tại", "status": "manual"\}\n    \n    file_ok = \(OUTPUT_DIR / "blacksea_wheat\.json"\)\.exists\(\)\n    last_up  = get_file_mtime\(OUTPUT_DIR / "blacksea_wheat\.json"\)\n\n    # Try to get raw value from blacksea file\n    raw_val = "Dữ liệu Chuyên gia"\n    raw_detail = ""\n    if bs_data:\n        try:\n            # Try to find an export rate\n            for k, v in bs_data\.items\(\):\n                if isinstance\(v, dict\) and "export_mt" in v:\n                    raw_val = f"\{v\[\'export_mt\'\]:,\.0f\} tấn/tháng"\n                    break\n                if isinstance\(v, dict\) and "price_fob" in v:\n                    raw_detail = f"FOB: \$\{v\[\'price_fob\'\]\}"\n        except:\n            pass\n\n    ov = manual_overrides\.get\("F1_Russia_Policy", \{\}\)'

f1_replacement = """def score_f1_blacksea(manual_overrides, bs_data, commodity="ZW"):
    \"\"\"F1: Nga/Ukraine Black Sea supply via manual override + blacksea data.\"\"\"
    ov = manual_overrides.get(f"F1_Ukraine_Policy_{commodity}", manual_overrides.get(f"F1_Russia_Policy_{commodity}", manual_overrides.get("F1_Russia_Policy", {})))
    
    if not ov and commodity == "ZC": 
        return {"score": 3, "raw_value": "Ukraine XK (F1)", "raw_detail": "Ukraine duy trì tiến độ xuất khẩu Ngô an toàn. Nga không phải yếu tố Ngô trọng điểm.", "last_updated": "Hiện tại", "status": "manual"}
    
    file_ok = (OUTPUT_DIR / "blacksea_wheat.json").exists()
    last_up  = get_file_mtime(OUTPUT_DIR / "blacksea_wheat.json")

    raw_val = "Dữ liệu Chuyên gia"
    raw_detail = ""
    if bs_data:
        try:
            for k, v in bs_data.items():
                if isinstance(v, dict) and "export_mt" in v:
                    raw_val = f"{v['export_mt']:,.0f} tấn/tháng"
                    break
                if isinstance(v, dict) and "price_fob" in v:
                    raw_detail = f"FOB: ${v['price_fob']}"
        except:
            pass"""

# 2. F3 Other Supply
f3_pattern = r'def score_f3_other_supply\(manual_overrides, commodity="ZW"\):\n    if commodity == "ZC": return \{"score": 2, "raw_value": "Mất thị phần TQ", "raw_detail": "Trung Quốc mua Ngô Brazil. Brazil soán ngôi Mỹ. MEGA BEARISH", "last_updated": "Hiện tại", "status": "manual"\}\n    """F3: Nguồn Cung Khác \(EU, Canada, Ấn Độ\.\.\.\) - manual\."""\n    ov    = manual_overrides\.get\("F3_Other_Supply", \{\}\)'
f3_replacement = """def score_f3_other_supply(manual_overrides, commodity="ZW"):
    \"\"\"F3: Nguồn Cung Khác (EU, Canada, Ấn Độ...) - manual.\"\"\"
    ov = manual_overrides.get(f"F3_Other_Supply_{commodity}", manual_overrides.get("F3_Other_Supply", {}))
    if not ov and commodity == "ZC":
        return {"score": 2, "raw_value": "Mất thị phần TQ", "raw_detail": "Trung Quốc mua Ngô Brazil. Brazil soán ngôi Mỹ. MEGA BEARISH", "last_updated": "Hiện tại", "status": "manual"}"""

# 3. F4S Supply SH
f4s_pattern = r'def score_f4s_supply_sh\(manual_overrides, commodity="ZW"\):\n    if commodity == "ZC": return \{"score": 2, "raw_value": "Mùa vụ Nam Mỹ", "raw_detail": "Brazil là nước XK Ngô #1. Úc bị loại khỏi biến số \(ít Ngô\). MEGA BEARISH", "last_updated": "Hiện tại", "status": "manual"\}\n    """F4S: Nguồn Cung Nam Bán Cầu \(Úc, Argentina\) - sản lượng dự báo\."""\n    ov    = manual_overrides\.get\("F4S_Supply_SH", \{\}\)'
f4s_replacement = """def score_f4s_supply_sh(manual_overrides, commodity="ZW"):
    \"\"\"F4S: Nguồn Cung Nam Bán Cầu (Úc, Argentina) - sản lượng dự báo.\"\"\"
    ov = manual_overrides.get(f"F4S_Supply_SH_{commodity}", manual_overrides.get("F4S_Supply_SH", {}))
    if not ov and commodity == "ZC":
        return {"score": 2, "raw_value": "Mùa vụ Nam Mỹ", "raw_detail": "Brazil là nước XK Ngô #1. Úc bị loại khỏi biến số (ít Ngô). MEGA BEARISH", "last_updated": "Hiện tại", "status": "manual"}"""

# 4. F8 Geopolitics
f8_pattern = r'def score_f8_geopolitics\(manual_overrides, commodity="ZW"\):\n    if commodity == "ZC": return \{"score": 5, "raw_value": "Logistics & Biển Đen", "raw_detail": "Chiến sự Biển Đen giảm nhiệt, tắc nghẽn vận tải không còn là điểm nóng\.", "last_updated": "Hiện tại", "status": "manual"\}\n    """F8: Geopolitics & Logistics - manual\."""\n    ov    = manual_overrides\.get\("F8_Geopolitics", \{\}\)'
f8_replacement = """def score_f8_geopolitics(manual_overrides, commodity="ZW"):
    \"\"\"F8: Geopolitics & Logistics - manual.\"\"\"
    ov = manual_overrides.get(f"F8_Geopolitics_{commodity}", manual_overrides.get("F8_Geopolitics", {}))
    if not ov and commodity == "ZC":
        return {"score": 5, "raw_value": "Logistics & Biển Đen", "raw_detail": "Chiến sự Biển Đen giảm nhiệt, tắc nghẽn vận tải không còn là điểm nóng.", "last_updated": "Hiện tại", "status": "manual"}"""

# 5. F12 Global Demand
f12_pattern = r'def score_f12_global_demand\(manual_overrides, commodity="ZW"\):\n    if commodity == "ZC": return \{"score": 4, "raw_value": "Nhu cầu suy yếu", "raw_detail": "Nhu cầu thức ăn chăn nuôi toàn cầu yếu do lo ngại kinh tế và dịch bệnh\.", "last_updated": "Hiện tại", "status": "manual"\}\n    """F12: Nhu Cầu Toàn Cầu \(Global Demand\) - Ai Cập, Ả Rập, Trung Quốc\.\.\."""\n    ov    = manual_overrides\.get\("F12_Global_Demand", \{\}\)'
f12_replacement = """def score_f12_global_demand(manual_overrides, commodity="ZW"):
    \"\"\"F12: Nhu Cầu Toàn Cầu (Global Demand) - Ai Cập, Ả Rập, Trung Quốc...\"\"\"
    ov = manual_overrides.get(f"F12_Global_Demand_{commodity}", manual_overrides.get("F12_Global_Demand", {}))
    if not ov and commodity == "ZC":
        return {"score": 4, "raw_value": "Nhu cầu suy yếu", "raw_detail": "Nhu cầu thức ăn chăn nuôi toàn cầu yếu do lo ngại kinh tế và dịch bệnh.", "last_updated": "Hiện tại", "status": "manual"}"""

content = re.sub(f1_pattern, f1_replacement, content)
content = re.sub(f3_pattern, f3_replacement, content)
content = re.sub(f4s_pattern, f4s_replacement, content)
content = re.sub(f8_pattern, f8_replacement, content)
content = re.sub(f12_pattern, f12_replacement, content)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
