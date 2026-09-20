import re

file_path = 'pages/6_MuaVu.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add new imports/loaders at the top
new_loaders = """
@st.cache_data(ttl=60)
def load_macro_scores():
    p = DATA_OUTPUT / "macro_scores.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

@st.cache_data(ttl=60)
def load_macro_weights():
    p = DATA_OUTPUT / "macro_weights.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

macro_scores = load_macro_scores()
macro_weights = load_macro_weights()
breakdown = macro_scores.get("breakdown", {})
forecast_3m = macro_weights.get("price_forecast", {})

f2w = breakdown.get("F2W", {})
weather_detail = f2w.get("raw_detail", "Không có cảnh báo thời tiết đặc biệt.")

def render_top_badges():
    top_factors = sorted(
        [k for k in breakdown.keys() if k not in ["F2W"]],
        key=lambda k: breakdown[k].get("weight_pct", 0),
        reverse=True
    )[:4]
    
    html = "<div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;'>"
    for k in top_factors:
        f_data = breakdown.get(k, {})
        weight = f_data.get("weight_pct", 0)
        score = f_data.get("score_1_to_10", 5)
        label_map = {"F1": "Biển Đen", "F2": "WASDE", "F3": "S.Lượng Các Nước", "F4": "T.Tiết Nam Bán Cầu", 
                     "F4S": "S.Lượng Nam Bán Cầu", "F5": "Xuất Khẩu", "F6": "Tồn Kho Mỹ", "F7": "Tồn Kho T.Giới",
                     "F8": "Địa Chính Trị", "F9": "DXY", "F10": "Dầu Thô", "F11": "COT", "F12": "Tin Tức"}
        label = label_map.get(k, k)
        bg = "#7f1d1d" if score <= 3 else "#1c3d5a" if score <= 7 else "#1e3a1e"
        col = "#fca5a5" if score <= 3 else "#93c5fd" if score <= 7 else "#86efac"
        icon = "🔴" if score <= 3 else "⚖️" if score <= 7 else "🟢"
        html += f"<span class='badge' style='background:{bg}; color:{col};'>{icon} {label} ({score}/10)</span>"
    html += "</div>"
    return html

def render_forecast_3m():
    html = "<div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:15px;'>"
    for month_key, f_data in forecast_3m.items():
        html += f'''
        <div class="metric-box" style="border-color:#3b82f6;">
            <div style="font-size:12px; font-weight:700; color:#93c5fd; margin-bottom:4px;">Tháng {month_key.replace("_", "/")}</div>
            <div style="font-size:14px; font-weight:800; color:#e2e8f0;">{f_data.get("low")} - {f_data.get("high")}</div>
            <div style="font-size:11px; color:#cbd5e1; margin-top:6px; line-height:1.4;">{f_data.get("note", "")}</div>
        </div>
        '''
    html += "</div>"
    return html
"""

content = content.replace("bs_up = bs_data.get(\"timestamp\", \"—\")", "bs_up = bs_data.get(\"timestamp\", \"—\")\n\n" + new_loaders)


# 2. Replace the El Nino Banner
old_banner = """# ── El Niño Alert Banner ────────────────────────────────────────────────────────
st.markdown(\"\"\"
<div style='background: linear-gradient(135deg, #7c2d12 0%, #991b1b 100%);
            border: 1px solid #ef4444; border-radius: 12px;
            padding: 14px 20px; margin-bottom: 20px;
            display:flex; align-items:center; gap:14px;'>
  <div style='font-size:32px;'>🌪️</div>
  <div>
    <div style='font-size:14px; font-weight:800; color:#fca5a5;'>CẢNH BÁO: KỊch Bản KHỦNG HOẢNG THỜI TIẾT — EL NIÑO 82%</div>
    <div style='font-size:12px; color:#fecaca; margin-top:3px;'>
      Năm 2026 xác nhận chu kỳ El Niño (82% xác suất). Quy luật giảm giá mùa gặt thông thường SẼ BỊ BẺ GÃY.
      Nhịp giảm sẽ cực nông (rũ bỏ) → Đảo chiều tăng mạnh vào Q4.
      <b>KHÔNG áp dụng tư duy "bán tháo mùa vụ" vào năm 2026.</b>
    </div>
  </div>
</div>
\"\"\", unsafe_allow_html=True)"""

