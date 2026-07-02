"""
Data/reports/export_sales.py
============================
Tự động tải và bóc tách báo cáo Giao Hàng Xuất Khẩu (Export Inspections)
từ USDA Grain Inspections API (public).

Nguồn: USDA FGIS Grain Inspections Reported by Commodity
API: https://www.ams.usda.gov/mnreports/ams_2852.xlsx (tuần mới nhất)
Hoặc fallback: https://apps.fas.usda.gov/export-sales/

Output:
  - Data/output/export_sales.json (chi tiết đầy đủ)
  - Cập nhật trường exports trong fundamental_data.json (ZC, ZW)

Chạy độc lập:
    python Data/reports/export_sales.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import datetime
import requests
import io
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from data_config import OUTPUT_DIR, FUNDAMENTAL_DATA, update_status

EXPORT_SALES_FILE = OUTPUT_DIR / "export_sales.json"

# ── Commodity mapping (từ tên trong báo cáo USDA → mã) ───────────────────────
COMMODITY_MAP = {
    "CORN":         "ZC",
    "WHEAT - TOTAL": "ZW",
    "SOYBEAN MEAL": "ZM",
    "SOYBEAN OIL":  "ZL",
}

# ── Số bushels quy đổi sang metric ton ───────────────────────────────────────
BUSHELS_TO_MT = {
    "ZC": 1 / 39.368,   # ngô
    "ZW": 1 / 36.744,   # lúa mì
}


def _try_usda_inspection_weekly():
    """
    Thử kéo dữ liệu từ USDA Weekly Export Inspections (FGIS).
    URL công khai, không cần key.
    Trả về dict {commodity_code: {current_week_mt, prev_week_mt, week_ending}}
    hoặc None nếu thất bại.
    """
    if not HAS_PANDAS:
        print("  [WARN] pandas chưa cài. Bỏ qua parse Excel.")
        return None

    # USDA FGIS thường publish theo tuần, URL dạng:
    # https://fgisonline.ams.usda.gov/ExportGrainReports/CY2026.aspx
    # Ta dùng API endpoint text thô của AMS
    base_urls = [
        "https://apps.fas.usda.gov/psdonline/app/index.html#/app/weeklyExports",
        "https://fgisonline.ams.usda.gov/ExportGrainReports/",
    ]

    # Thử kéo từ báo cáo USDA Export Sales weekly (FAS)
    # Đây là link JSON API của FAS cho export sales
    url = "https://apps.fas.usda.gov/esrquery/esrq.aspx"

    # Dùng USDA Grain Inspections public data (CSV/JSON endpoint)
    # Endpoint ổn định nhất: weekly inspections cho 2 tuần gần nhất
    api_url = "https://www.ams.usda.gov/mnreports/ams_2852.csv"
    try:
        resp = requests.get(api_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and len(resp.content) > 100:
            df = pd.read_csv(io.BytesIO(resp.content))
            return _parse_ams_csv(df)
    except Exception as e:
        print(f"  [WARN] AMS CSV thất bại: {e}")

    return None


def _parse_ams_csv(df):
    """Parse file CSV từ AMS, tìm dòng Corn/Wheat."""
    results = {}
    try:
        # Chuẩn hóa tên cột
        df.columns = [str(c).strip().upper() for c in df.columns]
        commodity_col = next((c for c in df.columns if 'COMM' in c or 'CROP' in c or 'GRAIN' in c), None)
        if commodity_col is None:
            return None

        for _, row in df.iterrows():
            commodity_raw = str(row.get(commodity_col, '')).strip().upper()
            code = next((v for k, v in COMMODITY_MAP.items() if k in commodity_raw), None)
            if code is None:
                continue

            # Tìm các cột số liệu
            num_cols = [c for c in df.columns if any(kw in c for kw in ['THIS', 'CURRENT', 'WEEK', 'TOTAL', 'MT', 'METRIC'])]
            if not num_cols:
                continue

            curr_val = 0
            prev_val = 0
            try:
                curr_val = float(str(row[num_cols[0]]).replace(',', '').strip() or 0)
                if len(num_cols) > 1:
                    prev_val = float(str(row[num_cols[1]]).replace(',', '').strip() or 0)
            except Exception:
                pass

            results[code] = {
                "current_mt": curr_val,
                "prev_mt": prev_val,
            }
    except Exception as e:
        print(f"  [WARN] _parse_ams_csv lỗi: {e}")

    return results if results else None


def _try_usda_esmis_inspections():
    """
    Kéo báo cáo từ USDA ESMIS (Grain Inspections / Weekly Export Inspections).
    pub_id 5020 = Grain Inspections Exports
    """
    try:
        pub_id = 5020
        api = f"https://esmis.nal.usda.gov/api/v1/release/findByPubId/{pub_id}"
        resp = requests.get(api, timeout=15)
        if resp.status_code != 200:
            return None

        releases = resp.json().get("results", [])
        if not releases:
            return None

        # Lấy release mới nhất
        latest = releases[0]
        files = latest.get("files", [])
        txt_url = next((f for f in files if f.endswith('.txt')), None)
        if not txt_url:
            return None

        full_url = f"https://esmis.nal.usda.gov{txt_url}" if txt_url.startswith('/') else txt_url
        resp2 = requests.get(full_url, timeout=20)
        if resp2.status_code != 200:
            return None

        return _parse_grain_inspection_txt(resp2.text, latest.get("releaseDate", ""))
    except Exception as e:
        print(f"  [WARN] ESMIS inspections thất bại: {e}")
        return None


def _parse_grain_inspection_txt(text, release_date):
    """
    Parse file text báo cáo Weekly Grain Inspections.
    Tìm dòng CORN, WHEAT và lấy số liệu tổng cộng.
    """
    results = {}
    lines = text.splitlines()

    # Tìm các dòng chứa tên commodity
    current_code = None
    for line in lines:
        line_up = line.strip().upper()
        for kw, code in COMMODITY_MAP.items():
            if kw in line_up and len(line_up) < 60:
                current_code = code
                break

        if current_code:
            # Tìm dòng chứa số liệu lớn (metric ton hoặc bushels)
            parts = line.split()
            nums = []
            for p in parts:
                try:
                    n = float(p.replace(',', ''))
                    if n > 1000:  # lọc số nhỏ vô nghĩa
                        nums.append(n)
                except Exception:
                    pass

            if len(nums) >= 2 and current_code not in results:
                results[current_code] = {
                    "current_mt": nums[0],
                    "prev_mt": nums[1] if len(nums) > 1 else 0,
                    "release_date": release_date,
                }

    return results if results else None


def _format_mt(val):
    """Format metric ton thành chuỗi đẹp."""
    if val >= 1_000_000:
        return f"{val/1_000_000:.2f}M MT"
    elif val >= 1_000:
        return f"{int(val):,} MT"
    else:
        return f"{val:.0f} MT"


def fetch_export_sales():
    """
    Main function: kéo dữ liệu Export Sales, lưu JSON, và cập nhật fundamental_data.
    """
    print("\n  -- USDA EXPORT SALES (Auto Parse) ---")

    now = datetime.datetime.now()
    # Xác định tuần kết thúc (thường là Chủ nhật vừa rồi)
    days_since_sunday = now.weekday() + 1 if now.weekday() < 6 else 0
    current_week_end = now - datetime.timedelta(days=days_since_sunday)
    prev_week_end = current_week_end - datetime.timedelta(days=7)
    current_week_str = current_week_end.strftime("%d/%m/%Y")
    prev_week_str = prev_week_end.strftime("%d/%m/%Y")

    parsed = None

    # Thử parse từ ESMIS Grain Inspections
    print("  📡 Thử USDA ESMIS Grain Inspections...")
    parsed = _try_usda_esmis_inspections()

    # Fallback: AMS CSV
    if not parsed:
        print("  📡 Thử AMS CSV fallback...")
        parsed = _try_usda_inspection_weekly()

    results = {
        "fetched_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "current_week_ending": current_week_str,
        "previous_week_ending": prev_week_str,
        "status": "OK" if parsed else "Partial",
        "commodities": {}
    }

    if parsed:
        for code, data in parsed.items():
            curr_mt = data.get("current_mt", 0)
            prev_mt = data.get("prev_mt", 0)
            pct_change = ((curr_mt - prev_mt) / prev_mt * 100) if prev_mt else 0
            label_map = {"ZC": "Ngô", "ZW": "Lúa Mì"}
            label = label_map.get(code, code)

            results["commodities"][code] = {
                "current_mt": curr_mt,
                "prev_mt": prev_mt,
                "pct_change": round(pct_change, 1),
            }
            print(f"  ✅ {code} ({label}): Hiện tại={_format_mt(curr_mt)}, Kỳ trước={_format_mt(prev_mt)}, Δ={pct_change:+.1f}%")
        _update_fundamental_exports(parsed, current_week_str, prev_week_str)
    else:
        print("  [WARN] Không parse được dữ liệu. Giữ nguyên dữ liệu cũ trong fundamental_data.json.")
        results["status"] = "NoData"

    # Lưu export_sales.json
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_SALES_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    update_status(
        "export_sales",
        results["status"],
        f"Tuần {current_week_str}: " + (
            ", ".join([f"{c}={_format_mt(v['current_mt'])}" for c, v in results["commodities"].items()])
            if results["commodities"] else "NoData"
        )
    )
    return results["status"] in ("OK", "Partial")


def _update_fundamental_exports(parsed, current_week_str, prev_week_str):
    """Ghi kết quả export vào fundamental_data.json."""
    if not FUNDAMENTAL_DATA.exists():
        return
    try:
        with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
            fdata = json.load(f)

        label_map = {"ZC": "Ngô", "ZW": "Lúa Mì"}
        for code, data in parsed.items():
            if code not in fdata:
                fdata[code] = {}
            curr_mt = data.get("current_mt", 0)
            prev_mt = data.get("prev_mt", 0)
            pct_change = ((curr_mt - prev_mt) / prev_mt * 100) if prev_mt else 0
            label = label_map.get(code, code)

            fdata[code]["exports"] = {
                "latest": f"Giao hàng Inspections: {_format_mt(curr_mt)} (Tuần kết thúc {current_week_str})",
                "previous": f"Giao hàng Inspections: {_format_mt(prev_mt)} (Tuần kết thúc {prev_week_str})",
                "latest_date": f"Tuần kết thúc {current_week_str}",
                "previous_date": f"Tuần kết thúc {prev_week_str}",
                "pct_change": round(pct_change, 1),
                "logic": (
                    f"{'Tăng mạnh' if pct_change > 10 else 'Tăng nhẹ' if pct_change > 0 else 'Giảm nhẹ' if pct_change > -10 else 'Giảm mạnh'} "
                    f"{abs(pct_change):.1f}% so tuần trước. "
                    f"{'Tín hiệu BULLISH — cầu xuất khẩu tăng.' if pct_change > 5 else 'Tín hiệu BEARISH — cầu xuất khẩu yếu.' if pct_change < -5 else 'Trung tính.'}"
                ),
                "next_date": "Thứ 5 hàng tuần, 21:30 (VN)",
            }

        with open(FUNDAMENTAL_DATA, "w", encoding="utf-8") as f:
            json.dump(fdata, f, ensure_ascii=False, indent=2)
        print(f"  💾 Đã cập nhật exports vào fundamental_data.json")
    except Exception as e:
        print(f"  [WARN] Không thể cập nhật fundamental_data.json: {e}")


if __name__ == "__main__":
    fetch_export_sales()
