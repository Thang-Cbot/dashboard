"""
pages/2_Profiles.py — Hồ Sơ Chi Tiết Từng Mã ZC / ZW
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import streamlit as st
import pandas as pd
from pathlib import Path
import importlib
import components.charts as charts
importlib.reload(charts)
from components.charts import render_candlestick

st.set_page_config(page_title="Hồ Sơ Mã — CBOT", page_icon="📈", layout="wide")

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

COMMODITIES  = {"🌽 ZC — Ngô": "ZC", "🌾 ZW — Lúa Mì": "ZW"}
CONTRACT_TYPES = {"Active (Giao dịch chính)": "active", "Swing (Trung hạn)": "swing", "DCA (Dài hạn)": "dca"}
CFTC_TO_CODE = {"002602": "ZC", "001602": "ZW"}

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


def get_cot_by_code(cot_data, code):
    if not cot_data:
        return {}
    if code in cot_data:
        return cot_data[code]
    commodities = cot_data.get("commodities", cot_data)
    for k, v in commodities.items():
        if isinstance(v, dict) and v.get("commodity") == code:
            return v
    return {}


# ── CSS & nav ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1629; }
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 220px !important; max-width: 220px !important; width: 220px !important; }
[data-testid="stSidebarNav"] { display: none !important; }
.card { background: #1a2035; border: 1px solid #2a3a5c; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.kv { margin-bottom:8px; }
.kv .lbl { font-size:11px; color:#64748b; }
.kv .val { font-size:13px; color:#e2e8f0; font-weight:600; }
</style>""", unsafe_allow_html=True)

st.sidebar.page_link("app.py",              label="🏠 Trang Chủ")
st.sidebar.page_link("pages/1_Overview.py", label="📊 Tổng Quan")
st.sidebar.page_link("pages/2_Profiles.py", label="📈 Hồ Sơ Từng Mã")
st.sidebar.page_link("pages/3_News.py",     label="📰 Báo Cáo USDA & Tin Tức")
st.sidebar.page_link("pages/4_Weather.py",  label="🌤️ Thời Tiết")
st.sidebar.page_link("pages/5_AgriMap.py",  label="🗺️ Bản Đồ Thời Tiết & ENSO")
st.sidebar.page_link("pages/6_MuaVu.py",   label="🌾 Mùa Vụ 2026")

st.markdown("## 📈 Hồ Sơ Chi Tiết Từng Mã")

