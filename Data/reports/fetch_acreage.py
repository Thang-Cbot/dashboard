"""
Data/reports/fetch_acreage.py  — USDA Planted Acreage Fetcher v2
================================================================
Chiến lược tối ưu (không cần API key):
1. ESMIS API (miễn phí): Tự động tải báo cáo Acreage/Prospective Plantings mới nhất
   - Tìm publicationId bằng search API
   - Tải file .txt → parse triệu mẫu Anh (million acres)
2. Fallback: Dữ liệu lịch sử USDA NASS đã được xác nhận (2015-2025)
3. Lịch báo cáo: Tự cập nhật trạng thái + ngày tiếp theo

NOTE: Acreage 2026 đã được công bố ngày 30/6/2026 — sẽ tự động tải về.

Output: Data/output/acreage_data.json
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import re
import json
import datetime
import requests
from pathlib import Path
from data_config import OUTPUT_DIR, update_status

ACREAGE_FILE = OUTPUT_DIR / "acreage_data.json"

# ─── DỮ LIỆU LỊCH SỬ USDA NASS (xác nhận từ báo cáo công khai) ─────────────
# Nguồn: USDA NASS Acreage Reports + Prospective Plantings
# Đơn vị: triệu mẫu Anh (million acres)
HISTORICAL = {
    "ZC": {  # Corn — Ngô
        2015: 88.0, 2016: 94.0, 2017: 90.2, 2018: 89.1, 2019: 91.7,
        2020: 92.0, 2021: 93.2, 2022: 89.9, 2023: 94.6, 2024: 90.0, 2025: 95.3,
    },
    "ZW": {  # Wheat — Lúa mì (tất cả các loại)
        2015: 55.4, 2016: 51.3, 2017: 46.0, 2018: 47.8, 2019: 45.2,
        2020: 44.3, 2021: 46.4, 2022: 47.3, 2023: 49.6, 2024: 46.1, 2025: 46.0,
    },
    "ZS": {  # Soybeans — Đậu tương
        2015: 82.7, 2016: 83.7, 2017: 90.2, 2018: 89.1, 2019: 76.1,
        2020: 83.1, 2021: 87.2, 2022: 87.5, 2023: 83.5, 2024: 86.1, 2025: 83.5,
    },
}
NAMES = {"ZC": "Ngô (Corn)", "ZW": "Lúa mì (Wheat)", "ZS": "Đậu tương (Soybeans)"}

# ─── LỊCH BÁO CÁO NASS 2026 ─────────────────────────────────────────────────
NASS_CALENDAR_2026 = [
    ("Grain Stocks Q1 2026",       datetime.date(2026, 1, 12),
     "Tồn kho ngũ cốc quý 1",
     "Xác nhận cung tồn kho — tác động ngắn hạn"),
    ("Prospective Plantings 2026", datetime.date(2026, 3, 31),
     "Dự kiến diện tích gieo trồng cả năm 2026",
     "⚡ CATALYST LỚN — thị trường biến động mạnh khi dự báo diện tích thay đổi"),
    ("Grain Stocks Q2 2026",       datetime.date(2026, 3, 31),
     "Tồn kho ngũ cốc quý 2",
     "Double catalyst cùng ngày Prospective Plantings"),
    ("Acreage 2026 (CHÍNH THỨC)", datetime.date(2026, 6, 30),
     "XÁC NHẬN chính thức diện tích đã gieo trồng 2026",
     "⚡⚡ CATALYST #1 MÙA HÈ — Thị trường phản ứng tức thì"),
    ("Grain Stocks Q3 2026",       datetime.date(2026, 6, 30),
     "Tồn kho ngũ cốc quý 3",
     "Double catalyst cùng ngày Acreage — biến động lớn"),
    ("Grain Stocks Q4 2026",       datetime.date(2026, 9, 30),
     "Tồn kho ngũ cốc quý 4",
     "Trước mùa thu hoạch — quan trọng cho chiến lược mùa gặt"),
]

# ─── ESMIS REPORT NAMES TO SEARCH ────────────────────────────────────────────
ESMIS_BASE = "https://esmis.nal.usda.gov/api/v1"


def esmis_find_pub_id(title_keyword: str) -> int | None:
    """Tìm publicationId từ ESMIS bằng tên báo cáo."""
    try:
        url = f"{ESMIS_BASE}/publication/search?title={requests.utils.quote(title_keyword)}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        results = r.json().get("results", [])
        # Ưu tiên NASS
        for pub in results:
            if "NASS" in pub.get("agencyCode", ""):
                return pub.get("id")
        return results[0].get("id") if results else None
    except Exception as e:
        print(f"    [WARN] ESMIS search '{title_keyword}': {e}")
        return None


def esmis_get_latest_txt(pub_id: int) -> tuple[str | None, str]:
    """Lấy URL file txt mới nhất từ ESMIS theo pub_id."""
    try:
        url = f"{ESMIS_BASE}/release/findByPubId/{pub_id}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None, ""
        releases = r.json().get("results", [])
        if not releases:
            return None, ""
        latest = releases[0]
        rel_date = latest.get("release_datetime", "")[:10]
        files = latest.get("files", [])
        txt = next((f for f in files if f.lower().endswith(".txt")), None)
        return txt, rel_date
    except Exception as e:
        print(f"    [WARN] ESMIS releases pub_id={pub_id}: {e}")
        return None, ""


def parse_acres_from_text(text: str) -> dict:
    """Parse triệu mẫu Anh từ file text USDA NASS."""
    parsed = {}
    # Pattern: số liệu thường xuất hiện dạng "90,700" (ngàn acres) hoặc "90.7 million"
    # NASS reports thường dùng "1,000 acres" units

    patterns = {
        "ZC": [
            r"CORN[,\s\-]*ALL[^\n]*?PLANTED[^\n]*?([\d,]+)",
            r"Corn[,\s]*All[^\n]*?Planted[^\n]*?([\d,]+)",
            r"Total\s+Corn[^\n]*?Planted[^\n]*?([\d,]+)",
        ],
        "ZW": [
            r"WHEAT[,\s\-]*ALL[^\n]*?PLANTED[^\n]*?([\d,]+)",
            r"All\s+Wheat[^\n]*?Planted[^\n]*?([\d,]+)",
            r"Total\s+Wheat[^\n]*?Planted[^\n]*?([\d,]+)",
        ],
        "ZS": [
            r"SOYBEANS[^\n]*?PLANTED[^\n]*?([\d,]+)",
            r"Soybeans[^\n]*?Planted[^\n]*?([\d,]+)",
        ],
    }

    for sym, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(",", "")
                try:
                    val = int(raw)
                    # NASS reports thường tính bằng 1,000 acres → chia 1000 = triệu
                    if val > 100000:
                        val_mln = round(val / 1_000_000, 1)
                    elif val > 1000:
                        val_mln = round(val / 1000, 1)
                    else:
                        val_mln = round(val, 1)
                    parsed[sym] = val_mln
                    break
                except ValueError:
                    continue
    return parsed


def try_esmis_fetch(report_title: str) -> tuple[dict, str]:
    """Tải và parse báo cáo mới nhất từ ESMIS."""
    print(f"    🔍 ESMIS: Tìm '{report_title}'...")
    pub_id = esmis_find_pub_id(report_title)
    if not pub_id:
        print(f"    [WARN] Không tìm thấy pub_id cho '{report_title}'")
        return {}, ""

    txt_url, rel_date = esmis_get_latest_txt(pub_id)
    if not txt_url:
        print(f"    [WARN] Không có file txt cho pub_id={pub_id}")
        return {}, rel_date

    try:
        print(f"    📥 Đang tải báo cáo {rel_date}: {txt_url[:70]}...")
        r = requests.get(txt_url, timeout=30)
        r.raise_for_status()
        parsed = parse_acres_from_text(r.text)
        if parsed:
            print(f"    ✅ Đã parse: {parsed}")
        else:
            print(f"    [WARN] Parse không ra dữ liệu từ file txt")
        return parsed, rel_date
    except Exception as e:
        print(f"    [ERR] Tải txt: {e}")
        return {}, rel_date


def fetch_acreage() -> bool:
    print("\n=======================================================")
    print("  FETCH ACREAGE – Diện Tích Gieo Trồng USDA NASS")
    print("=======================================================")

    today = datetime.date.today()
    live_data = {}    # Dữ liệu parse được từ ESMIS
    live_date = ""    # Ngày phát hành báo cáo

    # ── 1. Thử lấy báo cáo ESMIS (Acreage → Prospective Plantings) ──────────
    for report_name in ["Acreage", "Prospective Plantings"]:
        esmis_parsed, rel_date = try_esmis_fetch(report_name)
        if esmis_parsed:
            live_data = esmis_parsed
            live_date = rel_date
            print(f"    [OK] Dùng dữ liệu live từ ESMIS '{report_name}': {rel_date}")
            break

    # ── 2. Tích hợp dữ liệu live vào lịch sử ─────────────────────────────────
    commodities = {}
    for sym in ["ZC", "ZW", "ZS"]:
        hist = dict(HISTORICAL[sym])  # copy

        # Override năm 2026 nếu có dữ liệu live
        if sym in live_data and live_data[sym] > 0:
            hist[2026] = live_data[sym]
            print(f"    ✅ [{sym}] 2026 cập nhật từ báo cáo ESMIS: {live_data[sym]:.1f}M acres")

        sorted_years = sorted(hist.keys())
        history_list = [{"year": y, "planted_mln_acres": hist[y]} for y in sorted_years]

        latest_yr  = sorted_years[-1]
        prev_yr    = sorted_years[-2] if len(sorted_years) >= 2 else None
        latest_val = hist[latest_yr]
        prev_val   = hist[prev_yr] if prev_yr else latest_val
        delta      = round(latest_val - prev_val, 2)
        delta_pct  = round(delta / prev_val * 100, 1) if prev_val else 0

        if delta > 0.5:
            signal = "🐻 BEARISH — Tăng cung → áp lực giảm giá"
        elif delta < -0.5:
            signal = "🐂 BULLISH — Giảm cung → hỗ trợ tăng giá"
        else:
            signal = "⚖️ Neutral — Ít thay đổi"

        commodities[sym] = {
            "name":                    NAMES[sym],
            "history":                 history_list,
            "latest_year":             latest_yr,
            "latest_planted_mln_acres":latest_val,
            "prev_year":               prev_yr or "—",
            "prev_planted_mln_acres":  prev_val,
            "yoy_delta_mln_acres":     delta,
            "yoy_pct":                 delta_pct,
            "yoy_direction":           "↑ Tăng" if delta > 0 else ("↓ Giảm" if delta < 0 else "→ Không đổi"),
            "signal":                  signal,
            "data_source":             "ESMIS Live" if sym in live_data else "USDA NASS Historical",
        }
        print(f"  [{sym}] {latest_yr}: {latest_val:.1f}M acres "
              f"({commodities[sym]['yoy_direction']} {abs(delta):.1f}M | {delta_pct:+.1f}%) → {signal}")

    # ── 3. Xây dựng lịch báo cáo ──────────────────────────────────────────────
    calendar_items = []
    next_report = None
    for name, date, desc, impact in NASS_CALENDAR_2026:
        days_away = (date - today).days
        if days_away < -1:
            status = "✅ Đã phát hành"
        elif days_away <= 0:
            status = "⚡ VỪA PHÁT HÀNH!"
        elif days_away <= 7:
            status = f"🔴 CỰC KỲ GẦN — còn {days_away} ngày"
        elif days_away <= 30:
            status = f"🟡 Còn {days_away} ngày"
        else:
            status = f"📅 Còn {days_away} ngày"

        item = {
            "name":          name,
            "date_et":       str(date),
            "publish_vn":    f"{date.strftime('%d/%m/%Y')} lúc 23:00 VN",
            "description":   desc,
            "impact":        impact,
            "status":        status,
            "days_away":     days_away,
        }
        calendar_items.append(item)
        if next_report is None and days_away >= -1:
            next_report = item

    if next_report:
        print(f"\n  📅 Báo cáo tiếp theo: {next_report['name']}")
        print(f"           → {next_report['status']}")

    # ── 4. Lưu output ─────────────────────────────────────────────────────────
    output = {
        "fetched_at":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source":          "USDA NASS via ESMIS API + Historical Records",
        "data_note":       "Đơn vị: Triệu mẫu Anh (Million Acres). Lịch sử 2015-2026.",
        "live_report_date": live_date,
        "commodities":     commodities,
        "report_calendar": calendar_items,
        "next_report":     next_report,
    }

    with open(ACREAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  [OK] Đã lưu → {ACREAGE_FILE}")

    update_status(
        "acreage", "OK",
        f"ZC={output['commodities']['ZC']['latest_planted_mln_acres']:.1f}M, "
        f"ZW={output['commodities']['ZW']['latest_planted_mln_acres']:.1f}M acres"
    )
    return True


if __name__ == "__main__":
    fetch_acreage()
