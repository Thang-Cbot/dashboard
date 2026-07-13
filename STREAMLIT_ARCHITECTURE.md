# Cấu trúc & Kiến trúc Hệ thống CBOT Dashboard (Streamlit)

Bản tài liệu này mô tả chi tiết toàn bộ cấu trúc mã nguồn, luồng hoạt động và chức năng của từng tập tin trong dự án CBOT Dashboard của chúng ta.

---

## 1. Kiến trúc Tổng thể (Architecture Overview)

Hệ thống được thiết kế theo mô hình **Tách biệt Frontend và Backend**:
*   **Frontend (Giao diện web - Streamlit):** Đảm nhiệm việc hiển thị dữ liệu một cách trực quan, tương tác với người dùng. Frontend **không trực tiếp gọi API bên ngoài** để tránh việc web bị treo. Nó chỉ làm một nhiệm vụ duy nhất: Đọc file dữ liệu có sẵn trên ổ cứng và hiển thị ra màn hình siêu tốc.
*   **Backend (Data Pipeline & AI):** Tổ hợp các tập tin Python chạy ngầm. Nhiệm vụ của chúng là đi gom dữ liệu từ khắp nơi (USDA, CFTC, Yahoo Finance, Thời tiết), xử lý dữ liệu thô, nhờ AI (Gemini) phân tích, rồi ghi ra các file kết quả (`JSON`, `CSV`).

---

## 2. Sơ đồ Thư mục Cốt lõi (Directory Structure)

```text
Cbot/
│
├── app.py                      # Tệp gốc khởi chạy Web (Trang chủ & Sidebar)
├── components/                 # Các hàm UI và biểu đồ dùng chung
│   └── charts.py               # Chứa logic vẽ biểu đồ Plotly (Nến thật & AI)
│
├── pages/                      # Thư mục chứa các trang chức năng của Web
│   ├── 1_Overview.py           # Tổng quan thị trường & AI Phân tích
│   ├── 2_Profiles.py           # Hồ sơ chi tiết từng mã (ZC, ZW, ZS)
│   ├── 3_News.py               # Báo cáo USDA (WASDE, Acreage, Export)
│   ├── 4_Weather.py            # Phân tích Thời tiết (ENSO)
│   └── 5_AgriMap.py            # Bản đồ Vùng trồng trọt Nông sản
│
└── Data/                       # TRÁI TIM HỆ THỐNG - Dữ liệu & Trí tuệ Nhân tạo
    ├── run_data_update.py      # Bộ kịch bản (Orchestrator) cập nhật TẤT CẢ dữ liệu
    ├── data_scheduler.py       # Công nhân chạy ngầm (Daemon) tự động theo lịch
    ├── ai_analyzer.py          # Khối AI (Gemini) nhận định Fundamental & SMC
    ├── ai_chart_engine.py      # Khối AI dự báo và nội suy nến H1 tương lai
    │
    ├── price/                  # Module cào giá (yfinance), Vĩ mô, COT Matrix
    ├── reports/                # Module cào dữ liệu USDA (ESMIS, NASS API)
    ├── weather/                # Module cào dữ liệu rủi ro thời tiết (NOAA)
    │
    └── output/                 # Thư mục chứa CHUẨN ĐẦU RA cho Streamlit
        ├── ZC_active_H1.csv    # File nến lịch sử thực tế
        ├── ai_simulated_h1.json# Bản lưu trữ nến dự báo tương lai của AI
        └── fundamental_data.json
```

---

## 3. Chức năng chi tiết từng thành phần

### A. Tầng Giao diện (Streamlit Frontend - File hiển thị)

*   **`app.py`:** Điểm neo của toàn bộ ứng dụng. Nhiệm vụ: Thiết lập cấu hình trang (Icon, Title), vẽ thanh menu điều hướng bên trái (Sidebar), hiển thị thông tin trang chủ. Đặc biệt chứa các nút điều khiển trung tâm như `LÀM MỚI TRẠNG THÁI` (để xóa Cache RAM) và `RUN ALL DATA` (kích hoạt kịch bản tải dữ liệu thủ công).
*   **`pages/1_Overview.py`**: Bảng điều khiển (Dashboard) chính. Hiển thị nhanh các chỉ số vĩ mô (DXY, Dầu Brent), trạng thái thị trường tổng quan. Nó cũng chứa khung **AI Trading Desk** - nơi in ra các chiến lược giao dịch tự động do `ai_analyzer.py` đã viết sẵn.
*   **`pages/2_Profiles.py`**: Trái tim của phân tích kỹ thuật. Nơi bạn xem chi tiết từng mã Hàng hóa (Ngô, Lúa mì...). Nó tải biểu đồ nến, vẽ các vùng hỗ trợ/kháng cự SMC (S1/S2/R1/R2) và hiển thị ma trận Dòng tiền thông minh (COT Smart Money).
*   **`pages/3_News.py`**: Trạm dữ liệu cơ bản (Fundamental). Render các bảng biểu dưới dạng HTML gọn gàng cho các báo cáo Cung cầu của chính phủ Mỹ (USDA): WASDE, Diện tích gieo trồng (Acreage), Tiến độ vụ mùa, Xuất khẩu.
*   **`pages/4_Weather.py`**: Màn hình đánh giá rủi ro thời tiết. Có tích hợp thuật toán phân tích màu tự động (Đỏ: Rủi ro hạn hán/ngập lụt, Xanh: Mưa thuận gió hòa) giúp người dùng lướt nhanh tình trạng mùa vụ.
*   **`pages/5_AgriMap.py`**: Giao diện Bản đồ tương tác của Mỹ và các quốc gia cạnh tranh, phối hợp với biểu đồ thời tiết để có cái nhìn trực quan về vị trí địa lý của nguồn cung.
*   **`components/charts.py`**: Nơi chứa toàn bộ phép thuật vẽ biểu đồ `Plotly`. Hàm `render_candlestick` đảm nhận nhiệm vụ phức tạp nhất: Đọc nến AI giả lập từ Thứ 2 đến Thứ 6 -> Đọc nến giá thực tế -> Cắt bỏ các khung giờ không giao dịch (2h sáng - 7h sáng) -> Đè chấm vàng giá thực tế lên nến giả lập.

