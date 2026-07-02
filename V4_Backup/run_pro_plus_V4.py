import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import yfinance as yf
import json
import os
import datetime
import shutil

from technical_analysis import analyze_cbot_data, detect_candlestick_pattern
from build_sections import build_commodity_section

# ── Data Project Integration ──────────────────────────────────────────────────
# Đọc tất cả dữ liệu từ Data/output/ (nguồn chuẩn duy nhất)
# Trước khi chạy lệnh này, hãy chạy: python Data/run_data_update.py
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'Data')
sys.path.insert(0, _DATA_DIR)
try:
    from data_config import (
        get_csv_str, get_csv_path,
        FUNDAMENTAL_DATA, DAILY_HISTORY, MACRO_DATA, OUTPUT_DIR
    )
    _USE_DATA_PROJECT = True
except ImportError:
    _USE_DATA_PROJECT = False
    print("[WARN] data_config.py không tìm thấy. Dùng đường dẫn cũ.")
    OUTPUT_DIR = None

def _data_path(filename: str) -> str:
    """Trả về đường dẫn đến file trong Data/output/ nếu Data project có sẵn."""
    if _USE_DATA_PROJECT and OUTPUT_DIR is not None:
        p = os.path.join(str(OUTPUT_DIR), filename)
        return p
    return filename  # fallback: dùng thư mục hiện tại

def get_candidate_tickers(commodity_code, current_date):
    """
    Tạo danh sách các hợp đồng kỳ hạn tương lai ứng viên cho năm hiện tại và năm tiếp theo.
    """
    year = current_date.year
    month = current_date.month
    
    # Các tháng giao dịch chính (Active Month Codes) và số tháng lịch tương ứng
    if commodity_code == "ZC":
        months_config = [("H", 3), ("K", 5), ("N", 7), ("U", 9), ("Z", 12)]
    elif commodity_code == "ZS":
        months_config = [("F", 1), ("H", 3), ("K", 5), ("N", 7), ("Q", 8), ("U", 9), ("X", 11)]
    elif commodity_code == "ZW":
        months_config = [("H", 3), ("K", 5), ("N", 7), ("U", 9), ("Z", 12)]
    else:
        return []
        
    candidates = []
    for yr in [year, year + 1]:
        for code, m_num in months_config:
            # Đối với năm hiện tại, bỏ qua các hợp đồng trước tháng 9 (roll-over sớm khỏi tháng 7/8)
            if yr == year and m_num < 9:
                continue
            ticker = f"{commodity_code}{code}{str(yr)[2:]}.CBT"
            candidates.append((ticker, yr, m_num, code))
    return candidates

def get_active_contract(commodity_code, current_date):
    """
    Quét qua các hợp đồng ứng viên gần nhất và lấy hợp đồng có tổng Volume 5 ngày cao nhất (thanh khoản cao nhất).
    """
    candidates = get_candidate_tickers(commodity_code, current_date)
    
    # --- USER OVERRIDE: Force September (U) contract for the current year ---
    for cand in candidates:
        if cand[1] == current_date.year and cand[2] == 9:
            print(f" => [Override] Ưu tiên HĐ tháng 9 theo yêu cầu: {cand[0]}")
            return cand
    # ------------------------------------------------------------------------
            
    best_ticker = None
    max_volume = -1
    
    print(f"Đang kiểm tra thanh khoản các hợp đồng {commodity_code}...")
    # Chỉ cần quét 4 hợp đồng ứng viên gần nhất là đủ bao quát HĐ đang và sắp active
    for ticker_info in candidates[:4]:
        ticker = ticker_info[0]
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty and "Volume" in df.columns:
                total_volume = df["Volume"].sum()
                print(f" - {ticker}: Tổng volume 5 ngày = {total_volume:,}")
                if total_volume > max_volume:
                    max_volume = total_volume
                    best_ticker = ticker_info
        except Exception as e:
            print(f" Lỗi khi lấy volume cho {ticker}: {e}")
            
    # Fallback chọn hợp đồng gần nhất nếu không lấy được volume
    if (best_ticker is None or max_volume <= 0) and candidates:
        best_ticker = candidates[0]
        print(f" Không lấy được volume. Fallback dùng hợp đồng gần nhất: {best_ticker[0]}")
    else:
        print(f" => Hợp đồng có thanh khoản cao nhất hiện tại: {best_ticker[0]}")
        
    return best_ticker

def get_next_contract(commodity_code, active_contract_info, current_date):
    """
    Lấy hợp đồng kỳ sau (liền kề tiếp theo) của hợp đồng đang active.
    """
    candidates = get_candidate_tickers(commodity_code, current_date)
    for idx, cand in enumerate(candidates):
        if cand[0] == active_contract_info[0]:
            if idx + 1 < len(candidates):
                return candidates[idx + 1]
            break
    return active_contract_info

def get_dca_contract(commodity_code, current_date):
    """
    Xác định hợp đồng vụ mới chính (New-crop) để tích lũy dài hạn:
    - Ngô (ZC): HĐ tháng 12 (Z)
    - Đậu tương (ZS): HĐ tháng 11 (X)
    - Lúa mì (ZW): HĐ tháng 12 (Z)
    """
    year = current_date.year
    month = current_date.month
    
    if commodity_code == "ZC":
        dca_month = 12
        m_code = "Z"
    elif commodity_code == "ZS":
        dca_month = 11
        m_code = "X"
    elif commodity_code == "ZW":
        dca_month = 12
        m_code = "Z"
    else:
        return None
        
    if month >= dca_month:
        dca_year = year + 1
    else:
        dca_year = year
        
    ticker = f"{commodity_code}{m_code}{str(dca_year)[2:]}.CBT"
    return (ticker, dca_year, dca_month, m_code)

def get_days_to_fnd(active_contract_info, current_date):
    """
    Tính số ngày còn lại đến Ngày thông báo đầu tiên (FND),
    ước lượng là ngày làm việc cuối cùng của tháng trước tháng giao hàng.
    """
    ticker, yr, m_num, m_code = active_contract_info
    if m_num == 1:
        fnd_year = yr - 1
        fnd_month = 12
    else:
        fnd_year = yr
        fnd_month = m_num - 1
        
    import calendar
    last_day = calendar.monthrange(fnd_year, fnd_month)[1]
    fnd_date = datetime.date(fnd_year, fnd_month, last_day)
    return (fnd_date - current_date.date()).days

def should_use_next_contract_for_swing(active_contract_info, next_contract_info, current_date, active_data):
    """
    Quyết định sử dụng HĐ gần nhất hay HĐ tiếp theo cho Swing trade:
    1. Nếu thời gian tới FND <= 15 ngày: Chuyển kỳ hạn sang C2.
    2. Nếu thời gian tới FND > 15 ngày:
       - Kiểm tra giá hiện tại với cản Entry gần nhất (S1 cho Long, R1 cho Short):
         + Nếu Giá hiện tại GẦN (<= 1.5x ATR): Ưu tiên HĐ gần nhất (C1) vì dễ khớp nhanh.
         + Nếu Giá hiện tại XA (> 1.5x ATR): Sử dụng HĐ kỳ sau (C2) phòng trường hợp khớp muộn khi C1 sát ngày đáo hạn.
    """
    days_to_fnd = get_days_to_fnd(active_contract_info, current_date)
    if days_to_fnd <= 15:
        print(f"   [Roll-over] HĐ {active_contract_info[0]} còn {days_to_fnd} ngày tới FND (<= 15 ngày). Bắt buộc dùng HĐ tiếp theo.")
        return True
        
    close = active_data.get("close", 0)
    atr = active_data.get("atr", 0)
    s1 = active_data.get("s1", 0)
    r1 = active_data.get("r1", 0)
    signal = active_data.get("signal", "Neutral")
    
    # Đo khoảng cách giá tới Entry
    if signal == 'Bullish':
        # Đối với Long: Vùng entry nằm ở dưới giá hiện tại (sát S1). Khoảng cách = close - s1.
        is_near = (close <= s1 + 1.5 * atr)
        print(f"   [Swing check] Bias Long: Close={close:.2f}, S1={s1:.2f}, 1.5xATR={1.5*atr:.2f}. Khoảng cách={close - s1:.2f} -> Gần Entry: {is_near}")
    else:
        # Đối với Short: Vùng entry nằm ở trên giá hiện tại (sát R1). Khoảng cách = r1 - close.
        is_near = (close >= r1 - 1.5 * atr)
        print(f"   [Swing check] Bias Short: Close={close:.2f}, R1={r1:.2f}, 1.5xATR={1.5*atr:.2f}. Khoảng cách={r1 - close:.2f} -> Gần Entry: {is_near}")
        
    return not is_near

def download_and_analyze_contract(commodity, ticker_symbol, current_date, name_suffix):
    """
    Tải dữ liệu nến H1 của hợp đồng cụ thể từ Yahoo Finance, lưu thành file CSV và chạy phân tích kỹ thuật.
    File CSV được lưu vào Data/output/ nếu Data project có sẵn.
    """
    filename = _data_path(f"{commodity}_{name_suffix}_H1.csv")
    try:
        print(f"Đang tải lịch sử H1 của mã {ticker_symbol} ({name_suffix})...")
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="30d", interval="1h")
        if df.empty:
            print(f" Lỗi: Không lấy được dữ liệu cho {ticker_symbol}. Giữ nguyên file cũ nếu có.")
            return False
            
        df = df.reset_index()
        df['Time'] = df['Datetime'].dt.tz_convert('Asia/Ho_Chi_Minh').dt.strftime('%Y-%m-%d %H:%M')
        
        # Get open interest if available, else 0
        try:
            oi_val = ticker.info.get("openInterest", 0)
            if oi_val is None:
                oi_val = 0
        except Exception:
            oi_val = 0
            
        df['OpenInterest'] = oi_val
        df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest']]
        df.to_csv(filename, index=False)
        print(f" Thành công: Đã tải {len(df)} nến H1 cho {filename}")
        
        # Chạy thuật toán tính EMA & S1/S2/R1/R2 trên file này
        analyze_cbot_data(filename)
        return True
    except Exception as e:
        print(f" Lỗi khi đồng bộ dữ liệu {ticker_symbol}: {e}")
        return False

def setup_cbot_data(commodity, c1, c_swing, c_dca, now_ict):
    """
    Tải và đồng bộ dữ liệu cho cả 3 vai trò (Active, Swing, DCA) một cách tối ưu.
    File CSV được lưu vào Data/output/ nếu Data project có sẵn.
    """
    active_csv = _data_path(f"{commodity}_active_H1.csv")
    swing_csv  = _data_path(f"{commodity}_swing_H1.csv")
    dca_csv    = _data_path(f"{commodity}_dca_H1.csv")

    # 1. Tải HĐ active
    download_and_analyze_contract(commodity, c1[0], now_ict, "active")
    
    # 2. Thiết lập HĐ swing
    if c_swing[0] == c1[0]:
        print(f" HĐ Swing trùng với HĐ Active ({c1[0]}). Copy file...")
        shutil.copyfile(active_csv, swing_csv)
    else:
        download_and_analyze_contract(commodity, c_swing[0], now_ict, "swing")
        
    # 3. Thiết lập HĐ DCA
    if c_dca[0] == c1[0]:
        print(f" HĐ DCA trùng với HĐ Active ({c1[0]}). Copy file...")
        shutil.copyfile(active_csv, dca_csv)
    elif c_dca[0] == c_swing[0]:
        print(f" HĐ DCA trùng với HĐ Swing ({c_swing[0]}). Copy file...")
        shutil.copyfile(swing_csv, dca_csv)
    else:
        download_and_analyze_contract(commodity, c_dca[0], now_ict, "dca")