# Thêm nút Làm mới trạng thái
if st.button("🧹 LÀM MỚI TRẠNG THÁI", key="refresh_profile", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

c1, c2 = st.columns([1, 1])
with c1:
    selected_name = st.selectbox("Mã hàng hóa", list(COMMODITIES.keys()), index=1)
with c2:
    selected_contract = st.selectbox("Loại hợp đồng", list(CONTRACT_TYPES.keys()))

code   = COMMODITIES[selected_name]
suffix = CONTRACT_TYPES[selected_contract]

fund = load_json("fundamental_data.json")
cot  = load_json("cot_data.json")
meta = load_json("contracts_meta.json")

data      = fund.get(code, {})
cot_data  = get_cot_by_code(cot, code)
meta_data = meta.get(code, {})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Biểu đồ nến ──
render_candlestick(st, code, suffix, n_candles=120)

# ── 3 cột thông tin ──
col1, col2, col3 = st.columns(3)

# Cột 1: Chiến lược
with col1:
    swing_contract = meta_data.get("swing", {}).get("ticker", "")
    swing_month = meta_data.get("swing", {}).get("month", "")
    dca_contract = meta_data.get("dca", {}).get("ticker", "")
    month_str = f"(Kỳ Tháng {swing_month})" if swing_month else ""
    
    # Load TA levels from CSV
    s1, s2, r1, r2 = "—", "—", "—", "—"
    csv_path = DATA_OUTPUT / f"{code}_{suffix}_H1.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                last_row = df.iloc[-1]
                s1 = f"{last_row.get('S1', 0):.2f}"
                s2 = f"{last_row.get('S2', 0):.2f}"
                r1 = f"{last_row.get('R1', 0):.2f}"
                r2 = f"{last_row.get('R2', 0):.2f}"
        except Exception:
            pass
            
    st.markdown(f"<div class='card'><div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;'>📋 CHIẾN LƯỢC — {swing_contract} {month_str}</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; margin-bottom:12px; background:#0f1629; padding:8px; border-radius:6px; border: 1px solid #1e2d45;'>
        <div style='text-align:center; flex:1; border-right: 1px solid #1e2d45;'>
            <div style='font-size:10px; color:#ef4444; font-weight:700;'>KHÁNG CỰ (R1/R2)</div>
            <div style='font-size:13px; font-weight:700; color:#cbd5e1; margin-top:2px;'>{r1} / {r2}</div>
        </div>
        <div style='text-align:center; flex:1;'>
            <div style='font-size:10px; color:#22c55e; font-weight:700;'>HỖ TRỢ (S1/S2)</div>
            <div style='font-size:13px; font-weight:700; color:#cbd5e1; margin-top:2px;'>{s1} / {s2}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    trend_str = data.get("swing_trend", "").lower()
    is_short = "giảm" in trend_str or "bán" in trend_str or "short" in trend_str

    prefix = "swing_short" if is_short else "swing_long"
    dir_label = "(Short)" if is_short else "(Long)"

    for label, key in [
        ("Xu hướng Swing",   "swing_trend"),
        ("Intraday",         "intraday_strategy"),
        (f"Entry Zone {dir_label}", f"{prefix}_entry"),
        (f"Stop Loss {dir_label}",  f"{prefix}_sl"),
        (f"Take Profit {dir_label}",f"{prefix}_tp"),
        ("DCA Zone",         "dca_brackets"),
    ]:
        val = data.get(key, "—") or "—"
        if key == "dca_brackets" and dca_contract:
            val = f"{val} <br><span style='font-size:10px;color:#f59e0b;font-weight:600;'>Mã áp dụng: {dca_contract}</span>"
            
        # Bỏ rút gọn 80 ký tự để hiển thị đầy đủ logic SL/TP
        val_disp = str(val)
        st.markdown(f"""<div class='kv'>
            <div class='lbl'>{label}</div>
            <div class='val'>{val_disp}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Cột 2: Cơ bản mùa vụ
with col2:
    st.markdown("<div class='card'><div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;'>🌾 CƠ BẢN MÙA VỤ</div>", unsafe_allow_html=True)
    for label, key in [
        ("Gieo trồng Mỹ",   "us_planting"),
        ("Thu hoạch Mỹ",    "harvest_progress"),
        ("Chất lượng G/E",  "crop_condition"),
    ]:
        meta = data.get(key, {})
        if isinstance(meta, dict):
            curr = meta.get("latest", "—") or "—"
            prev = meta.get("previous", "—") or "—"
            date = meta.get("latest_date", "")
        else:
            curr, prev, date = str(meta) if meta else "—", "—", ""
        st.markdown(f"""
        <div style='background:#0f1629; border-radius:6px; padding:10px; margin-bottom:8px;'>
            <div style='font-size:11px; color:#64748b; margin-bottom:4px;'>{label}</div>
            <div style='display:flex; gap:12px;'>
                <div style='flex:1;'>
                    <div style='font-size:10px; color:#475569;'>Kỳ trước</div>
                    <div style='font-size:12px; color:#94a3b8;'>{prev}</div>
                </div>
                <div style='flex:1;'>
                    <div style='font-size:10px; color:#166534;'>Hiện tại</div>
                    <div style='font-size:12px; color:#22c55e; font-weight:700;'>{curr}</div>
                </div>
            </div>
            {f'<div style="font-size:10px;color:#374151;margin-top:4px;">{date}</div>' if date else ''}
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Cột 3: COT + Xuất khẩu
with col3:
    st.markdown("<div class='card'><div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;'>📊 COT & XUẤT KHẨU</div>", unsafe_allow_html=True)

    # COT
    if cot_data:
        net  = cot_data.get("net_position", 0) or 0
        chg  = cot_data.get("change", 0) or 0
        quad = cot_data.get("quadrant", cot_data.get("quadrant_label", "—"))
        action = cot_data.get("action", "")
        nc   = "#22c55e" if chg > 0 else "#ef4444"
        arrow = "▲" if chg > 0 else "▼"
        st.markdown(f"""
        <div style='background:#0f1629; border-radius:6px; padding:10px; margin-bottom:8px;'>
            <div style='font-size:11px; color:#64748b;'>COT Managed Money</div>
            <div style='font-size:18px; font-weight:700; color:{nc}; margin:4px 0;'>{net:+,} HD</div>
            <div style='font-size:11px; color:{nc};'>{arrow} {abs(chg):,} HD tuần này</div>
            <div style='font-size:11px; color:#94a3b8; margin-top:4px;'>{quad}</div>
            <div style='font-size:11px; color:#64748b; margin-top:2px;'>{action[:60] if action else ""}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:12px;color:#64748b;padding:8px;'>Chưa có dữ liệu COT.</div>", unsafe_allow_html=True)

    # Export Sales
    exp = data.get("exports", {})
    if exp:
        curr = exp.get("latest", "—") or "—"
        prev = exp.get("previous", "—") or "—"
        pct  = exp.get("pct_change", 0) or 0
        logic = exp.get("logic", "")
        ec = "#22c55e" if pct > 0 else "#ef4444"
        st.markdown(f"""
        <div style='background:#0f1629; border-radius:6px; padding:10px;'>
            <div style='font-size:11px; color:#64748b;'>Xuất Khẩu Tuần Này</div>
            <div style='font-size:12px; color:#22c55e; font-weight:600; margin:4px 0;'>{curr}</div>
            <div style='font-size:11px; color:#64748b;'>Kỳ trước: <span style="color:#94a3b8;">{prev}</span></div>
            <div style='font-size:13px; color:{ec}; font-weight:700; margin-top:4px;'>Δ {pct:+.1f}%</div>
            <div style='font-size:10px; color:#475569; margin-top:4px;'>{logic[:80] if logic else ""}...</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:12px;color:#64748b;padding:8px;'>Chưa có dữ liệu xuất khẩu.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Smart Money Matrix & Thanh Khoản ──
st.markdown("<div class='card'><div style='font-size:14px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;text-transform:uppercase;'>🧠 SMART MONEY MATRIX & DÒNG TIỀN (VOLUME + OI)</div>", unsafe_allow_html=True)

c_cot, c_vol = st.columns([1.5, 1], gap="large")

with c_cot:
    if cot_data:
        report_date = cot_data.get("report_date", "—")
        quadrant = cot_data.get("quadrant", "—")
        action = cot_data.get("action", "—")
        net = cot_data.get("net_position", 0)
        chg = cot_data.get("change", 0)
        
        quad_color = "#ef4444" if "Q4" in quadrant or "Q3" in quadrant or "SHORT" in quadrant else "#22c55e"
        chg_str = f"+{chg:,}" if chg > 0 else f"{chg:,}"
        
        st.markdown(f'''
        <style>
        .cot-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 0; }}
        .cot-table th {{ background: #1e293b; color: #cbd5e1; padding: 10px; text-align: left; border: 1px solid #334155; }}
        .cot-table td {{ padding: 10px; border: 1px solid #334155; color: #e2e8f0; }}
        .cot-table tr:nth-child(even) {{ background: #0f1629; }}
        </style>
        <table class="cot-table">
            <tr>
                <th style="width: 32%;">Báo cáo COT Managed Money</th>
                <th style="width: 32%;">{selected_name}</th>
                <th style="width: 36%;">Đánh giá & Hành động</th>
            </tr>
            <tr>
                <td><b>Ngày Báo Cáo</b></td>
                <td><b>{report_date}</b></td>
                <td style="color:#94a3b8;">Cập nhật mới nhất từ CFTC</td>
            </tr>
            <tr>
                <td><b>Trạng Thái Matrix</b></td>
                <td style="color:{quad_color}; font-weight:700;">{quadrant}</td>
                <td style="color:#cbd5e1; font-style:italic;">{action}</td>
            </tr>
            <tr>
                <td><b>Net Position</b></td>
                <td><b>{net:,}</b></td>
                <td style="color:#94a3b8;">Hợp đồng (<span style="color:#22c55e;font-weight:bold;">Long</span> - <span style="color:#ef4444;font-weight:bold;">Short</span>)</td>
            </tr>
            <tr>
                <td><b>Thay đổi Tuần qua</b></td>
                <td><b>{chg_str}</b></td>
                <td style="color:#94a3b8;">Hợp đồng thay đổi so với tuần trước</td>
            </tr>
        </table>
        ''', unsafe_allow_html=True)
    else:
        st.info("Chưa có dữ liệu COT cho mã này.")

with c_vol:
    liq = meta_data.get("liquidity", {})
    if liq:
        vol_today = liq.get("today_volume", 0)
        vol_prev = liq.get("prev_volume", 0)
        oi_today = liq.get("today_oi", 0)
        oi_prev = liq.get("prev_oi", 0)
        trend = liq.get("trend", "—")
        logic = liq.get("logic", "—")
        
        vol_chg = vol_today - vol_prev
        oi_chg = oi_today - oi_prev
        vol_pct = (vol_chg / vol_prev * 100) if vol_prev else 0
        oi_pct = (oi_chg / oi_prev * 100) if oi_prev else 0
        
        vol_color = "#22c55e" if vol_chg >= 0 else "#ef4444"
        oi_color = "#22c55e" if oi_chg >= 0 else "#ef4444"
        vol_arrow = "▲" if vol_chg >= 0 else "▼"
        oi_arrow = "▲" if oi_chg >= 0 else "▼"
        
        st.markdown(f"""
        <div style='background:#0f1629; border-radius:8px; padding:14px; border:1px solid #1e2d45; height: 100%;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:12px;'>
                <div style='flex:1;'>
                    <div style='font-size:11px; color:#64748b;'>Khối lượng (Volume)</div>
                    <div style='font-size:17px; font-weight:700; color:#e2e8f0;'>{vol_today:,.0f}</div>
                    <div style='font-size:11px; font-weight:600; color:{vol_color}; margin-top:2px;'>{vol_arrow} {abs(vol_pct):.1f}%</div>
                </div>
                <div style='flex:1;'>
                    <div style='font-size:11px; color:#64748b;'>Hợp đồng mở (OI)</div>
                    <div style='font-size:17px; font-weight:700; color:#e2e8f0;'>{oi_today:,.0f}</div>
                    <div style='font-size:11px; font-weight:600; color:{oi_color}; margin-top:2px;'>{oi_arrow} {abs(oi_pct):.1f}%</div>
                </div>
            </div>
            <hr style='border-color:#1e2d45; margin:12px 0;'>
            <div style='font-size:11px; font-weight:700; color:#94a3b8; margin-bottom:6px; letter-spacing:0.5px;'>🔍 XU HƯỚNG DÒNG TIỀN:</div>
            <div style='font-size:13px; font-weight:700; color:#38bdf8; margin-bottom:6px;'>{trend}</div>
            <div style='font-size:12px; color:#cbd5e1; line-height:1.6;'>{logic}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Chưa có dữ liệu Volume & OI.")

st.markdown("</div>", unsafe_allow_html=True)

# ── Swing & DCA Logic ──
swing_logic = data.get("swing_logic", "")
dca_logic   = data.get("dca_logic", "")
if swing_logic or dca_logic:
    lc1, lc2 = st.columns(2)
    if swing_logic:
        with lc1:
            st.markdown(f"""<div class='card' style='border-left:3px solid #60a5fa;'>
                <div style='font-size:12px;font-weight:700;color:#60a5fa;margin-bottom:6px;'>💡 Phân Tích Swing</div>
                <div style='font-size:12px;color:#94a3b8;line-height:1.6;'>{swing_logic}</div>
            </div>""", unsafe_allow_html=True)
    if dca_logic:
        with lc2:
            dca_brackets = data.get("dca_brackets", "—")
            st.markdown(f"""<div class='card' style='border-left:3px solid #34d399;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <div style='font-size:12px;font-weight:700;color:#34d399;'>📦 Chiến Lược DCA</div>
                    <div style='font-size:10px;font-weight:700;color:#fbbf24;background:#451a03;padding:2px 6px;border-radius:4px;'>Mã: {dca_contract}</div>
                </div>
                <div style='font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:8px;'>Vùng mua/bán gom: <span style='color:#34d399;'>{dca_brackets}</span></div>
                <div style='font-size:12px;color:#94a3b8;line-height:1.6;'>{dca_logic}</div>
            </div>""", unsafe_allow_html=True)
