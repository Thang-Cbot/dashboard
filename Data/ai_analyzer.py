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

    # Tóm lược dữ liệu giá & kỹ thuật
    zw = fund.get("ZW", {})
    zc = fund.get("ZC", {})

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""Bạn là một Chuyên gia Giao dịch Định lượng (Quant) Nông sản CBOT hàng đầu, \
chuyên phân tích theo trường phái Smart Money Concepts (SMC/ICT), kết hợp phân tích Mùa Vụ, \
Thời Tiết ENSO và Cấu Trúc Hợp Đồng Kỳ Hạn.

Thời điểm phân tích: {now_str} (Giờ Việt Nam)

=== KIẾN THỨC NỀN TẢNG (KHÔNG ĐƯỢC PHÉP BỎ QUA) ===

[MODULE 1 - MÙA VỤ 2026]
- LÚA MÌ (ZW): Diện tích gieo trồng 2026 giảm 6% (USDA 30/06) → Lò xo nén cực mạnh cho Q4.
  * Đáy 1 (Chữ W): Cuối T6/Đầu T7 khi gặt lúa đông 40-50%. Đây là điểm DCA chiến lược.
  * Đáy 2 (Thấp hơn): Cuối T8 do áp lực gặt lúa xuân (diện tích giảm 6% → đáy cạn hơn Đáy 1).
- NGÔ (ZC): Tồn kho +14% YoY nhưng diện tích giảm -3% + rủi ro ngập lũ Midwest.
  * Đáy thiết lập sớm khi gặt 5-10% (Tháng 9). Vùng DCA vững: 436-445 cents.

[MODULE 2 - SMART MONEY CONCEPTS (ICT)]
- Judas Swing (Bẫy thanh khoản): Tìm kiếm fake-down/up vào Thứ 2-3. Quét stop loss trước khi chạy hướng thật.
- MSS Breakout: Chỉ xác nhận đảo chiều khi nến H1/H4 đóng cửa vượt mạnh R1/S1 + tạo FVG.
- Entry an toàn: KHÔNG mua đuổi. Đợi hồi về OTE (0.618-0.786 Fibonacci) + lấp FVG. Khung H1/M15.

[MODULE 3 - THỜI TIẾT ENSO]
- El Niño (xác suất cao): Gây hạn hán ở Úc, Argentina, Vành đai Nam nước Mỹ → Cực Bullish ZW.
- Khi xác suất ENSO > 70%: Mọi dữ liệu cơ bản ngắn hạn PHẢI nhường chỗ cho rủi ro vĩ mô này.

[MODULE 4 - HỢP ĐỒNG KỲ HẠN]
- Dùng ZWZ6 (Tháng 12) để tính DCA dài hạn. Contango: ZW T12 cao hơn giao ngay ~15-25 cents.
- Vùng DCA lý tưởng ZW: 570-585 cents (kỳ hạn Tháng 12).

[MODULE 5 - LÚA MÌ NGA & BIỂN ĐEN (U-Shape 2026)]
- Nga = 25% thị phần xuất khẩu toàn cầu → định hình giá trần (Ceiling Price).
- QUY TẮC: Khi Nga xả hàng mạnh ra Biển Đen (T6-T7), ZC/ZW BUỘC phải giảm dù Mỹ mất mùa.
- MÁ TRẬN 2026:
  * Đầu-Giữa T7: Nga xả lũ + Mỹ gặt lúa đông → NGHIÊM CẤM All-in Long. Chỉ dò 20-30% vốn.
  * Cuối T7-Giữa T8 (GOLDEN ZONE): Cực đại áp lực cung → ĐÁY TUYỆT ĐỐI. Dồn hỏa lực DCA khi có tín hiệu SMC.
  * Nửa cuối T8-T9 (Điểm Uốn): Nga qua đỉnh xả + Mỹ lộ thiệt hại thu hoạch → Bứt phá mạnh.
- Biến số: Thiếu diesel → gặt trễ 1-2 tuần → giảm tạm thời áp lực Dump (dư địa nảy giá ngắn hạn).

=== DỮ LIỆU THỰC TẾ HIỆN TẠI ===

[GIÁ & KỸ THUẬT]
ZW (Lúa Mì): Giá={zw.get('price','N/A')} | S1={zw.get('s1','N/A')} | R1={zw.get('r1','N/A')} | RSI={zw.get('rsi','N/A')} | Xu hướng={zw.get('trend','N/A')}
ZC (Ngô):    Giá={zc.get('price','N/A')} | S1={zc.get('s1','N/A')} | R1={zc.get('r1','N/A')} | RSI={zc.get('rsi','N/A')} | Xu hướng={zc.get('trend','N/A')}

[VĨ MÔ]
```json
{json.dumps(macro, ensure_ascii=False, indent=None)}
```

[COT - DÒNG TIỀN TỔ CHỨC]
```json
{json.dumps(cot, ensure_ascii=False, indent=None)}
```

[THỜI TIẾT NGẮN HẠN]
```json
{json.dumps(weather, ensure_ascii=False, indent=None)}
```

[XUẤT KHẨU (EXPORT SALES/INSPECTIONS)]
```json
{json.dumps(exports, ensure_ascii=False, indent=None)}
```

[DIỆN TÍCH GIEO TRỒNG (USDA ACREAGE)]
```json
{json.dumps(acreage, ensure_ascii=False, indent=None)}
```

[TIN TỨC BIỂN ĐEN / LÚA MÌ NGA]
```json
{json.dumps(blacksea, ensure_ascii=False, indent=None)}
```

=== YÊU CẦU PHÂN TÍCH ===

Dựa trên 5 module kiến thức nền tảng + toàn bộ dữ liệu thực tế trên, hãy phân tích ngắn gọn, sắc bén, chính xác:

### 🌽 NGÔ (ZC) — Phân Tích Hiện Tại
- **Xu Hướng Ngắn Hạn:** [Bullish / Bearish / Neutral + Lý do 1 câu]
- **Tín Hiệu SMC:** [Có Judas Swing / MSS / FVG không? Cụ thể]
- **Vùng Hành Động:** [DCA ở đâu? Cản R1/S1 nào quan trọng?]
- **Rủi Ro Chính:** [1 câu]

### 🌾 LÚA MÌ (ZW) — Phân Tích Hiện Tại
- **Vị Trí Mùa Vụ:** [Đang ở giai đoạn nào của U-Shape 2026? Đáy 1 / Golden Zone / Điểm Uốn?]
- **Xu Hướng Ngắn Hạn:** [Bullish / Bearish / Neutral + Lý do 1 câu]
- **Tín Hiệu SMC:** [Có Judas Swing / MSS / FVG không? Cụ thể]
- **Yếu Tố Nga/Biển Đen:** [Nga đang ở pha nào? Ảnh hưởng thế nào đến giá trần?]
- **Vùng Hành Động:** [DCA ở đâu? Cản R1/S1 nào quan trọng?]
- **Rủi Ro Chính:** [1 câu]

### ⚡ NHẬN ĐỊNH TỔNG THỂ & LỜI KHUYÊN HÀNH ĐỘNG
- [2-3 câu sắc bén nhất: Nên làm gì với ZW và ZC trong 24-48h tới? Mức độ rủi ro toàn danh mục?]

KHÔNG giải thích lý thuyết, KHÔNG nói chung chung. Chỉ kết luận dựa trên số liệu thực tế và framework trên.
"""

    # Thử các model theo thứ tự ưu tiên
    models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 1500}
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
