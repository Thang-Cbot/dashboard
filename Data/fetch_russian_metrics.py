import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
import os
import json
import requests
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
METRICS_FILE = OUTPUT_DIR / "russian_metrics.json"

def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None

def fetch_rss_data():
    print("  [+] Đang thu thập dữ liệu số liệu từ Google News (SovEcon, IKAR, Russian Wheat)...")
    
    # Chúng ta sử dụng 2 query để đảm bảo quét đủ số liệu xuất khẩu, giá và tiến độ
    queries = [
        "Russian wheat harvest progress IKAR SovEcon",
        "Russian wheat FOB export price Black Sea"
    ]
    
    news_items = []
    
    for q in queries:
        encoded_query = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            response = urllib.request.urlopen(req, timeout=15)
            tree = ET.parse(response)
            for item in tree.findall('.//item')[:8]: # Lấy top 8 bài cho mỗi query
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                if title:
                    news_items.append(f"Title: {title}\nDate: {pub_date}\n")
        except Exception as e:
            print(f"  [WARN] Lỗi khi lấy RSS cho '{q}': {e}")
            
    return "\n".join(news_items)

def extract_metrics_with_ai():
    print("\n=======================================================")
    print("  RUSSIAN WHEAT METRICS EXTRACTOR (AI)")
    print("=======================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("  [ERR] Chưa có API Key.")
        return False
        
    rss_text = fetch_rss_data()
    if not rss_text:
        print("  [WARN] Không có dữ liệu để phân tích.")
        return False
        
    prompt = f"""Bạn là chuyên gia dữ liệu hàng hóa (Commodity Data Analyst).
Dưới đây là tiêu đề các báo cáo mới nhất về thị trường lúa mì Nga (SovEcon, IKAR, Reuters):

{rss_text}

Nhiệm vụ: Bóc tách các số liệu định lượng (nếu có nhắc đến) và đưa ra dự báo chung nhất về tình hình hiện tại. Nếu thông tin nào không xuất hiện trong văn bản trên, hãy tự sử dụng kiến thức chung cập nhật nhất của bạn hoặc để 'N/A' nếu không thể xác định.
Bạn BẮT BUỘC phải trả về kết quả dưới dạng JSON (không có ```json markdown), đúng cấu trúc sau:

{{
  "planted_area": "Diện tích gieo trồng (VD: 29.5 triệu ha hoặc N/A)",
  "production_forecast": "Sản lượng dự báo (VD: 80 - 85 triệu tấn)",
  "harvest_progress": "Tiến độ thu hoạch (VD: Đã gặt 20%, hoặc Đang bắt đầu)",
  "fob_price": "Giá xuất khẩu giao ngay (FOB) (VD: $230/tấn hoặc N/A)",
  "export_tax": "Thuế/Chính sách xuất khẩu hiện tại (VD: Đang tăng thuế, hoặc N/A)",
  "export_capacity": "Năng lực xuất khẩu (VD: 45 triệu tấn)",
  "quality_notes": "Chất lượng lúa mì (VD: Hư hại do sương giá, chất lượng protein cao...)",
  "harvest_time": "Tháng 6 - Tháng 7 (Vụ Đông), Tháng 7 - Thu (Vụ Xuân)",
  "ai_assessment": "1 câu nhận định tóm tắt về áp lực xả hàng của Nga lên giá CBOT hiện tại."
}}
Tuyệt đối chỉ trả về dữ liệu JSON, không có chữ nào nằm ngoài ngoặc nhọn {{}}.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    print("  [+] Đang gửi Prompt tới Google Gemini API bóc tách số liệu...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        
        text_output = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not text_output:
            print("  [ERR] API trả về rỗng.")
            return False
            
        try:
            metrics_data = json.loads(text_output)
        except json.JSONDecodeError:
            text_output = text_output.replace("```json", "").replace("```", "").strip()
            metrics_data = json.loads(text_output)
            
        result_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": metrics_data
        }
        
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        print("  [OK] Đã bóc tách thành công! Lưu tại russian_metrics.json")
        return True
        
    except Exception as e:
        print(f"  [ERR] Lỗi khi gọi Gemini API: {e}")
        return False

if __name__ == "__main__":
    extract_metrics_with_ai()
