import sys
import json
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
MACRO_WEIGHTS_FILE = DATA_DIR / "macro_weights.json"
AI_NEWS_FILE = OUTPUT_DIR / "ai_news.json"

def get_api_key():
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""

def update_macro_overrides():
    api_key = get_api_key()
    if not api_key:
        print("No API Key")
        return False
        
    # Read current weights
    try:
        with open(MACRO_WEIGHTS_FILE, 'r', encoding='utf-8') as f:
            weights = json.load(f)
    except Exception as e:
        print(f"Error reading weights: {e}")
        return False
        
    # Read news
    try:
        with open(AI_NEWS_FILE, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
            news_text = json.dumps(news_data.get('news', [])[:20], ensure_ascii=False)
    except:
        news_text = "No recent news."

    prompt = f"""Bạn là chuyên gia phân tích Vĩ mô hàng hóa CBOT (Ngô & Lúa Mì).
Nhiệm vụ: Cập nhật các yếu tố vĩ mô thủ công (từ 1 đến 10 điểm, 1 = Mega Bearish, 10 = Mega Bullish) dựa trên tin tức thị trường mới nhất.

Tin tức mới nhất:
{news_text}

LƯU Ý QUAN TRỌNG:
- BẮT BUỘC BÁO CÁO DỮ LIỆU THỰC TẾ TRẮNG ĐEN (Zero-Hallucination). Không xào nấu tin cũ. Nếu không có tin mới về một yếu tố, hãy ghi rõ "Chưa có tin mới, duy trì nhận định cũ".
- Chấm dứt suy diễn vô căn cứ.
- Cập nhật trường 'note' bằng tiếng Việt, giải thích lý do cho điểm số. TRÍCH DẪN SỐ LIỆU TỪ TIN TỨC.
- Phân biệt rõ LÚA MÌ (ZW) và NGÔ (ZC) cho các yếu tố.

Trả về DUY NHẤT một cục JSON đúng chuẩn định dạng như sau, KHÔNG bọc trong markdown, KHÔNG có text thừa:
{{
  "F1_Russia_Policy_ZW": {{"score": 2, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F1_Ukraine_Policy_ZC": {{"score": 3, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F3_Other_Supply_ZW": {{"score": 8, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F3_Other_Supply_ZC": {{"score": 2, "note": "Mất thị phần TQ...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F4S_Supply_SH_ZW": {{"score": 5, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F4S_Supply_SH_ZC": {{"score": 2, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F8_Geopolitics_ZW": {{"score": 7, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F8_Geopolitics_ZC": {{"score": 5, "note": "...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F12_Global_Demand_ZW": {{"score": 4, "note": "Doanh số xuất khẩu lúa mì đạt...", "updated_at": "YYYY-MM-DD HH:MM"}},
  "F12_Global_Demand_ZC": {{"score": 3, "note": "Doanh số xuất khẩu ngô đạt...", "updated_at": "YYYY-MM-DD HH:MM"}}
}}
Thay "YYYY-MM-DD HH:MM" bằng {datetime.now().strftime('%Y-%m-%d %H:%M')}.
"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text_resp = result['candidates'][0]['content']['parts'][0]['text']
            
            # clean json
            text_resp = text_resp.replace('```json', '').replace('```', '').strip()
            
            new_overrides = json.loads(text_resp)
            
            # Merge
            for k, v in new_overrides.items():
                if k in weights.get('manual_overrides', {}):
                    weights['manual_overrides'][k].update(v)
                else:
                    weights['manual_overrides'][k] = v
            
            with open(MACRO_WEIGHTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(weights, f, ensure_ascii=False, indent=2)
                
            print("Successfully updated manual overrides with AI.")
            return True
    except Exception as e:
        print(f"Failed to call Gemini or parse JSON: {e}")
        return False

if __name__ == "__main__":
    update_macro_overrides()
