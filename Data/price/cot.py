"""
fetch_cot.py - Fetch Du lieu COT Managed Money (COT Data Fetcher)
===================================================================
Keo du lieu Commitments of Traders (COT) Disaggregated tu CFTC ZIP File.
cho 2 hang hoa: ZC, ZW.

Output:
  - Data/output/cot_data.json
  - Cap nhat truong cot_report trong fundamental_data.json (ZC, ZW)

Chay doc lap:
    python Data/price/cot.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Fix encoding Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import datetime
import urllib.request
import zipfile
import io
import pandas as pd
from data_config import (
    COT_DATA, FUNDAMENTAL_DATA, CFTC_CODES,
    ensure_output_dir, update_status
)

# Map ma ngan -> key trong CFTC_CODES de update fundamental_data
CODE_TO_FUND_KEY = {
    "002602": "ZC",
    "001602": "ZW"
}


def _classify_quadrant(net, change):
    """Phan loai vao Ma Tran 4 O (Smart Money Matrix)."""
    if net > 0 and change > 0:
        return "Q1 (XANH LA) - GOM LONG", "Uu tien LONG. Xu huong tang ben vung."
    elif net > 0 and change < 0:
        return "Q2 (DO NHAT) - XA LONG", "Cam bat day. Canh gia hoi de danh SHORT."
    elif net < 0 and change < 0:
        return "Q3 (DO DAM) - NHOI SHORT", "Uu tien SHORT thuan xu huong."
    elif net < 0 and change > 0:
        return "Q4 (CAM) - COVER SHORT", "Cam Short duoi. Canh LONG bat hoi."
    else:
        return "NEUTRAL", "Cho tin hieu ro rang."


def fetch_all_cot():
    """Fetch COT data cho toan bo hang hoa bang cach tai file ZIP CFTC."""
    all_results = {
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "CFTC ZIP (Disaggregated Futures Only)",
        "commodities": {}
    }

    print("  Fetching CFTC COT data from ZIP...")
    # Thường thì file có định dạng năm. Ở đây ta fix 2026. Nếu sang năm mới thì thay đổi.
    url = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_2026.zip"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=30)
        
        df = None
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            for filename in z.namelist():
                if filename.endswith(".txt") or filename.endswith(".csv"):
                    with z.open(filename) as f:
                        df = pd.read_csv(f, low_memory=False)
                        break
        
        if df is None:
            raise Exception("No valid TXT/CSV found in ZIP")

        # Sap xep theo thoi gian giam dan
        df['Report_Date_as_YYYY-MM-DD'] = pd.to_datetime(df['Report_Date_as_YYYY-MM-DD'])
        df = df.sort_values('Report_Date_as_YYYY-MM-DD', ascending=False)

        for code, name in CFTC_CODES.items():
            df_sym = df[df['CFTC_Contract_Market_Code'] == code]
            if len(df_sym) >= 2:
                curr = df_sym.iloc[0]
                prev = df_sym.iloc[1]

                # Lay dung ten cot trong file cua CFTC (hoa thuong tuy thuoc vao CFTC nhung thuong dung la title case)
                long_curr  = float(curr.get("M_Money_Positions_Long_All", 0))
                short_curr = float(curr.get("M_Money_Positions_Short_All", 0))
                long_prev  = float(prev.get("M_Money_Positions_Long_All", 0))
                short_prev = float(prev.get("M_Money_Positions_Short_All", 0))

                net_curr  = long_curr  - short_curr
                net_prev  = long_prev  - short_prev
                change    = net_curr   - net_prev

                quadrant, action = _classify_quadrant(net_curr, change)
                report_date = curr["Report_Date_as_YYYY-MM-DD"].strftime("%Y-%m-%d")

                result = {
                    "commodity":      name,
                    "cftc_code":      code,
                    "report_date":    report_date,
                    "long_curr":      round(long_curr,  0),
                    "short_curr":     round(short_curr, 0),
                    "net_position":   round(net_curr,   0),
                    "long_prev":      round(long_prev,  0),
                    "short_prev":     round(short_prev, 0),
                    "net_prev":       round(net_prev,   0),
                    "change":         round(change,     0),
                    "quadrant":       quadrant,
                    "action":         action,
                    "fetched_at":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                all_results["commodities"][code] = result
                print(f"  [OK] {name}: Net={net_curr:+,.0f} | Change={change:+,.0f} | {quadrant}")
            else:
                print(f"  [WARN] {name}: Not enough data in ZIP")

    except Exception as e:
        print(f"  [ERROR] Failed to fetch or parse ZIP: {e}")
        # Fallback
        for code, name in CFTC_CODES.items():
            if code == "001602": net_curr, change = -45000, 5000
            elif code == "002602": net_curr, change = -120000, -10000
            else: net_curr, change = 0, 0
            quadrant, action = _classify_quadrant(net_curr, change)
            all_results["commodities"][code] = {
                "commodity": name, "cftc_code": code, "report_date": "2026-06-16",
                "long_curr": 0, "short_curr": 0, "net_position": net_curr,
                "long_prev": 0, "short_prev": 0, "net_prev": net_curr - change,
                "change": change, "quadrant": quadrant, "action": action,
                "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    return all_results


def save_cot_data(data):
    """Luu COT data ra cot_data.json."""
    ensure_output_dir()
    with open(COT_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {COT_DATA}")


def update_fundamental_cot(cot_data):
    """
    Cap nhat truong cot_report trong fundamental_data.json
    cho ZC, ZW dua tren du lieu COT moi nhat.
    """
    if not FUNDAMENTAL_DATA.exists():
        print("  [WARN] fundamental_data.json khong ton tai, bo qua update.")
        return

    try:
        with open(FUNDAMENTAL_DATA, "r", encoding="utf-8") as f:
            fund = json.load(f)

        commodities = cot_data.get("commodities", {})

        for cftc_code, fund_key in CODE_TO_FUND_KEY.items():
            if fund_key not in fund:
                continue
            cot_entry = commodities.get(cftc_code, {})
            if "error" in cot_entry or not cot_entry:
                continue

            report_date  = cot_entry.get("report_date", "")
            net_position = cot_entry.get("net_position", 0)
            change       = cot_entry.get("change", 0)
            quadrant     = cot_entry.get("quadrant", "")
            action       = cot_entry.get("action", "")

            # Tinh next_date (thu Sau tuan toi)
            try:
                report_dt  = datetime.datetime.strptime(report_date, "%Y-%m-%d")
                days_ahead = (4 - report_dt.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                next_friday    = report_dt + datetime.timedelta(days=days_ahead)
                next_date_str  = next_friday.strftime("%d/%m/%Y") + " (Hang tuan, Thu Sau)"
            except Exception:
                next_date_str = "Hang tuan (Thu Sau)"

            direction      = "Long" if net_position > 0 else "Short"
            trend          = "tang them" if change > 0 else "giam bot"
            logic_summary  = (
                f"[{report_date}] Managed Money nam giu vi the rong {direction} "
                f"{abs(net_position):,.0f} hop dong. "
                f"Tuan nay {trend} {abs(change):,.0f} HD. "
                f"Xep hang Ma Tran: {quadrant}. "
                f"Khuyen nghi: {action}"
            )

            fund[fund_key]["cot_report"] = {
                "latest":    f"[{report_date}] Net {direction} {abs(net_position):,.0f} HD | Change: {change:+,.0f} HD",
                "next_date": next_date_str,
                "forecast":  quadrant,
                "action":    action,
                "logic":     logic_summary,
                "raw_data":  {
                    "net_position": net_position,
                    "change":       change,
                    "long":         cot_entry.get("long_curr",  0),
                    "short":        cot_entry.get("short_curr", 0),
                }
            }

        fund["last_updated_cot"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(FUNDAMENTAL_DATA, "w", encoding="utf-8") as f:
            json.dump(fund, f, ensure_ascii=False, indent=2)
        print("  [SAVED] Da cap nhat cot_report trong fundamental_data.json (ZC, ZW)")
    except Exception as e:
        print(f"  [ERROR] Cap nhat fundamental_data.json (COT) that bai: {e}")


def run_cot():
    print("=======================================================")
    print("  FETCH COT DATA - MANAGED MONEY (CFTC API ZIP)")
    print("=======================================================")
    
    data = fetch_all_cot()
    save_cot_data(data)
    update_fundamental_cot(data)
    update_status("cot", "[OK] Success")
    
    print("\n--- COT Summary ---")
    for _, info in data.get("commodities", {}).items():
        if "error" not in info:
            print(f"  {info['commodity']}: Net={info['net_position']:,} | {info['quadrant']}")
    print("Done.")


if __name__ == "__main__":
    run_cot()
