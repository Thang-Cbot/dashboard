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



# Price helpers — read directly from D1 CSV for 1-month range
@st.cache_data(ttl=120)
def get_price_info(commodity):
    try:
        rows = []
        with open(DATA_OUTPUT / f"{commodity}_active_D1.csv", encoding="utf-8") as f:
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



# ─── SIDEBAR NAV ─────────────────────────────────────────────────────────────
st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather_Map.py",label="🌤️ Thời Tiết & Bản Đồ")
st.sidebar.page_link("pages/5_Macro_Matrix.py", label="🧠 Ma Trận Vĩ Mô (Brain)")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Cập Nhật Mùa Vụ (AI)", type="primary", use_container_width=True):
    with st.sidebar.status("⏳ Đang cập nhật dữ liệu...", expanded=True) as _s:
        env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"

        # Step 1: Fetch macro data
        st.write("📡 Bước 1/3: Tải dữ liệu macro (DXY, Dầu)...")
        r1 = subprocess.run([sys.executable, str(BASE_DIR/"Data"/"fetch_macro.py")],
                            capture_output=True, text=True, env=env)
        st.write("✅ Macro OK" if r1.returncode==0 else f"❌ Macro: {r1.stderr[-100:]}")

        # Step 2: Run AI analysis
        st.write("🤖 Bước 2/3: Phân tích AI (Gemini)...")
        r2 = subprocess.run([sys.executable, str(BASE_DIR/"Data"/"analyze_muavu_ai.py")],
                            capture_output=True, text=True, env=env)
        st.write("✅ AI OK" if r2.returncode==0 else f"❌ AI: {r2.stderr[-100:]}")

        # Step 3: Check status of all items
        st.write("🔍 Bước 3/3: Kiểm tra trạng thái toàn bộ dữ liệu...")
        r3 = subprocess.run([sys.executable, str(BASE_DIR/"Data"/"check_muavu_status.py")],
                            capture_output=True, text=True, env=env)
        st.write("✅ Kiểm tra xong" if r3.returncode==0 else f"❌ Check: {r3.stderr[-100:]}")

        if r2.returncode==0 and r3.returncode==0:
            _s.update(label="✅ Cập nhật hoàn tất!", state="complete", expanded=False)
        else:
            _s.update(label="⚠️ Hoàn tất với một số lỗi", state="error")
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

# ─── STATUS REPORT (Hiện sau khi bấm Cập Nhật) ───────────────────────────────
muavu_status = load_json("muavu_status.json")
if muavu_status:
    summary = muavu_status.get("summary", {})
    ok_cnt  = summary.get("ok", 0)
    warn_cnt= summary.get("warning", 0)
    err_cnt = summary.get("error", 0)
    total   = summary.get("total", 0)
    checked = muavu_status.get("checked_at", "—")

    # Summary bar
    bar_color = "#22c55e" if err_cnt==0 else ("#eab308" if warn_cnt>0 else "#ef4444")
    with st.expander(f"📋 Báo cáo trạng thái dữ liệu — ✅ {ok_cnt}/{total} OK  ⚠️ {warn_cnt}  ❌ {err_cnt}  |  Kiểm tra lúc: {checked}", expanded=(err_cnt>0 or warn_cnt>0)):
        items = muavu_status.get("items", [])
        # Group by group
        groups = {}
        for it in items:
            g = it["group"]
            groups.setdefault(g, []).append(it)

        for grp_name, grp_items in groups.items():
            st.markdown(f"**{grp_name}**")
            rows_html = ""
            for it in grp_items:
                st_icon = it["status"][:2]  # emoji icon
                val_color = "#22c55e" if "✅" in it["status"] else ("#eab308" if "⚠️" in it["status"] else "#ef4444")
                note_txt = f"<br><small style='color:#64748b;'>{it['note']}</small>" if it.get("note") else ""
                rows_html += f"""
                <tr>
                  <td style='padding:6px 10px; color:#94a3b8; font-size:11px; width:28%;'>{it['item']}</td>
                  <td style='padding:6px 10px; font-size:10px; width:10%;'>{it['type']}</td>
                  <td style='padding:6px 10px; color:{val_color}; font-weight:600; font-size:12px; width:28%;'>{it['value']}{note_txt}</td>
                  <td style='padding:6px 10px; font-size:11px; width:20%;'>{it['status']}</td>
                  <td style='padding:6px 10px; color:#475569; font-size:10px; width:14%;'>⏱ {it['updated']}</td>
                </tr>"""

            st.markdown(f"""
            <table style='width:100%; border-collapse:collapse; margin-bottom:12px;'>
              <thead><tr style='border-bottom:1px solid #1e2d45;'>
                <th style='padding:4px 10px; font-size:10px; color:#64748b; text-align:left;'>Mục dữ liệu</th>
                <th style='padding:4px 10px; font-size:10px; color:#64748b; text-align:left;'>Loại</th>
                <th style='padding:4px 10px; font-size:10px; color:#64748b; text-align:left;'>Giá trị</th>
                <th style='padding:4px 10px; font-size:10px; color:#64748b; text-align:left;'>Trạng thái</th>
                <th style='padding:4px 10px; font-size:10px; color:#64748b; text-align:left;'>Cập nhật</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""", unsafe_allow_html=True)


