import streamlit as st
import json
from pathlib import Path
import sys
import subprocess

st.set_page_config(page_title="CBOT - Lúa Mì Nga", page_icon="🇷🇺", layout="wide")

def load_json(filename):
    filepath = Path(__file__).parent.parent / "Data" / "output" / filename
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

st.title("🇷🇺 THE RUSSIAN FACTOR - LÚA MÌ BIỂN ĐEN")
st.markdown("""
Khu vực hiển thị riêng các số liệu định lượng về mùa vụ và xuất khẩu của Nga - Yếu tố tạo ra **Đáy 1 (Tháng 7)** và lực ép giá trần đối với Lúa mì CBOT.
""")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 CẬP NHẬT SỐ LIỆU MỚI NHẤT", use_container_width=True):
        with st.spinner("AI đang tổng hợp số liệu từ IKAR, SovEcon... (10-15s)"): 
            subprocess.run([sys.executable, str(Path(__file__).parent.parent / "Data" / "fetch_russian_metrics.py")])
            st.cache_data.clear()
            st.rerun()

data = load_json("russian_metrics.json")
if data and "metrics" in data:
    metrics = data["metrics"]
    st.markdown(f"<div style='font-size:12px; color:#64748b; margin-bottom:20px;'>Cập nhật lần cuối: {data.get('timestamp', '—')}</div>", unsafe_allow_html=True)
    
    st.markdown("### 📊 CHỈ SỐ MÙA VỤ & XUẤT KHẨU")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Diện tích gieo trồng", metrics.get("planted_area", "N/A"))
    m2.metric("Sản lượng dự báo", metrics.get("production_forecast", "N/A"))
    m3.metric("Giá FOB giao ngay", metrics.get("fob_price", "N/A"))
    
    m4, m5, m6 = st.columns(3)
    m4.metric("Năng lực xuất khẩu", metrics.get("export_capacity", "N/A"))
    m5.metric("Thuế/Chính sách XK", metrics.get("export_tax", "N/A"))
    m6.metric("Thời gian thu hoạch", metrics.get("harvest_time", "N/A"))
    
    st.markdown("---")
    st.markdown("### 🚜 TIẾN ĐỘ & CHẤT LƯỢNG")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**Tiến độ thu hoạch hiện tại:** {metrics.get('harvest_progress', 'N/A')}")
    with col_b:
        st.warning(f"**Đánh giá chất lượng:** {metrics.get('quality_notes', 'N/A')}")
        
    st.markdown("---")
    st.markdown("### 🧠 AI NHẬN ĐỊNH ÁP LỰC XẢ HÀNG LÊN CBOT")
    st.success(metrics.get("ai_assessment", "Chưa có nhận định."))

else:
    st.warning("Chưa có dữ liệu định lượng về Lúa mì Nga. Hãy nhấn nút 'Cập nhật' ở góc trên.")
