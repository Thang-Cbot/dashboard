"""
pages/5_Macro_Matrix.py — Hệ thống Phân tích Vĩ mô Định lượng (CBOT Macro Brain)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Macro Matrix — CBOT Brain", page_icon="🧠", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"
BASE_DIR = Path(__file__).parent.parent

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0b0f19; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* Dashboard Cards */
.macro-card {
    background: linear-gradient(145deg, #161e2e 0%, #0f1629 100%);
    border: 1px solid #2a3a5c;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
.section-title {
    font-size: 14px; font-weight: 800; color: #94a3b8;
    letter-spacing: 2px; text-transform: uppercase;
    border-bottom: 1px solid #2a3a5c;
    padding-bottom: 8px; margin-bottom: 16px;
}

/* Gauge Chart / Score styling */
.score-container {
    text-align: center;
    padding: 20px 0;
}
.score-number {
    font-size: 80px;
    font-weight: 900;
    line-height: 1;
    text-shadow: 0 0 20px rgba(255,255,255,0.1);
}
.score-trend {
    font-size: 24px;
    font-weight: 800;
    margin-top: 10px;
    letter-spacing: 1px;
}

/* Matrix Table Styling */
.matrix-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 6px;
}
.matrix-table th {
    text-align: left;
    padding: 12px 16px;
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid #2a3a5c;
}
.matrix-row {
    background: #111827;
    transition: transform 0.2s, background 0.2s;
}
.matrix-row:hover {
    background: #1e293b;
    transform: translateX(4px);
}
.matrix-cell {
    padding: 14px 16px;
    font-size: 13px;
    border-top: 1px solid #1e293b;
    border-bottom: 1px solid #1e293b;
}
.matrix-row td:first-child { border-left: 1px solid #1e293b; border-radius: 8px 0 0 8px; }
.matrix-row td:last-child { border-right: 1px solid #1e293b; border-radius: 0 8px 8px 0; }

.factor-name { font-weight: 700; color: #e2e8f0; font-size: 14px; }
.factor-desc { font-size: 11px; color: #64748b; margin-top: 4px; }
.weight-badge { 
    background: #1e293b; color: #94a3b8; 
    padding: 4px 8px; border-radius: 6px; 
    font-weight: 700; font-size: 12px;
}
.base-score { font-size: 16px; font-weight: 800; }
.contrib-score { font-size: 18px; font-weight: 900; }
</style>""", unsafe_allow_html=True)

