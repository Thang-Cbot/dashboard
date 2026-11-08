import pandas as pd
import numpy as np

# Load ZC 1D Data
zc_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZC1!, 1D.csv')
zc_df['time'] = pd.to_datetime(zc_df['time'].astype(str).str.split('T').str[0])
zc_df = zc_df.sort_values('time').reset_index(drop=True)

# Load COT Data
cot_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/cot_10y_history.csv')
cot_df['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(cot_df['Report_Date_as_YYYY-MM-DD'])
zc_cot = cot_df[cot_df['CFTC_Contract_Market_Code'].astype(str).str.endswith('2602')].sort_values('Report_Date_as_YYYY-MM-DD')

# Roll months for Corn: Feb (2), Apr (4), Jun (6), Aug (8), Nov (11)
roll_months = [2, 4, 6, 8, 11]
years = range(2016, 2027)

roll_events = []

for y in years:
    for m in roll_months:
        month_days = zc_df[(zc_df['time'].dt.year == y) & (zc_df['time'].dt.month == m)]
        if len(month_days) < 15:
            continue
        
        fnd_idx = month_days.index[-1]
        fnd_date = month_days.iloc[-1]['time']
        
        if fnd_idx >= 10 and fnd_idx + 3 < len(zc_df):
            row_dict = {
                'Year': y,
                'Month': m,
                'FND_Date': fnd_date,
            }
            
            t10_date = zc_df.iloc[fnd_idx - 10]['time']
            closest_cot = zc_cot[zc_cot['Report_Date_as_YYYY-MM-DD'] <= t10_date].tail(1)
            net_pos = closest_cot.iloc[0]['Net_Position'] if not closest_cot.empty else 0
            row_dict['COT_Net'] = net_pos
            row_dict['BM_Bias'] = 'Heavily_Short' if net_pos < -30000 else ('Heavily_Long' if net_pos > 30000 else 'Neutral')
            
            for offset in range(-10, 4):
                day_data = zc_df.iloc[fnd_idx + offset]
                ret = (day_data['close'] - day_data['open']) / day_data['open'] * 100
                key = f"T{offset}" if offset < 0 else f"T+{offset}"
                if offset == 0: key = "FND_T0"
                row_dict[key] = ret
            
            p2_ret = (zc_df.iloc[fnd_idx]['close'] - zc_df.iloc[fnd_idx - 5]['open']) / zc_df.iloc[fnd_idx - 5]['open'] * 100
            row_dict['Final_5D_Roll_Return'] = p2_ret
            
            roll_events.append(row_dict)

df_zc = pd.DataFrame(roll_events)
df_zc.to_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/rollover_zc_behavior_10y.csv', index=False)

print(f"Tong so ky Rollover Corn (ZC): {len(df_zc)}")
summary = df_zc.groupby('BM_Bias')[['Final_5D_Roll_Return', 'T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'FND_T0', 'T+1']].mean()
print(summary.to_string())

for bias in ['Heavily_Long', 'Heavily_Short']:
    sub = df_zc[df_zc['BM_Bias'] == bias]
    print(f"\n[CORN - {bias}] (N={len(sub)})")
    for col in ['T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'FND_T0', 'T+1']:
        win = (sub[col] > 0).mean() * 100
        print(f"  {col}: Nen Xanh {win:.1f}% | Nen Do {100-win:.1f}% | TB: {sub[col].mean():.2f}%")
