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
from components.charts import render_candlestick, get_smc_zones_for_display

st.set_page_config(page_title="Hồ Sơ Mã — CBOT", page_icon="favicon.png", layout="wide")

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
[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 260px !important; max-width: 260px !important; width: 260px !important; }
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
all_signals = load_json("last_signals.json")
live_sig    = all_signals.get(code, {})

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ── VOLATILITY DASHBOARD (vị trí đầu trang) ──
# ═══════════════════════════════════════════════════════════
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.markdown("""
<div style='font-size:16px; font-weight:800; color:#e2e8f0; letter-spacing:0.5px; margin-bottom:4px;'>
    📊 PHÂN TÍCH BIÊN ĐỘ GIÁ (VOLATILITY DASHBOARD)
</div>
<div style='font-size:12px; color:#64748b; margin-bottom:12px;'>
    Độ lệch Open↔Close và High↔Low từng ngày | 3 tuần gần nhất + Dự báo xu thế
</div>
""", unsafe_allow_html=True)

_csv_vol_path = DATA_OUTPUT / f"{code}_{suffix}_H1.csv"
if _csv_vol_path.exists():
    try:
        _dfv = pd.read_csv(_csv_vol_path)
        _dfv.columns = [c.strip() for c in _dfv.columns]
        _dcol = next((c for c in _dfv.columns if c.lower() in ['time','datetime','date','timestamp']), None)
        if _dcol:
            _dfv[_dcol] = pd.to_datetime(_dfv[_dcol], errors='coerce')
            _dfv = _dfv.dropna(subset=[_dcol]).rename(columns={_dcol: "Datetime"})

        _dfv["Date"] = _dfv["Datetime"].dt.date
        _daily = _dfv.groupby("Date").agg(
            Open=("Open", "first"), High=("High", "max"),
            Low=("Low", "min"), Close=("Close", "last"),
            Volume=("Volume", "sum"), ATR=("ATR", "mean"),
        ).reset_index()
        _daily["Date"] = pd.to_datetime(_daily["Date"])
        _daily = _daily[_daily["Date"].dt.weekday < 5].tail(15).reset_index(drop=True)

        _daily["OC_Delta"]  = (_daily["Close"] - _daily["Open"]).round(2)
        _daily["HL_Range"]  = (_daily["High"]  - _daily["Low"]).round(2)
        _daily["OC_Abs"]    = _daily["OC_Delta"].abs()
        _daily["Day_Label"] = _daily["Date"].dt.strftime("%a %d/%m")

        _idx_max = _daily["HL_Range"].idxmax()
        _idx_min = _daily["HL_Range"].idxmin()
        _day_max = _daily.loc[_idx_max, "Day_Label"]; _range_max = _daily.loc[_idx_max, "HL_Range"]
        _day_min = _daily.loc[_idx_min, "Day_Label"]; _range_min = _daily.loc[_idx_min, "HL_Range"]

        _last_date  = _daily["Date"].max()
        _week_start = _last_date - pd.Timedelta(days=_last_date.weekday())
        _tw = _daily[_daily["Date"] >= _week_start]
        _woc  = _tw["OC_Delta"].sum().round(2)
        _whl  = _tw["HL_Range"].sum().round(2)
        _whlm = _tw["HL_Range"].mean().round(2)
        _wg   = (_tw["OC_Delta"] > 0).sum()
        _wr   = (_tw["OC_Delta"] < 0).sum()

        _ratr = _daily["ATR"].tail(5).mean()
        _patr = _daily["ATR"].head(5).mean()
        _atr_trend = "📈 Tăng" if _ratr > _patr * 1.05 else ("📉 Giảm" if _ratr < _patr * 0.95 else "➡️ Ổn định")
        _l3   = _daily["OC_Delta"].tail(3).tolist()
        _mscore = sum(1 if x > 0 else -1 for x in _l3)
        _mstr = "🟢 Bullish (3 ngày đều tăng)" if _mscore == 3 else \
                "🟢 Bullish nhẹ" if _mscore > 0 else \
                "🔴 Bearish nhẹ" if _mscore < 0 else "⚪ Trung lập"
        _close_now = _daily["Close"].iloc[-1]
        _r1e = round(_close_now + _ratr, 2); _s1e = round(_close_now - _ratr, 2)
        _exp = round(_ratr, 2)

        # Block 1 — 5 thẻ tóm tắt tuần
        _wkc = "#22c55e" if _woc >= 0 else "#ef4444"
        _vc1, _vc2, _vc3, _vc4, _vc5 = st.columns(5)
        for _col_w, _lbl, _val, _clr in [
            (_vc1, "Tổng ΔOC Tuần",        f"{'+' if _woc>=0 else ''}{_woc}¢",   _wkc),
            (_vc2, "Tổng Biên Độ HL",       f"{_whl}¢",                            "#f59e0b"),
            (_vc3, "Biên Độ TB/Ngày",       f"{_whlm}¢",                           "#94a3b8"),
            (_vc4, "🔥 Ngày Biến Động Cao",  f"{_day_max} ({_range_max}¢)",        "#fb923c"),
            (_vc5, "🧊 Ngày Biến Động Thấp", f"{_day_min} ({_range_min}¢)",        "#a78bfa"),
        ]:
            _col_w.markdown(
                f"<div style='background:#1a2035;border-radius:10px;padding:12px;text-align:center;"
                f"border:1px solid #2a3a5c;height:76px;display:flex;flex-direction:column;justify-content:center;'>"
                f"<div style='font-size:10px;color:#64748b;font-weight:600;margin-bottom:4px;'>{_lbl}</div>"
                f"<div style='font-size:14px;font-weight:800;color:{_clr};'>{_val}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Block 2 — Biểu đồ 2 hàng
        _bar_oc = ["#22c55e" if x >= 0 else "#ef4444" for x in _daily["OC_Delta"]]
        _fig_v = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                               row_heights=[0.55, 0.45])
        _fig_v.add_trace(go.Bar(
            x=_daily["Day_Label"], y=_daily["HL_Range"], name="High-Low Range",
            marker_color=["#fb923c" if i==_idx_max else "#a78bfa" if i==_idx_min else "#38bdf8" for i in range(len(_daily))],
            text=[f"{v:.1f}¢" for v in _daily["HL_Range"]], textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
        ), row=1, col=1)
        _fig_v.add_hline(y=_daily["ATR"].mean(), row=1, col=1, line_dash="dash", line_color="#f59e0b",
                         line_width=1.5, annotation_text=f"ATR TB: {_daily['ATR'].mean():.2f}¢",
                         annotation_font=dict(size=10, color="#f59e0b"))
        _fig_v.add_trace(go.Bar(
            x=_daily["Day_Label"], y=_daily["OC_Delta"], name="Open→Close",
            marker_color=_bar_oc,
            text=[f"{'+' if v>=0 else ''}{v:.1f}¢" for v in _daily["OC_Delta"]],
            textposition="outside", textfont=dict(size=10),
        ), row=2, col=1)
        _fig_v.add_hline(y=0, row=2, col=1, line_color="#475569", line_width=1)
        _fig_v.update_layout(
            paper_bgcolor="#0f1629", plot_bgcolor="#0f1629",
            font=dict(color="#e2e8f0", family="Inter"),
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(gridcolor="#1e2d45"), yaxis=dict(gridcolor="#1e2d45", title="¢"),
            xaxis2=dict(gridcolor="#1e2d45"), yaxis2=dict(gridcolor="#1e2d45", title="¢"),
            showlegend=False, height=440,
        )
        st.plotly_chart(_fig_v, use_container_width=True)

        # Block 3 — Bảng chi tiết
        st.markdown("<div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:0.5px;margin-bottom:8px;'>📋 BẢNG CHI TIẾT TỪNG NGÀY</div>", unsafe_allow_html=True)
        _th = ("<table style='width:100%;border-collapse:collapse;font-size:12px;font-family:Inter,sans-serif;'>"
               "<thead><tr style='background:#1e293b;color:#94a3b8;'>"
               "<th style='padding:7px 10px;text-align:left;border-bottom:1px solid #334155;'>Ngày</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Open</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>High</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Low</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Close</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>ΔOC</th>"
               "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>HL Range</th>"
               "<th style='padding:7px 10px;text-align:center;border-bottom:1px solid #334155;'>Nến</th>"
               "</tr></thead><tbody>")
        for _i, _r in _daily.iterrows():
            _oc_c = "#22c55e" if _r["OC_Delta"] >= 0 else "#ef4444"
            _sgn  = "+" if _r["OC_Delta"] >= 0 else ""
            _rbg  = "background:#0c1a12;" if _i==_idx_max else "background:#1a0c1a;" if _i==_idx_min else ""
            _bdg  = " 🔥" if _i==_idx_max else " 🧊" if _i==_idx_min else ""
            _cnd  = "🟢" if _r["OC_Delta"] >= 0 else "🔴"
            _th += (f"<tr style='border-bottom:1px solid #1e2d45;{_rbg}'>"
                    f"<td style='padding:6px 10px;color:#cbd5e1;font-weight:600;'>{_r['Day_Label']}{_bdg}</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:#94a3b8;'>{_r['Open']:.2f}</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:#fb923c;'>{_r['High']:.2f}</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:#a78bfa;'>{_r['Low']:.2f}</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:#e2e8f0;font-weight:700;'>{_r['Close']:.2f}</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:{_oc_c};font-weight:700;'>{_sgn}{_r['OC_Delta']:.2f}¢</td>"
                    f"<td style='padding:6px 10px;text-align:right;color:#38bdf8;font-weight:700;'>{_r['HL_Range']:.2f}¢</td>"
                    f"<td style='padding:6px 10px;text-align:center;'>{_cnd}</td></tr>")
        _woc_c = "#22c55e" if _woc >= 0 else "#ef4444"
        _woc_s = "+" if _woc >= 0 else ""
        _th += (f"<tr style='background:#1e293b;border-top:2px solid #334155;font-weight:700;'>"
                f"<td style='padding:7px 10px;color:#f59e0b;'>📅 TUẦN NÀY</td>"
                f"<td></td><td></td><td></td><td></td>"
                f"<td style='padding:7px 10px;text-align:right;color:{_woc_c};'>{_woc_s}{_woc:.2f}¢</td>"
                f"<td style='padding:7px 10px;text-align:right;color:#f59e0b;'>{_whl:.2f}¢</td>"
                f"<td style='padding:7px 10px;text-align:center;color:#94a3b8;'>🟢×{_wg} 🔴×{_wr}</td></tr>"
                "</tbody></table>")
        st.markdown(_th, unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Block 4 — Dự báo xu thế
        _fc  = "#22c55e" if _mscore > 0 else "#ef4444" if _mscore < 0 else "#94a3b8"
        _vtc = "#ef4444" if "Tăng" in _atr_trend else "#22c55e" if "Giảm" in _atr_trend else "#f59e0b"
        st.markdown(
            f"<div style='background:#1a2035;border-radius:12px;padding:14px;border:1px solid #2a3a5c;'>"
            f"<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.5px;margin-bottom:10px;'>"
            f"🔮 DỰ BÁO XU THẾ (ATR & Momentum 3 ngày gần nhất)</div>"
            f"<div style='display:flex;gap:12px;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:150px;background:#0f1629;border-radius:8px;padding:10px;border-left:3px solid {_fc};'>"
            f"<div style='font-size:10px;color:#64748b;margin-bottom:3px;'>MOMENTUM GIÁ</div>"
            f"<div style='font-size:13px;font-weight:700;color:{_fc};'>{_mstr}</div></div>"
            f"<div style='flex:1;min-width:150px;background:#0f1629;border-radius:8px;padding:10px;border-left:3px solid {_vtc};'>"
            f"<div style='font-size:10px;color:#64748b;margin-bottom:3px;'>BIẾN ĐỘNG (ATR)</div>"
            f"<div style='font-size:13px;font-weight:700;color:{_vtc};'>{_atr_trend} | {_ratr:.2f}¢</div></div>"
            f"<div style='flex:1;min-width:150px;background:#0f1629;border-radius:8px;padding:10px;border-left:3px solid #38bdf8;'>"
            f"<div style='font-size:10px;color:#64748b;margin-bottom:3px;'>VÙNG KỲ VỌNG NGÀY TỚI</div>"
            f"<div style='font-size:13px;font-weight:700;color:#38bdf8;'>🟢 {_r1e}¢ &nbsp;|&nbsp; 🔴 {_s1e}¢</div>"
            f"<div style='font-size:10px;color:#475569;margin-top:2px;'>±{_exp:.2f}¢ (1× ATR)</div></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )
    except Exception as _ve:
        st.warning(f"Lỗi Volatility Dashboard: {_ve}")
else:
    st.info("Chưa có dữ liệu H1 để phân tích biên độ giá.")

st.markdown("<hr style='border-color:#1e2d45;margin:18px 0;'>", unsafe_allow_html=True)

# ── 3 cột thông tin ──
col1, col2, col3 = st.columns(3)

# Cột 1: Chiến lược
with col1:
    swing_contract = meta_data.get("swing", {}).get("ticker", "")
    swing_month = meta_data.get("swing", {}).get("month", "")
    dca_contract = meta_data.get("dca", {}).get("ticker", "")
    month_str = f"(Kỳ Tháng {swing_month})" if swing_month else ""

    # ── Tính SMC Liquidity Zones thực tế ──
    smc_zones = get_smc_zones_for_display(code, suffix)
    pdh_val = f"{smc_zones['pdh']:.2f}" if smc_zones.get("pdh") else "—"
    pdl_val = f"{smc_zones['pdl']:.2f}" if smc_zones.get("pdl") else "—"
    fvg_list = smc_zones.get("fvg_list", [])

    st.markdown(f"<div class='card'><div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;'>📋 CHIẾN LƯỢC — {swing_contract} {month_str}</div>", unsafe_allow_html=True)

    # ── Bảng SMC Liquidity Zones — render từng phần riêng biệt ──
    st.markdown(f"""
    <div style='background:#0f1629; border-radius:8px; padding:10px; margin-bottom:4px; border:1px solid #1e2d45;'>
        <div style='font-size:10px; color:#94a3b8; font-weight:700; letter-spacing:0.5px; margin-bottom:8px;'>📍 VÙNG THANH KHOẢN SMC</div>
        <div style='display:flex; gap:8px; margin-bottom:8px;'>
            <div style='flex:1; text-align:center; background:#1a1234; border:1px solid #7c3aed; border-radius:6px; padding:6px;'>
                <div style='font-size:10px; color:#a78bfa; font-weight:700;'>PDH (Đỉnh hôm qua)</div>
                <div style='font-size:14px; font-weight:800; color:#c4b5fd; margin-top:2px;'>{pdh_val}</div>
            </div>
            <div style='flex:1; text-align:center; background:#0c1a1a; border:1px solid #0891b2; border-radius:6px; padding:6px;'>
                <div style='font-size:10px; color:#67e8f9; font-weight:700;'>PDL (Đáy hôm qua)</div>
                <div style='font-size:14px; font-weight:800; color:#a5f3fc; margin-top:2px;'>{pdl_val}</div>
            </div>
        </div>
        <div style='font-size:10px; color:#94a3b8; font-weight:700; letter-spacing:0.5px; margin-bottom:6px;'>⚡ FVG CHƯA LẤP (OTE ZONE)</div>
    </div>
    """, unsafe_allow_html=True)

    # Render từng FVG item riêng để tránh lỗi escape HTML
    if fvg_list:
        for fvg in fvg_list:
            fvg_type   = fvg["type"]
            fvg_color  = "#22c55e" if fvg_type == "bullish" else "#ef4444"
            fvg_label  = "🟢 FVG Bullish" if fvg_type == "bullish" else "🔴 FVG Bearish"
            bg_rgba    = "rgba(34,197,94,0.10)" if fvg_type == "bullish" else "rgba(239,68,68,0.10)"
            bot_str    = f"{fvg['bottom']:.2f}"
            top_str    = f"{fvg['top']:.2f}"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"background:{bg_rgba};border-left:3px solid {fvg_color};border-radius:4px;"
                f"padding:5px 8px;margin-bottom:4px;'>"
                f"<span style='font-size:11px;color:{fvg_color};font-weight:700;'>{fvg_label}</span>"
                f"<span style='font-size:12px;color:#cbd5e1;font-weight:600;'>{bot_str} – {top_str}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            "<div style='font-size:11px;color:#475569;padding:4px 10px;margin-bottom:8px;'>Không phát hiện FVG chưa lấp.</div>",
            unsafe_allow_html=True
        )



    # ── Tín hiệu THỰC TẾ từ last_signals.json (cập nhật mỗi H1) ──
    live_setup   = live_sig.get("setup_type", "")      # "LONG" / "SHORT"
    live_entry   = live_sig.get("setup_entry_range", "—")
    live_ts      = live_sig.get("timestamp", "—")
    live_msg     = live_sig.get("msg", "")
    # Tách SL và TP từ msg nếu có
    import re
    sl_match = re.search(r"Stoploss:\s*([\d.]+)", live_msg)
    tp_match = re.search(r"Take Profit:\s*([\d.]+)", live_msg)
    live_sl  = sl_match.group(1) + " cents" if sl_match else "—"
    live_tp  = tp_match.group(1) + " cents" if tp_match else "—"
    # DCA zone tu fundamental_data
    dca_val  = data.get("dca_brackets", "—") or "—"
    # Xu huong tu contracts_meta
    liq_trend = meta_data.get("liquidity", {}).get("trend", data.get("swing_trend", "—"))

    signal_color = "#22c55e" if "LONG" in live_setup else "#ef4444" if "SHORT" in live_setup else "#94a3b8"
    signal_bg    = "#14532d" if "LONG" in live_setup else "#7f1d1d" if "SHORT" in live_setup else "#1e293b"
    signal_label = f"🟢 LỆNH MUA (LONG)" if "LONG" in live_setup else f"🔴 LỆNH BÁN (SHORT)" if "SHORT" in live_setup else "⏳ Chờ tín hiệu"

    st.markdown(f"""
    <div style='background:{signal_bg}; border:1px solid {signal_color}; border-radius:8px; padding:10px; margin-bottom:10px; text-align:center;'>
        <div style='font-size:14px; font-weight:800; color:{signal_color};'>{signal_label}</div>
        <div style='font-size:11px; color:#94a3b8; margin-top:4px;'>Cập nhật: {live_ts}</div>
    </div>
    """, unsafe_allow_html=True)

    for label, val in [
        ("📈 Xu hướng",        liq_trend),
        ("🎯 Entry Zone",      live_entry + " cents" if live_entry != "—" else "—"),
        ("🛑 Stop Loss",       live_sl),
        ("💵 Take Profit",     live_tp),
        ("💎 DCA Zone (DH)",   dca_val + (f" <br><span style='font-size:10px;color:#f59e0b;font-weight:600;'>Mã áp dụng: {dca_contract}</span>" if dca_contract else "")),
    ]:
        st.markdown(f"""<div class='kv'>
            <div class='lbl'>{label}</div>
            <div class='val'>{val}</div>
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
            <div style='font-size:13px; font-weight:600; color:#94a3b8; margin-bottom:6px;'>{label}</div>
            <div style='display:flex; gap:12px;'>
                <div style='flex:1;'>
                    <div style='font-size:12px; color:#475569;'>Kỳ trước</div>
                    <div style='font-size:14px; color:#94a3b8;'>{prev}</div>
                </div>
                <div style='flex:1;'>
                    <div style='font-size:12px; color:#166534;'>Hiện tại</div>
                    <div style='font-size:14px; color:#22c55e; font-weight:700;'>{curr}</div>
                </div>
            </div>
            {f'<div style="font-size:12px;color:#475569;margin-top:6px;">{date}</div>' if date else ''}
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
            <div style='font-size:13px; font-weight:600; color:#94a3b8;'>COT Managed Money <span style='float:right; font-size:11px; color:#475569;'>{cot_data.get("report_date", "—")}</span></div>
            <div style='font-size:20px; font-weight:700; color:{nc}; margin:4px 0;'>{net:+,} HD</div>
            <div style='font-size:13px; color:{nc};'>{arrow} {abs(chg):,} HD tuần này</div>
            <div style='font-size:13px; color:#94a3b8; font-weight:600; margin-top:4px;'>{quad}</div>
            <div style='font-size:13px; color:#64748b; margin-top:2px;'>{action[:60] if action else ""}</div>
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
            <div style='font-size:13px; font-weight:600; color:#94a3b8;'>Xuất Khẩu Tuần Này</div>
            <div style='font-size:14px; color:#22c55e; font-weight:600; margin:6px 0;'>{curr}</div>
            <div style='font-size:13px; color:#64748b;'>Kỳ trước: <span style="color:#94a3b8;">{prev}</span></div>
            <div style='font-size:15px; color:{ec}; font-weight:700; margin-top:4px;'>Δ {pct:+.1f}%</div>
            <div style='font-size:12px; color:#64748b; margin-top:4px;'>{logic[:80] if logic else ""}...</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:12px;color:#64748b;padding:8px;'>Chưa có dữ liệu xuất khẩu.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Smart Money Matrix & Thanh Khoản ──
updated_at_str = meta.get("updated_at", "")[:10]
date_html = f"<div style='font-size:10px;color:#475569;font-weight:400;text-transform:none;letter-spacing:0;'>Dữ liệu: {updated_at_str}</div>" if updated_at_str else ""
st.markdown(f"<div class='card'><div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'><div style='font-size:14px;font-weight:700;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;'>🧠 SMART MONEY MATRIX & DÒNG TIỀN</div>{date_html}</div>", unsafe_allow_html=True)

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


st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='font-size:16px; font-weight:800; color:#e2e8f0; letter-spacing:0.5px; margin-bottom:4px;'>
    📊 PHÂN TÍCH BIÊN ĐỘ GIÁ (VOLATILITY DASHBOARD)
</div>
<div style='font-size:12px; color:#64748b; margin-bottom:16px;'>
    Độ lệch Open↔Close và High↔Low từng ngày | Tuần gần nhất + Dự báo xu thế
</div>
""", unsafe_allow_html=True)

csv_vol_path = DATA_OUTPUT / f"{code}_{suffix}_H1.csv"
if csv_vol_path.exists():
    try:
        dfv = pd.read_csv(csv_vol_path)
        dfv.columns = [c.strip() for c in dfv.columns]
        date_col = next((c for c in dfv.columns if c.lower() in ['time','datetime','date','timestamp']), None)
        if date_col:
            dfv[date_col] = pd.to_datetime(dfv[date_col], errors='coerce')
            dfv = dfv.dropna(subset=[date_col]).rename(columns={date_col: "Datetime"})

        # ── Gộp H1 → Daily OHLCV ──
        dfv["Date"] = dfv["Datetime"].dt.date
        daily = dfv.groupby("Date").agg(
            Open=("Open", "first"),
            High=("High", "max"),
            Low=("Low", "min"),
            Close=("Close", "last"),
            Volume=("Volume", "sum"),
            ATR=("ATR", "mean"),
        ).reset_index()
        daily["Date"] = pd.to_datetime(daily["Date"])
        daily = daily[daily["Date"].dt.weekday < 5]   # Bỏ thứ 7/CN
        daily = daily.tail(15).reset_index(drop=True)  # 3 tuần gần nhất

        # ── Tính chỉ số biên độ ──
        daily["OC_Delta"]   = (daily["Close"] - daily["Open"]).round(2)   # Chênh lệch Open-Close (thân nến)
        daily["HL_Range"]   = (daily["High"]  - daily["Low"]).round(2)    # Biên độ cao nhất-thấp nhất
        daily["OC_Abs"]     = daily["OC_Delta"].abs()
        daily["Day_Label"]  = daily["Date"].dt.strftime("%a %d/%m")
        daily["IsGreen"]    = daily["OC_Delta"] >= 0

        # ── Xác định ngày cao/thấp nhất (theo HL_Range) ──
        idx_max = daily["HL_Range"].idxmax()
        idx_min = daily["HL_Range"].idxmin()
        day_max = daily.loc[idx_max, "Day_Label"]
        day_min = daily.loc[idx_min, "Day_Label"]
        range_max = daily.loc[idx_max, "HL_Range"]
        range_min = daily.loc[idx_min, "HL_Range"]

        # ── Tính thống kê tuần gần nhất ──
        # Xác định tuần hiện tại (dựa trên ngày cuối trong data)
        last_date = daily["Date"].max()
        week_start = last_date - pd.Timedelta(days=last_date.weekday())
        this_week = daily[daily["Date"] >= week_start]

        week_oc_total   = this_week["OC_Delta"].sum().round(2)
        week_hl_total   = this_week["HL_Range"].sum().round(2)
        week_hl_avg     = this_week["HL_Range"].mean().round(2)
        week_oc_avg     = this_week["OC_Abs"].mean().round(2)
        week_green_days = (this_week["OC_Delta"] > 0).sum()
        week_red_days   = (this_week["OC_Delta"] < 0).sum()

        # ── Dự báo xu thế dựa trên ATR & Momentum ──
        recent_atr      = daily["ATR"].tail(5).mean()
        prev_atr        = daily["ATR"].head(5).mean()
        atr_trend       = "📈 Tăng" if recent_atr > prev_atr * 1.05 else ("📉 Giảm" if recent_atr < prev_atr * 0.95 else "➡️ Ổn định")

        last3_oc        = daily["OC_Delta"].tail(3).tolist()
        momentum_score  = sum(1 if x > 0 else -1 for x in last3_oc)
        momentum_str    = "🟢 Bullish (3 ngày gần nhất đều tăng)" if momentum_score == 3 else \
                          "🟢 Bullish nhẹ" if momentum_score > 0 else \
                          "🔴 Bearish nhẹ" if momentum_score < 0 else "⚪ Trung lập"

        expected_range  = round(recent_atr * 1.0, 2)
        close_now       = daily["Close"].iloc[-1]
        r1_est          = round(close_now + recent_atr * 1.0, 2)
        s1_est          = round(close_now - recent_atr * 1.0, 2)

        # ═══ BLOCK 1: Thống kê tuần ═══
        w1, w2, w3, w4, w5 = st.columns(5)
        wk_color = "#22c55e" if week_oc_total >= 0 else "#ef4444"

        for col_w, lbl, val, clr in [
            (w1, "Tổng ΔOC Tuần", f"{'+' if week_oc_total>=0 else ''}{week_oc_total}¢", wk_color),
            (w2, "Tổng Biên Độ (HL)", f"{week_hl_total}¢", "#f59e0b"),
            (w3, "Biên Độ TB/Ngày", f"{week_hl_avg}¢", "#94a3b8"),
            (w4, "Ngày Biên Độ Cao Nhất", f"{day_max} ({range_max}¢)", "#fb923c"),
            (w5, "Ngày Biên Độ Thấp Nhất", f"{day_min} ({range_min}¢)", "#a78bfa"),
        ]:
            col_w.markdown(f"""
            <div style='background:#1a2035; border-radius:10px; padding:14px; text-align:center;
                        border:1px solid #2a3a5c; height:80px; display:flex; flex-direction:column; justify-content:center;'>
                <div style='font-size:10px; color:#64748b; font-weight:600; margin-bottom:4px;'>{lbl}</div>
                <div style='font-size:15px; font-weight:800; color:{clr};'>{val}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ═══ BLOCK 2: Biểu đồ Biên Độ Từng Ngày ═══
        bar_colors_oc = ["#22c55e" if x >= 0 else "#ef4444" for x in daily["OC_Delta"]]

        fig_vol = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.55, 0.45],
            subplot_titles=["📊 Biên Độ High-Low (Thân nến mở rộng)", "📐 Chênh lệch Open→Close (Hướng đi của ngày)"]
        )

        # Hàng 1: HL Range bar
        fig_vol.add_trace(go.Bar(
            x=daily["Day_Label"], y=daily["HL_Range"],
            name="High-Low Range",
            marker_color=[
                "#fb923c" if i == idx_max else "#a78bfa" if i == idx_min else "#38bdf8"
                for i in range(len(daily))
            ],
            text=[f"{v:.1f}¢" for v in daily["HL_Range"]],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
        ), row=1, col=1)

        # Đường ATR trung bình
        fig_vol.add_hline(
            y=daily["ATR"].mean(), row=1, col=1,
            line_dash="dash", line_color="#f59e0b", line_width=1.5,
            annotation_text=f"ATR TB: {daily['ATR'].mean():.2f}¢",
            annotation_font=dict(size=10, color="#f59e0b"),
        )

        # Hàng 2: OC Delta bar (thân nến)
        fig_vol.add_trace(go.Bar(
            x=daily["Day_Label"], y=daily["OC_Delta"],
            name="Open→Close",
            marker_color=bar_colors_oc,
            text=[f"{'+' if v>=0 else ''}{v:.1f}¢" for v in daily["OC_Delta"]],
            textposition="outside",
            textfont=dict(size=10),
        ), row=2, col=1)

        fig_vol.add_hline(y=0, row=2, col=1, line_color="#475569", line_width=1)

        fig_vol.update_layout(
            paper_bgcolor="#0f1629", plot_bgcolor="#0f1629",
            font=dict(color="#e2e8f0", family="Inter"),
            margin=dict(l=10, r=10, t=45, b=10),
            xaxis=dict(gridcolor="#1e2d45"), yaxis=dict(gridcolor="#1e2d45"),
            xaxis2=dict(gridcolor="#1e2d45"), yaxis2=dict(gridcolor="#1e2d45"),
            showlegend=False, height=460,
            annotations=[
                dict(text="📊 Biên Độ High-Low (¢)", x=0, xref="paper", y=1.04, yref="paper",
                     showarrow=False, font=dict(size=12, color="#94a3b8")),
                dict(text="📐 Chênh lệch Open→Close (¢)", x=0, xref="paper", y=0.42, yref="paper",
                     showarrow=False, font=dict(size=12, color="#94a3b8")),
            ]
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        # ═══ BLOCK 3: Bảng chi tiết từng ngày ═══
        st.markdown("<div style='font-size:12px; font-weight:700; color:#94a3b8; letter-spacing:0.5px; margin-bottom:8px;'>📋 BẢNG CHI TIẾT TỪNG NGÀY</div>", unsafe_allow_html=True)

        tbl_html = """
        <table style='width:100%; border-collapse:collapse; font-size:12px; font-family:Inter,sans-serif;'>
        <thead>
            <tr style='background:#1e293b; color:#94a3b8;'>
                <th style='padding:8px 10px; text-align:left; border-bottom:1px solid #334155;'>Ngày</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>Open</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>High</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>Low</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>Close</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>ΔOC (thân nến)</th>
                <th style='padding:8px 10px; text-align:right; border-bottom:1px solid #334155;'>HL Range (biên độ)</th>
                <th style='padding:8px 10px; text-align:center; border-bottom:1px solid #334155;'>Nến</th>
            </tr>
        </thead>
        <tbody>"""

        for i, row in daily.iterrows():
            oc_color  = "#22c55e" if row["OC_Delta"] >= 0 else "#ef4444"
            oc_sign   = "+" if row["OC_Delta"] >= 0 else ""
            is_max    = i == idx_max
            is_min    = i == idx_min
            row_bg    = "background:#0c1a12;" if is_max else "background:#1a0c1a;" if is_min else ""
            badge_max = " 🔥" if is_max else " 🧊" if is_min else ""
            candle    = "🟢" if row["OC_Delta"] >= 0 else "🔴"
            tbl_html += f"""
            <tr style='border-bottom:1px solid #1e2d45; {row_bg}'>
                <td style='padding:7px 10px; color:#cbd5e1; font-weight:600;'>{row['Day_Label']}{badge_max}</td>
                <td style='padding:7px 10px; text-align:right; color:#94a3b8;'>{row['Open']:.2f}</td>
                <td style='padding:7px 10px; text-align:right; color:#fb923c;'>{row['High']:.2f}</td>
                <td style='padding:7px 10px; text-align:right; color:#a78bfa;'>{row['Low']:.2f}</td>
                <td style='padding:7px 10px; text-align:right; color:#e2e8f0; font-weight:700;'>{row['Close']:.2f}</td>
                <td style='padding:7px 10px; text-align:right; color:{oc_color}; font-weight:700;'>{oc_sign}{row['OC_Delta']:.2f}¢</td>
                <td style='padding:7px 10px; text-align:right; color:#38bdf8; font-weight:700;'>{row['HL_Range']:.2f}¢</td>
                <td style='padding:7px 10px; text-align:center;'>{candle}</td>
            </tr>"""

        # Hàng tổng tuần
        tbl_html += f"""
            <tr style='background:#1e293b; border-top:2px solid #334155; font-weight:700;'>
                <td style='padding:8px 10px; color:#f59e0b;'>📅 TUẦN NÀY</td>
                <td style='padding:8px 10px;'></td><td style='padding:8px 10px;'></td>
                <td style='padding:8px 10px;'></td><td style='padding:8px 10px;'></td>
                <td style='padding:8px 10px; text-align:right; color:{"#22c55e" if week_oc_total>=0 else "#ef4444"};'>{'+' if week_oc_total>=0 else ''}{week_oc_total:.2f}¢</td>
                <td style='padding:8px 10px; text-align:right; color:#f59e0b;'>{week_hl_total:.2f}¢</td>
                <td style='padding:8px 10px; text-align:center; color:#94a3b8;'>🟢×{week_green_days} 🔴×{week_red_days}</td>
            </tr>
        </tbody></table>"""
        st.markdown(tbl_html, unsafe_allow_html=True)

        # ═══ BLOCK 4: Dự báo Xu thế ═══
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        forecast_color = "#22c55e" if momentum_score > 0 else "#ef4444" if momentum_score < 0 else "#94a3b8"
        vol_trend_color = "#ef4444" if "Tăng" in atr_trend else "#22c55e" if "Giảm" in atr_trend else "#f59e0b"

        st.markdown(f"""
        <div style='background:#1a2035; border-radius:12px; padding:16px; border:1px solid #2a3a5c;'>
            <div style='font-size:12px; font-weight:700; color:#94a3b8; letter-spacing:0.5px; margin-bottom:12px;'>
                🔮 DỰ BÁO XU THẾ (Dựa trên ATR & Momentum 3 ngày gần nhất)
            </div>
            <div style='display:flex; gap:16px; flex-wrap:wrap;'>
                <div style='flex:1; min-width:160px; background:#0f1629; border-radius:8px; padding:12px; border-left:3px solid {forecast_color};'>
                    <div style='font-size:10px; color:#64748b; margin-bottom:4px;'>MOMENTUM GIÁ</div>
                    <div style='font-size:13px; font-weight:700; color:{forecast_color};'>{momentum_str}</div>
                </div>
                <div style='flex:1; min-width:160px; background:#0f1629; border-radius:8px; padding:12px; border-left:3px solid {vol_trend_color};'>
                    <div style='font-size:10px; color:#64748b; margin-bottom:4px;'>BIẾN ĐỘNG (ATR)</div>
                    <div style='font-size:13px; font-weight:700; color:{vol_trend_color};'>{atr_trend} | ATR hiện tại: {recent_atr:.2f}¢</div>
                </div>
                <div style='flex:1; min-width:160px; background:#0f1629; border-radius:8px; padding:12px; border-left:3px solid #38bdf8;'>
                    <div style='font-size:10px; color:#64748b; margin-bottom:4px;'>VÙNG KỲ VỌNG NGÀY TỚI</div>
                    <div style='font-size:13px; font-weight:700; color:#38bdf8;'>
                        🟢 R1 ≈ {r1_est}¢ &nbsp;|&nbsp; 🔴 S1 ≈ {s1_est}¢
                    </div>
                    <div style='font-size:10px; color:#475569; margin-top:4px;'>Biên độ kỳ vọng ±{expected_range:.2f}¢ (1× ATR)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.warning(f"Lỗi tính Volatility Dashboard: {e}")
else:
    st.info("Chưa có dữ liệu H1 để phân tích biên độ giá.")

