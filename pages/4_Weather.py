"""
pages/4_Weather.py — Thời Tiết Ngắn Hạn & Dài Hạn ENSO
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Thời Tiết — CBOT", page_icon="🌤️", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

@st.cache_data(ttl=300)
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
.section-header { font-size:15px; font-weight:800; color:#e2e8f0; margin:20px 0 12px 0; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th { background:#0f1629; color:#94a3b8; padding:10px 12px; text-align:left; font-weight:600;
     font-size:11px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #2a3a5c; }
td { padding:10px 12px; color:#cbd5e1; border-bottom:1px solid #1e2d45; vertical-align:top; }
tr:hover td { background:#1e2d45; }
</style>""", unsafe_allow_html=True)

st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Tin Tức & Cung Cầu")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Nông Sản")

st.markdown("## 🌤️ Báo Cáo Thời Tiết")

ws = load_json("weather_short.json")
wl = load_json("weather_long.json")

# ── ENSO Dài Hạn ──────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🌊 Báo Cáo Thời Tiết Dài Hạn (Vĩ Mô ENSO)</div>", unsafe_allow_html=True)

if wl:
    enso = wl.get("enso_status", "Neutral")
    desc = wl.get("description", "")
    ts   = wl.get("fetched_at", "—")
    src  = wl.get("source", "NOAA")

    # Fix bad encoding and translate
    enso = enso.replace("NiAo", "Niño").replace("NiA\ufffdo", "Niño")
    desc = desc.replace("NiAo", "Niño").replace("NiA\ufffdo", "Niño")
    
    if "El Niño conditions are present" in desc:
        desc = "Hiện tượng El Niño đang xuất hiện và dự kiến sẽ mạnh lên vào mùa đông 2026-27 ở Bán cầu Bắc."
    elif "La Niña conditions are present" in desc:
        desc = "Hiện tượng La Niña đang xuất hiện và dự kiến sẽ kéo dài vào mùa đông ở Bán cầu Bắc."
    elif "Neutral" in desc:
        desc = "Trạng thái ENSO hiện đang trung tính."

    if "Advisory" in enso:
        enso = enso.replace("Advisory", "Cảnh Báo")
    if "Watch" in enso:
        enso = enso.replace("Watch", "Theo Dõi")

    # Màu ENSO
    enso_color = "#ef4444" if "el ni" in enso.lower() else ("#60a5fa" if "la ni" in enso.lower() else "#94a3b8")
    enso_icon  = "🔥" if "el ni" in enso.lower() else ("❄️" if "la ni" in enso.lower() else "⚖️")

    st.markdown(f"""
    <div class='card'>
        <div style='display:flex; align-items:center; gap:16px; margin-bottom:12px;'>
            <div style='font-size:40px;'>{enso_icon}</div>
            <div>
                <div style='font-size:20px; font-weight:800; color:{enso_color};'>{enso}</div>
                <div style='font-size:11px; color:#64748b;'>Nguồn: {src} | Cập nhật: {ts}</div>
            </div>
        </div>
        <div style='font-size:13px; color:#94a3b8; line-height:1.6; margin-bottom:12px;'>{desc}</div>
    </div>""", unsafe_allow_html=True)

    # Bảng tác động theo vùng
    impacts = wl.get("impacts", [])
    if impacts:
        html = "<div class='card'><table>"
        html += """<tr>
            <th style='width:20%'>Khu Vực</th>
            <th style='width:20%'>Nông Sản Tác Động</th>
            <th style='width:40%'>Chi Tiết & Thời Gian</th>
            <th style='width:10%'>Mức Độ</th>
            <th style='width:10%'>Tín Hiệu</th>
        </tr>"""

        for imp in impacts:
            region  = imp.get("region", "—")
            crop    = imp.get("crop", "—")
            effect  = imp.get("effect", "—")
            sev     = imp.get("severity", "—")
            bias    = imp.get("bias", "NEUTRAL")
            color   = imp.get("color", "#94a3b8")

            bias_badge = ""
            if "BULL" in bias:
                bias_badge = '<span style="background:#14532d;color:#4ade80;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">▲ BULL</span>'
            elif "BEAR" in bias:
                bias_badge = '<span style="background:#7f1d1d;color:#f87171;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">▼ BEAR</span>'
            else:
                bias_badge = '<span style="background:#1e2d45;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:11px;">— NEU</span>'

            sev_color = "#ef4444" if sev == "Cao" else ("#f59e0b" if sev == "Trung bình" else "#64748b")

            html += f"""<tr>
                <td><b style='color:{color};'>{region}</b></td>
                <td>{crop}</td>
                <td style='color:#94a3b8; font-size:12px;'>{effect}</td>
                <td><span style='color:{sev_color};font-weight:700;'>{sev}</span></td>
                <td>{bias_badge}</td>
            </tr>"""

        html += "</table></div>"
        st.markdown(html, unsafe_allow_html=True)
