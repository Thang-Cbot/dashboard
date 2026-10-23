"""
Data/ai_analyzer.py
===================
Hệ thống Tự động Chạy Giao thức RUN TIN TỨC 6 PHẦN CHUẨN MỰC (CBOT ZW & ZC).
- Phần 1 -> Phần 5: Phân tích dạng Bảng (Table) đối chiếu 2 mã W (Lúa mì) và C (Ngô),
  tích hợp quét trực tiếp chuyên mục AgWeb Market Analysis (https://www.agweb.com/markets/market-analysis) ở Phần 5.
- Phần 6 (Riêng biệt cuối cùng): Chiến lược tác chiến đúc kết trong ngày cho cả W và C.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
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

DATA_DIR          = Path(__file__).parent
OUTPUT_DIR        = DATA_DIR / "output"
API_KEY_FILE      = DATA_DIR / "api_key.txt"
AI_ANALYSIS_FILE  = OUTPUT_DIR / "ai_analysis.json"
FUNDAMENTAL_FILE  = OUTPUT_DIR / "fundamental_data.json"
ACREAGE_FILE      = OUTPUT_DIR / "acreage_data.json"
COT_FILE          = OUTPUT_DIR / "cot_data.json"
WEATHER_S_FILE    = OUTPUT_DIR / "weather_short.json"
WEATHER_L_FILE    = OUTPUT_DIR / "weather_long.json"
MACRO_FILE        = OUTPUT_DIR / "macro_data.json"
EXPORT_FILE       = OUTPUT_DIR / "export_sales.json"
BLACKSEA_FILE     = OUTPUT_DIR / "blacksea_wheat.json"
VIP_INTEL_FILE    = OUTPUT_DIR / "vip_intel.json"
AI_NEWS_FILE      = OUTPUT_DIR / "ai_news.json"


def get_api_key():
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
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


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^<]+?>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_agweb_market_analysis() -> list:
    """
    Quét trực tiếp chuyên mục AgWeb Market Analysis (https://www.agweb.com/markets/market-analysis)
    kết hợp Bing News RSS & Google News RSS để lấy đầy đủ tiêu đề, tóm tắt nhận định chuyên gia Mỹ và URL.
    """
    articles = []
    seen_titles = set()

    # 1. Bing News RSS cho site:agweb.com/markets/market-analysis (có đầy đủ snippet nhận định chuyên gia)
    bing_url = "https://www.bing.com/news/search?q=site:agweb.com/markets/market-analysis&format=rss"
    print("  [+] Đang quét AgWeb Market Analysis qua Bing News RSS...")
    try:
        req = urllib.request.Request(bing_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            tree = ET.parse(resp)
        for item in tree.findall(".//item")[:8]:
            title = clean_html(item.findtext("title") or "").replace(" - AgWeb", "").strip()
            link = item.findtext("link") or "https://www.agweb.com/markets/market-analysis"
            pub_date = (item.findtext("pubDate") or "")[:16]
            desc = clean_html(item.findtext("description") or "")
            if title and title[:30].lower() not in seen_titles:
                seen_titles.add(title[:30].lower())
                articles.append({
                    "title": title,
                    "pub_date": pub_date,
                    "summary": desc[:450],
                    "link": link,
                })
    except Exception as e:
        print(f"  [WARN] Bing RSS AgWeb: {e}")

    # 2. Jina Reader quét trực tiếp trang https://www.agweb.com/markets/market-analysis
    print("  [+] Đang quét trực tiếp trang https://www.agweb.com/markets/market-analysis...")
    try:
        r = requests.get(
            "https://r.jina.ai/https://www.agweb.com/markets/market-analysis",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=18,
        )
        if r.status_code == 200 and len(r.text) > 500:
            # Tìm các cặp link bài viết và đoạn tóm tắt phía dưới
            pattern = re.findall(
                r"\((https://www\.agweb\.com/markets/market-analysis/[a-z0-9\-]+)\)\s*\n+([^\n!\[\]]{30,350})",
                r.text,
            )
            for link, desc in pattern[:8]:
                slug = link.split("/")[-1].replace("-", " ").title()
                if not any(link == a.get("link") for a in articles):
                    articles.append({
                        "title": slug,
                        "pub_date": "Mới nhất",
                        "summary": desc.strip(),
                        "link": link,
                    })
                else:
                    for a in articles:
                        if a.get("link") == link and len(desc.strip()) > len(a.get("summary", "")):
                            a["summary"] = desc.strip()
    except Exception as e:
        print(f"  [WARN] Jina AgWeb: {e}")

    # 3. Google News RSS bổ sung
    gnews_url = "https://news.google.com/rss/search?q=site:agweb.com/markets/market-analysis+wheat+OR+corn&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(gnews_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            tree = ET.parse(resp)
        for item in tree.findall(".//item")[:6]:
            title = clean_html(item.findtext("title") or "").replace(" - AgWeb", "").strip()
            link = item.findtext("link") or "https://www.agweb.com/markets/market-analysis"
            pub_date = (item.findtext("pubDate") or "")[:16]
            if title and title[:30].lower() not in seen_titles:
                seen_titles.add(title[:30].lower())
                articles.append({
                    "title": title,
                    "pub_date": pub_date,
                    "summary": title,
                    "link": link,
                })
    except Exception as e:
        print(f"  [WARN] Google News AgWeb: {e}")

    return articles[:8]


def analyze():
    print("\n=====================================================================")
    print("  CBOT RUN TIN TỨC 6 PHẦN — BẢNG 5 PHẦN + CHIẾN LƯỢC TÁC CHIẾN PHẦN 6")
    print("=====================================================================")

    api_key = get_api_key()
    if not api_key:
        print("  [WARN] Chưa có API Key. Lưu vào Data/api_key.txt hoặc cấu hình Streamlit Secrets.")
        return False

    print("  [+] Đang đọc toàn bộ dữ liệu thị trường & quét AgWeb Market Analysis...")
    fund     = _load_json(FUNDAMENTAL_FILE)
    cot      = _load_json(COT_FILE)
    weather_s = _load_json(WEATHER_S_FILE)
    weather_l = _load_json(WEATHER_L_FILE)
    macro    = _load_json(MACRO_FILE)
    exports  = _load_json(EXPORT_FILE)
    blacksea = _load_json(BLACKSEA_FILE)
    vip      = _load_json(VIP_INTEL_FILE)
    ai_news  = _load_json(AI_NEWS_FILE)
    signals  = _load_json(OUTPUT_DIR / "last_signals.json")
    meta     = _load_json(OUTPUT_DIR / "contracts_meta.json")

    agweb_articles = fetch_agweb_market_analysis()
    agweb_text = "\n".join(
        [
            f"- [{a.get('pub_date','')}] {a.get('title','')}: {a.get('summary','')} (Link: {a.get('link','')})"
            for a in agweb_articles
        ]
    ) or "Chưa có bài mới từ AgWeb."

    zw = fund.get("ZW", {})
    zc = fund.get("ZC", {})

    zw_liq = meta.get("ZW", {}).get("liquidity", {})
    zc_liq = meta.get("ZC", {}).get("liquidity", {})

    zw_close = zw_liq.get("today_close", macro.get("zw_ref", {}).get("price", "N/A"))
    zw_prev  = zw_liq.get("prev_close", macro.get("zw_ref", {}).get("prev", "N/A"))
    zw_vol   = zw_liq.get("today_volume", "N/A")
    zw_oi    = zw_liq.get("today_oi", "N/A")
    zw_trend = zw_liq.get("trend", "N/A")

    zc_close = zc_liq.get("today_close", macro.get("zc_ref", {}).get("price", "N/A"))
    zc_prev  = zc_liq.get("prev_close", macro.get("zc_ref", {}).get("prev", "N/A"))
    zc_vol   = zc_liq.get("today_volume", "N/A")
    zc_oi    = zc_liq.get("today_oi", "N/A")
    zc_trend = zc_liq.get("trend", "N/A")

    def _cot(code):
        c = cot.get(code, {})
        if not c:
            for v in cot.get("commodities", cot).values():
                if isinstance(v, dict) and v.get("commodity") == code:
                    c = v
                    break
        return c

    cot_zw = _cot("ZW")
    cot_zc = _cot("ZC")

    zw_exp_mt = exports.get("commodities", {}).get("ZW", {}).get("current_mt", zw.get("exports", {}).get("latest", "N/A"))
    zc_exp_mt = exports.get("commodities", {}).get("ZC", {}).get("current_mt", zc.get("exports", {}).get("latest", "N/A"))

    dxy_price = macro.get("dxy", {}).get("price", "N/A")
    dxy_pct   = macro.get("dxy", {}).get("pct", 0)
    brent_p   = macro.get("brent", {}).get("price", "N/A")
    brent_pct = macro.get("brent", {}).get("pct", 0)

    enso_status = weather_l.get("enso_status", "El Niño Watch")
    enso_desc   = weather_l.get("description", "")

    roemer_summary = vip.get("bestweather_report", {}).get("executive_summary", "")
    dj_summary     = vip.get("dowjones_barchart_wrap", {}).get("session_headline", "")

    bs_news = blacksea.get("news", [])
    bs_str = "; ".join([n.get("title", "")[:90] for n in bs_news[:4]]) if bs_news else "Đàm phán 3 bên ở cấp độ kỹ thuật từ 10/11; Nga xuất khẩu qua cảng Baltic."

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""Bạn là Chuyên gia Chiến lược Giao dịch Nông sản CBOT (Senior Commodity Strategist).
Hãy thực thi giao thức **RUN TIN TỨC 6 PHẦN CHUẨN MỰC** tại thời điểm {now_str} (Giờ VN) cho 2 mã: **Lúa mì (W - ZW)** và **Ngô (C - ZC)**.

=== NGUYÊN TẮC CỐT TỬ ===
1. Trung lập khách quan tuyệt đối, không thiên kiến xác nhận (No Confirmation Bias).
2. Phân định rõ tin tức đã phản ánh vào giá (Priced-in) hay là chất xúc tác mới (Fresh Catalyst).
3. Đối chiếu với Trục Fair Value gốc: **ZW = 670 cents**, **ZC = 480 cents** (Sàn chi phí sản xuất: ZW ~ 600-620c, ZC ~ 445-460c).

=== DỮ LIỆU THỰC TẾ HỆ THỐNG ===
[1. Giá & Cấu trúc VSA/Wyckoff & COT]
- Lúa mì (ZW - ZWZ26): Giá hiện tại={zw_close}c (Phiên trước={zw_prev}c) | Volume={zw_vol} | OI={zw_oi} | Cấu trúc: {zw_trend}
  + COT ZW: Báo cáo={cot_zw.get('net_position','N/A')} HĐ | Ước tính hiện tại (Net Est)={cot_zw.get('net_estimated','N/A')} HĐ ({cot_zw.get('quadrant_estimated','N/A')})
- Ngô (ZC - ZCZ26): Giá hiện tại={zc_close}c (Phiên trước={zc_prev}c) | Volume={zc_vol} | OI={zc_oi} | Cấu trúc: {zc_trend}
  + COT ZC: Báo cáo={cot_zc.get('net_position','N/A')} HĐ | Ước tính hiện tại (Net Est)={cot_zc.get('net_estimated','N/A')} HĐ ({cot_zc.get('quadrant_estimated','N/A')})
- Tín hiệu kỹ thuật H1: ZW ({signals.get('ZW',{}).get('setup_type','N/A')} tại {signals.get('ZW',{}).get('setup_entry_range','N/A')}), ZC ({signals.get('ZC',{}).get('setup_type','N/A')} tại {signals.get('ZC',{}).get('setup_entry_range','N/A')})

[2. Cung Cầu, Báo Cáo USDA & Cạnh Tranh Quốc Tế]
- USDA Weekly Export Sales mới nhất: ZW đạt {zw_exp_mt} tấn; ZC đạt {zc_exp_mt} tấn.
- Cạnh tranh quốc tế: Nga xuất khẩu lúa mì qua cảng Baltic & Biển Đen (~267-268 USD/tấn FOB), hạn ngạch xuất khẩu mùa đông sắp áp dụng từ tháng 11.

[3. Địa Chính Trị Biển Đen & Vĩ Mô Liên Thị Trường]
- Biển Đen / Ukraine: {bs_str}
- Vĩ mô: DXY={dxy_price} ({dxy_pct:+.2f}%) | Dầu Brent={brent_p}$ ({brent_pct:+.2f}%)

[4. Thời Tiết & Mùa Vụ 2 Bán Cầu]
- ENSO: {enso_status} — {enso_desc}
- BestWeather (Jim Roemer): {roemer_summary}
- Tiến độ mùa vụ Mỹ: Thu hoạch Ngô đang ở giai đoạn cao điểm (>60-70%), gieo trồng lúa mì vụ Đông thuận lợi nhờ mưa rào nhẹ tại US Plains; Úc và Argentina chuẩn bị bước vào vụ gặt tháng 11.

[5. Chuyên Mục AgWeb Market Analysis (https://www.agweb.com/markets/market-analysis)]
{agweb_text}

=== YÊU CẦU ĐẦU RA (TRẢ VỀ JSON THUẦN, KHÔNG BỌC MARKDOWN) ===
Trả về đúng cấu trúc JSON sau:
{{
  "header_context": {{
    "report_time": "{now_str} (Giờ VN)",
    "zw_price_str": "{zw_close} ¢/bu (Fair Value gốc: 670c)",
    "zc_price_str": "{zc_close} ¢/bu (Fair Value gốc: 480c)",
    "cot_summary": "ZW Net Est: {cot_zw.get('net_estimated','N/A')} HĐ | ZC Net Est: {cot_zc.get('net_estimated','N/A')} HĐ",
    "macro_summary": "DXY: {dxy_price} ({dxy_pct:+.2f}%) | Brent: {brent_p}$"
  }},
  "table_parts": [
    {{
      "part_num": "PHẦN 1",
      "part_title": "Phiên Đêm, Cấu Trúc Giá (VSA/Wyckoff) & Vị Thế COT",
      "core_content": "Phân tích chi tiết hành vi giá, volume, trạng thái cạn cung/thanh lý của cả W và C, vị thế Net Short/Long của quỹ và độ chiết khấu so với Fair Value 670c/480c.",
      "zw_impact": "Nhận định rõ tác động & trạng thái kỹ thuật của mã W",
      "zw_badge": "HỒI PHỤC KỸ THUẬT / TẠO ĐÁY" hoặc "GIẰNG CO TÍCH LŨY" hoặc "ÁP LỰC GIẢM",
      "zc_impact": "Nhận định rõ tác động & trạng thái kỹ thuật của mã C",
      "zc_badge": "DÒ ĐÁY NGẮN HẠN" hoặc "GIẰNG CO TÍCH LŨY" hoặc "ÁP LỰC GIẢM"
    }},
    {{
      "part_num": "PHẦN 2",
      "part_title": "Cung Cầu Thực Tế, Báo Cáo USDA & Cạnh Tranh Quốc Tế",
      "core_content": "Phân tích số liệu USDA Export Sales, mức độ Priced-in vào giá, áp lực hàng giá rẻ từ Nga (Baltic/Biển Đen) và nhu cầu Ethanol/thức ăn chăn nuôi.",
      "zw_impact": "Tác động cung cầu lên mã W (đã Priced-in hay chưa)",
      "zw_badge": "TRUNG TÍNH (ĐÃ PRICED-IN)" hoặc "BEARISH NGẮN HẠN" hoặc "BULLISH",
      "zc_impact": "Tác động cung cầu lên mã C",
      "zc_badge": "HỖ TRỢ NỘI ĐỊA" hoặc "TRUNG TÍNH" hoặc "BEARISH"
    }},
    {{
      "part_num": "PHẦN 3",
      "part_title": "Địa Chính Trị Biển Đen & Vĩ Mô Liên Thị Trường",
      "core_content": "Phân tích bản chất đàm phán 3 bên (cấp kỹ thuật từ 10/11), rủi ro Biển Đen, bầu cử Mỹ (03/11), biến động DXY và giá Dầu thô.",
      "zw_impact": "Tác động địa chính trị & vĩ mô lên mã W",
      "zw_badge": "GIẢM ÁP LỰC BÁN / HỖ TRỢ NHẸ" hoặc "TRUNG TÍNH" hoặc "RỦI RO TIN ĐỒN",
      "zc_impact": "Tác động địa chính trị & năng lượng lên mã C",
      "zc_badge": "HỖ TRỢ TỪ GIÁ DẦU" hoặc "TRUNG TÍNH"
    }},
    {{
      "part_num": "PHẦN 4",
      "part_title": "Thời Tiết (NOAA / Jim Roemer) & Mùa Vụ 2 Bán Cầu",
      "core_content": "Phân tích thời tiết US Plains (lúa mì Đông), Corn Belt (thu hoạch Ngô), tiến độ mùa gặt Nam Bán Cầu (Úc/Argentina T11) và xác suất Super El Niño 2027.",
      "zw_impact": "Tác động thời tiết & mùa vụ lên mã W",
      "zw_badge": "KÌM ĐÀ TĂNG NGẮN / BULLISH 2027",
      "zc_impact": "Tác động thời tiết & thu hoạch lên mã C",
      "zc_badge": "ĐỈNH ÁP LỰC MÙA GẶT"
    }},
    {{
      "part_num": "PHẦN 5",
      "part_title": "Chuyên Mục AgWeb Market Analysis (Góc Nhìn Chuyên Gia Mỹ)",
      "core_content": "Tổng hợp nhận định thực chiến mới nhất từ chuyên mục AgWeb Market Analysis (Mark Schultz, Sam Hudson, DuWayne Bosse, Michelle Rook...) về trạng thái quá bán, tâm lý nông dân Mỹ đóng kho và tìm đáy mùa vụ.",
      "zw_impact": "Kết luận của chuyên gia AgWeb đối với mã W",
      "zw_badge": "QUÁ BÁN - CHỜ HỒI PHỤC (CORRECTION)",
      "zc_impact": "Kết luận của chuyên gia AgWeb đối với mã C",
      "zc_badge": "ĐANG THIẾT LẬP ĐÁY MÙA VỤ (HARVEST LOW)"
    }}
  ],
  "daily_trend_conclusion": {{
    "summary_label": "Tổng hợp trọng số từ 5 Phần trên cho phiên giao dịch hôm nay:",
    "zw_trend_title": "HỒI PHỤC KỸ THUẬT / SHORT-COVERING (HOẶC TÍCH LŨY BIÊN HẸP)",
    "zw_range": "Biên độ dự kiến (ví dụ: 623.0 – 636.0 ¢/bu)",
    "zw_rationale": "1 câu giải thích ngắn gọn lý do chốt xu hướng W",
    "zc_trend_title": "TÍCH LŨY DÒ ĐÁY MÙA VỤ (HARVEST LOW BASE)",
    "zc_range": "Biên độ dự kiến (ví dụ: 456.0 – 468.0 ¢/bu)",
    "zc_rationale": "1 câu giải thích ngắn gọn lý do chốt xu hướng C"
  }},
  "part6_strategy": {{
    "executive_verdict": "Đoạn văn đúc kết toàn diện 3-4 câu từ 5 phần trên: giải thích bức tranh thực tế giữa phe Long và phe Short, tại sao vùng đáy đang giữ vững và định hướng chủ đạo trong ngày.",
    "golden_rules": [
      "Nguyên tắc vàng 1 (về quản trị vốn / tâm thế tiền mặt / vị thế)",
      "Nguyên tắc vàng 2 (những điều cấm kỵ tuyệt đối trong ngày như không FOMO ở cản, không bán đuổi ở đáy cạn cung)",
      "Nguyên tắc vàng 3 (lưu ý về chênh lệch Spread kỳ gần Z và kỳ xa H trước mùa Rollover)"
    ],
    "zw_tactical": {{
      "intraday_contract": "ZWZ26 (HĐ Tháng 12/2026)",
      "intraday_plan": "Chiến thuật bắn tỉa ngắn hạn (Pullback hoặc Breakout), nêu rõ vùng chờ mua, SL và TP.",
      "support_zone": "621.0 – 624.5 ¢/bu",
      "resistance_zone": "631.0 – 638.0 ¢/bu",
      "macro_dca_contract": "ZWH27 (HĐ Tháng 03/2027)",
      "macro_dca_plan": "Kế hoạch chờ gom lại trung-dài hạn đón sóng mùa đông & El Niño 2027 (nêu rõ vùng giá mục tiêu 61x - 63x và thời điểm sau nhiễu đàm phán/rollover)."
    }},
    "zc_tactical": {{
      "intraday_contract": "ZCZ26 (HĐ Tháng 12/2026)",
      "intraday_plan": "Chiến thuật theo dõi tín hiệu tạo đáy ngắn hạn khi áp lực xả thu hoạch suy yếu.",
      "support_zone": "455.0 – 460.0 ¢/bu",
      "resistance_zone": "466.0 – 472.0 ¢/bu",
      "macro_dca_contract": "ZCZ26 / ZCH27",
      "macro_dca_plan": "Chiến lược rải vốn thu gom vùng đáy mùa gặt (Harvest Low) sát sàn chi phí sản xuất của nông dân Mỹ."
    }}
  }}
}}"""

    models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }

    print("  [+] Đang gửi Prompt RUN TIN TỨC 6 PHẦN tới Google Gemini API...")
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=75)
            if response.status_code == 200:
                res_json = response.json()
                text_output = (
                    res_json.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                if text_output:
                    clean_json_str = text_output.replace("```json", "").replace("```", "").strip()
                    structured = json.loads(clean_json_str)
                    result_data = {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "model": model,
                        "version": "run_tin_tuc_6_parts_v1",
                        "structured": structured,
                        "agweb_articles": agweb_articles,
                        "analysis": structured.get("part6_strategy", {}).get("executive_verdict", ""),
                    }
                    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
                    with open(AI_ANALYSIS_FILE, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    print(f"  [OK] RUN TIN TỨC 6 PHẦN hoàn tất! Model: {model} → ai_analysis.json")
                    return True
            else:
                err_msg = response.json().get("error", {}).get("message", response.text[:100])
                print(f"  [WARN] Model {model}: HTTP {response.status_code} — {err_msg}")
        except Exception as e:
            print(f"  [WARN] Model {model} lỗi: {e}")

    print("  [ERR] Tất cả model đều thất bại.")
    return False


if __name__ == "__main__":
    analyze()
