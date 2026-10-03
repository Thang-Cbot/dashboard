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
        return "â€”"

def score_f1_blacksea(manual_overrides, bs_data, commodity="ZW"):
    """F1: Nga/Ukraine Black Sea supply via manual override + blacksea data."""
    if commodity == "ZC": return {"score": 3, "raw_value": "Ukraine XK (F1)", "raw_detail": "Ukraine duy trÃ¬ tiáº¿n Ä‘á»™ xuáº¥t kháº©u NgÃ´ an toÃ n. Nga khÃ´ng pháº£i yáº¿u tá»‘ NgÃ´ trá»ng Ä‘iá»ƒm.", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    
    file_ok = (OUTPUT_DIR / "blacksea_wheat.json").exists()
    last_up  = get_file_mtime(OUTPUT_DIR / "blacksea_wheat.json")

    # Try to get raw value from blacksea file
    raw_val = "Dá»¯ liá»‡u ChuyÃªn gia"
    raw_detail = ""
    # Try to get raw value from blacksea file
    raw_val = "Dá»¯ liá»‡u ChuyÃªn gia"
    raw_detail = ""
    if bs_data:
        try:
            # Try to find an export rate
            for k, v in bs_data.items():
                if isinstance(v, dict) and "export_mt" in v:
                    raw_val = f"{v['export_mt']:,.0f} táº¥n/thÃ¡ng"
                    break
                if isinstance(v, dict) and "price_fob" in v:
                    raw_detail = f"FOB: ${v['price_fob']}"
        except:
            pass

    ov = manual_overrides.get("F1_Russia_Policy", {})
    score = ov.get("score", 5)
    note = ov.get("note", "")
    return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail or note, "last_updated": ov.get("updated_at", last_up), "status": "manual"}

def score_f2_us_production(fund_data, commodity="ZW"):
    """F2: US Production & Acreage (Macro Structural Supply)."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u", "last_updated": last_up, "status": "error"}
    try:
        import re as _re
        zw = fund_data.get(commodity, fund_data)
        
        # 1. Láº¥y dá»¯ liá»‡u Sáº£n LÆ°á»£ng (Production)
        prod = zw.get("us_production", {})
        prod_cur = prod.get("current", None)
        prod_pre = prod.get("previous", None)
        cur_mon  = prod.get("current_month", "")
        
        # 2. Láº¥y dá»¯ liá»‡u Diá»‡n TÃ­ch (Acreage)
        acre = zw.get("acreage", {})
        acre_pct = float(acre.get("pct_change", 0) or 0)
        acre_cur = acre.get("current", "").split(" ")[0] if acre.get("current") else ""

        if not prod_cur:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "ChÆ°a cÃ³ dá»¯ liá»‡u Sáº£n lÆ°á»£ng", "last_updated": last_up, "status": "error"}

        nums_cur = _re.findall(r"[\d\.,]+", str(prod_cur))
        nums_pre = _re.findall(r"[\d\.,]+", str(prod_pre)) if prod_pre else []
        cur_num  = float(str(nums_cur[0]).replace(",", "")) if nums_cur else None
        pre_num  = float(str(nums_pre[0]).replace(",", "")) if nums_pre else None
        cur_str  = nums_cur[0] if nums_cur else "?"
        pre_str  = nums_pre[0] if nums_pre else "?"

        pct_mom = 0.0
        if cur_num and pre_num and pre_num > 0:
            pct_mom = round((cur_num - pre_num) / pre_num * 100, 2)

        # Cháº¥m Ä‘iá»ƒm dá»±a trÃªn MoM Sáº£n LÆ°á»£ng (Sáº£n lÆ°á»£ng giáº£m = Bullish ZW = Äiá»ƒm cao)
        if   pct_mom >  2: score = 2
        elif pct_mom >  0: score = 4
        elif pct_mom > -1: score = 6
        elif pct_mom > -3: score = 8
        else:              score = 10
        
        # Cá»™ng thÃªm Ä‘iá»ƒm Bullish náº¿u diá»‡n tÃ­ch giáº£m máº¡nh (Acreage YoY < -3%)
        if acre_pct <= -3:
            score = min(10, score + 1)
        elif acre_pct >= 3:
            score = max(1, score - 1)

        raw_val = f"{cur_str} Mbu | MoM: {pct_mom:+.2f}% | Acreage: {acre_pct:+.1f}%"
        raw_detail = f"WASDE {cur_mon}: {cur_str} â† {pre_str} Mbu. Diá»‡n tÃ­ch: {acre_cur} M ac"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "Lá»—i xá»­ lÃ½ Data", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f2w_us_weather(manual_overrides, fund_data, commodity="ZW"):
    """F2W: Thá»i Tiáº¿t Má»¹ (Manual Score + Auto Text)."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    
    score = manual_overrides.get("F2W_US_Weather", {}).get("score", 5)
    note  = manual_overrides.get("F2W_US_Weather", {}).get("note", "")
    
    try:
        zw = fund_data.get(commodity, {}) if fund_data else {}
        weather_logic = zw.get("weather", {}).get("logic", "")
        short_weather = zw.get("short_term_weather", "")
        
        detail = weather_logic if weather_logic else note
        if short_weather and isinstance(short_weather, str):
            detail = f"{short_weather} | {detail}"
            
        return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": detail[:120], "last_updated": last_up, "status": "manual"}
    except Exception as e:
        return {"score": score, "raw_value": f"Äiá»ƒm: {score}/10", "raw_detail": note, "last_updated": last_up, "status": "manual"}

