# Hướng Dẫn Chi Tiết: Quá Trình Tạo Project "Future Chart"

Tài liệu này tóm tắt lại các bước logic và kỹ thuật đã được sử dụng để xây dựng mô hình giả lập giá lúa mì (ZW) "Future Chart".

---

## Bước 1: Tiếp nhận và Phân tích Yêu cầu
- **Mục tiêu:** Tạo một đồ thị mô phỏng (giả lập) giá lúa mì (ZW) chạy trong 1 tuần tới (theo nến 4H).
- **Nguồn dữ liệu đầu vào được yêu cầu:** Hệ thống V3 Pro, Hệ thống V4, Dữ liệu Mùa vụ 2026 (Mua Vu 2026) và Hệ thống CNOT ICT.
- **Yếu tố Vĩ mô (User inputs):** Giá dầu Brent ($85-$87) và chỉ số DXY (99.82).
- **Nguyên tắc:** Phân tích logic trước, chờ người dùng xác nhận (CONFIRM) mới bắt đầu code.

## Bước 2: Thu thập Dữ liệu (Data Gathering)
AI tiến hành rà soát các tệp dữ liệu trong thư mục `Cbot`:
1. **`v3_state_snapshot.json`**: Lấy các thông số kỹ thuật thời gian thực như giá đóng cửa gần nhất (589.75¢), các đường trung bình động (EMA 21: 587.38, EMA 50: 587.34), và xu hướng kỹ thuật.
2. **`CBOT_Visual_Advisor_V4.md`**: Đọc các quy tắc xác định vùng Order Block (OB), Fair Value Gap (FVG), và Market Structure Shift (MSS).
3. **`fundamental_data.json` & Nhật ký `CBOT_Reports_Log.md`**: Lấy các thông số mùa vụ (Lúa mì đông của Mỹ đang thu hoạch, chất lượng rất kém chỉ 25% Good/Excellent) và vị thế của các quỹ đầu cơ (COT Report).
4. **Web Search**: Kiểm tra giá chốt phiên cuối tuần thực tế để làm giá neo (Anchor Price) cho mô hình.

## Bước 3: Xây dựng Động cơ Mô phỏng (Simulation Engine)
Tạo file script Python `future_chart.py` với cấu trúc sau:
- **Biến số và Thông số (Inputs):** Gắn toàn bộ dữ liệu đã thu thập vào các hằng số.
- **Chấm điểm Đa nhân tố (Composite Bias Score):** Kết hợp tất cả các yếu tố V3, V4, Mùa vụ, Vĩ mô thành một thang điểm (từ -3 đến +3) để xác định xu hướng chung của tuần (Bullish hay Bearish). Ở dự án này, điểm tổng là `+4.70` (BULLISH mạnh).
- **Tạo nến 4H theo Kịch bản ICT (Scenario Generation):** 
  - Mô hình áp dụng **ICT Judas Swing** cho ngày Thứ Hai (tạo cú sụt giảm giả để quét thanh khoản).
  - Sử dụng xúc tác từ **Báo cáo USDA** vào Thứ Ba để tạo lực đẩy mua (Short Squeeze).
  - Xác nhận **MSS Breakout** vào Thứ Tư khi giá vượt cản R1.
  - Sử dụng hàm ngẫu nhiên (có kiểm soát) để tạo các thân nến và bóng nến 4H một cách thực tế, dựa trên biên độ ATR.
- **Xuất Dữ liệu:** Ghi dữ liệu kết quả ra file `future_chart_data.json`.

## Bước 4: Trực quan hóa dữ liệu (Interactive Dashboard)
Viết file `future_chart.html` để biến dữ liệu thô thành một Dashboard chuyên nghiệp:
- Sử dụng thư viện **Plotly.js** để vẽ biểu đồ nến Nhật (Candlestick Chart) chuẩn xác, cho cả khung 4H và khung Ngày (Daily).
- Thiết kế giao diện bằng HTML/CSS (chế độ Dark Mode, có hiệu ứng Glow) với các thẻ thành phần (Panels):
  - Bảng tổng hợp giá mở/đóng/cao/thấp từng ngày.
  - Thang điểm Bias.
  - Lịch sự kiện trong tuần.
  - Các mức giá Cản / Hỗ trợ quan trọng (Key Levels).
  - Các thẻ lý luận của AI (Reasoning Cards) giải thích tại sao giá chạy theo hướng đó vào mỗi ngày.

## Bước 5: Đóng gói và Quản lý
- Ban đầu các file được tạo trong thư mục `Cbot` chính.
- Theo yêu cầu của người dùng, tạo một folder mới tên `Future chart` và di chuyển toàn bộ 3 file (`.py`, `.json`, `.html`) vào thư mục này để gọn gàng.
- Cập nhật lại file `future_chart_bookmark.md` (nằm trong thư mục Artifacts của AI) để thay đổi đường dẫn chạy lệnh cho đúng với folder mới.

---

*Lưu ý: Mô hình này mang tính chất giả lập (simulation) để kiểm tra tính logic của các hệ thống giao dịch, không phải công cụ dự báo tương lai chắc chắn 100%.*
