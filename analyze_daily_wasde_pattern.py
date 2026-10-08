import pandas as pd
import numpy as np

# Load ZW 1D Data
zw_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZW1!, 1D.csv')
zw_df['time'] = pd.to_datetime(zw_df['time'].astype(str).str.split('T').str[0])
zw_df = zw_df.sort_values('time').set_index('time')

# Load Combined WASDE + COT Data
combined_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/wasde_cot_combined_analysis.csv')
combined_df['WASDE_Date'] = pd.to_datetime(combined_df['WASDE_Date'])
combined_df = combined_df.dropna(subset=['COT_ZW_Net_Position'])

results = []

for _, row in combined_df.iterrows():
    w_date = row['WASDE_Date']
    cot_net = row['COT_ZW_Net_Position']
    
    try:
        idx = zw_df.index.get_loc(w_date)
        
        # Ensure we have enough data bounds
        if idx >= 4 and idx + 3 < len(zw_df):
            # Calculate daily returns: (Close - Open) / Open * 100
            daily_returns = {}
            for offset in range(-4, 4): # -4, -3, -2, -1, 0, 1, 2, 3
                day_data = zw_df.iloc[idx + offset]
                day_ret = (day_data['close'] - day_data['open']) / day_data['open'] * 100
                key = f"T_{offset}" if offset < 0 else f"T_plus_{offset}"
                if offset == 0: key = "T_0"
                daily_returns[key] = day_ret
            
            daily_returns['WASDE_Date'] = w_date
            daily_returns['COT_Net'] = cot_net
            # Classify Big Money bias
            if cot_net > 10000:
                daily_returns['BM_Bias'] = 'Heavily_Long'
            elif cot_net < -10000:
                daily_returns['BM_Bias'] = 'Heavily_Short'
            else:
                daily_returns['BM_Bias'] = 'Neutral'
                
            results.append(daily_returns)
    except Exception as e:
        pass

daily_df = pd.DataFrame(results)

# Group by Big Money Bias
summary = daily_df.groupby('BM_Bias')[['T_-4', 'T_-3', 'T_-2', 'T_-1', 'T_0', 'T_plus_1', 'T_plus_2', 'T_plus_3']].mean()

print("\n=== QUY LUT LI NHUN TRUNG BNH TNG NGY (T-4 N T+3) THEO V TH BIG MONEY ===")
print("n v: % thay i gi (Close - Open) trong ngy .\n")

# Format for markdown output
out_str = "| Trng thi Big Money | T-4 | T-3 | T-2 | T-1 (Nn th) | T-0 (Bo co) | T+1 | T+2 | T+3 |\n"
out_str += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"

for bias in ['Heavily_Long', 'Heavily_Short']:
    if bias in summary.index:
        r = summary.loc[bias]
        out_str += f"| **{bias}** | {r['T_-4']:.2f}% | {r['T_-3']:.2f}% | {r['T_-2']:.2f}% | {r['T_-1']:.2f}% | {r['T_0']:.2f}% | {r['T_plus_1']:.2f}% | {r['T_plus_2']:.2f}% | {r['T_plus_3']:.2f}% |\n"

print(out_str)

# Calculate win rate per day (Probability of red vs green candle)
print("\n=== XC SUT NN XANH/ TNG NGY ===")
for bias in ['Heavily_Long', 'Heavily_Short']:
    print(f"\n[{bias}]")
    subset = daily_df[daily_df['BM_Bias'] == bias]
    for col in ['T_-4', 'T_-3', 'T_-2', 'T_-1', 'T_0', 'T_plus_1', 'T_plus_2', 'T_plus_3']:
        prob_up = (subset[col] > 0).mean() * 100
        prob_down = (subset[col] < 0).mean() * 100
        print(f"  {col}: Nn Xanh {prob_up:.1f}% | Nn  {prob_down:.1f}%")

