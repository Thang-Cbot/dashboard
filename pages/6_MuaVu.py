"""
pages/6_MuaVu.py - Phân tích Mùa Vụ (ZW & ZC)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json, csv
import streamlit as st
import subprocess
from pathlib import Path

st.set_page_config(page_title="Mùa Vụ - CBOT", page_icon="🌾", layout="wide")

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
    border: 1px solid #1e2d45; border-radius: 12px;
    padding: 16px 18px; margin-bottom: 8px; background: #111827;
}
.mv-card-title {
    font-size: 10px; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    border-bottom: 1px solid #1e2d45; padding-bottom: 6px;
}
.mv-card-value { font-size: 17px; font-weight: 800; color: #e2e8f0; margin-bottom: 4px; }
.mv-card-sub   { font-size: 11px; color: #94a3b8; }
.mv-card-updated { font-size: 9px; color: #475569; margin-top: 6px; }

.reg-table { width:100%; border-collapse: collapse; margin-top: 8px; }
.reg-table th {
    padding: 10px 14px; font-size: 10px; font-weight: 700;
    color: #64748b; text-transform: uppercase; letter-spacing: 1px;
    border-bottom: 2px solid #2a3a5c; text-align: left; background: #0b0f19;
}
.reg-table td {
    padding: 12px 14px; font-size: 12px; color: #cbd5e1;
    border-bottom: 1px solid #1e2d45; vertical-align: top; line-height: 1.7;
}
.reg-table tr:hover td { background: #161e2e; }
.region-header { font-weight: 700; color: #e2e8f0; font-size: 13px; }
.region-flag { font-size: 18px; }
.harvest-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 700; background: #1e3a5f; color: #60a5fa; margin-bottom: 4px;
}
.dot-green { color: #22c55e; font-weight: bold; }
.dot-yellow { color: #eab308; font-weight: bold; }
.dot-red { color: #ef4444; font-weight: bold; }

.dca-box {
    border: 2px solid #f59e0b; border-radius: 14px;
    padding: 20px 24px; background: #111820;
}
.dca-zone { border: 1px solid #374151; border-radius: 8px; padding: 12px 16px; margin-top: 10px; }
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

macro        = load_json("macro_scores.json")
macro_data   = load_json("macro_data.json")
fund         = load_json("fundamental_data.json")
cot          = load_json("cot_data.json")
ai_analysis  = load_json("ai_muavu_analysis.json")
export_s     = load_json("export_sales.json")
weather_long = load_json("weather_long.json")

breakdown    = macro.get("breakdown", {})
cot_zw       = cot.get("commodities", {}).get("001602", {})

# Price helpers — read directly from D1 CSV for 1-month range
@st.cache_data(ttl=120)
def get_zw_price_info():
    try:
        rows = []
        with open(DATA_OUTPUT / "ZW_active_D1.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader: rows.append(r)
        if not rows: return {}
        last = rows[-1]
        # last 22 trading days (~1 month)
        recent = rows[-22:]
        highs = [float(r["High"]) for r in recent]
        lows  = [float(r["Low"])  for r in recent]
        close = float(last["Close"])
        return {
            "close":    close,
            "high_1m":  max(highs),
            "low_1m":   min(lows),
            "s1":       float(last.get("S1", 0)),
            "s2":       float(last.get("S2", 0)),
            "r1":       float(last.get("R1", 0)),
            "r2":       float(last.get("R2", 0)),
            "atr":      float(last.get("ATR", 0)),
            "rsi":      float(last.get("RSI", 0)),
            "date":     last["Time"][:10],
        }
    except: return {}

zw_info = get_zw_price_info()

# ─── SIDEBAR NAV ─────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",                    label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py",       label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py",       label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",           label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",        label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",        label="🗺️ Bản Đồ Thời Tiết")
st.sidebar.page_link("pages/5_Macro_Matrix.py",   label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",          label="🌾 Mùa Vụ")
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
    "<span class='dot-green'>🟢 Auto (hệ thống tự lấy)</span> &nbsp;|&nbsp; "
    "<span class='dot-yellow'>🟡 AI / Chuyên gia (định giá kỳ vọng)</span> &nbsp;|&nbsp; "
    "<span class='dot-red'>🔴 Lỗi / Không có data</span>",
    unsafe_allow_html=True
)

# ─── PART 1: GLOBAL MACRO ────────────────────────────────────────────────────
st.subheader("🌍 PHẦN 1: GLOBAL MACRO (Vĩ Mô Toàn Cầu)")

def score_color(s):
    try: v=int(s)
    except: return "#94a3b8"
    return "#22c55e" if v>=7 else ("#eab308" if v>=5 else "#ef4444")

def score_badge(s):
    c = score_color(s)
    return f"<b style='color:{c};'>{s}/10</b>"

# Pull LIVE values from macro_data.json
mac_ts   = macro_data.get("timestamp", "—")[:16]
dxy_live = macro_data.get("dxy", {}).get("price", "N/A")
dxy_pct  = macro_data.get("dxy", {}).get("pct", 0)
oil_live = macro_data.get("brent", {}).get("price", "N/A")
oil_pct  = macro_data.get("brent", {}).get("pct", 0)
dxy_pt   = breakdown.get("F9",  {}).get("score_1_to_10", "N/A")
oil_pt   = breakdown.get("F10", {}).get("score_1_to_10", "N/A")
f8_s     = breakdown.get("F8",  {})
f8_up    = f8_s.get("last_updated", "—")
f12_s    = breakdown.get("F12", {})
f12_up   = f12_s.get("last_updated", "—")

# El Nino from weather_long
enso_status = weather_long.get("enso_status", "N/A")
enso_desc   = weather_long.get("description", "—")
enso_up     = weather_long.get("fetched_at", "—")[:16]

cot_net  = cot_zw.get("net_estimated", "N/A")
cot_q    = cot_zw.get("quadrant_estimated", "N/A")
cot_up   = cot_zw.get("fetched_at", cot.get("fetched_at", "—"))[:16]

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    pct_str = f"{dxy_pct:+.2f}%" if isinstance(dxy_pct, (int,float)) else ""
    pc = "#22c55e" if isinstance(dxy_pct,(int,float)) and dxy_pct<0 else "#ef4444"
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>🟢 Sức Mạnh USD (DXY)</div>
        <div class='mv-card-value'>{dxy_live}</div>
        <div class='mv-card-sub'>Điểm: {score_badge(dxy_pt)} &nbsp;<span style='color:{pc};'>{pct_str}</span></div>
        <div class='mv-card-sub'>DXY cao → lúa mì Mỹ đắt → Bearish XK</div>
        <div class='mv-card-updated'>⏱ {mac_ts}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    pc2 = "#22c55e" if isinstance(oil_pct,(int,float)) and oil_pct>=0 else "#ef4444"
    pct2 = f"{oil_pct:+.2f}%" if isinstance(oil_pct,(int,float)) else ""
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>🟢 Giá Dầu Brent</div>
        <div class='mv-card-value'>{oil_live} USD/thùng</div>
        <div class='mv-card-sub'>Điểm: {score_badge(oil_pt)} &nbsp;<span style='color:{pc2};'>{pct2}</span></div>
        <div class='mv-card-sub'>Dầu ảnh hưởng cước tàu & phân bón</div>
        <div class='mv-card-updated'>⏱ {mac_ts}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    cot_color = "#ef4444" if isinstance(cot_net,(int,float)) and cot_net < 0 else "#22c55e"
    cot_dot = "🟢" if cot_zw else "🔴"
    cot_net_fmt = f"{cot_net:,.0f}" if isinstance(cot_net,(int,float)) else cot_net
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>{cot_dot} Dòng Tiền COT – ZW</div>
        <div class='mv-card-value' style='color:{cot_color};'>{cot_net_fmt} HĐ</div>
        <div class='mv-card-sub'>{cot_q}</div>
        <div class='mv-card-updated'>⏱ {cot_up}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    f12_note = f12_s.get("raw_detail", "—")[:80]
    f12_pt   = f12_s.get("score_1_to_10", "N/A")
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>🟡 Nhu Cầu Thế Giới</div>
        <div class='mv-card-value'>Điểm: <span style='color:{score_color(f12_pt)};'>{f12_pt}/10</span></div>
        <div class='mv-card-sub'>{f12_note}</div>
        <div class='mv-card-updated'>⏱ {f12_up}</div>
    </div>""", unsafe_allow_html=True)

