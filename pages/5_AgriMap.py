"""
pages/5_AgriMap.py  – Bản Đồ Nông Sản Tương Tác
=================================================
Tab 1 – Thời tiết hiện tại (3 ngày): weather_short.json
Tab 2 – Dự báo dài hạn (ENSO):      weather_long.json
- Bản đồ Mỹ: 9 bang Lúa mì (viền nâu) + 9 bang Ngô (viền vàng)
- Bản đồ Thế giới: 6 quốc gia đối thủ
- Màu fill = mức độ rủi ro thời tiết (đỏ/vàng/xanh)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Bản Đồ Nông Sản – CBOT", page_icon="🗺️", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.map-card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 14px;
            padding: 20px; margin-bottom: 20px; }
.map-title { font-size: 15px; font-weight: 800; color: #94a3b8; letter-spacing: 1px;
             text-transform: uppercase; border-bottom: 1px solid #2a3a5c;
             padding-bottom: 10px; margin-bottom: 16px; }
.enso-badge { display:inline-block; padding:4px 14px; border-radius:20px;
              font-size:13px; font-weight:700; margin-bottom:14px; }
</style>""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

if st.sidebar.button("🔄 Làm mới Bản đồ", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ─── LOAD DỮ LIỆU ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_weather_short():
    p = DATA_OUTPUT / "weather_short.json"
    if not p.exists(): return {}
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

@st.cache_data(ttl=120)
def load_weather_long():
    p = DATA_OUTPUT / "weather_long.json"
    if not p.exists(): return {}
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def risk_to_score(risk: str) -> float:
    r = (risk or "").lower()
    if any(k in r for k in ["kho","han","hot","dry","nong","nang","ngap","lu","heavy","flood"]):
        return 0.0
    if any(k in r for k in ["thuan loi","favorable","tot","good"]):
        return 2.0
    return 1.0

def risk_label(risk: str) -> str:
    r = (risk or "").lower()
    if any(k in r for k in ["ngap","lu","heavy","flood"]): return "🔴 Ngập úng"
    if any(k in r for k in ["kho","han","hot","dry","nong","nang"]): return "🔴 Khô hạn/Nóng"
    if any(k in r for k in ["thuan loi","favorable"]): return "🟢 Thuận lợi"
    return "🟡 Bình thường"

# Colorscale riêng cho từng loại cây (phân biệt màu nền)
# Lúa mì: nâu nhạt-vàng-đỏ → dải màu ấm (warm/brown tones)
WHEAT_CS = [[0.0, "#b45309"], [0.5, "#d97706"], [1.0, "#fef3c7"]]
# Ngô:    vàng-xanh-đỏ → dải màu lạnh (cool/yellow-green tones)
CORN_CS  = [[0.0, "#dc2626"], [0.5, "#ca8a04"], [1.0, "#d9f99d"]]
# Thế giới (chung): đỏ-vàng-xanh
WORLD_CS = [[0.0, "#ef4444"], [0.5, "#eab308"], [1.0, "#22c55e"]]

def make_us_fig(regions: dict) -> go.Figure:
    """Tạo choropleth bản đồ Mỹ với 9 bang lúa mì (nâu) + 9 bang ngô (vàng)."""

    US_WINTER_WHEAT = {
        "KS": ("Kansas",       "🌾 Lúa mì HRW (Đông)",     "US_Wheat_Kansas"),
        "OK": ("Oklahoma",     "🌾 Lúa mì HRW (Đông)",     "US_Wheat_Oklahoma"),
        "TX": ("Texas",        "🌾 South Plains (Đông)",   "US_Wheat_Texas"),
        "CO": ("Colorado",     "🌾 Lúa mì HRW (Đông)",     "US_Wheat_Colorado"),
        "WA": ("Washington",   "🌾 Lúa mì SW (Đông)",      "US_Wheat_Washington"),
        "ID": ("Idaho",        "🌾 Lúa mì SW+HRW (Đông)",  "US_Wheat_Idaho"),
    }
    US_SPRING_WHEAT = {
        "ND": ("N. Dakota",    "🌾 Lúa mì Xuân (Spring/Durum)","US_Wheat_NorthDakota"),
        "SD": ("S. Dakota",    "🌾 Lúa mì Xuân (Spring/Durum)","US_Wheat_SouthDakota"),
        "MT": ("Montana",      "🌾 Lúa mì Xuân (HRS)","US_Wheat_Montana"),
    }
    US_CORN_META = {
        "IA": ("Iowa",      "🌽 Ngô + Đậu tương",  "US_Corn_Iowa"),
        "IL": ("Illinois",  "🌽 Ngô + Đậu tương",  "US_Corn_Illinois"),
        "NE": ("Nebraska",  "🌽 Ngô (Feedlot)",    "US_Corn_Nebraska"),
        "MN": ("Minnesota", "🌽 Ngô + Đậu tương",  "US_Corn_Minnesota"),
        "IN": ("Indiana",   "🌽 Ngô + Đậu tương",  "US_Corn_Indiana"),
        "OH": ("Ohio",      "🌽 Ngô + Đậu tương",  "US_Corn_Ohio"),
        "WI": ("Wisconsin", "🌽 Ngô Sữa",           "US_Corn_Wisconsin"),
        "MO": ("Missouri",  "🌽 Ngô + Đậu tương",  "US_Corn_Missouri"),
        "MI": ("Michigan",  "🌽 Ngô + Đậu tương",  "US_Corn_Michigan"),
    }

    # Tọa độ tâm bang để hiển thị label text
    STATE_CENTERS = {
        "KS":(38.5,-98.4), "MT":(47.0,-110.0), "WA":(47.4,-120.6), "OK":(35.6,-97.5),
        "ND":(47.5,-100.5),"TX":(31.5,-99.5),  "SD":(44.5,-100.3), "CO":(39.0,-105.5),
        "ID":(44.0,-114.5),"IA":(42.0,-93.5),  "IL":(40.0,-89.2),  "NE":(41.5,-99.9),
        "MN":(46.4,-94.0), "IN":(40.3,-86.1),  "OH":(40.4,-82.9),  "WI":(44.5,-90.0),
        "MO":(38.5,-92.5), "MI":(44.0,-85.0),
    }

    def make_hover(name, crop, rk):
        r = regions.get(rk, {})
        risk = r.get("risk_assessment", "—")
        return (f"<b>{name}</b><br>{crop}<br>"
                f"Mưa 3 ngày: {r.get('total_3d_rain_mm','—')} mm<br>"
                f"Max nhiệt độ: {r.get('max_temp_C','—')}°C<br>"
                f"Đánh giá: {risk_label(risk)}")

    fig = go.Figure()

    # Nền tất cả bang – màu tối trung tính
    all_states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
                  "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
                  "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
                  "TX","UT","VT","VA","WA","WV","WI","WY"]
    fig.add_trace(go.Choropleth(
        locations=all_states, z=[0]*len(all_states),
        locationmode="USA-states",
        colorscale=[[0,"#1e293b"],[1,"#1e293b"]],
        showscale=False, hoverinfo="skip",
        marker_line_color="#334155", marker_line_width=0.8,
    ))

    # Lớp Lúa mì Đông (Winter Wheat)
    w_w_codes  = list(US_WINTER_WHEAT.keys())
    w_w_scores = [risk_to_score(regions.get(US_WINTER_WHEAT[c][2],{}).get("risk_assessment","")) for c in w_w_codes]
    w_w_hover  = [make_hover(*US_WINTER_WHEAT[c]) for c in w_w_codes]
    fig.add_trace(go.Choropleth(
        locations=w_w_codes, z=w_w_scores,
        locationmode="USA-states",
        colorscale=WHEAT_CS, zmin=0, zmax=2,
        showscale=False,
        hovertemplate="%{customdata}<extra></extra>", customdata=w_w_hover,
        marker_line_color="#7f1d1d", marker_line_width=2.5,   # viền đỏ sẫm
        name="🌾 Lúa mì Đông",
    ))

    # Lớp Lúa mì Xuân (Spring Wheat)
    s_w_codes  = list(US_SPRING_WHEAT.keys())
    s_w_scores = [risk_to_score(regions.get(US_SPRING_WHEAT[c][2],{}).get("risk_assessment","")) for c in s_w_codes]
    s_w_hover  = [make_hover(*US_SPRING_WHEAT[c]) for c in s_w_codes]
    fig.add_trace(go.Choropleth(
        locations=s_w_codes, z=s_w_scores,
        locationmode="USA-states",
        colorscale=WHEAT_CS, zmin=0, zmax=2,
        showscale=False,
        hovertemplate="%{customdata}<extra></extra>", customdata=s_w_hover,
        marker_line_color="#0ea5e9", marker_line_width=2.5,   # viền xanh dương
        name="🌾 Lúa mì Xuân",
    ))

    # Lớp Ngô – dải màu vàng-xanh ngô (CORN_CS)
    c_codes  = list(US_CORN_META.keys())
    c_scores = [risk_to_score(regions.get(US_CORN_META[c][2],{}).get("risk_assessment","")) for c in c_codes]
    c_hover  = [make_hover(*US_CORN_META[c]) for c in c_codes]
    fig.add_trace(go.Choropleth(
        locations=c_codes, z=c_scores,
        locationmode="USA-states",
        colorscale=CORN_CS, zmin=0, zmax=2,
        showscale=False,
        hovertemplate="%{customdata}<extra></extra>", customdata=c_hover,
        marker_line_color="#4ade80", marker_line_width=2.5,   # viền xanh lá ngô
        name="🌽 Ngô",
    ))

    # Labels tên bang
    lats = [STATE_CENTERS[c][0] for c in STATE_CENTERS]
    lons = [STATE_CENTERS[c][1] for c in STATE_CENTERS]
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons, text=list(STATE_CENTERS.keys()), mode="text",
        textfont=dict(size=10, color="#ffffff", family="Inter"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        geo=dict(scope="usa", showland=True, landcolor="#0f1629",
                 showlakes=True, lakecolor="#1a2035",
                 showcoastlines=True, coastlinecolor="#334155",
                 showframe=False, bgcolor="#0f1629",
                 projection_type="albers usa"),
        paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
        margin=dict(l=0,r=0,t=10,b=0), height=460, showlegend=False,
    )
    return fig


def make_world_fig(regions: dict) -> go.Figure:
    """Bản đồ thế giới – 6 quốc gia đối thủ, màu theo rủi ro thời tiết."""
    WORLD_META = {
        "RUS": ("Nga",        "🌾 Lúa mì XK #1",       "Russia_Rostov"),
        "UKR": ("Ukraine",    "🌾🌽 Lúa mì + Ngô",     "Ukraine_Poltava"),
        "BRA": ("Brazil",     "🌱🌽 Đậu tương + Ngô",  "Brazil_MatoGrosso"),
        "ARG": ("Argentina",  "🌾🌽 Lúa mì + Ngô",     "Argentina_Pampas"),
        "AUS": ("Úc",         "🌾 Lúa mì",              "Australia_NSW"),
        "FRA": ("Pháp/EU",    "🌾 Lúa mì EU XK #2",    "EU_France_Centre"),
    }
    isos   = list(WORLD_META.keys())
    scores = [risk_to_score(regions.get(WORLD_META[i][2],{}).get("risk_assessment","")) for i in isos]
    hover  = []
    for iso, (name, crop, rk) in WORLD_META.items():
        r = regions.get(rk, {})
        hover.append(
            f"<b>{name}</b><br>{crop}<br>"
            f"Mưa 3 ngày: {r.get('total_3d_rain_mm','—')} mm<br>"
            f"Max nhiệt độ: {r.get('max_temp_C','—')}°C<br>"
            f"Đánh giá: {risk_label(r.get('risk_assessment',''))}"
        )

    fig = go.Figure(go.Choropleth(
        locations=isos, z=scores, locationmode="ISO-3",
        colorscale=WORLD_CS, zmin=0, zmax=2,
        showscale=False,
        hovertemplate="%{customdata}<extra></extra>", customdata=hover,
        marker_line_color="#64748b", marker_line_width=1.5,
    ))
    fig.update_layout(
        geo=dict(showland=True, landcolor="#1e293b",
                 showocean=True, oceancolor="#0f1629",
                 showlakes=True, lakecolor="#0f1629",
                 showcoastlines=True, coastlinecolor="#334155",
                 showframe=False, bgcolor="#0f1629",
                 projection_type="natural earth"),
        paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
        margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False,
    )
    return fig


def make_enso_world_fig(impacts: list) -> go.Figure:
    """Bản đồ ENSO: tô màu quốc gia theo tín hiệu Bullish/Bearish."""
    # Ánh xạ region ENSO → ISO codes + màu
    ENSO_MAP = {
        "chau uc": (["AUS"],        "Úc"),
        "australia": (["AUS"],      "Úc"),
        "nam my": (["ARG","BRA"],   "Nam Mỹ"),
        "argentina": (["ARG"],      "Argentina"),
        "brazil": (["BRA"],         "Brazil"),
        "bac my": (["USA"],         "Bắc Mỹ"),
        "us plains": (["USA"],      "Mỹ"),
        "ukraine": (["UKR"],        "Ukraine"),
        "nga": (["RUS"],            "Nga"),
        "russia": (["RUS"],         "Nga"),
        "chau au": (["DEU","FRA","POL"], "Châu Âu"),
        "eu": (["DEU","FRA","POL"],  "EU"),
        "an do": (["IND"],           "Ấn Độ"),
        "india": (["IND"],           "Ấn Độ"),
        "dong nam a": (["VNM","THA","IDN","PHL"], "Đông Nam Á"),
        "southeast asia": (["VNM","THA","IDN","PHL"], "Đông Nam Á"),
    }

    iso_scores = {}  # iso → score (0=bullish giá, 2=bearish giá)
    iso_labels = {}

    for impact in impacts:
        region_text = impact.get("region","").lower()
        bias = impact.get("bias","").upper()
        effect = impact.get("effect","")
        crop   = impact.get("crop","")
        severity = impact.get("severity","")
        score = 0.0 if "BULLISH" in bias else (2.0 if "BEARISH" in bias else 1.0)
        color_label = "🔴 BULLISH (Giá tăng)" if "BULLISH" in bias else ("🟢 BEARISH (Giá giảm)" if "BEARISH" in bias else "🟡 Trung tính")

        for key, (isos, friendly) in ENSO_MAP.items():
            if key in region_text:
                for iso in isos:
                    iso_scores[iso] = score
                    iso_labels[iso] = (
                        f"<b>{friendly}</b><br>"
                        f"Cây trồng: {crop}<br>"
                        f"Tín hiệu: {color_label}<br>"
                        f"Mức độ: {severity}<br>"
                        f"Chi tiết: {effect[:80]}..."
                    )

    isos   = list(iso_scores.keys())
    scores = [iso_scores[i] for i in isos]
    hover  = [iso_labels[i] for i in isos]

    # ENSO colorscale: đỏ = BULLISH (thiếu cung → giá tăng), xanh = BEARISH (dư cung → giá giảm)
    ENSO_CS = [[0.0,"#ef4444"],[0.5,"#eab308"],[1.0,"#22c55e"]]

    fig = go.Figure(go.Choropleth(
        locations=isos, z=scores, locationmode="ISO-3",
        colorscale=ENSO_CS, zmin=0, zmax=2,
        showscale=False,
        hovertemplate="%{customdata}<extra></extra>", customdata=hover,
        marker_line_color="#64748b", marker_line_width=1.5,
    ))
    fig.update_layout(
        geo=dict(showland=True, landcolor="#1e293b",
                 showocean=True, oceancolor="#0f1629",
                 showlakes=True, lakecolor="#0f1629",
                 showcoastlines=True, coastlinecolor="#334155",
                 showframe=False, bgcolor="#0f1629",
                 projection_type="natural earth"),
        paper_bgcolor="#1a2035", plot_bgcolor="#1a2035",
        margin=dict(l=0,r=0,t=10,b=0), height=320, showlegend=False,
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════════
ws = load_weather_short()
wl = load_weather_long()
regions_short = ws.get("regions", {})
fetched_at    = ws.get("fetched_at", "—")

# Header
st.markdown(f"""
<div style='margin-bottom:18px;'>
    <div style='font-size:22px; font-weight:800; color:#e2e8f0;'>🗺️ Bản Đồ Nông Sản Thế Giới</div>
    <div style='font-size:12px; color:#64748b; margin-top:4px;'>
        Dữ liệu thời tiết cập nhật lúc: <b style='color:#94a3b8;'>{fetched_at}</b>
        &nbsp;|&nbsp;
        <span style='color:#7f1d1d;'>■</span> Lúa mì Đông (viền đỏ sẫm)
        &nbsp;
        <span style='color:#0ea5e9;'>■</span> Lúa mì Xuân (viền xanh dương)
        &nbsp;
        <span style='color:#4ade80;'>■</span> Vùng Ngô (viền xanh lá)
        &nbsp;|&nbsp;
        <span style='color:#ef4444;'>■</span> Khô hạn
        &nbsp;
        <span style='color:#eab308;'>■</span> Bình thường
        &nbsp;
        <span style='color:#22c55e;'>■</span> Thuận lợi
    </div>
