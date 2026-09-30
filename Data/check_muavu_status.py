"""
Data/check_muavu_status.py
Kiểm tra trạng thái từng mục dữ liệu của trang Mùa Vụ và ghi ra muavu_status.json
"""
import sys, os, json, csv
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR   = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
STATUS_FILE = OUTPUT_DIR / "muavu_status.json"

def age_str(ts_str):
    """Tính khoảng cách thời gian từ timestamp string"""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(ts_str[:16], fmt[:len(ts_str[:16])])
            diff = datetime.now() - dt
            h = int(diff.total_seconds() // 3600)
            if h < 1: return "vừa cập nhật"
            if h < 24: return f"{h} giờ trước"
            return f"{diff.days} ngày trước"
        except: pass
    return "?"

def check_json(filename, *keys):
    """Kiểm tra xem file JSON có tồn tại và truy cập nested keys không"""
    p = OUTPUT_DIR / filename
    if not p.exists():
        return None, "❌ File không tồn tại"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        val = d
        for k in keys:
            val = val[k]
        return val, "✅"
    except KeyError as e:
        return None, f"⚠️ Thiếu key: {e}"
    except Exception as e:
        return None, f"❌ Lỗi: {str(e)[:50]}"

def run_check():
    results = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load raw files
    def load(fname):
        p = OUTPUT_DIR / fname
        if p.exists():
            try: return json.loads(p.read_text(encoding="utf-8"))
            except: return {}
        return {}

    macro      = load("macro_scores.json")
    macro_data = load("macro_data.json")
    macro_w    = load("macro_weights.json")
    cot_d      = load("cot_data.json")
    export_s   = load("export_sales.json")
    weather_l  = load("weather_long.json")
    weather_s  = load("weather_short.json")
    ai_muavu   = load("ai_muavu_analysis.json")
    fund       = load("fundamental_data.json")
    bd         = macro.get("breakdown", {})

    # ─── PHẦN 1: GLOBAL MACRO ───────────────────────────────────────
    # DXY
    dxy = macro_data.get("dxy", {})
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "Sức mạnh USD (DXY)",
        "type": "🟢 Auto",
        "value": f"{dxy.get('price', 'N/A')} ({dxy.get('pct', 0):+.2f}%)" if dxy.get('price') else "N/A",
        "status": "✅ Có data" if dxy.get("price") else "❌ Thiếu",
        "updated": age_str(macro_data.get("timestamp", "")) if macro_data.get("timestamp") else "—",
        "note": ""
    })

    # Dầu Brent
    oil = macro_data.get("brent", {})
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "Giá Dầu Brent",
        "type": "🟢 Auto",
        "value": f"{oil.get('price', 'N/A')} USD/thùng",
        "status": "✅ Có data" if oil.get("price") else "❌ Thiếu",
        "updated": age_str(macro_data.get("timestamp", "")) if macro_data.get("timestamp") else "—",
        "note": ""
    })

    # COT ZW
    cot_zw = cot_d.get("commodities", {}).get("001602", {})
    cot_est = cot_zw.get("net_estimated")
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "Dòng tiền COT – ZW",
        "type": "🟢 Auto",
        "value": f"{cot_est:,.0f} HĐ | {cot_zw.get('quadrant_estimated','N/A')}" if cot_est else "N/A",
        "status": "✅ Có data" if cot_est else "❌ Thiếu",
        "updated": age_str(cot_d.get("fetched_at","")) if cot_d.get("fetched_at") else "—",
        "note": ""
    })

    # Nhu cầu thế giới F12
    f12 = bd.get("F12", {})
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "Nhu Cầu Thế Giới (F12)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f12.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f12.get("score_1_to_10") else "❌ Thiếu",
        "updated": f12.get("last_updated", "—"),
        "note": f12.get("raw_detail","")[:60]
    })

    # Địa chính trị F8
    f8 = bd.get("F8", {})
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "Địa Chính Trị / Logistics (F8)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f8.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f8.get("score_1_to_10") else "❌ Thiếu",
        "updated": f8.get("last_updated", "—"),
        "note": f8.get("raw_detail","")[:60]
    })

    # El Nino
    enso = weather_l.get("enso_status")
    results.append({
        "group": "Phần 1: Global Macro",
        "item": "El Niño / La Niña (ENSO)",
        "type": "🟢 Auto",
        "value": enso if enso else "N/A",
        "status": "✅ Có data" if enso else "❌ Thiếu",
        "updated": age_str(weather_l.get("fetched_at","")) if weather_l.get("fetched_at") else "—",
        "note": weather_l.get("description","")[:60]
    })

    # ─── PHẦN 2: KHU VỰC ────────────────────────────────────────────
    # Mỹ – Tồn kho F2
    f2 = bd.get("F2", {})
    results.append({
        "group": "Phần 2: Bắc Bán Cầu (Mỹ)",
        "item": "Tồn kho WASDE (F2)",
        "type": "🟢 Auto",
        "value": f"Điểm {f2.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f2.get("score_1_to_10") else "❌ Thiếu",
        "updated": f2.get("last_updated", "—"),
        "note": f2.get("raw_detail","")[:60]
    })

    # Mỹ – Export Sales
    exp_zw = export_s.get("commodities", {}).get("ZW", {})
    exp_mt = exp_zw.get("current_mt")
    results.append({
        "group": "Phần 2: Bắc Bán Cầu (Mỹ)",
        "item": "Export Sales ZW",
        "type": "🟢 Auto",
        "value": f"{exp_mt:,.0f} MT (Tuần {export_s.get('current_week_ending','')})" if exp_mt else "N/A",
        "status": "✅ Có data" if exp_mt else "❌ Thiếu",
        "updated": age_str(export_s.get("fetched_at","")) if export_s.get("fetched_at") else "—",
        "note": ""
    })

    # Mỹ – Crop Progress F7
    f7 = bd.get("F7", {})
    results.append({
        "group": "Phần 2: Bắc Bán Cầu (Mỹ)",
        "item": "Tiến độ mùa vụ (F7)",
        "type": "🟢 Auto",
        "value": f"Điểm {f7.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f7.get("score_1_to_10") else "❌ Thiếu",
        "updated": f7.get("last_updated", "—"),
        "note": f7.get("raw_detail","")[:60]
    })

    # Mỹ – Thời tiết F2W
    f2w = bd.get("F2W", {})
    results.append({
        "group": "Phần 2: Bắc Bán Cầu (Mỹ)",
        "item": "Thời tiết Mỹ / HRW (F2W)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f2w.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f2w.get("score_1_to_10") else "❌ Thiếu",
        "updated": f2w.get("last_updated", "—"),
        "note": f2w.get("raw_detail","")[:60]
    })

    # EU – Nguồn cung F3
    f3 = bd.get("F3", {})
    results.append({
        "group": "Phần 2: Châu Âu (EU)",
        "item": "Nguồn cung EU (F3)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f3.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f3.get("score_1_to_10") else "❌ Thiếu",
        "updated": f3.get("last_updated", "—"),
        "note": f3.get("raw_detail","")[:60]
    })

    # Biển đen – F1 chính sách Nga
    f1 = bd.get("F1", {})
    results.append({
        "group": "Phần 2: Biển Đen (Nga & Ukraine)",
        "item": "Chính sách XK Nga (F1)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f1.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f1.get("score_1_to_10") else "❌ Thiếu",
        "updated": f1.get("last_updated", "—"),
        "note": f1.get("raw_detail","")[:60]
    })

    # Nam BC – Thời tiết F4
    f4 = bd.get("F4", {})
    results.append({
        "group": "Phần 2: Nam Bán Cầu (Úc & Argentina)",
        "item": "Thời tiết Nam BC (F4)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f4.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f4.get("score_1_to_10") else "❌ Thiếu",
        "updated": f4.get("last_updated", "—"),
        "note": f4.get("raw_detail","")[:60]
    })

    # Nam BC – Sản lượng F4S
    f4s = bd.get("F4S", {})
    results.append({
        "group": "Phần 2: Nam Bán Cầu (Úc & Argentina)",
        "item": "Sản lượng Nam BC (F4S)",
        "type": "🟡 Thủ công",
        "value": f"Điểm {f4s.get('score_1_to_10','N/A')}/10",
        "status": "✅ Có data" if f4s.get("score_1_to_10") else "❌ Thiếu",
        "updated": f4s.get("last_updated", "—"),
        "note": f4s.get("raw_detail","")[:60]
    })

    # ─── PHẦN 3: AI ANALYSIS ────────────────────────────────────────
    ai_text = ai_muavu.get("analysis","")
    results.append({
        "group": "Phần 3: AI Analysis & DCA",
        "item": "Phân tích AI (Gemini)",
        "type": "🤖 AI",
        "value": f"{len(ai_text)} ký tự" if ai_text else "Chưa có",
        "status": "✅ Đã phân tích" if ai_text else "⚠️ Chưa có – hãy ấn 'Cập Nhật'",
        "updated": ai_muavu.get("last_updated", "—"),
        "note": ""
    })

    # ZW Price
    try:
        rows = list(csv.DictReader(open(OUTPUT_DIR / "ZW_active_D1.csv", encoding="utf-8")))
        last = rows[-1]
        results.append({
            "group": "Phần 3: AI Analysis & DCA",
            "item": "Giá ZW (D1 chart)",
            "type": "🟢 Auto",
            "value": f"{float(last['Close']):.2f} cents",
            "status": "✅ Có data",
            "updated": last.get("Time","—")[:10],
            "note": f"RSI {float(last.get('RSI',0)):.1f} | ATR {float(last.get('ATR',0)):.1f}"
        })
    except Exception as e:
        results.append({
            "group": "Phần 3: AI Analysis & DCA",
            "item": "Giá ZW (D1 chart)",
            "type": "🟢 Auto",
            "value": "N/A",
            "status": f"❌ {str(e)[:40]}",
            "updated": "—",
            "note": ""
        })

    # Tổng kết
    total = len(results)
    ok    = sum(1 for r in results if "✅" in r["status"])
    warn  = sum(1 for r in results if "⚠️" in r["status"])
    err   = sum(1 for r in results if "❌" in r["status"])

    output = {
        "checked_at": now_str,
        "summary": {"total": total, "ok": ok, "warning": warn, "error": err},
        "items": results
    }

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[CHECK] {now_str} | ✅ {ok}/{total} OK | ⚠️ {warn} Warning | ❌ {err} Error")
    return output

if __name__ == "__main__":
    run_check()
