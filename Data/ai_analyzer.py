"""
Data/ai_analyzer.py
===================
Phân tích thị trường CBOT tự động bằng Google Gemini API.
Dùng framework chuyên sâu: SMC + Mùa Vụ + COT + ENSO + Lúa Mì Nga.

Chạy độc lập:
    python Data/ai_analyzer.py
Hoặc được gọi từ Streamlit (nút 🧠 AI Phân Tích) hoặc bộ lịch tự động.
"""
import os
import json
import requests
import datetime
from pathlib import Path

DATA_DIR          = Path(__file__).parent
OUTPUT_DIR        = DATA_DIR / "output"
API_KEY_FILE      = DATA_DIR / "api_key.txt"
AI_ANALYSIS_FILE  = OUTPUT_DIR / "ai_analysis.json"
FUNDAMENTAL_FILE  = OUTPUT_DIR / "fundamental_data.json"
ACREAGE_FILE      = OUTPUT_DIR / "acreage_data.json"
COT_FILE          = OUTPUT_DIR / "cot_data.json"
WEATHER_S_FILE    = OUTPUT_DIR / "weather_short.json"
MACRO_FILE        = OUTPUT_DIR / "macro_data.json"
EXPORT_FILE       = OUTPUT_DIR / "export_sales.json"
BLACKSEA_FILE     = OUTPUT_DIR / "blacksea_wheat.json"

# ── Thứ tự ưu tiên lấy API key ──────────────────────────────────────────────
def get_api_key():
    # 1. Streamlit Secrets (Online)
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    # 2. Biến môi trường (được truyền từ subprocess khi chạy Online)
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
    # 3. File txt (Local)
    if API_KEY_FILE.exists():
        key = API_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    return None


