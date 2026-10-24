import sys
import os
import csv
import re
import json
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
CONTEXT_FILE = DATA_DIR / "tactical_context.json"


def get_api_key():
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading API key: {e}")
        return ""


def _load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _last_close(csv_name):
    """Tra ve (close, date, low_cua_phien_cuoi) tu file D1; None neu loi."""
    try:
        with open(OUTPUT_DIR / csv_name, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        last = rows[-1]
        date = last.get("Time") or last.get("Date") or ""
        return float(last["Close"]), str(date)[:10], float(last["Low"])
    except Exception:
        return None


def _macro_brief(macro):
    bd = macro.get("breakdown", {})
    out = {"total_score": macro.get("total_score")}
    for k, v in bd.items():
        out[k] = {"score": v.get("score_1_to_10"), "note": str(v.get("raw_detail", v.get("raw_value", "")))[:140]}
    return out


def _cot_brief(cot, code):
    c = cot.get("commodities", {}).get(code, {})
    keys = ["report_date", "net_position", "net_prev", "change", "quadrant",
            "net_estimated", "estimated_extra_contracts", "quadrant_estimated",
            "latest_price", "latest_price_date"]
    return {k: c.get(k) for k in keys}


def build_prompt():
    ctx = _load_json(CONTEXT_FILE)
    cot = _load_json(OUTPUT_DIR / "cot_data.json")
    meta = _load_json(OUTPUT_DIR / "contracts_meta.json")
    macro_zw = _load_json(OUTPUT_DIR / "macro_scores_zw.json")
    macro_zc = _load_json(OUTPUT_DIR / "macro_scores_zc.json")

    prices = {
        "ZWZ26 (active)": _last_close("ZW_active_D1.csv"),
        "ZWH27 (swing)": _last_close("ZW_swing_D1.csv"),
        "ZCZ26 (active)": _last_close("ZC_active_D1.csv"),
        "ZCH27 (swing)": _last_close("ZC_swing_D1.csv"),
    }
    prices_txt = "\n".join(
        f"- {k}: close {v[0]} cent/bu (ngay {v[1]}, low phien {v[2]})" if v else f"- {k}: khong co du lieu"
        for k, v in prices.items()
    )

    liq_zw = meta.get("ZW", {}).get("liquidity", {})
    liq_zc = meta.get("ZC", {}).get("liquidity", {})

    return f"""
Bạn là chuyên gia chiến lược hàng hóa nông sản CBOT cấp cao (Lúa mì W & Ngô C). Hãy lập BẢNG TỔNG HỢP TÁC CHIẾN cho cửa sổ thời gian: {ctx.get('window', '2 tuần tới')}.

=== DỮ LIỆU ĐẦU VÀO (chỉ dùng số liệu dưới đây, KHÔNG bịa số) ===
1. GIÁ ĐÓNG CỬA MỚI NHẤT:
{prices_txt}

2. TÀI KHOẢN & QUẢN TRỊ VỐN: {json.dumps(ctx.get('account', {}), ensure_ascii=False)}; ký quỹ/lot (USD): {json.dumps(ctx.get('margin_per_lot_usd', {}), ensure_ascii=False)}

3. COT MANAGED MONEY:
- Lúa mì: {json.dumps(_cot_brief(cot, '001602'), ensure_ascii=False)} | Ghi chú: {ctx.get('official_cot_note', {}).get('ZW', '')}
- Ngô: {json.dumps(_cot_brief(cot, '002602'), ensure_ascii=False)} | Ghi chú: {ctx.get('official_cot_note', {}).get('ZC', '')}

4. MACRO SCORE:
- Lúa mì: {json.dumps(_macro_brief(macro_zw), ensure_ascii=False)}
- Ngô: {json.dumps(_macro_brief(macro_zc), ensure_ascii=False)}

5. THANH KHOẢN (Volume/OI):
- ZW: {liq_zw.get('trend', '')} — {liq_zw.get('logic', '')}
- ZC: {liq_zc.get('trend', '')} — {liq_zc.get('logic', '')}

6. LỊCH SỰ KIỆN: Tuần 1: {ctx.get('calendar', {}).get('week_1', '')} || Tuần 2: {ctx.get('calendar', {}).get('week_2', '')}

7. SÀN CHI PHÍ HÒA VỐN (cent/bu): {json.dumps(ctx.get('break_even_cents', {}), ensure_ascii=False)}

8. KẾ HOẠCH TÁC CHIẾN CỦA TRADER (BẮT BUỘC tôn trọng các mốc giá này; chỉ điều chỉnh nếu dữ liệu giá/COT ở trên mâu thuẫn rõ ràng và phải nêu lý do):
{json.dumps(ctx.get('playbook', {}), ensure_ascii=False, indent=1)}

=== YÊU CẦU ĐẦU RA (Markdown, tiếng Việt, đúng khuôn mẫu) ===
Bắt buộc xuất ĐÚNG cấu trúc sau, không thêm lời chào:

### ⚔️ BẢNG TỔNG HỢP TÁC CHIẾN 2 TUẦN TỚI ({ctx.get('window', '')}): LÚA MÌ (W) & NGÔ (C)
*(1 dòng tóm tắt: số dư tài khoản, số vị thế mở)*

#### 1. BẢNG MA TRẬN TÁC CHIẾN TỔNG HỢP
Một bảng Markdown 3 cột: | Tiêu Chí So Sánh | 🌾 LÚA MÌ CBOT (WHEAT - W) | 🌽 NGÔ CBOT (CORN - C) |
Với ĐÚNG các hàng, theo thứ tự:
Mã Hợp Đồng Tác Chiến; Giá Đóng Cửa Tuần Qua (kèm spread Contango H27-Z26); Vị Thế Quỹ (COT chính thức); Thuật Toán Realtime; Trạng Thái Dòng Tiền (góc phần tư COT + nhận định Short Squeeze/Xả Long); Bối Cảnh Tuần 1; Bối Cảnh Tuần 2; Sàn Chi Phí Vốn (Break-even); VÙNG GOM CHIẾN LƯỢC (Tranche 1); VÙNG ĐỆM QUÉT ĐÁY (Tranche 2); Điểm Kích Hoạt Bùng Nổ (Trigger); Mục Tiêu Chốt Lời (kèm lợi nhuận USD/lot, 1 cent/bu = 50 USD/lot); Ngưỡng Cắt Lỗ Cứng (Stop Loss).
Dùng <br> để xuống dòng trong ô, dùng `...` cho số giá.

#### 2. KẾ HOẠCH ĐIỀU ĐỘNG ĐẠN DƯỢC
Gạch đầu dòng: Trạng thái hiện tại; Lúa mì (quy mô, cách đi lệnh Tranche 1/2, quy tắc scalp); Ngô (quy mô, cách đi lệnh, quy tắc không bắt đáy sớm); Tỷ lệ quản trị rủi ro (tổng ký quỹ tối đa tính từ ký quỹ/lot ở trên, % tài khoản, tiền mặt tự do còn lại).

#### 3. NHẬN ĐỊNH RỦI RO & KỊCH BẢN SAI
2-3 gạch đầu dòng ngắn: điều kiện nào làm vô hiệu kế hoạch (ví dụ giá thủng stop, COT đảo chiều, tin địa chính trị bất ngờ).

Nguyên tắc: Zero-Hallucination, No Narrative Spinning, trung lập, không thiên vị Bullish hay Bearish; mọi con số phải đến từ dữ liệu đầu vào hoặc phép tính trực tiếp từ chúng.
"""


def call_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
    return res_data["candidates"][0]["content"]["parts"][0]["text"]


def generate_ai_analysis(commodity="ZW"):
    """Sinh Bang Ma Tran Tac Chien (W & C) va ghi vao file cua `commodity` (2 tab dung chung noi dung)."""
    print(f"[{commodity}] Building tactical table prompt...")
    api_key = get_api_key()
    if not api_key:
        print("No API Key found.")
        return False

    analysis_file = OUTPUT_DIR / f"ai_muavu_analysis_{commodity.lower()}.json"
    print(f"[{commodity}] Calling Gemini API...")
    try:
        ai_text = call_gemini(build_prompt(), api_key)
        # Streamlit coi $...$ là công thức LaTeX -> escape ký hiệu USD
        ai_text = re.sub(r"(?<!\\)\$", r"\\$", ai_text)
        out_data = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis": ai_text,
        }
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
        print(f"[{commodity}] AI Analysis generated successfully!")
        return True
    except Exception as e:
        print(f"[{commodity}] Gemini API Error: {e}")
        return False


if __name__ == "__main__":
    # Bang tac chien dung chung cho ca 2 tab -> goi API 1 lan, ghi ra 2 file.
    ok = generate_ai_analysis("ZW")
    if ok:
        src = OUTPUT_DIR / "ai_muavu_analysis_zw.json"
        dst = OUTPUT_DIR / "ai_muavu_analysis_zc.json"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print("[ZC] Synced from ZW tactical table.")
    else:
        sys.exit(1)