def score_f3_other_supply(manual_overrides, commodity="ZW"):
    if commodity == "ZC": return {"score": 2, "raw_value": "Máº¥t thá»‹ pháº§n TQ", "raw_detail": "Trung Quá»‘c mua NgÃ´ Brazil. Brazil soÃ¡n ngÃ´i Má»¹. MEGA BEARISH", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    """F3: Nguá»“n Cung KhÃ¡c (EU, Canada, áº¤n Äá»™...) - manual."""
    ov = manual_overrides.get("F3_Other_Supply", manual_overrides.get("F3_EU_Supply", {}))
    score = ov.get("score", 5)
    note = ov.get("note", "")
    return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thá»§ cÃ´ng"), "status": "manual"}

def score_f4_weather_sh(manual_overrides, commodity="ZW"):
    """F4: Thá»i Tiáº¿t Nam BÃ¡n Cáº§u (Ãšc / Argentina) - manual."""
    ov = manual_overrides.get("F4_Weather_SH", manual_overrides.get("F4_Southern_Hemisphere", {}))
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thá»§ cÃ´ng"), "status": "manual"}

def score_f4s_supply_sh(manual_overrides, commodity="ZW"):
    if commodity == "ZC": return {"score": 2, "raw_value": "MÃ¹a vá»¥ Nam Má»¹", "raw_detail": "Brazil lÃ  nÆ°á»›c XK NgÃ´ #1. Ãšc bá»‹ loáº¡i khá»i biáº¿n sá»‘ (Ã­t NgÃ´). MEGA BEARISH", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    """F4S: Nguá»“n Cung Nam BÃ¡n Cáº§u (Ãšc, Argentina) - sáº£n lÆ°á»£ng dá»± bÃ¡o."""
    ov    = manual_overrides.get("F4S_Supply_SH", {})
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thá»§ cÃ´ng"), "status": "manual"}

def score_f12_global_demand(manual_overrides, commodity="ZW"):
    if commodity == "ZC": return {"score": 4, "raw_value": "Nhu cáº§u suy yáº¿u", "raw_detail": "Nhu cáº§u thá»©c Äƒn chÄƒn nuÃ´i toÃ n cáº§u yáº¿u do lo ngáº¡i kinh táº¿ vÃ  dá»‹ch bá»‡nh.", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    """F12: Nhu Cáº§u ToÃ n Cáº§u (Global Demand) - Ai Cáº­p, áº¢ Ráº­p, Trung Quá»‘c..."""
    ov    = manual_overrides.get("F12_Global_Demand", {})
    score = ov.get("score", 5)
    note  = ov.get("note", "")
    return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thá»§ cÃ´ng"), "status": "manual"}


def score_f5_export_sales(sales_data, commodity="ZW"):
    """F5: US Weekly Export Sales â€” dÃ¹ng dá»¯ liá»‡u chi tiáº¿t tá»« fundamental_data.json (ZW.export_sales_weekly)."""
    filepath_fund = OUTPUT_DIR / "fundamental_data.json"
    filepath_sale = OUTPUT_DIR / "export_sales.json"
    last_up = get_file_mtime(filepath_fund) if filepath_fund.exists() else get_file_mtime(filepath_sale)

    # Æ¯u tiÃªn láº¥y tá»« fundamental_data.json (Ä‘á»§ hÆ¡n: WoW%, YoY%, lÅ©y káº¿)
    fund_data_local = load_json(filepath_fund)
    try:
        if fund_data_local:
            zw_f = fund_data_local.get(commodity, {})
            es   = zw_f.get("export_sales_weekly", {})
            if es:
                latest_str  = es.get("latest_net_sales", "")   # "313.5 nghÃ¬n táº¥n"
                prev_str    = es.get("previous_net_sales", "")  # "402.5 nghÃ¬n táº¥n"
                wow_pct     = float(es.get("pct_change", 0))    # -22.11
                yoy_pct     = float(es.get("yoy_pct", 0))       # -24.4
                accum       = es.get("accumulated_sales", "")   # "4.909 triá»‡u táº¥n"
                action      = es.get("action", "")              # "BEARISH"
                week_end    = es.get("week_ending", "")

                # TÃ¡ch sá»‘ tá»« chuá»—i nhÆ° "313.5 nghÃ¬n táº¥n"
                import re as _re
                nums = _re.findall(r"[-\d\.,]+", latest_str.replace(",", "."))
                net_k = float(nums[0]) if nums else 0.0

                # Cháº¥m Ä‘iá»ƒm dá»±a trÃªn cáº£ 3 chiá»u: WoW, YoY, vÃ  khá»‘i lÆ°á»£ng tuyá»‡t Ä‘á»‘i
                #  Tá»‘t (Bullish > ZW): net_k cao, WoW tÄƒng, YoY tÄƒng â†’ Ä‘iá»ƒm cao
                score_vol = 9 if net_k > 500 else (7 if net_k > 300 else (5 if net_k > 100 else (4 if net_k > 0 else 2)))
                score_wow = 8 if wow_pct > 20 else (6 if wow_pct > 0 else (4 if wow_pct > -20 else 2))
                score_yoy = 9 if yoy_pct > 10 else (6 if yoy_pct > 0 else (4 if yoy_pct > -15 else 2))
                score = round((score_vol * 0.4 + score_wow * 0.3 + score_yoy * 0.3))
                score = max(1, min(10, score))

                raw_val    = f"{net_k:+.1f}k MT | WoW:{wow_pct:+.1f}% | YoY:{yoy_pct:+.1f}%"
                raw_detail = f"Tuáº§n {week_end} | LÅ©y káº¿: {accum} | Prev: {prev_str}"
                return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}

        # Fallback vá» export_sales.json
        if not sales_data:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "ChÆ°a cÃ³ dá»¯ liá»‡u Export Sales", "last_updated": last_up, "status": "error"}
        zw  = sales_data.get("commodities", {}).get(commodity, {})
        net = float(zw.get("current_mt", 0)) / 1000
        pct = float(zw.get("pct_change", 0))
        score = 9 if net > 500 else (7 if net > 300 else (5 if net > 100 else (4 if net > 0 else 3)))
        return {"score": score, "raw_value": f"{net:+.0f}k MT | WoW:{pct:+.1f}%", "raw_detail": "Net Sales USDA (export_sales.json)", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}

def score_f6_us_stocks(fund_data, commodity="ZW"):
    if commodity == "ZC": return {"score": 1, "raw_value": "2.1 tá»· dáº¡ (+35% YoY)", "raw_detail": "Tá»“n kho NgÃ´ Má»¹ 2.1 tá»· dáº¡ (BÃ¡o cÃ¡o 30/09). TÄƒng sá»‘c 35%. Ãp lá»±c cá»±c Ä‘oan. MEGA BEARISH", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    """F6: US Ending Stocks â€” tá»± tÃ­nh MoM tá»« current/previous + dÃ¹ng pct_vs_prev_report Ä‘á»ƒ cháº¥m Ä‘iá»ƒm."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u", "last_updated": last_up, "status": "error"}
    try:
        import re as _re
        zw      = fund_data.get("ZW", fund_data)
        us_stk  = zw.get("us_ending_stocks", {})
        current = us_stk.get("current", None)          # "717 triá»‡u bushels (2026/27)"
        prev    = us_stk.get("previous", None)         # "722 triá»‡u bushels (2026/27)"
        # pct_vs_prev_report = so sÃ¡nh Aug vs Jul WASDE (Ä‘Ã¡ng tin cáº­y)
        pct_mom = float(us_stk.get("pct_vs_prev_report", 0) or 0)
        cur_mon = us_stk.get("current_month", "")
        pre_mon = us_stk.get("previous_month", "")
        logic   = us_stk.get("logic", "")

        if current is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiáº¿u trÆ°á»ng us_ending_stocks.current", "last_updated": last_up, "status": "error"}

        # Tá»± tÃ­nh MoM thá»±c tá»« sá»‘ liá»‡u (Ä‘á»ƒ trÃ¡nh phá»¥ thuá»™c vÃ o pct_change cÃ³ thá»ƒ sai)
        nums_cur = _re.findall(r"[\d\.,]+", str(current))
        nums_pre = _re.findall(r"[\d\.,]+", str(prev)) if prev else []
        cur_num  = float(str(nums_cur[0]).replace(",", "")) if nums_cur else None
        pre_num  = float(str(nums_pre[0]).replace(",", "")) if nums_pre else None
        cur_str  = nums_cur[0] if nums_cur else "?"
        pre_str  = nums_pre[0] if nums_pre else "?"

        # TÃ­nh láº¡i MoM thá»±c náº¿u cÃ³ Ä‘á»§ dá»¯ liá»‡u sá»‘ vÃ  LUÃ”N LUÃ”N tin tÆ°á»Ÿng káº¿t quáº£ tÃ­nh toÃ¡n nÃ y
        if cur_num is not None and pre_num is not None and pre_num > 0:
            pct_mom_calc = round((cur_num - pre_num) / pre_num * 100, 1)
            pct_mom = pct_mom_calc

        # Cháº¥m Ä‘iá»ƒm dá»±a trÃªn MoM WASDE (tá»“n kho giáº£m = Bullish cho ZW)
        # pct_mom Ã¢m â†’ tá»“n kho giáº£m â†’ Bullish â†’ Ä‘iá»ƒm cao
        if   pct_mom >  5: score = 2   # Tá»“n kho tÄƒng máº¡nh â†’ Bearish
        elif pct_mom >  0: score = 4   # Tá»“n kho tÄƒng nháº¹ â†’ hÆ¡i Bearish
        elif pct_mom > -3: score = 6   # Giáº£m nháº¹ â†’ trung láº­p
        elif pct_mom > -8: score = 8   # Giáº£m vá»«a â†’ Bullish
        else:              score = 10  # Giáº£m máº¡nh â†’ ráº¥t Bullish
        score = max(1, min(10, score))

        raw_val    = f"{cur_str} Mbu | WASDE {cur_mon}: {pct_mom:+.1f}% ({cur_str} â† {pre_str} Mbu)"
        raw_detail = logic[:80] if logic else f"WASDE {cur_mon} vs {pre_mon}"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}

def score_f7_global_stocks(fund_data, commodity="ZW"):
    """F7: Global Ending Stocks â€” tá»± tÃ­nh MoM tá»« current/previous + logic text."""
    filepath = OUTPUT_DIR / "fundamental_data.json"
    last_up  = get_file_mtime(filepath)
    if not fund_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u", "last_updated": last_up, "status": "error"}
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
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiáº¿u trÆ°á»ng global_ending_stocks.current", "last_updated": last_up, "status": "error"}

        nums_cur = _re.findall(r"[\d\.,]+", str(current))
        nums_pre = _re.findall(r"[\d\.,]+", str(prev)) if prev else []
        cur_num  = float(str(nums_cur[0]).replace(",", "")) if nums_cur else None
        pre_num  = float(str(nums_pre[0]).replace(",", "")) if nums_pre else None
        cur_str  = nums_cur[0] if nums_cur else "?"
        pre_str  = nums_pre[0] if nums_pre else "?"

        # Tá»± tÃ­nh MoM thá»±c vÃ  LUÃ”N LUÃ”N tin tÆ°á»Ÿng káº¿t quáº£ tÃ­nh toÃ¡n nÃ y
        if cur_num is not None and pre_num is not None and pre_num > 0:
            pct_mom_calc = round((cur_num - pre_num) / pre_num * 100, 2)
            pct_mom = pct_mom_calc

        # Tá»“n kho toÃ n cáº§u: giáº£m = Bullish ZW
        if   pct_mom >  3: score = 2
        elif pct_mom >  0: score = 4
        elif pct_mom > -2: score = 6
        elif pct_mom > -5: score = 8
        else:              score = 10
        score = max(1, min(10, score))

        raw_val    = f"{cur_str} Mmt | WASDE {cur_mon}: {pct_mom:+.2f}% ({cur_str} â† {pre_str} Mmt)"
        raw_detail = logic[:80] if logic else f"WASDE {cur_mon} vs {pre_mon}"
        return {"score": score, "raw_value": raw_val, "raw_detail": raw_detail, "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:80], "last_updated": last_up, "status": "error"}


def score_f8_geopolitics(manual_overrides, commodity="ZW"):
    if commodity == "ZC": return {"score": 5, "raw_value": "Logistics & Biá»ƒn Äen", "raw_detail": "Chiáº¿n sá»± Biá»ƒn Äen giáº£m nhiá»‡t, táº¯c ngháº½n váº­n táº£i khÃ´ng cÃ²n lÃ  Ä‘iá»ƒm nÃ³ng.", "last_updated": "Hiá»‡n táº¡i", "status": "manual"}
    """F8: Geopolitics & Logistics - manual."""
    ov = manual_overrides.get("F8_Geopolitics", {})
    score = ov.get("score", 5)
    note = ov.get("note", "")
    return {"score": score, "raw_value": f"PhÃ¢n tÃ­ch ChuyÃªn gia: {score}/10", "raw_detail": note, "last_updated": ov.get("updated_at", "Thá»§ cÃ´ng"), "status": "manual"}

def score_f9_dxy(macro_data, commodity="ZW"):
    """F9: DXY Index."""
    filepath = OUTPUT_DIR / "macro_data.json"
    last_up  = get_file_mtime(filepath)
    if not macro_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u macro", "last_updated": last_up, "status": "error"}
    try:
        dxy_d = macro_data.get("dxy", macro_data.get("DXY", {}))
        dxy   = dxy_d.get("price", None)
        pct   = dxy_d.get("pct", 0)
        if dxy is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiáº¿u giÃ¡ DXY", "last_updated": last_up, "status": "error"}
        if dxy >= 104: score = 2
        elif dxy >= 102: score = 3
        elif dxy >= 100.5: score = 4
        elif dxy >= 99: score = 5
        elif dxy >= 97: score = 7
        else: score = 9
        return {"score": score, "raw_value": f"DXY {dxy:.2f} ({pct:+.2f}%)", "raw_detail": "USD Index â€” Sá»©c máº¡nh Ä‘á»“ng Ä‘Ã´", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f10_oil(macro_data, commodity="ZW"):
    """F10: Crude Oil WTI/Brent."""
    filepath = OUTPUT_DIR / "macro_data.json"
    last_up  = get_file_mtime(filepath)
    if not macro_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u macro", "last_updated": last_up, "status": "error"}
    try:
        brent_d = macro_data.get("brent", macro_data.get("WTI", macro_data.get("wti", {})))
        price   = brent_d.get("price", None)
        pct     = brent_d.get("pct", 0)
        if price is None:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "Thiáº¿u giÃ¡ Brent/WTI", "last_updated": last_up, "status": "error"}
        if price < 70: score = 2
        elif price < 80: score = 5
        elif price < 90: score = 8
        else: score = 10
        if commodity == "ZC":
            return {"score": score, "raw_value": f"Brent ${price:.2f} ({pct:+.2f}%)", "raw_detail": "40% NgÃ´ náº¥u cá»“n. Dáº§u giáº£m kÃ©o NgÃ´ sáº­p (MEGA BEARISH).", "last_updated": last_up, "status": "ok"}
        return {"score": score, "raw_value": f"Brent ${price:.2f} ({pct:+.2f}%)", "raw_detail": "Crude Oil -> CÆ°á»›c tÃ u & PhÃ¢n bÃ³n", "last_updated": last_up, "status": "ok"}
    except Exception as e:
        return {"score": 5, "raw_value": "N/A", "raw_detail": str(e)[:50], "last_updated": last_up, "status": "error"}

def score_f11_cot(cot_data, commodity="ZW"):
    """F11: COT Net Position."""
    filepath = OUTPUT_DIR / "cot_data.json"
    last_up  = get_file_mtime(filepath)
    if not cot_data:
        return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng cÃ³ dá»¯ liá»‡u COT", "last_updated": last_up, "status": "error"}
    try:
        # Navigate to ZW data
        commodities = cot_data.get("commodities", {})
        zw_data = None
        for code, data in commodities.items():
            if data.get("commodity") == commodity:
                zw_data = data
                break
        if not zw_data:
            return {"score": 5, "raw_value": "N/A", "raw_detail": "KhÃ´ng tÃ¬m tháº¥y ZW trong COT", "last_updated": last_up, "status": "error"}
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


def calculate_macro_score(commodity="ZW"):
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

    if commodity == "ZC":
        weights["F10"] = 16
        weights["F6"] = 14
        weights["F3"] = 12
        weights["F2"] = 10
        weights["F9"] = 8
        weights["F4S"] = 8
        weights["F4"] = 7
        weights["F11"] = 7
        weights["F5"] = 5
        weights["F7"] = 4
        weights["F12"] = 4
        weights["F1"] = 3
        weights["F8"] = 2
        weights["F2W"] = 0
        
        tot = sum(weights.values())
        for k in weights: weights[k] = round((weights[k]/tot)*100, 1)


    # Calculate per-factor rich data
    factor_results = {
        "F1":  score_f1_blacksea(manual_overrides, bs_data, commodity),
        "F2":  score_f2_us_production(fund_data, commodity),
        "F2W": score_f2w_us_weather(manual_overrides, fund_data, commodity),
        "F3":  score_f3_other_supply(manual_overrides, commodity),
        "F4":  score_f4_weather_sh(manual_overrides, commodity),
        "F4S": score_f4s_supply_sh(manual_overrides, commodity),
        "F5":  score_f5_export_sales(sales_data, commodity),
        "F6":  score_f6_us_stocks(fund_data, commodity),
        "F7":  score_f7_global_stocks(fund_data, commodity),
        "F8":  score_f8_geopolitics(manual_overrides, commodity),
        "F9":  score_f9_dxy(macro_data, commodity),
        "F10": score_f10_oil(macro_data, commodity),
        "F11": score_f11_cot(cot_data, commodity),
        "F12": score_f12_global_demand(manual_overrides, commodity),
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
            "last_updated":  result.get("last_updated", "â€”"),
            "status":        result.get("status", "error"),
        }

    final_score_100 = round(total_score_10 * 10, 1)

    if final_score_100 < 30:   trend = "Strong Bearish â€” Giáº£m Ráº¥t Máº¡nh"
    elif final_score_100 < 45: trend = "Slightly Bearish â€” Giáº£m Nháº¹"
    elif final_score_100 < 55: trend = "Sideways â€” Äi Ngang"
    elif final_score_100 < 70: trend = "Slightly Bullish â€” TÄƒng Nháº¹"
    else:                      trend = "Strong Bullish â€” TÄƒng Máº¡nh"

    result = {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month":       current_month,
        "total_score": final_score_100,
        "trend":       trend,
        "breakdown":   breakdown,
    }

    with open(OUTPUT_DIR / f"macro_scores_{commodity.lower()}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    try:
        print(f"[MACRO ENGINE] {commodity} Month {current_month}: {final_score_100}/100 OK")
    except:
        print(f"[MACRO ENGINE] {commodity} Done.")


if __name__ == "__main__":
    calculate_macro_score("ZW")
    calculate_macro_score("ZC")
