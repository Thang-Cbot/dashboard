"""
Data/fetch_vip_intel.py — Module Quét Tự Động (Scraper/RSS) & Phân Tích AI
chuyên biệt từ 2 nguồn tin chiến lược:
1. Jim Roemer & Scott Mathews (BestWeather Inc. / Climatelligence Substack)
2. Dow Jones Daily Grain Highlights (Kirk Maltais / Marex) & Barchart Grain Market Wrap
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import re
import json
import html
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
VIP_INTEL_FILE = OUTPUT_DIR / "vip_intel.json"

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]


def get_api_key():
    if not API_KEY_FILE.exists():
        return None
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    return key if key else None


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^<]+?>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def call_gemini(api_key, prompt, temperature=0.2, max_retries=2):
    import time
    last_err = None
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=90,
                )
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"  [WAIT] {model}: 429, chờ {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                text = (
                    resp.json()
                    .get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                print(f"  [OK] Gemini Model: {model}")
                return text
            except Exception as e:
                last_err = e
                break
    raise Exception(f"Gemini API failed: {last_err}")


def fetch_roemer_bestweather():
    """Quét toàn văn từ Climatelligence Substack (Jim Roemer & Scott Mathews) + Google News BestWeather."""
    articles = []
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

    # 1. Climatelligence Substack Feed (Full text trong content:encoded)
    substack_url = "https://climatelligence.substack.com/feed"
    print("  [+] Đang quét Jim Roemer / Climatelligence Substack RSS...")
    try:
        req = urllib.request.Request(substack_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            tree = ET.parse(resp)
        for item in tree.findall(".//item")[:6]:
            title = clean_html(item.findtext("title") or "")
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            desc = clean_html(item.findtext("description") or "")
            content_el = item.find("content:encoded", ns)
            full_text = clean_html(content_el.text if content_el is not None and content_el.text else desc)
            if title:
                articles.append({
                    "source": "BestWeather / Climatelligence (Jim Roemer & Scott Mathews)",
                    "title": title,
                    "pub_date": pub_date[:16],
                    "link": link,
                    "content": full_text[:2800],
                })
    except Exception as e:
        print(f"  [WARN] Substack RSS: {e}")

    # 2. Google News RSS cho Jim Roemer / BestWeather
    gnews_roemer = (
        "https://news.google.com/rss/search?"
        "q=%22Jim+Roemer%22+OR+%22BestWeather%22+OR+%22Best+Weather%22+wheat+corn+soybeans"
        "&hl=en-US&gl=US&ceid=US:en"
    )
    print("  [+] Đang quét Google News (Jim Roemer / BestWeather)...")
    try:
        req = urllib.request.Request(gnews_roemer, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            tree = ET.parse(resp)
        for item in tree.findall(".//item")[:5]:
            title = clean_html(item.findtext("title") or "")
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            desc = clean_html(item.findtext("description") or "")
            if title and not any(a["title"][:30].lower() == title[:30].lower() for a in articles):
                articles.append({
                    "source": "Jim Roemer / BestWeather Syndicate",
                    "title": title,
                    "pub_date": pub_date[:16],
                    "link": link,
                    "content": desc[:1000],
                })
    except Exception as e:
        print(f"  [WARN] Google News Roemer: {e}")

    return articles


def fetch_dowjones_barchart_wrap():
    """Quét bản tin tổng hợp phiên từ Barchart Grain RSS, Dow Jones (Kirk Maltais) & Desk Chicago (Marex)."""
    articles = []

    feeds = [
        (
            "Barchart Grain Market Wrap",
            "https://www.barchart.com/news/rss/commodities/grain",
            10,
        ),
        (
            "Dow Jones / WSJ Grain Highlights",
            "https://news.google.com/rss/search?q=(%22On+the+Home+Front%22+OR+%22Kirk+Maltais%22+OR+%22Dow+Jones%22)+wheat+corn+soybeans+bushel&hl=en-US&gl=US&ceid=US:en",
            6,
        ),
        (
            "Chicago Desks (Marex / Futures Intl / AgResource)",
            "https://news.google.com/rss/search?q=(%22Marex%22+OR+%22Sernatinger%22+OR+%22Futures+International%22+OR+%22AgResource%22)+wheat+corn+CBOT&hl=en-US&gl=US&ceid=US:en",
            6,
        ),
        (
            "World Grain Market Report",
            "https://www.world-grain.com/rss/articles",
            6,
        ),
    ]

    for src_name, url, limit in feeds:
        print(f"  [+] Đang quét {src_name}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                tree = ET.parse(resp)
            for item in tree.findall(".//item")[:limit]:
                title = clean_html(item.findtext("title") or "")
                link = item.findtext("link") or ""
                pub_date = item.findtext("pubDate") or ""
                desc = clean_html(item.findtext("description") or "")
                author = clean_html(item.findtext("author") or "")
                if title:
                    articles.append({
                        "source": f"{src_name}" + (f" ({author})" if author else ""),
                        "title": title,
                        "pub_date": pub_date[:16],
                        "link": link,
                        "content": desc[:1200],
                    })
        except Exception as e:
            print(f"  [WARN] {src_name}: {e}")

    return articles


def run_vip_intel_pipeline():
    print("\n=======================================================")
    print("  VIP INTELLIGENCE SCRAPER: BESTWEATHER & DOW JONES")
    print("=======================================================")

    api_key = get_api_key()
    roemer_raw = fetch_roemer_bestweather()
    dj_raw = fetch_dowjones_barchart_wrap()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not api_key:
        print("  [WARN] Không tìm thấy API Key, lưu dữ liệu thô.")
        out = {
            "timestamp": now_str,
            "roemer_raw": roemer_raw,
            "dj_raw": dj_raw,
        }
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        VIP_INTEL_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    roemer_text = "\n\n".join(
        [
            f"[{i+1}] Nguồn: {a['source']} ({a['pub_date']})\nTiêu đề: {a['title']}\nLink: {a['link']}\nNội dung: {a['content']}"
            for i, a in enumerate(roemer_raw[:6])
        ]
    )

    dj_text = "\n\n".join(
        [
            f"[{i+1}] Nguồn: {a['source']} ({a['pub_date']})\nTiêu đề: {a['title']}\nLink: {a['link']}\nNội dung: {a['content']}"
            for i, a in enumerate(dj_raw[:14])
        ]
    )

    prompt = f"""Bạn là Chuyên gia Phân tích Nông sản CBOT cấp cao.
