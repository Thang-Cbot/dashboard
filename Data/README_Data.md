# 📊 Cbot Data Project — Hướng Dẫn Sử Dụng

## Mục Tiêu

**Data/** là **nguồn dữ liệu CHUẨN và DUY NHẤT** cho toàn bộ hệ thống Cbot.
Chỉ cần chạy **1 lệnh** → tất cả dữ liệu được cập nhật đồng bộ cho mọi lệnh khác.

---

## 🏗️ Kiến Trúc Hệ Thống (Mới)

Thư mục `Data/` được chia thành các phân khu chuyên biệt và chạy ngầm bằng Scheduler:

- `Data/price/`: Quản lý nến H1, Macro (Brent, DXY) và COT (CFTC). Chạy ở phút 15 mỗi giờ giao dịch.
- `Data/weather/`: Quét API thời tiết ngắn hạn (Open-Meteo) và dự báo ENSO dài hạn (NOAA). Chạy hàng ngày.
- `Data/reports/`: Xử lý báo cáo USDA (Crop Progress, WASDE, Export Sales). Tự động lấy "Kỳ này" và "Kỳ trước".
- `Data/output/`: Chứa tất cả kết quả file `.csv` và `.json` đầu ra để các lệnh khác sử dụng.
- `data_scheduler.py`: Bộ não điều phối chạy ngầm định kỳ toàn bộ các lệnh trên.

---

## 🚀 Cách Sử Dụng (Lệnh Tắt)

Tôi đã thiết lập sẵn 3 lệnh tắt (Batch Files) ở ngoài thư mục gốc Cbot, chỉ cần bấm đúp chuột:

1. **`RUN ALL DATA.bat`**
   - **Tác dụng:** Vừa cập nhật toàn bộ dữ liệu NGAY LẬP TỨC (tức thời), vừa bật lên cửa sổ chạy ngầm (Scheduler) để lấy dữ liệu tự động các khung giờ sau.
2. **`RUN NGẦM DATA.bat`**
   - **Tác dụng:** Chỉ bật cửa sổ chạy ngầm, không kích hoạt cập nhật ngay lúc đó. Hệ thống sẽ đợi đến khung giờ được lập trình (ví dụ phút thứ 15) mới quét.
3. **`RUN DATA.bat`**
   - **Tác dụng:** Cập nhật đồng bộ tức thời mọi dữ liệu ngay tại giây phút bấm lệnh. Phù hợp khi bạn cần xem số liệu mới nhất mà không muốn đợi lịch chạy ngầm.

---

## 🛠️ Tránh Xung Đột Hệ Thống
Lệnh `entry_alarm.py` đã được tách bạch với luồng Data. Lệnh Entry Alarm sẽ chỉ quét cảnh báo ở **phút 16** để đảm bảo Data Scheduler đã nạp xong số liệu ở phút 15. Bạn có thể mở đồng thời file chạy ngầm và Alarm bot mà không lo crash hoặc xung đột.

---

## 📁 Cấu Trúc Thư Mục

```
Data/
├── run_data_update.py    ⭐ Script chính — chạy tất cả
├── run_data.bat          🖱️ Double-click để chạy
├── data_config.py        🔧 Config trung tâm (paths, settings)
├── fetch_usda.py         📡 Fetch USDA/WASDE data
├── fetch_prices.py       📈 Fetch Price CSV (ZC/ZW/ZS H1)
├── fetch_macro.py        🌍 Fetch Brent, DXY
├── fetch_cot.py          💰 Fetch COT Managed Money (CFTC)
├── COT_Smart_Money_Matrix.md   📚 Tài liệu tham chiếu COT
├── README_Data.md        📖 File này
│
└── output/               📂 Tất cả output data (NGUỒN CHUẨN)
    ├── fundamental_data.json   USDA/WASDE + Chiến lược + Thời tiết
    ├── macro_data.json         Brent Crude, DXY, ZW Reference
    ├── cot_data.json           COT Managed Money (5 hàng hóa)
    ├── daily_market_history.json  Volume/OI lịch sử
    ├── contracts_meta.json     Thông tin hợp đồng Active/Swing/DCA
    ├── data_status.json        Trạng thái cập nhật mỗi module
    ├── ZC_active_H1.csv  ┐
    ├── ZC_swing_H1.csv   ├ Giá ngô (Corn)
    ├── ZC_dca_H1.csv     ┘
    ├── ZW_active_H1.csv  ┐
    ├── ZW_swing_H1.csv   ├ Giá lúa mì (Wheat)
    ├── ZW_dca_H1.csv     ┘
    ├── ZS_active_H1.csv  ┐
    ├── ZS_swing_H1.csv   ├ Giá đậu tương (Soybeans)
    └── ZS_dca_H1.csv     ┘
```

---

## 📋 Dữ Liệu Được Cập Nhật

### 🔄 Tự động (bot fetch)
| Module | Nguồn | Dữ liệu |
|--------|-------|---------|
| `fetch_usda.py` | USDA ESMIS API | WASDE, Crop Progress, Export Inspections |
| `fetch_prices.py` | Yahoo Finance (yfinance) | H1 Price CSV + Technical Analysis |
| `fetch_macro.py` | Yahoo Finance (yfinance) | Brent Crude (BZ=F), DXY (DX-Y.NYB) |
| `fetch_cot.py` | CFTC Public API | COT Managed Money cho 5 hàng hóa |

### ✏️ Thủ công (AI/người dùng cập nhật vào `fundamental_data.json`)
- Thời tiết ngắn hạn (Midwest, Plains)
- Thời tiết dài hạn (ENSO: La Niña/El Niño)
- Thời tiết + sản lượng đối thủ (Brazil, Argentina, Nga, Úc)
- Nhu cầu nhập khẩu (Trung Quốc, Ai Cập, Mexico...)
- Chiến lược intraday/swing/DCA
- Tồn kho dự báo trước WASDE

---

## 🔌 Tích Hợp cho Các Lệnh Khác

Tất cả lệnh khác đã được cập nhật tự động đọc từ `Data/output/`.
Để tích hợp một lệnh mới:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Data'))
from data_config import OUTPUT_DIR, FUNDAMENTAL_DATA, get_csv_path

# Đọc fundamental data
import json
with open(FUNDAMENTAL_DATA, 'r', encoding='utf-8') as f:
    fund = json.load(f)

# Đọc price CSV
import pandas as pd
df = pd.read_csv(get_csv_path('ZC', 'active'))

# Đọc macro data
with open(OUTPUT_DIR / 'macro_data.json', 'r', encoding='utf-8') as f:
    macro = json.load(f)
```

---

## 🕐 Khuyến Nghị Lịch Chạy

| Thời điểm | Hành động |
|-----------|-----------|
| Trước khi chạy V3 Pro | Chạy `run_data.bat` 1 lần |
| Sau khi có báo cáo USDA mới | Chạy `run_data.bat` |
| Thứ Sáu tối (sau khi CFTC release COT) | Chạy `run_data.bat` |
| Mỗi ngày giao dịch | Chạy `run_data.bat` (khuyến nghị) |

---

## ⚠️ Lưu Ý

- **Không sửa trực tiếp** các file trong `output/` — dữ liệu sẽ bị ghi đè khi chạy update
- **Thời tiết và chiến lược** phải cập nhật thủ công vào `output/fundamental_data.json`
- Nếu một module bị lỗi (ví dụ: USDA API down), các module khác vẫn chạy bình thường
- Kiểm tra `output/data_status.json` để xem trạng thái từng module
