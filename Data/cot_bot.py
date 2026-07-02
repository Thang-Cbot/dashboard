import requests
import pandas as pd

# Từ điển mã hợp đồng CFTC
CFTC_CODES = {
    "Ngô (ZC)": "002602",
    "Lúa mì (ZW)": "001602"
}

def fetch_cot_data(commodity_name, cftc_code):
    """
    Kéo dữ liệu COT Disaggregated (Futures Only) từ CFTC API cho 2 tuần gần nhất
    """
    # API Endpoint của CFTC (Public)
    url = "https://publicreporting.cftc.gov/resource/72hh-3qxg.json"
    
    # Query parameters: Lọc theo mã, lấy 2 dòng mới nhất (2 tuần gần nhất)
    params = {
        "cftc_contract_market_code": cftc_code,
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 2
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if len(data) < 2:
            return f"Không đủ dữ liệu cho {commodity_name}"
        
        # Dữ liệu tuần hiện tại (Index 0)
        current_week = data[0]
        # Dữ liệu tuần trước (Index 1)
        prev_week = data[1]
        
        # Lấy thông số Managed Money
        long_curr = float(current_week.get('m_money_positions_long_all', 0))
        short_curr = float(current_week.get('m_money_positions_short_all', 0))
        
        long_prev = float(prev_week.get('m_money_positions_long_all', 0))
        short_prev = float(prev_week.get('m_money_positions_short_all', 0))
        
        # Tính toán Net Position
        net_curr = long_curr - short_curr
        net_prev = long_prev - short_prev
        change = net_curr - net_prev
        
        # Phân loại Ma Trận 4 Ô (Quadrants)
        quadrant = ""
        action = ""
        
        if net_curr > 0 and change > 0:
            quadrant = "Q1 (MÀU XANH LÁ)"
            action = "GOM LONG - Bùng nổ xu hướng tăng. Ưu tiên LONG."
        elif net_curr > 0 and change < 0:
            quadrant = "Q2 (MÀU ĐỎ NHẠT)"
            action = "XẢ LONG - Áp lực chốt lời/tháo chạy. Ưu tiên Canh SHORT."
        elif net_curr < 0 and change < 0:
            quadrant = "Q3 (MÀU ĐỎ ĐẬM)"
            action = "NHỒI SHORT - Bùng nổ xu hướng giảm. Ưu tiên SHORT."
        elif net_curr < 0 and change > 0:
            quadrant = "Q4 (MÀU VÀNG CAM)"
            action = "COVER SHORT - Bẫy ép mua (Short Squeeze). Cấm Short đuổi, Canh LONG bắt hồi."
            
        # In Báo Cáo
        print(f"[{current_week['report_date_as_yyyy_mm_dd'][:10]}] PHÂN TÍCH COT: {commodity_name}")
        print(f" - Trạng thái ròng (Net Position): {net_curr:,.0f} hợp đồng")
        print(f" - Biến động so với tuần trước: {change:+,.0f} hợp đồng")
        print(f" => Xếp hạng Ma Trận: {quadrant}")
        print(f" => Khuyến nghị Action: {action}")
        print("-" * 60)
        
    except Exception as e:
        print(f"Lỗi khi kéo dữ liệu {commodity_name}: {e}")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    print("=" * 60)
    print(" KHỞI ĐỘNG BOT PHÂN TÍCH DÒNG TIỀN COT (MANAGED MONEY) ")
    print("=" * 60)
    
    for name, code in CFTC_CODES.items():
        fetch_cot_data(name, code)
