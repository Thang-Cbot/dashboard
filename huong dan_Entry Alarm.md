# Hướng Dẫn Vận Hành Hệ Thống CBOT Entry Alarm (ICT/SMC)

Tài liệu này mô tả chi tiết quy trình hoạt động, cấu trúc mã nguồn và cách thức vận hành của dự án **CBOT Entry Alarm** – hệ thống Bot Telegram tự động quét và cảnh báo điểm vào lệnh cho các mặt hàng nông sản (Ngô - ZC, Lúa mì - ZW, Đậu tương - ZS) dựa trên phương pháp giao dịch ICT/SMC kết hợp EMA.

---

## 1. Tổng Quan Dự Án

*   **Mục tiêu:** Tự động hóa việc theo dõi thị trường hàng hóa phái sinh CBOT trên khung thời gian H1.
*   **Chiến lược cốt lõi:** Giao dịch thuận xu hướng kết hợp Pullback. Tìm điểm vào lệnh (Entry) tại vùng **EMA 21 - EMA 50** khi có sự xác nhận từ cấu trúc thị trường (Market Structure Shift - MSS) và các vùng thanh khoản (Liquidity Sweep, Order Block, FVG, Breaker Block).
*   **Nền tảng cảnh báo:** Telegram Bot (gửi tin nhắn đến User và Group).
*   **Mã giao dịch chính:** `ZC` (Ngô), `ZW` (Lúa mì), `ZS` (Đậu tương).

---

## 2. Cấu Trúc Hệ Thống

Dự án bao gồm các thành phần chính sau:

### 2.1. Mã nguồn Python
*   **`entry_alarm.py` (Trái tim của hệ thống):**
    *   Chạy vòng lặp ngầm (background loop) 24/7.
    *   Mỗi giờ một lần (hoặc khi người dùng yêu cầu), gọi script lấy dữ liệu, phân tích và gửi cảnh báo nếu có setup.
    *   Xử lý tương tác Telegram (Polling) để nhận lệnh từ nút bấm "🔍 Scan Bot".
*   **`ict_engine.py` (Bộ não phân tích - Phiên bản 2.0):**
    *   Chứa toàn bộ logic phân tích ICT/SMC.
    *   Phát hiện: Swing Points, Liquidity Sweeps, CHoCH, MSS, Fair Value Gaps (FVG), High Quality Order Blocks (HQ OB), Breaker Blocks.
    *   Đánh giá Setup (Long/Short) và chấm điểm Win Rate.
*   **`update_active_data.py`:**
    *   Kết nối với thư viện `yfinance` để tải dữ liệu giá lịch sử và giá realtime cho các hợp đồng tương lai đang active có thanh khoản cao nhất.
    *   Tính toán các chỉ báo kỹ thuật cơ bản (EMA, RSI, ATR, Pivot Points).
*   **`debug_ict.py`:**
    *   Công cụ chạy độc lập để kiểm tra và in ra màn hình console kết quả phân tích chi tiết của engine mà không cần gửi tin nhắn Telegram.

### 2.2. Dữ liệu (Local Storage)
*   **`*_active_H1.csv` (`ZC_active_H1.csv`, v.v.):** Lưu trữ dữ liệu nến H1 mới nhất.
*   **`last_signals.json`:** Lưu trạng thái tín hiệu gần nhất để tránh spam tin nhắn trùng lặp.
*   **`active_contracts.json`:** Lưu thông tin hợp đồng đang có thanh khoản cao nhất được tự động chọn để theo dõi.

---

## 3. Quy Trình Hoạt Động (Workflow)

Hệ thống hoạt động theo quy trình tự động sau:

1.  **Định kỳ hàng giờ (hoặc khi bấm Scan Bot):** `entry_alarm.py` kích hoạt tiến trình phân tích.
2.  **Cập nhật dữ liệu:** Gọi `update_active_data.py`. Bot sẽ kiểm tra thanh khoản các hợp đồng (ví dụ: ZCZ26 vs ZCU26) để tự động switch sang hợp đồng active nhất. Sau đó tải dữ liệu nến H1 từ Yahoo Finance và lưu vào file CSV.
3.  **Phân tích kỹ thuật (ICT Engine v2.0):** `entry_alarm.py` đọc file CSV và truyền dữ liệu vào `ict_engine.py`. Engine sẽ:
    *   Xác định xu hướng chính dựa trên **MSS (Market Structure Shift)**.
    *   Lọc nhiễu bằng cách kiểm tra **Sweep** (Quét thanh khoản) và **CHoCH** (Change of Character) trước khi xác nhận MSS thật.
    *   Tìm các vùng hỗ trợ/kháng cự: **HQ OB** (thân nến >= 0.55 ATR), **FVG**, **Breaker Block**.
    *   Xác định vùng Entry là khoảng giữa **EMA 21 và EMA 50**.
    *   Kiểm tra điều kiện: Giá hiện tại có đang nằm chờ Pullback về vùng EMA hay không? Tính toán Stoploss, Take Profit (R:R 1:2) và Win Rate.
4.  **Cảnh báo Telegram:** Nếu có Setup hợp lệ (Win Rate >= 65%) VÀ tín hiệu này là mới (so với `last_signals.json`), Bot sẽ soạn tin nhắn định dạng và gửi qua Telegram. Nếu người dùng chủ động bấm "Scan Bot" mà không có tín hiệu mới, Bot sẽ trả về lại tín hiệu cũ gần nhất kèm theo chú thích thời gian.

---

## 4. Chi tiết Logic ICT v2.0

*   **Entry Zone (Vùng vào lệnh):** Mặc định sử dụng vùng giữa EMA 21 và EMA 50. Đây là vùng "Fair Value" được các Quỹ Managed Money sử dụng nhiều nhất trong thị trường nông sản CBOT.
*   **Phân cấp phá vỡ cấu trúc:**
    *   `Sweep`: Giá chọc râu qua Swing Point nhưng đóng cửa giật ngược lại → Chỉ là quét thanh khoản.
    *   `CHoCH`: Tín hiệu sớm sau Sweep.
    *   `MSS`: Đóng cửa dứt khoát qua Swing Point. Tín hiệu Win Rate cao nhất nếu trước đó đã có Sweep.
*   **Tối ưu Win Rate:** Điểm Win Rate cơ bản là 65%. Sẽ được cộng thêm điểm nếu Setup hội tụ các yếu tố: MSS có Sweep bảo kê (+10%), có HQ OB (+5%), có Breaker Block (+4%), có FVG (+3%).

---

## 5. Hướng Dẫn Vận Hành & Khắc Phục Sự Cố

### 5.1. Khởi động Bot
Bot được thiết kế để chạy ngầm (background task). Nếu máy chủ bị khởi động lại hoặc tiến trình bị ngắt, bạn có thể gọi trợ lý AI thực thi lệnh sau trên Terminal:
```powershell
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python.exe entry_alarm.py
```

### 5.2. Test và Debug
Nếu bạn nghi ngờ tín hiệu báo sai, hãy chạy file debug để xem chi tiết log của Engine:
```powershell
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python.exe debug_ict.py
```
Kết quả sẽ in ra terminal các vùng OB, FVG, đếm số lượng Sweep, CHoCH, MSS và lý do tại sao một mã không có Setup.

### 5.3. Sử dụng Bot trên Telegram
*   Vào đoạn chat với Bot hoặc Group có chứa Bot.
*   Bot cung cấp sẵn bàn phím ảo với nút **"🔍 Scan Bot"**.
*   Khi bấm nút, Bot sẽ mất khoảng 10-15 giây để tải dữ liệu, phân tích lại toàn bộ và trả về kết quả ngay lập tức. Tính năng này sử dụng `threading` và `Lock` nên sẽ không bị treo nếu bấm liên tục.

### 5.4. Chỉnh sửa cấu hình
*   **Thay đổi Token hoặc ID Nhóm:** Nằm tại phần đầu file `entry_alarm.py`.
*   **Điều chỉnh độ nhạy của Engine:** Nằm tại các hằng số đầu file `ict_engine.py` (ví dụ `HQ_OB_ATR_MULT = 0.55`).