with col5:
    f8_note = f8_s.get("raw_detail", "—")[:80]
    f8_pt   = f8_s.get("score_1_to_10", "N/A")
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>🟡 Địa Chính Trị / Logistics</div>
        <div class='mv-card-value'>Điểm: <span style='color:{score_color(f8_pt)};'>{f8_pt}/10</span></div>
        <div class='mv-card-sub'>{f8_note}</div>
        <div class='mv-card-updated'>⏱ {f8_up}</div>
    </div>""", unsafe_allow_html=True)

with col6:
    enso_col = "#ef4444" if "Niño" in enso_status else ("#22c55e" if "Niña" in enso_status else "#eab308")
    enso_short = enso_desc[:90] + "..." if len(enso_desc) > 90 else enso_desc
    st.markdown(f"""<div class='mv-card'>
        <div class='mv-card-title'>🟢 El Niño / La Niña (ENSO)</div>
        <div class='mv-card-value' style='color:{enso_col}; font-size:13px;'>{enso_status}</div>
        <div class='mv-card-sub'>{enso_short}</div>
        <div class='mv-card-updated'>⏱ {enso_up}</div>
    </div>""", unsafe_allow_html=True)


# ─── PART 2: REGIONAL TABLE ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("🗺️ PHẦN 2: MÙA VỤ THEO 4 KHU VỰC")

def pts(f): return f.get("score_1_to_10", "N/A")
def note(f, n=90): txt=f.get("raw_detail", f.get("raw_value","—")); return txt[:n]+"…" if len(txt)>n else txt
def upd(f): return f"<div style='font-size:9px;color:#475569;margin-top:4px;'>⏱ {f.get('last_updated','—')}</div>"

f1_s  = breakdown.get("F1", {})
f2w_s = breakdown.get("F2W", {})
f2_s  = breakdown.get("F2", {})
f3_s  = breakdown.get("F3", {})
f4_s  = breakdown.get("F4", {})
f4s_s = breakdown.get("F4S", {})
f7_s  = breakdown.get("F7", {})

exp_zw   = export_s.get("commodities", {}).get("ZW", {})
net_sales_raw = exp_zw.get("current_mt", "N/A")
net_sales = f"{net_sales_raw:,.0f}" if isinstance(net_sales_raw, (int,float)) else net_sales_raw
exp_date  = export_s.get("current_week_ending", export_s.get("fetched_at", "N/A"))
exp_updated = export_s.get("fetched_at", "—")[:16]

# El Nino impacts per region
def enso_impact(region_key):
    for imp in weather_long.get("impacts", []):
        if region_key in imp.get("region", ""):
            bias_col = "#ef4444" if imp["bias"]=="BULLISH" else "#22c55e"
            return f"<span style='color:{bias_col};font-weight:700;'>{imp['bias']}</span> – {imp['effect'][:80]}"
    return "—"

table_html = f"""
<table class='reg-table'>
<thead><tr>
  <th style='width:13%'>Khu Vực</th>
  <th style='width:14%'>Lịch Mùa Vụ</th>
  <th style='width:26%'>Sản Lượng / Tồn Kho</th>
  <th style='width:26%'>Thời Tiết & El Niño</th>
  <th style='width:21%'>Chính Sách / Xuất Khẩu</th>
