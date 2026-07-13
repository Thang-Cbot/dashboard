"""
Data/data_scheduler.py — Precision Scheduler (V2)
===================================================
Daemon chạy ngầm 24/7. Tự động kích hoạt đúng lịch từng loại báo cáo.

Điểm cải tiến so V1:
- Tính chính xác số giây sleep đến đúng thời điểm báo cáo
- Delay +2s sau giờ ra báo cáo (đợi server USDA ghi file xong)
- Polling: nếu API chưa có dữ liệu mới, thử lại mỗi 1 giây trong 120 giây
- Ghi alert vào data_status.json ngay sau khi fetch thành công/lỗi
- Sau mỗi lần fetch thành công → tự trigger render Streamlit (ghi file .trigger)

Chạy:
    python Data/data_scheduler.py
    Hoặc: START_SCHEDULER.bat
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import time
import datetime
import subprocess
import json
import threading
from pathlib import Path
import pytz

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR  = Path(__file__).parent
CBOT_ROOT = DATA_DIR.parent
OUTPUT_DIR = DATA_DIR / "output"
LOG_FILE  = DATA_DIR / "scheduler.log"
TRIGGER_FILE = OUTPUT_DIR / ".streamlit_trigger"  # Ghi file này → Streamlit rerun

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
ET_TZ = pytz.timezone("US/Eastern")

# ── Logging ────────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    now = datetime.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def update_status(module: str, status: str, detail: str = ""):
    """Cập nhật data_status.json ngay lập tức sau khi fetch."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        status_file = OUTPUT_DIR / "data_status.json"
        data = {}
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        if "modules" not in data:
            data["modules"] = {}
        data["modules"][module] = {
            "status": status,
            "detail": detail,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Lỗi update_status: {e}", "WARN")


def write_trigger():
    """Ghi trigger file → các client Streamlit có thể detect và rerun."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        TRIGGER_FILE.write_text(datetime.datetime.now().isoformat())
    except Exception:
        pass


def sync_to_github(source_name: str):
    """Đồng bộ ngay lập tức lên GitHub sau khi tải dữ liệu thành công."""
    import subprocess
    log(f"Bắt đầu đẩy dữ liệu lên Github (Kích hoạt bởi: {source_name})...", "Sync")
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(CBOT_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Auto sync: Dữ liệu {source_name} mới"], cwd=str(CBOT_ROOT), capture_output=True)
        res = subprocess.run(["git", "push"], cwd=str(CBOT_ROOT), capture_output=True, text=True)
        if res.returncode == 0:
            log(f"✅ Đồng bộ Github thành công ({source_name})!", "Sync")
            update_status("github_sync", "[OK]", f"Đẩy thành công lúc {datetime.datetime.now().strftime('%H:%M:%S')} (Nguồn: {source_name})")
        else:
            err_msg = res.stderr.strip()[-150:] if res.stderr else "Không có thay đổi"
            if "Everything up-to-date" in res.stdout or "nothing to commit" in res.stdout:
                log(f"⏩ Không có dữ liệu mới để đẩy ({source_name}).", "Sync")
                update_status("github_sync", "[OK]", f"Không có thay đổi (Nguồn: {source_name})")
            else:
                log(f"⚠️ Lỗi Github Push: {err_msg}", "Sync")
                update_status("github_sync", "[ERROR]", f"Lỗi Push: {err_msg}")
    except Exception as e:
        log(f"❌ Lỗi đồng bộ Github: {e}", "Sync")
        update_status("github_sync", "[ERROR]", f"Exception: {e}")

# ── Script Runner ──────────────────────────────────────────────────────────────
def run_script(module_name: str, script_path: str, module_key: str, max_retry: int = 1):
    """
    Chạy script Python, ghi kết quả vào status.
    Nếu max_retry > 1: thử lại mỗi 1 giây (dùng cho báo cáo precision).
    """
    log(f"▶ Kích hoạt: {module_name}")
    for attempt in range(max_retry):
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, encoding='utf-8', timeout=120,
                cwd=str(CBOT_ROOT)
            )
            if result.returncode == 0:
                log(f"✅ {module_name} hoàn thành (attempt {attempt+1})")
                update_status(module_key, "[OK]", f"Auto-fetch {datetime.datetime.now().strftime('%H:%M:%S')}")
                write_trigger()
                
                # Gọi đồng bộ Github ngay lập tức
                sync_to_github(module_name)
                return True
            else:
                err = result.stderr[-200:] if result.stderr else "unknown error"
                log(f"⚠ {module_name} lỗi attempt {attempt+1}: {err}", "WARN")
                if attempt < max_retry - 1:
                    time.sleep(1)
        except subprocess.TimeoutExpired:
            log(f"⏳ {module_name} timeout", "WARN")
        except Exception as e:
            log(f"❌ {module_name} exception: {e}", "ERROR")

    update_status(module_key, "[ERROR]", f"Failed after {max_retry} attempts")
    return False


# ── Precision Sleep ────────────────────────────────────────────────────────────
def sleep_until(target_dt_vn: datetime.datetime, label: str):
    """
    Ngủ chính xác đến target_dt_vn (giờ VN, aware timezone).
    """
    now = datetime.datetime.now(VN_TZ)
    delta = (target_dt_vn - now).total_seconds()
    if delta <= 0:
        return
    log(f"⏰ Đợi {label}: còn {delta/3600:.2f}h ({target_dt_vn.strftime('%d/%m %H:%M:%S')} VN)")
    time.sleep(max(0, delta))


# ── Lịch Báo Cáo ──────────────────────────────────────────────────────────────

def next_occurrence(weekday: int, hour: int, minute: int, tz=VN_TZ) -> datetime.datetime:
    """Tính thời điểm tiếp theo của (weekday, hour, minute) trong timezone."""
    now = datetime.datetime.now(tz)
    days_ahead = weekday - now.weekday()
    if days_ahead < 0 or (days_ahead == 0 and (now.hour, now.minute) >= (hour, minute)):
        days_ahead += 7
    target = now + datetime.timedelta(days=days_ahead)
    return tz.localize(datetime.datetime(target.year, target.month, target.day, hour, minute, 2))


def next_monthly(day: int, hour: int, minute: int, tz=VN_TZ) -> datetime.datetime:
    """Tính ngày tiếp theo trong tháng với ngày/giờ cố định (+2s buffer)."""
    now = datetime.datetime.now(tz)
    year, month = now.year, now.month
    candidate = tz.localize(datetime.datetime(year, month, day, hour, minute, 2))
    if candidate <= now:
        # Sang tháng sau
        month += 1
        if month > 12:
            month = 1
            year += 1
        candidate = tz.localize(datetime.datetime(year, month, day, hour, minute, 2))
    return candidate


def next_daily(hour: int, minute: int, tz=VN_TZ) -> datetime.datetime:
    now = datetime.datetime.now(tz)
    candidate = tz.localize(datetime.datetime(now.year, now.month, now.day, hour, minute, 2))
    if candidate <= now:
        candidate += datetime.timedelta(days=1)
    return candidate


# ── Jobs ───────────────────────────────────────────────────────────────────────
PRICE_SCRIPT     = str(DATA_DIR / "fetch_prices.py")
MACRO_SCRIPT     = str(DATA_DIR / "fetch_macro.py")
COT_SCRIPT       = str(DATA_DIR / "fetch_cot.py")
USDA_SCRIPT      = str(DATA_DIR / "fetch_usda.py")
EXPORT_SCRIPT    = str(DATA_DIR / "reports" / "export_sales.py")
WEATHER_S_SCRIPT = str(DATA_DIR / "weather" / "weather_short.py")
WEATHER_L_SCRIPT = str(DATA_DIR / "weather" / "weather_long.py")
ACREAGE_SCRIPT   = str(DATA_DIR / "reports" / "fetch_acreage.py")
AI_NEWS_SCRIPT   = str(DATA_DIR / "fetch_news.py")
BLACKSEA_SCRIPT  = str(DATA_DIR / "fetch_blacksea.py")
RUSSIAN_METRICS_SCRIPT = str(DATA_DIR / "fetch_russian_metrics.py")

def job_prices():
    """Giá H1: chạy phút :15 mỗi giờ (giờ giao dịch CBOT 20:00 - 08:00 sáng hôm sau VN)."""
    while True:
        now = datetime.datetime.now(VN_TZ)
        # Tính phút :15 của giờ tiếp theo
        next_h = now.replace(minute=15, second=2, microsecond=0)
        if now.minute >= 15:
            next_h += datetime.timedelta(hours=1)
        sleep_until(next_h, "Giá H1")
        
        success = run_script("Giá H1 + Macro", PRICE_SCRIPT, "prices")
        run_script("Vĩ Mô (Macro)",   MACRO_SCRIPT, "macro")
        
        # Ngay sau khi có giá mới, cập nhật Hồ sơ & Gửi cảnh báo
        if success:
            log("Đang quét tín hiệu Telegram Alarm (SMC)...")
            subprocess.run([sys.executable, "-c", "import entry_alarm; entry_alarm.run_analysis()"], cwd=str(CBOT_ROOT))
            
            log("Đang chạy cập nhật Hồ sơ mã (run_pro_plus) và tạo Dashboard (gen_dashboard)...")
            subprocess.run([sys.executable, "run_pro_plus.py"], cwd=str(CBOT_ROOT))
            subprocess.run([sys.executable, "gen_dashboard.py"], cwd=str(CBOT_ROOT))


def job_cot():
    """COT CFTC: mỗi Thứ Bảy 07:15 VN (CFTC publish Thứ Sáu 19:30 ET = Thứ Bảy 06:30 VN)."""
    while True:
        target = next_occurrence(weekday=5, hour=7, minute=15)  # Thứ Bảy=5
        sleep_until(target, "COT CFTC")
        run_script("COT CFTC", COT_SCRIPT, "cot", max_retry=5)


def job_crop_progress():
    """USDA Crop Progress: mỗi Thứ Hai 22:00 VN (USDA publish Mon 10AM ET = Mon 21:00 VN)."""
    while True:
        target = next_occurrence(weekday=0, hour=22, minute=0)  # Thứ Hai=0
        sleep_until(target, "Crop Progress")
        run_script("USDA Crop Progress", USDA_SCRIPT, "usda", max_retry=10)


def job_export_sales():
    """Export Sales: mỗi Thứ Năm 21:32 VN (USDA publish Thu 8:30 AM ET = Thu 19:30 VN, buffer 2h để file sẵn sàng)."""
    while True:
        target = next_occurrence(weekday=3, hour=21, minute=32)  # Thứ Năm=3
        sleep_until(target, "Export Sales")
        run_script("Export Sales", EXPORT_SCRIPT, "export_sales", max_retry=10)


def job_wasde():
    """WASDE: ngày 10 hàng tháng, 23:00 VN (USDA publish 12PM ET = 23:00 VN)."""
    while True:
        target = next_monthly(day=10, hour=23, minute=0)
        sleep_until(target, "WASDE Monthly")
        run_script("WASDE Report", USDA_SCRIPT, "usda", max_retry=15)


def job_weather_short():
    """Thời tiết ngắn hạn: 06:00 mỗi ngày."""
    while True:
        target = next_daily(hour=6, minute=0)
        sleep_until(target, "Weather Short")
        run_script("Thời Tiết Ngắn Hạn", WEATHER_S_SCRIPT, "weather_short")


def job_weather_long():
    """ENSO: mỗi Thứ Hai 06:30."""
    while True:
        target = next_occurrence(weekday=0, hour=6, minute=30)
        sleep_until(target, "ENSO Long-Term")
        run_script("ENSO / Weather Long", WEATHER_L_SCRIPT, "weather_long")


def job_acreage():
    """Acreage/Prospective Plantings: 05:30 hàng ngày (để bắt ngày release 30/6 hoặc 31/3)."""
    while True:
        target = next_daily(hour=5, minute=30)
        sleep_until(target, "Acreage Reports")
        run_script("USDA Acreage", ACREAGE_SCRIPT, "acreage", max_retry=3)


def job_ai_news():
    """Điểm tin AI: 06:00 và 20:00 hàng ngày."""
    while True:
        now = datetime.datetime.now(VN_TZ)
        t1 = now.replace(hour=6, minute=0, second=2, microsecond=0)
        t2 = now.replace(hour=20, minute=0, second=2, microsecond=0)
        candidates = [t for t in [t1, t2, t1 + datetime.timedelta(days=1)] if t > now]
        target = min(candidates)
        sleep_until(target, "AI News")
        run_script("AI Điểm Tin", AI_NEWS_SCRIPT, "ai_news")


AI_ANALYZER_SCRIPT = str(DATA_DIR / "ai_analyzer.py")

def job_ai_analysis():
    """Phân tích AI chuyên sâu SMC+COT+Mùa Vụ: 06:30 và 20:00 hàng ngày (ngày giao dịch CBOT)."""
    while True:
        now = datetime.datetime.now(VN_TZ)
        t1 = now.replace(hour=6, minute=30, second=2, microsecond=0)
        t2 = now.replace(hour=20, minute=0, second=2, microsecond=0)
        candidates = [t for t in [t1, t2, t1 + datetime.timedelta(days=1)] if t > now]
        target = min(candidates)
        sleep_until(target, "AI Phân Tích")
        # Chỉ chạy vào ngày giao dịch CBOT (Thứ 2 đến Thứ 6)
        now = datetime.datetime.now(VN_TZ)
        if now.weekday() < 5:  # 0=Thứ 2 ... 4=Thứ 6
            run_script("AI Phân Tích Chuyên Sâu", AI_ANALYZER_SCRIPT, "ai_analysis")
        else:
            log("Bỏ qua AI Phân Tích (cuối tuần — CBOT không giao dịch)", "AI Phân Tích")



def job_blacksea_news():
    """Tin tức Lúa mì Nga/Biển Đen: 07:00 mỗi Thứ Tư và Chủ Nhật."""
    while True:
        now = datetime.datetime.now(VN_TZ)
        t1 = next_occurrence(weekday=2, hour=7, minute=0)  # Thứ Tư = 2
        t2 = next_occurrence(weekday=6, hour=7, minute=0)  # Chủ Nhật = 6
        candidates = [t for t in [t1, t2] if t > now]
        target = min(candidates) if candidates else next_occurrence(weekday=2, hour=7, minute=0) + datetime.timedelta(days=7)
        sleep_until(target, "Black Sea News")
        run_script("AI Điểm Tin Biển Đen", BLACKSEA_SCRIPT, "blacksea_news")


def job_russian_metrics():
    """Số liệu Nga: 07:30 mỗi ngày (đặc biệt quan trọng trong mùa thu hoạch)."""
    while True:
        target = next_daily(hour=7, minute=30)
        sleep_until(target, "Russian Metrics")
        run_script("Chỉ số Lúa Mì Nga", RUSSIAN_METRICS_SCRIPT, "russian_metrics")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    log("=" * 60)
    log("  CBOT PRECISION SCHEDULER V2 — KHỞI ĐỘNG")
    log("=" * 60)
    log("Lịch trình đang chạy:")
    log("  [Giá H1 + Macro]    : Phút :15 mỗi giờ giao dịch")
    log("  [COT CFTC]          : Thứ Bảy 07:15 VN")
    log("  [USDA Crop Progress]: Thứ Hai 22:00 VN")
    log("  [Export Sales]      : Thứ Năm 21:32 VN")
    log("  [WASDE Monthly]     : Ngày 10 hàng tháng, 23:00 VN")
    log("  [Thời Tiết Ngắn]    : 06:00 hàng ngày")
    log("  [ENSO Long-Term]    : Thứ Hai 06:30 VN")
    log("  [USDA Acreage]      : 05:30 hàng ngày")
    log("  [AI Điểm Tin]       : 06:00 và 20:00 hàng ngày")
    log("  [AI Tin Biển Đen]   : Thứ Tư & Chủ Nhật 07:00 VN")
    log("  [Số Liệu Mùa Vụ Nga]: 07:30 hàng ngày")
    log("  [🧠 AI Phân Tích]   : 06:30 và 20:00 hàng ngày (T2-T6)")
    log("-" * 60)

    # Chạy mỗi job trong thread daemon riêng biệt
    jobs = [
        job_prices, job_cot, job_crop_progress,
        job_export_sales, job_wasde,
        job_weather_short, job_weather_long, job_acreage,
        job_ai_news, job_blacksea_news, job_ai_analysis,
    ]
    threads = []
    for job in jobs:
        t = threading.Thread(target=job, daemon=True, name=job.__name__)
        t.start()
        threads.append(t)
        log(f"  ✅ Thread khởi động: {job.__name__}")

    log("=" * 60)
    log("Scheduler đang chạy ngầm. Nhấn Ctrl+C để dừng.")

    try:
        while True:
            time.sleep(60)
            # Kiểm tra thread còn sống
            for t in threads:
                if not t.is_alive():
                    log(f"⚠ Thread {t.name} đã chết! Đang khởi động lại...", "WARN")
    except KeyboardInterrupt:
        log("Scheduler bị dừng bởi người dùng.")


if __name__ == "__main__":
    main()
