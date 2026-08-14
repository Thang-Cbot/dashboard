"""
Data/reports/export_sales.py
============================
Tự động tải và bóc tách báo cáo Giao Hàng Xuất Khẩu (Weekly Export Sales)
từ USDA FAS ESRQS (bản PDF Weekly Highlights).

Nguồn: https://apps.fas.usda.gov/esrqs/StaticReports/WeeklyHighlightsReport.pdf

Output:
  - Data/output/export_sales.json (chi tiết đầy đủ)
  - Cập nhật trường exports trong fundamental_data.json (ZC, ZW)

Chạy độc lập:
    python Data/reports/export_sales.py
"""
import sys
import os
import warnings

# Ignore PDF stream warnings
warnings.filterwarnings("ignore")

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
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import PyPDF2
except ImportError:
    print("Vui lòng cài đặt PyPDF2: pip install PyPDF2")
    sys.exit(1)

from data_config import OUTPUT_DIR, FUNDAMENTAL_DATA, update_status

EXPORT_SALES_FILE = OUTPUT_DIR / "export_sales.json"

def _try_weekly_highlights_pdf():
    """
    Tải file PDF báo cáo Weekly Highlights từ USDA FAS và bóc tách số liệu Ngô/Lúa Mì.
    """
    url = "https://apps.fas.usda.gov/esrqs/StaticReports/WeeklyHighlightsReport.pdf"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=30)
        if resp.status_code != 200:
            print(f"  [ERROR] Không thể tải PDF. Status Code: {resp.status_code}")
            return None, None
            
        f = io.BytesIO(resp.content)
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
            
        text_clean = text.replace('\n', ' ')
        
        # Extract Period
        period_match = re.search(r'for the period (.*?\d{4})', text_clean)
        period_str = period_match.group(1).strip() if period_match else datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Extract Wheat
        wheat_match = re.search(r'Wheat:.*?Net sales of ([\d,]+)\s*metric tons \(MT\)', text_clean, re.IGNORECASE)
        if not wheat_match:
            wheat_match = re.search(r'Wheat.*?Net sales of ([\d,]+)\s*MT', text_clean, re.IGNORECASE)
        wheat_ship_match = re.search(r'Wheat:.*?Exports of\s+([\d,]+)\s*MT', text_clean, re.IGNORECASE)
            
        # Extract Corn
        corn_match = re.search(r'Corn.*?:.*?Net sales of ([\d,]+)\s*MT', text_clean, re.IGNORECASE)
        corn_ship_match = re.search(r'Corn.*?:.*?Exports of\s+([\d,]+)\s*MT', text_clean, re.IGNORECASE)
        
        def to_float(s):
            return float(s.replace(',', '')) if s else 0
            
        results = {
            'ZW': {
                'current_mt': to_float(wheat_match.group(1) if wheat_match else '0'),
                'shipments_mt': to_float(wheat_ship_match.group(1) if wheat_ship_match else '0'),
                'prev_mt': 0
            },
            'ZC': {
                'current_mt': to_float(corn_match.group(1) if corn_match else '0'),
                'shipments_mt': to_float(corn_ship_match.group(1) if corn_ship_match else '0'),
                'prev_mt': 0
            }
        }
        
        return results, period_str
        
    except Exception as e:
        print(f"  [ERROR] Lỗi khi xử lý PDF: {e}")
        return None, None