</tr></thead>
<tbody>

<tr>
  <td><div class='region-flag'>🇺🇸</div><div class='region-header'>Bắc Bán Cầu<br>(Mỹ)</div></td>
  <td><span class='harvest-badge'>THU HOẠCH T6–T7</span><br>Gieo Đông: T9–T10<br>Mùa Xuân: T4–T5</td>
  <td>
    <span class='dot-green'>🟢</span> <b>Tồn kho WASDE:</b> {score_badge(pts(f2_s))}<br>
    <small style='color:#94a3b8;'>{note(f2_s, 70)}</small>{upd(f2_s)}
    <span class='dot-green'>🟢</span> <b>Export Sales (tuần {exp_date}):</b><br>
    <b style='color:#34d399; font-size:15px;'>{net_sales} MT</b>
    <div style='font-size:9px;color:#475569;'>⏱ {exp_updated}</div>
    <span class='dot-green'>🟢</span> <b>Crop Progress:</b> {score_badge(pts(f7_s))}<br>
    <small style='color:#94a3b8;'>{note(f7_s, 70)}</small>{upd(f7_s)}
  </td>
  <td>
    <span class='dot-yellow'>🟡</span> Thời tiết (HRW): {score_badge(pts(f2w_s))}<br>
    <small>{note(f2w_s)}</small>{upd(f2w_s)}<br>
    <b>El Niño:</b> {enso_impact("Bắc Mỹ")}
  </td>
  <td>
    <span class='dot-green'>🟢</span> DXY {dxy_live} → sức cạnh tranh XK<br>
    <small>DXY cao làm lúa mì Mỹ đắt hơn trên thị trường MENA.</small>
  </td>
