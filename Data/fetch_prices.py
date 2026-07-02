"""
fetch_prices.py — Fetch Dữ liệu Giá H1 (Price Data Fetcher)
=============================================================
Tải dữ liệu nến H1 cho ZC, ZW từ Yahoo Finance.
- Áp dụng cấu trúc Hợp đồng: Active, Swing, DCA.
- Tính toán Pro V2: EMA, ATR, RSI, Volatility, S1/S2/R1/R2, Pivot.
- Sinh nhận định xu hướng (Liquidity trend).

Output: Data/output/ZC_active_H1.csv, ZC_swing_H1.csv, ZC_dca_H1.csv (+ ZW)

Chạy độc lập:
    python Data/fetch_prices.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import shutil
import calendar
import datetime
import pandas as pd
import yfinance as yf

from data_config import (
    COMMODITY_CODES, CONTRACT_MONTHS, DCA_CONTRACT,
    OUTPUT_DIR, DAILY_HISTORY,
    get_csv_path, get_csv_str,
    ensure_output_dir, update_status, CBOT_ROOT
)

# Import technical_analysis từ thư mục gốc Cbot
sys.path.insert(0, str(CBOT_ROOT))
from technical_analysis import analyze_cbot_data, detect_candlestick_pattern, analyze_liquidity_trend


# ─────────────────────────────────────────────────────────────────────
# 1. XÁC ĐỊNH HỢP ĐỒNG
# ─────────────────────────────────────────────────────────────────────

def _get_candidate_tickers(commodity_code: str, current_date: datetime.datetime) -> list:
    """Tạo danh sách các hợp đồng ứng viên cho năm hiện tại và năm tiếp theo."""
    year  = current_date.year
    month = current_date.month
    months_config = CONTRACT_MONTHS.get(commodity_code, [])
    candidates = []
    for yr in [year, year + 1]:
        for code, m_num in months_config:
            if yr == year and m_num < month:
                continue
            ticker = f"{commodity_code}{code}{str(yr)[2:]}.CBT"
            candidates.append((ticker, yr, m_num, code))
    return candidates


def get_active_contract(commodity_code: str, current_date: datetime.datetime) -> tuple:
    """Chọn hợp đồng có thanh khoản cao nhất (Volume 5d)."""
    candidates = _get_candidate_tickers(commodity_code, current_date)
    best_ticker = None
    max_volume  = -1

    print(f"  Kiểm tra thanh khoản {commodity_code}...")
    for ticker_info in candidates[:4]:
        ticker = ticker_info[0]
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty and "Volume" in df.columns:
                total_vol = df["Volume"].sum()
                print(f"    {ticker}: Vol 5d = {total_vol:,}")
                if total_vol > max_volume:
                    max_volume = total_vol
                    best_ticker = ticker_info
        except Exception as e:
            print(f"    {ticker}: Lỗi → {e}")

    if (best_ticker is None or max_volume <= 0) and candidates:
        best_ticker = candidates[0]
        print(f"    Fallback → {best_ticker[0]}")
    else:
        print(f"    ✅ Active: {best_ticker[0]}")
    return best_ticker


def get_next_contract(commodity_code: str, active_info: tuple, current_date: datetime.datetime) -> tuple:
    """Lấy hợp đồng kỳ tiếp theo liền kề."""
    candidates = _get_candidate_tickers(commodity_code, current_date)
    for idx, cand in enumerate(candidates):
        if cand[0] == active_info[0]:
            if idx + 1 < len(candidates):
                return candidates[idx + 1]
            break
    return active_info


def get_dca_contract_info(commodity_code: str, current_date: datetime.datetime) -> tuple:
    """Xác định hợp đồng vụ mới (DCA long-term)."""
    year = current_date.year
    month = current_date.month
    m_code, dca_month = DCA_CONTRACT[commodity_code]
    dca_year = year + 1 if month >= dca_month else year
    ticker = f"{commodity_code}{m_code}{str(dca_year)[2:]}.CBT"
    return (ticker, dca_year, dca_month, m_code)


def _days_to_fnd(active_info: tuple, current_date: datetime.datetime) -> int:
    """Tính số ngày đến FND (First Notice Day)."""
    ticker, yr, m_num, m_code = active_info
    fnd_year  = yr - 1 if m_num == 1 else yr
    fnd_month = 12    if m_num == 1 else m_num - 1
    last_day  = calendar.monthrange(fnd_year, fnd_month)[1]
    fnd_date  = datetime.date(fnd_year, fnd_month, last_day)
    return (fnd_date - current_date.date()).days


def _should_use_next_for_swing(active_info, next_info, active_data, current_date) -> bool:
    """Quyết định dùng C1 hay C2 cho Swing trade."""
    days_to_fnd = _days_to_fnd(active_info, current_date)
    if days_to_fnd <= 15:
        print(f"    [Roll-over] {active_info[0]}: {days_to_fnd}d tới FND → Dùng C2")
        return True
    close = active_data.get("close", 0)
    atr   = active_data.get("atr",   0)
    s1    = active_data.get("s1",    0)
    r1    = active_data.get("r1",    0)
    signal = active_data.get("signal", "Neutral")
    if signal == "Bullish":
        is_near = (close <= s1 + 1.5 * atr)
    else:
        is_near = (close >= r1 - 1.5 * atr)
    return not is_near


# ─────────────────────────────────────────────────────────────────────
# 2. TẢI VÀ PHÂN TÍCH DỮ LIỆU
# ─────────────────────────────────────────────────────────────────────

def download_and_analyze(commodity: str, ticker_symbol: str, suffix: str) -> bool:
    """Tải H1 data, lưu CSV vào Data/output/, chạy technical analysis."""
    csv_path = get_csv_str(commodity, suffix)
    try:
        print(f"    Tải H1: {ticker_symbol} ({suffix})...")
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="30d", interval="1h")
        if df.empty:
            print(f"    ⚠️  Không lấy được data cho {ticker_symbol}. Giữ file cũ.")
            return False

        df = df.reset_index()
        df["Time"] = df["Datetime"].dt.tz_convert('Asia/Ho_Chi_Minh').dt.strftime("%Y-%m-%d %H:%M")
        try:
            oi_val = ticker.info.get("openInterest", 0) or 0
        except Exception:
            oi_val = 0
        df["OpenInterest"] = oi_val
        df = df[["Time", "Open", "High", "Low", "Close", "Volume", "OpenInterest"]]
        df.to_csv(csv_path, index=False)
        print(f"    ✅ Đã lưu {len(df)} nến → {csv_path}")
        analyze_cbot_data(csv_path)
        return True
    except Exception as e:
        print(f"    ❌ Lỗi {ticker_symbol}: {e}")
        return False


def setup_contracts(commodity: str, c1: tuple, c_swing: tuple, c_dca: tuple) -> None:
    """Tải và đồng bộ 3 vai trò Active/Swing/DCA."""
    download_and_analyze(commodity, c1[0], "active")

    if c_swing[0] == c1[0]:
        print(f"    Swing = Active ({c1[0]}). Copy file...")
        shutil.copyfile(get_csv_str(commodity, "active"), get_csv_str(commodity, "swing"))
    else:
        download_and_analyze(commodity, c_swing[0], "swing")

    if c_dca[0] == c1[0]:
        print(f"    DCA = Active ({c1[0]}). Copy file...")
        shutil.copyfile(get_csv_str(commodity, "active"), get_csv_str(commodity, "dca"))
    elif c_dca[0] == c_swing[0]:
        print(f"    DCA = Swing ({c_swing[0]}). Copy file...")
        shutil.copyfile(get_csv_str(commodity, "swing"), get_csv_str(commodity, "dca"))
    else:
        download_and_analyze(commodity, c_dca[0], "dca")


def get_latest_data(commodity: str, suffix: str) -> dict:
    """Đọc dòng cuối của CSV đã phân tích."""
    csv_path = get_csv_str(commodity, suffix)
    if not os.path.exists(csv_path):
        return {}
    df = pd.read_csv(csv_path)
    if df.empty:
        return {}
    row = df.iloc[-1]
    return {
        "time":         str(row["Time"]),
        "close":        float(row["Close"]),
        "ema_21":       float(row["EMA_21"]),
        "ema_50":       float(row["EMA_50"]),
        "volatility":   float(row["Volatility"]),
        "signal":       str(row["Signal"]),
        "rsi":          float(row["RSI"]),
        "atr":          float(row["ATR"]),
        "s1":           float(row["S1"]),
        "s2":           float(row["S2"]),
        "r1":           float(row["R1"]),
        "r2":           float(row["R2"]),
        "volume":       float(row.get("Volume", 0)),
        "open_interest":int(row.get("OpenInterest", 0)),
    }


# ─────────────────────────────────────────────────────────────────────
# 3. VOLUME / OI LỊCH SỬ
# ─────────────────────────────────────────────────────────────────────

def update_market_history(code: str, active_ticker: str) -> dict:
    """Cập nhật daily_market_history.json với Volume/OI hôm nay."""
    history_path = str(DAILY_HISTORY)
    history_data = {}
    if DAILY_HISTORY.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception:
            pass

    if code not in history_data:
        history_data[code] = {}

    ticker = yf.Ticker(active_ticker)
    df_5d  = ticker.history(period="5d")
    if df_5d.empty:
        return {}

    last_row    = df_5d.iloc[-1]
    today_date  = last_row.name.strftime("%Y-%m-%d")
    today_vol   = float(last_row["Volume"])
    today_close = float(last_row["Close"])
    today_open  = float(last_row["Open"])
    try:
        today_oi = int(ticker.info.get("openInterest", 0) or 0)
    except Exception:
        today_oi = 0

    for idx, row in df_5d.iterrows():
        d_str = idx.strftime("%Y-%m-%d")
        existing_oi = history_data[code].get(d_str, {}).get("open_interest", 0)
        history_data[code][d_str] = {
            "volume":        float(row["Volume"]),
            "open_interest": today_oi if d_str == today_date else int(existing_oi or today_oi),
            "close":         float(row["Close"]),
            "open":          float(row["Open"]),
        }

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    # Tính change
    sorted_dates = sorted([d for d in history_data[code].keys() if d < today_date])
    prev_vol = prev_oi = 0
    prev_close = today_close
    if sorted_dates:
        for d in reversed(sorted_dates):
            e = history_data[code][d]
            if e.get("volume", 0) > 0 or e.get("open_interest", 0) > 0:
                prev_vol   = e.get("volume", 0)
                prev_oi    = e.get("open_interest", 0)
                prev_close = e.get("close", today_close)
                break

    price_chg = today_close - prev_close
    vol_chg   = today_vol   - prev_vol
    oi_chg    = today_oi    - prev_oi
    trend, logic = analyze_liquidity_trend(price_chg, vol_chg, oi_chg)

    return {
        "today_volume":  today_vol,
        "prev_volume":   prev_vol,
        "today_oi":      today_oi,
        "prev_oi":       prev_oi,
        "today_close":   today_close,
        "prev_close":    prev_close,
        "trend":         trend,
        "logic":         logic,
    }


# ─────────────────────────────────────────────────────────────────────
# 4. CONTRACT METADATA
# ─────────────────────────────────────────────────────────────────────

def load_contracts_meta() -> dict:
    """Đọc contracts_meta.json (thông tin hợp đồng hiện tại)."""
    meta_path = OUTPUT_DIR / "contracts_meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_contracts_meta(meta: dict) -> None:
    """Lưu thông tin hợp đồng (c1, c2, c_swing, c_dca) cho mỗi mã."""
    meta_path = OUTPUT_DIR / "contracts_meta.json"
    meta["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────
# 5. ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def run_fetch_prices() -> bool:
    """Entry point chính - fetch toàn bộ price data cho ZC, ZW."""
    ensure_output_dir()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    contracts_meta = {}
    errors = []

    for code in COMMODITY_CODES:
        print(f"\n  ── {code} ──────────────────────────────────────")
        try:
            c1    = get_active_contract(code, now)
            c2    = get_next_contract(code, c1, now)
            c_dca = get_dca_contract_info(code, now)

            # Tải active trước để quyết định swing
            download_and_analyze(code, c1[0], "active")
            active_data = get_latest_data(code, "active")

            # Quyết định swing contract
            use_next = _should_use_next_for_swing(c1, c2, active_data, now)
            c_swing  = c2 if use_next else c1

            # Setup tất cả
            setup_contracts(code, c1, c_swing, c_dca)

            # Cập nhật volume/OI history
            hist = update_market_history(code, c1[0])
            trend = hist.get("trend", "N/A")
            print(f"    📈 Liquidity trend: {trend}")

            contracts_meta[code] = {
                "active":  {"ticker": c1[0],     "year": c1[1],     "month": c1[2]},
                "swing":   {"ticker": c_swing[0], "year": c_swing[1],"month": c_swing[2]},
                "dca":     {"ticker": c_dca[0],   "year": c_dca[1],  "month": c_dca[2]},
                "liquidity": hist,
            }
            print(f"  ✅ {code} done: Active={c1[0]}, Swing={c_swing[0]}, DCA={c_dca[0]}")

        except Exception as e:
            print(f"  ❌ {code} lỗi: {e}")
            errors.append(f"{code}: {e}")

    save_contracts_meta(contracts_meta)

    status = "OK" if not errors else f"PARTIAL ({len(errors)} errors)"
    detail = ", ".join(errors) if errors else f"ZC+ZW updated at {now.strftime('%H:%M')}"
    update_status("prices", status, detail)

    return len(errors) == 0


if __name__ == "__main__":
    print("=" * 55)
    print("  FETCH PRICE DATA - ZC / ZW (H1)")
    print("=" * 55)
    success = run_fetch_prices()
    print("\n=== Summary ===")
    for code in COMMODITY_CODES:
        active = get_latest_data(code, "active")
        if active:
            print(f"  {code}: Close={active['close']:.2f} | Signal={active['signal']} | RSI={active['rsi']:.1f}")
        else:
            print(f"  {code}: No data")
    print("Done." if success else "Done (with errors).")
