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

# Các nút điều khiển thủ công
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🧹 XÓA BỘ NHỚ TẠM (CACHE)", key="refresh_profile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_btn2:
    if st.button("🔄 TẢI GIÁ H1 & PHÂN TÍCH LẠI", key="force_fetch", use_container_width=True):
        import subprocess
        import os
        root_dir = str(Path(__file__).parent.parent)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        with st.spinner("Đang tải dữ liệu H1 từ TV và phân tích lại SMC... (Đợi 15-20s)"):
            subprocess.run([sys.executable, str(Path(root_dir) / "Data" / "fetch_prices.py")], env=env)
            subprocess.run([sys.executable, "-c", "import entry_alarm; entry_alarm.run_analysis()"], cwd=root_dir, env=env)
            subprocess.run([sys.executable, "run_pro_plus.py"], cwd=root_dir, env=env)
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

st.markdown(f"""
<div style='font-size:16px; font-weight:800; color:#e2e8f0; letter-spacing:0.5px; margin-bottom:4px;'>
    📊 PHÂN TÍCH BIÊN ĐỘ GIÁ (VOLATILITY DASHBOARD) - <span style='color:#f59e0b;'>{selected_name}</span> <span style='font-size:14px; color:#94a3b8;'>({selected_contract})</span>
</div>
<div style='font-size:12px; color:#64748b; margin-bottom:12px;'>
    Độ lệch Open↔Close và High↔Low từng ngày | 3 tuần gần nhất + Dự báo xu thế
</div>
""", unsafe_allow_html=True)

# ── TAB: D1 và Giá H4 ────────────────────────────────────────
_tab_d1, _tab_h4 = st.tabs(["📅 Tab D1", "📊 Giá H4"])

# ─── TAB D1: Giữ nguyên nội dung cũ ─────────────────────────
with _tab_d1:
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

