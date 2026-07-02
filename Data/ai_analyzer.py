import os
import json
import requests
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
AI_ANALYSIS_FILE = OUTPUT_DIR / "ai_analysis.json"
FUNDAMENTAL_FILE = OUTPUT_DIR / "fundamental_data.json"
ACREAGE_FILE = OUTPUT_DIR / "acreage_data.json"

def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None

def analyze():
    print("\n=======================================================")
    print("  AI ANALYZER - TỰ ĐỘNG PHÂN TÍCH THỊ TRƯỜNG BẰNG AI")
    print("=======================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key trong Data/api_key.txt. Bỏ qua AI.")
        return False
        
    if not FUNDAMENTAL_FILE.exists():
        print("  [WARN] Chưa có fundamental_data.json để phân tích.")
        return False
        
    print("  [+] Đang đọc dữ liệu tổng hợp...")
    with open(FUNDAMENTAL_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"  [ERR] Lỗi đọc JSON fundamental: {e}")
            return False
            
    acreage_data = {}
    if ACREAGE_FILE.exists():
        try:
            with open(ACREAGE_FILE, "r", encoding="utf-8") as f:
                acreage_data = json.load(f)
        except Exception as e:
            print(f"  [WARN] Lỗi đọc acreage JSON: {e}")
            
    prompt = f"""Bạn là một Chuyên gia Giao dịch Định lượng (Quant) Nông sản CBOT. 
Dưới đây là dữ liệu tổng hợp hiện tại của thị trường (bao gồm thời tiết, báo cáo USDA, dòng tiền COT, xuất khẩu, và các mốc cản Price Action của mã Ngô (ZC) và Lúa mì (ZW)):

--- DỮ LIỆU CƠ BẢN VÀ KỸ THUẬT ---
```json
{json.dumps(data, ensure_ascii=False)}
```

--- DỮ LIỆU DIỆN TÍCH GIEO TRỒNG (PLANTED ACREAGE) ---
```json
{json.dumps(acreage_data, ensure_ascii=False)}
```

Nhiệm vụ của bạn:
Phân tích sâu chuỗi dữ liệu trên và đưa ra nhận định giao dịch cực kỳ sắc bén. 
Hãy trình bày theo định dạng sau:

### 🌽 Phân Tích Ngô (ZC)
- **🔥 Xu hướng:** (Đánh giá mạnh: Bullish / Bearish / Neutral)
- **🎯 Lý do cốt lõi:**
  1. (Kết hợp số liệu thời tiết + Cung cầu)
  2. (Kết hợp dòng tiền COT + Technical S1/R1)

### 🌾 Phân Tích Lúa mì (ZW)
- **🔥 Xu hướng:** (Đánh giá mạnh: Bullish / Bearish / Neutral)
- **🎯 Lý do cốt lõi:**
  1. (Kết hợp số liệu tiến độ gặt/mùa vụ + Thời tiết)
  2. (Kết hợp dòng tiền COT + Technical S1/R1)

### 💡 Lời Khuyên Quản Trị Rủi Ro
- (1-2 câu lời khuyên sắc bén nhất về cách canh điểm vào lệnh hoặc mức độ rủi ro chung).

Vui lòng KHÔNG giải thích dông dài, trả lời thẳng vào trọng tâm chuyên môn.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    
    print("  [+] Đang gửi Prompt tới Google Gemini API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        
        text_output = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not text_output:
            print("  [ERR] API trả về rỗng.")
            return False
            
        result_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis": text_output.strip()
        }
        
        with open(AI_ANALYSIS_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        print("  [OK] Phân tích AI thành công! Đã lưu vào ai_analysis.json")
        return True
        
    except Exception as e:
        print(f"  [ERR] Lỗi khi gọi Gemini API: {e}")
        return False

if __name__ == "__main__":
    analyze()
