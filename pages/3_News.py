"""
pages/3_News.py — Bảng Tin Tức & Cung Cầu
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Tin Tức — CBOT", page_icon="📰", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

@st.cache_data(ttl=60)
def load_json(fname):
    p = DATA_OUTPUT / fname
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 220px !important; max-width: 220px !important; width: 220px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.section-header { font-size:15px; font-weight:800; color:#e2e8f0; margin:20px 0 12px 0; letter-spacing:0.5px; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th { background:#0f1629; color:#94a3b8; padding:10px 12px; text-align:left; font-weight:600;
     font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #2a3a5c; }
td { padding:10px 12px; color:#cbd5e1; border-bottom:1px solid #1e2d45; vertical-align:top; }
tr:hover td { background:#1e2d45; }
.curr { color:#22c55e; font-weight:700; }
.prev { color:#94a3b8; }
.bull { background:#14532d; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.bear { background:#7f1d1d; color:#f87171; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
</style>""", unsafe_allow_html=True)

st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Tin Tức & Cung Cầu")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Nông Sản")
    st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

st.markdown("## 📰 Tin Tức, Cung Cầu & Xuất Khẩu")

fund = load_json("fundamental_data.json")
acreage_data = load_json("acreage_data.json")

# ── Xuất Khẩu ────────────────────────────────────────────────────────────────
zc_exp = fund.get("ZC", {}).get("exports", {}) if fund else {}
ts = zc_exp.get("latest_date", "—") if isinstance(zc_exp, dict) else "—"
ts_html = f"<span style='font-size:11px; color:#64748b; font-weight:400; float:right; margin-top:4px;'>Cập nhật: {ts}</span>"
st.markdown(f"<div class='section-header'>🚢 Báo Cáo Xuất Khẩu (Export Sales) {ts_html}</div>", unsafe_allow_html=True)

export_sales = fund.get("export_sales", {}) if fund else {}
curr_week = export_sales.get("week_ending", "—") if export_sales else "—"
prev_week = export_sales.get("previous_week_ending", "—") if export_sales else "—"

if fund:
    cols2 = st.columns(2)
    for i, (code, name) in enumerate([("ZC", "🌽 Ngô"), ("ZW", "🌾 Lúa Mì")]):
        d = fund.get(code, {}).get("exports", {})
        with cols2[i]:
            if d:
                curr = d.get("latest", "N/A")
                prev = d.get("previous", "N/A")
                pct = d.get("pct_change", 0) or 0
                logic = d.get("logic", "")
                bias = "bull" if pct > 5 else ("bear" if pct < -5 else "")
                badge = f'<span class="{bias}">' + ("▲ BULL" if bias == "bull" else "▼ BEAR" if bias == "bear" else "—") + '</span>' if bias else "—"
                st.markdown(f"""
                <div class='card'>
                <div style='font-size:14px; font-weight:700; color:#e2e8f0;'>{name}</div>
                <div style='display:flex; justify-content:space-between; margin-top:8px;'>
                    <span class='prev'>Kỳ trước: {prev}</span>
                    <span class='curr'>{curr}</span>
                </div>
                <div style='margin-top:8px;'>{badge} &nbsp; {f'<span style="color:#22c55e;">+{pct:.1f}%</span>' if pct > 0 else f'<span style="color:#ef4444;">{pct:.1f}%</span>'}</div>
                <div style='font-size:11px; color:#64748b; margin-top:8px;'>{logic[:100]}...</div>
                </div>""", unsafe_allow_html=True)


# ── USDA Cung Cầu ──────────────────────────────────────────────────────────────
st.markdown(f"<div class='section-header'>📊 Cung Cầu Mùa Vụ (USDA Crop Progress)</div>", unsafe_allow_html=True)

USDA_METRICS = [
    ("planting_progress", "Tiến độ gieo trồng"),
    ("harvest_progress", "Tiến độ thu hoạch"),
    ("crop_condition", "Chất lượng (Good/Exc)"),
]

if fund:
    cols2 = st.columns(2)
    for i, (code, name, emoji) in enumerate([("ZC", "Ngô", "🌽"), ("ZW", "Lúa Mì", "🌾")]):
        d = fund.get(code, {})
        with cols2[i]:
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:700; color:#e2e8f0; margin-bottom:12px; font-size:14px;'>{emoji} {name}</div>", unsafe_allow_html=True)
            for metric_key, metric_label in USDA_METRICS:
                meta = d.get(metric_key, {})
                if not meta: continue
                curr = meta.get("latest", "—")
                prev = meta.get("previous", "—")
                curr_dt = meta.get("latest_date", "")
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:6px;'>
                    <span style='color:#cbd5e1; font-size:13px;'>{metric_label}</span>
                    <div style='text-align:right;'>
                        <div style='font-size:13px;'><span class='prev'>{prev}</span> ➔ <span class='curr'>{curr}</span></div>
                        <div style='font-size:10px; color:#475569;'>{curr_dt}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"</div>", unsafe_allow_html=True)