</tr>

<tr>
  <td><div class='region-flag'>🇪🇺</div><div class='region-header'>Châu Âu<br>(EU)</div></td>
  <td><span class='harvest-badge'>THU HOẠCH T7–T8</span><br>Xả hàng cao điểm: T8–T9</td>
  <td>
    <span class='dot-yellow'>🟡</span> Nguồn cung EU: {score_badge(pts(f3_s))}<br>
    <small>{note(f3_s)}</small>{upd(f3_s)}
  </td>
  <td>
    <b>El Niño:</b> {enso_impact("Biển Đen")}<br>
    <small>Nắng nóng cực đoan tại Pháp, Đức → mất mùa nghiêm trọng hơn dự báo.</small>
  </td>
  <td>
    <span class='dot-yellow'>🟡</span> Quota XK EU linh hoạt theo thị trường<br>
    <small>EU cạnh tranh với Mỹ tại thị trường MENA khi giá FOB Nga tăng.</small>
  </td>
</tr>

<tr>
  <td><div class='region-flag'>🇷🇺</div><div class='region-header'>Biển Đen<br>(Nga & Ukraine)</div></td>
  <td><span class='harvest-badge'>XẢ HÀNG T8–T10</span><br>Đỉnh áp lực giảm giá toàn cầu</td>
  <td>
    <span class='dot-yellow'>🟡</span> Chính sách xuất khẩu Nga: {score_badge(pts(f1_s))}<br>
    <small>{note(f1_s)}</small>{upd(f1_s)}
  </td>
  <td>
    <b>El Niño:</b> {enso_impact("Biển Đen")}<br>
    <small>Hạn hán tại vùng Đen ảnh hưởng tiến độ gieo hạt Lúa mì vụ Đông mới (T9–T11).</small>
  </td>
  <td>
    <span class='dot-yellow'>🟡</span> Logistics / Địa chính trị: {score_badge(pts(f8_s))}<br>
    <small>{note(f8_s)}</small>{upd(f8_s)}
  </td>
</tr>

<tr>
  <td><div class='region-flag'>🇦🇺</div><div class='region-header'>Nam Bán Cầu<br>(Úc & Argentina)</div></td>
  <td><span class='harvest-badge'>THU HOẠCH T11–T12</span><br>→ Áp lực cung cao nhất cuối năm</td>
  <td>
    <span class='dot-yellow'>🟡</span> Sản lượng Nam BC: {score_badge(pts(f4s_s))}<br>
    <small>{note(f4s_s)}</small>{upd(f4s_s)}
  </td>
  <td>
    <span class='dot-yellow'>🟡</span> Thời tiết: {score_badge(pts(f4_s))}<br>
    <small>{note(f4_s)}</small>{upd(f4_s)}<br>
    <b>El Niño → Úc:</b> {enso_impact("Châu Úc")}<br>
    <b>El Niño → Argentina:</b> {enso_impact("Nam Mỹ (Argentina)")}
  </td>
  <td>
    <span class='dot-yellow'>🟡</span> Úc: ABARES nâng lên 29.9M tấn (+vs kỳ vọng)<br>
    <small>Argentina: BCR cắt xuống 21M tấn do hạn hán. El Niño đang phát triển mạnh → Q1/2027 sẽ là thời điểm ảnh hưởng nặng nhất.</small>
  </td>
</tr>

</tbody>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)


# ─── PART 3: AI CONCLUSION + DCA BOX ────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 PHẦN 3: KẾT LUẬN & KẾ HOẠCH DCA (AI ANALYSIS)")

# DCA Snapshot Box
close   = zw_info.get("close", "N/A")
high1m  = zw_info.get("high_1m", "N/A")
low1m   = zw_info.get("low_1m", "N/A")
s1      = zw_info.get("s1", "N/A")
s2      = zw_info.get("s2", "N/A")
r1      = zw_info.get("r1", "N/A")
atr     = zw_info.get("atr", "N/A")
rsi     = zw_info.get("rsi", "N/A")
zw_date = zw_info.get("date", "—")

