"""
Data/weather/weather_long.py
============================
Thu thap du bao thoi tiet dai han (ENSO - El Nino/La Nina) tu NOAA.
Kem theo danh gia tac dong vung mien len nong san (ZC, ZW).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import json
import datetime
import requests
import re
from html import unescape
from data_config import OUTPUT_DIR, update_status

WEATHER_LONG_FILE = OUTPUT_DIR / "weather_long.json"

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return unescape(cleantext).strip()

def get_impacts(enso_status):
    status_lower = enso_status.lower()
    if 'el ni' in status_lower or 'el nino' in status_lower:
        return [
            {"region": "Châu Úc (Australia)", "crop": "Lúa Mì (ZW)", "effect": "Tháng 9-11 (Mùa sinh trưởng). Khô hạn nghiêm trọng làm giảm 15-20% sản lượng lúa mì vụ Đông.", "severity": "Cao", "bias": "BULLISH", "color": "var(--red)"},
            {"region": "Nam Mỹ (Argentina)", "crop": "Ngô (ZC) & Lúa Mì", "effect": "Tháng 10-12 (Gieo hạt). Mưa nhiều hơn trung bình. Thuận lợi gieo trồng nhưng rủi ro nấm mốc.", "severity": "Trung bình", "bias": "BEARISH", "color": "var(--green)"},
            {"region": "Nam Mỹ (Brazil)", "crop": "Ngô Safrinha (ZC)", "effect": "Tháng 4-6 (Giai đoạn trổ cờ vụ 2). Rủi ro khô hạn cục bộ tại phía Nam gây sụt giảm năng suất.", "severity": "Cao", "bias": "BULLISH", "color": "var(--red)"},
            {"region": "Bắc Mỹ (US Plains)", "crop": "Lúa Mì (ZW)", "effect": "Tháng 9-11 (Gieo hạt vụ Đông sắp tới). Mưa ẩm hỗ trợ lúa mì mùa đông (HRW), giảm hạn hán.", "severity": "Cao", "bias": "BEARISH", "color": "var(--green)"}
        ]
    elif 'la ni' in status_lower or 'la nina' in status_lower:
        return [
            {"region": "Châu Úc (Australia)", "crop": "Lúa Mì (ZW)", "effect": "Tháng 9-11 (Sinh trưởng). Mưa nhiều, thuận lợi mùa màng, dự báo sản lượng tăng cao.", "severity": "Cao", "bias": "BEARISH", "color": "var(--green)"},
            {"region": "Nam Mỹ (Argentina)", "crop": "Ngô (ZC) & Lúa Mì", "effect": "Tháng 11-2 (Phát triển/Thụ phấn). Khô hạn nghiêm trọng. Giảm mạnh sản lượng Ngô và Lúa mì.", "severity": "Cao", "bias": "BULLISH", "color": "var(--red)"},
            {"region": "Nam Mỹ (Brazil)", "crop": "Ngô Safrinha (ZC)", "effect": "Tháng 4-6 (Phát triển vụ 2). Mưa thuận lợi, sản lượng có thể đạt kỷ lục.", "severity": "Trung bình", "bias": "BEARISH", "color": "var(--green)"},
            {"region": "Bắc Mỹ (US Plains)", "crop": "Lúa Mì (ZW)", "effect": "Tháng 9-12 (Gieo hạt). Khô hạn và lạnh giá kéo dài, ảnh hưởng xấu đến lúa mì vụ đông.", "severity": "Cao", "bias": "BULLISH", "color": "var(--red)"}
        ]
    else:
        return [
            {"region": "Toàn cầu", "crop": "Ngô & Lúa Mì", "effect": "Hiện tại đang trạng thái trung tính. Theo dõi sát các diễn biến thời tiết ngắn hạn từng vùng.", "severity": "Thấp", "bias": "NEUTRAL", "color": "var(--t2)"}
        ]

def fetch_weather_long():
    print("\n  -- WEATHER (LONG-TERM ENSO) ---")
    results = {
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "NOAA Climate Prediction Center",
        "enso_status": "Unknown",
        "description": "",
        "impacts": []
    }
    
    try:
        url = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        status_match = re.search(r'ENSO Alert System Status:\s*(?:<[^>]+>\s*)*(.*?)\s*<', resp.text, re.IGNORECASE)
        if status_match:
            results["enso_status"] = clean_html(status_match.group(1))
            
        syn = re.search(r'Synopsis:\s*(?:<[^>]+>\s*)*(.*?)\s*(?:<br|<p)', resp.text, re.IGNORECASE | re.DOTALL)
        if syn:
            results["description"] = clean_html(syn.group(1))
            
        results["impacts"] = get_impacts(results["enso_status"])
            
        print(f"  [OK] ENSO Status: {results['enso_status']}")
        
        with open(WEATHER_LONG_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        update_status("weather_long", "OK", f"Status: {results['enso_status']}")
        return True
    except Exception as e:
        print(f"  [ERR] {e}")
        update_status("weather_long", "ERROR", str(e))
        return False

if __name__ == "__main__":
    fetch_weather_long()
