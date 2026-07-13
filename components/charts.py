"""
components/charts.py
====================
Plotly chart components dùng chung cho toàn bộ Streamlit Dashboard.
v3 — Real H1 Candles + SMC Liquidity Zones (PDH/PDL/FVG) + EMA 21/50 + Volume
"""
import json
import datetime
from pathlib import Path

try:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

COLORS = {
    "ZC": "#f59e0b",
    "ZW": "#60a5fa",
    "bg": "#0f1629",
    "grid": "#1e2d45",
    "text": "#e2e8f0",
}

CHART_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["bg"],
    font=dict(color=COLORS["text"], family="Inter"),
    margin=dict(l=10, r=10, t=45, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["grid"], orientation="h", y=1.08, x=0),
)


def load_price_csv(commodity: str, suffix: str = "active") -> "pd.DataFrame | None":
    """Đọc file CSV H1 cho commodity (ZC/ZW), suffix (active/swing/dca)."""
    if not HAS_PLOTLY:
        return None
    path = DATA_OUTPUT / f"{commodity}_{suffix}_H1.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.lower() in ['datetime', 'date', 'timestamp', 'time']), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
            df = df.rename(columns={date_col: "Datetime"})
        return df
    except Exception:
        return None


def compute_smc_zones(df: "pd.DataFrame") -> dict:
    """
    Tính toán các vùng Thanh Khoản theo chuẩn SMC từ DataFrame H1 thực tế.
    Trả về dict gồm: pdh, pdl, fvg_list (các Fair Value Gap H1 gần nhất).
    """
    zones = {"pdh": None, "pdl": None, "fvg_list": [], "mss_list": []}
    if df is None or df.empty or len(df) < 5:
        return zones

    # ── PDH / PDL: Đỉnh và Đáy của ngày giao dịch hoàn chỉnh gần nhất ──
    try:
        df["_date"] = df["Datetime"].dt.date
        today_date = df["_date"].max()
        # Lấy ngày hôm qua (ngày giao dịch trước ngày mới nhất trong data)
        unique_dates = sorted(df["_date"].unique())
        if len(unique_dates) >= 2:
            prev_date = unique_dates[-2]
            prev_day_df = df[df["_date"] == prev_date]
            if not prev_day_df.empty:
                zones["pdh"] = float(prev_day_df["High"].max())
                zones["pdl"] = float(prev_day_df["Low"].min())
        df.drop(columns=["_date"], inplace=True, errors="ignore")
    except Exception:
        pass

    # ── MSS (Market Structure Shift) ──
    try:
        recent = df.tail(120).reset_index(drop=True)
        mss_list = []
        last_sh = None
        last_sl = None
        
        for i in range(2, len(recent) - 2):
            is_sh = recent.loc[i, "High"] > max(recent.loc[i-1, "High"], recent.loc[i-2, "High"], recent.loc[i+1, "High"], recent.loc[i+2, "High"])
            is_sl = recent.loc[i, "Low"] < min(recent.loc[i-1, "Low"], recent.loc[i-2, "Low"], recent.loc[i+1, "Low"], recent.loc[i+2, "Low"])
            
            if is_sh:
                last_sh = {"index": i, "price": recent.loc[i, "High"], "time": recent.loc[i, "Datetime"]}
            if is_sl:
                last_sl = {"index": i, "price": recent.loc[i, "Low"], "time": recent.loc[i, "Datetime"]}
                
            close_price = recent.loc[i, "Close"]
            
            # Bullish MSS
            if last_sh and close_price > last_sh["price"] and i > last_sh["index"]:
                mss_level = last_sh["price"]
                sub_lows = recent.loc[i+1:, "Low"]
                mitigated = False
                if not sub_lows.empty and sub_lows.min() <= mss_level:
                    mitigated = True
                mss_list.append({"type": "bullish", "level": float(mss_level), "mitigated": mitigated})
                last_sh = None # reset
                
            # Bearish MSS
            elif last_sl and close_price < last_sl["price"] and i > last_sl["index"]:
                mss_level = last_sl["price"]
                sub_highs = recent.loc[i+1:, "High"]
                mitigated = False
                if not sub_highs.empty and sub_highs.max() >= mss_level:
                    mitigated = True
                mss_list.append({"type": "bearish", "level": float(mss_level), "mitigated": mitigated})
                last_sl = None # reset

        zones["mss_list"] = mss_list[-3:] # Giữ 3 cái gần nhất
    except Exception:
        pass

    # ── FVG (Fair Value Gap): Tìm trong 80 nến gần nhất ──
    try:
        recent = df.tail(80).reset_index(drop=True)
        fvg_list = []
        for i in range(2, len(recent)):
            h_i2 = recent.loc[i - 2, "High"]
            l_i2 = recent.loc[i - 2, "Low"]
            h_i  = recent.loc[i, "High"]
            l_i  = recent.loc[i, "Low"]
            dt_i = recent.loc[i, "Datetime"]

            if l_i > h_i2:  # Bullish FVG
                sub_lows = recent.loc[i+1:, "Low"]
                mitigated = False
                # Nếu giá quét xuống dưới bottom (h_i2) là đã lấp toàn bộ
                if not sub_lows.empty and sub_lows.min() <= h_i2:
                    mitigated = True
                fvg_list.append({
                    "type": "bullish",
                    "top": float(l_i),
                    "bottom": float(h_i2),
                    "time": dt_i,
                    "mitigated": mitigated
                })
            elif h_i < l_i2:  # Bearish FVG
                sub_highs = recent.loc[i+1:, "High"]
                mitigated = False
                # Nếu giá quét lên trên top (l_i2) là đã lấp toàn bộ
                if not sub_highs.empty and sub_highs.max() >= l_i2:
                    mitigated = True
                fvg_list.append({
                    "type": "bearish",
                    "top": float(l_i2),
                    "bottom": float(h_i),
                    "time": dt_i,
                    "mitigated": mitigated
                })

        # Lấy 5 FVG gần nhất để hiển thị
        zones["fvg_list"] = fvg_list[-5:]
    except Exception:
        pass

    return zones