new_banner = """# ── Weather Alert Banner (Synced with Macro F2W) ─────────────────────────────
st.markdown(f\"\"\"
<div style='background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            border: 1px solid #3b82f6; border-radius: 12px;
            padding: 14px 20px; margin-bottom: 20px;
            display:flex; align-items:center; gap:14px;'>
  <div style='font-size:32px;'>🌤️</div>
  <div>
    <div style='font-size:14px; font-weight:800; color:#93c5fd;'>TÌNH HÌNH THỜI TIẾT & ENSO (Cập nhật từ Ma Trận Vĩ Mô)</div>
    <div style='font-size:12px; color:#bfdbfe; margin-top:3px;'>
      {weather_detail}
    </div>
  </div>
</div>
\"\"\", unsafe_allow_html=True)"""

content = content.replace(old_banner, new_banner)


# 3. ZW Tab - Badges & Russian Wheat & Forecast
content = re.sub(
    r"<!-- BADGES -->.*?</div>",
    r"<!-- DYNAMIC BADGES -->\n          {render_top_badges()}",
    content,
    count=1,
    flags=re.DOTALL
)

# Replace ZW Forecast cycle
zw_forecast_old = r'<div class="section-title">📊 Phân Tích Chu Kỳ 10 Năm.*?</div>\s*</div>\s*</div>'
zw_forecast_new = r'''<div class="section-title">📊 Dự Báo Khung Giá 3 Tháng (Từ Ma Trận Vĩ Mô)</div>
        {render_forecast_3m()}
'''
content = re.sub(zw_forecast_old, zw_forecast_new, content, flags=re.DOTALL)

# Replace Russian Wheat block with macro-based one
russian_old = r'<!-- BLOCK RUSSIAN WHEAT -->.*?(?=</div>\s*""", unsafe_allow_html=True)'
f1_detail = '{breakdown.get("F1", {}).get("raw_detail", "")}'
russian_new = f'''<!-- BLOCK RUSSIAN WHEAT -->
          <div style='font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px; margin-top:14px;'>VI. Yếu Tố Biển Đen & Địa Chính Trị (Nga/Ukraine) 🇷🇺 🇺🇦</div>
          <div class='card' style='border-color:#3b0764; background:#1e1b4b; padding:12px; margin-bottom:14px;'>
            <div style='font-size:12px; color:#c4b5fd; line-height:1.6;'>
              📌 <b>Cập nhật từ Macro F1:</b> {f1_detail}
            </div>
          </div>
        </div>'''
content = re.sub(russian_old, russian_new, content, flags=re.DOTALL)


# 4. ZC Tab - Badges & Forecast
content = re.sub(
    r"<!-- BADGES -->.*?</div>",
    r"<!-- DYNAMIC BADGES -->\n          {render_top_badges()}",
    content,
    count=1,
    flags=re.DOTALL
)

# Replace ZC Forecast cycle
zc_forecast_old = r'<div class="section-title">📊 Phân Tích Kịch Bản & Điểm Đảo Chiều.*?</div>\s*</div>\s*</div>'
zc_forecast_new = r'''<div class="section-title">📊 Dự Báo Khung Giá 3 Tháng (Từ Ma Trận Vĩ Mô)</div>
        {render_forecast_3m()}
'''
content = re.sub(zc_forecast_old, zc_forecast_new, content, flags=re.DOTALL)

# Also fix the f-string issue if the badges variable is injected
content = content.replace("          {render_top_badges()}", "\n          \"\"\" + render_top_badges() + \"\"\"")
content = content.replace("        {render_forecast_3m()}", "\n        \"\"\" + render_forecast_3m() + \"\"\"")


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully.")
