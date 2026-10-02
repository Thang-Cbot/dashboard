import sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass
import os, json, requests, datetime, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR   = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
AI_NEWS_FILE  = OUTPUT_DIR / "ai_news.json"

# Thời hạn tin: loại tin đã cũ hơn 7 ngày
NEWS_MAX_DAYS = 7

CATEGORIES = ["dia_chinh_tri", "logistics", "san_luong_dien_tich", "cung_cau_nhan_dinh"]

def get_api_key():
    if not API_KEY_FILE.exists(): return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None

def fetch_rss_news():
    news_items = []

    feeds = [
        ("Yahoo Finance",         "https://feeds.finance.yahoo.com/rss/2.0/headline?s=ZC=F,ZW=F", 10),
        ("Farm Progress",         "https://www.farmprogress.com/rss.xml", 10),
        ("Google News (Geo)",     "https://news.google.com/rss/search?q=Russia+Ukraine+wheat+grain+Black+Sea&hl=en-US&gl=US&ceid=US:en", 10),
        ("Google News (Supply)",  "https://news.google.com/rss/search?q=wheat+corn+USDA+crop+harvest+production&hl=en-US&gl=US&ceid=US:en", 8),
        ("Google News (Shipping)","https://news.google.com/rss/search?q=wheat+corn+freight+shipping+logistics+port&hl=en-US&gl=US&ceid=US:en", 6),
    ]

    for source_name, url, limit in feeds:
        print(f"  [+] Đang tải RSS: {source_name}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=15)
            tree = ET.parse(resp)
            for item in tree.findall('.//item')[:limit]:
                title    = item.find('title').text or ""
                desc     = (item.find('description').text or "")[:300]
                link     = item.find('link').text or ""
                pub_date = item.find('pubDate').text or ""
                if title:
                    news_items.append(
                        f"Nguồn: {source_name}\nTiêu đề: {title}\nMô tả: {desc}\nLink: {link}\nThời gian: {pub_date}\n"
                    )
        except Exception as e:
            print(f"  [ERR] {source_name}: {e}")

    return "\n".join(news_items)

def call_gemini(api_key, prompt, temperature=0.2, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"}
    }
    import time
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=90)
            if resp.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"  [WAIT] Rate limit 429, chờ {wait}s rồi thử lại ({attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except requests.HTTPError as e:
            if attempt < max_retries - 1:
                time.sleep(20)
            else:
                raise
    raise Exception("Gemini API: Vượt quá số lần thử lại (429)")


def filter_old_news(news_array):
    """Giữ tin trong 7 ngày gần nhất."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=NEWS_MAX_DAYS)
    kept = []
    for item in news_array:
        src = item.get("source", "")
        # Thử parse ngày từ source string "29 Sep 2026 - ..."
        parsed = None
        for fmt in ("%d %b %Y", "%d %B %Y"):
            try:
                date_part = src.split("-")[0].strip()
                parsed = datetime.datetime.strptime(date_part, fmt)
                break
            except: pass
        if parsed is None or parsed >= cutoff:
            kept.append(item)
    return kept

def summarize_news():
    print("\n=======================================================")
    print("  AI NEWS AGGREGATOR - TÓM TẮT & PHÂN LOẠI TIN TỨC")
    print("=======================================================")

    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key. Bỏ qua.")
        return False

    rss_text = fetch_rss_news()
    if not rss_text:
        print("  [WARN] Không có tin tức nào được tải về.")
        return False

    # ── BƯỚC 1: Phân loại và tóm tắt tin tức ──────────────────────────────
    prompt_news = f"""Bạn là chuyên gia phân tích tin tức thị trường nông sản CBOT (Lúa mì ZW và Ngô ZC).
Dưới đây là danh sách tin tức thô vừa được thu thập:

{rss_text}

Yêu cầu:
1. Chọn lọc tối đa 15 tin quan trọng nhất, dịch sang Tiếng Việt.
2. Mỗi tin phải có:
   - "title": Tiêu đề tiếng Việt ngắn gọn, gây chú ý
   - "details": Mảng 3-5 ý chính (số liệu, nguyên nhân, tác động giá)
   - "link": URL gốc
   - "source": "DD Mon YYYY - Tên nguồn" (Ví dụ: "29 Sep 2026 - Yahoo Finance")
   - "category": MỘT trong các giá trị sau (chọn đúng nhất):
       * "dia_chinh_tri"    — Xung đột, chính sách thuế XK, địa chính trị Nga/Ukraine/MENA
       * "logistics"        — Vận tải biển, cảng, tắc nghẽn, cước phí, hành lang ngũ cốc
       * "san_luong_dien_tich" — Sản lượng, diện tích gieo trồng, thu hoạch, USDA NASS, ABARES
       * "cung_cau_nhan_dinh"  — Tồn kho, xuất khẩu, cung cầu, dự báo giá, nhận định chuyên gia

