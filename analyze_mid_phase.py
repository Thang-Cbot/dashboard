import pandas as pd
import numpy as np

# Load ZW data
zw_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/price/Gia 15 nam/CBOT_DL_ZW1!, 1D.csv')
zw_df['time'] = pd.to_datetime(zw_df['time'].astype(str).str.split('T').str[0])
zw_df = zw_df.sort_values('time').reset_index(drop=True)

# Load COT
cot_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/cot_10y_history.csv')
cot_df['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(cot_df['Report_Date_as_YYYY-MM-DD'])
zw_cot = cot_df[cot_df['CFTC_Contract_Market_Code'].astype(str).str.endswith('1602')].sort_values('Report_Date_as_YYYY-MM-DD')

roll_months = [2, 4, 6, 8, 11]
years = range(2016, 2027)

mid_phase_results = []

for y in years:
    for m in roll_months:
        month_days = zw_df[(zw_df['time'].dt.year == y) & (zw_df['time'].dt.month == m)]
        if len(month_days) < 18:
            continue
        
        # Goldman Roll is business day 5 to 9 (indices 4 to 8)
        # T-5 to FND is the last 5 trading days: indices -5 to -1
        # The Middle Gap is from business day 10 (index 9) to T-6 (index -6)
        day_10_idx = month_days.index[9]
        t_6_idx = month_days.index[-6]
        
        if t_6_idx >= day_10_idx:
            start_open = zw_df.loc[day_10_idx, 'open']
            end_close = zw_df.loc[t_6_idx, 'close']
            ret_mid = (end_close - start_open) / start_open * 100
            
            mid_date = zw_df.loc[day_10_idx, 'time']
            closest_cot = zw_cot[zw_cot['Report_Date_as_YYYY-MM-DD'] <= mid_date].tail(1)
            net_pos = closest_cot.iloc[0]['Net_Position'] if not closest_cot.empty else 0
            
            mid_phase_results.append({
                'Year': y,
                'Month': m,
                'Start_Date': zw_df.loc[day_10_idx, 'time'].strftime('%Y-%m-%d'),
                'End_Date': zw_df.loc[t_6_idx, 'time'].strftime('%Y-%m-%d'),
                'Days': t_6_idx - day_10_idx + 1,
                'Return_%': ret_mid,
                'COT_Net': net_pos,
                'BM_Bias': 'Heavily_Short' if net_pos < -15000 else ('Heavily_Long' if net_pos > 15000 else 'Neutral')
            })

df_mid = pd.DataFrame(mid_phase_results)

print("=== PHAN TICH GIAI DOAN DEM O GIUA (NGAY 10 DEN T-6 TRUOC FND) ===")
print("Tong so ky khao sat:", len(df_mid))
summary_mid = df_mid.groupby('BM_Bias')['Return_%'].agg(['count', 'mean', lambda x: (x > 0).mean() * 100, lambda x: (x < 0).mean() * 100])
summary_mid.columns = ['Count', 'Mean_Return_%', 'Win_Rate_Up_%', 'Win_Rate_Down_%']
print(summary_mid.to_string())

print("\n=== RIENG KY ROLL THANG 11 (KY Z -> H) ===")
nov_mid = df_mid[df_mid['Month'] == 11]
print(nov_mid[['Year', 'Start_Date', 'End_Date', 'Days', 'Return_%', 'COT_Net', 'BM_Bias']].to_string())
