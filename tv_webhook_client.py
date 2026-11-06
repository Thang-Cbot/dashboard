"""
tv_webhook_client.py — Module Kết Nối Nến M5 Realtime Từ TradingView (Qua Google Apps Script Webhook)
=====================================================================================================
Cơ chế hoạt động:
  1. TradingView (khung M5) bắn Webhook POST mỗi 5 phút lên Google Apps Script (GAS).
  2. GAS lưu trữ nến M5 mới nhất + lịch sử nến M5 trong giờ + tổng hợp thành nến H1 đang chạy.
  3. Module này gọi HTTP GET tới link GAS để lấy dữ liệu M5 Realtime (0 độ trễ), tự động quy đổi
     múi giờ UTC -> Giờ Việt Nam (UTC+7) và ghép trực tiếp vào dữ liệu phân tích của hệ thống
     (cả trên Localhost và trên thang-cbot.streamlit.app).
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

VN_OFFSET = datetime.timedelta(hours=7)


def parse_to_vn_datetime(raw_time) -> datetime.datetime:
    """
    Chuyển đổi thời gian từ TradingView (ISO UTC '...Z', epoch ms, hoặc chuỗi giờ)
    sang giờ Việt Nam (UTC+7).
    """
    if not raw_time:
        return datetime.datetime.utcnow() + VN_OFFSET

    s = str(raw_time).strip()
    try:
        # Trường hợp epoch milliseconds (từ Pine Script time_close)
        if s.isdigit():
            ts = int(s)
            if ts > 1e11:
                ts = ts / 1000.0
            dt_utc = datetime.datetime.utcfromtimestamp(ts)
            return dt_utc + VN_OFFSET

        # Trường hợp ISO 8601 UTC (VD: 2026-11-05T06:34:43Z)
        if s.endswith("Z"):
            clean_s = s[:-1].split(".")[0].replace("T", " ")
            dt_utc = datetime.datetime.strptime(clean_s, "%Y-%m-%d %H:%M:%S")
            return dt_utc + VN_OFFSET

        # Trường hợp có +00:00
        if "+00:00" in s:
            clean_s = s.replace("+00:00", "").split(".")[0].replace("T", " ")
            dt_utc = datetime.datetime.strptime(clean_s, "%Y-%m-%d %H:%M:%S")
            return dt_utc + VN_OFFSET

        # Trường hợp đã là chuỗi giờ thông thường
        clean_s = s.split(".")[0].replace("T", " ")
        if len(clean_s) == 16:
            return datetime.datetime.strptime(clean_s, "%Y-%m-%d %H:%M")
        return datetime.datetime.strptime(clean_s[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.datetime.utcnow() + VN_OFFSET


def get_webhook_url() -> str:
    """Lấy URL Google Apps Script Webhook từ file cấu hình hoặc biến môi trường."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                url = cfg.get("webhook_url", "").strip()
                if url:
                    return url
        except Exception:
            pass
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
    Tự động bổ sung trường time_vn (Giờ Việt Nam UTC+7) cho từng mã.
    """
    url = get_webhook_url()
    if not url:
        return load_cached_m5()

    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("status") == "ok":
                # Chuẩn hóa giờ Việt Nam cho tất cả các mã
                for sym, s_obj in data.get("symbols", {}).items():
                    m5 = s_obj.get("latest_m5")
                    if m5 and m5.get("time"):
                        vn_dt = parse_to_vn_datetime(m5["time"])
                        m5["time_vn"] = vn_dt.strftime("%Y-%m-%d %H:%M:%S")
                        m5["h1_bar_vn"] = vn_dt.strftime("%Y-%m-%d %H:00")
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
      - Quy đổi thời gian nến M5 từ UTC sang giờ Việt Nam (UTC+7) khớp chuẩn với CSV H1.
      - Nếu nến M5 thuộc cùng giờ với cây nến H1 cuối cùng: cập nhật High, Low, Close.
      - Nếu nến M5 thuộc giờ mới: tự động tạo cây nến H1 đang chạy (forming H1 candle)
        từ các nến M5 trong giờ đó và tính lại EMA21, EMA50, RSI, ATR tức thời.
    """
    if not candles:
        return candles

    rt_data = fetch_realtime_m5(timeout=4)
    symbols_map = rt_data.get("symbols", {})
    if not symbols_map:
        return candles

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

        vn_dt = parse_to_vn_datetime(latest_m5.get("time"))
        h1_time_str = vn_dt.strftime("%Y-%m-%d %H:00")

        last_c = candles[-1]
        last_time_prefix = str(last_c.get("time", ""))[:13]
        new_time_prefix = h1_time_str[:13]

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
            candles[-1]["high"] = max(float(last_c["high"]), m5_high)
            candles[-1]["low"] = min(float(last_c["low"]), m5_low)
            candles[-1]["close"] = m5_close
            candles[-1]["ema21"] = new_ema21
            candles[-1]["ema50"] = new_ema50
            candles[-1]["rsi"] = new_rsi
            candles[-1]["atr"] = new_atr
            candles[-1]["is_realtime_m5"] = True
        elif new_time_prefix > last_time_prefix:
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


