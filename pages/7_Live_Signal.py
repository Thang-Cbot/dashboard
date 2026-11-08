"""
pages/7_Live_Signal.py — Live Signal & Thống Kê Hiệu Suất Mô Phỏng CQG
=====================================================================
Giao diện phân tích và theo dõi tín hiệu Real-time / Backtest hiệu suất 90 ngày.
So sánh 3 phương pháp giao dịch:
  1. ICT MSS + Pullback EMA 21-50 (Thuận xu hướng SMC)
  2. FVG + Bắt Đáy / Đỉnh SMC Zone (Đảo chiều vùng cực trị 5 sao)
  3. Chiến Lược Hybrid (M1 + M2 Kết Hợp — Bắt Đáy/Đỉnh cạn kiệt + Thuận sóng xác nhận)
"""

import streamlit as st
import json
import os
import sys
import datetime
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# Đường dẫn
BASE_DIR = Path(__file__).parent.parent
DATA_OUTPUT = BASE_DIR / "Data" / "output"
BACKTEST_FILE = DATA_OUTPUT / "live_signals_backtest.json"
sys.path.insert(0, str(BASE_DIR))

import importlib
import tv_webhook_client
import backtest_engine
importlib.reload(tv_webhook_client)
importlib.reload(backtest_engine)

# ── CẤU HÌNH TRANG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Live Signal & Hiệu Suất | CBOT",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── HÀM LÀM SẠCH HTML KHỎI CODE-BLOCK MARKDOWN ─────────────────────────────────
def clean_html(raw_html: str) -> str:
    """Loại bỏ thụt đầu dòng (indentation) để Markdown không biến HTML thành thẻ <pre><code>"""
    return "\n".join([line.strip() for line in raw_html.strip().splitlines()])

# ── GLOBAL CSS ──────────────────────────────────────────────────────────────────
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #0b1120; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* Top Header Bar */
.top-header-bar {
display: flex;
align-items: center;
justify-content: space-between;
padding: 8px 0 20px 0;
border-bottom: 1px solid #1e293b;
margin-bottom: 24px;
}
.brand-title {
font-size: 26px;
font-weight: 800;
color: #f8fafc;
letter-spacing: -0.5px;
}
.brand-accent {
color: #f59e0b;
}

