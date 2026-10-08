import pandas as pd
import urllib.request
import zipfile
import io
import os
import time

out_dir = 'D:/0_Thang_Drive/Antigravity/Cbot/Data/output/COT_Archive'
os.makedirs(out_dir, exist_ok=True)

print("Bt u ti d liu COT 10 nm t y ban Giao dch CFTC...")
years = range(2016, 2027)
all_cot_data = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

WHEAT_CODE = '001602'
CORN_CODE = '002602'

for year in years:
    url = f"https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                txt_file = [f for f in z.namelist() if f.endswith('.txt')][0]
                with z.open(txt_file) as f:
                    df = pd.read_csv(f, low_memory=False)
                    
                    df['CFTC_Contract_Market_Code'] = df['CFTC_Contract_Market_Code'].astype(str).str.zfill(6)
                    filtered = df[df['CFTC_Contract_Market_Code'].isin([WHEAT_CODE, CORN_CODE])].copy()
                    
                    cols_to_keep = ['Report_Date_as_YYYY-MM-DD', 'CFTC_Contract_Market_Code', 
                                    'M_Money_Positions_Long_All', 'M_Money_Positions_Short_All']
                    filtered = filtered[cols_to_keep]
                    filtered['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(filtered['Report_Date_as_YYYY-MM-DD'])
                    filtered['Net_Position'] = filtered['M_Money_Positions_Long_All'] - filtered['M_Money_Positions_Short_All']
                    all_cot_data.append(filtered)
        print(f"-> {year} thnh cng!")
    except Exception as e:
        print(f"-> Li ti {year}: {e}")
    time.sleep(1)

if all_cot_data:
    final_cot = pd.concat(all_cot_data)
    final_cot = final_cot.sort_values(['CFTC_Contract_Market_Code', 'Report_Date_as_YYYY-MM-DD'])
    out_path = 'D:/0_Thang_Drive/Antigravity/Cbot/Data/output/cot_10y_history.csv'
    final_cot.to_csv(out_path, index=False)
    print(f"\n lu COT 10 nm ti: {out_path}")
    
    # MERGE COT WITH WASDE
    wasde_df = pd.read_csv('D:/0_Thang_Drive/Antigravity/Cbot/Data/output/wasde_price_behavior_10y.csv')
    wasde_df['WASDE_Date'] = pd.to_datetime(wasde_df['WASDE_Date'])
    
    # Only map for ZW as an example
    zw_cot = final_cot[final_cot['CFTC_Contract_Market_Code'] == WHEAT_CODE].copy()
    zw_cot = zw_cot.sort_values('Report_Date_as_YYYY-MM-DD')
    
    merged_results = []
    for _, row in wasde_df.iterrows():
        w_date = row['WASDE_Date']
        # Find the latest COT report BEFORE or ON the WASDE date (within 7 days)
        # CFTC is usually released on Friday, with data as of Tuesday.
        # If WASDE is on Wed (e.g. 10th), the closest COT available to the public is the previous Friday (data of previous Tue).
        closest_cot = zw_cot[zw_cot['Report_Date_as_YYYY-MM-DD'] <= w_date].tail(1)
        
        if not closest_cot.empty:
            cot_date = closest_cot.iloc[0]['Report_Date_as_YYYY-MM-DD']
            net_pos = closest_cot.iloc[0]['Net_Position']
        else:
            cot_date = None
            net_pos = None
            
        r = row.to_dict()
        r['COT_Date'] = cot_date.strftime('%Y-%m-%d') if cot_date else None
        r['COT_ZW_Net_Position'] = net_pos
        merged_results.append(r)
        
    merged_df = pd.DataFrame(merged_results)
    merged_out = 'D:/0_Thang_Drive/Antigravity/Cbot/Data/output/wasde_cot_combined_analysis.csv'
    merged_df.to_csv(merged_out, index=False)
    print(f" gp chung d liu WASDE v COT ti: {merged_out}")
