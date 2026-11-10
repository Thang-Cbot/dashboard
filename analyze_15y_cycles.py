import pandas as pd
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read dataset
df = pd.read_csv(r'D:\0_Thang_Drive\Antigravity\Cbot\Data\price\Gia 15 nam\ZW_nominal_daily_2011_2026.csv')
date_col = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'index' in c.lower()][0]
df['Date'] = pd.to_datetime(df[date_col], utc=True).dt.tz_localize(None)
df.sort_values('Date', inplace=True)
df.reset_index(drop=True, inplace=True)

def get_zigzag(df, min_delta=150):
    pivots = []
    direction = 0
    last_pivot_val = df.loc[0, 'Close']
    last_pivot_date = df.loc[0, 'Date']
    last_pivot_idx = 0
    
    curr_extrema_val = last_pivot_val
    curr_extrema_date = last_pivot_date
    curr_extrema_idx = 0
    
    for i, row in df.iterrows():
        h = row['High']
        l = row['Low']
        d = row['Date']
        
        if direction == 0:
            if h >= last_pivot_val + min_delta:
                direction = 1
                curr_extrema_val = h
                curr_extrema_date = d
                curr_extrema_idx = i
                pivots.append({'type': 'LOW', 'date': last_pivot_date, 'price': last_pivot_val, 'idx': last_pivot_idx})
            elif l <= last_pivot_val - min_delta:
                direction = -1
                curr_extrema_val = l
                curr_extrema_date = d
                curr_extrema_idx = i
                pivots.append({'type': 'HIGH', 'date': last_pivot_date, 'price': last_pivot_val, 'idx': last_pivot_idx})
        elif direction == 1:
            if h > curr_extrema_val:
                curr_extrema_val = h
                curr_extrema_date = d
                curr_extrema_idx = i
            elif l <= curr_extrema_val - min_delta:
                pivots.append({'type': 'HIGH', 'date': curr_extrema_date, 'price': curr_extrema_val, 'idx': curr_extrema_idx})
                direction = -1
                curr_extrema_val = l
                curr_extrema_date = d
                curr_extrema_idx = i
        elif direction == -1:
            if l < curr_extrema_val:
                curr_extrema_val = l
                curr_extrema_date = d
                curr_extrema_idx = i
            elif h >= curr_extrema_val + min_delta:
                pivots.append({'type': 'LOW', 'date': curr_extrema_date, 'price': curr_extrema_val, 'idx': curr_extrema_idx})
                direction = 1
                curr_extrema_val = h
                curr_extrema_date = d
                curr_extrema_idx = i
                
    if direction == 1:
        pivots.append({'type': 'HIGH', 'date': curr_extrema_date, 'price': curr_extrema_val, 'idx': curr_extrema_idx})
    elif direction == -1:
        pivots.append({'type': 'LOW', 'date': curr_extrema_date, 'price': curr_extrema_val, 'idx': curr_extrema_idx})
        
    return pd.DataFrame(pivots)

p150 = get_zigzag(df, min_delta=150)
legs = []
for i in range(len(p150) - 1):
    p1 = p150.iloc[i]
    p2 = p150.iloc[i+1]
    delta = abs(p2['price'] - p1['price'])
    trend = 'TĂNG' if p2['type'] == 'HIGH' else 'GIẢM'
    days = (p2['date'] - p1['date']).days
    legs.append({
        'from_type': p1['type'],
        'from_date': p1['date'],
        'from_price': p1['price'],
        'to_type': p2['type'],
        'to_date': p2['date'],
        'to_price': p2['price'],
        'delta': delta,
        'trend': trend,
        'days': days
    })

legs_df = pd.DataFrame(legs)

print("="*80)
print("DANH SÁCH TẤT CẢ CÁC SÓNG (ZIGZAG 150 - ĐÁNH DẤU CÁC SÓNG >= 200 GIÁ):")
print("="*80)
for idx, r in legs_df.iterrows():
    flag = "[>= 200 GIÁ]" if r['delta'] >= 200 else "[150 - 199]"
    print(f"{idx+1:02d}. {flag:12s} [{r['trend']:4s}] Từ {r['from_type']} {r['from_price']:6.2f} ({r['from_date'].strftime('%d/%m/%Y')}) "
          f"-> {r['to_type']} {r['to_price']:6.2f} ({r['to_date'].strftime('%d/%m/%Y')}) "
          f"| Biên độ: {r['delta']:6.2f} giá | {r['days']:3d} ngày")