def _try_cwr_commodity_summary_pdf():
    """
    Tải và bóc tách dữ liệu từ CWRCommoditySummary.pdf để lấy đầy đủ cả
    Net Sales, Shipments, Accumulated Exports và Prev Year Accumulated Exports.
    """
    url = "https://apps.fas.usda.gov/esrqs/StaticReports/CWRCommoditySummary.pdf"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    
    try:
        resp = None
        # Lưu ý: Kết nối từ VN đến apps.fas.usda.gov mất 60-90s để thiết lập (TCP handshake chậm).
        # Dùng tuple timeout=(connect_timeout, read_timeout) để phân biệt hai giai đoạn.
        retry_configs = [
            (90, 60),   # Lần 1: 90s TCP connect + 60s đọc dữ liệu
            (120, 60),  # Lần 2: 120s TCP connect (dự phòng nếu mạng chậm hơn bình thường)
        ]
        for attempt, (ct, rt) in enumerate(retry_configs, 1):
            try:
                print(f"  [Attempt {attempt}] GET PDF (connect={ct}s, read={rt}s)...")
                resp = requests.get(url, headers=headers, verify=False, timeout=(ct, rt))
                if resp.status_code == 200:
                    break
                print(f"  [WARN] Attempt {attempt} returned status {resp.status_code}")
                resp = None
            except Exception as e_inner:
                print(f"  [WARN] Attempt {attempt} failed: {e_inner}")
                resp = None
        if resp is None or resp.status_code != 200:
            print(f"  [ERROR] Không thể tải PDF CWRCommoditySummary sau {len(retry_configs)} lần thử.")
            return None, None

            
        f = io.BytesIO(resp.content)
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        results = {
            'ZW': {'current_mt': 0, 'shipments_mt': 0, 'outstanding_mt': 0, 'accumulated_mt': 0, 'prev_accum_mt': 0},
            'ZC': {'current_mt': 0, 'shipments_mt': 0, 'outstanding_mt': 0, 'accumulated_mt': 0, 'prev_accum_mt': 0}
        }
        
        period_str = ""
        
        def parse_block(start_idx):
            try:
                dt = lines[start_idx+1]
                # lines[start_idx+9] = Weekly Exports
                # lines[start_idx+10] = Net Sales
                # lines[start_idx+11] = Outstanding Sales
                # lines[start_idx+12] = Accumulated Exports
                # lines[start_idx+13] = Total Commitment
                # lines[start_idx+14] = Prev Year Accumulated Exports
                return {
                    'shipments_mt': float(lines[start_idx+9].replace(',', '')) * 1000,
                    'current_mt': float(lines[start_idx+10].replace(',', '')) * 1000,
                    'outstanding_mt': float(lines[start_idx+11].replace(',', '')) * 1000,
                    'accumulated_mt': float(lines[start_idx+12].replace(',', '')) * 1000,
                    'prev_accum_mt': float(lines[start_idx+14].replace(',', '')) * 1000,
                    'date': dt
                }
            except Exception as e:
                print(f"  [WARN] Parse error at block starting line {start_idx}: {e}")
                return None

        for i, line in enumerate(lines):
            if line.upper() == 'ALL WHEAT' and results['ZW']['current_mt'] == 0:
                data = parse_block(i)
                if data:
                    results['ZW'] = data
                    period_str = data['date']
            elif line.upper() == 'CORN - UNMILLED' and results['ZC']['current_mt'] == 0:
                data = parse_block(i)
                if data:
                    results['ZC'] = data
                    if not period_str: period_str = data['date']
                    
        return results, period_str
        
    except Exception as e:
        print(f"  [ERROR] Lỗi khi xử lý CWRCommoditySummary PDF: {e}")
        return None, None

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
    Main function: kéo dữ liệu Export Sales từ PDF, lưu JSON, và cập nhật fundamental_data.
    """
    print("\n  -- USDA EXPORT SALES (Auto Parse PDF) ---")
    now = datetime.datetime.now()

    print("  📡 Tải và phân tích báo cáo CWRCommoditySummary (PDF)...")
    parsed, period_str = _try_cwr_commodity_summary_pdf()

    results = {
        "fetched_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "current_week_ending": period_str,
        "previous_week_ending": "Tuần trước",
        "status": "OK" if parsed else "NoData",
        "commodities": {}
    }

    if parsed:
        for code, data in parsed.items():
            curr_mt = data.get("current_mt", 0)
            label_map = {"ZC": "Ngô", "ZW": "Lúa Mì"}
            label = label_map.get(code, code)

            results["commodities"][code] = {
                "current_mt": curr_mt,
                "prev_mt": 0,
                "pct_change": 0,
            }
            print(f"  ✅ {code} ({label}): Bán hàng ròng={_format_mt(curr_mt)}")

        _update_fundamental_exports(parsed, period_str)
    else:
        print("  [ERROR] Không parse được dữ liệu. Giữ nguyên dữ liệu cũ trong fundamental_data.json.")

    # Lưu export_sales.json
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_SALES_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    update_status(
        "export_sales",
        results["status"],
        f"Kỳ: {period_str} | " + (
            ", ".join([f"{c}={_format_mt(v['current_mt'])}" for c, v in results["commodities"].items()])
            if results.get("commodities") else "NoData"
        )
    )
    if not parsed:
        sys.exit(1)   # Báo lỗi cho UI biết thất bại
    return results["status"] == "OK"


def _update_fundamental_exports(parsed, period_str):
    """Ghi kết quả export vào fundamental_data.json.
    ANTI-DUPLICATE: Bỏ qua nếu period_str trùng với kỳ đã lưu (báo cáo chưa ra mới).
    """
    if not FUNDAMENTAL_DATA.exists():
        return
    try:
        with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
            fdata = json.load(f)

        for code, data in parsed.items():
            if code not in fdata:
                fdata[code] = {}

            # ── ANTI-DUPLICATE CHECK ──────────────────────────────────────────
            existing_week = fdata[code].get("export_sales_weekly", {}).get("week_ending", "")
            if existing_week and existing_week == period_str:
                print(f"  [SKIP ExportSales] {code}: Kỳ '{period_str}' đã có. Báo cáo chưa ra mới, bỏ qua ghi.")
                continue
            # ─────────────────────────────────────────────────────────────────

            # Lấy dữ liệu net_sales và shipments
            curr_mt = data.get("current_mt", 0)
            ship_mt = data.get("shipments_mt", 0)
            
            # Lấy dữ liệu của tuần trước từ file cũ
            old_sales_weekly = fdata[code].get("export_sales_weekly", {})
            old_net = old_sales_weekly.get("latest_net_sales", "0")
            # Parse old_net từ chuỗi (VD: "504.5 nghìn tấn" -> 504.5 * 1000)
            try:
                prev_mt = float(old_net.split()[0].replace(',', '')) * 1000
            except Exception:
                prev_mt = 0
            
            old_date = old_sales_weekly.get("latest_date", "Tuần trước")
            
            pct_change = ((curr_mt - prev_mt) / prev_mt * 100) if prev_mt else 0

            # Calculate YoY percentage
            accum_mt = data.get("accumulated_mt", 0)
            prev_accum_mt = data.get("prev_accum_mt", 0)
            outstanding_mt = data.get("outstanding_mt", 0)
            
            yoy_pct = ((accum_mt - prev_accum_mt) / prev_accum_mt * 100) if prev_accum_mt else 0
            
            # Extract marketing year
            my_year = ""
            label = code
            if code == "ZW":
                my_year = "2026/27"
                label = "Lúa Mì"
            elif code == "ZC":
                my_year = "2025/26"
                label = "Ngô"

            existing_exports = fdata[code].get("exports", {})
            
            fdata[code]["exports"] = {
                **existing_exports,
                "latest": f"Net Sales (Bán hàng): {_format_mt(curr_mt)} (Kỳ {period_str})",
                "previous": f"Net Sales (Tuần trước): {_format_mt(prev_mt)} ({old_date})",
                "latest_raw": curr_mt,
                "latest_date": period_str,
                "previous_date": old_date,
                "pct_change": round(pct_change, 1),
                "logic": (
                    f"{label} niên vụ {my_year} đạt {curr_mt/1000:,.1f} nghìn tấn, "
                    f"đưa lũy kế lên {accum_mt/1_000_000:,.3f} triệu tấn, "
                    f"{'cao hơn' if yoy_pct > 0 else 'thấp hơn'} {abs(yoy_pct):.1f}% so với cùng kỳ năm ngoái."
                ),
                "next_date": "Thứ 5 hàng tuần, 21:30 (VN)",
            }
            
            # Update `export_sales_weekly` for the UI
            fdata[code]["export_sales_weekly"] = {
                "report_type": "BAN_HANG",
                "latest_net_sales": f"{curr_mt/1000:,.1f} nghìn tấn",
                "previous_net_sales": f"{prev_mt/1000:,.1f} nghìn tấn" if prev_mt else "—",
                "pct_change": round(pct_change, 2),
                "latest_shipments": f"{ship_mt/1000:,.1f} nghìn tấn" if ship_mt else "N/A",
                "outstanding_sales": f"{outstanding_mt/1000:,.1f} nghìn tấn" if outstanding_mt else "N/A",
                "accumulated_sales": f"{accum_mt/1_000_000:,.3f} triệu tấn" if accum_mt else "N/A",
                "yoy_pct": round(yoy_pct, 1),
                "week_ending": period_str,
                "previous_week_ending": old_date,
                "latest_date": period_str,
                "next_report": "Thứ 5 hàng tuần lúc 21:30 (VN)",
                "action": "BULLISH" if pct_change > 5 else "BEARISH" if pct_change < -5 else "NEUTRAL",
                "logic": (
                    f"Doanh số ròng {'tăng' if pct_change > 0 else 'giảm'} {abs(pct_change):.1f}% xuống còn {curr_mt/1000:,.1f}k tấn. "
                    f"{label} niên vụ {my_year} đạt {curr_mt/1000:,.1f} nghìn tấn, "
                    f"đưa lũy kế lên {accum_mt/1_000_000:,.3f} triệu tấn, "
                    f"{'cao hơn' if yoy_pct > 0 else 'thấp hơn'} {abs(yoy_pct):.1f}% so với cùng kỳ năm ngoái."
                ),
                "note": "Nguồn: CWRCommoditySummary.pdf"
            }

        with open(FUNDAMENTAL_DATA, "w", encoding="utf-8") as f:
            json.dump(fdata, f, ensure_ascii=False, indent=2)
        print(f"  💾 Đã cập nhật exports vào fundamental_data.json")

        # ── EXCEL LOGGER ──────────────────────────────────────────────────────────
        try:
            import historical_logger
            # Lấy số raw và chia 1000 để ghi ngàn tấn (kMT)
            zc_net = fdata.get('ZC', {}).get('exports', {}).get('latest_raw', 0) / 1000
            zw_net = fdata.get('ZW', {}).get('exports', {}).get('latest_raw', 0) / 1000
            
            zc_pct = fdata.get('ZC', {}).get('exports', {}).get('pct_change', 0)
            zw_pct = fdata.get('ZW', {}).get('exports', {}).get('pct_change', 0)
            
            zc_ship = parsed.get('ZC', {}).get('shipments_mt', 0) / 1000 if 'ZC' in parsed else ""
            zw_ship = parsed.get('ZW', {}).get('shipments_mt', 0) / 1000 if 'ZW' in parsed else ""
            
            historical_logger.log_export_sales(
                date_str=period_str, 
                zc_sales=zc_net, zc_pct=zc_pct, zc_ship=zc_ship, zc_out="", 
                zw_sales=zw_net, zw_pct=zw_pct, zw_ship=zw_ship, zw_out=""
            )
        except Exception as e:
            print(f"  [WARN] Lỗi khi ghi lịch sử Excel: {e}")
        # ────────────────────────────────────────────────────────────────────────
    except Exception as e:

        print(f"  [WARN] Không thể cập nhật fundamental_data.json: {e}")

if __name__ == "__main__":
    fetch_export_sales()
