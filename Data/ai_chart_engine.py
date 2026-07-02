"""
Data/ai_chart_engine.py — AI Simulated H1 Chart Generator
=========================================================
Sử dụng Gemini API để dự báo giá các ngày còn lại trong tuần dựa trên 
Fundamentals, sau đó dùng nội suy (interpolation) để tạo nến H1 giả lập.
Ghép nến thật (đầu tuần -> hiện tại) + nến giả lập (hiện tại -> cuối tuần).
"""
import sys, os
import json
import math
import random
import datetime
import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
SIMULATED_FILE = OUTPUT_DIR / "ai_simulated_h1.json"

def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        return f.read().strip() or None

def get_week_boundaries():
    now = datetime.datetime.now()
    monday = now - datetime.timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    friday = monday + datetime.timedelta(days=4)
    friday = friday.replace(hour=23, minute=59, second=59)
    return now, monday, friday

def load_real_data(commodity: str):
    csv_path = OUTPUT_DIR / f"{commodity}_active_H1.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    date_col = next((c for c in df.columns if c.lower() in ['datetime', 'date', 'timestamp', 'time']), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col]).sort_values(date_col)
        df = df.rename(columns={date_col: "Datetime"})
    return df

def ask_ai_for_daily_targets(api_key, commodity, current_price, current_weekday, fund_data, acreage_data):
    # fund_data is fundamental_data.json
    # acreage_data is acreage_data.json
    
    prompt = f"""Bạn là AI Quant Trading chuyên nghiệp.
Phân tích mô phỏng giá (Simulation) cho {commodity} từ nay đến cuối tuần (Thứ 6).
Giá hiện tại: {current_price}
Ngày hiện tại trong tuần: Thứ {current_weekday + 2}

Dữ liệu cơ bản:
{json.dumps(fund_data.get(commodity, {}), ensure_ascii=False)[:1000]}
Diện tích: {json.dumps(acreage_data.get('commodities', {}).get(commodity, {}), ensure_ascii=False)[:500]}

Nhiệm vụ:
Dự báo Daily High, Low, Close cho TỪNG NGÀY còn lại trong tuần giao dịch này (đến hết Thứ 6).
- Nếu xu hướng Bearish mạnh (do Acreage tăng), giá phải giảm có cấu trúc (tạo LLO - Lower Lows).
- Nếu xu hướng Bullish, giá phải tăng có cấu trúc.
- Trả về CHÍNH XÁC định dạng JSON array sau, KHÔNG CÓ TEXT NÀO KHÁC:
[
  {{"day": 3, "name": "Wednesday", "close": 418.50, "high": 422.0, "low": 415.0}},
  {{"day": 4, "name": "Thursday", "close": 412.00, "high": 419.0, "low": 410.0}},
  {{"day": 5, "name": "Friday", "close": 410.00, "high": 414.0, "low": 408.0}}
]
(Chú ý day: 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri. Chỉ trả về các ngày >= ngày hiện tại).
"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    
    import time
    import re
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                r.raise_for_status()
                text = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return None
            except Exception as e:
                print(f"  [WARN] AI API {model} (Attempt {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(3)
    return None

def generate_h1_candles_for_day(start_price, daily_target, target_date):
    """Nội suy (interpolate) nến H1 cho 1 ngày từ start_price đến close_price."""
    candles = []
    close_p = daily_target["close"]
    high_p = daily_target["high"]
    low_p = daily_target["low"]
    
    # Giờ thực tế CBOT (VN time): 07:00 đến 01:00 sáng hôm sau
    hours_list = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1]
    num_candles = len(hours_list)
    
    current_open = start_price
    
    # Để đảm bảo chạm high và low, ta đặt vị trí nến high và low ngẫu nhiên
    high_idx = random.randint(2, num_candles - 3)
    low_idx = random.randint(2, num_candles - 3)
    if high_idx == low_idx:
        low_idx = (low_idx + 2) % num_candles
        
    for i, h in enumerate(hours_list):
        current_date = target_date
        if h < 7:  # Rạng sáng hôm sau
            current_date = target_date + datetime.timedelta(days=1)
        dt_str = current_date.replace(hour=h, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        
        # Tính target price cho nến này dựa trên nội suy tuyến tính đến Close
        progress = (i + 1) / num_candles
        expected_close = start_price + (close_p - start_price) * progress
        
        # Thêm nhiễu
        noise = random.uniform(-1.0, 1.0)
        
        c_close = expected_close + noise
        if i == high_idx:
            c_close = high_p - random.uniform(0, 0.5)
        elif i == low_idx:
            c_close = low_p + random.uniform(0, 0.5)
            
        # Nến cuối cùng phải đóng chính xác
        if i == num_candles - 1:
            c_close = close_p
            
        # Random Open, High, Low quanh Open và Close
        c_open = current_open
        c_high = max(c_open, c_close) + random.uniform(0, abs(high_p - max(c_open, c_close))*0.5 + 0.1)
        c_low = min(c_open, c_close) - random.uniform(0, abs(min(c_open, c_close) - low_p)*0.5 + 0.1)
        
        # Giới hạn không vượt quá daily High/Low
        c_high = min(c_high, high_p)
        c_low = max(c_low, low_p)
        
        candles.append({
            "Datetime": dt_str,
            "Open": round(c_open, 2),
            "High": round(c_high, 2),
            "Low": round(c_low, 2),
            "Close": round(c_close, 2)
        })
        current_open = c_close
        
    return candles

def generate():
    print("\n=======================================================")
    print("  AI CHART ENGINE - GENERATING SIMULATED H1 CANDLES")
    print("=======================================================")
    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Missing API Key. Skipping AI Chart Engine.")
        return False
        
    try:
        with open(OUTPUT_DIR / "fundamental_data.json", "r", encoding="utf-8") as f:
            fund_data = json.load(f)
        with open(OUTPUT_DIR / "acreage_data.json", "r", encoding="utf-8") as f:
            acreage_data = json.load(f)
    except Exception as e:
        print(f"  [ERR] Missing fundamental/acreage data: {e}")
        return False

    now, monday, friday = get_week_boundaries()
    current_weekday = now.weekday() # 0 = Monday, 4 = Friday
    
    simulated_results = {}
    
    for commodity in ["ZC", "ZW", "ZS"]:
        print(f"  [+] Processing {commodity}...")
        df_real = load_real_data(commodity)
        if df_real.empty:
            continue
            
        # Filter this week's real data
        df_week = df_real[(df_real["Datetime"] >= monday) & (df_real["Datetime"] <= now)]
        
        if df_week.empty:
            # Fallback if no real data this week yet
            last_price = df_real.iloc[-1]["Close"]
        else:
            last_price = df_week.iloc[-1]["Close"]
            
        # Convert real data to dict format
        final_candles = []
        for _, row in df_week.iterrows():
            final_candles.append({
                "Datetime": row["Datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "Open": row["Open"],
                "High": row["High"],
                "Low": row["Low"],
                "Close": row["Close"]
            })
            
        # If it's already Friday night/weekend, just use real data
        if current_weekday <= 4:
            print(f"  [+] Requesting AI path from {commodity} @ {last_price}...")
            targets = ask_ai_for_daily_targets(api_key, commodity, last_price, current_weekday, fund_data, acreage_data)
            
            if targets:
                print(f"  [+] AI targets received: {targets}")
                sim_start_price = last_price
                for tgt in targets:
                    day_idx = tgt.get("day", 1) - 1 # 0 to 4
                    if day_idx < current_weekday:
                        continue
                        
                    # Target date
                    target_date = monday + datetime.timedelta(days=day_idx)
                    
                    if day_idx == current_weekday:
                        # Today: generate from current hour to end of day
                        pass # For simplicity, just generate full block for remaining day
                        
                    day_candles = generate_h1_candles_for_day(sim_start_price, tgt, target_date)
                    # Filter out candles that are in the past
                    for c in day_candles:
                        c_dt = datetime.datetime.strptime(c["Datetime"], "%Y-%m-%d %H:%M:%S")
                        if c_dt > now:
                            final_candles.append(c)
                    
                    sim_start_price = tgt["close"]
            else:
                print(f"  [WARN] Failed to get AI targets for {commodity}")

        simulated_results[commodity] = final_candles
        
    with open(SIMULATED_FILE, "w", encoding="utf-8") as f:
        json.dump(simulated_results, f, indent=2)
        
    print(f"  [OK] Saved simulated charts to {SIMULATED_FILE}")
    return True

if __name__ == "__main__":
    generate()
