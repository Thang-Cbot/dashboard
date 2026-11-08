import pandas as pd
import numpy as np

# Load ZW 1D Data
zw_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZW1!, 1D.csv')
zw_df['time'] = pd.to_datetime(zw_df['time'].astype(str).str.split('T').str[0])
zw_df = zw_df.sort_values('time').reset_index(drop=True)

# Load COT Data
cot_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/cot_10y_history.csv')
cot_df['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(cot_df['Report_Date_as_YYYY-MM-DD'])
zw_cot = cot_df[cot_df['CFTC_Contract_Market_Code'].astype(str).str.endswith('1602')].sort_values('Report_Date_as_YYYY-MM-DD')

# Roll months for Wheat: Feb (2), Apr (4), Jun (6), Aug (8), Nov (11)
roll_months = [2, 4, 6, 8, 11]

# Identify all roll month periods from 2016 to 2026
years = range(2016, 2027)

roll_events = []

for y in years:
    for m in roll_months:
        # Get all trading days in this month
        month_days = zw_df[(zw_df['time'].dt.year == y) & (zw_df['time'].dt.month == m)]
        if len(month_days) < 15:
            continue
        
        # Last trading day of the month is FND (First Notice Day proxy)
        fnd_idx = month_days.index[-1]
        fnd_date = month_days.iloc[-1]['time']
        
        # Let's inspect the last 10 days leading to FND: T-10, T-9, ... T-1, FND (T-0)
        # And days after FND: T+1, T+2, T+3
        if fnd_idx >= 10 and fnd_idx + 3 < len(zw_df):
            row_dict = {
                'Year': y,
                'Month': m,
                'FND_Date': fnd_date,
            }
            
            # Find closest COT net position prior to T-10
            t10_date = zw_df.iloc[fnd_idx - 10]['time']
            closest_cot = zw_cot[zw_cot['Report_Date_as_YYYY-MM-DD'] <= t10_date].tail(1)
            net_pos = closest_cot.iloc[0]['Net_Position'] if not closest_cot.empty else 0
            row_dict['COT_Net'] = net_pos
            row_dict['BM_Bias'] = 'Heavily_Short' if net_pos < -15000 else ('Heavily_Long' if net_pos > 15000 else 'Neutral')
            
            # Daily returns: (close - open) / open * 100
            for offset in range(-10, 4):
                day_data = zw_df.iloc[fnd_idx + offset]
                ret = (day_data['close'] - day_data['open']) / day_data['open'] * 100
                key = f"T{offset}" if offset < 0 else f"T+{offset}"
                if offset == 0: key = "FND_T0"
                row_dict[key] = ret
            
            # Cumulative returns
            # Phase 1: Goldman Roll (days 5 to 9 of month)
            g_start = month_days.index[4] # 5th trading day
            g_end = month_days.index[8]   # 9th trading day
            g_ret = (zw_df.iloc[g_end]['close'] - zw_df.iloc[g_start]['open']) / zw_df.iloc[g_start]['open'] * 100
            row_dict['Goldman_Roll_Return'] = g_ret
            
            # Phase 2: Final 5 days to FND (T-5 to T0)
            p2_ret = (zw_df.iloc[fnd_idx]['close'] - zw_df.iloc[fnd_idx - 5]['open']) / zw_df.iloc[fnd_idx - 5]['open'] * 100
            row_dict['Final_5D_Roll_Return'] = p2_ret
            
            roll_events.append(row_dict)

df_roll = pd.DataFrame(roll_events)
df_roll.to_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/rollover_behavior_10y.csv', index=False)

print(f"Tong so ky Rollover phan tich: {len(df_roll)}")

# Summary by bias
summary = df_roll.groupby('BM_Bias')[['Goldman_Roll_Return', 'Final_5D_Roll_Return', 'T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'FND_T0', 'T+1', 'T+2']].mean()
print("\n=== LOI NHUAN TRUNG BINH THEO VI THE QUY (COT) TRONG KY ROLLOVER ===")
print(summary.to_string())

print("\n=== TY LE NEN XANH (%) THEO VI THE QUY ===")
for bias in ['Heavily_Long', 'Heavily_Short']:
    sub = df_roll[df_roll['BM_Bias'] == bias]
    print(f"\n[{bias}] (N={len(sub)})")
    for col in ['T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'FND_T0', 'T+1']:
        win = (sub[col] > 0).mean() * 100
        print(f"  {col}: Nen Xanh {win:.1f}% | Nen Do {100-win:.1f}% | TB: {sub[col].mean():.2f}%")
