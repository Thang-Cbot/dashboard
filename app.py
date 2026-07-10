"""
app.py — CBOT Streamlit Dashboard Entry Point
=============================================
Chạy: streamlit run app.py
Truy cập: http://localhost:8501
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import subprocess
import streamlit as st
from pathlib import Path

DATA_OUTPUT = Path(__file__).parent / "Data" / "output"

st.set_page_config(
    page_title="CBOT Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "CBOT Agri-Trading Dashboard | Powered by Streamlit"}
)

# ── Global CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
h1, h2, h3 { color: #e2e8f0 !important; }
hr { border-color: #2a3a5c !important; }
/* Style page_link in sidebar */
[data-testid="stSidebarNavLink"] { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_status():
    p = DATA_OUTPUT / "data_status.json"
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sidebar_status():
    """Sidebar: hiển thị tóm tắt trạng thái dữ liệu + nav."""
    st.sidebar.markdown("""
    <div style='text-align:center; padding:16px 0 8px;'>
        <div style='font-size:24px; font-weight:800; color:#e2e8f0;'>📊 CBOT</div>
        <div style='font-size:11px; color:#64748b; letter-spacing:2px;'>TRADING DASHBOARD</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation links
    st.sidebar.markdown("---")
    st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
    st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
    st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
    st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
    st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
    st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
    st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")
    st.sidebar.page_link("pages/7_System_Logs.py", label="⚙️ System Logs")
    
    st.sidebar.markdown("---")

    status = load_status()
    modules = status.get("modules", {})
    last_update = status.get("last_full_update", "—")

    for key, label in [
        ("usda",         "WASDE/Crop"),
        ("prices",       "Giá H1"),
        ("macro",        "Vĩ Mô"),
        ("cot",          "COT"),
        ("export_sales", "Xuất Khẩu"),
    ]:
        val = modules.get(key, {})
        status_str = val.get("status", "—") if isinstance(val, dict) else str(val)
        icon = "🟢" if "[OK]" in status_str else ("🟡" if "[Partial]" in status_str else ("🔴" if "[ERROR]" in status_str else "⚪"))
        updated = val.get("updated_at", "")[-8:] if isinstance(val, dict) else ""
        st.sidebar.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px;color:#94a3b8;">'
            f'<span>{icon} {label}</span>'
            f'<span style="color:#475569;">{updated}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.sidebar.markdown(f"""
    <div style='font-size:11px; color:#475569; text-align:center; margin-top:6px;'>
        Scan: {last_update}
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 LÀM MỚI TRẠNG THÁI", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("🔄 RUN ALL DATA", use_container_width=True):
        with st.sidebar:
            with st.spinner("Đang cập nhật..."):
                try:
                    base = Path(__file__).parent
                    result = subprocess.run(
                        [sys.executable, str(base / "Data" / "run_data_update.py")],
                        capture_output=True, text=True, timeout=300
                    )
                    if result.returncode == 0:
                        st.success("✅ Xong!")
                        st.cache_data.clear()
                    else:
                        st.error(result.stderr[-300:] if result.stderr else "Lỗi không rõ")
                except subprocess.TimeoutExpired:
                    st.warning("⏳ Đang chạy ngầm (>5 phút)")
                except Exception as e:
                    st.error(str(e))

    st.sidebar.markdown("""
    <div style='font-size:10px; color:#374151; text-align:center; padding:6px 0;'>
        Auto-update qua Precision Scheduler
    </div>
    """, unsafe_allow_html=True)


# ── Main Landing ────────────────────────────────────────────────────────────────
sidebar_status()

st.markdown("""
<div style='text-align:center; padding:40px 0 24px;'>
    <div style='font-size:48px; margin-bottom:8px;'>📊</div>
    <div style='font-size:32px; font-weight:800; color:#e2e8f0; margin-bottom:8px;'>
        CBOT Agri-Trading Dashboard
    </div>
    <div style='font-size:16px; color:#64748b; margin-bottom:32px;'>
        Nông Sản Tái Sinh — ZC · ZW
    </div>
</div>
""", unsafe_allow_html=True)

# Main action buttons
c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
with c2:
    if st.button("🔄 RUN ALL DATA (Lấy toàn bộ dữ liệu mới)", use_container_width=True):
        with st.spinner("Đang cập nhật toàn bộ hệ thống..."):
            try:
                base = Path(__file__).parent
                result = subprocess.run(
                    [sys.executable, str(base / "Data" / "run_data_update.py")],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    st.success("✅ Cập nhật hoàn tất!")
                    st.cache_data.clear()
                else:
                    st.error(result.stderr[-300:] if result.stderr else "Lỗi không rõ")
            except subprocess.TimeoutExpired:
                st.warning("⏳ Tiến trình đang chạy ngầm (>5 phút)")
            except Exception as e:
                st.error(str(e))
with c3:
    if st.button("🧹 LÀM MỚI TRẠNG THÁI (Xóa Cache)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Quick nav — dùng st.page_link để có thể click
col1, col2, col3, col4, col5, col6, col7 = st.columns(7, gap="small")
for col, icon, title, desc, page in [
    (col1, "📊", "Tổng Quan",       "Tóm tắt thị trường & Alert",  "pages/1_Overview.py"),
    (col2, "📈", "Hồ Sơ Mã",       "Biểu đồ H1 & chiến lược",     "pages/2_Profiles.py"),
    (col3, "📰", "Tin Tức",         "Xuất khẩu, USDA, WASDE",       "pages/3_News.py"),
    (col4, "🌤️","Thời Tiết",      "ENSO & dự báo ngắn hạn",       "pages/4_Weather.py"),
    (col5, "🗺️","Bản Đồ Nông Sản","Mỹ + Thế Giới, cập nhật thời tiết", "pages/5_AgriMap.py"),
    (col6, "🌾","Mùa Vụ 2026",   "Chiến lược mùa vụ, DCA dài hạn", "pages/6_MuaVu.py"),
    (col7, "⚙️","System Logs",   "Sức khỏe hệ thống, Đồng bộ", "pages/7_System_Logs.py"),
]:
    with col:
        st.markdown(f"""
        <div style='background:#1a2035; border:1px solid #2a3a5c; border-radius:12px;
                    padding:15px 5px; text-align:center; height:135px;'>
            <div style='font-size:26px; margin-bottom:4px;'>{icon}</div>
            <div style='font-size:13px; font-weight:700; color:#e2e8f0; line-height:1.2; margin-bottom:4px;'>{title}</div>
            <div style='font-size:10px; color:#64748b; margin-top:2px; line-height:1.2;'>{desc}</div>
        </div>""", unsafe_allow_html=True)
        st.page_link(page, label=f"Mở", use_container_width=True)

st.markdown("""
<div style='text-align:center; padding:16px; color:#475569; font-size:12px;'>
    Dùng sidebar bên trái hoặc nhấn nút bên trên để chuyển trang
</div>
""", unsafe_allow_html=True)
