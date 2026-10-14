"""
crop_compare.py — So sánh USDA Crop Progress với cùng kỳ năm trước & trung bình 5 năm
======================================================================================
- Tiến độ (gieo trồng / thu hoạch / chín / nảy mầm): USDA đã in sẵn cột "năm trước"
  và "TB 5 năm" trong báo cáo. Nếu cột năm trước là (NA) thì lấy từ lịch sử tự lưu.
- Chất lượng (Good + Excellent): báo cáo chỉ có tuần hiện tại -> tự tính từ lịch sử
  Data/output/crop_progress_history.json (có thể backfill bằng backfill_crop_history.py).

Dùng trong usda_crawler.py:
    import crop_compare
    prog_compare = crop_compare.run(report_text)   # {"ZC": {...}, "ZW": {...}}
"""
import re
import json
import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "Data" / "output" / "crop_progress_history.json"

# (key, tiêu đề bảng trong báo cáo, loại, mã hàng hóa, nhãn tiếng Việt)
SPECS = [
    ("corn_planted",   "Corn Planted",            "progress",  "ZC", "Gieo trồng ngô"),
    ("corn_mature",    "Corn Mature",             "progress",  "ZC", "Ngô chín (Mature)"),
    ("corn_harvested", "Corn Harvested",          "progress",  "ZC", "Thu hoạch ngô"),
    ("corn_condition", "Corn Condition",          "condition", "ZC", "Chất lượng ngô (G/E)"),
    ("ww_planted",     "Winter Wheat Planted",    "progress",  "ZW", "Gieo lúa mì đông"),
    ("ww_emerged",     "Winter Wheat Emerged",    "progress",  "ZW", "Lúa mì đông nảy mầm"),
    ("ww_condition",   "Winter Wheat Condition",  "condition", "ZW", "Chất lượng lúa mì đông (G/E)"),
    ("ww_harvested",   "Winter Wheat Harvested",  "progress",  "ZW", "Thu hoạch lúa mì đông"),
    ("sw_planted",     "Spring Wheat Planted",    "progress",  "ZW", "Gieo lúa mì xuân"),
    ("sw_harvested",   "Spring Wheat Harvested",  "progress",  "ZW", "Thu hoạch lúa mì xuân"),
    ("sw_condition",   "Spring Wheat Condition",  "condition", "ZW", "Chất lượng lúa mì xuân (G/E)"),
]

_SECTION_RE = re.compile(r'^([A-Z][A-Za-z ]+?)\s+-\s+Selected States', re.M)
_ROW_RE = re.compile(r'^\s*\d+\s+States\s*\.+:(.*)$', re.M)
_TOKEN_RE = re.compile(r'\(NA\)|\(X\)|-|\d+(?:\.\d+)?')


def _conv(tok):
    """'(NA)' / '(X)' -> None, '-' -> 0, số -> int/float."""
    if tok in ("(NA)", "(X)"):
        return None
    if tok == "-":
        return 0
    v = float(tok)
    return int(v) if v.is_integer() else v


def _week_ending(text):
    """Tuần kết thúc = Chủ nhật ngay trước ngày phát hành (Released <Month d, yyyy>)."""
    m = re.search(r'Released\s+([A-Za-z]+ \d{1,2}, \d{4})', text)
    if not m:
        return None
    try:
        rel = datetime.datetime.strptime(m.group(1), "%B %d, %Y").date()
    except ValueError:
        return None
    return rel - datetime.timedelta(days=(rel.weekday() + 1) % 7)


def parse_report(text):
    """Trả về (week_ending_date, {key: {...}}) từ nội dung 1 báo cáo Crop Progress."""
    text = text.replace("\r", "")
    week_end = _week_ending(text)
    if week_end is None:
        return None, {}

    starts = list(_SECTION_RE.finditer(text))
    sections = {}
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        sections.setdefault(m.group(1).strip(), text[m.end():end])

    metrics = {}
    for key, title, kind, _code, _label in SPECS:
        sec = sections.get(title)
        if not sec:
            continue
        row = _ROW_RE.search(sec)
        if not row:
            continue
        toks = [_conv(t) for t in _TOKEN_RE.findall(row.group(1))]
        if kind == "progress" and len(toks) >= 4:
            metrics[key] = {"kind": kind, "year_ago": toks[0], "prev_week": toks[1],
                            "current": toks[2], "avg5": toks[3]}
        elif kind == "condition" and len(toks) >= 5:
            g, e = toks[3] or 0, toks[4] or 0
            metrics[key] = {"kind": kind, "current": g + e}
    return week_end, metrics


# ── LỊCH SỬ ──────────────────────────────────────────────────────────────────
def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def update_history(history, week_end, metrics):
    iso = week_end.isoformat()
    for key, m in metrics.items():
        if m.get("current") is not None:
            history.setdefault(key, {})[iso] = m["current"]
    return history


def _lookup(series, target, tol=3):
    """Giá trị gần ngày target nhất (sai số ±tol ngày)."""
    best, best_d = None, None
    for k, v in (series or {}).items():
        try:
            d = datetime.date.fromisoformat(k)
        except ValueError:
            continue
        diff = abs((d - target).days)
        if diff <= tol and (best_d is None or diff < best_d):
            best, best_d = v, diff
    return best


def _shift_years(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:  # 29/02
        return d.replace(year=d.year - years, day=28)


# ── DỰNG DỮ LIỆU SO SÁNH ─────────────────────────────────────────────────────
def build_compare(code, week_end, metrics, history):
    items = []
    for key, _title, kind, c, label in SPECS:
        if c != code or key not in metrics:
            continue
        m = metrics[key]
        series = history.get(key, {})
        cur = m.get("current")
        if cur is None:
            continue

        if kind == "progress":
            prev_week = m.get("prev_week")
            year_ago, ya_src = m.get("year_ago"), "USDA"
            if year_ago is None:
                year_ago = _lookup(series, week_end - datetime.timedelta(days=364))
                ya_src = "lưu trữ" if year_ago is not None else None
            avg5, avg_label, avg_n = m.get("avg5"), "TB 5 năm (USDA)", 5
        else:
            prev_week = _lookup(series, week_end - datetime.timedelta(days=7), tol=1)
            year_ago = _lookup(series, week_end - datetime.timedelta(days=364))
            ya_src = "lưu trữ" if year_ago is not None else None
            vals = [v for v in (_lookup(series, _shift_years(week_end, k)) for k in range(1, 6)) if v is not None]
            avg5 = round(sum(vals) / len(vals), 1) if vals else None
            avg_n = len(vals)
            avg_label = f"TB {avg_n} năm (tự tính)" if vals else "TB 5 năm"

        items.append({
            "key": key, "label": label, "kind": kind, "current": cur,
            "prev_week": prev_week, "year_ago": year_ago, "year_ago_src": ya_src,
            "avg5": avg5, "avg_label": avg_label, "avg_n": avg_n,
        })
    if not items:
        return None
    return {"week_ending": week_end.isoformat(), "source": "USDA Crop Progress", "items": items}


def run(text):
    """Parse báo cáo -> cập nhật lịch sử -> trả về {"ZC": {...}, "ZW": {...}}."""
    week_end, metrics = parse_report(text)
    if week_end is None or not metrics:
        return {}
    history = load_history()
    update_history(history, week_end, metrics)
    save_history(history)
    out = {}
    for code in ("ZC", "ZW"):
        cmp_ = build_compare(code, week_end, metrics, history)
        if cmp_:
            out[code] = cmp_
    return out
