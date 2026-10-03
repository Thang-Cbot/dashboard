"""
pages/4_Weather_Map.py  – Thời Tiết & Bản Đồ Nông Sản (Unified)
=================================================
Tab 1 – Thời tiết ngắn hạn (3 ngày): Bản đồ Mỹ, Thế giới & Bảng tóm tắt
Tab 2 – Dự báo dài hạn (ENSO): Bản đồ ENSO & Tác động Vĩ mô
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Thời Tiết & Bản Đồ – CBOT", page_icon="favicon.png", layout="wide")

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
table { width:100%; border-collapse:collapse; font-size:12px; }
th { background:#0f1629; color:#94a3b8; padding:8px; text-align:left; font-weight:600; border-bottom:1px solid #2a3a5c; }
td { padding:8px; color:#cbd5e1; border-bottom:1px solid #1e2d45; }
tr:hover td { background:#1e2d45; }
</style>""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather_Map.py",label="🌤️ Thời Tiết & Bản Đồ")
st.sidebar.page_link("pages/5_Macro_Matrix.py", label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ")

if st.sidebar.button("🔄 Cập Nhật Data Thời Tiết", use_container_width=True):
    import subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    with st.spinner("Đang lấy data thời tiết ngắn hạn..."):
        subprocess.run([sys.executable, str(Path(__file__).parent.parent / "Data/weather/weather_short.py")], env=env)
    with st.spinner("Đang lấy data ENSO..."):
        subprocess.run([sys.executable, str(Path(__file__).parent.parent / "Data/weather/weather_long.py")], env=env)
    st.cache_data.clear()
    st.rerun()

# ─── LOAD DỮ LIỆU ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_weather_short():
    p = DATA_OUTPUT / "weather_short.json"
    if not p.exists(): return {}
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

@st.cache_data(ttl=120)
def load_weather_long():
    p = DATA_OUTPUT / "weather_long.json"
    if not p.exists(): return {}
    try:
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

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

WHEAT_CS = [[0.0, "#b45309"], [0.5, "#d97706"], [1.0, "#fef3c7"]]
CORN_CS  = [[0.0, "#dc2626"], [0.5, "#ca8a04"], [1.0, "#d9f99d"]]
WORLD_CS = [[0.0, "#ef4444"], [0.5, "#eab308"], [1.0, "#22c55e"]]

def make_us_fig(regions: dict) -> go.Figure:
    US_WINTER_WHEAT = { "KS": "US_Wheat_Kansas", "OK": "US_Wheat_Oklahoma", "TX": "US_Wheat_Texas", "CO": "US_Wheat_Colorado", "WA": "US_Wheat_Washington", "ID": "US_Wheat_Idaho" }
    US_SPRING_WHEAT = { "ND": "US_Wheat_NorthDakota", "SD": "US_Wheat_SouthDakota", "MT": "US_Wheat_Montana" }
    US_CORN_META = { "IA": "US_Corn_Iowa", "IL": "US_Corn_Illinois", "NE": "US_Corn_Nebraska", "MN": "US_Corn_Minnesota", "IN": "US_Corn_Indiana", "OH": "US_Corn_Ohio", "WI": "US_Corn_Wisconsin", "MO": "US_Corn_Missouri", "MI": "US_Corn_Michigan" }
    
    STATE_CENTERS = { "KS":(38.5,-98.4), "MT":(47.0,-110.0), "WA":(47.4,-120.6), "OK":(35.6,-97.5), "ND":(47.5,-100.5),"TX":(31.5,-99.5), "SD":(44.5,-100.3), "CO":(39.0,-105.5), "ID":(44.0,-114.5),"IA":(42.0,-93.5), "IL":(40.0,-89.2), "NE":(41.5,-99.9), "MN":(46.4,-94.0), "IN":(40.3,-86.1), "OH":(40.4,-82.9), "WI":(44.5,-90.0), "MO":(38.5,-92.5), "MI":(44.0,-85.0) }

    def make_hover(name, crop, rk):
        r = regions.get(rk, {})
        risk = r.get("risk_assessment", "—")
        return (f"<b>{name}</b><br>{crop}<br>Mưa 3N: {r.get('total_3d_rain_mm','—')} mm<br>Max: {r.get('max_temp_C','—')}°C<br>{risk_label(risk)}")

    fig = go.Figure()
    all_states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]
    fig.add_trace(go.Choropleth(locations=all_states, z=[0]*len(all_states), locationmode="USA-states", colorscale=[[0,"#1e293b"],[1,"#1e293b"]], showscale=False, hoverinfo="skip", marker_line_color="#334155", marker_line_width=0.5))

    ww_st = list(US_WINTER_WHEAT.keys()); ww_z = [risk_to_score(regions.get(US_WINTER_WHEAT[s],{}).get("risk_assessment","")) for s in ww_st]; ww_text = [make_hover(s, "Lúa mì HRW", US_WINTER_WHEAT[s]) for s in ww_st]
    fig.add_trace(go.Choropleth(locations=ww_st, z=ww_z, locationmode="USA-states", colorscale=WHEAT_CS, showscale=False, hoverinfo="text", hovertext=ww_text, marker_line_color="#b45309", marker_line_width=1.5, zmin=0, zmax=2))

    sw_st = list(US_SPRING_WHEAT.keys()); sw_z = [risk_to_score(regions.get(US_SPRING_WHEAT[s],{}).get("risk_assessment","")) for s in sw_st]; sw_text = [make_hover(s, "Lúa mì Xuân", US_SPRING_WHEAT[s]) for s in sw_st]
    fig.add_trace(go.Choropleth(locations=sw_st, z=sw_z, locationmode="USA-states", colorscale=WHEAT_CS, showscale=False, hoverinfo="text", hovertext=sw_text, marker_line_color="#b45309", marker_line_width=1.5, zmin=0, zmax=2))

    c_st = list(US_CORN_META.keys()); c_z = [risk_to_score(regions.get(US_CORN_META[s],{}).get("risk_assessment","")) for s in c_st]; c_text = [make_hover(s, "Ngô/Đậu tương", US_CORN_META[s]) for s in c_st]
    fig.add_trace(go.Choropleth(locations=c_st, z=c_z, locationmode="USA-states", colorscale=CORN_CS, showscale=False, hoverinfo="text", hovertext=c_text, marker_line_color="#eab308", marker_line_width=1.5, zmin=0, zmax=2))

    for s in list(US_WINTER_WHEAT.keys()) + list(US_SPRING_WHEAT.keys()) + list(US_CORN_META.keys()):
        lat, lon = STATE_CENTERS.get(s, (0,0))
        fig.add_trace(go.Scattergeo(lon=[lon], lat=[lat], text=[s], mode="text", textfont=dict(color="black", size=10, weight="bold"), hoverinfo="skip"))

    fig.update_layout(geo_scope="usa", geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#1e293b", projection_type="albers usa"), margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, dragmode=False)
    return fig

def make_world_fig(regions: dict) -> go.Figure:
    TARGETS = { "RUS": ("Nga (Rostov)", "Russia_Rostov"), "UKR": ("Ukraine (Poltava)", "Ukraine_Poltava"), "BRA": ("Brazil (MatoGrosso)", "Brazil_MatoGrosso"), "ARG": ("Argentina (Pampas)", "Argentina_Pampas"), "AUS": ("Úc (NSW)", "Australia_NSW"), "FRA": ("Pháp (Centre)", "EU_France_Centre") }
    isos = list(TARGETS.keys())
    z_vals = [risk_to_score(regions.get(TARGETS[iso][1],{}).get("risk_assessment","")) for iso in isos]
    hover_texts = []
    for iso in isos:
        name, rk = TARGETS[iso]
        r = regions.get(rk, {})
        risk = r.get("risk_assessment", "—")
        hover_texts.append(f"<b>{name}</b><br>Mưa 3N: {r.get('total_3d_rain_mm','—')} mm<br>Max: {r.get('max_temp_C','—')}°C<br>{risk_label(risk)}")

    fig = go.Figure()
    fig.add_trace(go.Choropleth(locations=isos, z=z_vals, locationmode="ISO-3", colorscale=WORLD_CS, showscale=False, hoverinfo="text", hovertext=hover_texts, marker_line_color="#475569", marker_line_width=1, zmin=0, zmax=2))
    fig.update_layout(geo=dict(showcoastlines=True, coastlinecolor="#334155", showland=True, landcolor="#1e293b", bgcolor="rgba(0,0,0,0)", projection_type="equirectangular", center=dict(lat=20, lon=0), projection_scale=1.1), margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, dragmode=False)
    return fig

def make_enso_world_fig(impacts: list) -> go.Figure:
    ISO_MAP = { "Úc":"AUS", "Australia":"AUS", "Nam Mỹ":"BRA", "Brazil":"BRA", "Argentina":"ARG", "Đông Nam Á":"IDN", "Ấn Độ":"IND", "Bắc Mỹ":"USA", "Canada":"CAN", "Nam Phi":"ZAF", "Biển Đen":"UKR", "Nga":"RUS", "Ukraine":"UKR" }
    fig = go.Figure()
    isos = []; z_vals = []; texts = []
    for imp in impacts:
        region = imp.get("region","")
        iso = ISO_MAP.get(region)
        if iso:
            bias = imp.get("bias","").upper()
            z = 0 if "BULL" in bias else (2 if "BEAR" in bias else 1)
            isos.append(iso); z_vals.append(z)
            texts.append(f"<b>{region}</b><br>{imp.get('crop','')} - {imp.get('effect','')}")
    if isos:
        fig.add_trace(go.Choropleth(locations=isos, z=z_vals, locationmode="ISO-3", colorscale=[[0,"#ef4444"],[0.5,"#eab308"],[1,"#22c55e"]], showscale=False, hoverinfo="text", hovertext=texts, zmin=0, zmax=2, marker_line_color="#475569", marker_line_width=1))
    fig.update_layout(geo=dict(showcoastlines=True, coastlinecolor="#334155", showland=True, landcolor="#1e293b", bgcolor="rgba(0,0,0,0)", projection_type="natural earth", center=dict(lat=0, lon=0), projection_scale=1), margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, dragmode=False)
    return fig

# ─── MAIN UI ──────────────────────────────────────────────────────────────────
st.markdown("## 🌤️ Thời Tiết & Bản Đồ Nông Sản")

ws = load_weather_short()
wl = load_weather_long()

tab1, tab2 = st.tabs(["🌡️ Ngắn Hạn (3 ngày)", "🌊 Dài Hạn (ENSO & Vĩ Mô)"])

# ================= TAB 1: NGẮN HẠN =================
with tab1:
    ws_ts = ws.get("fetched_at", "—")
    st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-bottom:12px;'>⏱️ Cập nhật (Open-Meteo): {ws_ts}</div>", unsafe_allow_html=True)
    
    col_map, col_table = st.columns([6, 4], gap="large")
    regions_short = ws.get("regions", {})
    
    with col_map:
        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("<div class='map-title'>🇺🇸 Hoa Kỳ (Lúa Mì & Ngô)</div>", unsafe_allow_html=True)
        fig_us = make_us_fig(regions_short)
        st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("<div class='map-title'>🌍 Khu Vực Quốc Tế (Đối Thủ)</div>", unsafe_allow_html=True)
        fig_world = make_world_fig(regions_short)
        st.plotly_chart(fig_world, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_table:
        st.markdown("<div class='map-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<div class='map-title'>📋 Báo Cáo Rủi Ro (Tất Cả Các Vùng)</div>", unsafe_allow_html=True)
        
        if regions_short:
            html = "<table>"
            html += "<tr><th style='width:30%'>Khu Vực</th><th style='width:15%;text-align:center;'>Mưa (mm)</th><th style='width:15%;text-align:center;'>T° Max</th><th style='width:40%'>Cảnh Báo</th></tr>"
            
            for rname, rdata in regions_short.items():
                risk = rdata.get("risk_assessment", "Bình thường")
                risk_lower = risk.lower() if risk else ""
                if any(kw in risk_lower for kw in ["khô","hạn","nóng","cao","kho","han","nong","ngập","ngap","lũ","lu"]):
                    risk_color = "#ef4444"; risk_icon = "🔴"
                elif any(kw in risk_lower for kw in ["thuận lợi","tốt","thuan loi","favorable","tot"]):
                    risk_color = "#22c55e"; risk_icon = "🟢"
                else:
                    risk_color = "#f59e0b"; risk_icon = "🟡"
                    
                rain = rdata.get("total_3d_rain_mm", "—")
                temp = rdata.get("max_temp_C", "—")
                display_name = rname.replace("_", " ")
                
                html += f"""<tr>
                    <td><b>{display_name}</b></td>
                    <td style='text-align:center;color:#60a5fa;'>{rain}</td>
                    <td style='text-align:center;color:#f97316;'>{temp}</td>
                    <td><span style='color:{risk_color};font-weight:600;'>{risk_icon} {risk}</span></td>
                </tr>"""
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Chưa có dữ liệu thời tiết.")
        st.markdown("</div>", unsafe_allow_html=True)

# ================= TAB 2: ENSO =================
with tab2:
    enso_status = wl.get("enso_status","—")
    enso_desc   = wl.get("description","—")
    impacts     = wl.get("impacts",[])
    fetched_long= wl.get("fetched_at","—")

    for bad, good in [("NiA\xc3\xb1o","Niño"),("NiA o","Niño"),("NiAo","Niño"),("La Ni?a","La Niña"),("chA?u","châu"),("A?c","Úc")]:
        enso_status = enso_status.replace(bad, good)
        enso_desc   = enso_desc.replace(bad, good)
        
    status_lower = enso_status.lower()
    if "el ni" in status_lower:
        badge_color = "#ef4444"; badge_text = "🌡️ El Niño"
    elif "la ni" in status_lower:
        badge_color = "#3b82f6"; badge_text = "❄️ La Niña"
    else:
        badge_color = "#64748b"; badge_text = "⚖️ ENSO Neutral"
        
    st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-bottom:12px;'>⏱️ Cập nhật (NOAA): {fetched_long}</div>", unsafe_allow_html=True)
    
    col_enso_map, col_enso_tbl = st.columns([5, 5], gap="large")
    
    with col_enso_map:
        st.markdown(f"""
        <div class='map-card'>
            <div class='map-title'>🌊 TRẠNG THÁI HIỆN TẠI</div>
            <span class='enso-badge' style='background:{badge_color}20; color:{badge_color}; border:1px solid {badge_color};'>
                {badge_text} — {enso_status}
            </span>
            <p style='font-size:13px; color:#94a3b8; margin:8px 0 0; line-height:1.5;'>{enso_desc}</p>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("""<div class='map-title'>
            🌍 TÁC ĐỘNG ENSO ĐẾN GIÁ NÔNG SẢN
            <br><span style='font-size:11px;font-weight:400;color:#94a3b8;'>
                🔴 BULLISH (Thiếu cung) &nbsp;|&nbsp; 🟢 BEARISH (Dư cung)
            </span>
        </div>""", unsafe_allow_html=True)
        if impacts:
            fig_enso = make_enso_world_fig(impacts)
            st.plotly_chart(fig_enso, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_enso_tbl:
        st.markdown("<div class='map-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<div class='map-title'>📋 Bảng Phân Tích Tác Động</div>", unsafe_allow_html=True)
        if impacts:
            html3 = """<table>
            <tr>
            <th>Khu Vực</th>
            <th>Nông Sản</th>
            <th style='text-align:center;'>Mức Độ</th>
            <th style='text-align:center;'>Tín Hiệu</th>
            </tr>"""
            for imp in impacts:
                bias = imp.get("bias","—").upper()
                sev  = imp.get("severity","—")
                if "BULLISH" in bias or "BULL" in bias:
                    bias_html = "<span style='color:#ef4444;font-weight:700;'>🔴 BULL</span>"
                    sev_color = "#ef4444"
                elif "BEARISH" in bias or "BEAR" in bias:
                    bias_html = "<span style='color:#22c55e;font-weight:700;'>🟢 BEAR</span>"
                    sev_color = "#22c55e"
                else:
                    bias_html = "<span style='color:#eab308;font-weight:700;'>🟡 NEUTRAL</span>"
                    sev_color = "#eab308"

                region = imp.get("region","—")
                for bad,good in [("ChA?u","Châu"),("A?c","Úc"),("Nam M?1","Nam Mỹ"),("B?_c M?1","Bắc Mỹ"),("LA?a MA?","Lúa Mì"),("NgA?","Ngô")]:
                    region = region.replace(bad,good)
                    
                sev = sev.replace("Cao","Cao").replace("Trung bình","T.Bình")
                
                html3 += f"""<tr>
                    <td><b>{region}</b><br><span style='font-size:11px;color:#64748b;'>{imp.get('effect','—')[:60]}...</span></td>
                    <td style='color:#94a3b8;'>{imp.get('crop','—')}</td>
                    <td style='text-align:center;color:{sev_color};font-weight:600;'>{sev}</td>
                    <td style='text-align:center;'>{bias_html}</td>
                </tr>"""
            html3 += "</table>"
            st.markdown(html3, unsafe_allow_html=True)
        else:
            st.info("Chưa có dữ liệu ENSO.")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    pass
