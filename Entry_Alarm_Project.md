# TÀI LIỆU DỰ ÁN: CBOT ENTRY ALARM (TELEGRAM BOT)

**Trạng thái:** Hoàn tất 100% & Đang hoạt động

## 🎯 1. Mục tiêu và Chức năng lõi
Module **Entry Alarm** là một kịch bản theo dõi thị trường chạy ngầm, được thiết kế để tự động quét dữ liệu CBOT (Lúa mì, Ngô, Đậu tương) và gửi cảnh báo Lệnh A+ thẳng đến ứng dụng Telegram của người dùng.

### Các Tính năng Nổi bật:
- **Bộ lọc Lệnh A+ (H1 MSS):** Chỉ báo động khi có sự phá vỡ cấu trúc (Market Structure Shift) rõ ràng trên khung thời gian H1. Điệu kiện: nến H1 đóng cửa vượt qua đường EMA 21 một cách dứt khoát.
- **Tư duy Giao dịch (Pullback):** Không báo mua/bán đuổi. Hệ thống yêu cầu chờ giá quay về vùng OTE (gần EMA 21) để đặt lệnh Limit, với SL cực ngắn.
- **Lịch Giao Dịch Chuẩn CME (pandas_market_calendars):** 
  - Khớp 100% với giờ mở/đóng cửa điện tử (Globex) thực tế.
  - Tự động bỏ qua các ngày nghỉ lễ của Mỹ (Thanksgiving, July 4th,...).
  - Tự động điều chỉnh chính xác múi giờ Mùa Hè/Mùa Đông (Daylight Saving Time).
  - Tự động đi ngủ (ngủ đông) vào giờ nghỉ trưa của sàn CBOT (19h45 - 20h45 giờ VN) và cuối tuần để tối ưu tài nguyên máy tính.

## ⚙️ 2. Quy trình Vận hành (Cấu trúc File)
- `entry_alarm.py`: Trái tim của hệ thống. Chứa vòng lặp vô hạn, gọi API tải dữ liệu, phân tích nến H1 và xử lý lệnh gửi Telegram.
- `run_alarm_bot.bat`: File khởi động nhanh (Shortcut).

## 🚀 3. Hướng dẫn Sử dụng (Quy trình hằng ngày)
Anh Thắng chỉ cần thực hiện thao tác rất đơn giản để hệ thống tự làm việc:

1. Đảm bảo máy tính có kết nối Internet.
2. Truy cập thư mục `Cbot`, nháy đúp chuột vào file **`run_alarm_bot.bat`**.
3. Cửa sổ dòng lệnh (Terminal màu đen) sẽ hiện ra. Điện thoại của anh sẽ nổ chuông và nhận tin nhắn Telegram: *"✅ Hệ thống CBOT Entry Alarm đã kích hoạt!"*
4. Cứ để nguyên cửa sổ đen thu nhỏ xuống thanh Taskbar. 

Bot sẽ canh đúng phút thứ `00` của mỗi giờ (VD: 20:00, 21:00) trong giờ mở cửa để lấy dữ liệu nến H1 vừa đóng và gửi báo cáo cho anh (nếu có tín hiệu Lệnh A+).

## 🔐 4. Thông tin Bảo mật Telegram
- **Bot Name:** CBOT Entry Alarm
- **Token:** `8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0` (Đã lưu trong mã nguồn)
- **Chat ID đích:** `5294991069` (Tài khoản của anh Thắng)
- *(Ghi chú: Nếu anh Thắng lỡ xóa chat với Bot trên điện thoại, chỉ cần tìm lại tên Bot và bấm START để kết nối lại).*
