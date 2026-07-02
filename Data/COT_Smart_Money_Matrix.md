# HỆ THỐNG PHÂN TÍCH: MA TRẬN DÒNG TIỀN COT (SMART MONEY MATRIX)
**Tác giả/Hệ quy chiếu:** Giao dịch Phái sinh Nông sản CBOT (Lúa mì, Ngô, Đậu tương)
**Đối tượng phân tích:** Managed Money (Quỹ đầu cơ - Smart Money)

## 1. BẢN CHẤT CÔNG THỨC (CORE LOGIC)
Hệ thống sử dụng dữ liệu từ báo cáo Commitments of Traders (COT) phát hành hàng tuần để phân loại dòng tiền vào 4 trạng thái (Góc phần tư - Quadrants).

* **NET_POSITION (Vị thế ròng)** = Tổng Hợp đồng Long (Mua) - Tổng Hợp đồng Short (Bán khống)
    * Nếu NET_POSITION > 0: Quỹ đang ôm NET LONG (Kỳ vọng thị trường Tăng).
    * Nếu NET_POSITION < 0: Quỹ đang ôm NET SHORT (Kỳ vọng thị trường Giảm).
* **CHANGE (Biến động tuần)** = NET_POSITION (Tuần này) - NET_POSITION (Tuần trước)
    * Nếu CHANGE > 0: Dòng tiền đang Mua vào (Bơm thêm Long hoặc Đóng bớt Short).
    * Nếu CHANGE < 0: Dòng tiền đang Bán ra (Đóng bớt Long hoặc Nhồi thêm Short).

## 2. MA TRẬN 4 GÓC PHẦN TƯ (THE 4 QUADRANTS)

### Q1: GOM LONG (BÙNG NỔ XU HƯỚNG TĂNG)
* **Điều kiện:** NET_POSITION > 0 VÀ CHANGE > 0
* **Bản chất:** Quỹ đang ôm Long và tiếp tục bơm tiền MUA THÊM (New Longs).
* **Hành động giá:** Breakout đỉnh là thật. Xu hướng tăng bền vững.
* **Tín hiệu Trading:** Ưu tiên đánh LONG.

### Q2: XẢ LONG (ÁP LỰC CHỐT LỜI / THÁO CHẠY)
* **Điều kiện:** NET_POSITION > 0 VÀ CHANGE < 0
* **Bản chất:** Quỹ đang ôm Long nhưng lại BÁN RA để chốt lời/cắt lỗ (Long Liquidation). Thường xuất hiện trước kỳ Rollover hoặc khi hết rủi ro thời tiết.
* **Hành động giá:** Sập mạnh. Rũ bỏ sâu.
* **Tín hiệu Trading:** Cấm bắt đáy. Canh giá hồi lên để đánh SHORT.

### Q3: NHỒI SHORT (BÙNG NỔ XU HƯỚNG GIẢM)
* **Điều kiện:** NET_POSITION < 0 VÀ CHANGE < 0
* **Bản chất:** Quỹ đang ôm Short và tiếp tục đè mâm BÁN KHỐNG THÊM (New Shorts).
* **Hành động giá:** Breakdown đáy là thật. Giá giảm dốc không cản nổi.
* **Tín hiệu Trading:** Ưu tiên đánh SHORT thuận xu hướng.

### Q4: COVER SHORT (SHORT SQUEEZE - BẪY ÉP MUA)
* **Điều kiện:** NET_POSITION < 0 VÀ CHANGE > 0
* **Bản chất:** Quỹ đang ôm Short kỷ lục nhưng bị ép MUA LẠI (Short Covering) để chốt lời hoặc cắt lỗ.
* **Hành động giá:** Bật tăng giật ngược cực mạnh (Spike) do lực mua kỹ thuật.
* **Tín hiệu Trading:** Cấm Short đuổi. Canh giá nhúng xuống hỗ trợ để bắt râu nến đánh LONG.

## 3. TỪ ĐIỂN MÃ HÀNG HÓA CFTC (CBOT)
Hệ thống bot cần dùng các mã này để kéo API từ CFTC:
* Ngô (Corn - ZC): `002602`
* Đậu tương (Soybeans - ZS): `005602`
* Lúa mì (Wheat - ZW): `001602`
* Dầu đậu tương (Soybean Oil - ZL): `007601`
* Khô đậu tương (Soybean Meal - ZM): `026603`