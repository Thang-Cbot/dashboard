"""
Data/run_data_now.py
====================
Chay dong bo toan bo du lieu NGAY LAP TUC (Price -> Weather -> Reports).
Duoc goi boi 'RUN CBot Data.bat'.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import time
import datetime

# Import tu cac module con
try: from price.prices import run_fetch_prices
except: run_fetch_prices = lambda force: True

try: from price.macro import run_fetch_macro
except: run_fetch_macro = lambda: True

try: from price.cot import run_fetch_cot
except: run_fetch_cot = lambda: True

try: from weather.weather_short import fetch_weather_short
except: fetch_weather_short = lambda: True

try: from weather.weather_long import fetch_weather_long
except: fetch_weather_long = lambda: True

try: from reports.export_sales import fetch_export_sales
except: fetch_export_sales = lambda: True

def main():
    t0 = time.time()
    print("="*60)
    print("  CBOT DATA - SYNCHRONIZING ALL DATA IMMEDIATELY")
    print("="*60)
    
    print("\n[1] DATA PRICE & MACRO")
    run_fetch_prices(force=True)  # force=True de bo qua kiem tra gio giao dich
    run_fetch_macro()
    run_fetch_cot()
    
    print("\n[2] DATA WEATHER")
    fetch_weather_short()
    fetch_weather_long()
    
    print("\n[3] DATA REPORTS")
    fetch_export_sales()
    # usda crawler duoc tich hop truc tiep neu can
    
    t1 = time.time()
    print("\n" + "="*60)
    print(f"  HOAN THANH TRONG: {int(t1-t0)} giay.")
    print("="*60)

if __name__ == "__main__":
    main()
