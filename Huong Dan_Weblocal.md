# Hướng Dẫn Sử Dụng CBOT Dashboard (Local Web)

Tài liệu này hướng dẫn bạn cách khởi động và sử dụng hệ thống CBOT Dashboard dưới dạng một Website nội bộ (Local Web) ngay trên máy tính cá nhân của bạn.

## 1. Yêu cầu hệ thống
- Máy tính chạy hệ điều hành Windows.
- Đã cài đặt Python (phiên bản 3.8 trở lên).
- Có kết nối Internet để hệ thống tự động cập nhật dữ liệu (từ Yahoo Finance, USDA, CFTC).

## 2. Cách khởi động Local Web (Chỉ với 1 Click)
Thay vì phải gõ lệnh phức tạp hay mở thủ công file HTML, hệ thống đã được tự động hóa hoàn toàn thông qua một file thực thi (Batch script).

1. Mở thư mục gốc của dự án **Cbot**.
2. Tìm và **Click đúp chuột** vào file có tên: `START DASHBOARD.bat`
3. Một cửa sổ dòng lệnh (Terminal nền đen) sẽ hiện lên. Đây là máy chủ thu nhỏ (Local Server) đang chạy ngầm. **TUYỆT ĐỐI KHÔNG ĐƯỢC TẮT CỬA SỔ NÀY** trong suốt quá trình bạn sử dụng web.
4. Ngay lập tức, trình duyệt Web mặc định của bạn sẽ tự động mở lên với đường dẫn: `http://localhost:8080/CBOT_Dashboard.html`

## 3. Cách cập nhật dữ liệu trực tiếp trên Web (Nút Scan Data)
Khi bạn đang xem Dashboard và muốn làm mới dữ liệu (giá cả, tồn kho, dòng tiền cá mập...) theo thời gian thực:

1. Nhìn lên góc trên cùng của thanh Menu trên trang Web, bấm vào nút **🔄 SCAN DATA**.
2. Nút bấm sẽ đổi sang trạng thái "Đang quét..." kèm vòng xoay loading. Lúc này, Website đang ra lệnh cho máy chủ nền chạy ngầm 2 tiến trình:
   - `Data/run_data_update.py`: Kéo toàn bộ dữ liệu thô mới nhất từ Internet về máy.
   - `run_pro_plus.py`: Phân tích dữ liệu bằng thuật toán và vẽ lại cấu trúc giao diện HTML mới.
3. Vui lòng đợi khoảng 20 - 40 giây tùy tốc độ mạng. Khi quá trình phân tích hoàn tất, trang Web sẽ **tự động tải lại (refresh)** và hiển thị bản cập nhật mới nhất cho bạn.

## 4. Các Lưu ý Quan trọng
- **Loading vô tận:** Nếu bạn bấm nút Scan Data mà nút xoay mãi không dừng quá 2 phút, hãy mở cửa sổ Terminal (màu đen) lên kiểm tra xem có dòng báo lỗi mạng hay chặn IP từ nguồn dữ liệu gốc (CFTC/USDA) hay không.
- **Bot Telegram:** Nút Scan Data chỉ chịu trách nhiệm cập nhật dữ liệu Vĩ mô, Kỹ thuật và Tồn kho lên giao diện Web. Nó **KHÔNG** chạy ngầm bot báo tín hiệu Telegram (`entry_alarm.py`). Để liên tục quét giá nhận cảnh báo qua Telegram, bạn vẫn cần mở một cửa sổ lệnh (CMD) riêng biệt và gõ `python entry_alarm.py` để bot "trực chiến" 24/24.
- **Cách tắt Web an toàn:** Khi không có nhu cầu sử dụng nữa, bạn chỉ cần tắt tab trình duyệt, sau đó tắt cửa sổ dòng lệnh màu đen (Local Server) là hệ thống sẽ dừng hoàn toàn.

## 5. Lộ trình Mở rộng (Chạy Live Online VPS)
Cấu trúc Local Web hiện tại (sử dụng thư viện `http.server` của Python và Endpoint bảo mật `/run-scan`) được thiết kế theo đúng chuẩn để dễ dàng chuyển đổi lên đám mây (Cloud). 
Nếu sau này bạn muốn hệ thống chạy Live Online 24/7 (truy cập bằng điện thoại bất cứ đâu trên thế giới thông qua tên miền riêng, ví dụ: `cbotmaster.com`), chúng ta chỉ cần chuyển toàn bộ bộ source code Cbot này lên một Máy chủ ảo (VPS) chạy Linux và cài đặt cấu hình Nginx/Gunicorn.
