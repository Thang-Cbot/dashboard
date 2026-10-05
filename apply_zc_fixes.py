import re

# 1. Update macro_engine.py to override F1 for ZC
with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    me_code = f.read()

pattern_f1 = r'(def score_f1_blacksea\(manual_overrides, bs_data, commodity="ZW"\):\n.*?\")'
replace_f1 = r'\1\n    if commodity == "ZC": return {"score": 3, "raw_value": "Ukraine XK (F1)", "raw_detail": "Ukraine duy trì tiến độ xuất khẩu Ngô an toàn. Nga không phải yếu tố Ngô trọng điểm.", "last_updated": "Hiện tại", "status": "manual"}\n'

me_code = re.sub(pattern_f1, replace_f1, me_code)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(me_code)

# 2. Update 6_MuaVu.py to make enso_impact ZC-specific
with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    mv_code = f.read()

enso_logic = """    def enso_impact(region_key):
        if commodity == "ZC":
            if "Mỹ" in region_key and "Nam" not in region_key:
                return "<span style='color:#94a3b8;font-weight:700;'>NEUTRAL</span> — Đang vụ Thu Hoạch, hiện tượng El Nino ít đe dọa trực tiếp tới nguồn cung."
            if "Brazil" in region_key:
                return "<span style='color:#ef4444;font-weight:700;'>BULLISH</span> — Rủi ro khô hạn cục bộ ảnh hưởng vụ Safrinha đầu năm."
            if "Argentina" in region_key:
                return "<span style='color:#22c55e;font-weight:700;'>BEARISH</span> — Tháng 10-12 (Gieo hạt). Mưa thuận lợi cho gieo trồng ngô."
            if "Trung Quốc" in region_key or "Ukraine" in region_key:
                return "—"

        for imp in weather_long.get("impacts", []):
            if region_key in imp.get("region", ""):
                bias_col = "#ef4444" if imp["bias"]=="BULLISH" else "#22c55e"
                return f"<span style='color:{bias_col};font-weight:700;'>{imp['bias']}</span> — {imp['effect'][:80]}"
        return "—"
"""

mv_code = re.sub(r'    def enso_impact\(region_key\):.*?return "—"\n', enso_logic, mv_code, flags=re.DOTALL)

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(mv_code)
