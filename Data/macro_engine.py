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
            if "N/A" in str(latest_str).upper() or "CUỐI" in str(latest_str).upper():
                return {"score": 5, "raw_value": "Cuối vụ/Đã thu hoạch", "raw_detail": str(latest_str)[:40], "last_updated": last_up, "status": "ok"}
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

def score_f3_other_supply(manual_overrides):
    """F3: Nguồn Cung Khác (EU, Canada, Ấn Độ...) - manual."""
    ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f4_weather_sh(manual_overrides):
    """F4: Thời Tiết Nam Bán Cầu (Úc / Argentina) - manual."""
    ov = manual_overrides.get("F4_Weather_SH", manual_overrides.get("F4_Southern_Hemisphere", {}))
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f4s_supply_sh(manual_overrides):
    """F4S: Nguồn Cung Nam Bán Cầu (Úc, Argentina) - sản lượng dự báo."""
    ov    = manual_overrides.get("F4S_Supply_SH", {})
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}

def score_f12_global_demand(manual_overrides):
    """F12: Nhu Cầu Toàn Cầu (Global Demand) - Ai Cập, Ả Rập, Trung Quốc..."""
    ov    = manual_overrides.get("F12_Global_Demand", {})
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"Điểm tự đánh giá: {score}/10", "raw_detail": note, "last_updated": "Thủ công", "status": "manual"}


def score_f5_export_sales(sales_data):
    """F5: US Weekly Export Sales — dùng dữ liệu chi tiết từ fundamental_data.json (ZW.export_sales_weekly)."""
    filepath_fund = OUTPUT_DIR / "fundamental_data.json"
    filepath_sale = OUTPUT_DIR / "export_sales.json"
    last_up = get_file_mtime(filepath_fund) if filepath_fund.exists() else get_file_mtime(filepath_sale)

    # Ưu tiên lấy từ fundamental_data.json (đủ hơn: WoW%, YoY%, lũy kế)
    fund_data_local = load_json(filepath_fund)
    try:
        if fund_data_local:
            zw_f = fund_data_local.get("ZW", {})
            es   = zw_f.get("export_sales_weekly", {})
            if es:
                latest_str  = es.get("latest_net_sales", "")   # "313.5 nghìn tấn"
                prev_str    = es.get("previous_net_sales", "")  # "402.5 nghìn tấn"
                wow_pct     = float(es.get("pct_change", 0))    # -22.11
                yoy_pct     = float(es.get("yoy_pct", 0))       # -24.4
                accum       = es.get("accumulated_sales", "")   # "4.909 triệu tấn"
                action      = es.get("action", "")              # "BEARISH"
                week_end    = es.get("week_ending", "")

                # Tách số từ chuỗi như "313.5 nghìn tấn"
                import re as _re
                nums = _re.findall(r"[-\d\.,]+", latest_str.replace(",", "."))
                net_k = float(nums[0]) if nums else 0.0

                # Chấm điểm dựa trên cả 3 chiều: WoW, YoY, và khối lượng tuyệt đối
                #  Tốt (Bullish > ZW): net_k cao, WoW tăng, YoY tăng → điểm cao
                score_vol = 9 if net_k > 500 else (7 if net_k > 300 else (5 if net_k > 100 else (4 if net_k > 0 else 2)))
                score_wow = 8 if wow_pct > 20 else (6 if wow_pct > 0 else (4 if wow_pct > -20 else 2))
                score_yoy = 9 if yoy_pct > 10 else (6 if yoy_pct > 0 else (4 if yoy_pct > -15 else 2))
                score = round((score_vol * 0.4 + score_wow * 0.3 + score_yoy * 0.3))
                score = max(1, min(10, score))

                raw_val    = f"{net_k:+.1f}k MT | WoW:{wow_pct:+.1f}% | YoY:{yoy_pct:+.1f}%"
                raw_detail = f"Tuần {week_end} | Lũy kế: {accum} | Prev: {prev_str}"
                return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}

        # Fallback về export_sales.json
        if not sales_data:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Chưa có dữ liệu Export Sales", "last_updated": last_up, "status": "error"}
        zw  = sales_data.get("commodities", {}).get("ZW", {})
        net = float(zw.get("current_mt", 0)) / 1000
        pct = float(zw.get("pct_change", 0))
        score = 9 if net > 500 else (7 if net > 300 else (5 if net > 100 else (4 if net > 0 else 3)))
        return {"score": score, "raw_value": f"{net:+.0f}k MT | WoW:{pct:+.1f}%", "raw_detail": "Net Sales USDA (export_sales.json)", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}

