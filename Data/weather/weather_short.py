"""
Data/weather/weather_short.py
=============================
Thu thap du lieu thoi tiet ngan han (3 ngay toi) bang Open-Meteo API (Mien phi).
Quet 3 ngay/lan.
Cac vung: US Corn Belt (Iowa), US Wheat Belt (Kansas), Brazil (Mato Grosso), Russia (Rostov).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import json
import datetime
import requests
from data_config import OUTPUT_DIR, update_status

WEATHER_DATA_FILE = OUTPUT_DIR / "weather_short.json"

REGIONS = {
    # ── NHÓM 1: HOA KỲ – TOP WHEAT STATES ──────────────────────────────────
    "US_Wheat_Kansas":      {"lat": 38.50, "lon": -98.00,  "desc": "Lúa mì HRW",
                             "state": "KS", "crop": "wheat", "country": "US"},
    "US_Wheat_Montana":     {"lat": 46.87, "lon": -110.36, "desc": "Lúa mì HRS",
                             "state": "MT", "crop": "wheat", "country": "US"},
    "US_Wheat_Washington":  {"lat": 47.00, "lon": -120.50, "desc": "Lúa mì SW",
                             "state": "WA", "crop": "wheat", "country": "US"},
    "US_Wheat_Oklahoma":    {"lat": 35.50, "lon": -97.50,  "desc": "Lúa mì HRW",
                             "state": "OK", "crop": "wheat", "country": "US"},
    "US_Wheat_NorthDakota": {"lat": 47.55, "lon": -101.00, "desc": "Durum+Spring Wheat",
                             "state": "ND", "crop": "wheat", "country": "US"},
    # Bổ sung thêm bang lúa mì
    "US_Wheat_Texas":       {"lat": 31.50, "lon": -99.00,  "desc": "Lúa mì HRW South Plains",
                             "state": "TX", "crop": "wheat", "country": "US"},
    "US_Wheat_SouthDakota": {"lat": 44.50, "lon": -100.30, "desc": "Spring Wheat + Durum",
                             "state": "SD", "crop": "wheat", "country": "US"},
    "US_Wheat_Colorado":    {"lat": 39.00, "lon": -105.50, "desc": "Lúa mì HRW",
                             "state": "CO", "crop": "wheat", "country": "US"},
    "US_Wheat_Idaho":       {"lat": 44.00, "lon": -114.50, "desc": "Lúa mì SW + HRW",
                             "state": "ID", "crop": "wheat", "country": "US"},

    # ── NHÓM 2: HOA KỲ – TOP CORN STATES ───────────────────────────────────
    "US_Corn_Iowa":         {"lat": 41.58, "lon": -93.62,  "desc": "Ngô, Đậu tương",
                             "state": "IA", "crop": "corn", "country": "US"},
    "US_Corn_Illinois":     {"lat": 40.00, "lon": -89.00,  "desc": "Ngô, Đậu tương",
                             "state": "IL", "crop": "corn", "country": "US"},
    "US_Corn_Nebraska":     {"lat": 41.50, "lon": -99.90,  "desc": "Ngô (Feedlot)",
                             "state": "NE", "crop": "corn", "country": "US"},
    "US_Corn_Minnesota":    {"lat": 44.95, "lon": -93.10,  "desc": "Ngô, Đậu tương",
                             "state": "MN", "crop": "corn", "country": "US"},
    "US_Corn_Indiana":      {"lat": 40.27, "lon": -86.13,  "desc": "Ngô, Đậu tương",
                             "state": "IN", "crop": "corn", "country": "US"},
    # Bổ sung thêm bang ngô
    "US_Corn_Ohio":         {"lat": 40.40, "lon": -82.90,  "desc": "Ngô, Đậu tương",
                             "state": "OH", "crop": "corn", "country": "US"},
    "US_Corn_Wisconsin":    {"lat": 44.50, "lon": -90.00,  "desc": "Ngô, Sữa (Dairy Corn)",
                             "state": "WI", "crop": "corn", "country": "US"},
    "US_Corn_Missouri":     {"lat": 38.50, "lon": -92.50,  "desc": "Ngô, Đậu tương",
                             "state": "MO", "crop": "corn", "country": "US"},
    "US_Corn_Michigan":     {"lat": 44.00, "lon": -85.00,  "desc": "Ngô, Đậu tương",
                             "state": "MI", "crop": "corn", "country": "US"},

    # ── NHÓM 3: NAM MỸ ──────────────────────────────────────────────────────
    "Brazil_MatoGrosso":    {"lat": -12.68, "lon": -55.98, "desc": "Đậu tương, Ngô Safrinha",
                             "country": "BRA", "crop": "soy"},
    "Argentina_Pampas":     {"lat": -35.00, "lon": -60.00, "desc": "Lúa mì, Ngô, Đậu tương",
                             "country": "ARG", "crop": "wheat"},

    # ── NHÓM 4: CHÂU ÂU & BIỂN ĐEN ─────────────────────────────────────────
    "Russia_Rostov":        {"lat": 47.23, "lon": 39.72,   "desc": "Lúa mì (XK số 1 TG)",
                             "country": "RUS", "crop": "wheat"},
    "Ukraine_Poltava":      {"lat": 49.59, "lon": 34.55,   "desc": "Ngô, Lúa mì",
                             "country": "UKR", "crop": "wheat"},
    "EU_France_Centre":     {"lat": 48.00, "lon":  2.00,   "desc": "Lúa mì (EU XK số 2)",
                             "country": "FRA", "crop": "wheat"},

    # ── NHÓM 5: CHÂU ÚC ─────────────────────────────────────────────────────
    "Australia_NSW":        {"lat": -32.00, "lon": 147.00, "desc": "Lúa mì",
                             "country": "AUS", "crop": "wheat"},
}

def fetch_weather_short():
    print("\n  -- WEATHER (SHORT-TERM) ---")
    results = {
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Open-Meteo API",
        "regions": {}
    }
    
    success_count = 0
    for region, coords in REGIONS.items():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=temperature_2m_max,precipitation_sum&forecast_days=3&timezone=auto"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            daily = data.get("daily", {})
            times = daily.get("time", [])
            t_max = daily.get("temperature_2m_max", [])
            precip = daily.get("precipitation_sum", [])
            
            forecast = []
            total_rain = 0
            for i in range(len(times)):
                forecast.append({
                    "date": times[i],
                    "max_temp_C": t_max[i],
                    "precip_mm": precip[i]
                })
                total_rain += precip[i] if precip[i] is not None else 0
                
            # Phan tich nhanh rui ro (Hardcoded rules)
            risk = "Binh thuong (Mild/Normal)"
            if total_rain < 2.0 and max(t_max) > 32:
                risk = "Rui ro kho han & nang nong (Dry & Hot)"
            elif total_rain > 30.0:
                risk = "Rui ro ngap ung (Heavy Rain)"
            elif 2.0 <= total_rain <= 30.0 and max(t_max) <= 32:
                risk = "Thuan loi (Favorable)"
                
            results["regions"][region] = {
                "desc": coords.get("desc", ""),
                "forecast": forecast,
                "total_3d_rain_mm": round(total_rain, 1),
                "max_temp_C": max(t_max),
                "risk_assessment": risk
            }
            print(f"  [OK] {region} ({coords.get('desc','')}): {risk} (Rain: {total_rain:.1f}mm)")
            success_count += 1
        except Exception as e:
            print(f"  [ERR] {region}: {e}")
            results["regions"][region] = {"error": str(e)}
            
    with open(WEATHER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    update_status("weather_short", "OK" if success_count == len(REGIONS) else "PARTIAL", f"{success_count}/{len(REGIONS)} fetched")
    return success_count > 0

if __name__ == "__main__":
    fetch_weather_short()