# ── WASDE Tồn Kho ──────────────────────────────────────────────────────────────
wasde_month = fund.get("ZC", {}).get("wasde", {}).get("month", "—") if fund else "—"
st.markdown(f"<div class='section-header'>🏛️ WASDE — Tồn Kho & Cân Đối Cung Cầu</div>", unsafe_allow_html=True)
st.markdown(f"""
<div style='font-size:12px; color:#64748b; margin-bottom:10px;'>Báo cáo WASDE tháng: <b style='color:#e2e8f0;'>{wasde_month} 2026</b></div>""",
unsafe_allow_html=True)

if fund:
    cols2 = st.columns(2)
    for i, (code, name, emoji) in enumerate([("ZC", "Ngô", "🌽"), ("ZW", "Lúa Mì", "🌾")]):
        d = fund.get(code, {})
        with cols2[i]:
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:700; color:#e2e8f0; margin-bottom:12px; font-size:14px;'>{emoji} {name}</div>", unsafe_allow_html=True)
            for metric_key, metric_label in [("us_ending_stocks", "Tồn Kho Mỹ"), ("global_ending_stocks", "Tồn Kho TG")]:
                meta = d.get(metric_key, {})
                if not meta: continue
                curr = meta.get("current", meta.get("latest", "—"))
                prev = meta.get("previous", "—")
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid #1e2d45; padding-bottom:6px;'>
                    <span style='color:#cbd5e1; font-size:13px;'>{metric_label}</span>
                    <div style='text-align:right;'>
                        <div style='font-size:13px;'><span class='prev'>{prev}</span> ➔ <span class='curr'>{curr}</span></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown(f"</div>", unsafe_allow_html=True)

# ── Diện Tích Gieo Trồng (Acreage) ─────────────────────────────────────────────
if acreage_data:
    st.markdown(f"<div class='section-header'>🌱 Diện Tích Gieo Trồng (NASS Planted Acreage)</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-size:12px; color:#64748b; margin-bottom:10px;'>
        Nguồn: <b style='color:#e2e8f0;'>USDA NASS</b> | Cập nhật: {acreage_data.get('fetched_at', '—')}
    </div>""", unsafe_allow_html=True)

    import plotly.graph_objects as go
    
    commodities = acreage_data.get("commodities", {})
    if commodities:
        # 1. Summary Cards
        cols3 = st.columns(3)
        for i, sym in enumerate(["ZC", "ZS", "ZW"]):
            if sym in commodities:
                d = commodities[sym]
                with cols3[i]:
                    st.markdown(f"""
                    <div class='card' style='text-align:center;'>
                        <div style='font-weight:700; color:#94a3b8; font-size:13px;'>{d.get('name')}</div>
                        <div style='font-size:24px; font-weight:800; color:#e2e8f0; margin:4px 0;'>{d.get('latest_planted_mln_acres', 0):.1f}<span style='font-size:14px; color:#64748b;'>M ac</span></div>
                        <div style='font-size:12px; color:{"#4ade80" if d.get('yoy_delta_mln_acres',0) < 0 else ("#f87171" if d.get('yoy_delta_mln_acres',0) > 0 else "#94a3b8")};'>
                            {d.get('yoy_direction')} {abs(d.get('yoy_delta_mln_acres', 0)):.1f}M ({d.get('yoy_pct', 0):+.1f}%)
                        </div>
                        <div style='font-size:11px; margin-top:8px; padding-top:8px; border-top:1px solid #1e2d45;'>
                            {d.get('signal')}
                        </div>
                    </div>""", unsafe_allow_html=True)

        # 2. History Chart
        fig = go.Figure()
        colors = {"ZC": "#facc15", "ZW": "#d97706", "ZS": "#4ade80"}
        for sym in ["ZC", "ZS", "ZW"]:
            if sym in commodities:
                d = commodities[sym]
                hist = d.get("history", [])
                if hist:
                    x = [h["year"] for h in hist]
                    y = [h["planted_mln_acres"] for h in hist]
                    fig.add_trace(go.Scatter(
                        x=x, y=y, mode="lines+markers", name=d.get("name"),
                        line=dict(color=colors[sym], width=2),
                        marker=dict(size=6)
                    ))
        
        fig.update_layout(
            title="Biểu Đồ Lịch Sử Diện Tích Gieo Trồng (2015-Nay)",
            title_font=dict(size=14, color="#e2e8f0"),
            paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
            font=dict(color="#cbd5e1"),
            xaxis=dict(showgrid=False, linecolor="#334155"),
            yaxis=dict(title="Triệu Mẫu Anh (M acres)", gridcolor="#1e2d45"),
            margin=dict(l=40, r=20, t=40, b=20),
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 3. Lịch báo cáo sắp tới
    next_rep = acreage_data.get("next_report")
    if next_rep:
        st.markdown(f"""
        <div class='card' style='background:rgba(59,130,246,0.1); border-color:#3b82f6;'>
            <div style='font-size:13px; color:#93c5fd; font-weight:700;'>📅 BÁO CÁO SẮP TỚI: {next_rep.get('name')}</div>
            <div style='font-size:15px; color:#e2e8f0; font-weight:700; margin:4px 0;'>Thời gian: {next_rep.get('publish_vn')}</div>
            <div style='font-size:13px; color:#cbd5e1;'>{next_rep.get('description')}</div>
            <div style='font-size:13px; color:#f87171; font-weight:600; margin-top:4px;'>⚠️ {next_rep.get('impact')}</div>
        </div>""", unsafe_allow_html=True)