# ── Sidebar nav ────────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết")
st.sidebar.page_link("pages/5_Macro_Matrix.py", label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

if st.sidebar.button("🧹 LÀM MỚI DỮ LIỆU", use_container_width=True):
    # Try running macro engine directly
    try:
        sys.path.insert(0, str(BASE_DIR / "Data"))
        from macro_engine import calculate_macro_score
        calculate_macro_score()
    except Exception as e:
        st.error(f"Lỗi: {e}")
    st.cache_data.clear()
    st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_scores():
    p = DATA_OUTPUT / "macro_scores.json"
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return None

@st.cache_data(ttl=60)
def load_weights_config():
    p = BASE_DIR / "Data" / "macro_weights.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

scores_data = load_scores()
weights_cfg = load_weights_config()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 20px 0 10px;'>
  <div style='font-size:32px; font-weight:900; color:#f8fafc; letter-spacing:-1px;'>🧠 THE MACRO MATRIX BRAIN</div>
  <div style='font-size:14px; color:#64748b; margin-top:6px;'>
    Hệ thống phân tích Định lượng Vĩ mô (Quantitative Macro Engine) | Tự động chấm điểm 11 yếu tố cốt lõi CBOT.
  </div>
</div>
""", unsafe_allow_html=True)

if not scores_data:
    st.warning("Chưa có dữ liệu Macro Scores. Đang chờ Engine chạy...")
    st.stop()

# ── Extract Data ──────────────────────────────────────────────────────────────
tot_score = scores_data.get("total_score", 50)
trend = scores_data.get("trend", "Neutral")
month = scores_data.get("month", "?")
up_time = scores_data.get("timestamp", "—")
breakdown = scores_data.get("breakdown", {})

# Determine Colors based on Score
if tot_score < 30: 
    color_hex, bg_grad = "#ef4444", "linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)" # Strong Bear
elif tot_score < 45: 
    color_hex, bg_grad = "#f87171", "linear-gradient(135deg, #450a0a 0%, #171717 100%)" # Slight Bear
elif tot_score < 55: 
    color_hex, bg_grad = "#94a3b8", "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)" # Neutral
elif tot_score < 70: 
    color_hex, bg_grad = "#4ade80", "linear-gradient(135deg, #064e3b 0%, #171717 100%)" # Slight Bull
else: 
    color_hex, bg_grad = "#22c55e", "linear-gradient(135deg, #14532d 0%, #064e3b 100%)" # Strong Bull

# ── Top Section: The Gauge & Month Control ──────────────────────────────────────
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown(f"""
    <div class='macro-card' style='background: {bg_grad}; border-color: {color_hex}40;'>
        <div style='font-size:11px; font-weight:800; color:#e2e8f0; text-transform:uppercase; letter-spacing:2px; text-align:center;'>
            XU HƯỚNG VĨ MÔ — THÁNG {month}
        </div>
        <div class='score-container'>
            <div class='score-number' style='color: {color_hex};'>{tot_score}</div>
            <div class='score-trend' style='color: {color_hex};'>{trend}</div>
        </div>
        <div style='text-align:center; font-size:10px; color:#94a3b8; margin-top:10px;'>
            Cập nhật: {up_time}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='macro-card' style='padding: 16px;'>
        <div style='font-size:11px; font-weight:700; color:#64748b; margin-bottom:8px;'>THANG ĐIỂM ENGINE (0-100)</div>
        <div style='display:flex; justify-content:space-between; font-size:10px; font-weight:700; margin-bottom:4px;'>
            <span style='color:#ef4444;'>0-30: Giảm Mạnh</span>
            <span style='color:#f87171;'>31-45: Giảm Nhẹ</span>
        </div>
        <div style='display:flex; justify-content:space-between; font-size:10px; font-weight:700; margin-bottom:4px;'>
            <span style='color:#94a3b8;'>46-55: Đi Ngang</span>
            <span style='color:#4ade80;'>56-70: Tăng Nhẹ</span>
        </div>
        <div style='display:flex; justify-content:space-between; font-size:10px; font-weight:700;'>
            <span></span>
            <span style='color:#22c55e;'>71-100: Tăng Mạnh</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Define factor names and descriptions
factor_dict = {
    "F1": {"name": "Nguồn Cung Biển Đen", "desc": "Nga & Ukraine: Tốc độ xuất khẩu, giá FOB, Thuế"},
    "F2": {"name": "Nguồn Cung Mỹ (Crop Progress)", "desc": "Tiến độ gieo gặt, Chất lượng G/E, Năng suất"},
    "F3": {"name": "Nguồn Cung EU & Canada", "desc": "Thời tiết Châu Âu, Pháp (FranceAgriMer)"},
    "F4": {"name": "Thời Tiết Nam Bán Cầu", "desc": "Úc / Argentina (Rủi ro El Nino/La Nina)"},
    "F5": {"name": "Báo Cáo Xuất Khẩu Mỹ", "desc": "Weekly Export Sales (Nhu cầu thực tế)"},
    "F6": {"name": "Tồn Kho Mỹ (US Stocks)", "desc": "Ending Stocks % Change (WASDE)"},
    "F7": {"name": "Tồn Kho Toàn Cầu (Global Stocks)", "desc": "World Ending Stocks % Change (WASDE)"},
    "F8": {"name": "Địa Chính Trị & Logistics", "desc": "Rủi ro chiến tranh Biển Đen, Tắc nghẽn vận tải"},
    "F9": {"name": "Sức Mạnh USD (DXY)", "desc": "Năng lực cạnh tranh xuất khẩu của Mỹ"},
    "F10": {"name": "Giá Dầu Thô (WTI)", "desc": "Chi phí cước tàu & Phân bón"},
    "F11": {"name": "Vị Thế Các Quỹ (COT)", "desc": "Dòng tiền Smart Money (Rủi ro Short Squeeze)"},
}

with col2:
    st.markdown('<div class="section-title">BẢNG MA TRẬN 11 YẾU TỐ (FIXED FACTORS)</div>', unsafe_allow_html=True)
    
    # Sort factors by contribution descending
    sorted_factors = sorted(breakdown.items(), key=lambda x: x[1]['contribution'], reverse=True)
    
    # Generate Table HTML
    table_html = """<table class='matrix-table'>
<tr>
<th width='35%'>Yếu Tố Vĩ Mô / Giá Trị Thực</th>
<th width='12%' style='text-align:center;'>Điểm Gốc<br>(1-10)</th>
<th width='12%' style='text-align:center;'>Tỷ Trọng<br>(Weight%)</th>
<th width='12%' style='text-align:center;'>Điểm Góp</th>
<th width='18%' style='text-align:center;'>Xu Hướng</th>
<th width='11%' style='text-align:center;'>Cập Nhật</th>
</tr>"""
    
    for f_key, f_data in sorted_factors:
        meta        = factor_dict.get(f_key, {"name": f_key, "desc": ""})
        base        = f_data.get('score_1_to_10', 5)
        weight      = f_data.get('weight_pct', 0)
        contrib     = f_data.get('contribution', 0)
        raw_value   = f_data.get('raw_value', 'N/A')
        raw_detail  = f_data.get('raw_detail', '')
        last_up     = f_data.get('last_updated', '—')
        status      = f_data.get('status', 'error')

        # Color coding for base score (1-10)
        if base <= 3:   b_col, b_bg = "#ef4444", "rgba(239,68,68,0.1)"
        elif base <= 4: b_col, b_bg = "#f87171", "rgba(248,113,113,0.1)"
        elif base <= 6: b_col, b_bg = "#94a3b8", "rgba(148,163,184,0.1)"
        elif base <= 8: b_col, b_bg = "#4ade80", "rgba(74,222,128,0.1)"
        else:           b_col, b_bg = "#22c55e", "rgba(34,197,94,0.1)"

        # Status dot
        if status == "ok":      dot = "🟢"; dot_tip = "Tự động cập nhật"
        elif status == "manual": dot = "🟡"; dot_tip = "Nhập thủ công"
        else:                   dot = "🔴"; dot_tip = "Lỗi / Không có dữ liệu"

        # Trend text badge
        if weight == 0:
            trend_html = "<span style='color:#475569; font-size:11px;'>N/A tháng này</span>"
        elif base <= 3:
            trend_html = "<span style='background:#7f1d1d; color:#fca5a5; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;'>▼ Giảm Mạnh</span>"
        elif base <= 4:
            trend_html = "<span style='background:#450a0a; color:#f87171; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;'>▼ Giảm Nhẹ</span>"
        elif base <= 6:
            trend_html = "<span style='background:#1e293b; color:#94a3b8; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;'>— Trung Lập</span>"
        elif base <= 8:
            trend_html = "<span style='background:#064e3b; color:#4ade80; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;'>▲ Tăng Nhẹ</span>"
        else:
            trend_html = "<span style='background:#14532d; color:#22c55e; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;'>▲ Tăng Mạnh</span>"

        # Last updated - show just time part if today
        try:
            from datetime import date
            if last_up not in ("Thủ công", "—") and len(last_up) > 10:
                up_date = last_up[:10]
                up_time_only = last_up[11:]
                today_str = date.today().strftime("%Y-%m-%d")
                if up_date == today_str:
                    last_up_show = f"Hôm nay {up_time_only}"
                else:
                    last_up_show = last_up
            else:
                last_up_show = last_up
        except:
            last_up_show = last_up

        table_html += f"""<tr class='matrix-row'>
<td class='matrix-cell'>
<div class='factor-name'>{dot} {meta['name']} <span style='font-size:10px; color:#475569;'>[{f_key}]</span></div>
<div class='factor-desc' style='color:#94a3b8; margin-top:3px;'>{raw_value}</div>
<div class='factor-desc'>{raw_detail}</div>
</td>
<td class='matrix-cell' style='text-align:center;'>
<span class='base-score' style='color:{b_col};'>{base}</span>
</td>
<td class='matrix-cell' style='text-align:center;'>
<span class='weight-badge'>{weight}%</span>
</td>
<td class='matrix-cell' style='text-align:center;'>
<span class='contrib-score' style='color:{b_col};'>{contrib}</span>
</td>
<td class='matrix-cell' style='text-align:center;'>
{trend_html}
</td>
<td class='matrix-cell' style='text-align:center; font-size:10px; color:#64748b;'>
{last_up_show}
</td>
</tr>"""
        
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.markdown("""
<div style='font-size:11px; color:#64748b; margin-top:16px; padding:12px; background:#111827; border-radius:8px; border: 1px dashed #2a3a5c;'>
<b>💡 Cách đọc Ma trận:</b><br>
🟢 Tự động cập nhật từ API/Data &nbsp;|&nbsp; 🟡 Nhập thủ công (cần cập nhật định kỳ) &nbsp;|&nbsp; 🔴 Lỗi / Không có data<br>
<b>Điểm Gốc (1-10):</b> 1=Cực Bearish cho giá ZW &nbsp; 5=Trung Lập &nbsp; 10=Cực Bullish.<br>
<b>Tỷ Trọng:</b> % ảnh hưởng của yếu tố trong <b>tháng hiện tại</b>. Tháng khác nhau → Tỷ trọng khác nhau.<br>
<b>Điểm Góp = Điểm Gốc × Tỷ Trọng.</b> Tổng tất cả Điểm Góp ×10 = Tổng Điểm Vĩ Mô (0-100).
</div>
    """, unsafe_allow_html=True)