def score_f6_us_stocks(fund_data):
    """F6: US Ending Stocks — tự tính MoM từ current/previous + dùng pct_vs_prev_report để chấm điểm."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu", "last_updated": last_up, "status": "error"}
    try:
        import re as _re
        zw      = fund_data.get("ZW", fund_data)
        us_stk  = zw.get("us_ending_stocks", {})
        current = us_stk.get("current", None)          # "717 triệu bushels (2026/27)"
        prev    = us_stk.get("previous", None)         # "722 triệu bushels (2026/27)"
        # pct_vs_prev_report = so sánh Aug vs Jul WASDE (đáng tin cậy)
        pct_mom = float(us_stk.get("pct_vs_prev_report", 0) or 0)
        cur_mon = us_stk.get("current_month", "")
        pre_mon = us_stk.get("previous_month", "")
        logic   = us_stk.get("logic", "")

        if current is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu trường us_ending_stocks.current", "last_updated": last_up, "status": "error"}

        # Tự tính MoM thực từ số liệu (để tránh phụ thuộc vào pct_change có thể sai)
        nums_cur = _re.findall(r"[\d\.,]+", str(current))
        nums_pre = _re.findall(r"[\d\.,]+", str(prev)) if prev else []
        cur_num  = float(str(nums_cur[0]).replace(",", "")) if nums_cur else None
        pre_num  = float(str(nums_pre[0]).replace(",", "")) if nums_pre else None
        cur_str  = nums_cur[0] if nums_cur else "?"
        pre_str  = nums_pre[0] if nums_pre else "?"

        # Tính lại MoM thực nếu có đủ dữ liệu số
        if cur_num and pre_num and pre_num > 0:
            pct_mom_calc = round((cur_num - pre_num) / pre_num * 100, 1)
            # Nếu pct_vs_prev_report = 0 hoặc không hợp lý, dùng tính toán thực
            if pct_mom == 0:
                pct_mom = pct_mom_calc

        # Chấm điểm dựa trên MoM WASDE (tồn kho giảm = Bullish cho ZW)
        # pct_mom âm → tồn kho giảm → Bullish → điểm cao
        if   pct_mom >  5: score = 2   # Tồn kho tăng mạnh → Bearish
        elif pct_mom >  0: score = 4   # Tồn kho tăng nhẹ → hơi Bearish
        elif pct_mom > -3: score = 6   # Giảm nhẹ → trung lập
        elif pct_mom > -8: score = 8   # Giảm vừa → Bullish
        else:              score = 10  # Giảm mạnh → rất Bullish
        score = max(1, min(10, score))

        raw_val    = f"{cur_str} Mbu | WASDE {cur_mon}: {pct_mom:+.1f}% ({cur_str} ← {pre_str} Mbu)"
        raw_detail = logic[:80] if logic else f"WASDE {cur_mon} vs {pre_mon}"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}

def score_f7_global_stocks(fund_data):
    """F7: Global Ending Stocks — tự tính MoM từ current/previous + logic text."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "Không có dữ liệu", "last_updated": last_up, "status": "error"}
    try:
        import re as _re
        zw      = fund_data.get("ZW", fund_data)
        gl_stk  = zw.get("global_ending_stocks", zw.get("world_ending_stocks", {}))
        current = gl_stk.get("current", gl_stk.get("value", None))
        prev    = gl_stk.get("previous", None)
        pct_mom = float(gl_stk.get("pct_vs_prev_report", 0) or 0)
        cur_mon = gl_stk.get("current_month", "")
        pre_mon = gl_stk.get("previous_month", "")
        logic   = gl_stk.get("logic", "")

        if current is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiếu trường global_ending_stocks.current", "last_updated": last_up, "status": "error"}

        nums_cur = _re.findall(r"[\d\.,]+", str(current))
        nums_pre = _re.findall(r"[\d\.,]+", str(prev)) if prev else []
        cur_num  = float(str(nums_cur[0]).replace(",", "")) if nums_cur else None
        pre_num  = float(str(nums_pre[0]).replace(",", "")) if nums_pre else None
        cur_str  = nums_cur[0] if nums_cur else "?"
        pre_str  = nums_pre[0] if nums_pre else "?"

        # Tự tính MoM nếu pct_vs_prev_report = 0
        if cur_num and pre_num and pre_num > 0:
            pct_mom_calc = round((cur_num - pre_num) / pre_num * 100, 2)
            if pct_mom == 0:
                pct_mom = pct_mom_calc

        # Tồn kho toàn cầu: giảm = Bullish ZW
        if   pct_mom >  3: score = 2
        elif pct_mom >  0: score = 4
        elif pct_mom > -2: score = 6
        elif pct_mom > -5: score = 8
        else:              score = 10
        score = max(1, min(10, score))

        raw_val    = f"{cur_str} Mmt | WASDE {cur_mon}: {pct_mom:+.2f}% ({cur_str} ← {pre_str} Mmt)"
        raw_detail = logic[:80] if logic else f"WASDE {cur_mon} vs {pre_mon}"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}


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
        "F3":  score_f3_other_supply(manual_overrides),
        "F4":  score_f4_weather_sh(manual_overrides),
        "F4S": score_f4s_supply_sh(manual_overrides),
        "F5":  score_f5_export_sales(sales_data),
        "F6":  score_f6_us_stocks(fund_data),
        "F7":  score_f7_global_stocks(fund_data),
        "F8":  score_f8_geopolitics(manual_overrides),
        "F9":  score_f9_dxy(macro_data),
        "F10": score_f10_oil(macro_data),
        "F11": score_f11_cot(cot_data),
        "F12": score_f12_global_demand(manual_overrides),
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
