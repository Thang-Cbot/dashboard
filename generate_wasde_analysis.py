import pandas as pd
import numpy as np
import json
import os

print("ang c d liu gi D1 15 nm...")
# Load ZW
zw_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZW1!, 1D.csv')
# time format could be 2026-10-08T...
zw_df['time'] = pd.to_datetime(zw_df['time'].astype(str).str.split('T').str[0])
zw_df = zw_df.sort_values('time').set_index('time')
zw_df['TR'] = zw_df['high'] - zw_df['low']

# Load ZC
zc_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZC1!, 1D.csv')
zc_df['time'] = pd.to_datetime(zc_df['time'].astype(str).str.split('T').str[0])
zc_df = zc_df.sort_values('time').set_index('time')
zc_df['TR'] = zc_df['high'] - zc_df['low']

print("Xc nh lch bo co WASDE bng thut ton Proxy Volatility (10 nm qua)...")
# Find WASDE Dates (Proxy: Highest TR between 8th and 12th of every month)
wasde_dates = []
for year in range(2016, 2027):
    for month in range(1, 13):
        if year == 2026 and month > 10:
            continue
        
        start_date = f"{year}-{month:02d}-08"
        end_date = f"{year}-{month:02d}-13"
        try:
            subset = zw_df.loc[start_date:end_date]
            if not subset.empty:
                wasde_day = subset['TR'].idxmax()
                wasde_dates.append(wasde_day)
        except Exception as e:
            pass

results = []
print("Thu thp hnh vi gi T-4 v T+3 xung quanh cc k WASDE...")
# Calculate T-4, T-0, T+3
for w_date in wasde_dates:
    try:
        idx = zw_df.index.get_loc(w_date)
        if idx >= 4 and idx + 3 < len(zw_df):
            t_minus_4 = zw_df.iloc[idx - 4]
            t_minus_1 = zw_df.iloc[idx - 1]
            t_0 = zw_df.iloc[idx]
            t_plus_3 = zw_df.iloc[idx + 3]
            
            pre_report_return = (t_minus_1['close'] - t_minus_4['open']) / t_minus_4['open'] * 100
            report_day_tr = t_0['high'] - t_0['low']
            post_report_return = (t_plus_3['close'] - t_0['close']) / t_0['close'] * 100
            
            results.append({
                'WASDE_Date': w_date.strftime('%Y-%m-%d'),
                'Month': w_date.strftime('%B'),
                'T_Minus_4_Open': t_minus_4['open'],
                'T_Minus_1_Close': t_minus_1['close'],
                'Pre_Report_Trend_%': round(pre_report_return, 2),
                'T_0_High': t_0['high'],
                'T_0_Low': t_0['low'],
                'T_0_Close': t_0['close'],
                'Report_Day_Range': round(report_day_tr, 2),
                'T_Plus_3_Close': t_plus_3['close'],
                'Post_Report_3D_Trend_%': round(post_report_return, 2)
            })
    except Exception as e:
        pass

res_df = pd.DataFrame(results)
out_path = 'D:/0_Thang_Drive/Antigravity/Cbot/Data/output/wasde_price_behavior_10y.csv'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
res_df.to_csv(out_path, index=False)
print(f"Hon thnh!  x l {len(res_df)} k bo co WASDE. Lu ti: {out_path}")
