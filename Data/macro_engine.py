import json
import os
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

def load_json(filepath):
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def get_file_mtime(filepath):
    """Return last modified time of file as formatted string."""
    try:
        ts = os.path.getmtime(filepath)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except:
        return "—"

def score_f1_blacksea(manual_overrides, bs_data):
    """F1: Nga/Ukraine Black Sea supply via manual override + blacksea data."""
    file_ok = (OUTPUT_DIR / "blacksea_wheat.json").exists()
    last_up  = get_file_mtime(OUTPUT_DIR / "blacksea_wheat.json")

    # Try to get raw value from blacksea file
    raw_val = "Nhập thủ công"
    raw_detail = ""
    if bs_data:
        try:
            # Try to find an export rate
            for k, v in bs_data.items():
                if isinstance(v, dict) and "export_mt" in v:
                    raw_val = f"{v['export_mt']:,.0f} tấn/tháng"
                    break
                if isinstance(v, dict) and "price_fob" in v:
                    raw_detail = f"FOB: ${v['price_fob']}"
        except:
            pass

    score = manual_overrides.get("F1_Russia_Policy", {}).get("score", 5)
    note  = manual_overrides.get("F1_Russia_Policy", {}).get("note", "")
    status = "manual"  # Always manual
    return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": last_up, "status": status}

