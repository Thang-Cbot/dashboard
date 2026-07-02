"""
fetch_usda.py — Fetch Dữ liệu USDA (USDA/WASDE Data Fetcher)
==============================================================
Wrapper gọi usda_crawler.py từ thư mục gốc Cbot/, sau đó đồng bộ
fundamental_data.json vào Data/output/fundamental_data.json.

Output: Data/output/fundamental_data.json (cập nhật WASDE, Crop Progress, Exports)

Chạy độc lập:
    python Data/fetch_usda.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import shutil
import datetime

from data_config import (
    FUNDAMENTAL_DATA, CBOT_ROOT, OUTPUT_DIR,
    ensure_output_dir, update_status
)

# Thêm thư mục gốc Cbot vào path để import usda_crawler
sys.path.insert(0, str(CBOT_ROOT))


def run_fetch_usda() -> bool:
    """
    Gọi USDA crawler để cập nhật báo cáo mới nhất từ USDA ESMIS,
    sau đó đồng bộ fundamental_data.json vào Data/output/.
    """
    ensure_output_dir()

    # ── Bước 1: Chạy USDA Crawler ──────────────────────────────────────────
    try:
        print("  📡 Đang gọi USDA crawler (ESMIS API)...")
        from usda_crawler import run_crawler_and_update
        run_crawler_and_update()
        print("  ✅ USDA crawler hoàn thành.")
    except Exception as e:
        print(f"  ⚠️  USDA crawler gặp lỗi: {e}")
        print("  → Tiếp tục với dữ liệu fundamental_data.json hiện tại.")

    # ── Bước 2: Đồng bộ fundamental_data.json từ gốc → Data/output/ ────────
    # usda_crawler.py ghi vào Cbot/fundamental_data.json (thư mục gốc)
    source_file = CBOT_ROOT / "fundamental_data.json"

    if source_file.exists():
        try:
            shutil.copy2(str(source_file), str(FUNDAMENTAL_DATA))
            print(f"  💾 Đã đồng bộ fundamental_data.json → {FUNDAMENTAL_DATA}")
        except Exception as e:
            print(f"  ⚠️  Không thể copy file: {e}")
    else:
        # Nếu không có file ở gốc, kiểm tra file đã được move vào output/ chưa
        if FUNDAMENTAL_DATA.exists():
            print(f"  ℹ️  fundamental_data.json đã có trong Data/output/ (không cần copy thêm).")
        else:
            print(f"  ❌ Không tìm thấy fundamental_data.json ở đâu cả!")
            update_status("usda", "ERROR", "fundamental_data.json not found")
            return False

    # ── Bước 3: Đọc và kiểm tra nội dung ─────────────────────────────────
    try:
        with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
            fund = json.load(f)

        # Lấy ngày cập nhật
        last_updated = fund.get("last_updated_fundamentals", "unknown")
        wasde_month  = fund.get("wasde_report_month", "unknown")

        summary = f"Updated: {last_updated} | WASDE: {wasde_month}"
        print(f"  📊 Dữ liệu fundamental: {summary}")

        # In tóm tắt các trường quan trọng
        for code in ["ZC", "ZW"]:
            if code not in fund:
                continue
            comm = fund[code]
            planting   = comm.get("us_planting",  {}).get("latest", "N/A")
            harvest    = comm.get("harvest_progress", {}).get("latest", "N/A")
            condition  = comm.get("crop_condition",   {}).get("latest", "N/A")
            exports    = comm.get("exports", {}).get("latest", "N/A")
            print(f"     [{code}] Planting: {planting} | Harvest: {harvest} | Cond: {condition}")
            print(f"            Exports: {exports[:60]}..." if len(str(exports)) > 60 else f"            Exports: {exports}")

        update_status("usda", "OK", summary)
        return True

    except Exception as e:
        print(f"  ❌ Lỗi đọc fundamental_data.json: {e}")
        update_status("usda", "ERROR", str(e))
        return False


def load_fundamental_data() -> dict:
    """Đọc fundamental data (dùng trong run_pro_plus.py và các lệnh khác)."""
    if not FUNDAMENTAL_DATA.exists():
        raise FileNotFoundError(f"Không tìm thấy {FUNDAMENTAL_DATA}. Hãy chạy fetch_usda.py trước.")
    with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fundamental_data(fund: dict) -> None:
    """Lưu fundamental data sau khi cập nhật thủ công."""
    ensure_output_dir()
    fund["last_updated_fundamentals"] = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(FUNDAMENTAL_DATA, "w", encoding="utf-8") as f:
        json.dump(fund, f, ensure_ascii=False, indent=2)
    print(f"  💾 Đã lưu: {FUNDAMENTAL_DATA}")


if __name__ == "__main__":
    print("=" * 55)
    print("  FETCH USDA/WASDE DATA")
    print("=" * 55)
    success = run_fetch_usda()
    print("Done." if success else "Hoàn thành với lỗi.")
