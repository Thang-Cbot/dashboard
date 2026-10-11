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
        ("Farm Progress",         "https://www.farmprogress.com/rss.xml", 8),
        ("Sky News (Biển Đen & TG)", "https://feeds.skynews.com/feeds/rss/world.xml", 12),
        ("Google News (Geo)",     "https://news.google.com/rss/search?q=Russia+Ukraine+wheat+grain+Black+Sea&hl=en-US&gl=US&ceid=US:en", 10),
        ("Google News (Supply)",  "https://news.google.com/rss/search?q=wheat+corn+USDA+crop+harvest+production&hl=en-US&gl=US&ceid=US:en", 8),
        ("Google News (Shipping)","https://news.google.com/rss/search?q=wheat+corn+freight+shipping+logistics+port&hl=en-US&gl=US&ceid=US:en", 6),
        ("Google News (Tenders)", "https://news.google.com/rss/search?q=wheat+tender+GASC+Algeria+Saudi+purchase&hl=en-US&gl=US&ceid=US:en", 8),
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


# Model fallback chain (tiết kiệm token tối đa):
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

def call_gemini(api_key, prompt, temperature=0.2, max_retries=2):
    """Gọi Gemini API với fallback qua nhiều model nếu bị 429."""
    import time
    last_err = None
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"}
        }
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json=payload, timeout=90)
                if resp.status_code == 429:
                    wait = 20 * (attempt + 1)
                    print(f"  [WAIT] {model}: 429, chờ {wait}s (lần {attempt+1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                text = resp.json().get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
                print(f"  [OK] Model: {model}")
                return text
            except requests.HTTPError as e:
                last_err = e
                if resp.status_code != 429:
                    break  # Lỗi khác, thử model tiếp theo
                if attempt == max_retries - 1:
                    print(f"  [SKIP] {model}: Hết lần retry, chuyển model tiếp theo...")
            except Exception as e:
                last_err = e
                break
    raise Exception(f"Tất cả model đều thất bại. Lỗi cuối: {last_err}")


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

    # ── BƯỚC 2: Nhận định Intraday cho cả ZW và ZC bằng Gemini ──────────
    print("  [+] Gọi AI nhận định intraday cho Lúa mì (ZW) và Ngô (ZC)...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    intraday = {}
    try:
        # Lấy giá và COT mới nhất cho cả ZW và ZC
        macro   = {}
        cot     = {}
        try:
            macro = json.loads((OUTPUT_DIR / "macro_data.json").read_text(encoding="utf-8"))
            cot   = json.loads((OUTPUT_DIR / "cot_data.json").read_text(encoding="utf-8"))
        except: pass

        dxy       = macro.get("dxy",{}).get("price", "N/A")
        oil       = macro.get("brent",{}).get("price", "N/A")
        price_ts  = macro.get("timestamp", "N/A")

        # Dữ liệu ZW (Lúa mì)
        cot_zw    = cot.get("commodities", {}).get("001602", {})
        zw_price  = macro.get("zw_ref",{}).get("price") or cot_zw.get("latest_price", "N/A")
        zw_pct    = macro.get("zw_ref",{}).get("pct", 0)
        cot_net_zw= cot_zw.get("net_estimated", "N/A")
        cot_quad_zw= cot_zw.get("quadrant_estimated", "N/A")

        # Dữ liệu ZC (Ngô)
        cot_zc    = cot.get("commodities", {}).get("002602", {})
        zc_price  = macro.get("zc_ref",{}).get("price") or cot_zc.get("latest_price", "N/A")
        zc_pct    = macro.get("zc_ref",{}).get("pct", 0)
        cot_net_zc= cot_zc.get("net_estimated", "N/A")
        cot_quad_zc= cot_zc.get("quadrant_estimated", "N/A")

        # Top 6 tin quan trọng nhất để đưa vào context
        top_news_ctx = "\n".join([f"- {n.get('title','')} ({n.get('category','')})" for n in news_array[:6]])

        prompt_intraday = f"""Bạn là chuyên gia giao dịch hàng hóa CBOT hàng đầu. Hãy phân tích xu hướng INTRADAY hôm nay cho cả 2 mặt hàng: Lúa mì (ZW) và Ngô (ZC).

DỮ LIỆU THỰC TẾ LIÊN THỊ TRƯỜNG (cập nhật {price_ts}):
- Vĩ mô chung: DXY={dxy}, Dầu Brent={oil} USD

1. LÚA MÌ (ZW):
- Giá ZW tham chiếu: {zw_price} cents ({zw_pct:+.2f}%)
- Vị thế COT Smart Money Net: {cot_net_zw} HĐ — Quadrant: {cot_quad_zw}

2. NGÔ (ZC):
- Giá ZC tham chiếu: {zc_price} cents ({zc_pct:+.2f}%)
- Vị thế COT Smart Money Net: {cot_net_zc} HĐ — Quadrant: {cot_quad_zc}

TIN TỨC THỊ TRƯỜNG & ĐỊA CHÍNH TRỊ NỔI BẬT:
{top_news_ctx}

Yêu cầu: Đưa ra nhận định INTRADAY độc lập cho từng mã ZW và ZC.
Trả về JSON thuần (không bọc markdown) với cấu trúc sau:
{{
  "ZW": {{
    "bias": "Bullish" hoặc "Bearish" hoặc "Neutral",
    "bias_vn": "Tăng" hoặc "Giảm" hoặc "Đi Ngang",
    "summary": "1 câu tóm tắt nhận định ZW (tối đa 110 ký tự)",
    "key_levels": {{
      "support": "mức hỗ trợ gần nhất (cents)",
      "resistance": "mức kháng cự gần nhất (cents)"
    }},
    "reasoning": ["lý do 1 (tối đa 70 ký tự)", "lý do 2", "lý do 3"],
    "risk": "rủi ro chính cần theo dõi đối với ZW (tối đa 90 ký tự)",
    "generated_at": "{now_str}"
  }},
  "ZC": {{
    "bias": "Bullish" hoặc "Bearish" hoặc "Neutral",
    "bias_vn": "Tăng" hoặc "Giảm" hoặc "Đi Ngang",
    "summary": "1 câu tóm tắt nhận định ZC (tối đa 110 ký tự)",
    "key_levels": {{
      "support": "mức hỗ trợ gần nhất (cents)",
      "resistance": "mức kháng cự gần nhất (cents)"
    }},
    "reasoning": ["lý do 1 (tối đa 70 ký tự)", "lý do 2", "lý do 3"],
    "risk": "rủi ro chính cần theo dõi đối với ZC (tối đa 90 ký tự)",
    "generated_at": "{now_str}"
  }}
}}"""

        text2 = call_gemini(api_key, prompt_intraday, 0.3)
        text2 = text2.replace("```json","").replace("```","").strip()
        parsed_raw = json.loads(text2)

        zw_res = parsed_raw.get("ZW", {})
        zc_res = parsed_raw.get("ZC", {})

        intraday = {
            "ZW": zw_res,
            "ZC": zc_res,
            "bias": zw_res.get("bias", "Neutral"),
            "bias_vn": zw_res.get("bias_vn", "Đi Ngang"),
            "summary": zw_res.get("summary", ""),
            "key_levels": zw_res.get("key_levels", {}),
            "reasoning": zw_res.get("reasoning", []),
            "risk": zw_res.get("risk", ""),
            "generated_at": zw_res.get("generated_at", now_str)
        }
    except Exception as e:
        print(f"  [WARN] Nhận định intraday lỗi: {e}")
        def default_item(name):
            return {
                "bias": "Neutral",
                "bias_vn": "Đi Ngang",
                "summary": f"Chưa đủ dữ liệu để nhận định intraday {name}",
                "key_levels": {"support": "N/A", "resistance": "N/A"},
                "reasoning": ["Đang chờ cập nhật dữ liệu"],
                "risk": "N/A",
                "generated_at": now_str
            }
        intraday = {
            "ZW": default_item("ZW"),
            "ZC": default_item("ZC"),
            "bias": "Neutral",
            "bias_vn": "Đi Ngang",
            "summary": "Chưa đủ dữ liệu để nhận định",
            "key_levels": {"support": "N/A", "resistance": "N/A"},
            "reasoning": ["Đang chờ cập nhật dữ liệu"],
            "risk": "N/A",
            "generated_at": now_str
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
