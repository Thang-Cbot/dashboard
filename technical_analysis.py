import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period-1, adjust=False).mean()
    avg_loss = loss.ewm(com=period-1, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.ewm(span=period, adjust=False).mean()

def analyze_cbot_data(csv_file_path):
    """
    Hàm này đọc dữ liệu giá (H1, M15), tính EMA, Volatility, RSI, ATR,
    và tự động xác định các vùng Hỗ trợ/Kháng cự Price Action (S1, S2, R1, R2).
    """
    try:
        # 1. Đọc dữ liệu từ file CSV
        df = pd.read_csv(csv_file_path)
        if df.empty:
            print(f"File CSV rỗng: {csv_file_path}")
            return False
            
        # 2. Tính toán EMA 21 và EMA 50
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # 3. Tính toán Độ biến động (Volatility) của từng nến
        df['Volatility'] = df['High'] - df['Low']
        
        # 4. Xác định tín hiệu giao cắt H1 (EMA Cross Signal)
        df['Signal'] = 'Neutral'
        df.loc[df['EMA_21'] > df['EMA_50'], 'Signal'] = 'Bullish'
        df.loc[df['EMA_21'] < df['EMA_50'], 'Signal'] = 'Bearish'
        
        # 5. Tính toán chỉ báo dao động RSI (14) và ATR (14)
        df['RSI'] = calculate_rsi(df['Close'], period=14)
        df['ATR'] = calculate_atr(df, period=14)
        
        # Điền các ô NaN đầu tiên của RSI/ATR bằng giá trị mặc định để tránh lỗi
        df['RSI'] = df['RSI'].ffill().bfill().fillna(50.0)
        df['ATR'] = df['ATR'].ffill().bfill().fillna(df['Volatility'].mean())
        
        # 6. Thuật toán Price Action để tìm các đỉnh/đáy cục bộ (Swing Highs/Lows)
        highs = df['High'].values
        lows = df['Low'].values
        
        peaks = []
        troughs = []
        
        # Quét qua nến với cửa sổ rolling để tìm cản thực tế (Price Action Swings)
        # Sử dụng window 3 nến trước và 3 nến sau để tìm cản H1 cứng hơn
        w = 3
        for k in range(w, len(df) - w):
            # Điều kiện đỉnh (Peak / Swing High)
            if all(highs[k] >= highs[k-j] for j in range(1, w+1)) and all(highs[k] >= highs[k+j] for j in range(1, w+1)):
                peaks.append(highs[k])
            # Điều kiện đáy (Trough / Swing Low)
            if all(lows[k] <= lows[k-j] for j in range(1, w+1)) and all(lows[k] <= lows[k+j] for j in range(1, w+1)):
                troughs.append(lows[k])
                
        # Loại bỏ các đỉnh/đáy trùng nhau để gom cụm và sắp xếp
        peaks = sorted(list(set(peaks)))
        troughs = sorted(list(set(troughs)))
        
        current_close = float(df['Close'].iloc[-1])
        latest_atr = float(df['ATR'].iloc[-1])
        
        # Xác định R2 (Kháng cự cực đại) và S2 (Hỗ trợ cực tiểu)
        R2 = float(df['High'].max())
        S2 = float(df['Low'].min())
        
        # Đảm bảo R1 và S1 không nằm quá sát giá hiện tại (lọc bỏ nhiễu ngắn hạn)
        min_dist = 0.5 * latest_atr
        
        # Xác định R1 (Kháng cự gần) - là đỉnh gần nhất phía trên giá Close hiện tại + min_dist
        valid_peaks = [p for p in peaks if p > current_close + min_dist]
        if valid_peaks:
            R1 = float(min(valid_peaks))
        else:
            R1 = float(current_close + 1.5 * latest_atr)
            
        # Xác định S1 (Hỗ trợ gần) - là đáy gần nhất phía dưới giá Close hiện tại - min_dist
        valid_troughs = [t for t in troughs if t < current_close - min_dist]
        if valid_troughs:
            S1 = float(max(valid_troughs))
        else:
            S1 = float(current_close - 1.5 * latest_atr)
            
        # Đảm bảo logic giá tăng dần và khoảng cách hợp lý: S2 < S1 < R1 < R2
        if S1 <= S2:
            S1 = S2 + 0.5 * latest_atr
        if R1 >= R2:
            R1 = R2 - 0.5 * latest_atr
            
        if S1 >= R1:
            S1 = current_close - 0.75 * latest_atr
            R1 = current_close + 0.75 * latest_atr
            
        if S2 >= S1:
            S2 = S1 - 1.0 * latest_atr
        if R2 <= R1:
            R2 = R1 + 1.0 * latest_atr
        
        # Gán mức cản cho toàn bộ các dòng cuối để lưu trữ
        df['S1'] = S1
        df['S2'] = S2
        df['R1'] = R1
        df['R2'] = R2
        
        # Lưu đè file với tất cả các cột chỉ báo Pro V2 mới
        df.to_csv(csv_file_path, index=False)
        print(f"Đã phân tích xong Pro V2 (EMA, Volatility, RSI, ATR, S1/S2, R1/R2) cho file: {csv_file_path}")
        return True
        
    except Exception as e:
        print(f"Lỗi khi tính toán chỉ báo Pro V2: {e}")
        return False

def detect_candlestick_pattern(df):
    """
    Phát hiện mô hình nến trên khung thời gian H1 dựa vào 2 nến cuối cùng.
    """
    try:
        if len(df) < 2:
            return "Không đủ dữ liệu nến"
        
        # Nến hiện tại (curr) và nến trước đó (prev)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        o_c, h_c, l_c, c_c = float(curr['Open']), float(curr['High']), float(curr['Low']), float(curr['Close'])
        o_p, h_p, l_p, c_p = float(prev['Open']), float(prev['High']), float(prev['Low']), float(prev['Close'])
        
        body_c = abs(c_c - o_c)
        range_c = h_c - l_c if (h_c - l_c) > 0 else 1e-6
        upper_wick_c = h_c - max(o_c, c_c)
        lower_wick_c = min(o_c, c_c) - l_c
        
        body_p = abs(c_p - o_p)
        
        # 1. Bullish Engulfing
        if c_p < o_p and c_c > o_c and c_c >= o_p and o_c <= c_p and body_c > body_p:
            return "Bullish Engulfing (Nhấn chìm tăng trưởng)"
        
        # 2. Bearish Engulfing
        if c_p > o_p and c_c < o_c and c_c <= o_p and o_c >= c_p and body_c > body_p:
            return "Bearish Engulfing (Nhấn chìm giảm thiểu)"
            
        # 3. Hammer (Búa) / Bullish Pinbar
        if lower_wick_c > 2.0 * body_c and upper_wick_c < 0.5 * body_c:
            return "Hammer / Bullish Pinbar (Nến búa đảo chiều tăng)"
            
        # 4. Shooting Star / Inverted Hammer / Bearish Pinbar
        if upper_wick_c > 2.0 * body_c and lower_wick_c < 0.5 * body_c:
            return "Shooting Star / Bearish Pinbar (Nến búa ngược đảo chiều giảm)"
            
        # 5. Doji
        if body_c < 0.1 * range_c:
            return "Doji (Nến lưỡng lự thế trận)"
            
        # 6. Marubozu
        if body_c > 0.9 * range_c:
            if c_c > o_c:
                return "Bullish Marubozu (Lực mua áp đảo tuyệt đối)"
            else:
                return "Bearish Marubozu (Lực bán áp đảo tuyệt đối)"
                
        return "Không phát hiện mô hình nến đặc biệt"
    except Exception as e:
        return f"Lỗi phân tích nến: {e}"

def analyze_liquidity_trend(price_chg, vol_chg, oi_chg):
    """
    Phân tích xu hướng dựa trên sự kết hợp giữa thay đổi Giá, Volume và Vị thế mở (OI).
    """
    price_up = price_chg > 0
    vol_up = vol_chg > 0
    oi_up = oi_chg > 0
    
    if price_up and vol_up and oi_up:
        trend = "Tăng mạnh mẽ (Strong Bullish / Long Buildup)"
        logic = "Giá tăng đi kèm Volume và Vị thế mở (OI) đều tăng. Phe Mua mới đang ồ ạt gia nhập thị trường, tạo động lực tăng vững chắc và có tính bền vững cao."
    elif price_up and not vol_up and not oi_up:
        trend = "Tăng yếu / Rủi ro đảo chiều (Short Covering Rally)"
        logic = "Giá tăng nhưng Volume giảm và OI giảm. Nhịp tăng này chủ yếu do phe Short đóng vị thế cắt lỗ (Short Covering) chứ không có dòng tiền mới mua lên hỗ trợ. Rủi ro đảo chiều giảm trở lại khi phe Short dừng tháo chạy."
    elif not price_up and vol_up and oi_up:
        trend = "Giảm mạnh mẽ (Strong Bearish / Short Buildup)"
        logic = "Giá giảm đi kèm Volume tăng và OI tăng. Phe Bán khống mới đang ồ ạt gia nhập thị trường, củng cố xu hướng giảm tiếp diễn."
    elif not price_up and not vol_up and not oi_up:
        trend = "Giảm suy yếu / Đáy ngắn hạn (Long Liquidation Decline)"
        logic = "Giá giảm cùng với Volume giảm và OI giảm. Nhịp giảm chủ yếu do phe Long tháo chạy cắt lỗ giải chấp vị thế (Long Liquidation) chứ không có lực bán khống mới. Áp lực giảm chuẩn bị cạn kiệt."
    elif price_up and vol_up and not oi_up:
        trend = "Tăng do phe Short chốt lời (Short Covering)"
        logic = "Giá tăng đi kèm Volume tăng nhưng OI giảm. Cho thấy phe Short đang ồ ạt cắt lỗ/chốt vị thế bán khống, giúp giá đẩy lên nhanh nhưng thiếu dòng tiền mới mua lên."
    elif not price_up and vol_up and not oi_up:
        trend = "Giảm do phe Long tháo chạy (Long Liquidation)"
        logic = "Giá giảm đi kèm Volume tăng nhưng OI giảm. Phe Long đang chủ động đóng vị thế hàng loạt để cắt lỗ, lực bán tháo kỹ thuật mạnh."
    else:
        if price_up:
            trend = "Tăng nhẹ tích lũy (Accumulation Rally)"
            logic = "Giá tăng nhẹ với các chỉ số thanh khoản hỗn hợp, cho thấy thị trường đang tích lũy lực cầu hoặc đi ngang."
        else:
            trend = "Giảm nhẹ tích lũy (Distribution Decline)"
            logic = "Giá giảm nhẹ với các chỉ số thanh khoản hỗn hợp, thị trường đang điều chỉnh đi ngang."
            
    return trend, logic

if __name__ == '__main__':
    import sys
    import os
    csv_file = "ZC_H1_sample.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if os.path.exists(csv_file):
        analyze_cbot_data(csv_file)
    else:
        # Check in the current directory or workspace
        if os.path.exists(os.path.join(os.path.dirname(__file__), csv_file)):
            analyze_cbot_data(os.path.join(os.path.dirname(__file__), csv_file))
        else:
            print(f"Không tìm thấy file: {csv_file}")