/* KPI Cards */
.kpi-container {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 16px;
margin-bottom: 24px;
}
.kpi-card {
background: #111827;
border: 1px solid #1f2937;
border-radius: 12px;
padding: 18px 20px;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.kpi-title {
font-size: 13px;
font-weight: 500;
color: #9ca3af;
margin-bottom: 8px;
}
.kpi-value-green {
font-size: 32px;
font-weight: 800;
color: #10b981;
line-height: 1.1;
margin-bottom: 6px;
}
.kpi-value-red {
font-size: 32px;
font-weight: 800;
color: #ef4444;
line-height: 1.1;
margin-bottom: 6px;
}
.kpi-value-white {
font-size: 32px;
font-weight: 800;
color: #f9fafb;
line-height: 1.1;
margin-bottom: 6px;
}
.kpi-sub {
font-size: 12px;
color: #6b7280;
}

/* Badges */
.badge-buy {
background-color: rgba(16, 185, 129, 0.15);
color: #10b981;
border: 1px solid rgba(16, 185, 129, 0.3);
padding: 3px 12px;
border-radius: 6px;
font-size: 12px;
font-weight: 700;
display: inline-block;
}
.badge-sell {
background-color: rgba(239, 68, 68, 0.15);
color: #ef4444;
border: 1px solid rgba(239, 68, 68, 0.3);
padding: 3px 12px;
border-radius: 6px;
font-size: 12px;
font-weight: 700;
display: inline-block;
}
.badge-res-tp3 {
background-color: rgba(16, 185, 129, 0.2);
color: #34d399;
font-weight: 700;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-tp2 {
background-color: rgba(52, 211, 153, 0.15);
color: #6ee7b7;
font-weight: 700;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-tp1 {
background-color: rgba(20, 184, 166, 0.15);
color: #2dd4bf;
font-weight: 700;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-entry {
background-color: rgba(107, 114, 128, 0.2);
color: #9ca3af;
font-weight: 600;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-sl {
background-color: rgba(239, 68, 68, 0.2);
color: #f87171;
font-weight: 700;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-pending {
background-color: rgba(75, 85, 99, 0.2);
color: #9ca3af;
font-weight: 500;
padding: 3px 8px;
border-radius: 4px;
}
.badge-res-open {
background-color: rgba(56, 189, 248, 0.2);
color: #38bdf8;
font-weight: 700;
padding: 3px 8px;
border-radius: 4px;
border: 1px solid rgba(56, 189, 248, 0.4);
}
.badge-tag-hybrid {
background-color: rgba(168, 85, 247, 0.15);
color: #c084fc;
border: 1px solid rgba(168, 85, 247, 0.3);
padding: 2px 6px;
border-radius: 4px;
font-size: 11px;
font-weight: 600;
}

/* Passport & Timeline Styles */
.passport-card {
background: #0f172a;
border: 1px solid #1e293b;
border-radius: 12px;
padding: 20px;
margin: 16px 0;
box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.passport-header {
display: flex;
justify-content: space-between;
align-items: center;
border-bottom: 1px solid #1e293b;
padding-bottom: 14px;
margin-bottom: 16px;
}
.passport-grid {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 12px;
margin-bottom: 18px;
}
.passport-metric {
background: #1e293b;
border: 1px solid #334155;
border-radius: 8px;
padding: 12px 14px;
}
.timeline-flow {
display: flex;
flex-direction: column;
gap: 10px;
margin-top: 10px;
}
.timeline-step {
display: flex;
gap: 14px;
background: #111827;
border: 1px solid #1e293b;
border-radius: 8px;
padding: 12px 16px;
align-items: flex-start;
}
.timeline-step-icon {
font-size: 20px;
min-width: 28px;
text-align: center;
line-height: 1.2;
}
.timeline-step-content {
flex: 1;
}
.timeline-step-title {
font-weight: 700;
font-size: 13px;
color: #f1f5f9;
margin-bottom: 4px;
}
.timeline-step-desc {
font-size: 12px;
color: #94a3b8;
line-height: 1.5;
}

/* Expandable Trade Accordion Table */
.trade-table-wrapper {
width: 100%;
margin-top: 10px;
font-size: 13px;
background: #0f172a;
border-radius: 8px;
border: 1px solid #1e293b;
overflow: hidden;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}
.trade-table-header {
display: flex;
align-items: center;
background-color: #0b1120;
color: #94a3b8;
font-weight: 600;
padding: 12px 16px;
border-bottom: 1px solid #1e293b;
user-select: none;
font-size: 12px;
}
.trade-accordion {
border-bottom: 1px solid #1e293b;
background: #0f172a;
transition: background-color 0.15s ease;
}
.trade-accordion:last-child {
border-bottom: none;
}
.trade-accordion:hover {
background-color: #162032;
}
.trade-accordion[open] {
background-color: #0c1424;
border-left: 3px solid #38bdf8;
}
.trade-summary {
display: flex;
align-items: center;
padding: 12px 16px;
cursor: pointer;
list-style: none;
user-select: none;
}
.trade-summary:hover {
background-color: rgba(56, 189, 248, 0.04);
}
.trade-summary::-webkit-details-marker {
display: none;
}
.trade-summary::marker {
display: none;
}
.trade-arrow {
display: inline-block;
transition: transform 0.2s ease, color 0.2s ease;
color: #64748b;
font-size: 12px;
font-weight: bold;
}
.trade-accordion[open] .trade-arrow {
transform: rotate(180deg);
color: #38bdf8;
}
.trade-detail-content {
padding: 14px 18px 18px 18px;
background: #090e17;
border-top: 1px solid #1e293b;
}

/* Radar Table Styles */
.radar-table-wrapper {
width: 100%;
margin-top: 10px;
font-size: 13px;
background: #0f172a;
border-radius: 8px;
border: 1px solid #312e81;
overflow: hidden;
box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}
.radar-header {
display: flex;
align-items: center;
background-color: #0b0f22;
color: #a5b4fc;
font-weight: 700;
padding: 12px 16px;
border-bottom: 1px solid #1e1b4b;
font-size: 12px;
letter-spacing: 0.3px;
}
.radar-accordion {
border-bottom: 1px solid #1e1b4b;
background: #0f172a;
transition: background-color 0.15s ease;
}
.radar-accordion:last-child {
border-bottom: none;
}
.radar-accordion:hover {
background-color: #161b36;
}
.radar-accordion[open] {
background-color: #0d1227;
border-left: 3px solid #818cf8;
}
.radar-summary {
display: flex;
align-items: center;
padding: 12px 16px;
cursor: pointer;
list-style: none;
user-select: none;
}
.radar-summary:hover {
background-color: rgba(99, 102, 241, 0.06);
}
.radar-summary::-webkit-details-marker {
display: none;
}
.radar-summary::marker {
display: none;
}
.radar-arrow {
display: inline-block;
transition: transform 0.2s ease, color 0.2s ease;
color: #6366f1;
font-size: 12px;
font-weight: bold;
}
.radar-accordion[open] .radar-arrow {
transform: rotate(180deg);
color: #a5b4fc;
}
.radar-detail-content {
padding: 14px 18px 18px 18px;
background: #090c1c;
border-top: 1px solid #1e1b4b;
}

/* Custom Table (Dùng cho Tab 4) */
.custom-table {
width: 100%;
border-collapse: collapse;
margin-top: 12px;
font-size: 13px;
background: #111827;
border-radius: 8px;
overflow: hidden;
border: 1px solid #1f2937;
}
.custom-table th {
background-color: #0f172a;
color: #9ca3af;
font-weight: 600;
text-align: left;
padding: 12px 16px;
border-bottom: 1px solid #1f2937;
}
.custom-table td {
padding: 12px 16px;
border-bottom: 1px solid #1f2937;
color: #d1d5db;
}
.custom-table tr:hover {
background-color: #1e293b;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
gap: 8px;
background-color: #0f172a;
padding: 6px;
border-radius: 8px;
border: 1px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
border-radius: 6px;
color: #94a3b8;
font-weight: 600;
padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
background-color: #1e293b !important;
color: #38bdf8 !important;
}
</style>
""")

# ── SIDEBAR NAV ─────────────────────────────────────────────────────────────
st.sidebar.html("""
<div style='text-align:center; padding:16px 0 8px;'>
<div style='font-size:24px; font-weight:800; color:#e2e8f0;'>📊 CBOT</div>
<div style='font-size:11px; color:#64748b; letter-spacing:2px;'>TRADING DASHBOARD</div>
</div>
""")
st.sidebar.markdown("---")
st.sidebar.page_link("app.py",                  label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py",     label="⚡ Tổng Quan (RUN TIN TỨC)")
st.sidebar.page_link("pages/2_Profiles.py",     label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",         label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather_Map.py",   label="🌤️ Thời Tiết & Bản Đồ")
st.sidebar.page_link("pages/5_Macro_Matrix.py", label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",        label="🌾 Mùa Vụ")
st.sidebar.page_link("pages/7_Live_Signal.py",  label="🎯 Live Signal & Hiệu Suất")
st.sidebar.page_link("pages/8_System_Logs.py",  label="⚙️ System Logs")
st.sidebar.markdown("---")

# ── TỰ ĐỘNG LÀM MỚI MỖI 5 PHÚT (THEO CHU KỲ NẾN M5) ─────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=300_000, key="m5_live_signal_refresh")
except Exception:
    pass

# ── TRẠM NHẬN NẾN M5 REALTIME TỪ TRADINGVIEW WEBHOOK ─────────────────────────
current_webhook_url = tv_webhook_client.get_webhook_url()
rt_m5_data = tv_webhook_client.fetch_realtime_m5(timeout=3) if current_webhook_url else tv_webhook_client.load_cached_m5()
rt_symbols = rt_m5_data.get("symbols", {})
rt_updated_at = rt_m5_data.get("updated_at", "")

# ── NẠP DỮ LIỆU BACKTEST (TẦNG 1: CẤU TRÚC H1 + M15/M30 | TẦNG 2: CẬP NHẬT TRẠNG THÁI M5) ──
@st.cache_data(ttl=60)
def load_backtest_data(m5_timestamp: str = "", _v: int = 2):
    need_full_run = not BACKTEST_FILE.exists()
    if not need_full_run:
        try:
            age_sec = (datetime.datetime.now() - datetime.datetime.fromtimestamp(BACKTEST_FILE.stat().st_mtime)).total_seconds()
            if age_sec > 3600:
                need_full_run = True
        except Exception:
            pass

    if need_full_run:
        backtest_engine.run_full_backtest(force_download=False)

    try:
        with open(BACKTEST_FILE, "r", encoding="utf-8") as f:
            res_data = json.load(f)
        # TẦNG 2: Cập nhật tức thời trạng thái lệnh đang mở & Radar khoảng cách theo M5 Realtime
        zc_c = backtest_engine.fetch_or_load_90d("ZC", force_download=False)
        zw_c = backtest_engine.fetch_or_load_90d("ZW", force_download=False)
        res_data["upcoming_radar"] = backtest_engine.compute_upcoming_radar(zc_c, zw_c)
        for m_key in ["method_1", "method_2", "method_3"]:
            if m_key in res_data and "trades" in res_data[m_key]:
                t_list = res_data[m_key]["trades"]
                t_list = backtest_engine.apply_m5_live_status_to_trades(t_list, "ZC")
                t_list = backtest_engine.apply_m5_live_status_to_trades(t_list, "ZW")
                res_data[m_key]["trades"] = t_list
        return res_data
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu backtest: {e}")
        return {}

data = load_backtest_data(rt_updated_at)

# ── HEADER & THANH ĐIỀU KHIỂN ──────────────────────────────────────────────
col_header, col_actions = st.columns([3, 1])
with col_header:
    st.html("""
    <div style='display:flex; align-items:center; gap:12px; margin-bottom:4px;'>
    <div style='font-size:28px; font-weight:800; color:#f8fafc;'>Invest<span style='color:#f59e0b;'>X</span> • Live Signal</div>
    <span style='background:#1e293b; color:#38bdf8; font-size:12px; font-weight:700; padding:4px 10px; border-radius:6px; border:1px solid #0284c7;'>CQG SIMULATION • ADAPTIVE 2-LAYER (H1/M15 + M5 TRACKER)</span>
    </div>
    <div style='font-size:20px; font-weight:700; color:#f1f5f9; margin-bottom:2px;'>Lịch sử & Thống kê hiệu suất</div>
    <div style='font-size:13px; color:#94a3b8; margin-bottom:18px;'>Cấu trúc & Điểm vào lệnh xác định bởi <b>Tầng 1 (H1 Đóng Cửa + M15/M30 Xung Lực Phiên Mỹ)</b> • Trạng thái khớp lệnh & Giá Live theo dõi bởi <b>Tầng 2 (M5 Realtime)</b></div>
    """)

with col_actions:
    st.html("<div style='height:14px'></div>")
    if st.button("🔄 Cập Nhật & Test Lại (90d)", use_container_width=True, type="primary"):
        with st.spinner("Đang tải dữ liệu H1 + Nến M5 Realtime và chạy lại mô phỏng 90 ngày..."):
            backtest_engine.run_full_backtest(force_download=True)
            st.cache_data.clear()
            st.rerun()

if rt_symbols:
    cards_m5 = []
    for sym_key, label_name in [("ZW", "🌾 Lúa Mì (ZWAZ26)"), ("ZC", "🌽 Ngô (ZCEZ26)")]:
        s_info = rt_symbols.get(sym_key, {})
        m5 = s_info.get("latest_m5")
        h1_form = s_info.get("forming_h1")
        if m5:
            c_val = m5.get("close", 0)
            o_val = m5.get("open", 0)
            h_val = m5.get("high", 0)
            l_val = m5.get("low", 0)
            t_val = m5.get("time_vn") or str(m5.get("time", ""))[:19].replace("T", " ")
            m5_cnt = h1_form.get("m5_count", 1) if h1_form else 1
            color_c = "#10b981" if c_val >= o_val else "#ef4444"
            cards_m5.append(
                f"<div style='background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:10px 14px; flex:1;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<b style='color:#f8fafc; font-size:13px;'>{label_name} • <span style='color:#10b981;'>🟢 Đã Kết Nối M5 Realtime</span></b>"
                f"<span style='font-size:11px; color:#94a3b8;'>⏱ {t_val} (Giờ VN • {m5_cnt} nến M5/giờ)</span>"
                f"</div>"
                f"<div style='margin-top:6px; font-family:monospace; font-size:13px; color:#cbd5e1;'>"
                f"Giá M5: <b style='color:{color_c}; font-size:16px;'>{c_val}</b> &nbsp;|&nbsp; "
                f"O: <b>{o_val}</b> • H: <b>{h_val}</b> • L: <b>{l_val}</b>"
                f"</div></div>"
            )
    if cards_m5:
        st.html("<div style='display:flex; gap:12px; margin-bottom:14px;'>" + "".join(cards_m5) + "</div>")

with st.expander("📡 Cấu Hình & Nhận Nến M5 Realtime Từ TradingView Webhook (0 Độ Trễ)", expanded=not bool(current_webhook_url)):
    c_wh1, c_wh2 = st.columns([3.5, 1])
    with c_wh1:
        new_wh_url = st.text_input(
            "Link Google Apps Script Web App URL (https://script.google.com/macros/s/.../exec)",
            value=current_webhook_url,
            placeholder="Dán link Web App URL từ Google Apps Script vào đây..."
        )
    with c_wh2:
        st.html("<div style='height:28px'></div>")
        if st.button("💾 Lưu & Đồng Bộ M5", use_container_width=True):
            if tv_webhook_client.save_webhook_url(new_wh_url):
                st.success("✅ Đã lưu URL Webhook M5! Đang cập nhật lại tín hiệu...")
                backtest_engine.run_full_backtest(force_download=False)
                st.cache_data.clear()
                st.rerun()
    st.html("""
    <div style='font-size:12px; color:#94a3b8; line-height:1.6;'>
    💡 <b>Kiến Trúc 2 Tầng Thích Ứng (Chống Nhiễu):</b><br>
    • <b>Tầng 1 (Cấu Trúc & Điểm Đón):</b> Dùng <b>Nến H1 Đóng Cửa</b> (khi Sideway/Phiên Á-Âu) kết hợp <b>Nến M15/M30 Đóng Cửa Xung Lực FVG 50%</b> (khi vào Phiên Mỹ hoặc biến động mạnh &ge; 0.85 ATR) để khóa cố định điểm Entry / SL / TP.<br>
    • <b>Tầng 2 (Theo Dõi Thực Chiến - M5 Realtime):</b> Nến M5 <b>chỉ dùng để cập nhật Giá Live, đo khoảng cách tiếp cận và kiểm tra khớp lệnh / chạm TP-SL</b>, tuyệt đối không dùng M5 để vẽ lại cấu trúc hay làm nhảy điểm SL/TP.
    </div>
    """)

# ── HÀM HIỂN THỊ RADAR PHÁT HIỆN ĐIỂM VÀO LỆNH TƯƠNG LAI ───────────────────
def render_future_radar_section(radar_list):
    if not radar_list:
        return
        
    ready_cnt = sum(1 for r in radar_list if "SẴN SÀNG" in r.get("status", ""))
    m1_cnt = sum(1 for r in radar_list if "M1" in r.get("method", ""))
    m2_cnt = sum(1 for r in radar_list if "M2" in r.get("method", ""))
    m3_cnt = sum(1 for r in radar_list if "M3" in r.get("method", ""))
    total_cnt = len(radar_list)
    
    rows_html = []
    for r in radar_list:
        comm = r["commodity"]
        prod = r["product"]
        method = r["method"]
        side = r["side"]
        cur_p = r["current_price"]
        entry_p = r["entry_target"]
        dist = r["distance_pts"]
        sl_p = r["sl_price"]
        tp1_p = r["tp1_price"]
        tp2_p = r["tp2_price"]
        tp3_p = r["tp3_price"]
        risk_pts = r["risk_pts"]
        risk_usd = r["risk_usd"]
        rr = r["rr"]
        status_str = r["status"]
        action_hint = r["action_hint"]
        condition = r["condition"]
        
        prod_badge = f"<span style='background:#78350f; color:#fde68a; font-weight:700; padding:2px 7px; border-radius:4px; font-size:11px;'>🌽 {prod}</span>" if comm == "ZC" else f"<span style='background:#1e3a8a; color:#bfdbfe; font-weight:700; padding:2px 7px; border-radius:4px; font-size:11px;'>🌾 {prod}</span>"
        side_badge = "<span style='background:rgba(239, 68, 68, 0.2); color:#f87171; border:1px solid #ef4444; padding:2px 8px; border-radius:4px; font-weight:800; font-size:11px;'>BÁN</span>" if side == "BÁN" else "<span style='background:rgba(16, 185, 129, 0.2); color:#34d399; border:1px solid #10b981; padding:2px 8px; border-radius:4px; font-weight:800; font-size:11px;'>MUA</span>"
        
        if "SẴN SÀNG" in status_str:
            status_badge = f"<span style='background:rgba(234, 179, 8, 0.2); color:#fde047; border:1px solid #eab308; padding:3px 8px; border-radius:4px; font-weight:700; font-size:11px;'>⚡ SẴN SÀNG ({dist:.2f} pts)</span>"
        elif "CHỜ HỒI" in status_str:
            status_badge = f"<span style='background:rgba(59, 130, 246, 0.15); color:#93c5fd; border:1px solid #3b82f6; padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;'>⏳ Chờ hồi {dist:.2f} pts</span>"
        else:
            status_badge = f"<span style='background:rgba(148, 163, 184, 0.15); color:#cbd5e1; border:1px solid #64748b; padding:3px 8px; border-radius:4px; font-weight:600; font-size:11px;'>🔍 Cách {dist:.2f} pts</span>"
            
        is_scalp = ("Scalp" in method or "M1" in method) and ("Swing" not in method)
        tp1_lbl = "+$200" if is_scalp else "+$400"
        tp2_lbl = "+$225" if is_scalp else "+$450"
        tp3_lbl = "+$250" if is_scalp else "+$500"
        target_pnl_str = "+$200 - $250 USD" if is_scalp else "+$400 - $500 USD"
        
        row = f"""
        <details class='radar-accordion'>
          <summary class='radar-summary'>
            <div style='width:95px;'>{prod_badge}</div>
            <div style='flex:1.2; font-weight:600; color:#e2e8f0; font-size:12px;'>{method}</div>
            <div style='width:70px; text-align:center;'>{side_badge}</div>
            <div style='width:80px; font-family:monospace; color:#94a3b8;'>{cur_p:.2f}</div>
            <div style='width:95px; font-family:monospace; font-weight:700; color:#38bdf8;'>{entry_p:.2f}</div>
            <div style='width:95px; text-align:center; font-family:monospace; color:{'#fde047' if dist <= 2.0 else '#cbd5e1'}; font-weight:{'700' if dist <= 2.0 else '400'};'>{dist:.2f} pts</div>
            <div style='width:85px; font-family:monospace; color:#ef4444;'>{sl_p:.2f}</div>
            <div style='width:85px; font-family:monospace; color:#34d399;'>{tp3_p:.2f}</div>
            <div style='width:65px; text-align:center; font-family:monospace; color:#cbd5e1;'>{rr}</div>
            <div style='width:170px;'>{status_badge}</div>
            <div style='width:30px; text-align:center;'><span class='radar-arrow'>▼</span></div>
          </summary>
          <div class='radar-detail-content'>
            <div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-bottom:12px;'>
              <div style='background:#111827; border:1px solid #374151; border-radius:6px; padding:10px;'>
                <div style='font-size:11px; color:#94a3b8; text-transform:uppercase;'>🎯 Điểm Đón Limit ({side})</div>
                <div style='font-size:16px; font-weight:800; color:#38bdf8; font-family:monospace; margin-top:2px;'>{entry_p:.2f}</div>
                <div style='font-size:11px; color:#64748b;'>Giá Live: {cur_p:.2f} (Cách {dist:.2f} pts)</div>
              </div>
              <div style='background:#111827; border:1px solid #374151; border-radius:6px; padding:10px;'>
                <div style='font-size:11px; color:#94a3b8; text-transform:uppercase;'>🛑 Cắt Lỗ An Toàn (SL)</div>
                <div style='font-size:16px; font-weight:800; color:#ef4444; font-family:monospace; margin-top:2px;'>{sl_p:.2f}</div>
                <div style='font-size:11px; color:#f87171;'>Rủi ro: {risk_pts:.2f} pts (${risk_usd:,.0f}/HĐ)</div>
              </div>
              <div style='background:#111827; border:1px solid #374151; border-radius:6px; padding:10px;'>
                <div style='font-size:11px; color:#94a3b8; text-transform:uppercase;'>🏆 Mục Tiêu Chốt Lời (TP)</div>
                <div style='font-size:13px; font-weight:700; color:#34d399; font-family:monospace; margin-top:2px;'>
                  TP1 (Dời BE): {tp1_p:.2f} ({tp1_lbl})<br>
                  TP2: {tp2_p:.2f} ({tp2_lbl})<br>
                  TP3 (Max): {tp3_p:.2f} ({tp3_lbl})
                </div>
              </div>
              <div style='background:#111827; border:1px solid #374151; border-radius:6px; padding:10px;'>
                <div style='font-size:11px; color:#94a3b8; text-transform:uppercase;'>⚖️ Tỷ Lệ Lợi Nhuận / Rủi Ro</div>
                <div style='font-size:16px; font-weight:800; color:#a78bfa; font-family:monospace; margin-top:2px;'>R:R = {rr}</div>
                <div style='font-size:11px; color:#c4b5fd;'>Mục tiêu: {target_pnl_str}</div>
              </div>
            </div>
            <div style='background:#1e1b4b; border-left:4px solid #818cf8; border-radius:6px; padding:10px 14px; margin-bottom:8px;'>
              <div style='font-size:12px; font-weight:700; color:#c7d2fe; margin-bottom:3px;'>💡 HƯỚNG DẪN ĐẶT LỆNH THỰC CHIẾN TRÊN CQG / TRADINGVIEW:</div>
              <div style='font-size:12px; color:#e0e7ff; line-height:1.5;'>{action_hint}</div>
            </div>
            <div style='font-size:11px; color:#94a3b8;'>📊 <b>Căn cứ kỹ thuật & cấu trúc nến:</b> {condition}</div>
          </div>
        </details>
        """
        rows_html.append(row)
        
    radar_html = f"""
    <div style='margin-bottom:24px;'>
      <div style='background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border:1px solid #4338ca; border-radius:10px; padding:16px 20px; margin-bottom:14px; box-shadow: 0 4px 15px rgba(67, 56, 202, 0.15);'>
        <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;'>
          <div>
            <div style='display:flex; align-items:center; gap:8px;'>
              <span style='font-size:20px;'>📡</span>
              <span style='font-size:18px; font-weight:800; color:#f8fafc; letter-spacing:0.3px;'>RADAR PHÁT HIỆN ĐIỂM VÀO LỆNH TƯƠNG LAI (UPCOMING SETUPS)</span>
              <span style='background:#312e81; color:#c7d2fe; font-size:11px; font-weight:700; padding:2px 8px; border-radius:12px; border:1px solid #4f46e5;'>LIVE WATCHLIST</span>
            </div>
            <div style='font-size:12px; color:#94a3b8; margin-top:4px;'>
              <b>Cấu trúc 3 Phương Pháp Mới:</b> M1 Scalp ($200 • Không giữ qua đêm) &nbsp;|&nbsp; M2 Swing ($400-$500 • Đỉnh/Đáy gần nhất) &nbsp;|&nbsp; M3 Hybrid (Phối hợp linh hoạt) &nbsp;|&nbsp; Con trỏ Giá M5 Realtime đo khoảng cách thực tế.
            </div>
          </div>
          <div style='display:flex; gap:10px; flex-wrap:wrap;'>
            <div style='background:#0f172a; border:1px solid #312e81; border-radius:8px; padding:8px 14px; text-align:center;'>
              <div style='font-size:10px; color:#a5b4fc; text-transform:uppercase;'>Tổng Kịch Bản</div>
              <div style='font-size:18px; font-weight:800; color:#ffffff;'>{total_cnt}</div>
            </div>
            <div style='background:#0f172a; border:1px solid #eab308; border-radius:8px; padding:8px 14px; text-align:center;'>
              <div style='font-size:10px; color:#fde047; text-transform:uppercase;'>⚡ Sẵn Sàng</div>
              <div style='font-size:18px; font-weight:800; color:#facc15;'>{ready_cnt}</div>
            </div>
            <div style='background:#0f172a; border:1px solid #0284c7; border-radius:8px; padding:8px 14px; text-align:center;'>
              <div style='font-size:10px; color:#38bdf8; text-transform:uppercase;'>M1 Scalp ($200)</div>
              <div style='font-size:18px; font-weight:800; color:#38bdf8;'>{m1_cnt}</div>
            </div>
            <div style='background:#0f172a; border:1px solid #f59e0b; border-radius:8px; padding:8px 14px; text-align:center;'>
              <div style='font-size:10px; color:#fbbf24; text-transform:uppercase;'>M2 Swing ($400-$500)</div>
              <div style='font-size:18px; font-weight:800; color:#fbbf24;'>{m2_cnt}</div>
            </div>
            <div style='background:#0f172a; border:1px solid #9333ea; border-radius:8px; padding:8px 14px; text-align:center;'>
              <div style='font-size:10px; color:#c084fc; text-transform:uppercase;'>M3 Hybrid</div>
              <div style='font-size:18px; font-weight:800; color:#c084fc;'>{m3_cnt}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class='radar-table-wrapper'>
        <div class='radar-header'>
          <div style='width:95px;'>Mã HĐ</div>
          <div style='flex:1.2;'>Chiến Lược Dự Kiến</div>
          <div style='width:70px; text-align:center;'>Vị Thế</div>
          <div style='width:80px;'>Giá Live</div>
          <div style='width:95px;'>Điểm Đón Plan</div>
          <div style='width:95px; text-align:center;'>Khoảng Cách</div>
          <div style='width:85px;'>Cắt Lỗ (SL)</div>
          <div style='width:85px;'>Chốt Lời TP3</div>
          <div style='width:65px; text-align:center;'>R:R</div>
          <div style='width:170px;'>Trạng Thái Radar</div>
          <div style='width:30px; text-align:center; color:#818cf8;' title='Bấm mũi tên để xem chi tiết'>Chi tiết</div>
        </div>
        {''.join(rows_html)}
      </div>
    </div>
    """
    st.html(radar_html)

# Lấy dữ liệu radar từ data json (hoặc tính tức thì nếu chưa có)
upcoming_radar_data = data.get("upcoming_radar", [])
if not upcoming_radar_data:
    try:
        zc_c = backtest_engine.fetch_or_load_90d("ZC", force_download=False)
        zw_c = backtest_engine.fetch_or_load_90d("ZW", force_download=False)
        upcoming_radar_data = backtest_engine.compute_upcoming_radar(zc_c, zw_c)
    except Exception:
        upcoming_radar_data = []

render_future_radar_section(upcoming_radar_data)

# ── BỘ LỌC CHUNG ────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns([1.3, 1.1, 1.1, 1.4])
with col_f1:
    time_filter = st.selectbox(
        "Khoảng thời gian",
        [
            "Từ đầu năm 2026 (YTD)",
            "30 ngày qua",
            "7 ngày qua",
            "90 ngày qua (Quý)",
            "1 năm qua (365 ngày)",
            "Toàn bộ lịch sử (Tất cả data)"
        ],
        index=0
    )
with col_f2:
    product_filter = st.selectbox(
        "Sản phẩm",
        ["Tất cả sản phẩm", "🌾 Lúa Mì (ZW1! / ZWAZ26)", "🌽 Ngô (ZC1! / ZCEZ26)"],
        index=0
    )
with col_f3:
    result_filter = st.selectbox(
        "Kết quả lệnh",
        ["Tất cả kết quả", "🟢 Vị Thế Đang Mở", "Lệnh Thắng (TP)", "Hòa Vốn (ENTRY)", "Thua Lỗ (SL)", "Chưa Khớp (Pending)"],
        index=0
    )
with col_f4:
    last_gen = data.get("generated_at", "—")
    st.html(f"""
    <div style='text-align:right; padding-top:28px; font-size:12px; color:#64748b;'>
    ⏱ Cập nhật: <b>{last_gen}</b>
    </div>
    """)

# Map days filter
days_map = {
    "Từ đầu năm 2026 (YTD)": "YTD",
    "30 ngày qua": 30,
    "7 ngày qua": 7,
    "90 ngày qua (Quý)": 90,
    "1 năm qua (365 ngày)": 365,
    "Toàn bộ lịch sử (Tất cả data)": "ALL"
}
selected_days = days_map.get(time_filter, "YTD")

# Hàm filter trades
def filter_trades(raw_trades, days, prod_sel, res_sel):
    res = backtest_engine.compute_metrics(raw_trades, days_filter=days)
    filtered = res["filtered_trades"]
    
    if "Lúa Mì" in prod_sel or "ZWAZ26" in prod_sel or "ZW1!" in prod_sel:
        filtered = [t for t in filtered if t["commodity"] == "ZW"]
    elif "Ngô" in prod_sel or "ZCEZ26" in prod_sel or "ZC1!" in prod_sel:
        filtered = [t for t in filtered if t["commodity"] == "ZC"]
        
    if "Đang Mở" in res_sel:
        filtered = [t for t in filtered if t["result"] == "ĐANG MỞ"]
    elif "Thắng" in res_sel:
        filtered = [t for t in filtered if t["result"] in ["TP1", "TP2", "TP3"]]
    elif "Hòa Vốn" in res_sel:
        filtered = [t for t in filtered if t["result"] == "ENTRY"]
    elif "Thua Lỗ" in res_sel:
        filtered = [t for t in filtered if t["result"] == "SL"]
    elif "Chưa Khớp" in res_sel:
        filtered = [t for t in filtered if t["result"] == "CHƯA KHỚP"]
        
    metrics = backtest_engine.compute_metrics(filtered, days_filter=None)
    return filtered, metrics

# ── HÀM HIỂN THỊ KPI CARDS ──────────────────────────────────────────────────
def render_kpi_cards(metrics, filter_label):
    pnl = metrics["total_pnl"]
    pnl_class = "kpi-value-green" if pnl >= 0 else "kpi-value-red"
    pnl_sign = "+" if pnl > 0 else ""
    pnl_str = f"{pnl_sign}${pnl:,.0f}" if abs(pnl) >= 1 else "$0"
    
    win_rate = metrics["win_rate"]
    total_signals = metrics["total_trades"]
    roi = metrics["roi_pct"]
    max_dd = metrics["max_drawdown"]
    
    open_cnt = metrics.get('open_trades', 0)
    open_sub = f"{open_cnt} Mở • " if open_cnt > 0 else ""
    
    html = f"""
<div class='kpi-container'>
<div class='kpi-card'>
<div class='kpi-title'>Tổng lợi nhuận</div>
<div class='{pnl_class}'>{pnl_str}</div>
<div class='kpi-sub'>Toàn bộ dữ liệu đã lọc ({filter_label})</div>
</div>
<div class='kpi-card'>
<div class='kpi-title'>Tỷ lệ thắng</div>
<div class='kpi-value-white'>{win_rate:.1f}%</div>
<div class='kpi-sub'>{metrics['win_trades']} thắng / {metrics.get('decisive_trades', metrics['win_trades'] + metrics['loss_trades'])} lệnh phân định ({metrics['breakeven_trades']} hòa vốn)</div>
</div>
<div class='kpi-card'>
<div class='kpi-title'>Vốn Khuyến Nghị</div>
<div class='kpi-value-white'>10k USD</div>
<div class='kpi-sub'>ROI: <b>{roi:+.1f}%</b> | Max DD: <b>${max_dd:,.0f}</b></div>
</div>
<div class='kpi-card'>
<div class='kpi-title'>Tổng tín hiệu</div>
<div class='kpi-value-white'>{total_signals}</div>
<div class='kpi-sub'>Gồm {open_sub}{metrics['win_trades']} TP • {metrics['breakeven_trades']} Hòa • {metrics['loss_trades']} SL</div>
</div>
</div>
"""
    st.html(html)

# ── HÀM ĐỊNH DẠNG NGÀY & GIỜ ────────────────────────────────────────────────
def format_display_date(date_str: str) -> str:
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return date_str

def format_display_dt(dt_str: str) -> str:
    if not dt_str or dt_str == "—" or "Đang" in str(dt_str):
        return str(dt_str)
    try:
        parts = dt_str.split(" ")
        date_parts = parts[0].split("-")
        if len(date_parts) == 3:
            time_part = f" {parts[1][:5]}" if len(parts) > 1 else ""
            return f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}{time_part}"
    except Exception:
        pass
    return str(dt_str)

# ── HÀM BÓC TÁCH NỘI DUNG HỘ CHIẾU VỊ THẾ KHI XỔ XUỐNG ─────────────────────
def get_trade_passport_inner_html(t, idx: int) -> str:
    side = t.get("side", "")
    prod = t.get("product", "")
    res = t.get("result", "")
    pnl = t.get("pnl", 0.0)
    diff = t.get("diff_points", 0.0)
    entry_p = t.get("entry_price", 0.0)
    exit_p = t.get("exit_price")
    sl_p = t.get("sl_price", 0.0)
    tp1_p = t.get("tp1_price", 0.0)
    tp2_p = t.get("tp2_price", 0.0)
    tp3_p = t.get("tp3_price", 0.0)
    risk_pts = t.get("risk_points", 0.0)
    bars = t.get("bars_held", 0)
    
    sig_time = format_display_dt(t.get("signal_time") or t.get("time", "—"))
    fill_time = format_display_dt(t.get("fill_time")) if t.get("fill_time") else None
    hit_tp1_time = format_display_dt(t.get("hit_tp1_time")) if t.get("hit_tp1_time") else None
    exit_time = format_display_dt(t.get("exit_time", "—"))
    reason = t.get("reason", "Tín hiệu kỹ thuật theo cấu trúc giá.")
    exit_desc = t.get("exit_desc", "—")
    
    side_color = "#ef4444" if side == "BÁN" else "#10b981"
    pnl_color = "#10b981" if pnl > 0 else ("#ef4444" if pnl < 0 else "#9ca3af")
    pnl_sign = "+" if pnl > 0 else ""
    diff_sign = "+" if diff > 0 else ""
    
    # Status badge HTML
    if res == "ĐANG MỞ":
        status_badge = "<span style='background:rgba(56, 189, 248, 0.2); color:#38bdf8; border:1px solid #38bdf8; padding:3px 8px; border-radius:4px; font-weight:700;'>🟢 ĐANG MỞ (Active)</span>"
    elif res in ["TP1", "TP2", "TP3"]:
        status_badge = f"<span style='background:rgba(16, 185, 129, 0.2); color:#10b981; border:1px solid #10b981; padding:3px 8px; border-radius:4px; font-weight:700;'>🎯 THẮNG ({res})</span>"
    elif res == "ENTRY":
        status_badge = "<span style='background:rgba(107, 114, 128, 0.2); color:#cbd5e1; border:1px solid #6b7280; padding:3px 8px; border-radius:4px; font-weight:700;'>🛡️ HÒA VỐN (ENTRY)</span>"
    elif res == "SL":
        status_badge = "<span style='background:rgba(239, 68, 68, 0.2); color:#ef4444; border:1px solid #ef4444; padding:3px 8px; border-radius:4px; font-weight:700;'>🛑 CẮT LỖ (SL)</span>"
    else:
        status_badge = "<span style='background:rgba(75, 85, 99, 0.2); color:#9ca3af; border:1px solid #4b5563; padding:3px 8px; border-radius:4px; font-weight:700;'>⏳ CHƯA KHỚP (Đã hủy)</span>"

    # Step 1
    step1_title = f"Bước 1: Phát hiện tín hiệu Setup ({sig_time})"
    step1_desc = f"<b>Điều kiện kích hoạt:</b> {reason}"
    
    # Step 2
    if fill_time:
        step2_title = f"Bước 2: Khớp lệnh thành công ({fill_time})"
        step2_desc = f"Vị thế <b>{side} {prod}</b> đã khớp tại mức giá <b>{entry_p:.2f}</b>. Stop Loss ban đầu thiết lập tại <b>{sl_p:.2f}</b> (Biên rủi ro: {risk_pts:.2f} pts = ${risk_pts*50:,.0f} USD)."
        step2_icon = "⚡"
    else:
        step2_title = f"Bước 2: Chờ khớp lệnh Limit ({entry_p:.2f})"
        step2_desc = f"Hệ thống treo lệnh Limit <b>{side} {prod}</b> tại giá <b>{entry_p:.2f}</b>. Thị trường không quay lại đón khớp trong vòng 24 nến (24 giờ) ➔ Đã tự động hủy lệnh lúc {exit_time} để bảo toàn vốn."
        step2_icon = "⏳"

    # Step 3
    if hit_tp1_time:
        step3_title = f"Bước 3: Chạm TP1 (1.0R) & Tự Động Dời SL Về Hòa Vốn ({hit_tp1_time})"
        step3_desc = f"Giá thị trường đã chạm mốc <b>TP1 ({tp1_p:.2f})</b>. Hệ thống tự động kích hoạt cơ chế bảo vệ vốn: Dời Stop Loss từ mức ban đầu <b>{sl_p:.2f}</b> về ngay điểm vào lệnh <b>{entry_p:.2f} (Breakeven)</b>, đưa vị thế về trạng thái an toàn tuyệt đối (Risk-Free)."
        step3_icon = "🛡️"
    elif res == "CHƯA KHỚP":
        step3_title = "Bước 3: Không phát sinh vị thế (Lệnh chưa khớp)"
        step3_desc = "Do lệnh Limit không khớp nên không phát sinh vị thế mở trên thị trường."
        step3_icon = "⚪"
    else:
        step3_title = "Bước 3: Diễn biến trong biên độ rủi ro ban đầu"
        step3_desc = f"Giá dao động trong biên độ giữa mức cắt lỗ <b>SL ({sl_p:.2f})</b> và mốc <b>TP1 ({tp1_p:.2f})</b>, chưa kích hoạt dời hòa vốn."
        step3_icon = "📊"

    # Step 4
    if res == "ĐANG MỞ":
        step4_title = f"Bước 4: Vị thế đang chạy Realtime (Đã giữ {bars} nến ~ {bars} giờ)"
        step4_desc = f"<b>Giá thị trường hiện tại:</b> <b style='color:#38bdf8; font-size:14px;'>{exit_p:.2f}</b> • Lợi nhuận tạm tính: <b style='color:{pnl_color}; font-size:14px;'>{pnl_sign}${pnl:,.0f} ({diff_sign}{diff:.2f} pts)</b>.<br>{exit_desc}"
        step4_icon = "🟢"
    elif res == "CHƯA KHỚP":
        step4_title = f"Bước 4: Hủy lệnh chờ Limit ({exit_time})"
        step4_desc = f"{exit_desc} Không phát sinh bất kỳ khoản lỗ hay chi phí nào."
        step4_icon = "🛑"
    else:
        step4_title = f"Bước 4: Đóng vị thế ({exit_time}) • Đã giữ {bars} nến (~{bars} giờ)"
        step4_desc = f"<b>Giá đóng thực tế:</b> <b>{exit_p:.2f}</b> • Kết quả ròng: <b style='color:{pnl_color}; font-size:14px;'>{pnl_sign}${pnl:,.0f} USD ({diff_sign}{diff:.2f} pts)</b>.<br><b>Nhật ký:</b> {exit_desc}"
        step4_icon = "🏁"

    return f"""
    <div style='background:rgba(15, 23, 42, 0.7); border:1px solid #1e293b; border-radius:8px; padding:14px 16px;'>
      <div style='display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:10px; margin-bottom:12px;'>
        <div>
          <span style='font-size:15px; font-weight:800; color:#f8fafc;'>HỘ CHIẾU VỊ THẾ #{idx+1:02d} • {prod} <span style='color:{side_color};'>({side})</span></span>
          <span style='margin-left:8px; font-size:11px; color:#94a3b8; font-family:monospace;'>⏱ Khớp: {fill_time or 'Chưa khớp'}</span>
        </div>
        <div style='display:flex; align-items:center; gap:8px;'>
          {status_badge}
          <span style='font-size:15px; font-weight:800; color:{pnl_color}; font-family:monospace;'>{pnl_sign}${pnl:,.0f}</span>
        </div>
      </div>
      
      <div class='passport-grid'>
        <div class='passport-metric'>
          <div style='font-size:10px; color:#94a3b8; text-transform:uppercase;'>Giá Vào (Entry)</div>
          <div style='font-size:15px; font-weight:700; color:#f8fafc; font-family:monospace;'>{entry_p:.2f}</div>
          <div style='font-size:11px; color:#64748b;'>{fill_time or 'Lệnh Limit'}</div>
        </div>
        <div class='passport-metric'>
          <div style='font-size:10px; color:#94a3b8; text-transform:uppercase;'>Cắt Lỗ Ban Đầu (SL)</div>
          <div style='font-size:15px; font-weight:700; color:#ef4444; font-family:monospace;'>{sl_p:.2f}</div>
          <div style='font-size:11px; color:#f87171;'>Rủi ro: {risk_pts:.2f} pts (${risk_pts*50:,.0f})</div>
        </div>
        <div class='passport-metric'>
          <div style='font-size:10px; color:#94a3b8; text-transform:uppercase;'>Mục Tiêu TP (1R / 1.5R / 2R)</div>
          <div style='font-size:12px; font-weight:700; color:#34d399; font-family:monospace;'>
            TP1: {tp1_p:.2f} | TP2: {tp2_p:.2f}<br>TP3 (Max): {tp3_p:.2f}
          </div>
          <div style='font-size:10px; color:#10b981;'>TP1 kích hoạt dời SL hòa vốn</div>
        </div>
        <div class='passport-metric'>
          <div style='font-size:10px; color:#94a3b8; text-transform:uppercase;'>Giá Đóng / Hiện Tại</div>
          <div style='font-size:15px; font-weight:700; color:{pnl_color}; font-family:monospace;'>{exit_p if exit_p else '—'}</div>
          <div style='font-size:11px; color:#64748b;'>Đã giữ: {bars} nến ({bars}h)</div>
        </div>
      </div>
      
      <div style='font-size:12px; font-weight:700; color:#cbd5e1; margin-bottom:8px;'>📜 HÀNH TRÌNH VỊ THẾ TỪNG BƯỚC:</div>
      <div class='timeline-flow'>
        <div class='timeline-step'>
          <div class='timeline-step-icon'>🕒</div>
          <div class='timeline-step-content'>
            <div class='timeline-step-title'>{step1_title}</div>
            <div class='timeline-step-desc'>{step1_desc}</div>
          </div>
        </div>
        <div class='timeline-step'>
          <div class='timeline-step-icon'>{step2_icon}</div>
          <div class='timeline-step-content'>
            <div class='timeline-step-title'>{step2_title}</div>
            <div class='timeline-step-desc'>{step2_desc}</div>
          </div>
        </div>
        <div class='timeline-step'>
          <div class='timeline-step-icon'>{step3_icon}</div>
          <div class='timeline-step-content'>
            <div class='timeline-step-title'>{step3_title}</div>
            <div class='timeline-step-desc'>{step3_desc}</div>
          </div>
        </div>
        <div class='timeline-step'>
          <div class='timeline-step-icon'>{step4_icon}</div>
          <div class='timeline-step-content'>
            <div class='timeline-step-title'>{step4_title}</div>
            <div class='timeline-step-desc'>{step4_desc}</div>
          </div>
        </div>
      </div>
    </div>
    """

# ── HÀM HIỂN THỊ BẢNG TÍN HIỆU VỚI MŨI TÊN XỔ XUỐNG CHI TIẾT (ACCORDION TABLE) ────
def render_trade_table(trades, show_tag: bool = False):
    if not trades:
        st.info("Không có tín hiệu nào phù hợp với bộ lọc hiện tại.")
        return

    banner_html = """
    <div style='background:rgba(56, 189, 248, 0.08); border-left:3px solid #38bdf8; padding:10px 14px; border-radius:6px; font-size:12px; color:#cbd5e1; margin:8px 0 12px 0; line-height:1.6;'>
      💡 <b>Hướng dẫn tương tác:</b> Bấm vào bất kỳ dòng lệnh nào (hoặc biểu tượng mũi tên <b style='color:#38bdf8;'>▼</b> ở cuối dòng) để <b>xổ xuống xem toàn bộ Hành Trình Lệnh</b> (Giá vào, SL ban đầu, TP đa tầng, Timeline từng bước).
      <br><span style='color:#94a3b8;'>Hệ số CBOT $50/pt: Biến động 1 point = $50 USD. Công thức: Lợi Nhuận ($) = Điểm (pts) × $50.</span>
    </div>
    """
    st.html(banner_html)

    rows_html = []
    for idx, t in enumerate(trades):
        side_badge = "<span class='badge-sell'>Bán</span>" if t["side"] == "BÁN" else "<span class='badge-buy'>Mua</span>"
        
        res = t.get("result", "")
        if res == "ĐANG MỞ":
            res_badge = "<span class='badge-res-open'>🟢 ĐANG MỞ</span>"
        elif res == "TP3":
            res_badge = "<span class='badge-res-tp3'>TP3 (2R)</span>"
        elif res == "TP2":
            res_badge = "<span class='badge-res-tp2'>TP2 (1.5R)</span>"
        elif res == "TP1":
            res_badge = "<span class='badge-res-tp1'>TP1 (1R)</span>"
        elif res == "ENTRY":
            res_badge = "<span class='badge-res-entry'>ENTRY (Hòa)</span>"
        elif res == "SL":
            res_badge = "<span class='badge-res-sl'>SL (Lỗ)</span>"
        else:
            res_badge = "<span class='badge-res-pending'>CHƯA KHỚP</span>"
            
        entry_val = t.get("entry_price")
        exit_val = t.get("exit_price")
        
        entry_str = f"{entry_val:.2f}" if entry_val is not None else "-"
        if res == "ĐANG MỞ":
            exit_str = f"<span style='color:#38bdf8;'>Live: {exit_val:.2f}</span>" if exit_val is not None else "-"
        elif res == "CHƯA KHỚP":
            exit_str = "<span style='color:#6b7280;'>—</span>"
        else:
            exit_str = f"{exit_val:.2f}" if exit_val is not None else "-"
            
        diff_pts = t.get("diff_points", 0.0)
        pnl = t.get("pnl", 0.0)
        
        if res == "CHƯA KHỚP":
            diff_html = "<span style='color:#6b7280;'>0.00 pts</span>"
            pnl_html = "<span style='color:#6b7280;'>$0</span>"
        elif diff_pts > 0:
            diff_html = f"<b style='color:#10b981;'>+{diff_pts:.2f} pts</b>"
            pnl_html = f"<b style='color:#10b981;'>+${pnl:,.0f}</b>"
        elif diff_pts < 0:
            diff_html = f"<b style='color:#ef4444;'>{diff_pts:.2f} pts</b>"
            pnl_html = f"<b style='color:#ef4444;'>-${abs(pnl):,.0f}</b>"
        else:
            diff_html = "<span style='color:#9ca3af;'>0.00 pts</span>"
            pnl_html = "<span style='color:#9ca3af;'>$0</span>"
            
        # Xác định tên phương thức cho dòng 2 (Dòng trên: Mã sản phẩm, Dòng dưới: Tên phương thức)
        method_name = t.get("tag")
        if not method_name:
            m_raw = t.get("method", "")
            if "M1" in m_raw:
                method_name = "M1 Scalp"
            elif "M2" in m_raw:
                method_name = "M2 Swing"
            elif "M3" in m_raw:
                method_name = "M3 Hybrid"
            else:
                method_name = "ICT Setup"
                
        # Phối màu trực quan theo từng phương thức (M1: Xanh dương Scalp, M2: Cam/Xanh lá Swing, M3: Tím hoàng gia Hybrid)
        if "M3" in method_name:
            if "Đáy" in method_name:
                tag_color = "#34d399"  # Xanh Mint Bắt Đáy
                tag_bg = "rgba(52, 211, 153, 0.12)"
                tag_border = "rgba(192, 132, 252, 0.5)"  # Viền tím M3
            elif "Đỉnh" in method_name:
                tag_color = "#fbbf24"  # Vàng Cam Bắt Đỉnh
                tag_bg = "rgba(251, 191, 36, 0.12)"
                tag_border = "rgba(192, 132, 252, 0.5)"  # Viền tím M3
            elif "Scalp" in method_name:
                tag_color = "#e879f9"  # Hồng Tím M3 Scalp
                tag_bg = "rgba(232, 121, 249, 0.14)"
                tag_border = "rgba(192, 132, 252, 0.55)"
            else:
                tag_color = "#c084fc"  # Tím Thạch Anh M3 Swing / Hybrid
                tag_bg = "rgba(192, 132, 252, 0.16)"
                tag_border = "rgba(192, 132, 252, 0.55)"
        elif "M1" in method_name or "Scalp" in method_name or "Trend" in method_name:
            tag_color = "#38bdf8"      # Xanh Dương M1 Scalp
            tag_bg = "rgba(56, 189, 248, 0.12)"
            tag_border = "rgba(56, 189, 248, 0.35)"
        elif "M2" in method_name or "Swing" in method_name:
            if "Đáy" in method_name:
                tag_color = "#10b981"  # Xanh Lá M2 Swing Đáy
                tag_bg = "rgba(16, 185, 129, 0.12)"
                tag_border = "rgba(16, 185, 129, 0.35)"
            elif "Đỉnh" in method_name:
                tag_color = "#f59e0b"  # Cam Hổ Phách M2 Swing Đỉnh
                tag_bg = "rgba(245, 158, 11, 0.12)"
                tag_border = "rgba(245, 158, 11, 0.35)"
            else:
                tag_color = "#fb923c"  # Cam M2 Swing
                tag_bg = "rgba(251, 146, 60, 0.12)"
                tag_border = "rgba(251, 146, 60, 0.35)"
        else:
            tag_color = "#94a3b8"
            tag_bg = "rgba(148, 163, 184, 0.12)"
            tag_border = "rgba(148, 163, 184, 0.35)"
            
        prod_col_html = (
            f"<div style='width:120px; display:flex; flex-direction:column; justify-content:center;'>"
            f"<div style='font-weight:700; color:#f8fafc; font-size:13px; line-height:1.2; letter-spacing:0.2px;'>{t['product']}</div>"
            f"<div style='margin-top:4px;'><span style='font-size:10px; font-weight:600; color:{tag_color}; background:{tag_bg}; border:1px solid {tag_border}; padding:1px 6px; border-radius:4px; display:inline-block; white-space:nowrap;'>{method_name}</span></div>"
            f"</div>"
        )
            
        raw_dt = t.get("fill_time") or t.get("signal_time") or t.get("time", "")
        display_time = format_display_dt(raw_dt)
        
        passport_content = get_trade_passport_inner_html(t, idx)
        
        row_accordion = (
            f"<details class='trade-accordion'>"
            f"<summary class='trade-summary'>"
            f"<div style='width:36px; text-align:center; color:#64748b; font-family:monospace;'>#{idx+1}</div>"
            f"<div style='width:130px; color:#cbd5e1; font-family:monospace; font-size:12px;'>{display_time}</div>"
            f"<div style='width:70px;'>{side_badge}</div>"
            f"{prod_col_html}"
            f"<div style='width:105px;'>{res_badge}</div>"
            f"<div style='width:80px; font-family:monospace; font-weight:600;'>{entry_str}</div>"
            f"<div style='width:90px; font-family:monospace; font-weight:600;'>{exit_str}</div>"
            f"<div style='width:90px; text-align:center; font-family:monospace;'>{diff_html}</div>"
            f"<div style='width:65px; text-align:center; color:#94a3b8; font-family:monospace;'>$50/pt</div>"
            f"<div style='flex:1; text-align:right; font-family:monospace; padding-right:12px;'>{pnl_html}</div>"
            f"<div style='width:30px; text-align:center;'><span class='trade-arrow'>▼</span></div>"
            f"</summary>"
            f"<div class='trade-detail-content'>"
            f"{passport_content}"
            f"</div>"
            f"</details>"
        )
        rows_html.append(row_accordion)
        
    full_table_html = (
        f"<div style='overflow-x:auto; margin-bottom:16px;'>"
        f"<div class='trade-table-wrapper' style='min-width:900px;'>"
        f"<div class='trade-table-header'>"
        f"<div style='width:36px; text-align:center;'>#</div>"
        f"<div style='width:130px;'>Ngày & Giờ Khớp</div>"
        f"<div style='width:70px;'>Vị thế</div>"
        f"<div style='width:120px;'>Sản phẩm</div>"
        f"<div style='width:105px;'>Trạng thái</div>"
        f"<div style='width:80px;'>Giá vào</div>"
        f"<div style='width:90px;'>Giá đóng/Live</div>"
        f"<div style='width:90px; text-align:center;'>Điểm (Pts)</div>"
        f"<div style='width:65px; text-align:center;'>Hệ số</div>"
        f"<div style='flex:1; text-align:right; padding-right:12px;'>Lợi nhuận ($)</div>"
        f"<div style='width:30px; text-align:center; color:#38bdf8;' title='Bấm mũi tên để xổ xuống'>Chi tiết</div>"
        f"</div>"
        f"{''.join(rows_html)}"
        f"</div>"
        f"</div>"
    )
    st.html(full_table_html)

# ── BIỂU ĐỒ EQUITY CURVE ────────────────────────────────────────────────────
def render_equity_chart(trades, method_name):
    if not trades:
        return
    sorted_trades = sorted([t for t in trades if t["result"] != "CHƯA KHỚP"], key=lambda x: x["time"])
    if not sorted_trades:
        return
        
    dates = []
    equity = [10000.0]
    cur = 10000.0
    dates.append(format_display_date(sorted_trades[0]["date"]))
    
    for t in sorted_trades:
        cur += t["pnl"]
        dates.append(format_display_date(t["date"]))
        equity.append(cur)
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=equity,
        mode='lines+markers',
        name='Vốn Tài Khoản ($)',
        line=dict(color='#10b981' if cur >= 10000 else '#ef4444', width=3),
        marker=dict(size=5, color='#38bdf8'),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.08)' if cur >= 10000 else 'rgba(239, 68, 68, 0.08)'
    ))
    
    fig.add_hline(y=10000, line_dash="dash", line_color="#64748b", annotation_text="Vốn ban đầu $10,000")
    
    fig.update_layout(
        title=f"Đường Tăng Trưởng Vốn (Equity Curve) — {method_name}",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#9ca3af"),
        height=320,
        margin=dict(l=40, r=40, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#1f2937"),
        yaxis=dict(showgrid=True, gridcolor="#1f2937", tickprefix="$")
    )
    st.plotly_chart(fig, use_container_width=True)

# ── NẠP DỮ LIỆU CẢ 3 PHƯƠNG PHÁP ───────────────────────────────────────────
m1_raw = data.get("method_1", {}).get("trades", [])
m2_raw = data.get("method_2", {}).get("trades", [])
m3_raw = data.get("method_3", {}).get("trades", [])

m1_trades, m1_metrics = filter_trades(m1_raw, selected_days, product_filter, result_filter)
m2_trades, m2_metrics = filter_trades(m2_raw, selected_days, product_filter, result_filter)
m3_trades, m3_metrics = filter_trades(m3_raw, selected_days, product_filter, result_filter)

# ── 4 TABS GIAO DIỆN ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ M1: Scalp / Intraday ($200)",
    "🎯 M2: Swing Đỉnh/Đáy ($400–$500)",
    "🚀 M3: Hybrid (Scalp + Swing)",
    "⚔️ So Sánh Đối Đầu (M1 • M2 • M3)"
])

# ── TAB 1 ───────────────────────────────────────────────────────────────────
with tab1:
    st.html("""
    <div style='background:#111827; border-left:4px solid #38bdf8; padding:12px 16px; border-radius:6px; margin-bottom:16px;'>
    <b style='color:#38bdf8; font-size:14px;'>⚡ Nguyên Lý Giao Dịch Scalp / Intraday (Mục Tiêu $200 USD • Không Giữ Qua Đêm):</b>
    <span style='color:#cbd5e1; font-size:13px;'>
    Giao dịch ngắn hạn thuận xu hướng <b>EMA 21 – 50</b> trong khung giờ sôi động nhất trong ngày (<b>14:00 – 22:00 VN</b>). 
    Đặt lệnh Limit đón nhịp nhúng về sát EMA21, mục tiêu chốt lời nhanh <b>TP1 = +4.0 pts ($200 USD)</b>, <b>TP2 = +4.5 pts ($225 USD)</b>, <b>TP3 = +5.0 pts ($250 USD)</b>. 
    Khi lệnh lãi đạt <b>+$120–$130</b> tự động dời SL về hòa vốn. <b>Tuyệt đối tất toán trong ngày (tối đa 9 nến H1), không treo hay giữ lệnh qua đêm.</b>
    </span>
    </div>
    """)
    
    render_kpi_cards(m1_metrics, time_filter)
    
    st.html(f"<div style='font-size:14px; color:#9ca3af; margin-bottom:8px;'>Hiển thị <b>1–{len(m1_trades)}</b> trên <b>{len(m1_trades)}</b> tín hiệu (Bấm vào dòng lệnh hoặc mũi tên <b style='color:#38bdf8;'>▼</b> để xem chi tiết)</div>")
    render_trade_table(m1_trades)
    st.html("<div style='height:20px'></div>")
    render_equity_chart(m1_trades, "M1 (Scalp / Intraday • $200 USD)")

# ── TAB 2 ───────────────────────────────────────────────────────────────────
with tab2:
    st.html("""
    <div style='background:#111827; border-left:4px solid #f59e0b; padding:12px 16px; border-radius:6px; margin-bottom:16px;'>
    <b style='color:#f59e0b; font-size:14px;'>🎯 Nguyên Lý Giao Dịch Swing Đỉnh / Đáy Gần Nhất (Mục Tiêu $400–$500 USD • Giữ Vài Ngày):</b>
    <span style='color:#cbd5e1; font-size:13px;'>
    Xác định cấu trúc <b>Đỉnh / Đáy Gần Nhất</b> (Vùng SMC Zone đạt chuẩn &ge; 5/8 sao hoặc cụm Đáy cao hơn / Đỉnh thấp hơn 20 nến đồng thuận xu hướng EMA 21–50). 
    Đặt lệnh đón tại vùng Đỉnh/Đáy với mục tiêu lợi nhuận lớn: <b>TP1 = +8.0 pts ($400 USD)</b>, <b>TP2 = +9.0 pts ($450 USD)</b>, <b>TP3 = +10.0 pts ($500 USD)</b>. 
    <b>Lệnh được phép treo và giữ qua vài ngày (tối đa 5 ngày giao dịch)</b> để ăn trọn con sóng Swing, tự động dời SL về hòa vốn khi lãi đạt +$225–$250.
    </span>
    </div>
    """)
    
    render_kpi_cards(m2_metrics, time_filter)
    
    st.html(f"<div style='font-size:14px; color:#9ca3af; margin-bottom:8px;'>Hiển thị <b>1–{len(m2_trades)}</b> trên <b>{len(m2_trades)}</b> tín hiệu (Bấm vào dòng lệnh hoặc mũi tên <b style='color:#38bdf8;'>▼</b> để xem chi tiết)</div>")
    render_trade_table(m2_trades)
    st.html("<div style='height:20px'></div>")
    render_equity_chart(m2_trades, "M2 (Swing Đỉnh/Đáy • $400–$500 USD)")

# ── TAB 3: CHIẾN LƯỢC HYBRID (M1 + M2 KẾT HỢP) ──────────────────────────────
with tab3:
    st.html("""
    <div style='background:#111827; border-left:4px solid #a855f7; padding:12px 16px; border-radius:6px; margin-bottom:16px;'>
    <b style='color:#c084fc; font-size:14px;'>🚀 Cơ Chế Phối Hợp Hybrid Độc Quyền (Scalp Intraday $200 + Swing Đỉnh/Đáy $400–$500):</b>
    <span style='color:#cbd5e1; font-size:13px;'>
    <b>1. Ưu Tiên 1 — Bắt Sóng Lớn Swing ($400–$500 USD):</b> Khi xuất hiện cấu trúc Đỉnh/Đáy gần nhất (SMC Zone 5★ hoặc Swing 20 nến với biên độ ATR mở rộng), hệ thống kích hoạt lệnh <b>Swing giữ vài ngày</b> để thu về $400–$500/lệnh.<br>
    <b>2. Ưu Tiên 2 — Đánh Ngắn Scalp Intraday ($200 USD):</b> Khi thị trường vận động giữa chu kỳ sóng trong khung giờ 14h–22h, hệ thống linh hoạt đi lệnh <b>Scalp ngắn hạn chốt $200 USD</b> và đóng ngay trong ngày.<br>
    <b>3. Quản Trị Xung Đột Lệnh:</b> Tuyệt đối không mở vị thế chồng chéo khi đang có lệnh hoạt động, giúp tối đa hóa cả Tỷ lệ thắng (Win Rate > 60%) lẫn Tổng lợi nhuận ròng.
    </span>
    </div>
    """)
    
    render_kpi_cards(m3_metrics, time_filter)
    
    st.html(f"<div style='font-size:14px; color:#9ca3af; margin-bottom:8px;'>Hiển thị <b>1–{len(m3_trades)}</b> trên <b>{len(m3_trades)}</b> tín hiệu (Đã gắn nhãn • Bấm vào dòng lệnh hoặc mũi tên <b style='color:#38bdf8;'>▼</b> để xem chi tiết)</div>")
    render_trade_table(m3_trades, show_tag=True)
    st.html("<div style='height:20px'></div>")
    render_equity_chart(m3_trades, "M3 (Chiến Lược Hybrid Scalp + Swing)")

# ── TAB 4: SO SÁNH HIỆU QUẢ CẢ 3 PHƯƠNG PHÁP ĐỐI ĐẦU ────────────────────────
with tab4:
    st.html(f"""
    <div style='font-size:18px; font-weight:800; color:#f8fafc; margin-bottom:4px;'>
    ⚔️ BẢNG SO SÁNH ĐỐI ĐẦU CẢ 3 CHIẾN LƯỢC ({time_filter.upper()})
    </div>
    <div style='font-size:13px; color:#94a3af; margin-bottom:16px;'>
    Đối chiếu toàn diện giữa <b>M1 (Scalp / Intraday $200)</b>, <b>M2 (Swing Đỉnh/Đáy $400–$500)</b> và <b>M3 (Hybrid Kết Hợp)</b> trên vốn chuẩn $10,000 USD
    </div>
    """)
    
    m1_pnl_color = "#10b981" if m1_metrics["total_pnl"] >= 0 else "#ef4444"
    m2_pnl_color = "#10b981" if m2_metrics["total_pnl"] >= 0 else "#ef4444"
    m3_pnl_color = "#10b981" if m3_metrics["total_pnl"] >= 0 else "#ef4444"
    
    open_m1_str = f"<span style='color:#38bdf8;'>{m1_metrics['open_trades']} Mở</span> • " if m1_metrics.get("open_trades") else ""
    open_m2_str = f"<span style='color:#38bdf8;'>{m2_metrics['open_trades']} Mở</span> • " if m2_metrics.get("open_trades") else ""
    open_m3_str = f"<span style='color:#38bdf8;'>{m3_metrics['open_trades']} Mở</span> • " if m3_metrics.get("open_trades") else ""
    
    pending_m1_str = f" • <span style='color:#6b7280;'>({m1_metrics['pending_trades']} Chưa khớp)</span>" if m1_metrics.get("pending_trades") else ""
    pending_m3_str = f" • <span style='color:#6b7280;'>({m3_metrics['pending_trades']} Chưa khớp)</span>" if m3_metrics.get("pending_trades") else ""
    
    comp_table = (
        f"<table class='custom-table'>"
        f"<thead><tr>"
        f"<th style='width:22%;'>Chỉ Số Đánh Giá (Metric)</th>"
        f"<th style='width:26%; color:#38bdf8;'>⚡ M1: Scalp / Intraday ($200)</th>"
        f"<th style='width:26%; color:#f59e0b;'>🎯 M2: Swing Đỉnh/Đáy ($400–$500)</th>"
        f"<th style='width:26%; color:#c084fc;'>🚀 M3: Hybrid (Scalp + Swing)</th>"
        f"</tr></thead>"
        f"<tbody>"
        f"<tr><td><b>Tổng Lợi Nhuận Ròng (PnL)</b></td>"
        f"<td><b style='color:{m1_pnl_color}; font-size:16px;'>{m1_metrics['total_pnl']:+,} USD</b></td>"
        f"<td><b style='color:{m2_pnl_color}; font-size:16px;'>{m2_metrics['total_pnl']:+,} USD</b></td>"
        f"<td><b style='color:{m3_pnl_color}; font-size:16px;'>{m3_metrics['total_pnl']:+,} USD</b></td></tr>"
        f"<tr><td><b>Tỷ Suất Lợi Nhuận (ROI trên 10k)</b></td>"
        f"<td><b style='color:{m1_pnl_color};'>{m1_metrics['roi_pct']:+.1f}%</b></td>"
        f"<td><b style='color:{m2_pnl_color};'>{m2_metrics['roi_pct']:+.1f}%</b></td>"
        f"<td><b style='color:{m3_pnl_color}; font-weight:800;'>{m3_metrics['roi_pct']:+.1f}%</b></td></tr>"
        f"<tr><td><b>Tỷ Lệ Thắng Thực Tế (Win Rate)</b><br><span style='font-size:11px; color:#94a3b8; font-weight:normal;'>Win / (Win + Loss) • Không tính lệnh Hòa $0</span></td>"
        f"<td><b style='font-size:15px; color:#f8fafc;'>{m1_metrics['win_rate']:.1f}%</b></td>"
        f"<td><b style='font-size:15px; color:#f8fafc;'>{m2_metrics['win_rate']:.1f}%</b></td>"
        f"<td><b style='font-size:15px; color:#a855f7;'>{m3_metrics['win_rate']:.1f}%</b></td></tr>"
        f"<tr style='background:rgba(56, 189, 248, 0.06);'><td><b>🎯 Tỷ Lệ Chạm TP1 / Kích Hoạt Dời Hòa Vốn</b><br><span style='font-size:11px; color:#38bdf8; font-weight:normal;'>Đo độ chuẩn của Điểm Vào Lệnh (Entry Accuracy)</span></td>"
        f"<td><b style='font-size:15px; color:#34d399;'>{m1_metrics.get('tp1_reach_rate', 0.0):.1f}%</b> <span style='font-size:12px; color:#94a3b8;'>({m1_metrics.get('tp1_reach_trades', 0)}/{m1_metrics['closed_trades']} lệnh)</span></td>"
        f"<td><b style='font-size:15px; color:#34d399;'>{m2_metrics.get('tp1_reach_rate', 0.0):.1f}%</b> <span style='font-size:12px; color:#94a3b8;'>({m2_metrics.get('tp1_reach_trades', 0)}/{m2_metrics['closed_trades']} lệnh)</span></td>"
        f"<td><b style='font-size:15px; color:#34d399;'>{m3_metrics.get('tp1_reach_rate', 0.0):.1f}%</b> <span style='font-size:12px; color:#94a3b8;'>({m3_metrics.get('tp1_reach_trades', 0)}/{m3_metrics['closed_trades']} lệnh)</span></td></tr>"
        f"<tr><td><b>Hệ Số Lợi Nhuận (Profit Factor)</b></td>"
        f"<td><b>{m1_metrics['profit_factor']}</b></td>"
        f"<td><b>{m2_metrics['profit_factor']}</b></td>"
        f"<td><b style='color:#10b981;'>{m3_metrics['profit_factor']}</b></td></tr>"
        f"<tr><td><b>Mức Sụt Giảm Tối Đa (Max Drawdown)</b></td>"
        f"<td style='color:#f87171;'>-${m1_metrics['max_drawdown']:,.0f}</td>"
        f"<td style='color:#f87171;'>-${m2_metrics['max_drawdown']:,.0f}</td>"
        f"<td style='color:#34d399;'>-${m3_metrics['max_drawdown']:,.0f}</td></tr>"
        f"<tr><td><b>Tổng Số Lệnh Phát Tín Hiệu</b></td>"
        f"<td>{m1_metrics['total_trades']} tín hiệu</td>"
        f"<td>{m2_metrics['total_trades']} tín hiệu</td>"
        f"<td>{m3_metrics['total_trades']} tín hiệu</td></tr>"
        f"<tr><td><b>Cơ Cấu Lệnh (Thắng / Hòa / Thua)</b></td>"
        f"<td>{open_m1_str}<span style='color:#10b981;'>{m1_metrics['win_trades']} TP</span> • <span style='color:#9ca3af;'>{m1_metrics['breakeven_trades']} Hòa</span> • <span style='color:#ef4444;'>{m1_metrics['loss_trades']} SL</span>{pending_m1_str}</td>"
        f"<td>{open_m2_str}<span style='color:#10b981;'>{m2_metrics['win_trades']} TP</span> • <span style='color:#9ca3af;'>{m2_metrics['breakeven_trades']} Hòa</span> • <span style='color:#ef4444;'>{m2_metrics['loss_trades']} SL</span></td>"
        f"<td>{open_m3_str}<span style='color:#10b981;'>{m3_metrics['win_trades']} TP</span> • <span style='color:#9ca3af;'>{m3_metrics['breakeven_trades']} Hòa</span> • <span style='color:#ef4444;'>{m3_metrics['loss_trades']} SL</span>{pending_m3_str}</td></tr>"
        f"<tr><td><b>Phong Cách & Thời Gian Giữ Lệnh</b></td>"
        f"<td style='color:#93c5fd;'>Đánh ngắn trong ngày (Không giữ qua đêm • $200/lệnh)</td>"
        f"<td style='color:#fde68a;'>Treo giữ lệnh vài ngày (Đỉnh/Đáy gần nhất • $400–$500/lệnh)</td>"
        f"<td style='color:#c084fc;'>Kết hợp linh hoạt (Vừa ăn sóng Swing lớn, vừa Scalp trong ngày)</td></tr>"
        f"</tbody></table>"
    )
    st.html(comp_table)
    
    st.html("<div style='height:16px'></div>")
    
    st.html("""
    <div style='background:#111827; border:1px solid #1f2937; border-radius:8px; padding:16px 20px;'>
    <div style='font-size:15px; font-weight:700; color:#f8fafc; margin-bottom:8px;'>💡 KẾT LUẬN & ĐÁNH GIÁ THỰC CHIẾN 3 PHƯƠNG PHÁP:</div>
    <ul style='color:#cbd5e1; font-size:13px; line-height:1.7; margin:0; padding-left:20px;'>
    <li><b>Phương Pháp 1 (Scalp / Intraday — Mục tiêu $200 USD):</b> Dành cho nhà đầu tư thích đánh nhanh rút gọn trong phiên (14h–22h), tuyệt đối không giữ lệnh qua đêm để tránh rủi ro Gap mở cửa phiên hôm sau. Tỷ lệ thắng rất cao (&gt;60%) nhờ mục tiêu chốt lời vừa vặn với biên độ dao động nội ngày (4.0 pts = $200 USD).</li>
    <li><b>Phương Pháp 2 (Swing Đỉnh / Đáy Gần Nhất — Mục tiêu $400–$500 USD):</b> Dành cho giao dịch theo sóng lớn tại các vùng Đỉnh/Đáy quan trọng. Lệnh được phép treo và giữ qua vài ngày (tối đa 5 ngày) với biên độ SL rộng hơn để chịu được nhịp rung lắc, mang lại lợi nhuận lớn $400–$500 USD trên mỗi giao dịch thắng.</li>
    <li><b>Phương Pháp 3 (Chiến Lược Hybrid Khuyến Nghị):</b> Tối ưu hóa dòng vốn bằng cách ưu tiên vào lệnh <b>Swing ($400–$500)</b> khi xuất hiện cấu trúc Đỉnh/Đáy gần nhất có biên độ lớn, và chuyển sang đánh <b>Scalp Intraday ($200)</b> trong ngày khi thị trường đi giữa sóng.</li>
    </ul>
    </div>
    """)
