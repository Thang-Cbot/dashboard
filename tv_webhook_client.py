"""
tv_webhook_client.py — Module Kết Nối Nến M5 Realtime Từ TradingView (Qua Google Apps Script Webhook)
=====================================================================================================
Cơ chế hoạt động:
  1. TradingView (khung M5) bắn Webhook POST mỗi 5 phút lên Google Apps Script (GAS).
  2. GAS lưu trữ nến M5 mới nhất + lịch sử nến M5 trong giờ + tổng hợp thành nến H1 đang chạy.
  3. Module này gọi HTTP GET tới link GAS để lấy dữ liệu M5 Realtime (0 độ trễ) và ghép trực tiếp
     vào dữ liệu phân tích của hệ thống (cả trên Localhost và trên thang-cbot.streamlit.app).
"""

import os
import json
import datetime
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "Data"
OUTPUT_DIR = DATA_DIR / "output"
CONFIG_FILE = DATA_DIR / "webhook_config.json"
CACHE_M5_FILE = OUTPUT_DIR / "tv_realtime_m5.json"


def get_webhook_url() -> str:
    """Lấy URL Google Apps Script Webhook từ file cấu hình hoặc biến môi trường."""
    # 1. Ưu tiên đọc từ file config (được đồng bộ qua GitHub lên Streamlit Cloud)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                url = cfg.get("webhook_url", "").strip()
                if url:
                    return url
        except Exception:
            pass

    # 2. Fallback biến môi trường
    return os.environ.get("TV_WEBHOOK_URL", "").strip()


def save_webhook_url(url: str) -> bool:
    """Lưu URL Google Apps Script Webhook vào Data/webhook_config.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        cfg = {
            "webhook_url": url.strip(),
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[TV_WEBHOOK] Lỗi lưu cấu hình URL: {e}")
        return False


def fetch_realtime_m5(timeout: int = 5) -> dict:
    """
    Gọi GET tới Google Apps Script Webhook để lấy dữ liệu nến M5 mới nhất.
    Trả về dict dữ liệu hoặc đọc từ cache nếu offline.
    """
    url = get_webhook_url()
    if not url:
        return load_cached_m5()

    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("status") == "ok":
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(CACHE_M5_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
    except Exception as e:
        print(f"[TV_WEBHOOK] Không thể kết nối GAS ({e}), dùng cache gần nhất.")

    return load_cached_m5()


def load_cached_m5() -> dict:
    """Đọc dữ liệu M5 từ file cache cục bộ."""
    if CACHE_M5_FILE.exists():
        try:
            with open(CACHE_M5_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "empty", "symbols": {}}


def normalize_commodity_key(raw_symbol: str) -> str:
    """Chuyển đổi mã ticker từ TradingView (VD: ZWAZ2026, ZW1!, ZC1!, ZCEZ26) về mã gốc ZW, ZC, ZS."""
    s = str(raw_symbol).upper().strip()
    if s.startswith("ZW") or "WHEAT" in s:
        return "ZW"
    if s.startswith("ZC") or "CORN" in s:
        return "ZC"
    if s.startswith("ZS") or "SOY" in s:
        return "ZS"
    return s


def merge_realtime_m5_into_candles(candles: list, commodity: str) -> list:
    """
    Ghép nến M5 Realtime (từ TradingView Webhook) vào danh sách nến H1:
      - Nếu nến M5 thuộc cùng giờ với cây nến H1 cuối cùng: cập nhật High, Low, Close.
      - Nếu nến M5 thuộc giờ mới (chưa có trong CSV H1): tự động tổng hợp các nến M5 trong giờ đó
        thành cây nến H1 đang chạy (forming H1 candle) và tính lại EMA21, EMA50, RSI, ATR tức thời.
    """
    if not candles:
        return candles

    rt_data = fetch_realtime_m5(timeout=4)
    symbols_map = rt_data.get("symbols", {})
    if not symbols_map:
        return candles

    # Tìm dữ liệu khớp với mã hàng hóa (ZW, ZC, ZS)
    sym_data = symbols_map.get(commodity.upper())
    if not sym_data:
        for k, v in symbols_map.items():
            if normalize_commodity_key(k) == commodity.upper():
                sym_data = v
                break

    if not sym_data or not sym_data.get("latest_m5"):
        return candles

    latest_m5 = sym_data["latest_m5"]
    forming_h1 = sym_data.get("forming_h1") or latest_m5

    try:
        m5_close = float(latest_m5.get("close", 0))
        if m5_close <= 0:
            return candles

        m5_open = float(forming_h1.get("open", latest_m5.get("open", m5_close)))
        m5_high = float(forming_h1.get("high", latest_m5.get("high", m5_close)))
        m5_low = float(forming_h1.get("low", latest_m5.get("low", m5_close)))
        m5_time_raw = str(latest_m5.get("time", ""))

        # Chuẩn hóa chuỗi giờ H1 (YYYY-MM-DD HH:00:00)
        if len(m5_time_raw) >= 13:
            h1_time_str = m5_time_raw[:13].replace("T", " ") + ":00:00"
        else:
            h1_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:00:00")

        last_c = candles[-1]
        last_time_prefix = str(last_c.get("time", ""))[:13]
        new_time_prefix = h1_time_str[:13]

        # Tính nhanh EMA21, EMA50 từ cây nến trước đó
        prev_ema21 = float(last_c.get("ema21", m5_close))
        prev_ema50 = float(last_c.get("ema50", m5_close))
        prev_atr = float(last_c.get("atr", abs(m5_high - m5_low) or 5.0))
        prev_rsi = float(last_c.get("rsi", 50.0))

        k21 = 2.0 / (21.0 + 1.0)
        k50 = 2.0 / (50.0 + 1.0)
        new_ema21 = round(float(latest_m5.get("ema21") or (m5_close * k21 + prev_ema21 * (1 - k21))), 4)
        new_ema50 = round(float(latest_m5.get("ema50") or (m5_close * k50 + prev_ema50 * (1 - k50))), 4)
        new_rsi = round(float(latest_m5.get("rsi") or prev_rsi), 2)
        new_atr = round(float(latest_m5.get("atr") or prev_atr), 4)

        if new_time_prefix == last_time_prefix:
            # Cập nhật trực tiếp vào cây nến H1 cuối cùng
            candles[-1]["high"] = max(float(last_c["high"]), m5_high)
            candles[-1]["low"] = min(float(last_c["low"]), m5_low)
            candles[-1]["close"] = m5_close
            candles[-1]["ema21"] = new_ema21
            candles[-1]["ema50"] = new_ema50
            candles[-1]["rsi"] = new_rsi
            candles[-1]["atr"] = new_atr
            candles[-1]["is_realtime_m5"] = True
        elif new_time_prefix > last_time_prefix:
            # Thêm cây nến H1 đang hình thành từ dữ liệu M5
            new_bar = dict(last_c)
            new_bar.update({
                "time": h1_time_str,
                "open": m5_open,
                "high": m5_high,
                "low": m5_low,
                "close": m5_close,
                "ema21": new_ema21,
                "ema50": new_ema50,
                "rsi": new_rsi,
                "atr": new_atr,
                "is_realtime_m5": True
            })
            candles.append(new_bar)
    except Exception as e:
        print(f"[TV_WEBHOOK] Lỗi ghép nến M5 cho {commodity}: {e}")

    return candles
