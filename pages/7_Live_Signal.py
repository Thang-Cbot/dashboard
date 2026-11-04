"""
pages/7_Live_Signal.py — Live Signal & Thống Kê Hiệu Suất Mô Phỏng CQG
=====================================================================
Giao diện phân tích và theo dõi tín hiệu Real-time / Backtest hiệu suất 90 ngày.
So sánh 2 phương pháp giao dịch:
  1. ICT MSS + Pullback EMA 21-50 (Thuận xu hướng SMC)
  2. FVG + Bắt Đáy / Đỉnh SMC Zone (Đảo chiều vùng cực trị 5 sao)
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

import backtest_engine

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
st.markdown(clean_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #0b1120; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }

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

/* Custom Table */
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
"""), unsafe_allow_html=True)


# ── SIDEBAR NAV ─────────────────────────────────────────────────────────────
st.sidebar.markdown(clean_html("""
<div style='text-align:center; padding:16px 0 8px;'>
<div style='font-size:24px; font-weight:800; color:#e2e8f0;'>📊 CBOT</div>
<div style='font-size:11px; color:#64748b; letter-spacing:2px;'>TRADING DASHBOARD</div>
</div>
"""), unsafe_allow_html=True)
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


# ── NẠP DỮ LIỆU BACKTEST ───────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_backtest_data():
    if not BACKTEST_FILE.exists():
        backtest_engine.run_full_backtest(force_download=False)
    try:
        with open(BACKTEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu backtest: {e}")
        return {}

data = load_backtest_data()

# ── HEADER & THANH ĐIỀU KHIỂN ──────────────────────────────────────────────
col_header, col_actions = st.columns([3, 1])
with col_header:
    st.markdown(clean_html("""
    <div style='display:flex; align-items:center; gap:12px; margin-bottom:4px;'>
    <div style='font-size:28px; font-weight:800; color:#f8fafc;'>Invest<span style='color:#f59e0b;'>X</span> • Live Signal</div>
    <span style='background:#1e293b; color:#38bdf8; font-size:12px; font-weight:700; padding:4px 10px; border-radius:6px; border:1px solid #0284c7;'>CQG SIMULATION</span>
    </div>
    <div style='font-size:20px; font-weight:700; color:#f1f5f9; margin-bottom:2px;'>Lịch sử & Thống kê hiệu suất</div>
    <div style='font-size:13px; color:#94a3b8; margin-bottom:18px;'>Kết quả các tín hiệu vào lệnh mô phỏng theo dữ liệu giá thực tế CBOT trong 90 ngày qua</div>
    """), unsafe_allow_html=True)

with col_actions:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Cập Nhật & Test Lại (90d)", use_container_width=True, type="primary"):
        with st.spinner("Đang tải dữ liệu H1 từ Yahoo và chạy lại toàn bộ mô phỏng 90 ngày..."):
            backtest_engine.run_full_backtest(force_download=True)
            st.cache_data.clear()
            st.rerun()

# ── BỘ LỌC CHUNG ────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns([1.2, 1.2, 1.2, 1.5])
with col_f1:
    time_filter = st.selectbox(
        "Khoảng thời gian",
        ["30 ngày qua", "7 ngày qua", "90 ngày qua (Toàn bộ)"],
        index=0
    )
with col_f2:
    product_filter = st.selectbox(
        "Sản phẩm",
        ["Tất cả sản phẩm", "🌾 ZWAZ26 (Lúa Mì)", "🌽 ZCEZ26 (Ngô)"],
        index=0
    )
with col_f3:
    result_filter = st.selectbox(
        "Kết quả lệnh",
        ["Tất cả kết quả", "Lệnh Thắng (TP)", "Hòa Vốn (ENTRY)", "Thua Lỗ (SL)", "Chưa Khớp"],
        index=0
    )
with col_f4:
    last_gen = data.get("generated_at", "—")
    st.markdown(clean_html(f"""
    <div style='text-align:right; padding-top:28px; font-size:12px; color:#64748b;'>
    ⏱ Cập nhật: <b>{last_gen}</b>
    </div>
    """), unsafe_allow_html=True)

# Map days filter
days_map = {
    "7 ngày qua": 7,
    "30 ngày qua": 30,
    "90 ngày qua (Toàn bộ)": 90
}
selected_days = days_map.get(time_filter, 30)

# Hàm filter trades
def filter_trades(raw_trades, days, prod_sel, res_sel):
    res = backtest_engine.compute_metrics(raw_trades, days_filter=days)
    filtered = res["filtered_trades"]
    
    if "ZWAZ26" in prod_sel:
        filtered = [t for t in filtered if t["commodity"] == "ZW"]
    elif "ZCEZ26" in prod_sel:
        filtered = [t for t in filtered if t["commodity"] == "ZC"]
        
    if res_sel == "Lệnh Thắng (TP)":
        filtered = [t for t in filtered if t["result"] in ["TP1", "TP2", "TP3"]]
    elif res_sel == "Hòa Vốn (ENTRY)":
        filtered = [t for t in filtered if t["result"] == "ENTRY"]
    elif res_sel == "Thua Lỗ (SL)":
        filtered = [t for t in filtered if t["result"] == "SL"]
    elif res_sel == "Chưa Khớp":
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
<div class='kpi-sub'>{metrics['win_trades']} thắng / {metrics['closed_trades']} lệnh đóng</div>
</div>
<div class='kpi-card'>
<div class='kpi-title'>Vốn Khuyến Nghị</div>
<div class='kpi-value-white'>10k USD</div>
<div class='kpi-sub'>ROI: <b>{roi:+.1f}%</b> | Max DD: <b>${max_dd:,.0f}</b></div>
</div>
<div class='kpi-card'>
<div class='kpi-title'>Tổng tín hiệu</div>
<div class='kpi-value-white'>{total_signals}</div>
<div class='kpi-sub'>Gồm {metrics['win_trades']} TP • {metrics['breakeven_trades']} Hòa • {metrics['loss_trades']} SL</div>
</div>
</div>
"""
    st.markdown(clean_html(html), unsafe_allow_html=True)


# ── HÀM HIỂN THỊ BẢNG TÍN HIỆU ──────────────────────────────────────────────
def render_trade_table(trades):
    if not trades:
        st.info("Không có tín hiệu nào phù hợp với bộ lọc hiện tại.")
        return
        
    rows = []
    for t in trades:
        side_badge = "<span class='badge-sell'>Bán</span>" if t["side"] == "BÁN" else "<span class='badge-buy'>Mua</span>"
        
        res = t["result"]
        if res == "TP3":
            res_badge = "<span class='badge-res-tp3'>TP3</span>"
        elif res == "TP2":
            res_badge = "<span class='badge-res-tp2'>TP2</span>"
        elif res == "TP1":
            res_badge = "<span class='badge-res-tp1'>TP1</span>"
        elif res == "ENTRY":
            res_badge = "<span class='badge-res-entry'>ENTRY</span>"
        elif res == "SL":
            res_badge = "<span class='badge-res-sl'>SL</span>"
        else:
            res_badge = "<span class='badge-res-pending'>CHƯA KHỚP</span>"
            
        entry_str = f"{t['entry_price']:.2f}" if t.get("entry_price") else "-"
        exit_str = f"{t['exit_price']:.2f}" if t.get("exit_price") else "-"
        
        pnl = t["pnl"]
        if pnl > 0:
            pnl_html = f"<b style='color:#10b981;'>+${pnl:,.0f}</b>"
        elif pnl < 0:
            pnl_html = f"<b style='color:#ef4444;'>-${abs(pnl):,.0f}</b>"
        else:
            pnl_html = "<span style='color:#9ca3af;'>$0</span>"
            
        row = (
            f"<tr>"
            f"<td style='color:#9ca3af; font-family:monospace;'>{t['date']}</td>"
            f"<td>{side_badge}</td>"
            f"<td><b style='color:#f3f4f6;'>{t['product']}</b></td>"
            f"<td>{res_badge}</td>"
            f"<td style='font-family:monospace; font-weight:600;'>{entry_str}</td>"
            f"<td style='font-family:monospace; font-weight:600;'>{exit_str}</td>"
            f"<td style='text-align:center; font-family:monospace; color:#cbd5e1;'>50</td>"
            f"<td style='font-family:monospace; text-align:right;'>{pnl_html}</td>"
            f"</tr>"
        )
        rows.append(row)
        
    tbody = "".join(rows)
    table_html = (
        f"<table class='custom-table'>"
        f"<thead><tr>"
        f"<th>Ngày</th><th>Vị thế</th><th>Sản phẩm</th><th>Kết quả</th>"
        f"<th>Giá vào</th><th>Giá đóng</th><th style='text-align:center;'>Chênh lệch</th><th style='text-align:right;'>Lợi nhuận</th>"
        f"</tr></thead>"
        f"<tbody>{tbody}</tbody>"
        f"</table>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


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
    dates.append(sorted_trades[0]["date"])
    
    for t in sorted_trades:
        cur += t["pnl"]
        dates.append(t["date"])
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


# ── NỘI DUNG 2 PHƯƠNG PHÁP & SO SÁNH ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📈 Phương Pháp 1: ICT MSS + Pullback EMA",
    "🎯 Phương Pháp 2: FVG + Bắt Đáy / Đỉnh SMC",
    "⚔️ So Sánh Hiệu Quả Đối Đầu (Head-to-Head)"
])

m1_raw = data.get("method_1", {}).get("trades", [])
m2_raw = data.get("method_2", {}).get("trades", [])

m1_trades, m1_metrics = filter_trades(m1_raw, selected_days, product_filter, result_filter)
m2_trades, m2_metrics = filter_trades(m2_raw, selected_days, product_filter, result_filter)

# ── TAB 1 ───────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(clean_html("""
    <div style='background:#111827; border-left:4px solid #38bdf8; padding:12px 16px; border-radius:6px; margin-bottom:16px;'>
    <b style='color:#38bdf8; font-size:14px;'>💎 Nguyên Lý Giao Dịch:</b>
    <span style='color:#cbd5e1; font-size:13px;'>
    Thuận xu hướng cấu trúc thị trường (Trend-Following). Sau khi xuất hiện <b>Market Structure Shift (MSS)</b> phá vỡ Swing Point, 
    hệ thống kiên nhẫn chờ giá hồi (Pullback) về dải <b>EMA 21 - 50</b> để kích hoạt lệnh. SL đặt sau Swing/ATR, chốt lời đa tầng <b>TP1 (1R) dời hòa vốn, TP2 (1.5R), TP3 (2R)</b>.
    </span>
    </div>
    """), unsafe_allow_html=True)
    
    render_kpi_cards(m1_metrics, time_filter)
    
    st.markdown(f"<div style='font-size:14px; color:#9ca3af; margin-bottom:8px;'>Hiển thị <b>1–{len(m1_trades)}</b> trên <b>{len(m1_trades)}</b> tín hiệu</div>", unsafe_allow_html=True)
    render_trade_table(m1_trades)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    render_equity_chart(m1_trades, "Phương Pháp 1 (ICT Trend Pullback)")

# ── TAB 2 ───────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(clean_html("""
    <div style='background:#111827; border-left:4px solid #f59e0b; padding:12px 16px; border-radius:6px; margin-bottom:16px;'>
    <b style='color:#f59e0b; font-size:14px;'>🎯 Nguyên Lý Giao Dịch:</b>
    <span style='color:#cbd5e1; font-size:13px;'>
    Đảo chiều vùng cực trị (Contrarian Reversal). Phát hiện các cụm nến <b>Bắt Đáy / Bắt Đỉnh SMC Zone đạt chuẩn 5 sao (Điểm số >= 5/8)</b> 
    kết hợp quét thanh khoản (BSL/SSL Liquidity Sweep), RSI quá mua/quá bán và khối mất cân bằng giá (FVG). Vào lệnh ngay tại nến xác nhận đảo chiều.
    </span>
    </div>
    """), unsafe_allow_html=True)
    
    render_kpi_cards(m2_metrics, time_filter)
    
    st.markdown(f"<div style='font-size:14px; color:#9ca3af; margin-bottom:8px;'>Hiển thị <b>1–{len(m2_trades)}</b> trên <b>{len(m2_trades)}</b> tín hiệu</div>", unsafe_allow_html=True)
    render_trade_table(m2_trades)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    render_equity_chart(m2_trades, "Phương Pháp 2 (SMC Zone Reversal)")

# ── TAB 3: SO SÁNH ĐỐI ĐẦU ──────────────────────────────────────────────────
with tab3:
    st.markdown(clean_html(f"""
    <div style='font-size:18px; font-weight:800; color:#f8fafc; margin-bottom:4px;'>
    ⚔️ BẢNG SO SÁNH HIỆU QUẢ ĐỐI ĐẦU ({time_filter.upper()})
    </div>
    <div style='font-size:13px; color:#94a3af; margin-bottom:16px;'>
    Đối chiếu trực tiếp giữa Chiến lược Thuận Xu Hướng (M1) và Chiến lược Đảo Chiều Vùng Cực Trị (M2) trên vốn chuẩn $10,000 USD
    </div>
    """), unsafe_allow_html=True)
    
    m1_pnl_color = "#10b981" if m1_metrics["total_pnl"] >= 0 else "#ef4444"
    m2_pnl_color = "#10b981" if m2_metrics["total_pnl"] >= 0 else "#ef4444"
    
    pending_m1_str = f" • <span style='color:#6b7280;'>({m1_metrics['pending_trades']} Chưa khớp)</span>" if m1_metrics.get("pending_trades") else ""
    
    comp_table = (
        f"<table class='custom-table'>"
        f"<thead><tr>"
        f"<th style='width:30%;'>Chỉ Số Đánh Giá (Metric)</th>"
        f"<th style='width:35%; color:#38bdf8;'>📈 Phương Pháp 1 (ICT Trend Pullback)</th>"
        f"<th style='width:35%; color:#f59e0b;'>🎯 Phương Pháp 2 (SMC Zone Reversal)</th>"
        f"</tr></thead>"
        f"<tbody>"
        f"<tr><td><b>Tổng Lợi Nhuận Ròng (PnL)</b></td><td><b style='color:{m1_pnl_color}; font-size:16px;'>{m1_metrics['total_pnl']:+,} USD</b></td><td><b style='color:{m2_pnl_color}; font-size:16px;'>{m2_metrics['total_pnl']:+,} USD</b></td></tr>"
        f"<tr><td><b>Tỷ Suất Lợi Nhuận (ROI trên 10k)</b></td><td><b style='color:{m1_pnl_color};'>{m1_metrics['roi_pct']:+.1f}%</b></td><td><b style='color:{m2_pnl_color};'>{m2_metrics['roi_pct']:+.1f}%</b></td></tr>"
        f"<tr><td><b>Tỷ Lệ Thắng (Win Rate)</b></td><td><b style='font-size:15px; color:#f8fafc;'>{m1_metrics['win_rate']:.1f}%</b></td><td><b style='font-size:15px; color:#f8fafc;'>{m2_metrics['win_rate']:.1f}%</b></td></tr>"
        f"<tr><td><b>Hệ Số Lợi Nhuận (Profit Factor)</b></td><td><b>{m1_metrics['profit_factor']}</b></td><td><b>{m2_metrics['profit_factor']}</b></td></tr>"
        f"<tr><td><b>Mức Sụt Giảm Tối Đa (Max Drawdown)</b></td><td style='color:#f87171;'>-${m1_metrics['max_drawdown']:,.0f}</td><td style='color:#f87171;'>-${m2_metrics['max_drawdown']:,.0f}</td></tr>"
        f"<tr><td><b>Tổng Số Lệnh Phát Tín Hiệu</b></td><td>{m1_metrics['total_trades']} tín hiệu</td><td>{m2_metrics['total_trades']} tín hiệu</td></tr>"
        f"<tr><td><b>Cơ Cấu Lệnh (Thắng / Hòa / Thua)</b></td>"
        f"<td><span style='color:#10b981;'>{m1_metrics['win_trades']} TP</span> • <span style='color:#9ca3af;'>{m1_metrics['breakeven_trades']} Hòa</span> • <span style='color:#ef4444;'>{m1_metrics['loss_trades']} SL</span>{pending_m1_str}</td>"
        f"<td><span style='color:#10b981;'>{m2_metrics['win_trades']} TP</span> • <span style='color:#9ca3af;'>{m2_metrics['breakeven_trades']} Hòa</span> • <span style='color:#ef4444;'>{m2_metrics['loss_trades']} SL</span></td></tr>"
        f"<tr><td><b>Phong Cách Giao Dịch Phù Hợp</b></td><td style='color:#93c5fd;'>Swing / Trend Trading (Ăn sóng dài, tỷ lệ R:R cao)</td><td style='color:#fde68a;'>Contrarian / Scalping (Bắt đảo chiều nhanh, chốt sớm)</td></tr>"
        f"</tbody></table>"
    )
    st.markdown(comp_table, unsafe_allow_html=True)
    
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    st.markdown(clean_html("""
    <div style='background:#111827; border:1px solid #1f2937; border-radius:8px; padding:16px 20px;'>
    <div style='font-size:15px; font-weight:700; color:#f8fafc; margin-bottom:8px;'>💡 KẾT LUẬN & KHUYẾN NGHỊ TỐI ƯU HÓA:</div>
    <ul style='color:#cbd5e1; font-size:13px; line-height:1.7; margin:0; padding-left:20px;'>
    <li><b>Phương Pháp 1 (Trend Pullback):</b> Đạt hiệu quả cao nhất khi thị trường Nông sản vào mùa vụ có xu hướng rõ ràng (ví dụ chu kỳ giảm thu hoạch của Ngô hoặc tin tức chiến tranh Biển Đen của Lúa Mì). Điểm mạnh là bảo toàn vốn rất tốt nhờ cơ chế dời SL hòa vốn sau khi đạt TP1.</li>
    <li><b>Phương Pháp 2 (SMC Zone Reversal):</b> Hoạt động cực kỳ hiệu quả trong các giai đoạn thị trường tích lũy (Sideway) hoặc sau những cú xả quá đà (Sell Climax). Tỷ lệ thắng thường cao hơn ở các nhịp hồi ngắn hạn.</li>
    <li><b>Chiến Lược Hybrid (Khuyến Nghị):</b> Kết hợp cả 2 — <i>Chỉ kích hoạt Phương Pháp 2 (Bắt Đáy) khi Phương Pháp 1 đã hoàn thành sóng xả và có tín hiệu hấp thụ cung; Ngược lại, đi lệnh đầy đủ volume theo Phương Pháp 1 khi xu hướng chính đã được xác nhận.</i></li>
    </ul>
    </div>
    """), unsafe_allow_html=True)
