"""
fetch_macro.py — Fetch Dữ liệu Vĩ mô (Macro Data Fetcher)
===========================================================
Kéo dữ liệu Brent Crude Oil và US Dollar Index từ Yahoo Finance.
Output: Data/output/macro_data.json

Chạy độc lập:
    python Data/fetch_macro.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import datetime
import yfinance as yf
from data_config import MACRO_DATA, MACRO_TICKERS, ensure_output_dir, update_status


def fetch_macro_data() -> dict:
    """
    Fetch Brent, DXY và ZW reference từ Yahoo Finance.
    Trả về dict chứa giá + % thay đổi.
    """
    result = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "brent": {},
        "dxy": {},
        "zw_ref": {},
    }

    # ── Brent Crude Oil ────────────────────────────
    try:
        brent = yf.Ticker(MACRO_TICKERS["brent"])
        brent_data = brent.history(period="2d")
        if len(brent_data) >= 2:
            price = float(brent_data["Close"].iloc[-1])
            prev  = float(brent_data["Close"].iloc[-2])
            pct   = ((price - prev) / prev) * 100
        elif not brent_data.empty:
            price = float(brent_data["Close"].iloc[-1])
            prev  = price
            pct   = 0.0
        else:
            price, prev, pct = 90.74, 90.74, 0.0

        result["brent"] = {
            "price": round(price, 2),
            "prev":  round(prev,  2),
            "pct":   round(pct,   3),
            "ticker": MACRO_TICKERS["brent"],
        }
        print(f"  ✅ Brent: ${price:.2f} ({pct:+.2f}%)")
    except Exception as e:
        result["brent"] = {"price": 90.74, "prev": 90.74, "pct": 0.0, "error": str(e)}
        print(f"  ⚠️  Brent: Lỗi → {e}. Dùng giá trị fallback.")

    # ── US Dollar Index ─────────────────────────────
    try:
        dxy = yf.Ticker(MACRO_TICKERS["dxy"])
        dxy_data = dxy.history(period="2d")
        if len(dxy_data) >= 2:
            price = float(dxy_data["Close"].iloc[-1])
            prev  = float(dxy_data["Close"].iloc[-2])
            pct   = ((price - prev) / prev) * 100
        elif not dxy_data.empty:
            price = float(dxy_data["Close"].iloc[-1])
            prev  = price
            pct   = 0.0
        else:
            price, prev, pct = 99.09, 99.09, 0.0

        result["dxy"] = {
            "price": round(price, 3),
            "prev":  round(prev,  3),
            "pct":   round(pct,   3),
            "ticker": MACRO_TICKERS["dxy"],
        }
        print(f"  ✅ DXY: {price:.3f} ({pct:+.2f}%)")
    except Exception as e:
        result["dxy"] = {"price": 99.09, "prev": 99.09, "pct": 0.0, "error": str(e)}
        print(f"  ⚠️  DXY: Lỗi → {e}. Dùng giá trị fallback.")

    # ── ZW Reference (liên thị trường) ─────────────
    try:
        zw = yf.Ticker(MACRO_TICKERS["zw_ref"])
        zw_data = zw.history(period="2d")
        if len(zw_data) >= 2:
            price = float(zw_data["Close"].iloc[-1])
            prev  = float(zw_data["Close"].iloc[-2])
            pct   = ((price - prev) / prev) * 100
        elif not zw_data.empty:
            price = float(zw_data["Close"].iloc[-1])
            prev  = price
            pct   = 0.0
        else:
            price, prev, pct = 600.0, 600.0, 0.0

        result["zw_ref"] = {
            "price": round(price, 2),
            "prev":  round(prev,  2),
            "pct":   round(pct,   3),
            "ticker": MACRO_TICKERS["zw_ref"],
        }
        print(f"  ✅ ZW Ref: {price:.2f} cents ({pct:+.2f}%)")
    except Exception as e:
        result["zw_ref"] = {"price": 600.0, "prev": 600.0, "pct": 0.0, "error": str(e)}
        print(f"  ⚠️  ZW Ref: Lỗi → {e}. Dùng giá trị fallback.")

    return result


def save_macro_data(data: dict) -> None:
    """Lưu macro data ra file JSON."""
    ensure_output_dir()
    with open(MACRO_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Đã lưu: {MACRO_DATA}")


def load_macro_data() -> dict:
    """Đọc macro data từ file JSON (dùng trong các lệnh khác)."""
    if not MACRO_DATA.exists():
        return {}
    try:
        with open(MACRO_DATA, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_macro_values() -> tuple:
    """
    Trả về tuple (brent_price, brent_pct, dxy_price, dxy_pct, zw_pct)
    để dùng trong run_pro_plus.py giống hệt fetch_macro() cũ.
    """
    data = load_macro_data()
    brent_price = data.get("brent", {}).get("price", 90.74)
    brent_pct   = data.get("brent", {}).get("pct",   0.0)
    dxy_price   = data.get("dxy",   {}).get("price", 99.09)
    dxy_pct     = data.get("dxy",   {}).get("pct",   0.0)
    zw_pct      = data.get("zw_ref",{}).get("pct",   0.0)
    return brent_price, brent_pct, dxy_price, dxy_pct, zw_pct


def run_fetch_macro() -> bool:
    """Entry point chính — fetch và lưu macro data."""
    try:
        data = fetch_macro_data()
        save_macro_data(data)
        update_status("macro", "OK", f"Brent={data['brent'].get('price','?')}, DXY={data['dxy'].get('price','?')}")
        return True
    except Exception as e:
        update_status("macro", "ERROR", str(e))
        print(f"  ❌ Lỗi fetch macro: {e}")
        return False


if __name__ == "__main__":
    print("=" * 55)
    print("  FETCH MACRO DATA (Brent, DXY, ZW Reference)")
    print("=" * 55)
    run_fetch_macro()
    print("Done.")
