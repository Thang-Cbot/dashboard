import json
import os
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

def load_json(filepath):
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def score_f1_blacksea_supply(bs_data, manual_overrides):
    # Fallback to manual override since deep analysis of SovEcon/Tax is hard
    return manual_overrides.get("F1_Russia_Policy", {}).get("score", 5)

def score_f2_us_crop(fund_data):
    try:
        zw = fund_data.get("ZW", {})
        cc = zw.get("crop_condition", {}).get("latest", "0%")
        # Example cc: "45% G/E"
        val = int(cc.split("%")[0])
        if val > 65: return 2
        if val > 55: return 4
        if val > 45: return 6
        if val > 35: return 8
        return 10
    except:
        return 5

def score_f3_eu_supply(manual_overrides):
    return manual_overrides.get("F3_EU_Supply", {}).get("score", 5)

def score_f4_south_hemisphere(manual_overrides):
    return manual_overrides.get("F4_Southern_Hemisphere", {}).get("score", 5)

def score_f5_export_sales(sales_data):
    # Simplify: If data exists and is positive, slightly bullish, else neutral
    # A real implementation would parse the weekly sales volume
    return 5

def score_f6_us_stocks(fund_data):
    try:
        zw = fund_data.get("ZW", {})
        us_stk = zw.get("us_ending_stocks", {})
        pct = us_stk.get("pct_change", 0)
        if pct is None: return 5
        if pct > 10: return 2
        if pct > 0: return 4
        if pct > -10: return 7
        return 9
    except:
        return 5

def score_f7_global_stocks(fund_data):
    try:
        zw = fund_data.get("ZW", {})
        gl_stk = zw.get("global_ending_stocks", {})
        pct = gl_stk.get("pct_change", 0)
        if pct is None: return 5
        if pct > 5: return 2
        if pct > 0: return 4
        if pct > -5: return 7
        return 9
    except:
        return 5

def score_f8_geopolitics(manual_overrides):
    return manual_overrides.get("F8_Geopolitics", {}).get("score", 5)

def score_f9_dxy(macro_data):
    try:
        dxy = macro_data.get("DXY", {}).get("price", 102.0)
        if dxy > 105: return 2
        if dxy > 103: return 4
        if dxy > 100: return 6
        if dxy > 98: return 8
        return 10
    except:
        return 5

def score_f10_oil(macro_data):
    try:
        wti = macro_data.get("WTI", {}).get("price", 75.0)
        if wti < 70: return 2
        if wti < 80: return 5
        if wti < 90: return 8
        return 10
    except:
        return 5

def score_f11_cot(cot_data):
    try:
        net_pos = cot_data.get("ZW", {}).get("net_position", 0)
        # If deeply net short, high chance of squeeze (bullish)
        if net_pos < -80000: return 10
        if net_pos < -50000: return 8
        if net_pos < 0: return 6
        if net_pos < 30000: return 4
        return 2
    except:
        return 5

def calculate_macro_score():
    # Load all data
    fund_data = load_json(OUTPUT_DIR / "fundamental_data.json")
    macro_data = load_json(OUTPUT_DIR / "macro_data.json")
    cot_data = load_json(OUTPUT_DIR / "cot_data.json")
    sales_data = load_json(OUTPUT_DIR / "export_sales.json")
    bs_data = load_json(OUTPUT_DIR / "blacksea_wheat.json")
    weights_config = load_json(BASE_DIR / "macro_weights.json")
    
    manual_overrides = weights_config.get("manual_overrides", {})
    monthly_weights = weights_config.get("monthly_weights", {})
    
    # Get current month
    current_month = str(datetime.now().month)
    weights = monthly_weights.get(current_month, {})
    
    if not weights:
        # Fallback to even weights if config is broken
        weights = {f"F{i}": 100/11 for i in range(1, 12)}
    
    # Calculate base scores (1-10)
    scores = {
        "F1": score_f1_blacksea_supply(bs_data, manual_overrides),
        "F2": score_f2_us_crop(fund_data),
        "F3": score_f3_eu_supply(manual_overrides),
        "F4": score_f4_south_hemisphere(manual_overrides),
        "F5": score_f5_export_sales(sales_data),
        "F6": score_f6_us_stocks(fund_data),
        "F7": score_f7_global_stocks(fund_data),
        "F8": score_f8_geopolitics(manual_overrides),
        "F9": score_f9_dxy(macro_data),
        "F10": score_f10_oil(macro_data),
        "F11": score_f11_cot(cot_data),
    }
    
    # Calculate weighted contributions
    total_score_10 = 0
    breakdown = {}
    
    for factor, score in scores.items():
        weight_pct = weights.get(factor, 0)
        contribution = score * (weight_pct / 100.0)
        total_score_10 += contribution
        
        breakdown[factor] = {
            "score_1_to_10": score,
            "weight_pct": weight_pct,
            "contribution": round(contribution, 2)
        }
    
    # Scale from 1-10 to 1-100
    final_score_100 = round(total_score_10 * 10, 1)
    
    # Determine Trend
    trend = "Neutral"
    if final_score_100 < 30: trend = "Strong Bearish (Giảm Rất Mạnh)"
    elif final_score_100 < 45: trend = "Slightly Bearish (Giảm Nhẹ)"
    elif final_score_100 < 55: trend = "Sideways (Đi Ngang)"
    elif final_score_100 < 70: trend = "Slightly Bullish (Tăng Nhẹ)"
    else: trend = "Strong Bullish (Tăng Mạnh)"
    
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month": current_month,
        "total_score": final_score_100,
        "trend": trend,
        "breakdown": breakdown
    }
    
    # Save output
    with open(OUTPUT_DIR / "macro_scores.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
        
    print(f"[MACRO ENGINE] Updated Matrix Score for Month {current_month}: {final_score_100}/100 ({trend})")

if __name__ == "__main__":
    calculate_macro_score()