# ─── TAB H4: Biểu đồ Nến H4 + EMA 21/50 ────────────────────
with _tab_h4:
    _csv_h4_path = DATA_OUTPUT / f"{code}_active_H4.csv"
    if _csv_h4_path.exists():
        try:
            _dfh4 = pd.read_csv(_csv_h4_path)
            _dfh4.columns = [c.strip() for c in _dfh4.columns]
            _tcol = next((c for c in _dfh4.columns if c.lower() in ['time','datetime','date','timestamp']), None)
            if _tcol:
                _dfh4[_tcol] = pd.to_datetime(_dfh4[_tcol], errors='coerce')
                _dfh4 = _dfh4.dropna(subset=[_tcol]).rename(columns={_tcol: "Datetime"})
            _dfh4 = _dfh4.sort_values("Datetime").reset_index(drop=True)

            # Tính EMA 21 và EMA 50 trên chuỗi Close
            _dfh4["EMA21"] = _dfh4["Close"].ewm(span=21, adjust=False).mean()
            _dfh4["EMA50"] = _dfh4["Close"].ewm(span=50, adjust=False).mean()

            # Xác định Đỉnh/Đáy (Swing High / Swing Low) bằng Fractal 5 nến
            _dfh4['Swing_High'] = False
            _dfh4['Swing_Low'] = False
            for i in range(2, len(_dfh4)-2):
                if _dfh4.loc[i, 'High'] > _dfh4.loc[i-1, 'High'] and _dfh4.loc[i, 'High'] > _dfh4.loc[i-2, 'High'] and \
                   _dfh4.loc[i, 'High'] > _dfh4.loc[i+1, 'High'] and _dfh4.loc[i, 'High'] > _dfh4.loc[i+2, 'High']:
                    _dfh4.loc[i, 'Swing_High'] = True
                if _dfh4.loc[i, 'Low'] < _dfh4.loc[i-1, 'Low'] and _dfh4.loc[i, 'Low'] < _dfh4.loc[i-2, 'Low'] and \
                   _dfh4.loc[i, 'Low'] < _dfh4.loc[i+1, 'Low'] and _dfh4.loc[i, 'Low'] < _dfh4.loc[i+2, 'Low']:
                    _dfh4.loc[i, 'Swing_Low'] = True

            # Xác định Thay đổi cấu trúc / Phá vỡ (ChoCh / BOS)
            _dfh4['BOS_Bull'] = False
            _dfh4['BOS_Bear'] = False
            _last_sh_val = None
            _last_sl_val = None

            for i in range(len(_dfh4)):
                # Đánh giá xem nến đóng cửa có vượt qua Đỉnh/Đáy gần nhất không
                if _last_sh_val is not None and _dfh4.loc[i, 'Close'] > _last_sh_val:
                    _dfh4.loc[i, 'BOS_Bull'] = True
                    _last_sh_val = None  # Reset để chờ đỉnh mới
                if _last_sl_val is not None and _dfh4.loc[i, 'Close'] < _last_sl_val:
                    _dfh4.loc[i, 'BOS_Bear'] = True
                    _last_sl_val = None
                    
                # Cập nhật Đỉnh/Đáy vừa được xác nhận (Nến i-2 được xác nhận khi nến i đóng cửa)
                if i >= 2:
                    if _dfh4.loc[i-2, 'Swing_High']:
                        _last_sh_val = _dfh4.loc[i-2, 'High']
                    if _dfh4.loc[i-2, 'Swing_Low']:
                        _last_sl_val = _dfh4.loc[i-2, 'Low']

            # Nhãn hiển thị trục X: ngày + giờ VN
            _dfh4["Label"] = _dfh4["Datetime"].dt.strftime("%d/%m %H:%M")

            # Màu nến: Bullish = xanh, Bearish = đỏ
            _clr_up   = "#22c55e"
            _clr_dn   = "#ef4444"
            _clr_up_b = "rgba(34,197,94,0.15)"
            _clr_dn_b = "rgba(239,68,68,0.15)"

            _colors_fill   = [_clr_up   if r["Close"] >= r["Open"] else _clr_dn   for _, r in _dfh4.iterrows()]
            _colors_border = [_clr_up   if r["Close"] >= r["Open"] else _clr_dn   for _, r in _dfh4.iterrows()]

            _fig_h4 = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.80, 0.20],
                subplot_titles=[f"Biểu đồ nến H4 — {selected_name} ({selected_contract})", "Volume"]
            )

            # Nến Candlestick
            _fig_h4.add_trace(go.Candlestick(
                x=_dfh4["Label"],
                open=_dfh4["Open"],
                high=_dfh4["High"],
                low=_dfh4["Low"],
                close=_dfh4["Close"],
                name="H4 Candle",
                increasing=dict(line=dict(color=_clr_up, width=1.5), fillcolor=_clr_up),
                decreasing=dict(line=dict(color=_clr_dn, width=1.5), fillcolor=_clr_dn),
            ), row=1, col=1)

            # EMA 21 (màu vàng)
            _fig_h4.add_trace(go.Scatter(
                x=_dfh4["Label"], y=_dfh4["EMA21"],
                mode="lines", name="EMA 21",
                line=dict(color="#f59e0b", width=1.8, dash="solid"),
                opacity=0.9,
            ), row=1, col=1)

            # EMA 50 (màu tím nhạt)
            _fig_h4.add_trace(go.Scatter(
                x=_dfh4["Label"], y=_dfh4["EMA50"],
                mode="lines", name="EMA 50",
                line=dict(color="#a78bfa", width=1.8, dash="solid"),
                opacity=0.9,
            ), row=1, col=1)

            # --- Đánh dấu Đỉnh (Swing High) ---
            _y_pad_marker = (_dfh4["High"].max() - _dfh4["Low"].min()) * 0.08
            _sh_df = _dfh4[_dfh4['Swing_High']]
            if not _sh_df.empty:
                _fig_h4.add_trace(go.Scatter(
                    x=_sh_df["Label"], y=_sh_df["High"] + (_y_pad_marker * 0.1),
                    mode="markers+text", name="Đỉnh H4",
                    marker=dict(symbol="triangle-down", size=6, color="#ef4444"),
                    text="▼", textposition="top center", textfont=dict(color="#ef4444", size=9),
                    hoverinfo="skip", showlegend=True
                ), row=1, col=1)

            # --- Đánh dấu Đáy (Swing Low) ---
            _sl_df = _dfh4[_dfh4['Swing_Low']]
            if not _sl_df.empty:
                _fig_h4.add_trace(go.Scatter(
                    x=_sl_df["Label"], y=_sl_df["Low"] - (_y_pad_marker * 0.1),
                    mode="markers+text", name="Đáy H4",
                    marker=dict(symbol="triangle-up", size=6, color="#22c55e"),
                    text="▲", textposition="bottom center", textfont=dict(color="#22c55e", size=9),
                    hoverinfo="skip", showlegend=True
                ), row=1, col=1)

            # --- Đánh dấu Break Cấu Trúc Tăng (ChoCh/BOS Bull) ---
            _bull_break = _dfh4[_dfh4['BOS_Bull']]
            if not _bull_break.empty:
                _fig_h4.add_trace(go.Scatter(
                    x=_bull_break["Label"], y=_bull_break["Low"] - (_y_pad_marker * 0.3),
                    mode="markers+text", name="Break Tăng",
                    marker=dict(symbol="star", size=10, color="#38bdf8"),
                    text="<b>🚀 Đảo chiều/Tiếp diễn Tăng</b>", textposition="bottom center",
                    textfont=dict(color="#38bdf8", size=10),
                    hoverinfo="skip"
                ), row=1, col=1)

            # --- Đánh dấu Break Cấu Trúc Giảm (ChoCh/BOS Bear) ---
            _bear_break = _dfh4[_dfh4['BOS_Bear']]
            if not _bear_break.empty:
                _fig_h4.add_trace(go.Scatter(
                    x=_bear_break["Label"], y=_bear_break["High"] + (_y_pad_marker * 0.3),
                    mode="markers+text", name="Break Giảm",
                    marker=dict(symbol="star", size=10, color="#fb7185"),
                    text="<b>🩸 Đảo chiều/Tiếp diễn Giảm</b>", textposition="top center",
                    textfont=dict(color="#fb7185", size=10),
                    hoverinfo="skip"
                ), row=1, col=1)

            # Volume bars
            _vol_colors = [_clr_up if r["Close"] >= r["Open"] else _clr_dn for _, r in _dfh4.iterrows()]
            _fig_h4.add_trace(go.Bar(
                x=_dfh4["Label"], y=_dfh4["Volume"],
                name="Volume", marker_color=_vol_colors, opacity=0.6,
            ), row=2, col=1)

            # Nhãn giá Close nến cuối cùng
            _last_close = _dfh4["Close"].iloc[-1]
            _last_label = _dfh4["Label"].iloc[-1]
            _last_color = _clr_up if _dfh4["Close"].iloc[-1] >= _dfh4["Open"].iloc[-1] else _clr_dn
            _fig_h4.add_annotation(
                x=_last_label, y=_last_close,
                text=f"  {_last_close:.2f}",
                showarrow=False, xanchor="left",
                font=dict(color=_last_color, size=12, family="Inter"),
                row=1, col=1
            )

            # Layout — mặc định hiển thị 10 ngày (50 nến H4), có thể kéo xem thêm
            _total_bars = len(_dfh4)
            _default_bars = 50  # 10 ngày * 5 nến H4/ngày
            _x_start_idx = max(0, _total_bars - _default_bars)  # index bắt đầu hiển thị
            _x_start_label = _dfh4["Label"].iloc[_x_start_idx]
            _x_end_label   = _dfh4["Label"].iloc[-1]

            # Y-range chỉ cho 10 ngày hiển thị, + padding
            _vis_df  = _dfh4.iloc[_x_start_idx:]
            _y_lo    = _vis_df["Low"].min()
            _y_hi    = _vis_df["High"].max()
            _y_pad   = (_y_hi - _y_lo) * 0.08

            _fig_h4.update_layout(
                paper_bgcolor="#0f1629",
                plot_bgcolor="#0d1425",
                font=dict(color="#e2e8f0", family="Inter"),
                margin=dict(l=10, r=60, t=40, b=60),
                xaxis=dict(
                    gridcolor="#1e2d45",
                    tickangle=-45,
                    tickfont=dict(size=9),
                    range=[_x_start_label, _x_end_label],  # mặc định hiển thị 10 ngày
                    rangeslider=dict(visible=False),
                    type="category",  # dùng category để không bị khoảng trống cuối tuần
                ),
                yaxis=dict(
                    gridcolor="#1e2d45", tickformat=".2f",
                    range=[_y_lo - _y_pad, _y_hi + _y_pad],
                    title="Giá (¢/bu)", title_font=dict(size=11),
                ),
                xaxis2=dict(
                    gridcolor="#1e2d45", tickangle=-45, tickfont=dict(size=9),
                    rangeslider=dict(
                        visible=True,
                        bgcolor="#0d1425",
                        bordercolor="#334155",
                        borderwidth=1,
                        thickness=0.04,  # chiều cao thanh trượt mỏng
                    ),
                ),
                yaxis2=dict(gridcolor="#1e2d45", title="Volume", title_font=dict(size=10)),
                showlegend=True,
                legend=dict(
                    x=0.01, y=0.99, bgcolor="rgba(15,22,41,0.7)",
                    bordercolor="#334155", borderwidth=1,
                    font=dict(size=11),
                ),
                height=640,  # chiều cao đủ lớn + không gian cho thanh trượt
                hovermode="x unified",
            )
            _fig_h4.update_yaxes(showgrid=True, zeroline=False)

            # Phân tách ngày bằng đường kẻ dọc
            _dates_seen = set()
            for _lbl_i, _dt_i in zip(_dfh4["Label"], _dfh4["Datetime"]):
                _d = _dt_i.strftime("%d/%m")
                if _d not in _dates_seen:
                    _dates_seen.add(_d)
                    _fig_h4.add_vline(
                        x=_lbl_i, line_dash="dot",
                        line_color="rgba(100,116,139,0.35)", line_width=1
                    )

            # Tiêu đề cập nhật dữ liệu
            _h4_last_time = _dfh4["Datetime"].iloc[-1].strftime("%d/%m/%Y %H:%M")
            st.markdown(
                f"<div style='font-size:11px;color:#64748b;margin-bottom:8px;'>"
                f"Nến H4 · 30 ngày gần nhất · Hiển thị mặc định: 10 ngày (kéo thanh trượt bên dưới để xem thêm) · Cập nhật đến: "
                f"<span style='color:#f59e0b;font-weight:700;'>{_h4_last_time} (VN)</span> · "
                f"EMA <span style='color:#f59e0b;'>21 (vàng)</span> · "
                f"EMA <span style='color:#a78bfa;'>50 (tím)</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.plotly_chart(_fig_h4, use_container_width=True)

            # Bảng tóm tắt nến H4 cuối cùng
            st.markdown("<div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:0.5px;margin:8px 0 6px;'>📋 CÁC NẾN H4 GẦN NHẤT</div>", unsafe_allow_html=True)
            _th4 = ("<table style='width:100%;border-collapse:collapse;font-size:12px;font-family:Inter,sans-serif;'>"
                    "<thead><tr style='background:#1e293b;color:#94a3b8;'>"
                    "<th style='padding:7px 10px;text-align:left;border-bottom:1px solid #334155;'>Thời gian (VN)</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Open</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>High</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Low</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>Close</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>EMA21</th>"
                    "<th style='padding:7px 10px;text-align:right;border-bottom:1px solid #334155;'>EMA50</th>"
                    "<th style='padding:7px 10px;text-align:center;border-bottom:1px solid #334155;'>Nến</th>"
                    "</tr></thead><tbody>")
            for _, _rh4 in _dfh4.tail(10).iloc[::-1].iterrows():
                _bul = _rh4["Close"] >= _rh4["Open"]
                _cc  = "#22c55e" if _bul else "#ef4444"
                _cn4 = "🟢" if _bul else "🔴"
                _e21 = f"{_rh4['EMA21']:.2f}" if not pd.isna(_rh4.get("EMA21", float('nan'))) else "—"
                _e50 = f"{_rh4['EMA50']:.2f}" if not pd.isna(_rh4.get("EMA50", float('nan'))) else "—"
                _th4 += (f"<tr style='border-bottom:1px solid #1e2d45;'>"
                         f"<td style='padding:6px 10px;color:#94a3b8;font-weight:600;'>{_rh4['Label']}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#cbd5e1;'>{_rh4['Open']:.2f}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#fb923c;'>{_rh4['High']:.2f}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#a78bfa;'>{_rh4['Low']:.2f}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#e2e8f0;font-weight:700;'>{_rh4['Close']:.2f}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#f59e0b;'>{_e21}</td>"
                         f"<td style='padding:6px 10px;text-align:right;color:#a78bfa;'>{_e50}</td>"
                         f"<td style='padding:6px 10px;text-align:center;'>{_cn4}</td></tr>")
            _th4 += "</tbody></table>"
            st.markdown(_th4, unsafe_allow_html=True)

        except Exception as _he:
            st.warning(f"Lỗi vẽ biểu đồ H4: {_he}")
    else:
        st.info("Chưa có file dữ liệu H4. Hãy chạy: python Data/fetch_prices_H4.py")

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
    mss_list = smc_zones.get("mss_list", [])

    st.markdown(f"<div class='card'><div style='font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:1px;margin-bottom:12px;'>📋 CHIẾN LƯỢC — {swing_contract} {month_str}</div>", unsafe_allow_html=True)

    # ── Build toàn bộ SMC HTML bằng string concatenation (tránh triple-quote indent bug) ──
    H = ""
    H += "<div style='background:#0f1629;border-radius:8px;padding:12px;margin-bottom:12px;border:1px solid #1e2d45;'>"
    H += "<div style='font-size:10px;color:#94a3b8;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;'>📍 VÙNG THANH KHOẢN SMC</div>"
    H += "<div style='display:flex;gap:8px;margin-bottom:16px;'>"
    H += f"<div style='flex:1;text-align:center;background:#1a1234;border:1px solid #7c3aed;border-radius:6px;padding:8px;'><div style='font-size:10px;color:#a78bfa;font-weight:700;'>PDH (Đỉnh hôm qua)</div><div style='font-size:14px;font-weight:800;color:#c4b5fd;margin-top:2px;'>{pdh_val}</div></div>"
    H += f"<div style='flex:1;text-align:center;background:#0c1a1a;border:1px solid #0891b2;border-radius:6px;padding:8px;'><div style='font-size:10px;color:#67e8f9;font-weight:700;'>PDL (Đáy hôm qua)</div><div style='font-size:14px;font-weight:800;color:#a5f3fc;margin-top:2px;'>{pdl_val}</div></div>"
    H += "</div>"

    # ── MSS ──
    H += "<div style='font-size:10px;color:#94a3b8;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;margin-top:4px;'>⚡ MSS (MARKET STRUCTURE SHIFT)</div>"
    if mss_list:
        for mss in reversed(mss_list):
            mt = mss["type"]
            mg = mss.get("mitigated", False)
            mc = "#64748b" if mg else ("#22c55e" if mt == "bullish" else "#ef4444")
            ml = ("🟢 MSS Bullish" if mt == "bullish" else "🔴 MSS Bearish")
            mbg = "rgba(100,116,139,0.10)" if mg else ("rgba(34,197,94,0.10)" if mt == "bullish" else "rgba(239,68,68,0.10)")
            mts = "text-decoration:line-through;color:#64748b;" if mg else "color:#cbd5e1;"
            msl = "(Đã test)" if mg else "(Chưa test)"
            mlv = f"{mss['level']:.2f}"
            H += f"<div style='display:flex;justify-content:space-between;align-items:center;background:{mbg};border-left:3px solid {mc};border-radius:4px;padding:6px 10px;margin-bottom:6px;'><span style='font-size:11px;font-weight:700;{mts}'>{ml} <span style='font-weight:400;font-size:10px;'>{msl}</span></span><span style='font-size:12px;font-weight:600;{mts}'>{mlv}</span></div>"
    else:
        H += "<div style='font-size:11px;color:#475569;margin-bottom:12px;'>Không phát hiện MSS nào gần đây.</div>"

    # ── FVG ──
    H += "<div style='font-size:10px;color:#94a3b8;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;margin-top:16px;'>⚡ FVG (OTE ZONE)</div>"
    if fvg_list:
        for fvg in reversed(fvg_list):
            ft = fvg["type"]
            fg = fvg.get("mitigated", False)
            fc = "#64748b" if fg else ("#22c55e" if ft == "bullish" else "#ef4444")
            fl = ("🟢 FVG Bullish" if ft == "bullish" else "🔴 FVG Bearish")
            fbg = "rgba(100,116,139,0.10)" if fg else ("rgba(34,197,94,0.10)" if ft == "bullish" else "rgba(239,68,68,0.10)")
            fts = "text-decoration:line-through;color:#64748b;" if fg else "color:#cbd5e1;"
            fsl = "(Đã lấp)" if fg else "(Chưa lấp)"
            fbot = f"{fvg['bottom']:.2f}"
            ftop = f"{fvg['top']:.2f}"
            H += f"<div style='display:flex;justify-content:space-between;align-items:center;background:{fbg};border-left:3px solid {fc};border-radius:4px;padding:6px 10px;margin-bottom:6px;'><span style='font-size:11px;font-weight:700;{fts}'>{fl} <span style='font-weight:400;font-size:10px;'>{fsl}</span></span><span style='font-size:12px;font-weight:600;{fts}'>{fbot} – {ftop}</span></div>"
    else:
        H += "<div style='font-size:11px;color:#475569;margin-bottom:4px;'>Không phát hiện FVG nào.</div>"

    H += "</div>"
    st.markdown(H, unsafe_allow_html=True)



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
        <div style='font-size:11px; color:#94a3b8; margin-top:4px;'>Phát tín hiệu: {live_ts}</div>
    </div>
    """, unsafe_allow_html=True)

    # Xu Hướng
    st.markdown(f"""<div class='kv'>
        <div class='lbl'>📈 Xu hướng</div>
        <div class='val'>{liq_trend}</div>
    </div>""", unsafe_allow_html=True)
    
    # Logic to extract FVG for Intraday (Ngắn Hạn)
    fvg_intraday = "—"
    if fvg_list:
        target_type = "bullish" if "LONG" in live_setup else ("bearish" if "SHORT" in live_setup else None)
        if target_type:
            # fvg_list is usually ordered by time, reversed gets the most recent ones
            for fvg in reversed(fvg_list):
                if fvg["type"] == target_type and not fvg.get("mitigated", False):
                    fvg_intraday = f"{fvg['bottom']:.2f} - {fvg['top']:.2f} cents"
                    break
    
    # 3 Entry Zones side-by-side
    entry_2_val = live_entry + " cents" if live_entry != "—" else "—"
    dca_sub = f"<br><span style='font-size:10px;color:#f59e0b;font-weight:600;'>Mã áp dụng: {dca_contract}</span>" if dca_contract else ""
    st.markdown(f"""<div style='display:flex; gap:8px; margin-bottom:12px;'>
        <div style='flex:1; background:#1a2035; padding:10px; border-radius:6px; border-left:3px solid #f43f5e;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:600; margin-bottom:4px;'>🎯 Vùng 1 (Ngắn Hạn)</div>
            <div style='font-size:13px; font-weight:700; color:#e2e8f0;'>{fvg_intraday}</div>
        </div>
        <div style='flex:1; background:#1a2035; padding:10px; border-radius:6px; border-left:3px solid #38bdf8;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:600; margin-bottom:4px;'>💎 Vùng 2 (Trung Hạn)</div>
            <div style='font-size:13px; font-weight:700; color:#e2e8f0;'>{entry_2_val}</div>
        </div>
        <div style='flex:1; background:#1a2035; padding:10px; border-radius:6px; border-left:3px solid #f59e0b;'>
            <div style='font-size:11px; color:#94a3b8; font-weight:600; margin-bottom:4px;'>📦 Vùng 3 (Mùa Vụ)</div>
            <div style='font-size:13px; font-weight:700; color:#e2e8f0;'>{dca_val}{dca_sub}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Stop Loss & Take Profit
    for label, val in [
        ("🛑 Stop Loss",       live_sl),
        ("💵 Take Profit",     live_tp),
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
<div style='background:#0f1629; border-radius:12px; padding:16px; border:1px solid #1e2d45; margin-top:16px;'>
<div style='font-size:14px; font-weight:800; color:#e2e8f0; letter-spacing:0.5px; margin-bottom:12px; display:flex; align-items:center; gap:8px;'>
<span>📚</span> CHÚ GIẢI THUẬT NGỮ (GLOSSARY)
</div>
<div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:16px;'>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #7c3aed;'>
<div style='font-size:13px; font-weight:700; color:#c4b5fd; margin-bottom:4px;'>PDH / PDL (Previous Day High / Low)</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.5;'>
Mức giá Cao nhất (PDH) và Thấp nhất (PDL) của ngày giao dịch trước đó. Trong SMC, đây là các vùng thanh khoản quan trọng (Liquidity Pools) mà giá thường có xu hướng quét qua để lấy thanh khoản trước khi đảo chiều.
</div>
</div>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #0891b2;'>
<div style='font-size:13px; font-weight:700; color:#67e8f9; margin-bottom:4px;'>FVG (OTE ZONE)</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.5;'>
<b>FVG (Fair Value Gap - Khoảng trống giá):</b> Khoảng trống tạo ra bởi một nến có thân rất dài, thể hiện dòng tiền lớn vừa đổ vào.<br/>
<b>Chưa lấp (Unmitigated):</b> Giá chưa quay lại khu vực này. Nó đóng vai trò như thỏi nam châm hút giá về để tạo điểm vào lệnh tối ưu (OTE).<br/>
<b style='color:#22c55e;'>FVG Bullish:</b> Khoảng trống tạo ra bởi nến tăng mạnh. Giá thường quay về đây để tạo hỗ trợ -> <b>Canh lệnh LONG (Mua)</b>.<br/>
<b style='color:#ef4444;'>FVG Bearish:</b> Khoảng trống tạo ra bởi nến giảm mạnh. Giá thường quay về đây để tạo kháng cự -> <b>Canh lệnh SHORT (Bán)</b>.
</div>
</div>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #ec4899;'>
<div style='font-size:13px; font-weight:700; color:#f472b6; margin-bottom:4px;'>MSS (Market Structure Shift)</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.5;'>
<b>MSS (Sự thay đổi cấu trúc thị trường):</b> Xảy ra khi giá phá vỡ một Đỉnh hoặc Đáy quan trọng (Swing High/Low) tạo ra sự đảo chiều cấu trúc. Đây là <b>vùng vào lệnh có tỷ lệ Win cực cao</b>.<br/>
<b>Chưa test:</b> Giá chưa quay lại retest vùng giá bị phá vỡ. Thường giá sẽ quay về đây kiểm tra trước khi chạy tiếp.<br/>
<b style='color:#22c55e;'>MSS Bullish:</b> Giá phá vỡ Đỉnh cũ để đi lên. Vùng đỉnh cũ trở thành Hỗ trợ -> <b>Canh lệnh LONG</b>.<br/>
<b style='color:#ef4444;'>MSS Bearish:</b> Giá phá vỡ Đáy cũ để đi xuống. Vùng đáy cũ trở thành Kháng cự -> <b>Canh lệnh SHORT</b>.
</div>
</div>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #f59e0b;'>
<div style='font-size:13px; font-weight:700; color:#fcd34d; margin-bottom:4px;'>ATR (Average True Range)</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.5;'>
Chỉ báo đo lường biến động giá (Volatility). ATR càng cao nghĩa là biên độ dao động trong ngày càng rộng. Chúng ta dùng ATR để ước tính vùng kháng cự (R1) và hỗ trợ (S1) kỳ vọng cho ngày giao dịch tiếp theo.
</div>
</div>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #22c55e;'>
<div style='font-size:13px; font-weight:700; color:#86efac; margin-bottom:4px;'>ΔOC / HL Range</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.5;'>
<b>ΔOC (Open-Close):</b> Chênh lệch giữa giá Mở cửa và Đóng cửa (chiều dài thân nến). Thể hiện hướng đi dứt khoát của ngày hôm đó.<br/>
<b>HL Range (High-Low):</b> Khoảng cách từ đỉnh cao nhất đến đáy thấp nhất. Thể hiện tổng biên độ quét (biến động) toàn ngày.
</div>
</div>

</div>

<div style='background:#1a2035; padding:12px; border-radius:8px; border-left:3px solid #38bdf8; grid-column: 1 / -1;'>
<div style='font-size:13px; font-weight:700; color:#7dd3fc; margin-bottom:8px;'>🌊 Q1 – Q4 (SMART MONEY MATRIX / DÒNG TIỀN)</div>
<div style='font-size:12px; color:#94a3b8; line-height:1.6;'>
Trạng thái <b>Dòng Tiền Thông Minh (Smart Money - Managed Money)</b> dựa trên báo cáo COT. Ma trận này chia dòng tiền thành 4 góc phần tư (Quadrants) phản ánh chu kỳ mua/bán của Cá mập:
<div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:8px; margin-top:10px;'>
<div style='background:#0f1629; border-radius:6px; padding:8px; border-top:2px solid #22c55e;'>
<div style='font-size:12px; font-weight:700; color:#22c55e; margin-bottom:4px;'>Q1 (XANH) — GOM LONG</div>
<div style='font-size:11px; color:#94a3b8; line-height:1.5;'>Vị thế Net (Ròng) lớn hơn 0 và đang Tăng. Smart Money đang đổ tiền vào mua (Long). Động lượng mạnh, xu hướng tăng giá rõ rệt. <b>-> Ưu tiên đánh LONG.</b></div>
</div>
<div style='background:#0f1629; border-radius:6px; padding:8px; border-top:2px solid #ef4444;'>
<div style='font-size:12px; font-weight:700; color:#fca5a5; margin-bottom:4px;'>Q2 (ĐỎ) — XẢ LONG</div>
<div style='font-size:11px; color:#94a3b8; line-height:1.5;'>Vị thế Net vẫn lớn hơn 0 nhưng đang Giảm. Smart Money bắt đầu chốt lời lệnh Long cũ, dòng tiền rút ra. Giá có thể điều chỉnh giảm ngắn hạn. <b>-> Không mua đuổi, cẩn trọng đảo chiều.</b></div>
</div>
<div style='background:#0f1629; border-radius:6px; padding:8px; border-top:2px solid #eab308;'>
<div style='font-size:12px; font-weight:700; color:#fde047; margin-bottom:4px;'>Q3 (VÀNG) — ĐẨY SHORT</div>
<div style='font-size:11px; color:#94a3b8; line-height:1.5;'>Vị thế Net nhỏ hơn 0 và tiếp tục Giảm sâu hơn. Smart Money đang gia tăng bán khống (Short). Xu hướng giảm mạnh, lực ép giá rất lớn. <b>-> Ưu tiên đánh SHORT.</b></div>
</div>
<div style='background:#0f1629; border-radius:6px; padding:8px; border-top:2px solid #f97316;'>
<div style='font-size:12px; font-weight:700; color:#fdba74; margin-bottom:4px;'>Q4 (CAM) — COVER SHORT</div>
<div style='font-size:11px; color:#94a3b8; line-height:1.5;'>Vị thế Net nhỏ hơn 0 nhưng đang Tăng trở lại. Smart Money đang mua lại để chốt lời lệnh Short (Cover Short). Sức ép bán giảm bớt, giá thường tạo đáy và bật lên. <b>-> Canh LONG bắt sóng hồi.</b></div>
</div>
</div>
</div>
</div>

</div>
</div>
""", unsafe_allow_html=True)

