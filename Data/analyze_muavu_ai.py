import sys
import os
import json
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent
OUTPUT_DIR = DATA_DIR / "output"
API_KEY_FILE = DATA_DIR / "api_key.txt"
ANALYSIS_FILE = OUTPUT_DIR / "ai_muavu_analysis_zw.json"

def get_api_key():
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading API key: {e}")
        return ""

def generate_ai_analysis():
    print("Loading data for AI analysis...")
    api_key = get_api_key()
    if not api_key:
        print("No API Key found.")
        return False

    # Load data
    try:
        macro = json.loads((OUTPUT_DIR / "macro_scores.json").read_text(encoding="utf-8"))
    except: macro = {}
    
    try:
        fund = json.loads((OUTPUT_DIR / "fundamental_data.json").read_text(encoding="utf-8"))
    except: fund = {}
    
    try:
        cot = json.loads((OUTPUT_DIR / "cot_data.json").read_text(encoding="utf-8"))
    except: cot = {}

    # Compile prompt
    prompt = f"""
Bạn là một chuyên gia phân tích lúa mì (CBOT Wheat) cấp cao. 
Tôi muốn bạn phân tích tính mùa vụ (Seasonality) và Độ lệch pha mùa vụ của 4 khu vực chính, kết hợp với các chỉ báo Vĩ mô hiện tại để đưa ra KẾ HOẠCH GOM HÀNG DCA DÀI HẠN.

=== DỮ LIỆU ĐẦU VÀO ===
1. MACRO SCORE HIỆN TẠI: {macro.get('total_score')} / 100
- Chính sách Nga (F1): {macro.get('breakdown', {}).get('F1', {}).get('score_1_to_10')} (Note: {macro.get('breakdown', {}).get('F1', {}).get('raw_detail')})
- Nguồn cung EU (F3): {macro.get('breakdown', {}).get('F3', {}).get('score_1_to_10')} (Note: {macro.get('breakdown', {}).get('F3', {}).get('raw_detail')})
- Thời tiết Nam Bán cầu (F4): {macro.get('breakdown', {}).get('F4', {}).get('score_1_to_10')} (Note: {macro.get('breakdown', {}).get('F4', {}).get('raw_detail')})
- Sản lượng Nam Bán cầu (F4S): {macro.get('breakdown', {}).get('F4S', {}).get('score_1_to_10')} (Note: {macro.get('breakdown', {}).get('F4S', {}).get('raw_detail')})
- DXY (F9): {macro.get('breakdown', {}).get('F9', {}).get('raw_value')}
- Nhu cầu Thế giới (F12): {macro.get('breakdown', {}).get('F12', {}).get('score_1_to_10')} (Note: {macro.get('breakdown', {}).get('F12', {}).get('raw_detail')})

2. DÒNG TIỀN COT (MANAGED MONEY):
{json.dumps(cot.get('commodities', {}).get('001602', {}), ensure_ascii=False)}

=== YÊU CẦU ĐẦU RA ===
Hãy viết một bài phân tích ngắn gọn, súc tích (dưới 400 chữ), chia làm 2 phần:
Phần 1: Nhận diện Độ lệch pha Mùa vụ (Seasonality Overlap). Xác định Áp lực BÁN MẠNH NHẤT trên toàn cầu đang rơi vào thời điểm nào (Tháng mấy) dựa trên vụ thu hoạch của Nga và Nam Bán cầu.
Phần 2: Action Plan (Kế hoạch DCA). Căn cứ vào điểm số Vĩ mô và COT, hãy đưa ra:
- Khung thời gian an toàn để bắt đầu gom (Timing).
- Đánh giá tổng quan xu hướng dài hạn (Bullish/Bearish).
Lưu ý: Viết bằng tiếng Việt, định dạng Markdown đẹp, chuyên nghiệp, sắc bén. Tuyệt đối bám sát nguyên tắc "Định giá kỳ vọng" (chỉ quan tâm sự thay đổi so với kỳ vọng trước đó).
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    print("Calling Gemini API...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            ai_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            
            out_data = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analysis": ai_text
            }
            with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
                json.dump(out_data, f, ensure_ascii=False, indent=2)
            print("AI Analysis generated successfully!")
            return True
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return False

if __name__ == "__main__":
    generate_ai_analysis()
