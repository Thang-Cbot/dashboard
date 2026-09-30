"""
pages/6_MuaVu.py - Phân tích Mùa Vụ 2026 (ZW & ZC)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
import subprocess
from pathlib import Path

st.set_page_config(page_title="Mùa Vụ 2026 - CBOT", page_icon="🌾", layout="wide")

BASE_DIR = Path(__file__).parent.parent
DATA_OUTPUT = BASE_DIR / "Data" / "output"

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0b0f19; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; }
[data-testid="stSidebarNav"] { display: none !important; }

.mv-card {
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 8px;
    background: #111827;
}
.mv-card-title {
    font-size: 11px; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    border-bottom: 1px solid #1e2d45; padding-bottom: 6px;
}
.mv-card-value { font-size: 15px; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
.mv-card-detail { font-size: 11px; color: #94a3b8; line-height: 1.6; }

/* Regional Table */
.reg-table { width:100%; border-collapse: collapse; margin-top: 8px; }
.reg-table th {
    padding: 10px 14px; font-size: 11px; font-weight: 700;
    color: #64748b; text-transform: uppercase; letter-spacing: 1px;
    border-bottom: 2px solid #2a3a5c; text-align: left;
    background: #0b0f19;
}
.reg-table td {
    padding: 12px 14px; font-size: 12px; color: #cbd5e1;
    border-bottom: 1px solid #1e2d45; vertical-align: top;
    line-height: 1.7;
}
.reg-table tr:hover td { background: #161e2e; }
.region-header { font-weight: 700; color: #e2e8f0; font-size: 13px; }
.region-flag { font-size: 16px; margin-right: 6px; }
.harvest-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 700; background: #1e3a5f; color: #60a5fa;
    margin-bottom: 4px;
}
.dot-green { color: #22c55e; font-weight: bold; }
.dot-yellow { color: #eab308; font-weight: bold; }
.dot-red { color: #ef4444; font-weight: bold; }
.score-pill {
    display: inline-block; padding: 1px 7px; border-radius: 6px;
    font-size: 11px; font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=60)
def load_json(filename):
    p = DATA_OUTPUT / filename
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except: return {}
    return {}

macro      = load_json("macro_scores.json")
fund       = load_json("fundamental_data.json")
cot        = load_json("cot_data.json")
ai_analysis= load_json("ai_muavu_analysis.json")
export_s   = load_json("export_sales.json")

breakdown  = macro.get("breakdown", {})
cot_zw     = cot.get("commodities", {}).get("001602", {})

# ─── SIDEBAR NAV ─────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",                    label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py",       label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py",       label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",           label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",        label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",        label="🗺️ Bản Đồ Thời Tiết")
st.sidebar.page_link("pages/5_Macro_Matrix.py",   label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",          label="🌾 Mùa Vụ 2026")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Cập Nhật Mùa Vụ (AI)", type="primary", use_container_width=True):
    with st.sidebar.status("⏳ Đang phân tích...", expanded=True) as _s:
        env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
        script_path = str(BASE_DIR / "Data" / "analyze_muavu_ai.py")
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, env=env)
        if res.returncode == 0:
            _s.update(label="✅ Cập nhật AI thành công!", state="complete", expanded=False)
        else:
            _s.update(label="❌ Lỗi khi gọi AI", state="error")
        st.cache_data.clear()
        st.rerun()

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.title("🌾 TỔNG HỢP MÙA VỤ & VĨ MÔ 2026")
st.markdown(
    "Quy tắc: <span class='dot-green'>🟢 Auto Data (có sẵn trong hệ thống)</span> &nbsp;|&nbsp; "
    "<span class='dot-yellow'>🟡 AI / Chuyên gia (định giá kỳ vọng)</span> &nbsp;|&nbsp; "
    "<span class='dot-red'>🔴 Lỗi / Không có dữ liệu</span>",
    unsafe_allow_html=True
)

# ─── PART 1: GLOBAL MACRO ────────────────────────────────────────────────────
st.subheader("🌍 PHẦN 1: GLOBAL MACRO (Vĩ Mô Toàn Cầu)")

def score_color(s):
    try: s=int(s)
    except: return "#94a3b8"
    if s>=7: return "#22c55e"
    elif s>=5: return "#eab308"
    else: return "#ef4444"

dxy_s   = breakdown.get("F9",  {})
oil_s   = breakdown.get("F10", {})
f12_s   = breakdown.get("F12", {})

dxy_val  = dxy_s.get("raw_value", "N/A")
dxy_pt   = dxy_s.get("score_1_to_10", "N/A")
oil_val  = oil_s.get("raw_value", "N/A")
oil_pt   = oil_s.get("score_1_to_10", "N/A")
cot_net  = cot_zw.get("net_estimated", "N/A")
cot_q    = cot_zw.get("quadrant_estimated", "N/A")
f12_pt   = f12_s.get("score_1_to_10", "N/A")
f12_note = f12_s.get("raw_detail", "—")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='mv-card'>
        <div class='mv-card-title'>🟢 Sức Mạnh USD (DXY)</div>
        <div class='mv-card-value'>{dxy_val}</div>
        <div class='mv-card-detail'>Điểm số: <b style='color:{score_color(dxy_pt)};'>{dxy_pt}/10</b><br>
        DXY cao → USD mạnh → hàng hóa CBOT đắt hơn → Bearish</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='mv-card'>
        <div class='mv-card-title'>🟢 Giá Dầu Thô (Crude Oil)</div>
        <div class='mv-card-value'>{oil_val}</div>
        <div class='mv-card-detail'>Điểm số: <b style='color:{score_color(oil_pt)};'>{oil_pt}/10</b><br>
        Dầu cao → chi phí sản xuất và vận chuyển tăng → Bullish gián tiếp</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    cot_color = "#ef4444" if isinstance(cot_net, (int, float)) and cot_net < 0 else "#22c55e"
    cot_dot = "🟢" if cot_zw else "🔴"
    st.markdown(f"""
    <div class='mv-card'>
        <div class='mv-card-title'>{cot_dot} Dòng Tiền COT – Managed Money (ZW)</div>
        <div class='mv-card-value' style='color:{cot_color};'>Ước tính: {cot_net:,.0f} HĐ</div>
        <div class='mv-card-detail'>Trạng thái: <b>{cot_q}</b></div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='mv-card'>
        <div class='mv-card-title'>🟡 Nhu Cầu Thế Giới (Global Demand)</div>
        <div class='mv-card-value'>Điểm: <span style='color:{score_color(f12_pt)};'>{f12_pt}/10</span></div>
        <div class='mv-card-detail'>{f12_note}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── PART 2: REGIONAL TABLE ──────────────────────────────────────────────────
