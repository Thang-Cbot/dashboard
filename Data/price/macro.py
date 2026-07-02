"""
Data/price/macro.py
===================
Fetch Brent Crude Oil and US Dollar Index (DXY).
Runs every hour at :15 during CBOT trading hours.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import json
import yfinance as yf
from data_config import OUTPUT_DIR, update_status

MACRO_FILE = OUTPUT_DIR / "macro_data.json"

def run_fetch_macro():
    """Fetch Brent and DXY from Yahoo Finance."""
    print("\n  -- MACRO DATA ---")
    data = {}
    
    # 1. Brent Crude Oil (BZ=F)
    try:
        tk_brent = yf.Ticker("BZ=F")
        df_brent = tk_brent.history(period="2d")
        if not df_brent.empty:
            curr = float(df_brent.iloc[-1]["Close"])
            prev = float(df_brent.iloc[-2]["Close"]) if len(df_brent) > 1 else curr
            data["brent"] = {
                "price": round(curr, 2),
                "change_pct": round((curr - prev) / prev * 100, 2) if prev else 0.0
            }
            print(f"  [OK] Brent: ${data['brent']['price']} ({data['brent']['change_pct']:+.2f}%)")
    except Exception as e:
        print(f"  [ERR] Brent: {e}")
        
    # 2. US Dollar Index (DX-Y.NYB)
    try:
        tk_dxy = yf.Ticker("DX-Y.NYB")
        df_dxy = tk_dxy.history(period="2d")
        if not df_dxy.empty:
            curr = float(df_dxy.iloc[-1]["Close"])
            prev = float(df_dxy.iloc[-2]["Close"]) if len(df_dxy) > 1 else curr
            data["dxy"] = {
                "price": round(curr, 3),
                "change_pct": round((curr - prev) / prev * 100, 2) if prev else 0.0
            }
            print(f"  [OK] DXY: {data['dxy']['price']} ({data['dxy']['change_pct']:+.2f}%)")
    except Exception as e:
        print(f"  [ERR] DXY: {e}")
        
    if data:
        with open(MACRO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        update_status("macro", "OK", f"Brent: ${data.get('brent',{}).get('price')} | DXY: {data.get('dxy',{}).get('price')}")
        return True
    else:
        update_status("macro", "ERROR", "Failed to fetch macro data")
        return False

if __name__ == "__main__":
    run_fetch_macro()
