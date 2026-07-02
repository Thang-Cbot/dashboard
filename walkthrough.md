# 🌟 Hoàn tất Tái Cấu Trúc CBOT Data Project & V3 Pro

## 🎯 Mục tiêu đã đạt được
Toàn bộ hệ thống CBOT đã được thiết kế lại theo chuẩn kiến trúc một nguồn dữ liệu tập trung (Single Source of Truth). Bây giờ, toàn bộ các script dự báo (V3 Pro) và cảnh báo (Entry Alarm) đều sử dụng chung một cơ sở dữ liệu được quản lý tự động tại `Data/output/`.

---

## 🛠️ Những Thay Đổi Chi Tiết

### 1. Xây Dựng Kiến Trúc `Data/` Mới
- **`run_data_update.py`**: Trái tim của hệ thống. Lệnh này sẽ kích hoạt toàn bộ các mô-đun để thu thập mọi dữ liệu cần thiết.
- **`run_data.bat`**: File batch giúp người dùng Double-click chạy dễ dàng mà không cần dùng dòng lệnh.
- **`data_config.py`**: Quản lý toàn bộ cấu hình đường dẫn và biến số của hệ thống.

### 2. Các Modules Thu Thập Dữ Liệu Tự Động
- **📡 `fetch_usda.py`**: Lấy báo cáo WASDE, tiến độ mùa vụ, báo cáo xuất khẩu từ API của Bộ Nông Nghiệp Mỹ.
- **📈 `fetch_prices.py`**: Tải cấu trúc nến H1, phân tích kỹ thuật (EMA, RSI, S/R, ATR) và tính toán Volume/OI từ Yahoo Finance.
- **🌍 `fetch_macro.py`**: Lấy số liệu liên thị trường (DXY, giá dầu Brent).
- **💰 `fetch_cot.py`**: Phân tích dòng tiền Smart Money (Managed Money) từ bảng dữ liệu của CFTC.

### 3. Tích Hợp Vào Hệ Thống V3 Pro & Cảnh Báo
- **`run_pro_plus.py`**: Đã loại bỏ logic tải dữ liệu dư thừa. Thay vào đó, kịch bản đọc và truy xuất toàn bộ dữ liệu từ `Data/output/`. Báo cáo V3 Pro được xuất ra mượt mà và tận dụng kho dữ liệu đã tổng hợp sẵn (như file CSV H1, `fundamental_data.json`, `macro_data.json`).
- **`entry_alarm.py`**: Cập nhật đường dẫn trỏ thẳng đến `Data/output/` để quét tín hiệu kỹ thuật và thông báo vào Telegram.

---

## 🧑‍💻 Hướng Dẫn Sử Dụng
> [!IMPORTANT]
> Từ nay, quy trình hoạt động hàng ngày của bạn đã được đơn giản hóa tối đa!

1. **Khởi động Data Project:** Mỗi ngày, chỉ cần chạy file `Data/run_data.bat` **một lần duy nhất**. Nó sẽ quét và làm mới toàn bộ kho dữ liệu đầu vào.
2. **Cập nhật thủ công (Nếu cần):** Đối với thời tiết, sản lượng đối thủ, và chiến lược mới, hãy cập nhật vào trong `Data/output/fundamental_data.json`.
3. **Phân tích Thị trường:** Chạy `run_pro_plus.py` để xuất báo cáo chiến lược giao dịch V3. Dữ liệu sẽ chạy cực nhanh do mọi thứ đã có sẵn.

---

## 🔍 Xác Minh Hoạt Động (Verification)
- Đã Fix các lỗi Unicode khi in ra Console PowerShell trên Windows (Lỗi `cp1252`).
- Đã Fix lỗi HTTP 403 Forbidden khi kết nối đến API CFTC Public bằng User-Agent Headers chuẩn.
- Script **`run_data_update.py`** hoàn thành xuất sắc quá trình quét dữ liệu của toàn bộ 4 modules trong thời gian **~46 giây**.
- Báo cáo chiến lược **V3 Pro (`run_pro_plus.py`)** chạy mượt mà không xuất hiện bất kỳ cảnh báo thiếu file nào.
