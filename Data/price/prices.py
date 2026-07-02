"""
Data/price/prices.py
====================
Fetch gia nen H1 cho ZC, ZW tu Yahoo Finance.
Chay vao phut :15 cua moi gio trong gio giao dich CBOT.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import json, datetime, shutil
import pandas as pd
import yfinance as yf
from data_config import (
    OUTPUT_DIR, COMMODITY_CODES, CONTRACT_MONTHS, DCA_CONTRACT,
    get_csv_str, ensure_output_dir, update_status, CBOT_ROOT
)
sys.path.insert(0, str(CBOT_ROOT))
from technical_analysis import analyze_cbot_data, detect_candlestick_pattern, analyze_liquidity_trend

# ── Gio giao dich CBOT (ICT = UTC+7) ─────────────────────────────────
# CBOT Grains: Mo 20:00 ICT (Sun) - Dong 07:45 ICT (Mon-Sat), nghi 07:45-08:30
# Toan phan electronic ~ 24/5
CBOT_OPEN_HOUR_ICT  = 20   # 8 PM ICT (Sunday)
CBOT_CLOSE_HOUR_ICT = 8    # 8 AM ICT (break end)

def is_cbot_open():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    if now.weekday() == 5:  # Saturday sau 8AM: dong
        return now.hour < 8
    if now.weekday() == 6:  # Sunday: mo tu 8PM
        return now.hour >= 20
    # Mon-Fri: mo 24h tru 07:45-08:30
    if 0 <= now.weekday() <= 4:
        if now.hour == 7 and now.minute >= 45:
            return False
        if now.hour == 8 and now.minute < 30:
            return False
        return True
    return False

# ── Contract Detection ────────────────────────────────────────────────
def get_active_contract(commodity_code, current_date):
    candidates = _get_candidates(commodity_code, current_date)
    best, max_vol = None, -1
    for info in candidates[:5]:
        try:
            df = yf.Ticker(info[0]).history(period="3d")
            if not df.empty:
                vol = df["Volume"].sum()
                if vol > max_vol:
                    max_vol, best = vol, info
        except: pass
    return best or candidates[0]

def get_next_contract(commodity_code, active_info, current_date):
    candidates = _get_candidates(commodity_code, current_date)
    for i, c in enumerate(candidates):
        if c[0] == active_info[0] and i+1 < len(candidates):
            return candidates[i+1]
    return active_info

def get_dca_contract(commodity_code, current_date):
    year = current_date.year
    month = current_date.month
    m_code, dca_month = DCA_CONTRACT[commodity_code]
    dca_year = year + 1 if month >= dca_month else year
    ticker = f"{commodity_code}{m_code}{str(dca_year)[2:]}.CBT"
    return (ticker, dca_year, dca_month, m_code)

def _get_candidates(commodity_code, dt):
    year, month = dt.year, dt.month
    months_config = CONTRACT_MONTHS.get(commodity_code, [])
    out = []
    for yr in [year, year+1]:
        for code, m_num in months_config:
            if yr == year and m_num < month:
                continue
            out.append((f"{commodity_code}{code}{str(yr)[2:]}.CBT", yr, m_num, code))
    return out

def _days_to_fnd(active_info, current_date):
    import calendar
    ticker, yr, m_num, m_code = active_info
    fnd_year  = yr - 1 if m_num == 1 else yr
    fnd_month = 12    if m_num == 1 else m_num - 1
    last_day  = calendar.monthrange(fnd_year, fnd_month)[1]
    fnd_date  = datetime.date(fnd_year, fnd_month, last_day)
    return (fnd_date - current_date.date()).days

def choose_swing(c1, c2, active_data, now):
    days = _days_to_fnd(c1, now)
    if days <= 15:
        return c2
    close = active_data.get("close", 0)
    atr   = active_data.get("atr", 0)
    s1    = active_data.get("s1", 0)
    r1    = active_data.get("r1", 0)
    signal = active_data.get("signal", "Neutral")
    near = (close <= s1 + 1.5*atr) if signal == "Bullish" else (close >= r1 - 1.5*atr)
    return c2 if not near else c1

# ── Download & Analyze ────────────────────────────────────────────────
def download_h1(commodity, ticker_symbol, suffix):
    csv_path = get_csv_str(commodity, suffix)
    try:
        print(f"    [D] {ticker_symbol} ({suffix})...")
        tk = yf.Ticker(ticker_symbol)
        df = tk.history(period="30d", interval="1h")
        if df.empty:
            print(f"    [WARN] No data for {ticker_symbol}")
            return False
        df = df.reset_index()
        df["Time"] = df["Datetime"].dt.strftime("%Y-%m-%d %H:%M")
        try: oi_val = int(tk.info.get("openInterest", 0) or 0)
        except: oi_val = 0
        df["OpenInterest"] = oi_val
        df = df[["Time","Open","High","Low","Close","Volume","OpenInterest"]]
        df.to_csv(csv_path, index=False)
        analyze_cbot_data(csv_path)
        print(f"    [OK] {len(df)} candles -> {os.path.basename(csv_path)}")
        return True
    except Exception as e:
        print(f"    [ERR] {e}")
        return False

def get_latest_row(commodity, suffix):
    csv_path = get_csv_str(commodity, suffix)
    if not os.path.exists(csv_path): return {}
    try:
        df = pd.read_csv(csv_path)
        if df.empty: return {}
        row = df.iloc[-1]
        return {k: float(row[k]) if k != "Time" else str(row[k]) 
                for k in ["Time","Open","High","Low","Close","Volume","OpenInterest",
                          "EMA_21","EMA_50","Volatility","Signal","RSI","ATR",
                          "S1","S2","R1","R2"] if k in row}
    except: return {}

# ── Volume / OI History ───────────────────────────────────────────────
def update_oi_history(code, active_ticker):
    hist_path = OUTPUT_DIR / "daily_market_history.json"
    history = {}
    if hist_path.exists():
        try:
            with open(hist_path,"r",encoding="utf-8") as f: history = json.load(f)
        except: pass
    if code not in history: history[code] = {}

    tk  = yf.Ticker(active_ticker)
    df5 = tk.history(period="5d")
    if df5.empty: return {}

    try: today_oi = int(tk.info.get("openInterest",0) or 0)
    except: today_oi = 0
    for idx, row in df5.iterrows():
        d = idx.strftime("%Y-%m-%d")
        existing_oi = history[code].get(d,{}).get("open_interest", today_oi)
        history[code][d] = {
            "volume": float(row["Volume"]),
            "open_interest": today_oi if d == df5.index[-1].strftime("%Y-%m-%d") else int(existing_oi),
            "close": float(row["Close"]),
            "open":  float(row["Open"]),
        }
    with open(hist_path,"w",encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    sorted_dates = sorted([d for d in history[code] if d < df5.index[-1].strftime("%Y-%m-%d")])
    last_row = df5.iloc[-1]
    today_vol   = float(last_row["Volume"])
    today_close = float(last_row["Close"])
    prev_vol = prev_oi = prev_close = 0
    if sorted_dates:
        for d in reversed(sorted_dates):
            e = history[code][d]
            if e.get("volume",0) > 0:
                prev_vol, prev_oi, prev_close = e["volume"], e.get("open_interest",0), e["close"]
                break
    from technical_analysis import analyze_liquidity_trend
    trend, logic = analyze_liquidity_trend(today_close-prev_close, today_vol-prev_vol, today_oi-prev_oi)
    return {"trend": trend, "logic": logic, "today_vol": today_vol,
            "today_oi": today_oi, "today_close": today_close}

# ── Contracts Meta ────────────────────────────────────────────────────
def save_contracts_meta(meta):
    meta_path = OUTPUT_DIR / "contracts_meta.json"
    meta["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(meta_path,"w",encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# ── Main Fetch ────────────────────────────────────────────────────────
def run_fetch_prices(force=False):
    """Fetch H1 prices. force=True: bo qua kiem tra gio giao dich."""
    if not force and not is_cbot_open():
        print("  [SKIP] CBOT dang dong cua.")
        return True
    ensure_output_dir()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    meta, errors = {}, []

    for code in COMMODITY_CODES:
        print(f"\n  -- {code} ---")
        try:
            c1    = get_active_contract(code, now)
            c2    = get_next_contract(code, c1, now)
            c_dca = get_dca_contract(code, now)

            # Tai active truoc de quyet dinh swing
            download_h1(code, c1[0], "active")
            active_data = get_latest_row(code, "active")
            c_swing = choose_swing(c1, c2, active_data, now)

            # Download swing & dca (de tranh tai lai neu trung nhau)
            if c_swing[0] == c1[0]:
                shutil.copyfile(get_csv_str(code,"active"), get_csv_str(code,"swing"))
                print(f"    Swing = Active ({c1[0]})")
            else:
                download_h1(code, c_swing[0], "swing")

            if c_dca[0] == c1[0]:
                shutil.copyfile(get_csv_str(code,"active"), get_csv_str(code,"dca"))
            elif c_dca[0] == c_swing[0]:
                shutil.copyfile(get_csv_str(code,"swing"), get_csv_str(code,"dca"))
            else:
                download_h1(code, c_dca[0], "dca")

            hist = update_oi_history(code, c1[0])
            print(f"    Liquidity: {hist.get('trend','?')}")
            meta[code] = {
                "active":  {"ticker": c1[0],      "year": c1[1],      "month": c1[2]},
                "swing":   {"ticker": c_swing[0],  "year": c_swing[1], "month": c_swing[2]},
                "dca":     {"ticker": c_dca[0],    "year": c_dca[1],   "month": c_dca[2]},
                "liquidity": hist,
            }
            print(f"  [OK] {code}: Active={c1[0]} Swing={c_swing[0]} DCA={c_dca[0]}")
        except Exception as e:
            print(f"  [ERR] {code}: {e}")
            errors.append(f"{code}: {e}")

    save_contracts_meta(meta)
    update_status("prices", "OK" if not errors else "PARTIAL", 
                  f"{len(COMMODITY_CODES)-len(errors)}/{len(COMMODITY_CODES)} OK")
    return len(errors) == 0

if __name__ == "__main__":
    print("="*50)
    print("  FETCH PRICES (H1) - ZC/ZW")
    print("="*50)
    run_fetch_prices(force=True)