def score_f2_us_crop(fund_data):
    """F2: US Crop G/E Progress."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu", "last_updated": last_up, "status": "error"}
    try:
        import re
        zw = fund_data.get("ZW", fund_data)
        cc = zw.get("crop_condition", {})
        latest_str = cc.get("latest", cc.get("good_excellent", "50"))
        
        # Extract number from "Đông N/A (Cuối vụ), Xuân 55% G/E" or "50%"
        nums = re.findall(r'(\d+)', str(latest_str))
        if not nums:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Không tìm thấy %", "last_updated": last_up, "status": "error"}
        
        val = int(nums[-1]) # take the last number assuming it's the spring wheat % if winter is N/A
        
        if val > 65: score = 2
        elif val > 55: score = 4
        elif val > 45: score = 6
        elif val > 35: score = 8
        else: score = 10
        return {"score": score, "raw_value": f"{val}% G/E", "raw_detail": str(latest_str)[:40], "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "Parse Error", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f3_eu_supply(manual_overrides):
    """F3: EU/France supply - manual."""
    score = manual_overrides.get("F3_EU_Supply", {}).get("score", 5)
    note  = manual_overrides.get("F3_EU_Supply", {}).get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f4_south_hemisphere(manual_overrides):
    """F4: Southern Hemisphere - manual."""
    score = manual_overrides.get("F4_Southern_Hemisphere", {}).get("score", 5)
    note  = manual_overrides.get("F4_Southern_Hemisphere", {}).get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f5_export_sales(sales_data):
    """F5: US Weekly Export Sales."""
    filepath = OUTPUT_DIR / "export_sales.json"
    last_up  = get_file_mtime(filepath)
    if not sales_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Chưa có dữ liệu Export Sales", "last_updated": last_up, "status": "error"}
    try:
        zw = sales_data.get("commodities", {}).get("ZW", {})
        net = zw.get("current_mt", 0)
        net_k = float(net) / 1000
        if net_k > 500: score = 9
        elif net_k > 300: score = 7
        elif net_k > 100: score = 5
        elif net_k > 0:   score = 4
        else:             score = 3
        return {"score": score, "raw_value": f"{net_k:,.0f}k tấn/tuần", "raw_detail": "Net Sales report USDA", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f6_us_stocks(fund_data):
    """F6: US Ending Stocks % change."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu", "last_updated": last_up, "status": "error"}
    try:
        import re
        zw = fund_data.get("ZW", fund_data)
        us_stk = zw.get("us_ending_stocks", {})
        val    = us_stk.get("value", us_stk.get("current", None))
        pct    = us_stk.get("pct_change", us_stk.get("change_pct", None))
        if val is None and pct is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu trường us_ending_stocks", "last_updated": last_up, "status": "error"}
        pct = pct or 0
        if pct > 10: score = 2
        elif pct > 0: score = 4
        elif pct > -10: score = 7
        else: score = 9
        
        # val could be a string like "722 triệu bushels (2026/27)"
        if val:
            nums = re.findall(r"([\d\.,]+)", str(val))
            val_str = nums[0] if nums else str(val)
            raw_val = f"{val_str} Mbu ({pct:+.1f}%)"
        else:
            raw_val = f"{pct:+.1f}%"
            
        return {"score": score, "raw_value": raw_val, "raw_detail": "WASDE US Ending Stocks", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f7_global_stocks(fund_data):
    """F7: Global Ending Stocks % change."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu", "last_updated": last_up, "status": "error"}
    try:
        import re
        zw = fund_data.get("ZW", fund_data)
        gl_stk = zw.get("global_ending_stocks", zw.get("world_ending_stocks", {}))
        val    = gl_stk.get("value", gl_stk.get("current", None))
        pct    = gl_stk.get("pct_change", gl_stk.get("change_pct", None))
        if val is None and pct is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu trường global_ending_stocks", "last_updated": last_up, "status": "error"}
        pct = pct or 0
        if pct > 5: score = 2
        elif pct > 0: score = 4
        elif pct > -5: score = 7
        else: score = 9
        
        if val:
            nums = re.findall(r"([\d\.,]+)", str(val))
            val_str = nums[0] if nums else str(val)
            raw_val = f"{val_str} Mmt ({pct:+.1f}%)"
        else:
            raw_val = f"{pct:+.1f}%"
            
        return {"score": score, "raw_value": raw_val, "raw_detail": "WASDE World Ending Stocks", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f8_geopolitics(manual_overrides):
    """F8: Geopolitics & Logistics - manual."""
    score = manual_overrides.get("F8_Geopolitics", {}).get("score", 5)
    note  = manual_overrides.get("F8_Geopolitics", {}).get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f9_dxy(macro_data):
    """F9: DXY Index."""
    filepath = OUTPUT_DIR / "macro_data.json"
    last_up  = get_file_mtime(filepath)
    if not macro_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu macro", "last_updated": last_up, "status": "error"}
    try:
        dxy_d = macro_data.get("dxy", macro_data.get("DXY", {}))
        dxy   = dxy_d.get("price", None)
        pct   = dxy_d.get("pct", 0)
        if dxy is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu giá DXY", "last_updated": last_up, "status": "error"}
        if dxy > 105: score = 2
        elif dxy > 103: score = 4
        elif dxy > 100: score = 6
        elif dxy > 98: score = 8
        else: score = 10
        return {"score": score, "raw_value": f"DXY {dxy:.2f} ({pct:+.2f}%)", "raw_detail": "USD Index — Sức mạnh đồng đô", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f10_oil(macro_data):
    """F10: Crude Oil WTI/Brent."""
    filepath = OUTPUT_DIR / "macro_data.json"
    last_up  = get_file_mtime(filepath)
    if not macro_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu macro", "last_updated": last_up, "status": "error"}
    try:
        brent_d = macro_data.get("brent", macro_data.get("WTI", macro_data.get("wti", {})))
        price   = brent_d.get("price", None)
        pct     = brent_d.get("pct", 0)
        if price is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu giá Brent/WTI", "last_updated": last_up, "status": "error"}
        if price < 70: score = 2
        elif price < 80: score = 5
        elif price < 90: score = 8
        else: score = 10
        return {"score": score, "raw_value": f"Brent ${price:.2f} ({pct:+.2f}%)", "raw_detail": "Crude Oil — Cước tàu & Phân bón", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f11_cot(cot_data):
    """F11: COT Net Position."""
    filepath = OUTPUT_DIR / "cot_data.json"
    last_up  = get_file_mtime(filepath)
    if not cot_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu COT", "last_updated": last_up, "status": "error"}
    try:
        # Navigate to ZW data
        commodities = cot_data.get("commodities", {})
        zw_data = None
        for code, data in commodities.items():
            if data.get("commodity") == "ZW":
                zw_data = data
                break
        if not zw_data:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Không tìm thấy ZW trong COT", "last_updated": last_up, "status": "error"}
        net_pos  = zw_data.get("net_position", 0)
        change   = zw_data.get("change", 0)
        quadrant = zw_data.get("quadrant", "")
        if net_pos < -80000: score = 10
        elif net_pos < -50000: score = 8
        elif net_pos < -20000: score = 7
        elif net_pos < 0: score = 6
        elif net_pos < 30000: score = 4
        else: score = 2
        raw_val = f"Net: {net_pos:+,.0f} ({change:+,.0f})"
        raw_detail = quadrant or "COT Managed Money (CFTC)"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}


def calculate_macro_score():
    # Load all data
    fund_data    = load_json(OUTPUT_DIR / "fundamental_data.json")
    macro_data   = load_json(OUTPUT_DIR / "macro_data.json")
    cot_data     = load_json(OUTPUT_DIR / "cot_data.json")
    sales_data   = load_json(OUTPUT_DIR / "export_sales.json")
    bs_data      = load_json(OUTPUT_DIR / "blacksea_wheat.json")
    weights_cfg  = load_json(BASE_DIR / "macro_weights.json") or {}

    manual_overrides = weights_cfg.get("manual_overrides", {})
    monthly_weights  = weights_cfg.get("monthly_weights", {})

    current_month = str(datetime.now().month)
    weights = monthly_weights.get(current_month, {f"F{i}": round(100/11, 1) for i in range(1, 12)})

    # Calculate per-factor rich data
    factor_results = {
        "F1":  score_f1_blacksea(manual_overrides, bs_data),
        "F2":  score_f2_us_crop(fund_data),
        "F3":  score_f3_eu_supply(manual_overrides),
        "F4":  score_f4_south_hemisphere(manual_overrides),
        "F5":  score_f5_export_sales(sales_data),
        "F6":  score_f6_us_stocks(fund_data),
        "F7":  score_f7_global_stocks(fund_data),
        "F8":  score_f8_geopolitics(manual_overrides),
        "F9":  score_f9_dxy(macro_data),
        "F10": score_f10_oil(macro_data),
        "F11": score_f11_cot(cot_data),
    }

    total_score_10 = 0
    breakdown = {}

    for f_key, result in factor_results.items():
        score      = result["score"]
        weight_pct = weights.get(f_key, 0)
        contribution = round(score * (weight_pct / 100.0), 2)
        total_score_10 += contribution

        breakdown[f_key] = {
            "score_1_to_10": score,
            "weight_pct":    weight_pct,
            "contribution":  contribution,
            "raw_value":     result.get("raw_value", "N/A"),
            "raw_detail":    result.get("raw_detail", ""),
            "last_updated":  result.get("last_updated", "—"),
            "status":        result.get("status", "error"),
        }

    final_score_100 = round(total_score_10 * 10, 1)

    if final_score_100 < 30:   trend = "Strong Bearish — Giảm Rất Mạnh"
    elif final_score_100 < 45: trend = "Slightly Bearish — Giảm Nhẹ"
    elif final_score_100 < 55: trend = "Sideways — Đi Ngang"
    elif final_score_100 < 70: trend = "Slightly Bullish — Tăng Nhẹ"
    else:                      trend = "Strong Bullish — Tăng Mạnh"

    result = {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month":       current_month,
        "total_score": final_score_100,
        "trend":       trend,
        "breakdown":   breakdown,
    }

    with open(OUTPUT_DIR / "macro_scores.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    try:
        print(f"[MACRO ENGINE] Month {current_month}: {final_score_100}/100 OK")
    except:
        print(f"[MACRO ENGINE] Done.")


if __name__ == "__main__":
    calculate_macro_score()