else:
    st.info("Chưa có dữ liệu ENSO. Chạy RUN ALL DATA.bat.")

# ── Thời Tiết Ngắn Hạn ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🌡️ Báo Cáo Thời Tiết Ngắn Hạn (3 Ngày)</div>", unsafe_allow_html=True)

if ws:
    ws_ts   = ws.get("fetched_at", "—")
    ws_src  = ws.get("source", "Open-Meteo")
    regions = ws.get("regions", {})

    st.markdown(f"""
    <div style='font-size:11px;color:#64748b;margin-bottom:10px;'>
        Nguồn: {ws_src} | Cập nhật: {ws_ts}
    </div>""", unsafe_allow_html=True)

    if regions:
        html = "<div class='card'><table>"
        html += """<tr>
            <th style='width:22%'>Khu Vực</th>
            <th style='width:15%'>Mô Tả</th>
            <th style='width:12%'>Mưa 3N (mm)</th>
            <th style='width:11%'>T° Tối Đa</th>
            <th style='width:25%'>Đánh Giá Rủi Ro</th>
            <th style='width:15%'>Dự Báo Chi Tiết</th>
        </tr>"""

        for rname, rdata in regions.items():
            desc     = rdata.get("desc", "—")
            risk     = rdata.get("risk_assessment", "Bình thường")
            rain     = rdata.get("total_3d_rain_mm", "—")
            temp     = rdata.get("max_temp_C", "—")
            forecast = rdata.get("forecast", [])

            risk_lower = risk.lower() if risk else ""
            # Check for both accented and unaccented keywords
            if any(kw in risk_lower for kw in ["khô", "hạn", "nóng", "cao", "kho", "han", "nong", "ngập", "ngap", "lũ", "lu"]):
                risk_color = "#ef4444"
                risk_icon  = "🔴"
            elif any(kw in risk_lower for kw in ["thuận lợi", "tốt", "thuan loi", "favorable", "tot"]):
                risk_color = "#22c55e"
                risk_icon  = "🟢"
            else: # Bình thường or anything else
                risk_color = "#f59e0b"
                risk_icon  = "🟡"

            forecast_str = " | ".join([
                f"{f.get('date','')}: {f.get('precip_mm',0):.0f}mm/{f.get('temp_max_C',0):.0f}°C"
                for f in forecast[:3]
            ]) if forecast else "—"

            html += f"""<tr>
                <td><b>{rname.replace('_', ' ')}</b></td>
                <td style='color:#94a3b8;font-size:12px;'>{desc}</td>
                <td style='text-align:center;'>{rain}</td>
                <td style='text-align:center;'>{temp}°C</td>
                <td><span style='color:{risk_color};'>{risk_icon} {risk}</span></td>
                <td style='font-size:11px;color:#64748b;'>{forecast_str}</td>
            </tr>"""

        html += "</table></div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("Chưa có dữ liệu vùng thời tiết.")
else:
    st.info("Chưa có dữ liệu thời tiết ngắn hạn. Chạy RUN ALL DATA.bat.")
