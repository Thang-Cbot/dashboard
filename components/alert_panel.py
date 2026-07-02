"""
components/alert_panel.py
=========================
Component hiển thị Alert & Trạng Thái hệ thống dữ liệu.
Đọc từ Data/output/data_status.json để render real-time.
"""
import json
import datetime
from pathlib import Path
import streamlit.components.v1 as components


DATA_DIR = Path(__file__).parent.parent / "Data" / "output"
STATUS_FILE = DATA_DIR / "data_status.json"

# Map tên module → label hiển thị đẹp
MODULE_LABELS = {
    "usda":           "WASDE & Crop Progress",
    "prices":         "Gia H1 (ZC/ZW)",
    "macro":          "Vi Mo (Brent/DXY)",
    "cot":            "COT CFTC",
    "export_sales":   "Xuat Khau (Export Sales)",
    "weather_short":  "Thoi Tiet Ngan Han",
    "weather_long":   "ENSO / El Nino",
}

# Nhãn đẹp có dấu để hiển thị trên HTML (không dùng trong dict key)
MODULE_DISPLAY = {
    "usda":           "WASDE &amp; Crop Progress",
    "prices":         "Gi&aacute; H1 (ZC/ZW)",
    "macro":          "V&#297; M&ocirc; (Brent/DXY)",
    "cot":            "COT CFTC",
    "export_sales":   "Xu&#7845;t Kh&#7849;u (Export Sales)",
    "weather_short":  "Th&#7901;i Ti&#7871;t Ng&#7855;n H&#7841;n",
    "weather_long":   "ENSO / El Ni&ntilde;o",
}

# Khoảng thời gian tối đa trước khi cảnh báo "CŨ" (tính bằng giờ)
MAX_AGE_HOURS = {
    "usda":          36,
    "prices":         2,
    "macro":          2,
    "cot":           50,
    "export_sales":  50,
    "weather_short":  26,
    "weather_long":  170,
}


def _compute_age(updated_at_str: str) -> float:
    """Trả về số giờ kể từ lần cập nhật cuối. -1 nếu không parse được."""
    try:
        dt = datetime.datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.now() - dt
        return delta.total_seconds() / 3600
    except Exception:
        return -1


def _age_label(hours: float) -> str:
    if hours < 0:
        return "?"
    elif hours < 1:
        return f"{int(hours*60)}p truoc"
    elif hours < 24:
        return f"{hours:.1f}h truoc"
    else:
        return f"{hours/24:.1f}d truoc"


def load_status() -> dict:
    """Đọc data_status.json."""
    if not STATUS_FILE.exists():
        return {}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def render_alert_panel(st):
    """
    Render Alert Panel bằng Streamlit components.v1.html (bypass Markdown parser).
    """
    status_data = load_status()
    modules = status_data.get("modules", {})
    if not modules:
        modules = {k: v for k, v in status_data.items()
                   if isinstance(v, dict) and "status" in v}

    last_full = status_data.get("last_full_update", "")

    # Build rows
    rows = []
    for key in MODULE_LABELS:
        label_html = MODULE_DISPLAY[key]
        mod = modules.get(key, {})
        if not mod:
            icon = "&#9898;"   # ⚪
            color = "#64748b"
            age_text = "Chua chay"
            detail_text = ""
        else:
            if isinstance(mod, str):
                status_val = mod
                detail = ""
                updated_at = ""
            else:
                status_val = mod.get("status", "")
                detail = mod.get("detail", "")
                updated_at = mod.get("updated_at", "")

            hours = _compute_age(updated_at)
            max_age = MAX_AGE_HOURS.get(key, 48)

            if "ERROR" in status_val.upper() or "FAIL" in status_val.upper():
                icon = "&#128308;"  # 🔴
                color = "#ef4444"
            elif "PARTIAL" in status_val.upper() or "WARN" in status_val.upper():
                icon = "&#9888;"    # ⚠
                color = "#f59e0b"
            elif hours > max_age and hours > 0:
                icon = "&#128336;"  # 🕐
                color = "#94a3b8"
            else:
                icon = "&#9989;"    # ✅
                color = "#22c55e"

            age_text = _age_label(hours) if hours >= 0 else "?"
            detail_text = detail[:55] + "..." if len(detail) > 55 else detail

        sub = f" &middot; {detail_text}" if detail_text else ""
        rows.append(
            f'<div style="display:flex;align-items:flex-start;padding:7px 0;'
            f'border-bottom:1px solid #1e2d45;">'
            f'<span style="font-size:14px;margin-right:8px;">{icon}</span>'
            f'<div style="flex:1;">'
            f'<div style="font-size:12px;font-weight:600;color:{color};">{label_html}</div>'
            f'<div style="font-size:10px;color:#64748b;">{age_text}{sub}</div>'
            f'</div></div>'
        )

    scan_line = (f'<div style="font-size:11px;color:#64748b;margin-bottom:10px;">'
                 f'&#128336; Full scan: {last_full}</div>') if last_full else ""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; padding:0; background:transparent; }}
</style>
</head>
<body>
<div style="background:linear-gradient(135deg,#1a2035 0%,#0f1629 100%);
            border:1px solid #2a3a5c;border-radius:12px;padding:16px;
            font-family:Inter,sans-serif;">
  <div style="font-size:14px;font-weight:700;color:#e2e8f0;letter-spacing:1px;
              border-bottom:1px solid #2a3a5c;padding-bottom:8px;margin-bottom:12px;">
    &#128276; ALERT &amp; TRANG THAI HE THONG
  </div>
  {scan_line}
  {"".join(rows)}
</div>
</body>
</html>"""

    # Dùng components.v1.html để bypass Markdown parser hoàn toàn
    components.html(html, height=len(rows) * 52 + 100, scrolling=False)

    # Nút Refresh
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("&#128260; Lam Moi Trang Thai", use_container_width=True, key="refresh_alert"):
        st.rerun()
