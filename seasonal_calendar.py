"""
seasonal_calendar.py — La Bàn Mùa Vụ 12 Tháng (ZW & ZC)

Hiển thị lịch mùa vụ dạng Timeline/Mindmap:
  - Nhánh trên: Lúa Mì (ZW) — màu Cam
  - Trục giữa: 12 tháng + đường minh họa chu kỳ mùa vụ (định tính) + mốc Đỉnh/Đáy
  - Nhánh dưới: Ngô (ZC) — màu Vàng
  - Tháng hiện tại được làm nổi bật và đối chiếu với Macro Score thực tế.

Dữ liệu mùa vụ: Data/seasonal_calendar.json (có thể chỉnh sửa trực tiếp).
Dữ liệu vĩ mô:  Data/output/macro_scores_zw.json, macro_scores_zc.json
"""
import json
from datetime import datetime
from pathlib import Path

import streamlit.components.v1 as components

BASE_DIR = Path(__file__).parent
CAL_FILE = BASE_DIR / "Data" / "seasonal_calendar.json"
OUT_DIR = BASE_DIR / "Data" / "output"

COLORS = {"ZW": "#f97316", "ZC": "#84cc16"}
NAMES = {"ZW": "🌾 Lúa Mì (ZW)", "ZC": "🌽 Ngô (ZC)"}
MONTHS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
QUARTERS = [("🌱 QUÝ 1", 0), ("☀️ QUÝ 2", 3), ("🍂 QUÝ 3", 6), ("❄️ QUÝ 4", 9)]

BIAS = {
    "up":    ("▲ Tăng",     "#22c55e"),
    "down":  ("▼ Giảm",     "#ef4444"),
    "flat":  ("◆ Đi ngang", "#94a3b8"),
    "mixed": ("⇅ Hỗn hợp",  "#a78bfa"),
}

COL_W = 120          # px per month column
N = 12
TOTAL_W = COL_W * N  # 1440


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _macro_bias(score):
    if score is None:
        return "flat", "Chưa có dữ liệu"
    if score >= 55:
        return "up", "Tăng"
    if score <= 45:
        return "down", "Giảm"
    return "flat", "Đi ngang"


def _consensus(season_bias, macro_bias):
    if season_bias in ("flat", "mixed") or macro_bias == "flat":
        return "Chưa đồng thuận rõ ràng — theo dõi thêm", "#94a3b8"
    if season_bias == macro_bias:
        txt = "ĐỒNG THUẬN TĂNG" if season_bias == "up" else "ĐỒNG THUẬN GIẢM"
        return txt + " (Mùa vụ + Vĩ mô cùng chiều)", BIAS[season_bias][1]
    s = BIAS[season_bias][0]
    m = BIAS[macro_bias][0]
    return f"PHÂN KỲ — Mùa vụ {s} nhưng Vĩ mô {m}", "#f59e0b"


def _smooth_path(points):
    """Catmull-Rom → cubic Bezier path."""
    if len(points) < 2:
        return ""
    d = f"M {points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C {c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def _curve_svg(cal, cur_m):
    H, PAD = 170, 22
    svg = [f"<svg width='{TOTAL_W}' height='{H}' viewBox='0 0 {TOTAL_W} {H}' xmlns='http://www.w3.org/2000/svg'>"]
    # grid
    for i in range(1, N):
        x = i * COL_W
        svg.append(f"<line x1='{x}' y1='0' x2='{x}' y2='{H}' stroke='#1e2d45' stroke-width='1'/>")
    # current month band
    cx0 = (cur_m - 1) * COL_W
    svg.append(f"<rect x='{cx0}' y='0' width='{COL_W}' height='{H}' fill='#38bdf8' fill-opacity='0.07'/>")
    svg.append(f"<line x1='{cx0 + COL_W/2}' y1='0' x2='{cx0 + COL_W/2}' y2='{H}' stroke='#38bdf8' stroke-dasharray='4 4' stroke-width='1.5'/>")

    for com in ("ZW", "ZC"):
        data = cal.get(com, {})
        pts = []
        for m in range(1, 13):
            v = data.get(str(m), {}).get("curve", 50)
            x = (m - 1) * COL_W + COL_W / 2
            y = PAD + (100 - v) / 100 * (H - 2 * PAD)
            pts.append((x, y))
        col = COLORS[com]
        svg.append(f"<path d='{_smooth_path(pts)}' fill='none' stroke='{col}' stroke-width='3' stroke-linecap='round' opacity='0.95'/>")
        for m, (x, y) in enumerate(pts, start=1):
            mk = data.get(str(m), {}).get("marker")
            if mk:
                is_peak = mk == "peak"
                label = ("ĐỈNH " if is_peak else "ĐÁY ") + com
                ty = y - 12 if is_peak else y + 20
                svg.append(f"<circle cx='{x}' cy='{y}' r='7' fill='{col}' stroke='#0b0f19' stroke-width='2'/>")
                svg.append(f"<text x='{x}' y='{ty}' fill='{col}' font-size='10' font-weight='800' text-anchor='middle'>{'▲' if is_peak else '▼'} {label}</text>")
            else:
                svg.append(f"<circle cx='{x}' cy='{y}' r='3' fill='{col}'/>")
    svg.append("</svg>")
    return "".join(svg)