def get_latest_m5_price(commodity: str) -> dict:
    """
    Lấy giá nến M5 Realtime mới nhất (close, open, high, low, volume, time_vn, diff, pct).
    Dùng để thay thế hoặc đè lên giá nến H1 trên toàn bộ các trang Streamlit.
    """
    c_code = normalize_commodity_key(commodity).upper()
    cached = load_cached_m5()
    symbols = cached.get("symbols", {})
    sym_data = symbols.get(c_code)
    if not sym_data:
        for k, v in symbols.items():
            if normalize_commodity_key(k) == c_code:
                sym_data = v
                break
    if not sym_data or not sym_data.get("latest_m5"):
        return None

    m5 = sym_data["latest_m5"]
    forming = sym_data.get("forming_h1") or m5
    try:
        close = float(m5.get("close", 0))
        if close <= 0:
            return None
        open_p = float(forming.get("open", m5.get("open", close)))
        high_p = float(forming.get("high", m5.get("high", close)))
        low_p  = float(forming.get("low", m5.get("low", close)))
        vol    = int(m5.get("volume", 0))
        time_vn = m5.get("time_vn") or str(m5.get("time", ""))
        diff = round(close - open_p, 2)
        pct  = round((diff / open_p * 100.0), 2) if open_p > 0 else 0.0

        contract_name = "ZCEZ26" if c_code == "ZC" else ("ZWAZ26" if c_code == "ZW" else f"{c_code}Z26")
        return {
            "symbol": c_code,
            "contract": contract_name,
            "close": close,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "volume": vol,
            "diff": diff,
            "pct": pct,
            "time_vn": time_vn,
            "interval": "M5",
            "is_m5": True
        }
    except Exception:
        return None


def merge_realtime_m5_into_df(df, commodity: str):
    """
    Ghép nến M5 Realtime vào DataFrame nến H1 của Pandas (dùng cho biểu đồ và bảng giá).
    """
    if df is None or df.empty:
        return df

    m5_info = get_latest_m5_price(commodity)
    if not m5_info:
        return df

    import pandas as pd
    try:
        tcol = next((c for c in df.columns if c.lower() in ['time', 'datetime', 'date', 'timestamp']), None)
        if not tcol:
            return df

        m5_close = m5_info["close"]
        m5_open  = m5_info["open"]
        m5_high  = m5_info["high"]
        m5_low   = m5_info["low"]
        time_vn  = m5_info["time_vn"]
        h1_time_str = str(time_vn)[:13] + ":00"

        last_idx = df.index[-1]
        last_time_val = str(df.loc[last_idx, tcol])[:13]
        new_time_val  = str(h1_time_str)[:13]

        ccol = next((c for c in df.columns if c.lower() == 'close'), 'Close')
        hcol = next((c for c in df.columns if c.lower() == 'high'), 'High')
        lcol = next((c for c in df.columns if c.lower() == 'low'), 'Low')
        ocol = next((c for c in df.columns if c.lower() == 'open'), 'Open')

        if new_time_val == last_time_val:
            df.loc[last_idx, hcol] = max(float(df.loc[last_idx, hcol]), m5_high)
            df.loc[last_idx, lcol] = min(float(df.loc[last_idx, lcol]), m5_low)
            df.loc[last_idx, ccol] = m5_close
        elif new_time_val > last_time_val:
            new_row = df.loc[last_idx].to_dict()
            new_row[tcol] = pd.to_datetime(h1_time_str) if isinstance(df.loc[last_idx, tcol], pd.Timestamp) else h1_time_str
            new_row[ocol] = m5_open
            new_row[hcol] = m5_high
            new_row[lcol] = m5_low
            new_row[ccol] = m5_close
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    except Exception as e:
        print(f"[TV_WEBHOOK] Lỗi ghép M5 vào DataFrame cho {commodity}: {e}")

    return df


def sync_m5_to_active_h1_csv():
    """
    Cập nhật trực tiếp giá nến M5 mới nhất vào tất cả các file CSV H1 trong Data/output/
    để tất cả các module đọc CSV đều nhận được giá nến M5 Realtime mà không cần tải lại toàn bộ.
    """
    import pandas as pd
    for comm in ["ZC", "ZW"]:
        m5_info = get_latest_m5_price(comm)
        if not m5_info:
            continue
        csv_files = [
            OUTPUT_DIR / f"{comm}_active_H1.csv",
            OUTPUT_DIR / f"{comm}_swing_H1.csv",
            OUTPUT_DIR / f"{comm}_dca_H1.csv",
            OUTPUT_DIR / f"{comm}_90d_H1.csv",
        ]
        for cf in csv_files:
            if cf.exists():
                try:
                    df = pd.read_csv(cf)
                    df = merge_realtime_m5_into_df(df, comm)
                    df.to_csv(cf, index=False)
                except Exception as e:
                    print(f"[TV_WEBHOOK] Lỗi cập nhật M5 vào {cf.name}: {e}")

