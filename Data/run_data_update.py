"""
run_data_update.py - Script Chinh Cap Nhat Du Lieu (Main Data Orchestrator)
=============================================================================
Chay script nay de cap nhat TAT CA du lieu can thiet cho he thong Cbot:
  1. USDA/WASDE Data    -> fundamental_data.json
  2. Price Data CSV     -> ZC/ZW _active/swing/dca_H1.csv
  3. Macro Data         -> macro_data.json
  4. COT Data           -> cot_data.json
  5. Data Status        -> data_status.json

Sau khi chay xong, tat ca cac lenh khac (run_pro_plus.py, entry_alarm.py)
se doc truc tiep tu Data/output/ ma khong can tu fetch nua.

Chay:
    python Data/run_data_update.py
    hoac double-click: Data/run_data.bat
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Fix encoding cho Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import time
import datetime
import traceback
from pathlib import Path

from data_config import OUTPUT_DIR, DATA_STATUS, COMMODITY_CODES, ensure_output_dir


# ─────────────────────────────────────────────────────────────────────
# HELPER: Progress Banner
# ─────────────────────────────────────────────────────────────────────

def _banner(step, total, title):
    bar = "#" * step + "." * (total - step)
    print("")
    print("+======================================================+")
    print(f"|  [{step}/{total}] [{bar}]  {title:<30}|")
    print("+======================================================+")


def _ok(msg):
    print(f"  [OK] {msg}")


def _fail(msg):
    print(f"  [ERROR] {msg}")


# ─────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────

def run_all():
    start_time = time.time()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

    print("+======================================================+")
    print("|        CBOT DATA PROJECT -- RUN UPDATE               |")
    print("+======================================================+")
    print(f"|  Thoi gian: {now.strftime('%d/%m/%Y %H:%M:%S')} (ICT)              |")
    print("|  Nguon du lieu chuan DUY NHAT cho toan bo Cbot       |")
    print("+======================================================+")

    ensure_output_dir()

    results = {}
    TOTAL_STEPS = 9

    def _make_mod(status_str, detail_str=""):
        """Tạo dict chuẩn cho từng module, dùng để lưu vào data_status.json."""
        return {
            "status": "OK" if "[OK]" in status_str else ("PARTIAL" if "Partial" in status_str else "ERROR"),
            "detail": detail_str or status_str,
            "updated_at": finish_time_str if 'finish_time_str' in dir() else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ══ STEP 1: USDA / WASDE DATA ══════════════════════════════════════
    _banner(1, TOTAL_STEPS, "USDA/WASDE DATA")
    try:
        from fetch_usda import run_fetch_usda
        ok = run_fetch_usda()
        results["usda"] = {"status": "OK" if ok else "PARTIAL", "detail": "WASDE + Crop Progress updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"USDA: {e}")
        traceback.print_exc()
        results["usda"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 2: PRICE DATA (ZC / ZW H1) ══════════════════════════
    _banner(2, TOTAL_STEPS, "PRICE DATA CSV")
    print("  >> Tai du lieu nen H1 cho ZC, ZW (Active + Swing + DCA)")
    print("  >> Buoc nay mat khoang 2-3 phut...")
    try:
        from fetch_prices import run_fetch_prices
        ok = run_fetch_prices()
        results["prices"] = {"status": "OK" if ok else "PARTIAL", "detail": "ZC+ZW H1 updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Prices: {e}")
        traceback.print_exc()
        results["prices"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 3: MACRO DATA (Brent, DXY) ════════════════════════════════
    _banner(3, TOTAL_STEPS, "MACRO DATA")
    try:
        from fetch_macro import run_fetch_macro
        ok = run_fetch_macro()
        results["macro"] = {"status": "OK" if ok else "PARTIAL", "detail": "Brent/DXY updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Macro: {e}")
        traceback.print_exc()
        results["macro"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 4: COT DATA (CFTC Managed Money) ══════════════════════════
    _banner(4, TOTAL_STEPS, "COT DATA (CFTC)")
    try:
        from fetch_cot import run_fetch_cot
        ok = run_fetch_cot()
        results["cot"] = {"status": "OK" if ok else "PARTIAL", "detail": "COT CFTC updated (fallback if 403)", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"COT: {e}")
        traceback.print_exc()
        results["cot"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 5: EXPORT SALES ════════════════════════════════════════════
    _banner(5, TOTAL_STEPS, "EXPORT SALES")
    try:
        import subprocess
        res = subprocess.run([sys.executable, str(Path(__file__).parent / "reports" / "export_sales.py")], capture_output=True, text=True)
        if res.returncode == 0:
            _ok("Export Sales updated successfully.")
            results["export_sales"] = {"status": "OK", "detail": "Export Sales updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
        else:
            _fail(f"Export Sales error: {res.stderr[-100:]}")
            results["export_sales"] = {"status": "ERROR", "detail": "Lỗi cập nhật", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Export Sales: {e}")
        results["export_sales"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 6: WEATHER SHORT ═══════════════════════════════════════════
    _banner(6, TOTAL_STEPS, "WEATHER SHORT")
    try:
        import subprocess
        res = subprocess.run([sys.executable, str(Path(__file__).parent / "weather" / "weather_short.py")], capture_output=True, text=True)
        if res.returncode == 0:
            _ok("Weather Short updated successfully.")
            results["weather_short"] = {"status": "OK", "detail": "Weather short-term updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
        else:
            _fail(f"Weather Short error: {res.stderr[-100:]}")
            results["weather_short"] = {"status": "ERROR", "detail": "Lỗi cập nhật", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Weather Short: {e}")
        results["weather_short"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ══ STEP 7: ENSO / EL NINO (WEATHER LONG) ═══════════════════════════
    _banner(7, TOTAL_STEPS, "WEATHER LONG (ENSO)")
    try:
        import subprocess
        res = subprocess.run([sys.executable, str(Path(__file__).parent / "weather" / "weather_long.py")], capture_output=True, text=True)
        if res.returncode == 0:
            _ok("Weather Long updated successfully.")
            results["weather_long"] = {"status": "OK", "detail": "ENSO/El Nino updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
        else:
            _fail(f"Weather Long error: {res.stderr[-100:]}")
            results["weather_long"] = {"status": "ERROR", "detail": "Lỗi cập nhật", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Weather Long: {e}")
        results["weather_long"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # -------------------------------------------------------------------------
    # Bước 8: GỌI BỘ NÃO AI (AI ANALYZER)
    # -------------------------------------------------------------------------
    _banner(8, TOTAL_STEPS, "AI ANALYZER (GEMINI)")
    try:
        # Import hàm analyze từ ai_analyzer thay vì dùng subprocess để tận dụng code python
        from ai_analyzer import analyze
        ai_ok = analyze()
        if ai_ok:
            _ok("AI Analysis completed successfully.")
            results["ai"] = {"status": "OK", "detail": "Generated AI narrative", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
        else:
            _fail("AI Analysis skipped or failed (API Key missing/error).")
            results["ai"] = {"status": "SKIPPED", "detail": "Missing API Key or Error", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
            
        # Tự động sinh nến H1 giả lập cho 1 tuần
        try:
            from ai_chart_engine import generate as gen_ai_chart
            gen_ai_chart()
            _ok("AI Chart Engine (H1 Simulated) completed.")
        except Exception as e_chart:
            _fail(f"AI Chart Engine: {e_chart}")
            
    except Exception as e:
        _fail(f"AI Analyzer: {e}")
        results["ai"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # -------------------------------------------------------------------------
    # Bước 9: DIỆN TÍCH GIEO TRỒNG (ACREAGE)
    # -------------------------------------------------------------------------
    _banner(9, TOTAL_STEPS, "PLANTED ACREAGE (USDA PSD)")
    try:
        from reports.fetch_acreage import fetch_acreage
        acr_ok = fetch_acreage()
        if acr_ok:
            _ok("Acreage data updated successfully.")
            results["acreage"] = {"status": "OK", "detail": "Planted acreage ZC/ZW/ZS updated", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
        else:
            _fail("Acreage: partial or no data from PSD API.")
            results["acreage"] = {"status": "PARTIAL", "detail": "PSD API partial", "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        _fail(f"Acreage: {e}")
        results["acreage"] = {"status": "ERROR", "detail": str(e)[:80], "updated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")}

    # ─────────────────────────────────────────────────────────────────────────
    # TỔNG KẾT
    # ─────────────────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    finish_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

    print("")
    def _res(key):
        v = results.get(key, "N/A")
        if isinstance(v, dict):
            return v.get("status", "N/A")
        return str(v)

    print("+======================================================+")
    print("| TONG KET TRANG THAI DU LIEU                          |")
    print("+======================================================+")
    print(f"  [1] USDA/WASDE     : {_res('usda')}")
    print(f"  [2] Price Data H1  : {_res('prices')}")
    print(f"  [3] Macro Data     : {_res('macro')}")
    print(f"  [4] COT CFTC       : {_res('cot')}")
    print(f"  [5] Export Sales   : {_res('export_sales')}")
    print(f"  [6] Weather Short  : {_res('weather_short')}")
    print(f"  [7] Weather Long   : {_res('weather_long')}")
    print(f"  [8] AI Analyzer    : {_res('ai')}")
    print("+======================================================+")
    print(f"|  Hoan thanh: {finish_time.strftime('%H:%M:%S')} | Thoi gian: {elapsed:.0f}s               |")
    print("+======================================================+")

    # Kiem tra cac file output
    print("\n  Kiem tra Data/output/:")
    critical_files = [
        "fundamental_data.json",
        "macro_data.json",
        "cot_data.json",
        "ai_analysis.json",
        "daily_market_history.json",
        "ZC_active_H1.csv", "ZW_active_H1.csv",
        "ZC_swing_H1.csv",  "ZW_swing_H1.csv",
        "ZC_dca_H1.csv",    "ZW_dca_H1.csv",
    ]
    all_ok = True
    for fname in critical_files:
        fpath = OUTPUT_DIR / fname
        if fpath.exists():
            size_kb = fpath.stat().st_size / 1024
            print(f"    [OK]   {fname:<35} ({size_kb:.1f} KB)")
        else:
            print(f"    [MISS] {fname:<35} (MISSING!)")
            all_ok = False

    # Luu final status
    final_status = {
        "last_full_update": finish_time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 1),
        "modules": results,
        "all_ok": all_ok,
    }
    with open(DATA_STATUS, "w", encoding="utf-8") as f:
        json.dump(final_status, f, ensure_ascii=False, indent=2)

    print(f"\n  [SAVED] data_status.json")

    if all_ok:
        print("\n  >>> TAT CA DU LIEU DA SAN SANG! <<<")
        print("  Ban co the chay run_pro_plus.py hoac entry_alarm.py ngay.")
    else:
        print("\n  [WARN] Mot so file bi thieu -- kiem tra loi o tren.")

    print("\n" + "=" * 56)
    print("  DA HOAN TAT CAP NHAT DU LIEU CBOT DATA PROJECT")
    print("=" * 56)


if __name__ == "__main__":
    run_all()
