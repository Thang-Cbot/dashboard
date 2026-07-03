"""
components/charts.py
====================
Plotly chart components dùng chung cho toàn bộ Streamlit Dashboard.
"""
import json
import datetime
from pathlib import Path

try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

DATA_OUTPUT = Path(__file__).parent.parent / "Data" / "output"

COLORS = {
    "ZC": "#f59e0b",   # Vàng — Ngô
    "ZW": "#60a5fa",   # Xanh dương - Lúa Mì
    "bg": "#0f1629",
    "grid": "#1e2d45",
    "text": "#e2e8f0",
}

CHART_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["bg"],
    font=dict(color=COLORS["text"], family="Inter"),
    xaxis=dict(gridcolor=COLORS["grid"], showgrid=True, zeroline=False),
    yaxis=dict(gridcolor=COLORS["grid"], showgrid=True, zeroline=False),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["grid"]),
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
        # Chuẩn hóa tên cột
        df.columns = [c.strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.lower() in ['datetime', 'date', 'timestamp', 'time']), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(date_col)
            df = df.rename(columns={date_col: "Datetime"})
        return df
    except Exception:
        return None


def render_candlestick(st, commodity: str, suffix: str = "active", n_candles: int = 100):
    """Render biểu đồ nến H1: Nến giả lập (AI) nguyên tuần + Chấm vàng giá thực tế."""
    if not HAS_PLOTLY:
        st.warning("Cần cài plotly: `pip install plotly`")
        return

    fig = go.Figure()

    # 1. Đọc dữ liệu mô phỏng AI
    sim_path = DATA_OUTPUT / "ai_simulated_h1.json"
    sim_df = None
    if sim_path.exists():
        try:
            with open(sim_path, "r", encoding="utf-8") as f:
                sim_data = json.load(f)
            if commodity in sim_data:
                sim_df = pd.DataFrame(sim_data[commodity])
                sim_df["Datetime"] = pd.to_datetime(sim_df["Datetime"])
        except Exception as e:
            st.warning(f"Lỗi đọc AI simulation: {e}")

    # Xác định khung hiển thị tuần giao dịch
    now = datetime.datetime.now()
    
    # Nếu có dữ liệu giả lập, dịch khung hiển thị sang tuần bắt đầu của chuỗi giả lập
    if sim_df is not None and not sim_df.empty:
        target_date = sim_df["Datetime"].min()
    else:
        target_date = now

    monday = target_date - datetime.timedelta(days=target_date.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    friday = monday + datetime.timedelta(days=4)
    friday = friday.replace(hour=23, minute=59, second=59)

    # (Đã di chuyển logic đọc AI lên trên)

    # 2. Vẽ nến (Ưu tiên nến AI, nếu không có thì dùng nến thực)
    df_actual = load_price_csv(commodity, suffix)
    
    if sim_df is not None and not sim_df.empty:
        fig.add_trace(go.Candlestick(
            x=sim_df["Datetime"],
            open=sim_df["Open"],
            high=sim_df["High"],
            low=sim_df["Low"],
            close=sim_df["Close"],
            name=f"{commodity} AI Forecast",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
            opacity=1.0 # Người dùng yêu cầu màu bình thường
        ))
    elif df_actual is not None and not df_actual.empty:
        # Fallback: Nếu không có AI simulation, hiển thị nến thật cắt theo tuần
        df_real_week = df_actual[df_actual["Datetime"] >= monday]
        fig.add_trace(go.Candlestick(
            x=df_real_week["Datetime"],
            open=df_real_week["Open"],
            high=df_real_week["High"],
            low=df_real_week["Low"],
            close=df_real_week["Close"],
            name=f"{commodity} Real H1",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        ))

    # 3. Vẽ đường giá thực tế (chấm vàng)
    if df_actual is not None and not df_actual.empty:
        # Lọc dữ liệu thực tế chỉ lấy từ Thứ 2 trở đi
        df_real_week = df_actual[df_actual["Datetime"] >= monday]
        if not df_real_week.empty:
            fig.add_trace(go.Scatter(
                x=df_real_week["Datetime"],
                y=df_real_week["Close"],
                mode="lines+markers",
                name="Giá Thực Tế",
                line=dict(color="#facc15", width=2), # Yellow
                marker=dict(color="#facc15", size=6, symbol="circle")
            ))

        # Thêm EMA & Cản dựa trên dữ liệu thực tế MỚI NHẤT
        last_row = df_real_week.iloc[-1] if not df_real_week.empty else df_actual.iloc[-1]
        
        if "EMA_21" in df_actual.columns:
            fig.add_trace(go.Scatter(
                x=df_real_week["Datetime"], y=df_real_week["EMA_21"],
                name="EMA 21", line=dict(color="#60a5fa", width=1.5), mode="lines"
            ))
        if "EMA_50" in df_actual.columns:
            fig.add_trace(go.Scatter(
                x=df_real_week["Datetime"], y=df_real_week["EMA_50"],
                name="EMA 50", line=dict(color="#f59e0b", width=1.5, dash="dot"), mode="lines"
            ))

        for level_col, level_name, lcolor in [
            ("S1", "S1", "#ef4444"), ("S2", "S2", "#dc2626"),
            ("R1", "R1", "#22c55e"), ("R2", "R2", "#16a34a"),
        ]:
            if level_col in df_actual.columns and not pd.isna(last_row[level_col]):
                fig.add_hline(
                    y=last_row[level_col],
                    line_dash="dot", line_color=lcolor, line_width=1,
                    annotation_text=f"{level_name}: {last_row[level_col]:.2f}",
                    annotation_font=dict(size=10, color=lcolor),
                )

    names = {"ZC": "Ngô (Corn)", "ZW": "Lúa Mì (Wheat)", "ZS": "Đậu Tương (Soybeans)"}
    
    # Thiết lập khung hiển thị cố định trong 1 tuần
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"📈 {names.get(commodity, commodity)} — Tuần Này ({monday.strftime('%d/%m')} - {friday.strftime('%d/%m')})", font=dict(size=14)),
        xaxis_rangeslider_visible=False,
        xaxis_range=[monday, friday],
        height=420,
    )
    
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Ẩn thứ 7, Chủ nhật
            dict(bounds=[2, 7], pattern="hour"),  # Ẩn khoảng trống từ 2h sáng đến 7h sáng
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)


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
