"""
seasonal_curve.py — Biểu đồ đường cong MÙA VỤ chuẩn hóa 0–100 (Năm hiện tại vs Trung bình 3Y / 5Y)
================================================================================================
- Nguồn dữ liệu : Hợp đồng liên tục ZW=F (ZW1!) và ZC=F (ZC1!) khung D1 lấy đồng nhất từ Yahoo Finance
                  (lưu cache tại Data/output/ZW1_daily.csv & ZC1_daily.csv, tự động cập nhật khi quá 1 giờ).
- Chuẩn hóa     : Mỗi năm riêng biệt, 0 = đáy của năm đó, 100 = đỉnh của năm đó
                  (năm hiện tại: đáy/đỉnh tính từ đầu năm đến ngày mới nhất).
- Trục X        : 52 tuần (T1..T12 = tháng 1..12).
- 3 đường       : Năm hiện tại (trắng) · TB 3 năm gần nhất (xanh lá nét đứt) · TB 5 năm gần nhất (xanh dương).
"""
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

_BASE = Path(__file__).parent
_OUT_DIR = _BASE / "Data" / "output"
_PRICE_DIR = _BASE / "Data" / "price" / "Gia 15 nam"

_CFG = {
    "ZW": {"label": "LÚA MÌ (ZW1!)", "yf": "ZW=F", "cache": "ZW1_daily.csv", "fallback": "ZW_nominal_daily_2011_2026.csv"},
    "ZC": {"label": "NGÔ (ZC1!)",    "yf": "ZC=F", "cache": "ZC1_daily.csv", "fallback": "CBOT_DL_ZC1!, 1D.csv"},
}

# Tuần bắt đầu của mỗi tháng (ngày thứ 1,32,60,... của năm) → nhãn T1..T12
_MONTH_START_DOY = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]