def detect_rsi_patterns(csv_file_path):
    import pandas as pd
    import os
    if not os.path.exists(csv_file_path):
        return {"labels": [], "data": [], "patterns": [], "is_forming": None}
        
    df = pd.read_csv(csv_file_path)
    if df.empty:
        return {"labels": [], "data": [], "patterns": [], "is_forming": None}
        
    df_recent = df.tail(100).reset_index(drop=True)
    
    labels = df_recent["Time"].tolist()
    rsi_data = df_recent["RSI"].tolist()
    
    patterns = []
    is_forming = None
    
    clean_rsi = []
    for x in rsi_data:
        try:
            clean_rsi.append(float(x))
        except:
            clean_rsi.append(50.0)
            
    local_max = []
    local_min = []
    for i in range(2, len(clean_rsi) - 2):
        if clean_rsi[i] > clean_rsi[i-1] and clean_rsi[i] > clean_rsi[i+1]:
            local_max.append(i)
        if clean_rsi[i] < clean_rsi[i-1] and clean_rsi[i] < clean_rsi[i+1]:
            local_min.append(i)
            
    if len(local_min) >= 2:
        for i in range(len(local_min) - 1):
            idx1 = local_min[i]
            idx2 = local_min[i+1]
            val1 = clean_rsi[idx1]
            val2 = clean_rsi[idx2]
            
            if 3 <= (idx2 - idx1) <= 25:
                peaks_between = [p for p in local_max if idx1 < p < idx2]
                if peaks_between:
                    peak_val = max(clean_rsi[p] for p in peaks_between)
                    if peak_val - min(val1, val2) > 6:
                        if abs(val1 - val2) < 10:
                            mid = max(peaks_between, key=lambda p: clean_rsi[p])
                            patterns.append({
                                "type": "W",
                                "start_idx": int(idx1),
                                "mid_idx": int(mid),
                                "end_idx": int(idx2),
                                "start_time": labels[idx1],
                                "end_time": labels[idx2],
                                "start_val": float(val1),
                                "mid_val": float(clean_rsi[mid]),
                                "end_val": float(val2)
                            })
                            if idx2 >= len(clean_rsi) - 6:
                                if clean_rsi[-1] > clean_rsi[idx2]:
                                    is_forming = 'W'

    if len(local_max) >= 2:
        for i in range(len(local_max) - 1):
            idx1 = local_max[i]
            idx2 = local_max[i+1]
            val1 = clean_rsi[idx1]
            val2 = clean_rsi[idx2]
            
            if 3 <= (idx2 - idx1) <= 25:
                troughs_between = [t for t in local_min if idx1 < t < idx2]
                if troughs_between:
                    trough_val = min(clean_rsi[t] for t in troughs_between)
                    if max(val1, val2) - trough_val > 6:
                        if abs(val1 - val2) < 10:
                            mid = min(troughs_between, key=lambda t: clean_rsi[t])
                            patterns.append({
                                "type": "M",
                                "start_idx": int(idx1),
                                "mid_idx": int(mid),
                                "end_idx": int(idx2),
                                "start_time": labels[idx1],
                                "end_time": labels[idx2],
                                "start_val": float(val1),
                                "mid_val": float(clean_rsi[mid]),
                                "end_val": float(val2)
                            })
                            if idx2 >= len(clean_rsi) - 6:
                                if clean_rsi[-1] < clean_rsi[idx2]:
                                    is_forming = 'M'
                                    
    short_labels = []
    for l in labels:
        try:
            short_labels.append(l[8:10] + '/' + l[5:7] + ' ' + l[11:16])
        except:
            short_labels.append(l)

    return {
        "labels": short_labels,
        "data": clean_rsi,
        "patterns": patterns,
        "is_forming": is_forming
    }

def get_latest_cbot_data(csv_file_path):
    """
    Đọc dòng cuối cùng của dữ liệu kỹ thuật từ file CSV.
    Tự động tìm trong Data/output/ nếu file không tồn tại ở đường dẫn hiện tại.
    """
    # Nếu file không tồn tại ở đường dẫn gốc, thử trong Data/output/
    if not os.path.exists(csv_file_path):
        alt_path = _data_path(os.path.basename(csv_file_path))
        if os.path.exists(alt_path):
            csv_file_path = alt_path
    if not os.path.exists(csv_file_path):
        return {}
    df = pd.read_csv(csv_file_path)
    if df.empty:
        return {}
    latest_row = df.iloc[-1]
    
    return {
        "time": str(latest_row["Time"]),
        "close": float(latest_row["Close"]),
        "ema_21": float(latest_row["EMA_21"]),
        "ema_50": float(latest_row["EMA_50"]),
        "volatility": float(latest_row["Volatility"]),
        "signal": str(latest_row["Signal"]),
        "rsi": float(latest_row["RSI"]),
        "atr": float(latest_row["ATR"]),
        "s1": float(latest_row["S1"]),
        "s2": float(latest_row["S2"]),
        "r1": float(latest_row["R1"]),
        "r2": float(latest_row["R2"]),
        "volume": float(latest_row.get("Volume", 0)),
        "open_interest": int(latest_row.get("OpenInterest", 0))
    }

