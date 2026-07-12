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
BLACKSEA_NEWS_FILE = OUTPUT_DIR / "blacksea_wheat.json"

def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None

def fetch_blacksea_rss():
    print("  [+] Đang tải tin tức từ Google News (Từ khóa: Russian, Black Sea, EU Wheat)...")
    
    # Query for Russian, Black Sea, Don-Azov, Kerch Strait and EU wheat news
    query = "Russia OR \"Black Sea\" OR \"Don-Azov\" OR \"Kerch Strait\" OR \"Azov Sea\" wheat export crop"
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req, timeout=15)
        tree = ET.parse(response)
        
        news_items = []
        # Take the top 15 results
        for item in tree.findall('.//item')[:15]:
            title = item.find('title').text if item.find('title') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            if title:
                news_items.append(f"Tiêu đề: {title}\nLink: {link}\nThời gian: {pub_date}\n")
                
        return "\n".join(news_items)
    except Exception as e:
        print(f"  [ERR] Lỗi khi tải RSS Biển Đen: {e}")
        return ""

def summarize_blacksea_news():
    print("\n=======================================================")
    print("  BLACK SEA WHEAT AGGREGATOR - TÓM TẮT LÚA MÌ NGA/EU")
    print("=======================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key trong Data/api_key.txt. Bỏ qua.")
        return False
        
    rss_text = fetch_blacksea_rss()
    if not rss_text:
        print("  [WARN] Không có tin tức nào được tải về.")
        return False
        
    prompt = f"""Bạn là một chuyên gia phân tích thị trường lúa mì quốc tế, đặc biệt là khu vực Biển Đen (Nga, Ukraine) và Châu Âu (EU).
Dưới đây là danh sách các tin tức thô lấy từ Google News về lúa mì khu vực này:

{rss_text}

Yêu cầu:
1. Đọc và lọc ra tối đa 8-10 tin tức QUAN TRỌNG NHẤT liên quan đến: Sản lượng lúa mì Nga/EU, thời tiết, tiến độ thu hoạch, chính sách thuế xuất khẩu, biến động giá FOB, và đặc biệt là rủi ro địa chính trị Biển Đen (tắc nghẽn eo biển Kerch, Kênh đào Don-Azov, cấm vận, tấn công quân sự).
2. Dịch và tóm tắt sang Tiếng Việt. KHÔNG làm sai lệch nội dung bài gốc.
3. Cấu trúc mỗi tin tức gồm: 1 Tiêu đề tóm tắt và 3-4 ý chính (details) bóc tách số liệu cụ thể.
4. Bạn BẮT BUỘC phải trả về kết quả dưới dạng một mảng JSON thuần túy (không chứa markdown ```json...```), với cấu trúc sau:
[
  {{
    "title": "Tiêu đề tiếng Việt",
    "details": [
      "Ý chính 1...",
      "Ý chính 2...",
      "Ý chính 3..."
    ],
    "link": "Link gốc của bài viết lấy từ danh sách trên",
    "source": "Thời gian xuất bản (Nguồn: Google News)"
  }}
]

Tuyệt đối chỉ trả về JSON.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
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
            
        try:
            news_array = json.loads(text_output)
        except json.JSONDecodeError:
            text_output = text_output.replace("```json", "").replace("```", "").strip()
            news_array = json.loads(text_output)
            
        news_array = news_array[:10] 
            
        result_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "news": news_array
        }
        
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        with open(BLACKSEA_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        print("  [OK] Điểm tin Lúa mì Nga/Biển Đen thành công! Đã lưu vào blacksea_wheat.json")
        return True
        
    except Exception as e:
        print(f"  [ERR] Lỗi khi gọi Gemini API: {e}")
        return False

if __name__ == "__main__":
    summarize_blacksea_news()
