"""
Data/fetch_cot.py — Wrapper gọi COT Fetcher từ Data/price/cot.py
=================================================================
Được gọi bởi run_data_update.py khi cập nhật toàn bộ dữ liệu.

Chạy độc lập:
    python Data/fetch_cot.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'price'))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_fetch_cot() -> bool:
    """Wrapper gọi run_fetch_cot() từ Data/price/cot.py"""
    try:
        from price.cot import run_fetch_cot as _run
        return _run()
    except Exception as e:
        print(f"  [ERROR] fetch_cot wrapper: {e}")
        return False

if __name__ == "__main__":
    ok = run_fetch_cot()
    print("  [OK] COT Done." if ok else "  [FAIL] COT Failed.")
