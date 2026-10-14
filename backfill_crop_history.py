"""
backfill_crop_history.py — Nạp lịch sử USDA Crop Progress (≈5 năm) vào Data/output/crop_progress_history.json
=============================================================================================================
Chạy 1 lần (hoặc khi muốn nạp lại):   python backfill_crop_history.py [số_năm=5.3]
Nguồn: USDA ESMIS (pubId 2179), mỗi trang 25 báo cáo.
"""
import sys
import time
import datetime
import requests
import crop_compare

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

API = "https://esmis.nal.usda.gov/api/v1/release/findByPubId/2179?page={}"


def _get(url, retries=3, timeout=30):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return None


def main(years=5.3):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=int(365 * years))
    history = crop_compare.load_history()
    done = 0
    page = 0
    stop = False
    while not stop:
        r = _get(API.format(page))
        if r is None:
            print(f"[ERR] Không tải được trang {page}")
            break
        results = r.json().get("results", [])
        if not results:
            break
        for rel in results:
            dt_s = rel.get("release_datetime", "")
            try:
                dt = datetime.datetime.strptime(dt_s, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                continue
            if dt < cutoff:
                stop = True
                break
            txt = next((f for f in rel.get("files", []) if f.endswith(".txt")), None)
            if not txt:
                continue
            tr = _get(txt)
            if tr is None:
                print(f"[SKIP] {dt_s[:10]}: lỗi tải")
                continue
            week_end, metrics = crop_compare.parse_report(tr.text)
            if week_end is None or not metrics:
                print(f"[SKIP] {dt_s[:10]}: không đọc được bảng")
                continue
            crop_compare.update_history(history, week_end, metrics)
            done += 1
            print(f"[OK] {dt_s[:10]} -> tuần {week_end} ({len(metrics)} chỉ số)")
            time.sleep(0.3)
        page += 1
        crop_compare.save_history(history)
    crop_compare.save_history(history)
    print(f"=== Hoàn tất: {done} báo cáo -> {crop_compare.HISTORY_FILE} ===")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 5.3)