def _card(com, m, item, cur_m, below=False):
    col = COLORS[com]
    b_txt, b_col = BIAS.get(item.get("bias", "flat"), BIAS["flat"])
    mk = item.get("marker")
    mk_html = ""
    if mk == "peak":
        mk_html = f"<div class='mk' style='background:{col}22;color:{col};border:1px solid {col};'>🔺 VÙNG ĐỈNH</div>"
    elif mk == "bottom":
        mk_html = f"<div class='mk' style='background:{col}22;color:{col};border:1px solid {col};'>🔻 VÙNG ĐÁY</div>"
    cur_cls = " cur" if m == cur_m else ""
    side = "bottom" if below else "top"
    return f"""
    <div class='cell'>
      {"<div class='stem' style='background:"+col+"'></div>" if below else ""}
      <div class='card{cur_cls}' style='border-{side}:3px solid {col};' title="{item.get('detail','')}">
        <div class='focus' style='color:{col};'>{item.get('focus','—')}</div>
        <div class='bias' style='color:{b_col};'>{b_txt}</div>
        {mk_html}
        <div class='detail'>{item.get('detail','')}</div>
      </div>
      {"" if below else "<div class='stem' style='background:"+col+"'></div>"}
    </div>"""


def render_seasonal_calendar(height=900):
    cal = _load(CAL_FILE)
    if not cal:
        components.html("<div style='color:#ef4444'>Không tìm thấy Data/seasonal_calendar.json</div>", height=40)
        return

    cur_m = datetime.now().month

    # ── Current-month panel (Mùa vụ vs Vĩ mô) ──
    panel = ""
    for com in ("ZW", "ZC"):
        mac = _load(OUT_DIR / f"macro_scores_{com.lower()}.json")
        score = mac.get("total_score")
        trend = mac.get("trend", "—")
        ts = mac.get("timestamp", "—")
        item = cal.get(com, {}).get(str(cur_m), {})
        s_bias = item.get("bias", "flat")
        m_bias, m_txt = _macro_bias(score)
        cons_txt, cons_col = _consensus(s_bias, m_bias)
        s_lbl, s_col = BIAS.get(s_bias, BIAS["flat"])
        m_lbl, m_col = BIAS[m_bias]
        col = COLORS[com]
        score_txt = f"{score:.1f}/100" if isinstance(score, (int, float)) else "N/A"
        panel += f"""
        <div class='pbox' style='border-left:4px solid {col};'>
          <div class='ptitle' style='color:{col};'>{NAMES[com]} — Tháng {cur_m}: {item.get('focus','—')}</div>
          <div class='prow'>
            <div><span class='plbl'>Xu hướng mùa vụ (lịch sử)</span><br><b style='color:{s_col};'>{s_lbl}</b></div>
            <div><span class='plbl'>Vĩ mô hiện tại (Macro Score)</span><br><b style='color:{m_col};'>{m_lbl}</b> <span class='pdim'>{score_txt} · {trend}</span></div>
          </div>
          <div class='pcons' style='color:{cons_col};border-color:{cons_col}55;'>⚖️ {cons_txt}</div>
          <div class='pdim' style='margin-top:4px;'>⏱ Macro cập nhật: {ts}</div>
        </div>"""

    # ── Quarter header ──
    q_html = "".join(
        f"<div class='q' style='width:{COL_W*3}px;'>{name}</div>" for name, _ in QUARTERS
    )

    # ── Month axis ──
    axis = ""
    for i, mn in enumerate(MONTHS, start=1):
        cls = "node cur" if i == cur_m else "node"
        axis += f"<div class='axcell'><div class='{cls}'>{mn}</div></div>"

    zw_cards = "".join(_card("ZW", m, cal.get("ZW", {}).get(str(m), {}), cur_m) for m in range(1, 13))
    zc_cards = "".join(_card("ZC", m, cal.get("ZC", {}).get(str(m), {}), cur_m, below=True) for m in range(1, 13))

    html = f"""
<html><head><meta charset='utf-8'>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
body {{ margin:0; background:transparent; font-family:'Inter',sans-serif; color:#cbd5e1; overflow-x:hidden; }}
.wrap {{ width:100%; box-sizing:border-box; padding:4px 0; }}
.hdr {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px; padding:0 4px; }}
.title {{ font-size:15px; font-weight:800; color:#e2e8f0; letter-spacing:1px; }}
.legend span {{ font-size:11px; margin-left:14px; font-weight:700; }}
.panel {{ display:flex; gap:12px; margin-bottom:14px; flex-wrap:wrap; }}
.pbox {{ flex:1; min-width:360px; background:#111827; border:1px solid #1e2d45; border-radius:10px; padding:10px 14px; }}
.ptitle {{ font-size:13px; font-weight:800; margin-bottom:6px; }}
.prow {{ display:flex; gap:28px; font-size:13px; }}
.plbl {{ font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.5px; }}
.pdim {{ font-size:10px; color:#64748b; }}
.pcons {{ margin-top:8px; font-size:12px; font-weight:800; border:1px dashed; border-radius:6px; padding:4px 8px; display:inline-block; }}
.scroll {{ overflow-x:auto; padding-bottom:6px; }}
.board {{ width:{TOTAL_W}px; }}
.qrow, .row, .axis {{ display:flex; }}
.q {{ text-align:center; font-size:11px; font-weight:800; color:#94a3b8; letter-spacing:1px; padding:4px 0; border-bottom:1px solid #2a3a5c; }}
.cell {{ width:{COL_W}px; box-sizing:border-box; padding:0 4px; display:flex; flex-direction:column; align-items:center; }}
.card {{ width:100%; box-sizing:border-box; height:178px; overflow:hidden; background:#111827; border:1px solid #1e2d45;
         border-radius:8px; padding:7px 7px; transition:transform .15s; }}
.card:hover {{ transform:scale(1.04); background:#162033; overflow:visible; z-index:5; }}
.card.cur {{ box-shadow:0 0 0 2px #38bdf8, 0 0 18px #38bdf866; background:#0f1d33; }}
.focus {{ font-size:11px; font-weight:800; line-height:1.3; min-height:28px; }}
.bias {{ font-size:11px; font-weight:800; margin:3px 0; }}
.mk {{ font-size:9.5px; font-weight:800; border-radius:4px; padding:1px 4px; display:inline-block; margin-bottom:3px; }}
.detail {{ font-size:10px; color:#94a3b8; line-height:1.4; }}
.stem {{ width:2px; height:12px; opacity:.7; }}
.axcell {{ width:{COL_W}px; display:flex; justify-content:center; }}
.node {{ width:44px; height:24px; border-radius:12px; background:#1e293b; color:#cbd5e1; font-size:11px; font-weight:800;
         display:flex; align-items:center; justify-content:center; border:1px solid #334155; }}
.node.cur {{ background:#0ea5e9; color:#0b0f19; border-color:#38bdf8; box-shadow:0 0 12px #38bdf8; }}
.foot {{ font-size:10px; color:#475569; margin-top:8px; }}
</style></head><body>
<div class='wrap'>
  <div class='hdr'>
    <div class='title'>🧭 LA BÀN MÙA VỤ 12 THÁNG — CHU KỲ ĐỈNH / ĐÁY</div>
    <div class='legend'>
      <span style='color:{COLORS["ZW"]};'>━ 🌾 Lúa Mì (ZW)</span>
      <span style='color:{COLORS["ZC"]};'>━ 🌽 Ngô (ZC)</span>
      <span style='color:#38bdf8;'>▌Tháng hiện tại</span>
    </div>
  </div>
  <div class='panel'>{panel}</div>
  <div class='scroll'><div class='board' id='board'>
    <div class='qrow'>{q_html}</div>
    <div style='font-size:10px;color:{COLORS["ZW"]};font-weight:800;margin:6px 0 4px 4px;'>🌾 NHÁNH LÚA MÌ (ZW)</div>
    <div class='row'>{zw_cards}</div>
    {_curve_svg(cal, cur_m)}
    <div class='axis'>{axis}</div>
    <div class='row'>{zc_cards}</div>
    <div style='font-size:10px;color:{COLORS["ZC"]};font-weight:800;margin:4px 0 0 4px;'>🌽 NHÁNH NGÔ (ZC)</div>
  </div></div>
  <div class='foot'>📌 Đường cong là minh họa định tính chu kỳ mùa vụ (theo Hồ sơ Mùa vụ & backtest 10 năm), KHÔNG phải giá thực tế.
  "Xu hướng mùa vụ" là quy luật lịch sử; "Vĩ mô hiện tại" lấy từ Macro Score (≥55 Tăng · ≤45 Giảm · còn lại Đi ngang).
  Rê chuột vào thẻ để xem đầy đủ.</div>
</div>
<script>
  function fitBoard() {{
    var b = document.getElementById('board');
    var avail = b.parentElement.clientWidth;
    var s = Math.min(1, avail / {TOTAL_W});
    b.style.zoom = s;
  }}
  window.addEventListener('resize', fitBoard);
  window.addEventListener('load', fitBoard);
  fitBoard();
</script>
</body></html>"""
    components.html(html, height=height, scrolling=True)
