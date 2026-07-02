# CẨM NANG THỰC CHIẾN: CBOT VISUAL ENTRY ADVISOR PRO (V4)

Cẩm nang hướng dẫn giao dịch nhất quán, an toàn cao dành cho hệ thống phân tích trực quan kết hợp **CBOT V4 Pro**, tập trung vào việc tìm kiếm các **Lệnh giao dịch A+ (Winrate > 65%)** và xác định điểm **MSS / Entry Timing trên khung M15**.

---

## 🌟 PHẦN 1: ĐỊNH NGHĨA LỆNH GIAO DỊCH LỚN A+ (WINRATE > 65%)

Lệnh A+ là cơ hội giao dịch có xác suất thành công cao nhất, xuất hiện khi có sự đồng thuận hoàn hảo giữa bối cảnh vĩ mô (Khung D1/H1) và hành động giá tức thời (Khung M15).

### 3 Bộ Lọc Nghiêm Ngặt của Lệnh A+:

```
+-------------------------------------------------------------------+
|  MÀNG LỌC 1: BỐI CẢNH VĨ MÔ & CẢN CỨNG H1 (HTF CONTEXT)           |
|  - Giá chạm sát vùng cản hỗ trợ cứng S1/S2 hoặc kháng cự R1/R2.   |
|  - Chỉ báo RSI H1 đi vào vùng quá mức (Quá bán < 30 / Quá mua > 70)|
|  - Khối lượng giao dịch (Volume) đạt đỉnh Climax (Bán/Mua tháo).   |
+-------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
|  MÀNG LỌC 2: TÍN HIỆU ĐẢO CHIỀU KHUNG M15 (LTF MSS TRIGGER)       |
|  - Xuất hiện cấu trúc phá vỡ xu hướng vi mô (MSS - CHoCH) trên M15|
|  - Giá Reclaim (giành lại) và đóng cửa giữ vững trên EMA 21 M15.   |
|  - Xuất hiện cụm nến đảo chiều có xác nhận (Pinbar, Engulfing).   |
+-------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
|  MÀNG LỌC 3: QUẢN TRỊ RỦI RO & TỶ LỆ R:R (RISK/REWARD FILTER)     |
|  - Điểm đặt Stop Loss (SL) cực ngắn (ngay dưới đáy/đỉnh M15 vừa tạo)|
|  - Tỷ lệ Lợi nhuận / Rủi ro thực tế đạt tối thiểu từ 1:2.5 trở lên. |
+-------------------------------------------------------------------+
```

---

## 🎯 PHẦN 2: QUY TRÌNH XÁC ĐỊNH MSS VÀ ENTRY TIMING TRÊN KHUNG M15

Việc xác định điểm **MSS (Market Structure Shift)** và thời điểm vào lệnh (Timing) trên khung **M15** giúp anh/chị có một điểm vào lệnh sớm, khoảng cách dừng lỗ cực ngắn, từ đó đạt hiệu suất R:R và tỷ lệ thắng tốt nhất.

### 1. Cách xác định điểm MSS trên khung M15:
* **MSS (Market Structure Shift) trong xu hướng GIẢM sang TĂNG:**
  * Xác định đỉnh gần nhất tạo ra cái đáy thấp nhất của xu hướng giảm vi mô trên M15.
  * Điểm MSS chính là mốc giá cao nhất của đỉnh gần nhất này.
  * *Tín hiệu kích hoạt:* Một cây nến M15 tăng mạnh mẽ và **đóng cửa vượt lên trên mốc giá MSS** này (xác nhận cấu trúc giảm bị phá vỡ).
* **MSS (Market Structure Shift) trong xu hướng TĂNG sang GIẢM:**
  * Xác định đáy gần nhất tạo ra cái đỉnh cao nhất của xu hướng tăng vi mô trên M15.
  * Điểm MSS chính là mốc giá thấp nhất của đáy gần nhất này.
  * *Tín hiệu kích hoạt:* Một cây nến M15 giảm mạnh mẽ và **đóng cửa dưới mốc giá MSS** này.

### 2. Cách xác định thời điểm vào lệnh (Entry Timing) tối ưu:
* **TUYỆT ĐỐI KHÔNG MUA ĐUỔI (FOMO):** Khi một cây nến M15 đóng cửa kích hoạt MSS, giá thường đã tăng mạnh, nếu mua ngay lập tức sẽ bị trễ nhịp và chịu Stop Loss rộng.
* **QUY TẮC NHỊP HỒI (PULLBACK TIMING):**
  1. Xác định vùng **Order Block (OB)** hoặc **Fair Value Gap (FVG)** được tạo bởi lực tăng mạnh mẽ của cây nến breakout MSS.
  2. Vẽ công cụ Fibonacci từ đáy vừa tạo lên đỉnh của cây nến breakout.
  3. **Thời điểm đặt lệnh:** Đặt lệnh **Limit mua** sẵn tại vùng **OTE (Optimal Trade Entry - thoái lui 50% - 62% của con sóng tăng)**, trùng khớp với vùng OB hoặc FVG trên M15.
  4. **Điểm dừng lỗ (SL):** Đặt dưới đáy tuyệt đối vừa tạo từ 1.0 đến 2.0 giá (ATR buffer).

---

## 🛡️ PHẦN 3: NGUYÊN TẮC KỶ LUẬT THỰC CHIẾN

1. **Không có MSS, Không vào lệnh:** Nếu giá chạm hỗ trợ H1 nhưng trên M15 vẫn liên tục tạo đỉnh/đáy thấp dần và chưa kích hoạt MSS, hãy kiên nhẫn đứng ngoài. Đây là cách tốt nhất để tránh **bắt dao rơi**.
2. **Không có Pullback, Bỏ qua lệnh:** Nếu giá kích hoạt MSS nhưng tăng dựng đứng hình chữ V mà không hồi lại vùng OTE/OB, chấp nhận bỏ qua cơ hội. Tuyệt đối không mua đuổi để tránh **chặn đầu ô tô**.
3. **Tuân thủ SL tuyệt đối:** Luôn đặt SL tự động ngay sau khi lệnh khớp. SL là chi phí bảo hiểm để bảo vệ tài khoản của anh/chị.
