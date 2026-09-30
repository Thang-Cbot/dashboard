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
.metric-box { border: 1px solid #1e2d45; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: #0b1120; }
.auto-dot { color: #22c55e; font-weight: bold; }
.manual-dot { color: #eab308; font-weight: bold; }
.err-dot { color: #ef4444; font-weight: bold; }
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

macro = load_json("macro_scores.json")
macro_w = load_json("macro_weights.json")
fund = load_json("fundamental_data.json")
cot = load_json("cot_data.json")
ai_analysis = load_json("ai_muavu_analysis.json")
export_sales = load_json("export_sales.json")

breakdown = macro.get("breakdown", {})
dxy_score = breakdown.get("F9", {})
cot_zw = cot.get("commodities", {}).get("001602", {})

# --- SIDEBAR BUTTON ---
if st.sidebar.button("🔄 Cập Nhật Mùa Vụ (AI)", type="primary", use_container_width=True):
    with st.spinner("Đang tổng hợp dữ liệu và gọi Gemini AI phân tích..."):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        script_path = str(BASE_DIR / "Data" / "analyze_muavu_ai.py")
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, env=env)
        if res.returncode == 0:
            st.sidebar.success("✅ Cập nhật AI thành công!")
        else:
            st.sidebar.error(f"❌ Lỗi: {res.stderr}")
        st.cache_data.clear()
        st.rerun()

st.title("🌾 TỔNG HỢP MÙA VỤ & VĨ MÔ 2026")
st.markdown("Quy tắc: <span class='auto-dot'>🟢 Auto Data (Có sẵn)</span> | <span class='manual-dot'>🟡 Manual/AI (Định giá kỳ vọng)</span> | <span class='err-dot'>🔴 No Data</span>", unsafe_allow_html=True)

# --- PART 1: GLOBAL MACRO ---
st.subheader("🌍 PHẦN 1: GLOBAL MACRO (Vĩ Mô Toàn Cầu)")
col1, col2, col3, col4 = st.columns(4)

def dot(val): return "🟢" if val else "🔴"

with col1:
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown(f"**Sức mạnh USD (DXY)**")
    dxy_val = dxy_score.get('raw_value', 'N/A')
    st.markdown(f"<span class='auto-dot'>🟢</span> {dxy_val}", unsafe_allow_html=True)
    st.markdown(f"Điểm số: {dxy_score.get('score_1_to_10', 'N/A')}/10")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    oil_score = breakdown.get("F10", {})
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown(f"**Giá Dầu (Crude Oil)**")
    st.markdown(f"<span class='auto-dot'>🟢</span> {oil_score.get('raw_value', 'N/A')}", unsafe_allow_html=True)
    st.markdown(f"Điểm số: {oil_score.get('score_1_to_10', 'N/A')}/10")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown(f"**Dòng tiền COT (ZW)**")
    if cot_zw:
        st.markdown(f"<span class='auto-dot'>🟢</span> Realtime: {cot_zw.get('net_estimated', 'N/A')} HĐ", unsafe_allow_html=True)
        st.markdown(f"Trạng thái: {cot_zw.get('quadrant_estimated', 'N/A')}")
    else:
        st.markdown("<span class='err-dot'>🔴</span> Không có dữ liệu", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    f12 = breakdown.get("F12", {})
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown(f"**Nhu cầu Thế giới**")
    st.markdown(f"<span class='manual-dot'>🟡</span> Điểm: {f12.get('score_1_to_10', 'N/A')}/10", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px; color:#94a3b8;'>{f12.get('raw_detail', '')}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# --- PART 2: REGIONAL SEASONALITY ---
st.subheader("🗺️ PHẦN 2: ĐỊA CHÍNH TRỊ & MÙA VỤ 4 KHU VỰC")
tb1, tb2, tb3, tb4 = st.tabs(["🇺🇸 Bắc Bán Cầu (Mỹ)", "🇪🇺 Châu Âu (EU)", "🇷🇺 Biển Đen (Nga/UA)", "🇦🇺 Nam Bán Cầu (Úc/Argen)"])

with tb1:
    st.markdown("### 🇺🇸 Yếu tố mùa vụ Mỹ")
    f7 = breakdown.get("F7", {})
    us_weather = breakdown.get("F2W", {})
    exp_zw = export_sales.get("ZW", {})
    
    st.markdown(f"- <span class='auto-dot'>🟢</span> **Tồn kho Mỹ:** Dữ liệu tự động kéo từ WASDE/Grain Stocks.", unsafe_allow_html=True)
    st.markdown(f"- <span class='auto-dot'>🟢</span> **Tiến độ Mùa vụ (Crop Progress):** Điểm {f7.get('score_1_to_10', 'N/A')}/10 - {f7.get('raw_detail', '')}", unsafe_allow_html=True)
    st.markdown(f"- <span class='auto-dot'>🟢</span> **Export Sales:** {exp_zw.get('net_sales', 'N/A')} MT (Tuần: {exp_zw.get('date', 'N/A')})", unsafe_allow_html=True)
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Thời tiết Mỹ:** Điểm {us_weather.get('score_1_to_10', 'N/A')}/10 - {us_weather.get('raw_detail', '')}", unsafe_allow_html=True)

with tb2:
    st.markdown("### 🇪🇺 Yếu tố mùa vụ Châu Âu")
    f3 = breakdown.get("F3", {})
    st.markdown("- **Thời điểm thu hoạch:** Tháng 7 - Tháng 8 (Áp lực nguồn cung).")
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Nguồn cung EU (Định giá kỳ vọng):** Điểm {f3.get('score_1_to_10', 'N/A')}/10", unsafe_allow_html=True)
    st.markdown(f"  *Chi tiết:* {f3.get('raw_detail', '')}")

with tb3:
    st.markdown("### 🇷🇺 Yếu tố mùa vụ Biển Đen (Nga & Ukraine)")
    f1 = breakdown.get("F1", {})
    f8 = breakdown.get("F8", {})
    st.markdown("- **Thời điểm thu hoạch & Xả hàng:** Tháng 8 - Tháng 10 (Đỉnh điểm áp lực giá rẻ).")
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Chính sách Nga (Export Duty):** Điểm {f1.get('score_1_to_10', 'N/A')}/10 - {f1.get('raw_detail', '')}", unsafe_allow_html=True)
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Logistics / Địa chính trị:** Điểm {f8.get('score_1_to_10', 'N/A')}/10 - {f8.get('raw_detail', '')}", unsafe_allow_html=True)

with tb4:
    st.markdown("### 🇦🇺 Yếu tố mùa vụ Nam Bán Cầu (Úc & Argentina)")
    f4 = breakdown.get("F4", {})
    f4s = breakdown.get("F4S", {})
    st.markdown("- **Thời điểm thu hoạch:** Tháng 11 - Tháng 12.")
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Thời tiết Nam Bán cầu:** Điểm {f4.get('score_1_to_10', 'N/A')}/10 - {f4.get('raw_detail', '')}", unsafe_allow_html=True)
    st.markdown(f"- <span class='manual-dot'>🟡</span> **Sản lượng Nam Bán cầu (ABARES/BCR):** Điểm {f4s.get('score_1_to_10', 'N/A')}/10 - {f4s.get('raw_detail', '')}", unsafe_allow_html=True)


# --- PART 3: AI CONCLUSION ---
st.subheader("🤖 PHẦN 3: KẾT LUẬN & KẾ HOẠCH DCA (AI ANALYSIS)")
if ai_analysis and "analysis" in ai_analysis:
    st.info(f"Lần cập nhật AI cuối: {ai_analysis.get('last_updated', '')}")
    st.markdown(ai_analysis["analysis"])
else:
    st.warning("Chưa có bản phân tích AI. Vui lòng ấn nút 'Cập Nhật Mùa Vụ (AI)' ở thanh bên trái để hệ thống Gemini phân tích dữ liệu hiện tại.")

