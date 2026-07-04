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
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
AI_NEWS_FILE = OUTPUT_DIR / "ai_news.json"

def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None

def fetch_rss_news():
    news_items = []
    
    # 1. Yahoo Finance RSS
    print("  [+] Đang tải tin tức từ Yahoo Finance RSS...")
    yahoo_url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=ZC=F,ZW=F"
    req_yahoo = urllib.request.Request(yahoo_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp_yahoo = urllib.request.urlopen(req_yahoo, timeout=15)
        tree_yahoo = ET.parse(resp_yahoo)
        for item in tree_yahoo.findall('.//item')[:10]:
            title = item.find('title').text if item.find('title') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            if title:
                news_items.append(f"Nguồn: Yahoo Finance\nTiêu đề: {title}\nMô tả: {desc}\nLink: {link}\nThời gian: {pub_date}\n")
    except Exception as e:
        print(f"  [ERR] Lỗi khi tải Yahoo RSS: {e}")
        
    # 2. Farm Progress RSS
    print("  [+] Đang tải tin tức từ Farm Progress RSS...")
    fp_url = "https://www.farmprogress.com/rss.xml"
    req_fp = urllib.request.Request(fp_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp_fp = urllib.request.urlopen(req_fp, timeout=15)
        tree_fp = ET.parse(resp_fp)
        for item in tree_fp.findall('.//item')[:10]:
            title = item.find('title').text if item.find('title') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            # Loai bo bot HTML trong desc neu qua dai, hoac cu de nguyen
            desc = desc[:300] + "..." if len(desc) > 300 else desc
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            if title:
                news_items.append(f"Nguồn: Farm Progress\nTiêu đề: {title}\nMô tả: {desc}\nLink: {link}\nThời gian: {pub_date}\n")
    except Exception as e:
        print(f"  [ERR] Lỗi khi tải Farm Progress RSS: {e}")
        
    return "\n".join(news_items)

def summarize_news():
    print("\n=======================================================")
    print("  AI NEWS AGGREGATOR - TÓM TẮT TIN TỨC BẰNG AI")
    print("=======================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key trong Data/api_key.txt. Bỏ qua tóm tắt tin tức.")
        return False
        
    rss_text = fetch_rss_news()
    if not rss_text:
        print("  [WARN] Không có tin tức nào được tải về.")
        return False
        
    prompt = f"""Bạn là một chuyên gia phân tích tin tức thị trường nông sản (Lúa mì và Ngô CBOT).
Dưới đây là danh sách các tin tức thô vừa được lấy từ hệ thống (tiếng Anh):

{rss_text}

Yêu cầu:
1. Đọc, chọn lọc và bóc tách tối đa 15 tin tức quan trọng nhất liên quan trực tiếp đến Lúa mì (Wheat) và Ngô (Corn).
2. Tóm tắt từng tin tức một cách trung thực, KHÔNG làm sai lệch nội dung bài viết gốc. Dịch sang Tiếng Việt.
3. Với mỗi tin tức, hãy chia thành 1 Tiêu đề (gây chú ý, khái quát) và 3-5 ý chính (details) tóm tắt được hết ý quan trọng của bài viết (số liệu, nguyên nhân, vĩ mô).
4. Bạn BẮT BUỘC phải trả về kết quả dưới dạng một mảng JSON thuần túy (không chứa markdown ```json...```), với cấu trúc sau:
[
  {{
    "title": "Tiêu đề tiếng Việt khái quát nội dung",
    "details": [
      "Ý chính 1...",
      "Ý chính 2...",
      "Ý chính 3..."
    ],
    "link": "Link gốc của bài viết lấy từ danh sách trên",
    "source": "Thời gian và Nguồn (Ví dụ: 04 Jul 2026 - Yahoo Finance)"
  }}
]

Tuyệt đối chỉ trả về JSON, không giải thích gì thêm.
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
            
        # Parse JSON
        try:
            news_array = json.loads(text_output)
        except json.JSONDecodeError:
            print("  [ERR] Lỗi khi parse JSON từ AI.")
            # Khắc phục fallback nếu AI lỡ chèn markdown
            text_output = text_output.replace("```json", "").replace("```", "").strip()
            news_array = json.loads(text_output)
            
        news_array = news_array[:15] # Giới hạn tối đa 15 tin
            
        result_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "news": news_array
        }
        
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        with open(AI_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        print("  [OK] Điểm tin AI thành công! Đã lưu vào ai_news.json")
        return True
        
    except Exception as e:
        print(f"  [ERR] Lỗi khi gọi Gemini API: {e}")
        return False

if __name__ == "__main__":
    summarize_news()