pct_1m = ((close - low1m) / (high1m - low1m) * 100) if isinstance(close,(int,float)) and isinstance(high1m,(int,float)) and high1m!=low1m else None

col_a, col_b = st.columns([1, 1])
with col_a:
    rsi_color = "#22c55e" if isinstance(rsi,(int,float)) and rsi < 35 else ("#ef4444" if isinstance(rsi,(int,float)) and rsi > 65 else "#eab308")
    pct_bar = f"({pct_1m:.0f}% trong biên độ 1 tháng)" if pct_1m is not None else ""
    st.markdown(f"""
    <div class='dca-box'>
      <div style='font-size:11px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;'>
        📊 THÔNG SỐ GIÁ ZW (ZWZ26) – Cập nhật: {zw_date}
      </div>
      <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;'>
        <div class='dca-zone'>
          <div style='font-size:10px;color:#64748b;'>GIÁ HIỆN TẠI</div>
          <div style='font-size:24px;font-weight:800;color:#f59e0b;'>{close:.2f}¢</div>
          <div style='font-size:10px;color:#94a3b8;'>{pct_bar}</div>
        </div>
        <div class='dca-zone'>
          <div style='font-size:10px;color:#64748b;'>BIÊN ĐỘ 1 THÁNG</div>
          <div style='font-size:14px;font-weight:700;color:#e2e8f0;'>Cao: <span style='color:#ef4444;'>{high1m:.2f}¢</span></div>
          <div style='font-size:14px;font-weight:700;color:#e2e8f0;'>Thấp: <span style='color:#22c55e;'>{low1m:.2f}¢</span></div>
        </div>
        <div class='dca-zone'>
          <div style='font-size:10px;color:#64748b;'>RSI / ATR</div>
          <div style='font-size:16px;font-weight:700;color:{rsi_color};'>RSI {rsi:.1f}</div>
          <div style='font-size:12px;color:#94a3b8;'>ATR {atr:.1f}¢ / ngày</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class='dca-box' style='border-color:#22c55e;'>
      <div style='font-size:11px;font-weight:700;color:#22c55e;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;'>
        🎯 VÙNG GOM DCA DỰ KIẾN (DỰA TRÊN VĨ MÔ + KỸ THUẬT)
      </div>
      <div class='dca-zone' style='border-color:#22c55e; margin-bottom:8px;'>
        <div style='font-size:10px;color:#64748b;'>THỜI GIAN GOM TỐI ƯU</div>
        <div style='font-size:15px;font-weight:700;color:#86efac;'>Cuối T11 – Giữa T12/2026</div>
        <div style='font-size:11px;color:#94a3b8;'>Khi áp lực xả hàng Úc+Argentina đạt đỉnh, El Niño bắt đầu ảnh hưởng Q1/2027</div>
      </div>
      <div class='dca-zone' style='border-color:#f59e0b; margin-bottom:8px;'>
        <div style='font-size:10px;color:#64748b;'>VÙNG GOM ZONE 1 (Ưu tiên)</div>
        <div style='font-size:18px;font-weight:800;color:#fde68a;'>{s1:.0f} – 680¢</div>
        <div style='font-size:11px;color:#94a3b8;'>Hỗ trợ kỹ thuật S1 + Đáy 1 tháng gần nhất</div>
      </div>
      <div class='dca-zone' style='border-color:#94a3b8;'>
        <div style='font-size:10px;color:#64748b;'>VÙNG GOM ZONE 2 (Dự phòng Bearish cực đoan)</div>
        <div style='font-size:18px;font-weight:800;color:#cbd5e1;'>{s2:.0f} – 620¢</div>
        <div style='font-size:11px;color:#94a3b8;'>Chỉ DCA thêm khi có tin tức vĩ mô cực kỳ Bearish bất ngờ</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if ai_analysis and "analysis" in ai_analysis:
    st.caption(f"⏱ Lần phân tích AI cuối: **{ai_analysis.get('last_updated', '')}** — Ấn 'Cập Nhật Mùa Vụ' để làm mới.")
    st.markdown(ai_analysis["analysis"])
else:
    st.warning("Chưa có bản phân tích AI. Ấn nút **'🔄 Cập Nhật Mùa Vụ (AI)'** ở cột trái.")