Hãy tổng hợp và phân tích chuyên sâu 2 luồng tình báo VIP dưới đây sang Tiếng Việt chuẩn xác, sắc bén:

=== LUỒNG 1: BÁO CÁO KHÍ TƯỢNG NÔNG SẢN TỪ JIM ROEMER (BESTWEATHER & CLIMATELLIGENCE) ===
{roemer_text}

=== LUỒNG 2: BẢN TIN TỔNG HỢP SÀN CBOT & DESK CHICAGO (DOW JONES / BARCHART / MAREX) ===
{dj_text}

YÊU CẦU ĐẦU RA (Trả về JSON thuần, không bọc markdown):
{{
  "bestweather_report": {{
    "weather_premium_status": "ĐANG XÌ HƠI (BEARISH)" hoặc "ĐANG BƠM (BULLISH)" hoặc "TRUNG TÍNH",
    "headline_vn": "Tiêu đề tổng hợp nhận định mới nhất của Jim Roemer & Scott Mathews",
    "executive_summary": "Tóm tắt cốt lõi 2-3 câu về câu chuyện thời tiết đang chi phối thị trường ngũ cốc (nhấn mạnh quy luật Thời tiết là Vua mùa thu hoạch/gieo trồng)",
    "regional_impacts": [
      {{
        "region": "🇺🇸 Đồng bằng Mỹ (US Plains - Lúa mì vụ Đông)",
        "condition": "Tình trạng mưa/độ ẩm hiện tại",
        "impact": "Bearish" hoặc "Bullish" hoặc "Neutral",
        "detail": "Chi tiết tác động lên giá Lúa mì (ZW)"
      }},
      {{
        "region": "🌽 Vành đai Corn Belt Mỹ (Thu hoạch Ngô & Đậu tương)",
        "condition": "Tình trạng thời tiết thu hoạch",
        "impact": "Bearish" hoặc "Bullish" hoặc "Neutral",
        "detail": "Chi tiết tác động lên tiến độ thu hoạch và giá ZC/ZS"
      }},
      {{
        "region": "🌎 Nam Mỹ (Brazil/Argentina) & Úc",
        "condition": "Tình trạng mưa đầu vụ Nam Mỹ & thu hoạch Úc",
        "impact": "Bearish" hoặc "Bullish" hoặc "Neutral",
        "detail": "Chi tiết tác động cung cầu và rủi ro El Niño mùa đông"
      }}
    ],
    "winter_outlook": "Nhận định của BestWeather về cơ hội sóng tăng giá mùa Đông (Winter Bullish Opportunity / El Niño)",
    "articles": [
      {{
        "title_vn": "Tiêu đề bài viết dịch sang tiếng Việt",
        "title_en": "Tiêu đề gốc",
        "date": "Ngày đăng",
        "link": "URL gốc",
        "key_points": ["Ý chính 1", "Ý chính 2", "Ý chính 3"]
      }}
    ]
  }},
  "dowjones_barchart_wrap": {{
    "session_headline": "Tiêu đề tổng kết phiên giao dịch CBOT mới nhất",
    "on_the_home_front": "Phân tích mục 'On the Home Front': Tình hình thời tiết thực địa, tiến độ gieo trồng/thu hoạch Mỹ đang tác động thế nào tới tâm lý trader",
    "cut_and_run_funds": "Phân tích mục 'Cut and Run': Động thái của các quỹ Managed Money (thanh lý Long hay Short-covering) và lực bán phòng hộ (Pre-hedging) của nông dân/trạm thu mua",
    "feeling_flat_demand": "Phân tích mục 'Feeling Flat / Export Demand': Phản ứng của giá với các đơn hàng Flash Sales / Export Sales của USDA",
    "insight_bottom_line": "Phân tích mục 'Insight': Chuỗi phiên tăng/giảm, sức mạnh đồng USD và định hướng ngắn hạn cho ZW và ZC",
    "articles": [
      {{
        "title_vn": "Tiêu đề bản tin dịch sang tiếng Việt",
        "source": "Tên nguồn & ngày",
        "link": "URL gốc",
        "summary_points": ["Điểm chính 1 (số liệu giá/cent)", "Điểm chính 2 (nhận định chuyên gia)"]
      }}
    ]
  }}
}}"""

    print("  [+] Đang gọi Gemini AI bóc tách báo cáo BestWeather & Dow Jones Wrap...")
    try:
        raw_json = call_gemini(api_key, prompt, temperature=0.2)
        raw_json = raw_json.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw_json)
    except Exception as e:
        print(f"  [ERR] Gemini AI: {e}")
        parsed = {}

    final_data = {
        "timestamp": now_str,
        "bestweather_report": parsed.get("bestweather_report", {}),
        "dowjones_barchart_wrap": parsed.get("dowjones_barchart_wrap", {}),
        "roemer_raw_count": len(roemer_raw),
        "dj_raw_count": len(dj_raw),
    }

    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    with open(VIP_INTEL_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Đã lưu thành công vào {VIP_INTEL_FILE}")
    return True


if __name__ == "__main__":
    run_vip_intel_pipeline()
