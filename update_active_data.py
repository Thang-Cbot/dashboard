import sys
import os
import datetime

# Thu muc goc chua run_pro_plus.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from run_pro_plus import get_active_contract, download_and_analyze_contract
except ImportError as e:
    print(f"Khong the import run_pro_plus: {e}")
    sys.exit(1)

def update_all():
    print("--- DANG TAI DU LIEU GIA MOI NHAT TU YAHOO FINANCE ---")
    now_ict = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    for code in ["ZC", "ZW", "ZS"]:
        c1 = get_active_contract(code, now_ict)
        if c1:
            download_and_analyze_contract(code, c1[0], now_ict, "active")
        else:
            print(f"Khong tim thay hop dong active cho {code}")

if __name__ == '__main__':
    update_all()
