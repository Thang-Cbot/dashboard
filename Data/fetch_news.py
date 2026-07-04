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
    print("  [+] Đang tải tin tức từ Yahoo Finance RSS...")
    url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=ZC=F,ZW=F"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req, timeout=15)
        tree = ET.parse(response)
        
        news_items = []
        for item in tree.findall('.//item')[:15]:
            title = item.find('title').text if item.find('title') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            if title:
                news_items.append(f"Tiêu đề: {title}\nMô tả: {desc}\nLink: {link}\nThời gian: {pub_date}\n")
                
        return "\n".join(news_items)
    except Exception as e:
        print(f"  [ERR] Lỗi khi tải RSS: {e}")
        return ""

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
1. Hãy tóm tắt các tin tức trên thành các ý chính SIÊU NGẮN GỌN (mỗi ý không quá 2 dòng).
2. Dịch sang Tiếng Việt.
3. Chỉ chọn lọc những tin quan trọng liên quan trực tiếp đến Lúa mì (Wheat) và Ngô (Corn), các yếu tố thời tiết, xuất khẩu, chính trị, bỏ qua các tin nhiễu hoặc không liên quan.
4. BẮT BUỘC trình bày dưới dạng gạch đầu dòng bằng dấu "+".
5. BẮT BUỘC chèn thêm thông tin Thời gian và Link bài viết NGAY LIỀN KỀ Ở CUỐI MỖI CÂU (KHÔNG XUỐNG DÒNG) theo đúng format HTML sau: <span style="font-size:11px; color:#94a3b8; font-style:italic;">(Nguồn: Thời gian) - <a href="Link" target="_blank" style="color:#38bdf8;">Đọc chi tiết</a></span>

Ví dụ: 
+ Trung Quốc vừa mới ký thỏa thuận mua đậu tương và ngô Mỹ với 10tr tấn. <span style="font-size:11px; color:#94a3b8; font-style:italic;">(Nguồn: 04 Jul 2026) - <a href="https://finance.yahoo.com/..." target="_blank" style="color:#38bdf8;">Đọc chi tiết</a></span>

Không giải thích dài dòng, chỉ in ra các dấu +
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
            
        # Parse bullet points
        bullets = []
        for line in text_output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('+') or line.startswith('-') or line.startswith('*'):
                clean_line = '+ ' + line[1:].strip()
                if "(Nguồn:" in clean_line and bullets and clean_line.startswith("+ <span") or clean_line.startswith("+ (Nguồn"):
                    bullets[-1] = bullets[-1] + " " + clean_line[2:].strip()
                else:
                    bullets.append(clean_line)
            elif "(Nguồn:" in line and bullets:
                bullets[-1] = bullets[-1] + " " + line.strip()
            else:
                if bullets:
                    bullets[-1] = bullets[-1] + " " + line
                else:
                    bullets.append('+ ' + line)
                
        if not bullets:
            bullets = ["+ Không có tin tức nào nổi bật trong 24h qua."]
            
        bullets = bullets[:15]
            
        result_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bullets": bullets
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