Chỉ trả về JSON thuần, không markdown, không giải thích. Cấu trúc:
[
  {{
    "title": "...",
    "details": ["...", "...", "..."],
    "link": "...",
    "source": "...",
    "category": "..."
  }}
]"""

    print("  [+] Gọi AI phân loại tin tức...")
    try:
        text1 = call_gemini(api_key, prompt_news, 0.15)
        text1 = text1.replace("```json","").replace("```","").strip()
        news_array = json.loads(text1)[:15]
        news_array = filter_old_news(news_array)
    except Exception as e:
        print(f"  [ERR] Phân loại tin: {e}")
        news_array = []

    # ── BƯỚC 2: Nhận định Intraday bằng Gemini ────────────────────────────
    print("  [+] Gọi AI nhận định intraday...")
    try:
        # Lấy giá và COT mới nhất
        macro   = {}
        cot_zw  = {}
        try:
            macro = json.loads((OUTPUT_DIR / "macro_data.json").read_text(encoding="utf-8"))
            cot   = json.loads((OUTPUT_DIR / "cot_data.json").read_text(encoding="utf-8"))
            cot_zw = cot.get("commodities", {}).get("001602", {})
        except: pass

        zw_price  = macro.get("zw_ref",{}).get("price", "N/A")
        zw_pct    = macro.get("zw_ref",{}).get("pct", 0)
        dxy       = macro.get("dxy",{}).get("price", "N/A")
        oil       = macro.get("brent",{}).get("price", "N/A")
        cot_net   = cot_zw.get("net_estimated", "N/A")
        cot_quad  = cot_zw.get("quadrant_estimated", "N/A")
        price_ts  = macro.get("timestamp", "N/A")

        # Top 5 tin quan trọng nhất để đưa vào context
        top_news_ctx = "\n".join([f"- {n.get('title','')} ({n.get('category','')})" for n in news_array[:5]])

        prompt_intraday = f"""Bạn là chuyên gia giao dịch hàng hóa CBOT, phân tích intraday cho Lúa mì (ZW).

DỮ LIỆU THỰC TẾ (cập nhật {price_ts}):
- Giá ZW tham chiếu: {zw_price} cents ({zw_pct:+.2f}%)
- DXY: {dxy}
- Dầu Brent: {oil} USD
- COT ZW Net (ước tính): {cot_net:,.0f} HĐ — Quadrant: {cot_quad}

TIN TỨC NỔI BẬT HÔM NAY:
{top_news_ctx}

Yêu cầu: Đưa ra nhận định INTRADAY ngắn gọn cho ZW hôm nay. Trả về JSON với cấu trúc:
{{
  "bias": "Bullish" hoặc "Bearish" hoặc "Neutral",
  "bias_vn": "Tăng" hoặc "Giảm" hoặc "Đi Ngang",
  "summary": "1 câu tóm tắt nhận định (tối đa 100 ký tự)",
  "key_levels": {{
    "support": "mức hỗ trợ gần nhất (cents)",
    "resistance": "mức kháng cự gần nhất (cents)"
  }},
  "reasoning": ["lý do 1 (tối đa 60 ký tự)", "lý do 2", "lý do 3"],
  "risk": "rủi ro chính cần theo dõi (tối đa 80 ký tự)",
  "generated_at": "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
}}
Chỉ trả JSON thuần, không markdown."""

        text2 = call_gemini(api_key, prompt_intraday, 0.3)
        text2 = text2.replace("```json","").replace("```","").strip()
        intraday = json.loads(text2)
    except Exception as e:
        print(f"  [WARN] Nhận định intraday lỗi: {e}")
        intraday = {
            "bias": "Neutral",
            "bias_vn": "Đi Ngang",
            "summary": "Chưa đủ dữ liệu để nhận định intraday",
            "key_levels": {"support": "N/A", "resistance": "N/A"},
            "reasoning": ["Dữ liệu chưa đầy đủ"],
            "risk": "N/A",
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    # ── LƯU KẾT QUẢ ──────────────────────────────────────────────────────
    result = {
        "timestamp":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "news":       news_array,
        "intraday":   intraday,
        "categories": CATEGORIES
    }
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    with open(AI_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Stats
    by_cat = {}
    for n in news_array:
        c = n.get("category","other")
        by_cat[c] = by_cat.get(c, 0) + 1
    print(f"  [OK] Lưu {len(news_array)} tin | Phân loại: {by_cat}")
    print(f"  [OK] Intraday bias: {intraday.get('bias','?')} — {intraday.get('summary','')}")
    return True

if __name__ == "__main__":
    summarize_news()