### B. Tầng Dữ liệu (Data Pipeline & Crawler)

*   **`Data/data_scheduler.py`**: Được thiết kế để chạy liên tục dưới nền máy tính. Nó hẹn giờ tự động: Phút thứ 15 mỗi giờ sẽ tải giá H1; 5h30 sáng tải báo cáo USDA, 2h chiều tải thời tiết... Giúp bạn luôn có dữ liệu tươi mới mà không cần thao tác gì.
*   **`Data/run_data_update.py`**: "Nút bấm đỏ" của hệ thống. Mỗi khi bạn ấn RUN ALL DATA trên web, tệp này sẽ kích hoạt tuần tự 9 bước (Step 1 đến Step 9): Tải Giá -> Vĩ mô -> CFTC (COT) -> USDA -> Thời tiết -> Chạy AI phân tích xu hướng -> Chạy AI vẽ nến H1.
*   **Các thư mục con `price/`, `reports/`, `weather/`**: Tập hợp các "công nhân" (scripts) chuyên biệt. Ví dụ `reports/fetch_acreage.py` chuyên gọi API của NASS, `price/cot.py` chuyên vượt rào CFTC để lấy vị thế Long/Short của Quỹ đầu cơ.

### C. Tầng Trí tuệ Nhân tạo (AI Integration)

*   **`Data/ai_analyzer.py`**: Đóng vai trò **Giám đốc Phân tích**. Sau khi toàn bộ dữ liệu (Thời tiết, Mùa vụ, COT, Giá) được gom về dạng JSON thô, tệp này sẽ tổng hợp lại thành 1 văn bản cực dài (Prompt) và gửi cho Google Gemini. AI sẽ nhận định thị trường dựa trên tư duy SMC và đưa ra lời khuyên mua/bán gom dài hạn. Kết quả được lưu ra file để Streamlit đọc.
*   **`Data/ai_chart_engine.py`**: Đóng vai trò **Trader & Kỹ thuật viên mô phỏng**. Đọc giá đóng cửa mới nhất của thị trường, sau đó hỏi AI xem mục tiêu của các ngày tiếp theo trong tuần là gì (Daily High, Low, Close). Khi có được mục tiêu từ AI, tập lệnh này sử dụng thuật toán nội suy ngẫu nhiên (Interpolation) để tự động sinh ra từng cây nến H1 khớp liền mạch với giá thực tế, vẽ nên con đường di chuyển của giá trong tương lai. Có cơ chế fallback 3 lần (giữa Gemini 2.5 Flash và 1.5 Flash) để chống đứt gãy kết nối mạng.

---

## 4. Kiến trúc Đồng bộ Nguyên khối (V2 Unified Data Pipeline)

Vào tháng 07/2026, luồng xử lý dữ liệu (Data Pipeline) đã được tối ưu hóa để loại bỏ độ trễ và xung đột giữa các module (đặc biệt là giữa Data Scheduler và Entry Alarm):

1. **Gom dữ liệu tại nguồn (Data Scheduler):** Tại phút 15 mỗi giờ giao dịch, `Data/data_scheduler.py` kích hoạt `fetch_prices.py` để tải dữ liệu H1 và Vĩ mô.
2. **Kích hoạt đồng bộ tuần tự (Synchronous Trigger):** Ngay khi việc tải dữ liệu hoàn tất thành công, Scheduler sẽ **lập tức** gọi lệnh phân tích tín hiệu Telegram (`entry_alarm.py` qua lệnh `-c`), cập nhật trạng thái Snapshot (`run_pro_plus.py`) và tạo lại giao diện web (`gen_dashboard.py`).
3. **Chế độ người lắng nghe (Listener Mode):** Tệp `entry_alarm.py` không còn vòng lặp tải dữ liệu độc lập vào phút thứ 16 nữa. Nó chạy thuần túy ở chế độ Telegram Listener, giúp tiết kiệm tài nguyên hệ thống, ngăn chặn việc ghi đè dữ liệu cũ, và đảm bảo mọi thông tin (từ Telegram Alarm, FVG Profile, Dashboard HTML) đồng bộ chính xác trong cùng một tích tắc.
