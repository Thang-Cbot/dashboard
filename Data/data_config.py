"""
data_config.py — Cấu hình Trung tâm (Central Config)
======================================================
File này định nghĩa TẤT CẢ đường dẫn dữ liệu cho toàn bộ hệ thống Cbot.
Mọi lệnh khác chỉ cần import từ đây để đảm bảo đồng bộ 100%.

Cách dùng:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Data'))
    from data_config import OUTPUT_DIR, FUNDAMENTAL_DATA, get_csv_path
    # hoặc từ trong thư mục Data/:
    from data_config import OUTPUT_DIR, FUNDAMENTAL_DATA, get_csv_path
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# THƯ MỤC GỐC
# ─────────────────────────────────────────────
# Thư mục chứa file data_config.py này (= Cbot/Data/)
DATA_DIR = Path(__file__).parent.resolve()

# Thư mục gốc Cbot/ (= cha của Data/)
CBOT_ROOT = DATA_DIR.parent

# Thư mục output — nguồn dữ liệu chuẩn DUY NHẤT
OUTPUT_DIR = DATA_DIR / "output"

# ─────────────────────────────────────────────
# JSON DATA FILES
# ─────────────────────────────────────────────
FUNDAMENTAL_DATA   = OUTPUT_DIR / "fundamental_data.json"
MACRO_DATA         = OUTPUT_DIR / "macro_data.json"
COT_DATA           = OUTPUT_DIR / "cot_data.json"
DAILY_HISTORY      = OUTPUT_DIR / "daily_market_history.json"
LAST_SIGNALS       = OUTPUT_DIR / "last_signals.json"
DATA_STATUS        = OUTPUT_DIR / "data_status.json"

# ─────────────────────────────────────────────
# CSV PRICE FILES
# ─────────────────────────────────────────────
# Các suffix hợp lệ: "active", "swing", "dca"
def get_csv_path(commodity_code: str, suffix: str) -> Path:
    """
    Trả về đường dẫn tuyệt đối đến file CSV H1 của hợp đồng.
    
    Ví dụ:
        get_csv_path("ZC", "active")  →  .../Data/output/ZC_active_H1.csv
        get_csv_path("ZW", "swing")   →  .../Data/output/ZW_swing_H1.csv
    """
    return OUTPUT_DIR / f"{commodity_code}_{suffix}_H1.csv"

def get_csv_str(commodity_code: str, suffix: str) -> str:
    """Trả về đường dẫn dạng string (tiện dùng với pandas, shutil, v.v.)"""
    return str(get_csv_path(commodity_code, suffix))

# ─────────────────────────────────────────────
# USDA CRAWLER PATH
# ─────────────────────────────────────────────
# Đường dẫn đến usda_crawler.py trong thư mục gốc Cbot/
USDA_CRAWLER_PATH  = CBOT_ROOT / "usda_crawler.py"

# ─────────────────────────────────────────────
# TECHNICAL ANALYSIS PATH
# ─────────────────────────────────────────────
TECHNICAL_ANALYSIS_PATH = CBOT_ROOT / "technical_analysis.py"

# ─────────────────────────────────────────────
# DANH SÁCH CÁC MÃ HÀNG HÓA CHÍNH
# ─────────────────────────────────────────────
COMMODITY_CODES = {
    "ZC": "CORN",
    "ZW": "WHEAT"
}

# ─────────────────────────────────────────────
# MÃ CFTC (dùng cho COT fetch)
# ─────────────────────────────────────────────
CFTC_CODES = {
    "002602": "ZC",  # Corn
    "001602": "ZW"   # Wheat
}

# ─────────────────────────────────────────────
# TICKER SYMBOLS (yfinance)
# ─────────────────────────────────────────────
MACRO_TICKERS = {
    "brent": "BZ=F",
    "dxy":   "DX-Y.NYB",
    "zw_ref": "ZW=F",   # Tham chiếu liên thị trường lúa mì
}

# Cấu hình tháng giao dịch cho từng hàng hóa
CONTRACT_MONTHS = {
    "ZC": [("H", 3), ("K", 5), ("N", 7), ("U", 9), ("Z", 12)],
    "ZW": [("H", 3), ("K", 5), ("N", 7), ("U", 9), ("Z", 12)],
}

# Hợp đồng DCA (vụ mới) cho từng mã
DCA_CONTRACT = {
    "ZC": ("Z", 12),
    "ZW": ("Z", 12),
}

# ─────────────────────────────────────────────
# KIỂM TRA / KHỞI TẠO
# ─────────────────────────────────────────────
def ensure_output_dir():
    """Đảm bảo thư mục output tồn tại."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_all_status() -> dict:
    """Đọc trạng thái cập nhật mới nhất của từng module."""
    import json
    if DATA_STATUS.exists():
        try:
            with open(DATA_STATUS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def update_status(module: str, status: str, detail: str = ""):
    """Cập nhật trạng thái cho một module vào data_status.json."""
    import json
    from datetime import datetime
    data = get_all_status()
    data[module] = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    ensure_output_dir()
    with open(DATA_STATUS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("=== DATA CONFIG — Cbot Data Project ===")
    print(f"DATA_DIR       : {DATA_DIR}")
    print(f"OUTPUT_DIR     : {OUTPUT_DIR}")
    print(f"FUNDAMENTAL    : {FUNDAMENTAL_DATA}")
    print(f"MACRO_DATA     : {MACRO_DATA}")
    print(f"COT_DATA       : {COT_DATA}")
    print(f"ZC active CSV  : {get_csv_path('ZC', 'active')}")
    print(f"ZW swing  CSV  : {get_csv_path('ZW', 'swing')}")
    ensure_output_dir()
    print("Output dir OK.")