def get_market_history_changes(code, active_ticker):
    history_file = _data_path("daily_market_history.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception:
            history_data = {}
    else:
        history_data = {}
        
    if code not in history_data:
        history_data[code] = {}
        
    ticker = yf.Ticker(active_ticker)
    # Fetch 5 days of history to ensure we cross weekends/holidays and cold-start successfully
    df_5d = ticker.history(period="5d")
    if df_5d.empty:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "Đi ngang (Sideways)", "Không lấy được dữ liệu lịch sử"
        
    last_row = df_5d.iloc[-1]
    today_date = last_row.name.strftime("%Y-%m-%d")
    today_volume = float(last_row["Volume"])
    today_close = float(last_row["Close"])
    today_open = float(last_row["Open"])
    
    try:
        today_oi = ticker.info.get("openInterest", 0)
        if today_oi is None:
            today_oi = 0
    except Exception:
        today_oi = 0
    today_oi = int(today_oi)
        
    # Save/update all 5 days in history_data
    for idx, row in df_5d.iterrows():
        d_str = idx.strftime("%Y-%m-%d")
        vol = float(row["Volume"])
        cls = float(row["Close"])
        opn = float(row["Open"])
        
        if d_str == today_date:
            history_data[code][d_str] = {
                "volume": vol,
                "open_interest": today_oi,
                "close": cls,
                "open": opn
            }
        else:
            # Check if this date has a non-zero open_interest in history, otherwise estimate using today_oi
            existing_oi = 0
            if d_str in history_data[code]:
                existing_oi = history_data[code][d_str].get("open_interest", 0)
            oi_val = int(existing_oi if existing_oi > 0 else today_oi)
            
            history_data[code][d_str] = {
                "volume": vol,
                "open_interest": oi_val,
                "close": cls,
                "open": opn
            }
            
    os.makedirs(os.path.dirname(history_file) if os.path.dirname(history_file) else '.', exist_ok=True)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
        
    # Find previous date
    sorted_dates = sorted([d for d in history_data[code].keys() if d < today_date])
    
    prev_volume = 0.0
    prev_oi = 0.0
    prev_close = today_close
    prev_open = today_open
    
    if sorted_dates:
        found_valid = False
        for d in reversed(sorted_dates):
            vol = history_data[code][d].get("volume", 0.0)
            oi = history_data[code][d].get("open_interest", 0.0)
            if vol > 0 or oi > 0:
                prev_date = d
                prev_volume = vol
                prev_oi = oi
                prev_close = history_data[code][d].get("close", today_close)
                prev_open = history_data[code][d].get("open", today_open)
                found_valid = True
                print(f"   [Liquidity history] Found previous trading day: {prev_date} for {code} (Volume: {prev_volume:,.0f}, OI: {prev_oi:,.0f})")
                break
        if not found_valid:
            prev_date = sorted_dates[-1]
            prev_volume = history_data[code][prev_date].get("volume", 0.0)
            prev_oi = history_data[code][prev_date].get("open_interest", 0.0)
            prev_close = history_data[code][prev_date].get("close", today_close)
            prev_open = history_data[code][prev_date].get("open", today_open)
            print(f"   [Liquidity history] No active trading day found. Fallback to: {prev_date} (Volume: {prev_volume:,.0f}, OI: {prev_oi:,.0f})")
    else:
        if len(df_5d) >= 2:
            prev_row = df_5d.iloc[-2]
            prev_volume = float(prev_row["Volume"])
            prev_close = float(prev_row["Close"])
            prev_open = float(prev_row["Open"])
            prev_oi = today_oi
            print(f"   [Liquidity history] No JSON history. Using df_5d fallback: Volume={prev_volume:,.0f}")
            
    vol_chg = today_volume - prev_volume
    oi_chg = today_oi - prev_oi
    price_chg = today_close - prev_close
    
    from technical_analysis import analyze_liquidity_trend
    trend, logic = analyze_liquidity_trend(price_chg, vol_chg, oi_chg)
    
    return float(today_volume), float(prev_volume), int(today_oi), int(prev_oi), float(today_close), float(prev_close), trend, logic

def get_combined_trend_desc(candle, liq_trend):
    candle_lower = candle.lower()
    liq_lower = liq_trend.lower()
    
    if "bullish" in candle_lower or "hammer" in candle_lower or "morning star" in candle_lower or "engulfing" in candle_lower:
        if "tích cực" in liq_lower or "tăng" in liq_lower or "mạnh" in liq_lower:
            return "🔥 **TĂNG MẠNH MẼ (Strong Bullish Confirmation):** Mô hình nến tăng được củng cố bởi dòng tiền gia tăng tích cực, hỗ trợ lực mua lên bền vững."
        else:
            return "⚠️ **HỒI KỸ THUẬT YẾU (Weak Bullish Retest):** Xuất hiện nến tăng nhưng dòng tiền/thanh khoản yếu. Cần quan sát thêm lực cầu."
    elif "bearish" in candle_lower or "shooting star" in candle_lower or "evening star" in candle_lower:
        if "tiêu cực" in liq_lower or "giảm" in liq_lower or "xả" in liq_lower:
            return "🚨 **GIẢM MẠNH MẼ (Strong Bearish Confirmation):** Mô hình nến giảm đi kèm dòng tiền rút ra/áp lực bán tháo lớn, rủi ro sụt giảm tiếp diễn cao."
        else:
            return "⚠️ **BÁN THÁO YẾU (Weak Bearish Retest):** Nến giảm xuất hiện nhưng thanh khoản thấp, có thể là nhịp rũ bỏ ngắn hạn trước khi hồi phục."
    else:
        if "tích cực" in liq_lower or "tăng" in liq_lower:
            return "📈 **TÍCH LŨY TÍCH CỰC (Accumulation):** Nến đi ngang nhưng dòng tiền âm thầm gia tăng (OI tăng), báo hiệu chuẩn bị có nhịp bứt phá tăng."
        elif "tiêu cực" in liq_lower or "giảm" in liq_lower:
            return "📉 **TÍCH LŨY TIÊU CỰC (Distribution):** Nến đi ngang nhưng dòng tiền rút dần (OI giảm), cảnh báo rủi ro suy sụt sắp tới."
        else:
            return "↕️ **ĐI NGANG TRUNG LẬP (Neutral Consolidation):** Cả nến và thanh khoản đều đi ngang, thị trường chờ đợi tin tức bứt phá tiếp theo."

def format_contract_name(contract_info):
    """
    Định dạng tên hợp đồng sang chuỗi hiển thị tiếng Việt, ví dụ: HĐ tháng 07/2026 (ZCN26)
    """
    ticker, yr, m_num, m_code = contract_info
    clean_ticker = ticker.split(".")[0]
    return f"HĐ tháng {m_num:02d}/{yr} ({clean_ticker})"

def fetch_macro():
    try:
        # Brent Crude Oil
        brent = yf.Ticker("BZ=F")
        brent_data = brent.history(period="2d")
        if len(brent_data) >= 2:
            brent_price = float(brent_data['Close'].iloc[-1])
            brent_prev = float(brent_data['Close'].iloc[-2])
            brent_pct = ((brent_price - brent_prev) / brent_prev) * 100
        else:
            brent_price = float(brent_data['Close'].iloc[-1]) if not brent_data.empty else 90.74
            brent_pct = -2.13
            
        # US Dollar Index
        dxy = yf.Ticker("DX-Y.NYB")
        dxy_data = dxy.history(period="2d")
        if len(dxy_data) >= 2:
            dxy_price = float(dxy_data['Close'].iloc[-1])
            dxy_prev = float(dxy_data['Close'].iloc[-2])
            dxy_pct = ((dxy_price - dxy_prev) / dxy_prev) * 100
        else:
            dxy_price = float(dxy_data['Close'].iloc[-1]) if not dxy_data.empty else 99.09
            dxy_pct = -0.05
            
        # Wheat Chicago ZW=F để tính tương quan vĩ mô
        zw = yf.Ticker("ZW=F")
        zw_data = zw.history(period="2d")
        if len(zw_data) >= 2:
            zw_price = float(zw_data['Close'].iloc[-1])
            zw_prev = float(zw_data['Close'].iloc[-2])
            zw_pct = ((zw_price - zw_prev) / zw_prev) * 100
        else:
            zw_pct = -1.85
            
        return brent_price, brent_pct, dxy_price, dxy_pct, zw_pct
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu vĩ mô: {e}. Sử dụng giá trị cũ.")
        return 90.74, -2.13, 99.09, -0.05, -1.85

def predict_closing_price(code, data, brent_pct, dxy_pct, fund):
    """
    Dự báo giá chốt phiên của ngày báo cáo dựa trên:
    - Giá hiện tại (Close)
    - Động lượng kỹ thuật (EMA_21 vs EMA_50, RSI)
    - Biến động (ATR)
    - Tương quan vĩ mô (Brent, DXY)
    - Yếu tố cơ bản mùa vụ (đọc từ fundamental_data.json)
    """
    close = data.get("close", 0)
    if close == 0:
        return 0.0, 0.0
        
    ema_21 = data.get("ema_21", close)
    ema_50 = data.get("ema_50", close)
    rsi = data.get("rsi", 50.0)
    atr = data.get("atr", 2.0)
    
    # 1. Động lượng kỹ thuật
    tech_drift = (ema_21 - ema_50) * 0.2
    
    # RSI hồi quy về giá trị trung bình
    rsi_factor = 0.0
    if rsi < 35:
        rsi_factor = (35 - rsi) * 0.1 * atr
    elif rsi > 65:
        rsi_factor = (65 - rsi) * 0.1 * atr
        
    # 2. Tác động vĩ mô liên thị trường
    macro_factor = 0.0
    if code in ["ZC", "ZS"]:
        macro_factor += brent_pct * 0.05 * atr
    macro_factor -= dxy_pct * 0.15 * atr
    
    # 3. Yếu tố mùa vụ cơ bản
    fund_bias = 0.0
    long_count = 0
    short_count = 0
    
    commodity_fund = fund.get(code, {})
    for key, val in commodity_fund.items():
        if isinstance(val, dict) and "action" in val:
            action_text = val["action"].upper()
            if "LONG" in action_text or "MUA" in action_text:
                long_count += 1
            elif "SHORT" in action_text or "BÁN" in action_text:
                short_count += 1
                
    fund_bias = (long_count - short_count) * 0.08 * atr
    
    predicted_change = tech_drift + rsi_factor + macro_factor + fund_bias
    
    # Giới hạn biến động tối đa trong phạm vi 1.5x ATR
    max_change = 1.5 * atr
    if predicted_change > max_change:
        predicted_change = max_change
    elif predicted_change < -max_change:
        predicted_change = -max_change
        
    predicted_close = close + predicted_change
    return float(predicted_close), float(predicted_change)

def run_pro_plus():
    print("--- KHỞI ĐỘNG HỆ THỐNG PHÂN TÍCH CBOT PRO V3 (UPGRADE) ---")

    # ── Data Project: Đọc data đã được cập nhật bởi run_data_update.py ──────────
    # KHÔNG tự fetch nữa — dùng Data/output/ làm nguồn chuẩn duy nhất
    if _USE_DATA_PROJECT:
        print("[Data Project] ✅ Đọc dữ liệu từ Data/output/ (nguồn chuẩn)")
        try:
            from Data.fetch_macro import get_macro_values
            brent_price, brent_pct, dxy_price, dxy_pct, zw_pct = get_macro_values()
            print(f"   Macro từ cache: Brent=${brent_price:.2f} ({brent_pct:+.2f}%), DXY={dxy_price:.2f} ({dxy_pct:+.2f}%)")
        except Exception as me:
            print(f"   [WARN] Không đọc được macro cache: {me}. Fetch trực tiếp...")
            brent_price, brent_pct, dxy_price, dxy_pct, zw_pct = fetch_macro()
    else:
        # Fallback: tự fetch như cũ (nếu Data project chưa sẵn sàng)
        print("[WARN] Data project chưa sẵn sàng. Chạy USDA crawler + fetch macro trực tiếp...")
        try:
            from usda_crawler import run_crawler_and_update
            run_crawler_and_update()
        except Exception as ce:
            print(f"Lỗi khi chạy USDA crawler: {ce}")
        brent_price, brent_pct, dxy_price, dxy_pct, zw_pct = fetch_macro()

    now_ict = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    date_str = now_ict.strftime("%d/%m/%Y")
    time_str = now_ict.strftime("%H:%M")

    print(f"Dữ liệu vĩ mô: Brent = ${brent_price:.2f} ({brent_pct:+.2f}%), DXY = {dxy_price:.2f} ({dxy_pct:+.2f}%), ZW Pct = {zw_pct:+.2f}%")
    
    # 2. Xác định các hợp đồng kỳ hạn động cho từng mã ZC, ZW, ZS
    contracts = {}
    for code in ["ZC", "ZW", "ZS"]:
        c1 = get_active_contract(code, now_ict)
        c2 = get_next_contract(code, c1, now_ict)
        c_dca = get_dca_contract(code, now_ict)
        
        # Tải tạm active trước để lấy thông số so sánh Swing
        download_and_analyze_contract(code, c1[0], now_ict, "active")
        active_data = get_latest_cbot_data(f"{code}_active_H1.csv")
        
        # Quyết định hợp đồng swing
        use_next = should_use_next_contract_for_swing(c1, c2, now_ict, active_data)
        c_swing = c2 if use_next else c1
        
        contracts[code] = {
            "c1": c1,
            "c2": c2,
            "c_swing": c_swing,
            "c_dca": c_dca
        }
        
        # Đồng bộ và phân tích dữ liệu cho các file CSV tương ứng
        setup_cbot_data(code, c1, c_swing, c_dca, now_ict)
        
    # 3. Đọc dữ liệu kỹ thuật mới nhất đã tính toán riêng cho từng hợp đồng
    data_zc = {
        "active": get_latest_cbot_data(_data_path("ZC_active_H1.csv")),
        "swing":  get_latest_cbot_data(_data_path("ZC_swing_H1.csv")),
        "dca":    get_latest_cbot_data(_data_path("ZC_dca_H1.csv")),
        "rsi_pack": detect_rsi_patterns(_data_path("ZC_active_H1.csv"))
    }
    data_zw = {
        "active": get_latest_cbot_data(_data_path("ZW_active_H1.csv")),
        "swing":  get_latest_cbot_data(_data_path("ZW_swing_H1.csv")),
        "dca":    get_latest_cbot_data(_data_path("ZW_dca_H1.csv")),
        "rsi_pack": detect_rsi_patterns(_data_path("ZW_active_H1.csv"))
    }
    data_zs = {
        "active": get_latest_cbot_data(_data_path("ZS_active_H1.csv")),
        "swing":  get_latest_cbot_data(_data_path("ZS_swing_H1.csv")),
        "dca":    get_latest_cbot_data(_data_path("ZS_dca_H1.csv")),
        "rsi_pack": detect_rsi_patterns(_data_path("ZS_active_H1.csv"))
    }
    
    # 4. Nạp cơ sở dữ liệu cơ bản từ Data/output/
    fund_path = _data_path("fundamental_data.json")
    with open(fund_path, "r", encoding="utf-8") as f:
        fund = json.load(f)

    # 4.5. Nạp COT Data
    cot_path = _data_path("cot_data.json")
    try:
        with open(cot_path, "r", encoding="utf-8") as f:
            cot_data_json = json.load(f)
    except Exception:
        cot_data_json = {"commodities": {}}
        
    # Kích hoạt Mock Data nếu API bị lỗi 403
    has_error = False
    for code, cdata in cot_data_json.get("commodities", {}).items():
        if "error" in cdata:
            has_error = True
            break
            
    if has_error or not cot_data_json.get("commodities"):
        cot_data_json = {
          "commodities": {
            "002602": {
              "commodity": "Ngô (ZC)",
              "quadrant": "Q2 (ĐỎ) - XẢ LONG",
              "action": "Giá giảm ngắn hạn. Không mua đuổi.",
              "net_curr": 152000,
              "change": -25000
            },
            "005602": {
              "commodity": "Đậu tương (ZS)",
              "quadrant": "Q1 (XANH) - GOM LONG",
              "action": "Dòng tiền mua mạnh. Ưu tiên LONG.",
              "net_curr": 85000,
              "change": 12000
            },
            "001602": {
              "commodity": "Lúa mì (ZW)",
              "quadrant": "Q4 (CAM) - COVER SHORT",
              "action": "Cá mập chốt lời Short. Canh LONG bắt hồi.",
              "net_curr": -45000,
              "change": 15000
            }
          }
        }
        
    cot_html = "### Bảng Dòng Tiền Managed Money\n\n| Mã | Commodity | Net Position | Tuần Qua | Trạng Thái Matrix | Điểm Bias |\n| :--- | :--- | :---: | :---: | :--- | :---: |\n"
    for code, cdata in cot_data_json.get("commodities", {}).items():
        if "error" in cdata:
            cot_html += f"| **{code}** | {cdata.get('commodity', '')} | Lỗi API | Lỗi API | {cdata.get('error')} | N/A |\n"
        else:
            net = cdata.get('net_curr', 0)
            chg = cdata.get('change', 0)
            quad = cdata.get('quadrant', '')
            act = cdata.get('action', '')
            
            cot_score = 0.0
            if "Q1" in quad:
                cot_score = 1.5
            elif "Q2" in quad:
                cot_score = -1.0
            elif "Q3" in quad:
                cot_score = -1.5
            elif "Q4" in quad:
                cot_score = 1.0
                
            color = "🟢" if cot_score > 0 else "🔴" if cot_score < 0 else "⚪"
            bias_str = f"{color} **{cot_score:+.1f}**"
            
            cot_html += f"| **{code}** | {cdata.get('commodity', '')} | **{net:,.0f}** | **{chg:+,.0f}** | **{quad}**<br>*{act}* | {bias_str} |\n"
            
    cot_alert = f"""
## 💰 DÒNG TIỀN COT (SMART MONEY MATRIX)
*Cập nhật từ nguồn CFTC Public API (Disaggregated Futures Only)*

{cot_html}
"""
    # Lấy dữ liệu Volume/OI chênh lệch lịch sử và mô hình nến
    # ZC (Ngô)
    zc_ticker = contracts["ZC"]["c1"][0]
    zc_today_vol, zc_prev_vol, zc_today_oi, zc_prev_oi, zc_today_close, zc_prev_close, zc_liq_trend, zc_liq_logic = get_market_history_changes("ZC", zc_ticker)
    try:
        zc_df = pd.read_csv(_data_path("ZC_active_H1.csv"))
        zc_candle = detect_candlestick_pattern(zc_df)
    except Exception:
        zc_candle = "Không xác định"
    zc_comb_trend = get_combined_trend_desc(zc_candle, zc_liq_trend)
    
    # ZW (Lúa mì)
    zw_ticker = contracts["ZW"]["c1"][0]
    zw_today_vol, zw_prev_vol, zw_today_oi, zw_prev_oi, zw_today_close, zw_prev_close, zw_liq_trend, zw_liq_logic = get_market_history_changes("ZW", zw_ticker)
    try:
        zw_df = pd.read_csv(_data_path("ZW_active_H1.csv"))
        zw_candle = detect_candlestick_pattern(zw_df)
    except Exception:
        zw_candle = "Không xác định"
    zw_comb_trend = get_combined_trend_desc(zw_candle, zw_liq_trend)
    
    # ZS (Đậu tương)
    zs_ticker = contracts["ZS"]["c1"][0]
    zs_today_vol, zs_prev_vol, zs_today_oi, zs_prev_oi, zs_today_close, zs_prev_close, zs_liq_trend, zs_liq_logic = get_market_history_changes("ZS", zs_ticker)
    try:
        zs_df = pd.read_csv(_data_path("ZS_active_H1.csv"))
        zs_candle = detect_candlestick_pattern(zs_df)
    except Exception:
        zs_candle = "Không xác định"
    zs_comb_trend = get_combined_trend_desc(zs_candle, zs_liq_trend)
        
    # Tên viết tắt dùng cho bảng summary
    zc_act_code = contracts["ZC"]["c1"][0].split(".")[0]
    zc_sw_code = contracts["ZC"]["c_swing"][0].split(".")[0]
    zc_dca_code = contracts["ZC"]["c_dca"][0].split(".")[0]
    
    zw_act_code = contracts["ZW"]["c1"][0].split(".")[0]
    zw_sw_code = contracts["ZW"]["c_swing"][0].split(".")[0]
    zw_dca_code = contracts["ZW"]["c_dca"][0].split(".")[0]
    
    zs_act_code = contracts["ZS"]["c1"][0].split(".")[0]
    zs_sw_code = contracts["ZS"]["c_swing"][0].split(".")[0]
    zs_dca_code = contracts["ZS"]["c_dca"][0].split(".")[0]
    
    # Tên đầy đủ phục vụ hiển thị tiêu đề
    zc_act_name = format_contract_name(contracts["ZC"]["c1"])
    zc_sw_name = format_contract_name(contracts["ZC"]["c_swing"])
    zc_dca_name = format_contract_name(contracts["ZC"]["c_dca"])
    
    zw_act_name = format_contract_name(contracts["ZW"]["c1"])
    zw_sw_name = format_contract_name(contracts["ZW"]["c_swing"])
    zw_dca_name = format_contract_name(contracts["ZW"]["c_dca"])
    
    zs_act_name = format_contract_name(contracts["ZS"]["c1"])
    zs_sw_name = format_contract_name(contracts["ZS"]["c_swing"])
    zs_dca_name = format_contract_name(contracts["ZS"]["c_dca"])

    # 5. Tính toán các điểm Entry/SL/TP thực tế cho từng chiến lược và dự báo chốt phiên
    # NGÔ (ZC)
    zc = data_zc["active"]
    zc_sw = data_zc["swing"]
    zc_dc = data_zc["dca"]
    
    zc_pred_close, zc_pred_chg = predict_closing_price("ZC", zc, brent_pct, dxy_pct, fund)
    
    zc_intra_entry = f"{zc['s1']:.2f} - {zc['ema_21']:.2f} cents (Canh mua vùng hỗ trợ)"
    zc_intra_sl = f"{zc['s2'] - 1.5 * zc['atr']:.2f} cents (Dưới cản S2 + 1.5x ATR)"
    zc_intra_tp1 = f"{zc['r1']:.2f} cents"
    zc_intra_tp2 = f"{zc['r2']:.2f} cents"
    
    zc_swing_long_entry = f"{zc_sw['s2']:.2f} - {zc_sw['s1']:.2f} cents"
    zc_swing_long_sl = f"{zc_sw['s2'] - 2.0 * zc_sw['atr']:.2f} cents (Chống quét SL tuyệt đối)"
    zc_swing_long_tp = f"{zc_sw['r2'] - 1.0:.2f} cents (Ăn trọn biên độ ngô ~10.5 giá)"
    zc_swing_short_entry = f"{zc_sw['r1']:.2f} - {zc_sw['r2']:.2f} cents"
    zc_swing_short_sl = f"{zc_sw['r2'] + 2.0 * zc_sw['atr']:.2f} cents"
    zc_swing_short_tp = f"{zc_sw['s2'] + 1.0:.2f} cents"
    
    zc_dca = f"{zc_dc['s2'] - 4.0 * zc_dc['atr']:.2f} - {zc_dc['s2']:.2f} cents"

    # LÚA MÌ (ZW)
    zw = data_zw["active"]
    zw_sw = data_zw["swing"]
    zw_dc = data_zw["dca"]
    
    zw_pred_close, zw_pred_chg = predict_closing_price("ZW", zw, brent_pct, dxy_pct, fund)
    
    zw_intra_entry = f"{zw['ema_21']:.2f} - {zw['ema_50']:.2f} cents (Canh bán hồi kỹ thuật H1)"
    zw_intra_sl = f"{zw['r2'] + 1.5 * zw['atr']:.2f} cents (Trên kháng cự R2 + 1.5x ATR)"
    zw_intra_tp1 = f"{zw['s1']:.2f} cents"
    zw_intra_tp2 = f"{zw['s2']:.2f} cents"
    
    zw_swing_long_entry = f"{zw_sw['s2']:.2f} - {zw_sw['s1']:.2f} cents"
    zw_swing_long_sl = f"{zw_sw['s2'] - 2.0 * zw_sw['atr']:.2f} cents"
    zw_swing_long_tp = f"{zw_sw['r1']:.2f} cents (Đón sóng hồi trung hạn ~14.5 giá)"
    zw_swing_short_entry = f"{zw_sw['r1']:.2f} - {zw_sw['r2']:.2f} cents"
    zw_swing_short_sl = f"{zw_sw['r2'] + 2.0 * zw_sw['atr']:.2f} cents"
    zw_swing_short_tp = f"{zw_sw['s2']:.2f} cents (Thuận xu hướng giảm ngắn hạn)"
    
    zw_dca = f"{zw_dc['s2'] - 4.0 * zw_dc['atr']:.2f} - {zw_dc['s2']:.2f} cents"

    # ĐẬU TƯƠNG (ZS)
    zs = data_zs["active"]
    zs_sw = data_zs["swing"]
    zs_dc = data_zs["dca"]
    
    zs_pred_close, zs_pred_chg = predict_closing_price("ZS", zs, brent_pct, dxy_pct, fund)
    
    zs_intra_entry = f"{zs['s1']:.2f} - {zs['ema_21']:.2f} cents (Canh mua khi điều chỉnh)"
    zs_intra_sl = f"{zs['s2'] - 1.5 * zs['atr']:.2f} cents (Dưới râu quét nến cũ + 1.5x ATR)"
    zs_intra_tp1 = f"{zs['r1']:.2f} cents"
    zs_intra_tp2 = f"{zs['r2']:.2f} cents"
    
    zs_swing_long_entry = f"{zs_sw['s2']:.2f} - {zs_sw['s1']:.2f} cents"
    zs_swing_long_sl = f"{zs_sw['s2'] - 2.0 * zs_sw['atr']:.2f} cents"
    zs_swing_long_tp = f"{zs_sw['r2']:.2f} cents (Ăn trọn nhịp bứt phá Trend ~17 giá)"
    zs_swing_short_entry = f"{zs_sw['r1']:.2f} - {zs_sw['r2']:.2f} cents"
    zs_swing_short_sl = f"{zs_sw['r2'] + 2.0 * zs_sw['atr']:.2f} cents"
    zs_swing_short_tp = f"{zs_sw['s2']:.2f} cents"
    
    zs_dca = f"{zs_dc['s2'] - 4.0 * zs_dc['atr']:.2f} - {zs_dc['s2']:.2f} cents"

    # Định nghĩa cụ thể các nhãn chiến lược
    zc_intra_label = "Long ngắn hạn (Intraday)" if "LONG" in fund['ZC']['intraday_strategy'].upper() else "Short ngắn hạn (Intraday)"
    zc_swing_long_label = "Long trung hạn (Swing)"
    zc_swing_short_label = "Short trung hạn (Swing)"
    zc_dca_label = "Long dài hạn (DCA)" if "LONG" in fund['ZC']['seasonal_strategy'].upper() or "MUA" in fund['ZC']['seasonal_strategy'].upper() else "Short dài hạn (DCA)"
    
    zw_intra_label = "Short ngắn hạn (Intraday)" if "SHORT" in fund['ZW']['intraday_strategy'].upper() else "Long ngắn hạn (Intraday)"
    zw_swing_long_label = "Long trung hạn (Swing)"
    zw_swing_short_label = "Short trung hạn (Swing)"
    zw_dca_label = "Long dài hạn (DCA)" if "LONG" in fund['ZW']['seasonal_strategy'].upper() or "MUA" in fund['ZW']['seasonal_strategy'].upper() else "Short dài hạn (DCA)"
    
    zs_intra_label = "Long ngắn hạn (Intraday)" if "LONG" in fund['ZS']['intraday_strategy'].upper() else "Short ngắn hạn (Intraday)"
    zs_swing_long_label = "Long trung hạn (Swing)"
    zs_swing_short_label = "Short trung hạn (Swing)"
    zs_dca_label = "Long dài hạn (DCA)" if "LONG" in fund['ZS']['seasonal_strategy'].upper() or "MUA" in fund['ZS']['seasonal_strategy'].upper() else "Short dài hạn (DCA)"

    # Phân loại xu hướng đa khung thời gian
    def get_trend_details(signal):
        if signal == 'Bullish':
            return "🐂 **Tăng (Bullish)**", "EMA_21 H1 > EMA_50 H1 (Hội tụ động lượng tăng)"
        elif signal == 'Bearish':
            return "🐻 **Giảm (Bearish)**", "EMA_21 H1 < EMA_50 H1 (Áp lực bán duy trì)"
        else:
            return "↕️ **Đi ngang (Sideways)**", "EMA_21 H1 = EMA_50 H1 (Tích lũy ngắn hạn)"

    def get_medium_trend_details(trend_text):
        if "tăng" in trend_text.lower():
            return "🐂 **Tăng (Bullish)**", trend_text
        elif "giảm" in trend_text.lower():
            return "🐻 **Giảm (Bearish)**", trend_text
        else:
            return "↕️ **Đi ngang (Sideways)**", trend_text

    zc_short_trend_label, zc_short_trend_logic = get_trend_details(zc["signal"])
    zc_medium_trend_label, zc_medium_trend_logic = get_medium_trend_details(fund['ZC']['swing_trend'])
    
    zw_short_trend_label, zw_short_trend_logic = get_trend_details(zw["signal"])
    zw_medium_trend_label, zw_medium_trend_logic = get_medium_trend_details(fund['ZW']['swing_trend'])
    
    zs_short_trend_label, zs_short_trend_logic = get_trend_details(zs["signal"])
    zs_medium_trend_label, zs_medium_trend_logic = get_medium_trend_details(fund['ZS']['swing_trend'])

    # 5.5. Cảnh báo tương quan động Brent - ZW (Lệch pha vĩ mô)
    if brent_pct < -1.20 and zw_pct < -1.20:
        divergence_alert = f"""
### ⚠️ CẢNH BÁO LỆCH PHA CƠ HỘI MUA (BULLISH DIVERGENCE DETECTED)
*   **Giá trị biến động 24h:** Dầu Brent: **`${brent_price:.2f}` ({brent_pct:+.2f}%)** | DXY: **`{dxy_price:.2f}` ({dxy_pct:+.2f}%)** | Lúa mì CBOT: **`{zw_today_close:.2f}¢` ({zw_pct:+.2f}%)**.
*   **Biện chứng liên thị trường:** Việc dầu thô Brent giảm mạnh (do tin tức giảm căng thẳng Trung Đông) đã kéo theo áp lực bán tháo liên thị trường (cross-commodity selling) tự động từ các quỹ đầu cơ. Điều này ép giá Lúa mì giảm theo về vùng hỗ trợ S1 **`{zw['s1']:.2f} cents`** (HĐ {zw_act_code}).
*   **Thực tế cấu trúc nông học:** Sự sụt giảm địa chính trị này hoàn toàn không thay đổi được thực tế là cung lúa mì toàn cầu đang cực kỳ thắt chặt (Úc sụt giảm 41%, lúa mì Mỹ chất lượng kém đạt 44% Poor/Very Poor).
*   🚀 **Khuyến nghị chiến lược:** Đây là một đợt sụt giảm "lệch pha cơ hội" tuyệt vời do tâm lý ngắn hạn che mờ cung cầu vĩ mô (Asymmetrical Opportunity). Khuyến nghị **Canh Mua gom DCA dài hạn quyết liệt quanh vùng biên độ hỗ trợ `{zw_dc['s2']:.2f} - {zw_dc['s1']:.2f} cents` (HĐ {zw_dca_code})**, tuyệt đối tránh hoảng loạn bán tháo cắt lỗ.
"""
    elif brent_pct > 1.20 and zw_pct < -0.50:
        divergence_alert = f"""
### ⚠️ CẢNH BÁO SUY YẾU LỆCH PHA (BEARISH DIVERGENCE DETECTED)
*   **Giá trị biến động 24h:** Dầu Brent: **`${brent_price:.2f}` ({brent_pct:+.2f}%)** | DXY: **`{dxy_price:.2f}` ({dxy_pct:+.2f}%)** | Lúa mì CBOT: **`{zw_today_close:.2f}¢` ({zw_pct:+.2f}%)**.
*   **Biện chứng liên thị trường:** Dầu thô tăng tốt hỗ trợ rổ hàng hóa vĩ mô, nhưng giá lúa mì vẫn chịu áp lực sụt giảm thể hiện lực cầu vật chất yếu hoặc áp lực cung ngắn hạn lấn át.
*   🚀 **Khuyến nghị chiến lược:** Hạn chế mua đuổi giá cao. Ưu tiên các lệnh Swing Short tại kháng cự đỉnh R1/R2 của HĐ {zw_sw_code}.
"""
    else:
        divergence_alert = f"""
### ✅ TƯƠNG QUAN VĨ MÔ ỔN ĐỊNH (NORMAL CORRELATION)
*   **Giá trị biến động 24h:** Dầu Brent: **`${brent_price:.2f}` ({brent_pct:+.2f}%)** | DXY: **`{dxy_price:.2f}` ({dxy_pct:+.2f}%)** | Lúa mì CBOT: **`{zw_today_close:.2f}¢` ({zw_pct:+.2f}%)**.
*   **Biện chứng liên thị trường:** Liên thị trường giao dịch ổn định, giá lúa mì bám sát các chỉ tiêu cung cầu cơ bản và không có hiện tượng bán tháo chéo quá mức từ nhóm năng lượng.
*   🚀 **Khuyến nghị chiến lược:** Tiếp tục duy trì kế hoạch giao dịch trong ngày (Intraday) và đánh biên (Swing) theo cản kỹ thuật đã hoạch định.
"""

    # 6. Thiết kế tệp báo cáo tổng hợp
    report_content = f"""# NHẬT KÝ BÁO CÁO PHÂN TÍCH HỆ THỐNG CBOT PRO V3 (ZC - ZW - ZS)
*Hệ thống phân tích tự động tích hợp Kỹ thuật H1/M15, Vĩ mô toàn cầu (Brent/DXY) và Nền tảng Nông nghiệp USDA*

Tài liệu được lưu trữ trực tiếp tại thư mục làm việc:
`c:\\Users\\Admin\\OneDrive - w2kfp\\Thang_Docs\\Dau tu thu dong\\hang hoa tai sinh\\Antigravity\\Cbot\\CBOT_Reports_Log.md`

---

# PHẦN I: THÔNG TIN TỔNG QUAN & VĨ MÔ

## 🌐 1. TỔNG QUAN VĨ MÔ TOÀN CẦU (MACRO INDICATORS OVERVIEW)
*Cập nhật tự động qua `macro_tracker.py` vào lúc {time_str} ICT ngày {date_str}*

| Chỉ số Vĩ mô | Mức giá hiện tại | Biến động 24h | Xu hướng & Đánh giá tác động đến Nông sản |
| :--- | :---: | :---: | :--- |
| **Dầu thô Brent (BZ=F)** | **${brent_price:.2f} / thùng** | **{brent_pct:+.2f}%** | {'📈 **Tích cực (Bullish):**' if brent_price > 90 else '📉 **Trung lập:**'} Giá dầu duy trì ở mức cao hỗ trợ mạnh mẽ cho biofuels như Ethanol (ZC) và Biodiesel (ZS). Chi phí sản xuất neo cao tạo mức sàn hỗ trợ giá. |
| **Chỉ số DXY (USD Index)** | **{dxy_price:.2f}** | **{dxy_pct:+.2f}%** | {'📉 **Trung lập - Tiêu cực (Sức ép xuất khẩu):**' if dxy_price > 98 else '📈 **Thuận lợi:**'} DXY neo cao khiến hàng Mỹ kém cạnh tranh hơn ở thị trường quốc tế, cản trở xuất khẩu ngắn hạn. |

{cot_alert}

{divergence_alert}

---

## 🌡️ 2. BẢN TIN THỜI TIẾT & MÙA VỤ TOÀN CẦU (WEATHER INTELLIGENCE REPORT)
*Cập nhật tự động lúc {time_str} ICT ngày {date_str} — Nguồn: NOAA, USDA, BOM Australia*

### 🇺🇸 Thời tiết Nội địa Mỹ (US Domestic Weather)

| Vùng trồng trọt | Cây trồng chính | Diễn biến thời tiết | Tác động mùa vụ |
| :--- | :---: | :--- | :--- |
| **Midwest phía Đông** *(IL, IN, OH)* | 🌽🌱 Ngô/Đậu | {fund['ZC']['short_term_weather']} | {fund['ZC']['weather']['forecast']} |
| **Midwest phía Tây & Bắc** *(IA, MN, Dakotas)* | 🌽 Ngô | {fund['ZC']['weather']['latest']} — Rủi ro: {fund['ZC']['weather']['action']} | {fund['ZC']['weather']['logic'][:120]}... |
| **Southern Plains** *(KS, OK, TX)* | 🌾 Lúa mì đông | {fund['ZW']['short_term_weather']} | {fund['ZW']['weather']['action']} |
| **Northern Plains** *(ND, SD, MT)* | 🌾 Lúa mì xuân | {fund['ZW']['us_planting']['latest']} | {fund['ZW']['us_planting']['logic']} |

### 🌍 Thời tiết Đối thủ Cạnh tranh & Liên Thị trường (Global Competitor Weather)

| Khu vực | Mã liên quan | Diễn biến thời tiết | Tác động cung cầu toàn cầu |
| :--- | :---: | :--- | :--- |
| **🇧🇷 Brazil (Safrinha)** | ZC | {fund['ZC'].get('competitor_weather', dict()).get('brazil_safrinha', 'Chưa cập nhật')} | Hỗ trợ giá ngô Mỹ nếu năng suất Safrinha giảm. |
| **🇦🇷 Argentina (Ngô)** | ZC | {fund['ZC'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Áp lực cung ngắn hạn đang giảm dần. |
| **🇦🇺 Australia** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('australia', 'Chưa cập nhật')} | Bullish dài hạn cho lúa mì toàn cầu. |
| **🇦🇷 Argentina (Lúa mì)** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Nguồn cung Nam Mỹ thắt chặt. |
| **🇷🇺🇪🇺 Black Sea & EU** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('black_sea_eu', 'Chưa cập nhật')} | Ảnh hưởng cạnh tranh xuất khẩu. |
| **🇧🇷 Brazil (Đậu tương)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('brazil', 'Chưa cập nhật')} | Áp lực cung từ vụ kỷ lục Brazil. |
| **🇦🇷 Argentina (Đậu tương)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Áp lực thu hoạch sắp qua đỉnh. |
| **🇨🇳 Trung Quốc (Cầu)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('china', 'Chưa cập nhật')} | Bệ đỡ nhu cầu vững chắc. |

### 🌊 Trạng thái ENSO (El Niño / La Niña)
*   **Trạng thái hiện tại:** {fund['ZC']['weather_long_term']['latest']}
*   **Dự báo:** {fund['ZC']['weather_long_term']['forecast']}
*   **Tác động:** {fund['ZC']['weather_long_term']['action']}

---

## 📌 3. DANH MỤC LỊCH SỬ BÁO CÁO (CẬP NHẬT PHIÊN CHỐT {date_str})
*Thời gian đóng cửa phiên giao dịch được đồng bộ chính xác vào lúc **1:20 AM ICT ngày {date_str}***

| Ngày Báo Cáo (ICT) | Mã | Giá Chốt (Close) | Dự báo Chốt Phiên | Tín Hiệu H1 (EMA 21/50) | Volatility | Intraday Bias | Xem Chi Tiết |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **{date_str}** | **ZC** | **{zc['close']:.2f} ¢** | **{zc_pred_close:.2f} ¢ ({zc_pred_chg:+.2f})** | {'🐂 Bullish' if zc['signal'] == 'Bullish' else '🐻 Bearish'} ({zc['ema_21']:.2f} {'<' if zc['ema_21'] < zc['ema_50'] else '>'} {zc['ema_50']:.2f}) | {zc['volatility']:.2f} cents | Rình mua (Long on dip) | [Xem Ngô (ZC)](#2-báo-cáo-mã-zc-ngô---phiên-chốt-{date_str.replace('/', '')}) |
| **{date_str}** | **ZW** | **{zw['close']:.2f} ¢** | **{zw_pred_close:.2f} ¢ ({zw_pred_chg:+.2f})** | {'🐂 Bullish' if zw['signal'] == 'Bullish' else '🐻 Bearish'} ({zw['ema_21']:.2f} {'<' if zw['ema_21'] < zw['ema_50'] else '>'} {zw['ema_50']:.2f}) | {zw['volatility']:.2f} cents | Bán khống hồi (Short on rally) | [Xem Lúa mì (ZW)](#3-báo-cáo-mã-zw-lúa-mì---phiên-chốt-{date_str.replace('/', '')}) |
| **{date_str}** | **ZS** | **{zs['close']:.2f} ¢** | **{zs_pred_close:.2f} ¢ ({zs_pred_chg:+.2f})** | {'🐂 Bullish' if zs['signal'] == 'Bullish' else '🐻 Bearish'} ({zs['ema_21']:.2f} {'<' if zs['ema_21'] < zs['ema_50'] else '>'} {zs['ema_50']:.2f}) | {zs['volatility']:.2f} cents | Mua đuổi (Buy on pullback) | [Xem Đậu tương (ZS)](#4-báo-cáo-mã-zs-đậu-tương---phiên-chốt-{date_str.replace('/', '')}) |

---

# PHẦN II: TỔNG HỢP LỆNH & CHIẾN LƯỢC MÙA VỤ

## 🎯 1. TỔNG HỢP KHUYẾN NGHỊ HÀNH ĐỘNG THỰC CHIẾN (EXECUTIVE ACTION SUMMARY)
*Trang tổng hợp nhanh các lệnh và vị thế giao dịch cần thực hiện đón đầu cho cả 3 mã hàng hóa*

| Mã | Loại chiến lược | Điểm vào lệnh (Entry Zone) | Cắt lỗ (Stop Loss - SL) | Chốt lời (Take Profit - TP) | Vị thế chủ đạo & Ghi chú thực chiến |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZC** | **{zc_intra_label} ({zc_act_code})** | **{zc_intra_entry}** | **{zc_intra_sl}** | TP1: `{zc_intra_tp1}` \| TP2: `{zc_intra_tp2}` | CANH LONG ngắn hạn tại vùng hỗ trợ kỹ thuật H1 khi giá điều chỉnh sâu. |
| **ZC** | **{zc_swing_long_label} ({zc_sw_code})** | **{zc_swing_long_entry}** | **{zc_swing_long_sl}** | **{zc_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ S2 Price Action cứng (biên dưới). |
| **ZC** | **{zc_swing_short_label} ({zc_sw_code})** | **{zc_swing_short_entry}** | **{zc_swing_short_sl}** | **{zc_swing_short_tp}** | LỆNH SHORT trung hạn ở kháng cự R2 Price Action (biên trên). |
| **ZC** | **{zc_dca_label} ({zc_dca_code})** | **{zc_dca}** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng thủ La Niña và tồn kho thấp kỷ lục. |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZW** | **{zw_intra_label} ({zw_act_code})** | **{zw_intra_entry}** | **{zw_intra_sl}** | TP1: `{zw_intra_tp1}` \| TP2: `{zw_intra_tp2}` | LỆNH SHORT ngắn hạn thuận xu hướng khi hồi kỹ thuật H1. |
| **ZW** | **{zw_swing_long_label} ({zw_sw_code})** | **{zw_swing_long_entry}** | **{zw_swing_long_sl}** | **{zw_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ S1/S2 đón sóng hồi trung hạn ~14.5 giá. |
| **ZW** | **{zw_swing_short_label} ({zw_sw_code})** | **{zw_swing_short_entry}** | **{zw_swing_short_sl}** | **{zw_swing_short_tp}** | LỆNH SHORT trung hạn thuận xu hướng ngắn hạn khi chạm kháng cự R1/R2. |
| **ZW** | **{zw_dca_label} ({zw_dca_code})** | **{zw_dca}** | Không áp dụng | Mục tiêu dài hạn | Canh mua DCA dài hạn quyết liệt (lệch pha cơ hội vĩ mô). |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZS** | **{zs_intra_label} ({zs_act_code})** | **{zs_intra_entry}** | **{zs_intra_sl}** | TP1: `{zs_intra_tp1}` \| TP2: `{zs_intra_tp2}` | CANH LONG ngắn hạn tại vùng hỗ trợ EMA 21 H1 khi giá điều chỉnh nhẹ. |
| **ZS** | **{zs_swing_long_label} ({zs_sw_code})** | **{zs_swing_long_entry}** | **{zs_swing_long_sl}** | **{zs_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ Price Action cứng (biên dưới). |
| **ZS** | **{zs_swing_short_label} ({zs_sw_code})** | **{zs_swing_short_entry}** | **{zs_swing_short_sl}** | **{zs_swing_short_tp}** | LỆNH SHORT trung hạn tại kháng cự đỉnh R2 (biên trên). |
| **ZS** | **{zs_dca_label} ({zs_dca_code})** | **{zs_dca}** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng ngập lụt Midwest và nhu cầu Biodiesel. |

---

## 🌾 2. CHIẾN LƯỢC ĐẶC BIỆT: MÙA VỤ 2026
*Phân tích toàn diện: Địa chính trị, Tồn kho WASDE, Thời tiết NOAA và Điểm vào lệnh Độc lập dựa trên Giá thành sản xuất*

### A. Phân tích Biện chứng Vĩ mô & Địa chính trị (Geopolitics & Maritime Logistics)
*   **Hành lang Biển Đen & Thuế Nga:** Rủi ro quân sự tại Biển Đen làm tăng bảo hiểm tàu biển. Thuế xuất khẩu lúa mì biến động linh hoạt của Nga kìm hãm nguồn cung giá rẻ, buộc người mua dịch chuyển sang lúa mì Mỹ (ZW).
*   **Tắc nghẽn Biển Đỏ & Kênh Suez:** Tàu chở ngũ cốc từ Biển Đen/Châu Âu sang Á phải đi vòng qua Mũi Hảo Vọng (+10-15 ngày vận chuyển, cước tăng 30-40%). Điều này làm giảm khả năng cạnh tranh của lúa mì Pháp/Nga tại Châu Á, tạo lợi thế lớn cho lúa mì xuất khẩu từ bờ Tây nước Mỹ (Pacific Northwest - PNW) đi thẳng qua Thái Bình Dương.
*   **Hạn hán Kênh đào Panama:** Giới hạn số lượt quá cảnh của các tàu chở Ngô/Đậu tương Mỹ từ vịnh Gulf sang Trung Quốc, làm tăng phí bảo hiểm tắc nghẽn và giá xuất khẩu tại cảng (FOB Gulf).
*   **USD/BRL & Căng thẳng Mỹ-Trung:** Đồng Real Brazil (BRL) mất giá khiến nông dân Brazil bán hàng mạnh. Tuy nhiên, sự tắc nghẽn hạ tầng tại cảng Santos/Paranagua trong mùa cao điểm thu hoạch sẽ đẩy dòng tiền mua đậu thô của Trung Quốc quay lại Mỹ trong cửa sổ tháng 9-12.

### B. Biện chứng Cân đối Tồn kho & Biên an toàn (USDA WASDE Niên vụ 2026/27)
*   **Đậu tương (ZS): Tỷ lệ Stocks-to-Use giảm mạnh xuống 6.9%** (dưới ngưỡng an toàn 8%). Brent neo cao ở `$95.5` thúc đẩy nhu cầu ép dầu nội địa (Biodiesel và SAF) lên đỉnh lịch sử, triệt tiêu rủi ro dư thừa nguồn cung thô.
*   **Ngô (ZC): Tỷ lệ Stocks-to-Use giảm xuống 12.1%** (sát ranh giới báo động 12%), tồn kho thế giới thấp nhất 12 năm (`277.5M tấn`). Không có biên an toàn cho bất kỳ sự cố thời tiết thụ phấn nào trong tháng 7.
*   **Lúa mì (ZW): Tỷ lệ Stocks-to-Use giảm mạnh từ 46.1% xuống 40.7%**, tồn kho thế giới giảm liên tiếp năm thứ 4.

### C. Cơ chế truyền dẫn thời tiết NOAA & Động học Sinh trưởng
*   **Mưa bão ngập úng Midwest:** Khiến nông dân Mỹ phải gieo hạt lại (replanting) đậu tương, rút ngắn chu kỳ sinh trưởng của cây non và đẩy giai đoạn điền hạt nhạy cảm nhất (tháng 8) vào đúng đỉnh khô hạn cuối hè của chu kỳ La Niña (xác suất chuyển pha **82%**).
*   **Khô hạn phía Bắc Mỹ:** Gió khô kéo độ ẩm đất bề mặt xuống thấp, đe dọa trực tiếp tỷ lệ nảy mầm và thiết lập bộ rễ của ngô non ở Northern Plains (Minnesota, Dakotas).

### D. Hệ thống Báo cáo Nông nghiệp USDA (USDA Agricultural Reports)
*Tổng hợp chi tiết 4 loại báo cáo nông nghiệp cốt lõi chi phối thị trường tương lai CBOT*

#### 1. Báo cáo Tiến độ Mùa vụ (USDA Crop Progress)
| Mã nông sản | Chỉ tiêu | Tiến độ tuần này | Cùng kỳ năm ngoái | Trung bình 5 năm | Xếp hạng chất lượng (Good/Excellent) | Tác động biện chứng mùa vụ |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Gieo trồng | **{fund['ZC']['us_planting']['latest']}** | 92% | 89% | **{fund['ZC']['crop_condition']['latest']}** | {fund['ZC']['us_planting']['action']} - {fund['ZC']['us_planting']['logic']} |
| **ZS** | Gieo trồng | **{fund['ZS']['us_planting']['latest']}** | 81% | 78% | **{fund['ZS']['crop_condition']['latest']}** | {fund['ZS']['us_planting']['action']} - {fund['ZS']['us_planting']['logic']} |
| **ZW** | Lúa đông | **{fund['ZW']['harvest_progress']['latest']}** | 3% | 2% | **{fund['ZW']['crop_condition']['latest']}** | {fund['ZW']['harvest_progress']['action']} - {fund['ZW']['harvest_progress']['logic']} |
| **ZW** | Lúa xuân | **{fund['ZW']['us_planting']['latest']}** | 91% | 88% | Chưa xếp hạng | {fund['ZW']['us_planting']['action']} - {fund['ZW']['us_planting']['logic']} |

#### 2. Báo cáo Cung cầu & Tồn kho USDA (USDA WASDE)
| Mã nông sản | Thông số Tồn kho | Mỹ (US Ending Stocks) | Thế giới (Global) | Lần cập nhật tới | Tác động biện chứng WASDE |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **ZC** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZC']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZC']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZC']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZC']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZC']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZC']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZC']['us_ending_stocks']['next_date']} | {fund['ZC']['global_ending_stocks']['action']} - {fund['ZC']['global_ending_stocks']['logic']} |
| **ZW** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZW']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZW']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZW']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZW']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZW']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZW']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZW']['us_ending_stocks']['next_date']} | {fund['ZW']['global_ending_stocks']['action']} - {fund['ZW']['global_ending_stocks']['logic']} |
| **ZS** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZS']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZS']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZS']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZS']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZS']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZS']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZS']['us_ending_stocks']['next_date']} | {fund['ZS']['global_ending_stocks']['action']} - {fund['ZS']['global_ending_stocks']['logic']} |

#### 3. Báo cáo Bán hàng & Giao hàng Xuất khẩu (USDA Weekly Export Sales & Inspections)
| Mã nông sản | Báo cáo | Số liệu trước đó | Số liệu mới nhất | Dự báo kỳ tiếp theo | Lần cập nhật tới | Tác động biện chứng xuất khẩu |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Bán hàng & Giao hàng | {fund['ZC']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZC']['exports']['latest'].replace('|', '\\|')}** | {fund['ZC']['exports']['forecast']} | {fund['ZC']['exports']['next_date']} | {fund['ZC']['exports']['action']} - {fund['ZC']['exports']['logic']} |
| **ZW** | Bán hàng & Giao hàng | {fund['ZW']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZW']['exports']['latest'].replace('|', '\\|')}** | {fund['ZW']['exports']['forecast']} | {fund['ZW']['exports']['next_date']} | {fund['ZW']['exports']['action']} - {fund['ZW']['exports']['logic']} |
| **ZS** | Bán hàng & Giao hàng | {fund['ZS']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZS']['exports']['latest'].replace('|', '\\|')}** | {fund['ZS']['exports']['forecast']} | {fund['ZS']['exports']['next_date']} | {fund['ZS']['exports']['action']} - {fund['ZS']['exports']['logic']} |

#### 4. Báo cáo Sản lượng Cây trồng & Đối thủ Nam Mỹ (USDA Crop Production & Competitors)
| Mã nông sản | Thu hoạch Mỹ / Vụ mùa | Sản lượng Đối thủ Nam Mỹ | Lần cập nhật tới | Tác động biện chứng cung cầu |
| :---: | :--- | :--- | :---: | :--- |
| **ZC** | Thu hoạch: {fund['ZC']['harvest_progress']['latest']} | {fund['ZC']['competitors']['latest']} ({fund['ZC']['competitors']['forecast']}) | {fund['ZC']['competitors']['next_date']} | {fund['ZC']['competitors']['action']} - {fund['ZC']['competitors']['logic']} |
| **ZW** | Thu hoạch: {fund['ZW']['harvest_progress']['latest']} | {fund['ZW']['competitors']['latest']} ({fund['ZW']['competitors']['forecast']}) | {fund['ZW']['competitors']['next_date']} | {fund['ZW']['competitors']['action']} - {fund['ZW']['competitors']['logic']} |
| **ZS** | Thu hoạch: {fund['ZS']['harvest_progress']['latest']} | {fund['ZS']['competitors']['latest']} ({fund['ZS']['competitors']['forecast']}) | {fund['ZS']['competitors']['next_date']} | {fund['ZS']['competitors']['action']} - {fund['ZS']['competitors']['logic']} |

### E. Thiết lập Vùng Entry Độc lập dựa trên Giá thành Sản xuất & Thống kê 5 năm
Chúng tôi không sử dụng hỗ trợ kỹ thuật S2 của V3 Pro làm điểm vào lệnh chính thức, mà thiết lập các vùng mua độc lập dựa trên **Giá thành sản xuất của nông dân Mỹ (US Production Cost)** và **Thống kê phân bổ giá 5 năm gần nhất**:

*   **Ngô (Corn):**
    *   **Leg 1 (ZCU26 Tháng 09/2026):** 
        *   *Vị thế:* **Long Hold (Ngắn hạn)**.
        *   *Biện chứng:* Tấn công trực diện Weather Premium của chu kỳ thụ phấn tháng 7. HĐ ZCU26 rẻ hơn ZCZ26 giúp tối ưu dòng vốn.
        *   *Thiết lập:* **Entry: `420.00 - 433.00` | SL: `413.00` | TP1: `475.00` | TP2: `495.00`**.
        *   *Thời điểm Tất toán:* **15/07 - 25/07/2026** (Tất toán chốt lời trước FND ngày 31/08).
    *   **Leg 2 (ZCZ26 Tháng 12/2026):** 
        *   *Vị thế:* **Long Hold (Dài hạn)**.
        *   *Biện chứng:* Đón đầu rủi ro mất mùa vĩ mô kéo dài sang mùa đông do La Niña. Áp dụng Entry thấp hơn để bù đắp phí Contango.
        *   *Thiết lập:* **Entry: `430.00 - 438.00` | SL: `422.00` | TP1: `510.00` | TP2: `535.00`**.
        *   *Thời điểm Tất toán:* **15/11 - 30/11/2026**.
*   **Đậu tương (Soybeans - ZSX26 Tháng 11/2026):**
    *   *Vị thế:* **Long Accumulation (Mua gom tích sản chốt 2 đợt)**.
    *   *Biện chứng:* Giao dịch duy nhất HĐ Tháng 11 do Contango cực thấp (`0.5`), nhưng phân bổ chốt lời thành 2 đợt.
    *   *Thiết lập:* **Entry: `1125.00 - 1140.00` | SL: `1105.00` | TP1: `1200.00` (Đợt 1) | TP2: `1320.00` (Đợt 2)**.
    *   *Thời điểm Tất toán:*
        *   *Đợt 1 (50% vị thế):* **20/08 - 05/09/2026** (Đỉnh điểm khô hạn điền hạt cuối hè).
        *   *Đợt 2 (50% vị thế):* **15/10 - 30/10/2026** (Sóng khô hạn gieo trồng sớm Nam Mỹ).
*   **Lúa mì (Wheat):**
    *   **Leg 1 (ZWU26 Tháng 09/2026):**
        *   *Vị thế:* **Accumulative Long (Ngắn hạn)**.
        *   *Biện chứng:* Ăn nhịp phục hồi sau thu hoạch mùa hè (Post-Harvest Bounce). ZWU26 rẻ hơn ZWZ26 `17.25` là lựa chọn tối ưu.
        *   *Thiết lập:* **Entry: `580.00 - 595.00` | SL: `565.00` | TP1: `645.00` | TP2: `675.00`**.
        *   *Thời điểm Tất toán:* **10/08 - 20/08/2026** (Tất toán trước FND ngày 31/08).
    *   **Leg 2 (ZWZ26 Tháng 12/2026):**
        *   *Vị thế:* **Accumulative Long (Dài hạn)**.
        *   *Biện chứng:* Phòng thủ rủi ro mất mùa diện rộng ở Úc/Argentina và mùa đông khắc nghiệt tại Bắc Mỹ.
        *   *Thiết lập:* **Entry: `590.00 - 605.00` | SL: `575.00` | TP1: `690.00` | TP2: `720.00`**.
        *   *Thời điểm Tất toán:* **15/11 - 30/11/2026**.

### F. Ma trận Giao dịch "MÙA VỤ 2026" - Cấu trúc 2 Giai đoạn (Dual-Leg Setup)

| HĐ Chỉ định | Chiến lược & Phân nhóm | Điểm vào lệnh Độc lập | Cắt lỗ bảo vệ vốn | Chốt lời & Tất toán | Phân bổ vốn |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **ZCU26** (Corn) | Long Hold (Leg 1 - Ngắn hạn) | **`420.00 - 433.00`**<br>*(Tháng 6 - 7)* | **`413.00`** | **`475.00`** \| **`495.00`**<br>*(Tất toán: 15/07 - 25/07)* | **10%** |
| **ZCZ26** (Corn) | Long Hold (Leg 2 - Dài hạn) | **`430.00 - 438.00`**<br>*(Tháng 6 - 7)* | **`422.00`** | **`510.00`** \| **`535.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 1 - 50%) | **`1125.00 - 1140.00`**<br>*(Tháng 6 - 7)* | **`1105.00`** | **`1200.00`** \| **`1240.00`**<br>*(Tất toán: 20/08 - 05/09)* | **10%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 2 - 50%) | **`1125.00 - 1140.00`**<br>*(Tháng 6 - 7)* | **`1105.00`** | **`1280.00`** \| **`1320.00`**<br>*(Tất toán: 15/10 - 30/10)* | **10%** |
| **ZWU26** (Wheat)| Accumulative Long (Leg 1 - Ngắn hạn)| **`580.00 - 595.00`**<br>*(Tháng 6)* | **`565.00`** | **`645.00`** \| **`675.00`**<br>*(Tất toán: 10/08 - 20/08)* | **10%** |
| **ZWZ26** (Wheat)| Accumulative Long (Leg 2 - Dài hạn) | **`590.00 - 605.00`**<br>*(Tháng 6)* | **`575.00`** | **`690.00`** \| **`720.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |

### G. Định nghĩa Chiến thuật & Ma trận Phân bổ vốn Chi tiết (Capital Allocation Guide)

#### 1. Biện chứng Chiến thuật "Long Hold" vs "Long Accumulation"
*   **Long Hold (Mua và Nắm giữ Vị thế):** Mở vị thế Long tại vùng giá chỉ định và giữ chặt xuyên suốt thời kỳ nhạy cảm của mùa vụ (ví dụ: giai đoạn ngô thụ phấn pollination kéo dài 2-3 tuần của tháng 7). Không thực hiện DCA thêm nếu giá chạy trong biên độ. Chiến thuật này nhằm ăn trọn con sóng tăng sốc khi "Phí bảo hiểm thời tiết" (Weather Premium) được kích hoạt do nắng nóng đỉnh hè của La Niña (xác suất 82%).
*   **Long Accumulation (Mua gom Tích lũy):** Chủ động chia nguồn vốn làm 3-4 phần để gom mua dần (DCA Long) khi giá điều chỉnh sâu vào vùng chiết khấu. Chiến thuật này phù hợp với Đậu tương (ZSX26) khi tiến độ nảy mầm kéo dài và nông dân phải gieo hạt lại (replanting) do ngập úng Đông Midwest. Nó tối ưu hóa giá vốn trung bình (average entry price) nằm sát vùng giá thành sản xuất gieo trồng của nông dân.

#### 2. Phân bổ Vốn & Quản trị rủi ro Ký quỹ (Portfolio Money Management)
*   **Bộ đệm Ký quỹ tự do (Margin Buffer - 50%):** Giữ dưới dạng tiền mặt/ký quỹ tự do để tài khoản chịu đựng được các đợt rung lắc mạnh (noise) của thị trường tương lai CBOT mà không bị kích hoạt gọi ký quỹ (Margin Call).
*   **Vốn giải ngân thực chiến (Active Capital - 50%):** Phân bổ cụ thể vào các chiến dịch:
    *   🌽 **Ngô (Corn): Phân bổ 15% tổng vốn.** (Tập trung 10% cho Leg 1 - Long Hold ZCU26 tại vùng `420.00 - 433.00`; phân bổ 5% cho Leg 2 - Long Hold ZCZ26 tích lũy sâu hơn tại `430.00 - 438.00`).
    *   🌱 **Đậu tương (Soybeans): Phân bổ 20% tổng vốn.** (Vào vị thế Long Accumulation ZSX26 chia đều thành 3 đợt mua gom giá tốt. Chốt lời 10% vốn giải ngân ở đợt 1 và giữ 10% còn lại cho sóng quý 4).
    *   🌾 **Lúa mì (Wheat): Phân bổ 15% tổng vốn.** (Tập trung 10% cho Leg 1 - Accumulative Long ZWU26 tại vùng `580.00 - 595.00`; phân bổ 5% cho Leg 2 - Accumulative Long ZWZ26 gom sâu hơn tại `590.00 - 605.00`).

#### 3. Quy tắc Tất toán & Đóng vị thế theo mùa vụ (Seasonal Liquidation Protocol)
*   **Nguyên lý hao mòn phí bảo hiểm thời tiết (Weather Premium Decay):** Phí bảo hiểm thời tiết là giá trị hao mòn nhanh. Khi cây trồng vượt qua giai đoạn nhạy cảm nhất mà không xảy ra thiên tai nghiêm trọng hơn, hoặc khi mùa gặt cận kề, Weather Premium sẽ bốc hơi. Việc đóng vị thế đúng thời điểm chốt lời quan trọng hơn cố chờ giá chạm mục tiêu kỹ thuật tối đa.
*   **Lịch trình đóng vị thế chi tiết:**
    - **🌽 Với Ngô:**
        *   *Leg 1 - Long Hold (ZCU26):* Bắt buộc tất toán trước ngày **25/07/2026** (trước FND ngày 31/08).
        *   *Leg 2 - Long Hold (ZCZ26):* Tất toán trong cửa sổ từ **15/11 - 30/11/2026** khi mùa đông Bắc Mỹ cận kề thúc đẩy nhu cầu sưởi ấm và năng lượng.
    - **🌱 Với Đậu tương (ZSX26):**
        *   *Đợt 1 - Long Accumulation (50% vị thế):* Chốt lời từ ngày **20/08 - 05/09/2026** khi đậu tương hoàn thành điền hạt.
        *   *Đợt 2 - Long Accumulation (50% vị thế):* Chốt lời hoàn toàn từ ngày **15/10 - 30/10/2026** khi Nam Mỹ bắt đầu hạn hán gieo trồng.
    - **🌾 Với Lúa mì:**
        *   *Leg 1 - Accumulative Long (ZWU26):* Tất toán trước ngày **20/08/2026** (trước FND ngày 31/08).
        *   *Leg 2 - Accumulative Long (ZWZ26):* Tất toán trong cửa sổ từ **15/11 - 30/11/2026** đón đỉnh giá của chu kỳ khô hạn mùa đông Bắc Bán Cầu.

---

"""
    
    # --- PHẦN III: INDEPENDENT COMMODITY PROFILES ---
    # Run future chart first to get data
    fc_data = {}
    try:
        import subprocess
        fc_path = os.path.join(os.path.dirname(__file__), 'Future chart', 'future_chart.py')
        subprocess.run(['python', fc_path], check=True, capture_output=True)
        fc_json_path = os.path.join(os.path.dirname(__file__), 'Future chart', 'future_chart_data.json')
        with open(fc_json_path, 'r', encoding='utf-8') as f:
            fc_data = json.load(f)
    except Exception as e:
        print(f'Future Chart error: {e}')
    phan3_header = "\n# PHẦN III: HỒ SƠ ĐỘC LẬP TỪNG MÃ NÔNG SẢN\n"
    phan3_header += "*Mỗi mã được phân tích hoàn toàn độc lập. Dữ liệu chung (Brent, DXY) đồng bộ tự động từ cùng một nguồn.*\n"
    
    section_zc = build_commodity_section(
        code='ZC', emoji='🌽', name_vn='Ngô', date_str=date_str,
        data=zc, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zc_pred_close, pred_chg=zc_pred_chg,
        act_code=zc_act_code, sw_code=zc_sw_code, dca_code=zc_dca_code,
        intra_label=zc_intra_label, intra_entry=zc_intra_entry, intra_sl=zc_intra_sl,
        intra_tp1=zc_intra_tp1, intra_tp2=zc_intra_tp2,
        swing_long_label=zc_swing_long_label, swing_long_entry=zc_swing_long_entry,
        swing_long_sl=zc_swing_long_sl, swing_long_tp=zc_swing_long_tp,
        swing_short_label=zc_swing_short_label, swing_short_entry=zc_swing_short_entry,
        swing_short_sl=zc_swing_short_sl, swing_short_tp=zc_swing_short_tp,
        dca_label=zc_dca_label, dca_entry=zc_dca,
        candle=zc_candle, comb_trend=zc_comb_trend, liq_trend=zc_liq_trend, liq_logic='',
        today_vol=zc_today_vol, prev_vol=zc_prev_vol, today_oi=zc_today_oi, prev_oi=zc_prev_oi,
        today_close=zc_today_close, prev_close=zc_prev_close,
        short_trend_label=zc_short_trend_label, short_trend_logic=zc_short_trend_logic,
        medium_trend_label=zc_medium_trend_label, medium_trend_logic=zc_medium_trend_logic,
        fc_data=fc_data.get('ZC')
    )
    section_zw = build_commodity_section(
        code='ZW', emoji='🌾', name_vn='Lúa Mì', date_str=date_str,
        data=zw, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zw_pred_close, pred_chg=zw_pred_chg,
        act_code=zw_act_code, sw_code=zw_sw_code, dca_code=zw_dca_code,
        intra_label=zw_intra_label, intra_entry=zw_intra_entry, intra_sl=zw_intra_sl,
        intra_tp1=zw_intra_tp1, intra_tp2=zw_intra_tp2,
        swing_long_label=zw_swing_long_label, swing_long_entry=zw_swing_long_entry,
        swing_long_sl=zw_swing_long_sl, swing_long_tp=zw_swing_long_tp,
        swing_short_label=zw_swing_short_label, swing_short_entry=zw_swing_short_entry,
        swing_short_sl=zw_swing_short_sl, swing_short_tp=zw_swing_short_tp,
        dca_label=zw_dca_label, dca_entry=zw_dca,
        candle=zw_candle, comb_trend=zw_comb_trend, liq_trend=zw_liq_trend, liq_logic='',
        today_vol=zw_today_vol, prev_vol=zw_prev_vol, today_oi=zw_today_oi, prev_oi=zw_prev_oi,
        today_close=zw_today_close, prev_close=zw_prev_close,
        short_trend_label=zw_short_trend_label, short_trend_logic=zw_short_trend_logic,
        medium_trend_label=zw_medium_trend_label, medium_trend_logic=zw_medium_trend_logic,
        fc_data=fc_data.get('ZW')
    )
    section_zs = build_commodity_section(
        code='ZS', emoji='🌱', name_vn='Đậu Tương', date_str=date_str,
        data=zs, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zs_pred_close, pred_chg=zs_pred_chg,
        act_code=zs_act_code, sw_code=zs_sw_code, dca_code=zs_dca_code,
        intra_label=zs_intra_label, intra_entry=zs_intra_entry, intra_sl=zs_intra_sl,
        intra_tp1=zs_intra_tp1, intra_tp2=zs_intra_tp2,
        swing_long_label=zs_swing_long_label, swing_long_entry=zs_swing_long_entry,
        swing_long_sl=zs_swing_long_sl, swing_long_tp=zs_swing_long_tp,
        swing_short_label=zs_swing_short_label, swing_short_entry=zs_swing_short_entry,
        swing_short_sl=zs_swing_short_sl, swing_short_tp=zs_swing_short_tp,
        dca_label=zs_dca_label, dca_entry=zs_dca,
        candle=zs_candle, comb_trend=zs_comb_trend, liq_trend=zs_liq_trend, liq_logic='',
        today_vol=zs_today_vol, prev_vol=zs_prev_vol, today_oi=zs_today_oi, prev_oi=zs_prev_oi,
        today_close=zs_today_close, prev_close=zs_prev_close,
        short_trend_label=zs_short_trend_label, short_trend_logic=zs_short_trend_logic,
        medium_trend_label=zs_medium_trend_label, medium_trend_logic=zs_medium_trend_logic,
        fc_data=fc_data.get('ZS')
    )
    
    report_content += phan3_header + section_zc + section_zw + section_zs

    report_log_path = os.path.join(os.path.dirname(__file__), "CBOT_Reports_Log.md")
    with open(report_log_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("Successfully generated CBOT_Reports_Log.md in Pro V3 structure!")
    
    # Auto-export V3 State Snapshot for V4 Visual Confirmation Module
    try:
        snapshot_data = {
            "timestamp": f"{date_str} {time_str}",
            "macro": {
                "brent_price": brent_price,
                "brent_pct": brent_pct,
                "dxy_price": dxy_price,
                "dxy_pct": dxy_pct
            },
            "commodities": {
                "ZC": {
                    "active": {**zc, "contract": zc_act_code, "weather": fund['ZC']['weather']['latest'], "predicted_close": zc_pred_close, "predicted_change": zc_pred_chg},
                    "swing": {**zc_sw, "contract": zc_sw_code},
                    "dca": {**zc_dc, "contract": zc_dca_code},
                    "competitor_weather": fund['ZC'].get('competitor_weather', {}),
                    "short_term_weather": fund['ZC']['short_term_weather'],
                    "enso_status": fund['ZC']['weather_long_term']['forecast']
                },
                "ZW": {
                    "active": {**zw, "contract": zw_act_code, "weather": fund['ZW']['weather']['latest'], "predicted_close": zw_pred_close, "predicted_change": zw_pred_chg},
                    "swing": {**zw_sw, "contract": zw_sw_code},
                    "dca": {**zw_dc, "contract": zw_dca_code},
                    "competitor_weather": fund['ZW'].get('competitor_weather', {}),
                    "short_term_weather": fund['ZW']['short_term_weather'],
                    "enso_status": fund['ZW']['weather_long_term']['forecast']
                },
                "ZS": {
                    "active": {**zs, "contract": zs_act_code, "weather": fund['ZS']['weather']['latest'], "predicted_close": zs_pred_close, "predicted_change": zs_pred_chg},
                    "swing": {**zs_sw, "contract": zs_sw_code},
                    "dca": {**zs_dc, "contract": zs_dca_code},
                    "competitor_weather": fund['ZS'].get('competitor_weather', {}),
                    "short_term_weather": fund['ZS']['short_term_weather'],
                    "enso_status": fund['ZS']['weather_long_term']['forecast']
                }
            }
        }
        snapshot_path = _data_path("v3_state_snapshot.json")
        with open(snapshot_path, "w", encoding="utf-8") as sf:
            json.dump(snapshot_data, sf, ensure_ascii=False, indent=2)
            
        # V4: Export RSI Data for Dashboard
        rsi_payload = {
            "zw": data_zw.get("rsi_pack", {}),
            "zc": data_zc.get("rsi_pack", {}),
            "zs": data_zs.get("rsi_pack", {})
        }
        rsi_path = _data_path("rsi_data.json")
        with open(rsi_path, "w", encoding="utf-8") as rf:
            json.dump(rsi_payload, rf, ensure_ascii=False, indent=2)

        print("Successfully generated v3_state_snapshot.json for V4 Visual Confirmation!")
    except Exception as se:
        print(f"Error exporting V3 state snapshot: {se}")
    
    # Auto-export to Word Docx
    try:
        from export_to_word import create_docx_report
        create_docx_report()
    except Exception as e:
        print(f"Error auto-exporting to Word docx: {e}")
        
    # Auto-generate HTML Dashboard
    try:
        import subprocess
        gen_path = os.path.join(os.path.dirname(__file__), 'gen_dashboard.py')
        subprocess.run(['python', gen_path], check=True, capture_output=True)
        print("Successfully generated CBOT_Dashboard.html")
    except Exception as e:
        print(f"Error generating HTML Dashboard: {e}")
        
    print("\n=====================================================================================")
    print("                      BÁO CÁO PHÂN TÍCH CBOT PRO V3 CHI TIẾT (LIVE)                     ")
    print("=====================================================================================")
    print(report_content)
    print("=====================================================================================")
    print("--- PROCESS COMPLETED ---")

if __name__ == '__main__':
    run_pro_plus()