def _load_json(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def analyze():
    print("\n=======================================================")
    print("  CBOT AI ANALYZER  –  Phân tích chuyên sâu SMC + Mùa Vụ + COT + ENSO")
    print("=======================================================")

    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key. Lưu vào Data/api_key.txt hoặc cấu hình Streamlit Secrets.")
        return False

    if not FUNDAMENTAL_FILE.exists():
        print("  [WARN] Chưa có fundamental_data.json. Chạy fetch_prices.py trước.")
        return False

    print("  [+] Đang đọc toàn bộ dữ liệu thị trường...")
    fund     = _load_json(FUNDAMENTAL_FILE)
    acreage  = _load_json(ACREAGE_FILE)
    cot      = _load_json(COT_FILE)
    weather  = _load_json(WEATHER_S_FILE)
    macro    = _load_json(MACRO_FILE)
    exports  = _load_json(EXPORT_FILE)
    blacksea = _load_json(BLACKSEA_FILE)
    signals  = _load_json(OUTPUT_DIR / "last_signals.json")
    meta     = _load_json(OUTPUT_DIR / "contracts_meta.json")

    # ── Trích xuất số liệu cốt lõi (thay vì dump JSON thô) ──────────────────
    zw = fund.get("ZW", {})
    zc = fund.get("ZC", {})

    # Giá từ contracts_meta (cập nhật H1)
    zw_close = meta.get("ZW", {}).get("liquidity", {}).get("today_close", "N/A")
    zc_close = meta.get("ZC", {}).get("liquidity", {}).get("today_close", "N/A")
    zw_trend = meta.get("ZW", {}).get("liquidity", {}).get("trend", zw.get("swing_trend", "N/A"))
    zc_trend = meta.get("ZC", {}).get("liquidity", {}).get("trend", zc.get("swing_trend", "N/A"))
    zw_vol   = meta.get("ZW", {}).get("liquidity", {}).get("today_volume", "N/A")
    zc_vol   = meta.get("ZC", {}).get("liquidity", {}).get("today_volume", "N/A")
    zw_oi    = meta.get("ZW", {}).get("liquidity", {}).get("today_oi", "N/A")
    zc_oi    = meta.get("ZC", {}).get("liquidity", {}).get("today_oi", "N/A")

    # Tín hiệu ICT MSS mới nhất
    zw_sig   = signals.get("ZW", {})
    zc_sig   = signals.get("ZC", {})

    # COT
    def _cot(code):
        c = cot.get(code, {})
        if not c:
            for v in cot.values():
                if isinstance(v, dict) and v.get("commodity") == code:
                    c = v; break
        return c
    cot_zw = _cot("ZW")
    cot_zc = _cot("ZC")

    # Thời tiết tóm tắt
    wx_alerts = []
    if isinstance(weather, dict):
        for k, v in weather.items():
            if isinstance(v, dict) and v.get("alert"):
                wx_alerts.append(f"{k}: {v.get('alert','')[:80]}")
            elif isinstance(v, list):
                for item in v[:2]:
                    if isinstance(item, dict) and item.get("summary"):
                        wx_alerts.append(f"{k}: {str(item.get('summary',''))[:80]}")
                        break
    wx_str = "\n".join(wx_alerts[:5]) if wx_alerts else "Không có cảnh báo đặc biệt"

    # Mùa vụ
    zw_harvest = zw.get("harvest_progress", {})
    zc_harvest = zc.get("harvest_progress", {})
    zw_harv_str = f"Mỹ: {zw_harvest.get('latest','N/A')} (kỳ trước: {zw_harvest.get('previous','N/A')})" if isinstance(zw_harvest, dict) else str(zw_harvest)
    zc_harv_str = f"Mỹ: {zc_harvest.get('latest','N/A')} (kỳ trước: {zc_harvest.get('previous','N/A')})" if isinstance(zc_harvest, dict) else str(zc_harvest)

    # Acreage
    zw_area = acreage.get("ZW", {}).get("planted_acres", acreage.get("ZW", {}).get("latest", "N/A"))
    zc_area = acreage.get("ZC", {}).get("planted_acres", acreage.get("ZC", {}).get("latest", "N/A"))

    # Blacksea tóm tắt
    bs_news = blacksea.get("news", [])
    bs_str = "; ".join([n.get("title", "")[:80] for n in bs_news[:3]]) if bs_news else "Không có tin mới"

    # DCA zones
    zw_dca = zw.get("dca_brackets", "N/A")
    zc_dca = zc.get("dca_brackets", "N/A")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""Bạn là Chuyên gia Giao dịch Định lượng (Quant) Nông sản CBOT, \
phân tích theo SMC/ICT + Mùa Vụ + ENSO + Lúa Mì Nga.

Thời điểm: {now_str} (Giờ VN)

=== KIẾN THỨC NỀN TẢNG ===
[Mùa Vụ 2026]
- ZW: Diện tích -6% (USDA 30/06) → Q4 Bullish mạnh. Đáy 1: Cuối T6/Đầu T7 khi gặt 40-50%. Đáy 2: Cuối T8. DCA lý tưởng: 590-610 cents (Áp dụng cho kỳ hạn ZWZ6 T12, vì có Contango +15-25c so với tháng 9).
- ZC: Tồn kho +14% YoY, diện tích -3%, ngập lũ Midwest. DCA: 436-445 cents.

[SMC/ICT] Judas Swing T2-T3. MSS = nến H1/H4 vượt R1/S1 + FVG. Entry tại OTE 0.618-0.786, H1/M15.

[ENSO] El Niño xác suất cao → Bullish ZW. Khi ENSO >70%: ưu tiên rủi ro vĩ mô.

[Lúa Mì Nga U-Shape 2026]
- Đầu-Giữa T7: Nga xả lũ + Mỹ gặt lúa đông → NGHIÊM CẤM All-in Long (chỉ dò 20-30% vốn).
- Cuối T7-Giữa T8 GOLDEN ZONE: Đáy Tuyệt Đối → Dồn hỏa lực DCA.
- Nửa sau T8-T9: Điểm Uốn → Bứt phá mạnh.

=== DỮ LIỆU THỰC TẾ ===
[Giá & Volume & OI - H1 mới nhất]
ZW: Giá={zw_close}c | Volume={zw_vol} | OI={zw_oi} | Xu hướng: {zw_trend}
ZC: Giá={zc_close}c | Volume={zc_vol} | OI={zc_oi} | Xu hướng: {zc_trend}

[Tín hiệu ICT MSS mới nhất (H1)]
ZW: {zw_sig.get('setup_type','N/A')} | Entry={zw_sig.get('setup_entry_range','N/A')} | Lúc={zw_sig.get('timestamp','N/A')}
ZC: {zc_sig.get('setup_type','N/A')} | Entry={zc_sig.get('setup_entry_range','N/A')} | Lúc={zc_sig.get('timestamp','N/A')}

[COT - Dòng tiền tổ chức]
ZW: Net={cot_zw.get('net_position','N/A')} | Thay đổi={cot_zw.get('change','N/A')} | Góc phần tư={cot_zw.get('quadrant','N/A')}
ZC: Net={cot_zc.get('net_position','N/A')} | Thay đổi={cot_zc.get('change','N/A')} | Góc phần tư={cot_zc.get('quadrant','N/A')}

[Tiến độ Thu hoạch]
ZW: {zw_harv_str}
ZC: {zc_harv_str}

[Diện tích Gieo trồng 2026]
ZW: {zw_area} | ZC: {zc_area}

[Vĩ Mô]
DXY={macro.get('dxy',{}).get('price','N/A')} ({macro.get('dxy',{}).get('pct','N/A')}%) | Brent={macro.get('brent',{}).get('price','N/A')}

[Thời tiết Ngắn hạn]
{wx_str}

[Tin Biển Đen / Nga]
{bs_str}

[DCA Zones (Dài hạn)]
ZW DCA: {zw_dca} | ZC DCA: {zc_dca}

=== YÊU CẦU PHÂN TÍCH ===

### 🌽 NGÔ (ZC) — Phân Tích Hiện Tại
- **Xu Hướng Ngắn Hạn:** [Bullish/Bearish/Neutral + lý do 1 câu dựa trên giá, Volume, OI]
- **Tín Hiệu SMC:** [Tín hiệu H1 hiện tại? Có Judas Swing/MSS/FVG không?]
- **Vùng Hành Động:** [Entry/DCA ở đâu? LƯU Ý ĐẶC BIỆT: Phải ghi rõ giá DCA là của "Hợp đồng tháng 12", không phải tháng 9. S1/R1 quan trọng?]
- **Rủi Ro:** [1 câu]

### 🌾 LÚA MÌ (ZW) — Phân Tích Hiện Tại
- **Vị Trí Mùa Vụ:** [Đang ở giai đoạn nào U-Shape 2026? Đáy 1/Golden Zone/Điểm Uốn?]
- **Xu Hướng Ngắn Hạn:** [Bullish/Bearish/Neutral + lý do dựa trên giá, tiến độ gặt, COT]
- **Tín Hiệu SMC:** [Tín hiệu H1 hiện tại? Có Judas Swing/MSS/FVG không?]
- **Yếu Tố Nga:** [Nga đang ở pha nào? Ảnh hưởng giá trần?]
- **Vùng Hành Động:** [Entry/DCA? LƯU Ý ĐẶC BIỆT: Phải ghi rõ giá DCA là của "Hợp đồng tháng 12", không phải tháng 9. S1/R1 quan trọng?]
- **Rủi Ro:** [1 câu]

### ⚡ NHẬN ĐỊNH TỔNG THỂ
- [2-3 câu sắc bén: Nên làm gì với ZW và ZC trong 24-48h tới?]

KHÔNG giải thích lý thuyết. Chỉ kết luận dựa trên số liệu thực tế.
"""

    # Thử các model theo thứ tự ưu tiên (dùng đúng tên theo API)
    models = [
        "gemini-2.5-flash",             # Full power, ổn định nhất
        "gemini-2.0-flash",             # Fallback
    ]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 4096}
    }

    print("  [+] Đang gửi Prompt tới Google Gemini API...")
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                res_json = response.json()
                text_output = (
                    res_json.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                if text_output:
                    result_data = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "model": model,
                        "analysis": text_output.strip()
                    }
                    with open(AI_ANALYSIS_FILE, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    print(f"  [OK] Phân tích AI thành công! Model: {model} → ai_analysis.json")
                    return True
                else:
                    print(f"  [WARN] Model {model} trả về rỗng.")
            else:
                err_msg = response.json().get("error", {}).get("message", response.text[:100])
                print(f"  [WARN] Model {model}: HTTP {response.status_code} — {err_msg}")
        except Exception as e:
            print(f"  [WARN] Model {model} lỗi: {e}")

    print("  [ERR] Tất cả model đều thất bại. Kiểm tra lại API Key.")
    return False


if __name__ == "__main__":
    analyze()