</div>""", unsafe_allow_html=True)

# ─── 2 TABS ───────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🌡️ Thời Tiết Hiện Tại (3 Ngày)", "🌊 Dự Báo Dài Hạn (ENSO)"])

# ═══════════════════════════════════ TAB 1 ════════════════════════════════════
with tab1:

    # Bản đồ Mỹ
    st.markdown("<div class='map-card'>", unsafe_allow_html=True)
    st.markdown("""<div class='map-title'>
        🇺🇸 HOA KỲ — Vùng Trồng Lúa Mì & Ngô
        <span style='font-size:11px; font-weight:400; margin-left:12px;'>
            Màu fill = mức rủi ro thời tiết &nbsp;·&nbsp; Viền đỏ sẫm = Lúa đông &nbsp;·&nbsp; Viền xanh dương = Lúa xuân &nbsp;·&nbsp; Viền xanh lá = Ngô
        </span>
    </div>""", unsafe_allow_html=True)

    fig_us = make_us_fig(regions_short)
    st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})

    # Chú thích màu 2 cây trồng
    st.markdown("""
    <div style='display:flex; gap:30px; flex-wrap:wrap; margin-top:8px; font-size:12px; color:#94a3b8;'>
        <div><span style='color:#7f1d1d; font-size:16px;'>▬</span><span style='color:#0ea5e9; font-size:16px;'>▬</span> <b>Lúa mì (Đông/Xuân):</b>
            <span style='background:#fef3c7; color:#000; padding:2px 7px; border-radius:4px;'>Thuận lợi</span>
            <span style='background:#d97706; color:#fff; padding:2px 7px; border-radius:4px; margin:0 4px;'>Bình thường</span>
            <span style='background:#b45309; color:#fff; padding:2px 7px; border-radius:4px;'>Rủi ro</span>
        </div>
        <div><span style='color:#4ade80; font-size:16px;'>▬</span> <b>Ngô:</b>
            <span style='background:#d9f99d; color:#000; padding:2px 7px; border-radius:4px;'>Thuận lợi</span>
            <span style='background:#ca8a04; color:#fff; padding:2px 7px; border-radius:4px; margin:0 4px;'>Bình thường</span>
            <span style='background:#dc2626; color:#fff; padding:2px 7px; border-radius:4px;'>Rủi ro</span>
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Bản đồ Thế giới
    st.markdown("<div class='map-card'>", unsafe_allow_html=True)
    st.markdown("""<div class='map-title'>
        🌍 QUỐC GIA ĐỐI THỦ — Thời Tiết 3 Ngày
        <span style='font-size:11px; font-weight:400; margin-left:12px;'>
            Di chuột vào nước để xem chi tiết thời tiết
        </span>
    </div>""", unsafe_allow_html=True)
    fig_world = make_world_fig(regions_short)
    st.plotly_chart(fig_world, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # Bảng chi tiết
    st.markdown("<div class='map-card'>", unsafe_allow_html=True)
    st.markdown("<div class='map-title'>📋 Chi Tiết Thời Tiết Ngắn Hạn</div>", unsafe_allow_html=True)
    col_us, col_world = st.columns(2, gap="large")

    US_ALL_META = {
        "KS":("Kansas","🌾","US_Wheat_Kansas"), "MT":("Montana","🌾","US_Wheat_Montana"),
        "WA":("Washington","🌾","US_Wheat_Washington"), "OK":("Oklahoma","🌾","US_Wheat_Oklahoma"),
        "ND":("N.Dakota","🌾","US_Wheat_NorthDakota"), "TX":("Texas","🌾","US_Wheat_Texas"),
        "SD":("S.Dakota","🌾","US_Wheat_SouthDakota"), "CO":("Colorado","🌾","US_Wheat_Colorado"),
        "ID":("Idaho","🌾","US_Wheat_Idaho"),
        "IA":("Iowa","🌽","US_Corn_Iowa"), "IL":("Illinois","🌽","US_Corn_Illinois"),
        "NE":("Nebraska","🌽","US_Corn_Nebraska"), "MN":("Minnesota","🌽","US_Corn_Minnesota"),
        "IN":("Indiana","🌽","US_Corn_Indiana"), "OH":("Ohio","🌽","US_Corn_Ohio"),
        "WI":("Wisconsin","🌽","US_Corn_Wisconsin"), "MO":("Missouri","🌽","US_Corn_Missouri"),
        "MI":("Michigan","🌽","US_Corn_Michigan"),
    }
    with col_us:
        st.markdown("**🇺🇸 Hoa Kỳ**")
        html = """<table style='width:100%;border-collapse:collapse;font-size:11.5px;'>
<tr style='color:#64748b;border-bottom:1px solid #334155;'>
<th style='text-align:left;padding:5px 3px;'>Bang</th>
<th style='text-align:left;padding:5px 3px;'>Cây</th>
<th style='text-align:center;padding:5px 3px;'>Mưa(mm)</th>
<th style='text-align:center;padding:5px 3px;'>°C Max</th>
<th style='text-align:left;padding:5px 3px;'>Đánh Giá</th>
</tr>"""
        for code,(name,icon,rk) in US_ALL_META.items():
            r = regions_short.get(rk,{})
            html += (f"<tr style='border-bottom:1px solid #1e2d45;'>"
                     f"<td style='padding:4px 3px;color:#e2e8f0;font-weight:600;'>{code}</td>"
                     f"<td style='padding:4px 3px;color:#94a3b8;'>{icon}</td>"
                     f"<td style='padding:4px 3px;text-align:center;color:#60a5fa;'>{r.get('total_3d_rain_mm','—')}</td>"
                     f"<td style='padding:4px 3px;text-align:center;color:#f97316;'>{r.get('max_temp_C','—')}</td>"
                     f"<td style='padding:4px 3px;'>{risk_label(r.get('risk_assessment',''))}</td>"
                     f"</tr>")
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

    WORLD_ALL = {
        "RUS":("Nga","Russia_Rostov"), "UKR":("Ukraine","Ukraine_Poltava"),
        "BRA":("Brazil","Brazil_MatoGrosso"), "ARG":("Argentina","Argentina_Pampas"),
        "AUS":("Úc","Australia_NSW"), "FRA":("Pháp/EU","EU_France_Centre"),
    }
    with col_world:
        st.markdown("**🌍 Quốc Tế**")
        html2 = """<table style='width:100%;border-collapse:collapse;font-size:11.5px;'>
<tr style='color:#64748b;border-bottom:1px solid #334155;'>
<th style='text-align:left;padding:5px 3px;'>Quốc Gia</th>
<th style='text-align:center;padding:5px 3px;'>Mưa(mm)</th>
<th style='text-align:center;padding:5px 3px;'>°C Max</th>
<th style='text-align:left;padding:5px 3px;'>Đánh Giá</th>
</tr>"""
        for iso,(name,rk) in WORLD_ALL.items():
            r = regions_short.get(rk,{})
            html2 += (f"<tr style='border-bottom:1px solid #1e2d45;'>"
                      f"<td style='padding:4px 3px;color:#e2e8f0;font-weight:600;'>{name}</td>"
                      f"<td style='padding:4px 3px;text-align:center;color:#60a5fa;'>{r.get('total_3d_rain_mm','—')}</td>"
                      f"<td style='padding:4px 3px;text-align:center;color:#f97316;'>{r.get('max_temp_C','—')}</td>"
                      f"<td style='padding:4px 3px;'>{risk_label(r.get('risk_assessment',''))}</td>"
                      f"</tr>")
        html2 += "</table>"
        st.markdown(html2, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════ TAB 2 ════════════════════════════════════
with tab2:
    enso_status = wl.get("enso_status","—")
    enso_desc   = wl.get("description","—")
    impacts     = wl.get("impacts",[])
    fetched_long= wl.get("fetched_at","—")

    # Dịch lỗi font NiAo
    for bad, good in [("NiA\xc3\xb1o","Niño"),("NiA o","Niño"),("NiAo","Niño"),
                       ("La Ni?a","La Niña"),("chA?u","châu"),("A?c","Úc")]:
        enso_status = enso_status.replace(bad, good)
        enso_desc   = enso_desc.replace(bad, good)

    # Badge màu trạng thái ENSO
    status_lower = enso_status.lower()
    if "el ni" in status_lower:
        badge_color = "#ef4444"; badge_text = "🌡️ El Niño"
    elif "la ni" in status_lower:
        badge_color = "#3b82f6"; badge_text = "❄️ La Niña"
    else:
        badge_color = "#64748b"; badge_text = "⚖️ ENSO Neutral"

    st.markdown(f"""
    <div class='map-card'>
        <div class='map-title'>🌊 TRẠNG THÁI ENSO (Nguồn: NOAA) &nbsp;·&nbsp;
            <span style='font-size:11px; font-weight:400;'>Cập nhật: {fetched_long}</span>
        </div>
        <span class='enso-badge' style='background:{badge_color}20; color:{badge_color}; border:1px solid {badge_color};'>
            {badge_text} — {enso_status}
        </span>
        <p style='font-size:13px; color:#94a3b8; margin:8px 0 0;'>{enso_desc}</p>
    </div>""", unsafe_allow_html=True)

    # Bản đồ ENSO
    if impacts:
        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("""<div class='map-title'>
            🌍 TÁC ĐỘNG ENSO ĐẾN GIÁ NÔNG SẢN
            <span style='font-size:11px;font-weight:400;margin-left:10px;'>
                🔴 BULLISH (Thiếu cung → Giá tăng) &nbsp;·&nbsp; 🟢 BEARISH (Dư cung → Giá giảm)
            </span>
        </div>""", unsafe_allow_html=True)
        fig_enso = make_enso_world_fig(impacts)
        st.plotly_chart(fig_enso, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Bảng tác động ENSO chi tiết
    st.markdown("<div class='map-card'>", unsafe_allow_html=True)
    st.markdown("<div class='map-title'>📋 Phân Tích Tác Động ENSO Chi Tiết</div>", unsafe_allow_html=True)
    if impacts:
        html3 = """<table style='width:100%;border-collapse:collapse;font-size:12px;'>
<tr style='color:#64748b;border-bottom:1px solid #334155;'>
<th style='padding:6px;text-align:left;'>Khu Vực</th>
<th style='padding:6px;text-align:left;'>Cây Trồng</th>
<th style='padding:6px;text-align:center;'>Mức Độ</th>
<th style='padding:6px;text-align:center;'>Tín Hiệu Giá</th>
<th style='padding:6px;text-align:left;'>Tác Động</th>
</tr>"""
        for imp in impacts:
            bias = imp.get("bias","—").upper()
            sev  = imp.get("severity","—")
            if "BULLISH" in bias:
                bias_html = "<span style='color:#ef4444;font-weight:700;'>🔴 BULLISH</span>"
                sev_color = "#ef4444"
            elif "BEARISH" in bias:
                bias_html = "<span style='color:#22c55e;font-weight:700;'>🟢 BEARISH</span>"
                sev_color = "#22c55e"
            else:
                bias_html = "<span style='color:#eab308;font-weight:700;'>🟡 Neutral</span>"
                sev_color = "#eab308"

            region = imp.get("region","—")
            for bad,good in [("ChA?u","Châu"),("A?c","Úc"),("Nam M?1","Nam Mỹ"),
                              ("B?_c M?1","Bắc Mỹ"),("LA?a MA?","Lúa Mì"),("NgA?","Ngô")]:
                region = region.replace(bad,good)

            effect = imp.get("effect","—")
            html3 += (f"<tr style='border-bottom:1px solid #1e2d45;'>"
                      f"<td style='padding:5px 6px;color:#e2e8f0;font-weight:600;'>{region}</td>"
                      f"<td style='padding:5px 6px;color:#94a3b8;'>{imp.get('crop','—')}</td>"
                      f"<td style='padding:5px 6px;text-align:center;color:{sev_color};font-weight:600;'>{sev}</td>"
                      f"<td style='padding:5px 6px;text-align:center;'>{bias_html}</td>"
                      f"<td style='padding:5px 6px;color:#64748b;font-size:11px;'>{effect[:100]}...</td>"
                      f"</tr>")
        html3 += "</table>"
        st.markdown(html3, unsafe_allow_html=True)
    else:
        st.info("Chưa có dữ liệu ENSO. Hãy chạy 'Run All Data' để cập nhật.")
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    pass
