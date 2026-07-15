import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

import datetime
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from data_config import OUTPUT_DIR, get_csv_str
from fetch_prices import get_active_contract

def _fetch_from_tradingview_h4(ticker_symbol: str) -> pd.DataFrame:
    """
    Fetch 30 days of H4 data from TradingView.
    30 days * ~5 H4 bars/day = ~150 bars. Fetch 200 to be safe.
    """
    try:
        from tvDatafeed import TvDatafeed, Interval
        tv = TvDatafeed()
        # Chuyển ZCZ26.CBT -> ZCZ2026
        base = ticker_symbol.split('.')[0]
        sym = base[:-2]
        yr = base[-2:]
        tv_sym = f"{sym}20{yr}"
        
        import time
        # Retry up to 3 times
        for attempt in range(3):
            try:
                # Lấy số lượng nến tương đương 30 ngày
                df = tv.get_hist(symbol=tv_sym, exchange='CBOT', interval=Interval.in_4_hour, n_bars=200)
                
                if df is not None and not df.empty:
                    df = df.reset_index()
                    # TV datetime index là giờ VN (naive)
                    # Lọc lấy 30 ngày gần nhất
                    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    df = df[df['datetime'] >= thirty_days_ago]
                    
                    # Format time: YYYY-MM-DD HH:MM
                    df["Time"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M")
                    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
                    df["OpenInterest"] = 0
                    
                    # Giải thích giờ mở cửa/đóng cửa CBOT (Giờ VN - Mùa Hè DST):
                    # Mở cửa phiên tối: 07:00
                    # Nghỉ giữa phiên: 19:45 - 20:30
                    # Mở cửa phiên ngày: 20:30
                    # Đóng cửa: 01:20 sáng hôm sau
                    # TradingView H4 tự động chia nến: 07:00, 11:00, 15:00, 19:00, 23:00.
                    return df[["Time", "Open", "High", "Low", "Close", "Volume", "OpenInterest"]]
            except Exception as e:
                print(f"Lỗi TradingView API H4 (lần {attempt+1}): {e}")
            time.sleep(1)
            
    except ImportError:
        print("⚠️ tvDatafeed chưa được cài đặt.")
    except Exception as e:
        print(f"Lỗi TradingView API H4 tổng: {e}")
        
    return pd.DataFrame()

def run_fetch_h4():
    current_date = datetime.datetime.now()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for code in ["ZC", "ZW"]:
        print(f"\n--- Đang xử lý lấy H4 cho {code} ---")
        active_info = get_active_contract(code, current_date)
        if not active_info:
            print(f"Không tìm thấy HĐ active cho {code}")
            continue
            
        ticker_symbol = active_info[0]
        print(f"Hợp đồng Active: {ticker_symbol}")
        
        df_h4 = _fetch_from_tradingview_h4(ticker_symbol)
        
        if not df_h4.empty:
            # File name pattern: ZC_active_H4.csv
            csv_name = f"{code}_active_H4.csv"
            csv_path = os.path.join(OUTPUT_DIR, csv_name)
            df_h4.to_csv(csv_path, index=False)
            print(f"✅ Đã lưu {len(df_h4)} nến H4 vào {csv_path}")
            print("Mẫu dữ liệu mới nhất (Giờ VN):")
            print(df_h4.tail())
        else:
            print(f"❌ Không lấy được dữ liệu H4 cho {ticker_symbol}")

if __name__ == "__main__":
    run_fetch_h4()