st.subheader("🗺️ PHẦN 2: MÙA VỤ THEO 4 KHU VỰC")

f1_s  = breakdown.get("F1", {})
f2w_s = breakdown.get("F2W", {})
f3_s  = breakdown.get("F3", {})
f4_s  = breakdown.get("F4", {})
f4s_s = breakdown.get("F4S", {})
f7_s  = breakdown.get("F7", {})
f8_s  = breakdown.get("F8", {})

exp_zw = export_s.get("ZW", {})
net_sales = exp_zw.get("net_sales", exp_zw.get("Net Sales ZW", "N/A"))
exp_date  = exp_zw.get("date", exp_zw.get("period", "N/A"))

def pts(f): return f.get("score_1_to_10", "N/A")
def note(f): return f.get("raw_detail", f.get("raw_value", "—"))

def score_badge(s):
    try: v = int(s)
    except: return f"<span style='color:#94a3b8;'>{s}</span>"
    c = "#22c55e" if v>=7 else ("#eab308" if v>=5 else "#ef4444")
    return f"<b style='color:{c};'>{v}/10</b>"

table_html = f"""
<table class='reg-table'>
<thead>
<tr>
  <th>Khu Vực</th>
  <th>Lịch Mùa Vụ</th>
  <th>Sản Lượng / Tồn Kho</th>
  <th>Thời Tiết / Điều Kiện</th>
  <th>Chính Sách / Xuất Khẩu</th>
</tr>
</thead>
<tbody>

<tr>
  <td><span class='region-flag'>🇺🇸</span><span class='region-header'>Bắc Bán Cầu<br>(Mỹ)</span></td>
  <td><span class='harvest-badge'>THU HOẠCH T6–T7</span><br>Gieo hạt Đông: T9–T10<br>Mùa Xuân: T4–T5</td>
  <td><span class='dot-green'>🟢</span> Tồn kho: Kéo từ WASDE / Grain Stocks<br>
      <span class='dot-green'>🟢</span> Export Sales tuần {exp_date}: <b>{net_sales} MT</b><br>
      <span class='dot-green'>🟢</span> Crop Progress: {score_badge(pts(f7_s))}</td>
  <td><span class='dot-yellow'>🟡</span> Thời tiết Mỹ: {score_badge(pts(f2w_s))}<br>
      <small>{note(f2w_s)}</small></td>
  <td><span class='dot-green'>🟢</span> DXY {dxy_val} → Sức cạnh tranh XK<br>
      <small>DXY cao ảnh hưởng trực tiếp tới khả năng bán hàng của Mỹ trên thị trường quốc tế.</small></td>
</tr>

<tr>
  <td><span class='region-flag'>🇪🇺</span><span class='region-header'>Châu Âu<br>(EU)</span></td>
  <td><span class='harvest-badge'>THU HOẠCH T7–T8</span><br>Áp lực xả hàng cao điểm: T7–T9</td>
  <td><span class='dot-yellow'>🟡</span> Nguồn cung EU: {score_badge(pts(f3_s))}<br>
      <small>{note(f3_s)}</small></td>
  <td><span class='dot-yellow'>🟡</span> Hạn hán / Mưa lũ: Cập nhật theo báo cáo COCERAL/MARS<br>
      <small>Báo cáo gần nhất: Mất mùa do nắng nóng tại Pháp & Đức → Nguồn cung EU sụt giảm.</small></td>
  <td><span class='dot-yellow'>🟡</span> Chính sách xuất khẩu EU: Quota linh hoạt theo thị trường<br>
      <small>EU thường cạnh tranh với Mỹ ở thị trường MENA khi giá FOB Nga tăng cao.</small></td>
</tr>

<tr>
  <td><span class='region-flag'>🇷🇺</span><span class='region-header'>Biển Đen<br>(Nga & Ukraine)</span></td>
  <td><span class='harvest-badge'>XẢ HÀNG T8–T10</span><br>Đỉnh điểm áp lực giảm giá toàn cầu</td>
  <td><span class='dot-yellow'>🟡</span> Chính sách xuất khẩu Nga: {score_badge(pts(f1_s))}<br>
      <small>{note(f1_s)}</small></td>
  <td><span class='dot-yellow'>🟡</span> Logistics Biển Đen: {score_badge(pts(f8_s))}<br>
      <small>{note(f8_s)}</small></td>
  <td><span class='dot-yellow'>🟡</span> Nga xóa thuế XK đến 31/12/2026 → Tối ưu hóa cạnh tranh giá thấp.<br>
      <small>Ukraine tiếp tục xuất khẩu qua cảng Chornomorsk dù bị tấn công định kỳ.</small></td>
</tr>

<tr>
  <td><span class='region-flag'>🇦🇺</span><span class='region-header'>Nam Bán Cầu<br>(Úc & Argentina)</span></td>
  <td><span class='harvest-badge'>THU HOẠCH T11–T12</span><br>Áp lực cung cuối năm → đầu năm sau</td>
  <td><span class='dot-yellow'>🟡</span> Sản lượng Nam BC: {score_badge(pts(f4s_s))}<br>
      <small>{note(f4s_s)}</small></td>
  <td><span class='dot-yellow'>🟡</span> Thời tiết Nam BC: {score_badge(pts(f4_s))}<br>
      <small>{note(f4_s)}</small></td>
  <td><span class='dot-yellow'>🟡</span> ABARES (Úc): Nâng dự báo lên 29.9M tấn (trên TBC 10 năm).<br>
      BAGE (Argentina): Cắt giảm xuống 23.4M tấn do khô hạn.<br>
      <small>Tổng hợp: Nguồn cung Nam BC <i>tốt hơn kỳ vọng trước đó</i> → Bearish tương đối.</small></td>
</tr>

</tbody>
</table>
"""

st.markdown(table_html, unsafe_allow_html=True)


# ─── PART 3: AI CONCLUSION ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 PHẦN 3: KẾT LUẬN & KẾ HOẠCH DCA (AI ANALYSIS)")
if ai_analysis and "analysis" in ai_analysis:
    st.caption(f"⏱ Lần phân tích AI cuối: **{ai_analysis.get('last_updated', '')}** — Ấn nút 'Cập Nhật Mùa Vụ' để làm mới.")
    st.markdown(ai_analysis["analysis"])
else:
    st.warning("Chưa có bản phân tích AI. Vui lòng ấn nút **'🔄 Cập Nhật Mùa Vụ (AI)'** ở thanh bên trái để hệ thống Gemini phân tích dữ liệu hiện tại.")