def render_candlestick(st, commodity: str, suffix: str = "active", n_candles: int = 150):
    """
    Render biểu đồ nến H1 thực tế với:
    - 150 nến H1 thực tế gần nhất
    - EMA 21 (xanh dương) + EMA 50 (vàng)
    - PDH / PDL (đường nét đứt)
    - FVG Zones (ô màu mờ)
    - Volume subplot phía dưới
    """
    if not HAS_PLOTLY:
        st.warning("Cần cài plotly: `pip install plotly`")
        return

    df = load_price_csv(commodity, suffix)
    if df is None or df.empty:
        st.warning(f"Chưa có dữ liệu H1 thực tế cho {commodity} ({suffix}). Hãy chạy lệnh cập nhật dữ liệu.")
        return

    # Lấy n_candles nến gần nhất
    df = df.tail(n_candles).reset_index(drop=True)

    # Tính SMC zones
    smc = compute_smc_zones(load_price_csv(commodity, suffix))

    names = {"ZC": "Ngô (Corn)", "ZW": "Lúa Mì (Wheat)"}
    contract_name = names.get(commodity, commodity)
    last_dt = df["Datetime"].iloc[-1]
    last_close = df["Close"].iloc[-1]

    # Subplot: 2 hàng (nến + volume)
    has_vol = "Volume" in df.columns and df["Volume"].sum() > 0
    row_heights = [0.75, 0.25] if has_vol else [1.0]
    rows = 2 if has_vol else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # ── 1. Nến H1 thực tế ──
    fig.add_trace(go.Candlestick(
        x=df["Datetime"],
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="H1 Thực Tế",
        increasing_line_color="#22c55e",
        decreasing_line_color="#ef4444",
        increasing_fillcolor="#166534",
        decreasing_fillcolor="#7f1d1d",
    ), row=1, col=1)

    # ── 2. EMA 21 & EMA 50 ──
    if "EMA_21" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Datetime"], y=df["EMA_21"],
            name="EMA 21", mode="lines",
            line=dict(color="#60a5fa", width=1.5),
        ), row=1, col=1)
    if "EMA_50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Datetime"], y=df["EMA_50"],
            name="EMA 50", mode="lines",
            line=dict(color="#f59e0b", width=1.5, dash="dot"),
        ), row=1, col=1)

    # ── 3. PDH / PDL (Đỉnh/Đáy ngày hôm qua) ──
    x_start = df["Datetime"].iloc[0]
    x_end   = df["Datetime"].iloc[-1] + datetime.timedelta(hours=4)  # kéo dài chút

    if smc["pdh"] is not None:
        fig.add_hline(
            y=smc["pdh"], line_dash="dash", line_color="#fb923c", line_width=1.2,
            annotation_text=f"PDH {smc['pdh']:.2f}",
            annotation_font=dict(size=10, color="#fb923c"),
            annotation_position="top right",
            row=1, col=1,
        )
    if smc["pdl"] is not None:
        fig.add_hline(
            y=smc["pdl"], line_dash="dash", line_color="#a78bfa", line_width=1.2,
            annotation_text=f"PDL {smc['pdl']:.2f}",
            annotation_font=dict(size=10, color="#a78bfa"),
            annotation_position="bottom right",
            row=1, col=1,
        )

    # ── 4. FVG Zones (Vùng chưa lấp) ──
    for fvg in smc.get("fvg_list", []):
        color = "rgba(34,197,94,0.12)" if fvg["type"] == "bullish" else "rgba(239,68,68,0.12)"
        border = "#22c55e" if fvg["type"] == "bullish" else "#ef4444"
        label  = f"FVG {'🟢' if fvg['type'] == 'bullish' else '🔴'} {fvg['bottom']:.0f}-{fvg['top']:.0f}"
        fig.add_hrect(
            y0=fvg["bottom"], y1=fvg["top"],
            fillcolor=color, opacity=1.0,
            line_width=0.8, line_color=border, line_dash="dot",
            annotation_text=label,
            annotation_font=dict(size=9, color=border),
            annotation_position="top left",
            row=1, col=1,
        )

    # ── 5. Volume subplot ──
    if has_vol:
        vol_colors = [
            "#22c55e" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#ef4444"
            for i in range(len(df))
        ]
        fig.add_trace(go.Bar(
            x=df["Datetime"], y=df["Volume"],
            name="Volume", marker_color=vol_colors,
            opacity=0.7, showlegend=False,
        ), row=2, col=1)

    # ── Layout ──
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=f"📈 {contract_name} — {n_candles} nến H1 thực tế | Giá: <b>{last_close:.2f}¢</b> | {last_dt.strftime('%d/%m %H:%M')}",
            font=dict(size=13),
        ),
        xaxis_rangeslider_visible=False,
        height=500,
    )

    # Ẩn khoảng trắng ngoài giờ giao dịch (Thứ 7, CN)
    fig.update_xaxes(
        gridcolor=COLORS["grid"], showgrid=True, zeroline=False,
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    fig.update_yaxes(gridcolor=COLORS["grid"], showgrid=True, zeroline=False)

    st.plotly_chart(fig, use_container_width=True)
    return smc  # trả về để 2_Profiles.py dùng hiển thị bảng


def get_smc_zones_for_display(commodity: str, suffix: str = "active") -> dict:
    """Hàm tiện ích: trả về dict SMC zones để hiển thị trong bảng UI."""
    df = load_price_csv(commodity, suffix)
    return compute_smc_zones(df)


def render_macro_bar(st, macro_data: dict):
    """Render bảng vĩ mô: Brent, DXY."""
    if not macro_data:
        return

    items = []
    for key, label in [("brent", "Brent Oil"), ("dxy", "DXY"), ("zw_ref", "ZW Ref")]:
        d = macro_data.get(key, {})
        if d:
            items.append({
                "label": label,
                "price": d.get("price", "—"),
                "change_pct": d.get("change_pct", 0),
            })

    if not items or not HAS_PLOTLY:
        return

    cols = st.columns(len(items))
    for i, item in enumerate(items):
        pct = item["change_pct"] or 0
        color = "#22c55e" if pct >= 0 else "#ef4444"
        arrow = "▲" if pct >= 0 else "▼"
        cols[i].markdown(f"""
        <div style='background:#1a2035; border-radius:8px; padding:12px; text-align:center;
                    border:1px solid #2a3a5c;'>
            <div style='font-size:11px; color:#64748b; font-weight:600;'>{item['label']}</div>
            <div style='font-size:20px; font-weight:700; color:#e2e8f0;'>{item['price']:.2f}</div>
            <div style='font-size:13px; color:{color}; font-weight:600;'>{arrow} {abs(pct):.2f}%</div>
        </div>""", unsafe_allow_html=True)