# ─── PART 1: GLOBAL MACRO ────────────────────────────────────────────────────
tab_zw, tab_zc = st.tabs(["🌾 Lúa Mì (ZW)", "🌽 Ngô (ZC)"])

def render_muavu_tab(commodity):
    macro        = load_json(f"macro_scores_{commodity.lower()}.json") or {}
    macro_data   = load_json("macro_data.json") or {}
    fund         = load_json("fundamental_data.json") or {}
    cot          = load_json("cot_data.json") or {}
    ai_analysis  = load_json(f"ai_muavu_analysis_{commodity.lower()}.json") or {}
    export_s     = load_json("export_sales.json") or {}
    weather_long = load_json("weather_long.json") or {}
    weights_cfg  = load_json("macro_weights.json") or {}
    dca_targets  = weights_cfg.get("dca_targets", {})

    breakdown    = macro.get("breakdown", {})
    cot_com      = cot.get("commodities", {}).get(commodity, {})
    if not cot_com:
        for k, v in cot.get("commodities", {}).items():
            if v.get("commodity") == commodity:
                cot_com = v
                break
    price_info = get_price_info(commodity)

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

    cot_net  = cot_com.get("net_estimated", "N/A")
    cot_q    = cot_com.get("quadrant_estimated", "N/A")
    cot_up   = cot_com.get("fetched_at", cot.get("fetched_at", "—"))[:16]

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        pct_str = f"{dxy_pct:+.2f}%" if isinstance(dxy_pct, (int,float)) else ""
        pc = "#22c55e" if isinstance(dxy_pct,(int,float)) and dxy_pct<0 else "#ef4444"
        st.markdown(f"""<div class='mv-card'>
            <div class='mv-card-title'>🟢 Sức Mạnh USD (DXY)</div>
            <div class='mv-card-value'>{dxy_live}</div>
            <div class='mv-card-sub'>Điểm: {score_badge(dxy_pt)} &nbsp;<span style='color:{pc};'>{pct_str}</span></div>
            <div class='mv-card-sub'>{'DXY cao → lúa mì Mỹ đắt → Bearish XK' if commodity == 'ZW' else 'DXY cao → Ngô Mỹ đắt → Bearish XK'}</div>
            <div class='mv-card-updated'>⏱ {mac_ts}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        pc2 = "#22c55e" if isinstance(oil_pct,(int,float)) and oil_pct>=0 else "#ef4444"
        pct2 = f"{oil_pct:+.2f}%" if isinstance(oil_pct,(int,float)) else ""
        st.markdown(f"""<div class='mv-card'>
            <div class='mv-card-title'>🟢 Giá Dầu Brent</div>
            <div class='mv-card-value'>{oil_live} USD/thùng</div>
            <div class='mv-card-sub'>Điểm: {score_badge(oil_pt)} &nbsp;<span style='color:{pc2};'>{pct2}</span></div>
            <div class='mv-card-sub'>{'Dầu ảnh hưởng cước tàu & phân bón' if commodity == 'ZW' else 'Ngô chạy theo Dầu (40% SP nấu Ethanol)'}</div>
            <div class='mv-card-updated'>⏱ {mac_ts}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        cot_color = "#ef4444" if isinstance(cot_net,(int,float)) and cot_net < 0 else "#22c55e"
        cot_dot = "🟢" if cot_com else "🔴"
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
        if commodity == "ZC":
            if "Mỹ" in region_key and "Nam" not in region_key:
                return "<span style='color:#94a3b8;font-weight:700;'>NEUTRAL</span> — Đang vụ Thu Hoạch, hiện tượng El Nino ít đe dọa trực tiếp tới nguồn cung."
            if "Brazil" in region_key:
                return "<span style='color:#ef4444;font-weight:700;'>BULLISH</span> — Rủi ro khô hạn cục bộ ảnh hưởng vụ Safrinha đầu năm."
            if "Argentina" in region_key:
                return "<span style='color:#22c55e;font-weight:700;'>BEARISH</span> — Tháng 10-12 (Gieo hạt). Mưa thuận lợi cho gieo trồng ngô."
            if "Trung Quốc" in region_key or "Ukraine" in region_key:
                return "—"

        for imp in weather_long.get("impacts", []):
            if region_key in imp.get("region", ""):
                bias_col = "#ef4444" if imp["bias"]=="BULLISH" else "#22c55e"
                return f"<span style='color:{bias_col};font-weight:700;'>{imp['bias']}</span> — {imp['effect'][:80]}"
        return "—"

    if commodity == "ZW":
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
    else:
        table_html = f'''
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
      <td><span class='harvest-badge'>THU HOẠCH T9-T11</span><br>Gieo Hạt: T4-T5</td>
      <td>
        <span class='dot-green'>🟢</span> <b>Sản lượng Mỹ:</b> {score_badge(pts(f2_s))}<br>
        <small style='color:#94a3b8;'>{note(f2_s, 70)}</small>{upd(f2_s)}
        <span class='dot-green'>🟢</span> <b>Export Sales (tuần {exp_date}):</b><br>
        <b style='color:#34d399; font-size:15px;'>{net_sales} MT</b>
        <div style='font-size:9px;color:#475569;'>Cập nhật {exp_updated}</div>
        <span class='dot-red'>🔴</span> <b>Tồn kho Mỹ (Cực lớn):</b> {score_badge(pts(breakdown.get("F6", {})))}<br>
        <small style='color:#94a3b8;'>{note(breakdown.get("F6", {}), 70)}</small>
      </td>
      <td>
        <span class='dot-yellow'>🟡</span> Thời tiết (Corn Belt): {score_badge(pts(f2w_s))}<br>
        <small>Vào mùa thu hoạch, rủi ro thời tiết nội địa không còn quá đáng ngại.</small><br>
        <b>El Niño:</b> {enso_impact("Bắc Mỹ")}
      </td>
      <td>
        <span class='dot-green'>🟢</span> Dầu thô & Ethanol: {score_badge(pts(breakdown.get("F10", {})))}<br>
        <small>{note(breakdown.get("F10", {}))}</small><br>
        <span class='dot-green'>🟢</span> DXY {dxy_live} → Cản trở XK.
      </td>
    </tr>

    <tr>
      <td><div class='region-flag'>🇧🇷</div><div class='region-header'>Nam Mỹ<br>(Brazil)</div></td>
      <td><span class='harvest-badge'>SAFRINHA T6-T8</span><br>Gieo Vụ 2: T1-T2<br>Vụ 1 (nhỏ): T9-T11</td>
      <td>
        <span class='dot-red'>🔴</span> Nguồn cung Nam Mỹ: {score_badge(pts(f4s_s))}<br>
        <small>{note(f4s_s)}</small>{upd(f4s_s)}
      </td>
      <td>
        <span class='dot-yellow'>🟡</span> Thời tiết Nam Mỹ: {score_badge(pts(f4_s))}<br>
        <small>El Nino/La Nina cực kỳ quan trọng cho vụ Safrinha đầu năm.</small><br>
        <b>El Niño:</b> {enso_impact("Nam Mỹ")}
      </td>
      <td>
        <span class='dot-red'>🔴</span> Mất thị phần Trung Quốc: {score_badge(pts(f3_s))}<br>
        <small>{note(f3_s, 70)}</small>
      </td>
    </tr>

    <tr>
      <td><div class='region-flag'>🇦🇷</div><div class='region-header'>Nam Mỹ<br>(Argentina)</div></td>
      <td><span class='harvest-badge'>THU HOẠCH T3-T5</span><br>Gieo Hạt: T9-T11</td>
      <td>
        <span class='dot-yellow'>🟡</span> Thuộc chung Cung Nam Mỹ: {score_badge(pts(f4s_s))}<br>
        <small>Argentina là nhà XK lớn thứ 3. Ảnh hưởng mạnh đến giá đầu năm.</small>
      </td>
      <td>
        <b>El Niño:</b> {enso_impact("Nam Mỹ")}<br>
        <small>La Nina gây hạn hán nặng cho Argentina (Bullish), El Nino mang mưa tốt (Bearish).</small>
      </td>
      <td>
        <span class='dot-yellow'>🟡</span> Rủi ro Dịch Bệnh / Thuế XK<br>
        <small>Dịch bệnh rụng lá (Spiroplasma) hoặc thay đổi thuế XK có thể gây sốc cung.</small>
      </td>
    </tr>

    <tr>
      <td><div class='region-flag'>🇨🇳🇺🇦</div><div class='region-header'>Trung Quốc &<br>Ukraine</div></td>
      <td><span class='harvest-badge'>THU HOẠCH T9-T10</span><br>TQ Nhập khẩu đỉnh T4-T8</td>
      <td>
        <span class='dot-yellow'>🟡</span> Biển Đen (Ukraine XK): {score_badge(pts(f1_s))}<br>
        <small>{note(f1_s, 70)}</small>{upd(f1_s)}
      </td>
      <td>
        <b>El Niño:</b> {enso_impact("Châu Á")}<br>
        <small>Mùa vụ TQ ảnh hưởng bởi lũ lụt hoặc hạn hán cục bộ.</small>
      </td>
      <td>
        <span class='dot-yellow'>🟡</span> Logistics Biển Đen: {score_badge(pts(f8_s))}<br>
        <small>{note(f8_s, 60)}</small><br>
        <span class='dot-yellow'>🟡</span> Nhu cầu (F12): {score_badge(pts(breakdown.get("F12", {})))}
      </td>
    </tr>

    </tbody>
    </table>
    '''

    st.markdown(table_html, unsafe_allow_html=True)


    # ─── PART 3: AI CONCLUSION + DCA BOX ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🤖 PHẦN 3: KẾT LUẬN & KẾ HOẠCH DCA (AI ANALYSIS)")

    # DCA Snapshot Box
    close   = price_info.get("close", "N/A")
    high1m  = price_info.get("high_1m", "N/A")
    low1m   = price_info.get("low_1m", "N/A")
    s1      = price_info.get("s1", "N/A")
    s2      = price_info.get("s2", "N/A")
    r1      = price_info.get("r1", "N/A")
    atr     = price_info.get("atr", "N/A")
    rsi     = price_info.get("rsi", "N/A")
    zw_date = price_info.get("date", "—")

    pct_1m = ((close - low1m) / (high1m - low1m) * 100) if isinstance(close,(int,float)) and isinstance(high1m,(int,float)) and high1m!=low1m else None

    if commodity == "ZW":
        sym_text = f"THÔNG SỐ GIÁ ZW (ZWZ26) - Cập nhật: {zw_date}"
        dca_time = "Cuối T11 - Giữa T12/2026"
        dca_reason = "Khi áp lực xả hàng Úc+Argentina đạt đỉnh, El Niño bắt đầu ảnh hưởng Q1/2027"
        s1_v = s1 if isinstance(s1, (int,float)) else 600
        l1_v = low1m if isinstance(low1m, (int,float)) else s1_v+15
        z1_price = f"{min(s1_v, l1_v):.0f} - {max(s1_v, l1_v):.0f}¢"
        macro_z1 = dca_targets.get(commodity, {}).get("zone1", "550 - 580¢")
    else:
        sym_text = f"THÔNG SỐ GIÁ ZC (ZCZ26) - Cập nhật: {zw_date}"
        dca_time = "Giai đoạn T10 - T11/2026"
        dca_reason = "Khi áp lực mùa vụ thu hoạch tại Mỹ đạt đỉnh điểm (Nguồn cung bung ra mạnh nhất)"
        s1_v = s1 if isinstance(s1, (int,float)) else 400
        l1_v = low1m if isinstance(low1m, (int,float)) else s1_v+15
        z1_price = f"{min(s1_v, l1_v):.0f} - {max(s1_v, l1_v):.0f}¢"
        macro_z1 = dca_targets.get(commodity, {}).get("zone1", "400 - 420¢")


    col_a, col_b = st.columns([1, 1])
    with col_a:
        rsi_color = "#22c55e" if isinstance(rsi,(int,float)) and rsi < 35 else ("#ef4444" if isinstance(rsi,(int,float)) and rsi > 65 else "#eab308")
        pct_bar = f"({pct_1m:.0f}% trong biên độ 1 tháng)" if pct_1m is not None else ""
        st.markdown(f"""
        <div class='dca-box'>
          <div style='font-size:11px;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;'>
            📊 {sym_text}
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
            <div style='font-size:15px;font-weight:700;color:#86efac;'>{dca_time}</div>
            <div style='font-size:11px;color:#94a3b8;'>{dca_reason}</div>
          </div>
          <div class='dca-zone' style='border-color:#f59e0b; margin-bottom:8px;'>
            <div style='font-size:10px;color:#64748b;'>🎯 VÙNG GOM VĨ MÔ (Cấu trúc Dài hạn)</div>
            <div style='font-size:18px;font-weight:800;color:#fde68a;'>{macro_z1}</div>
            <div style='font-size:11px;color:#94a3b8;'>Đáy cấu trúc Vĩ mô / Giá thành sản xuất (Cấu hình tùy chỉnh)</div>
          </div>
          <div class='dca-zone' style='border-color:#94a3b8;'>
            <div style='font-size:10px;color:#64748b;'>⚡ VÙNG GOM KỸ THUẬT (Biến động Ngắn hạn)</div>
            <div style='font-size:18px;font-weight:800;color:#cbd5e1;'>{z1_price}</div>
            <div style='font-size:11px;color:#94a3b8;'>Biến động Real-time: Hỗ trợ S1 + Đáy 1 tháng gần nhất</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if ai_analysis and "analysis" in ai_analysis:
        st.caption(f"⏱ Lần phân tích AI cuối: **{ai_analysis.get('last_updated', '')}** — Ấn 'Cập Nhật Mùa Vụ' để làm mới.")
        st.markdown(ai_analysis["analysis"])
    else:
        st.warning("Chưa có bản phân tích AI. Ấn nút **'🔄 Cập Nhật Mùa Vụ (AI)'** ở cột trái.")


with tab_zw:
    render_muavu_tab("ZW")
with tab_zc:
    render_muavu_tab("ZC")