def _week_of_year(idx: pd.DatetimeIndex) -> pd.Index:
    return pd.Index(((idx.dayofyear.to_numpy() - 1) // 7 + 1).clip(max=52))


def _refresh_yf_cache(code: str) -> Path:
    """Tải nến D1 ZW=F / ZC=F từ yfinance nếu cache chưa có hoặc đã quá 1 giờ."""
    cfg = _CFG[code]
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _OUT_DIR / cfg["cache"]
    need_fetch = (not cache_path.exists()) or (time.time() - cache_path.stat().st_mtime > 3600)
    if need_fetch:
        try:
            import yfinance as yf
            cur_year = pd.Timestamp.now().year
            df = yf.Ticker(cfg["yf"]).history(start=f"{cur_year - 6}-01-01", interval="1d")
            if not df.empty:
                df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df.index.name = "Date"
                df = df[~df.index.duplicated(keep="last")].sort_index()
                df.to_csv(cache_path)
        except Exception:
            pass
    return cache_path


@st.cache_data(show_spinner=False, ttl=1800)
def _load_daily(code: str) -> pd.DataFrame:
    """Trả về DataFrame D1 đồng nhất của ZW1! / ZC1! (index=ngày; cột High, Low, Close)."""
    cfg = _CFG[code]
    cache_path = _refresh_yf_cache(code)
    if cache_path.exists():
        df = pd.read_csv(cache_path)
        df["Date"] = pd.to_datetime(df["Date"])
        return df.drop_duplicates("Date", keep="last").set_index("Date").sort_index()[["High", "Low", "Close"]]

    # Fallback nếu offline hoàn toàn và chưa có cache
    fb_path = _PRICE_DIR / cfg["fallback"]
    df = pd.read_csv(fb_path)
    t_col = "Date" if "Date" in df.columns else "time"
    df[t_col] = pd.to_datetime(df[t_col], utc=True).dt.tz_localize(None).dt.normalize()
    df = df.rename(columns={t_col: "Date", "high": "High", "low": "Low", "close": "Close"})
    return df.drop_duplicates("Date", keep="last").set_index("Date").sort_index()[["High", "Low", "Close"]]


def _year_curve(df_year: pd.DataFrame) -> pd.Series:
    """Chuẩn hóa 0–100 theo đỉnh/đáy của chính năm đó, gộp theo tuần (giá đóng cửa cuối tuần)."""
    lo, hi = float(df_year["Low"].min()), float(df_year["High"].max())
    if hi <= lo:
        return pd.Series(dtype=float)
    norm = (df_year["Close"] - lo) / (hi - lo) * 100.0
    wk = _week_of_year(norm.index)
    return norm.groupby(wk).last()


def _build(code: str):
    df = _load_daily(code)

    last_date = df.index.max()
    cur_year = last_date.year
    curves = {}
    for y in range(cur_year - 5, cur_year + 1):
        dy = df[df.index.year == y]
        if len(dy) >= 20:
            curves[y] = _year_curve(dy)

    weeks = list(range(1, 53))
    full = pd.DataFrame({y: c.reindex(weeks) for y, c in curves.items()}).interpolate(limit_area="inside")

    past = [y for y in sorted(curves) if y < cur_year]
    y3, y5 = past[-3:], past[-5:]
    avg3 = full[y3].mean(axis=1) if y3 else None
    avg5 = full[y5].mean(axis=1) if y5 else None
    cur = curves.get(cur_year)
    return df, last_date, cur_year, cur, avg3, avg5, y3, y5


def _render_chart(code: str):
    df, last_date, cur_year, cur, avg3, avg5, y3, y5 = _build(code)
    label = _CFG[code]["label"]
    cur_week = min((last_date.dayofyear - 1) // 7 + 1, 52)

    fig = go.Figure()
    if avg5 is not None:
        fig.add_trace(go.Scatter(
            x=avg5.index, y=avg5.round(1), mode="lines", name=f"TB 5 năm ({y5[0]}–{y5[-1]})",
            line=dict(color="#60a5fa", width=3), hovertemplate="T%{x}: %{y:.1f}<extra>TB 5 năm</extra>"))
    if avg3 is not None:
        fig.add_trace(go.Scatter(
            x=avg3.index, y=avg3.round(1), mode="lines", name=f"TB 3 năm ({y3[0]}–{y3[-1]})",
            line=dict(color="#4ade80", width=2, dash="dash"), hovertemplate="T%{x}: %{y:.1f}<extra>TB 3 năm</extra>"))
    if cur is not None:
        fig.add_trace(go.Scatter(
            x=cur.index, y=cur.round(1), mode="lines+markers", name=f"{cur_year} (hiện tại)",
            line=dict(color="#ffffff", width=3.5), marker=dict(size=5, color="#ffffff"),
            hovertemplate="W%{x}: %{y:.1f}<extra>" + str(cur_year) + "</extra>"))

    fig.add_vline(x=cur_week, line_dash="dot", line_color="#38bdf8", line_width=1,
                  annotation_text=f"W{cur_week}", annotation_font=dict(color="#38bdf8", size=11),
                  annotation_position="top")

    tick_w = [min((d - 1) // 7 + 1, 52) for d in _MONTH_START_DOY]
    fig.update_layout(
        height=430, margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="#0b1220", plot_bgcolor="#0b1220",
        font=dict(color="#94a3b8", family="Inter"),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11)),
        hovermode="x unified",
        xaxis=dict(tickmode="array", tickvals=tick_w, ticktext=[f"T{i}" for i in range(1, 13)],
                   range=[1, 52], gridcolor="#16233a", zeroline=False),
        yaxis=dict(range=[0, 100], dtick=25, gridcolor="#16233a", zeroline=False),
    )

    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:flex-end;margin:4px 0 2px;'>"
        f"<div><div style='font-size:15px;font-weight:800;color:#e2e8f0;'>{label} · {cur_year} VÀ ĐƯỜNG TRUNG BÌNH MÙA VỤ</div>"
        f"<div style='font-size:11px;color:#94a3b8;'>0 = đáy của năm · 100 = đỉnh của năm (nến D1 {_CFG[code]['yf']})</div></div>"
        f"<div style='font-size:11px;color:#94a3b8;text-align:right;'>"
        f"Xanh dương: TB 5Y ({y5[0]}–{y5[-1]}) · Xanh lá nét đứt: TB 3Y ({y3[0]}–{y3[-1]}) · Trắng: {cur_year} đến {last_date.date()}"
        f"</div></div>" if (y3 and y5) else f"<b>{label}</b>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"seasonal_curve_{code}")


def render_seasonal_curve():
    """Hiển thị biểu đồ đường cong mùa vụ với 2 tab: Lúa mì (mặc định) và Ngô."""
    st.markdown(
        "<div style='font-size:13px;font-weight:800;color:#38bdf8;letter-spacing:0.5px;margin:18px 0 6px;'>"
        "📈 ĐƯỜNG CONG MÙA VỤ — NĂM HIỆN TẠI vs TRUNG BÌNH 3 NĂM / 5 NĂM (CHUẨN HÓA 0–100)</div>",
        unsafe_allow_html=True,
    )
    tab_w, tab_c = st.tabs(["🌾 Lúa Mì (ZW1!)", "🌽 Ngô (ZC1!)"])
    with tab_w:
        _render_chart("ZW")
    with tab_c:
        _render_chart("ZC")
