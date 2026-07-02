# NHẬT KÝ BÁO CÁO PHÂN TÍCH HỆ THỐNG CBOT PRO V2 (ZC - ZW - ZS)
*Hệ thống phân tích tự động tích hợp Kỹ thuật H1/M15, Vĩ mô toàn cầu (Brent/DXY) và Nền tảng Nông nghiệp USDA*

Tài liệu được lưu trữ trực tiếp tại thư mục làm việc:
`c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\CBOT_Reports_Log.md`

---

## 🌐 TỔNG QUAN VĨ MÔ TOÀN CẦU (MACRO INDICATORS OVERVIEW)
*Cập nhật tự động qua `macro_tracker.py` vào lúc 20:39 ICT ngày 30/05/2026*

| Chỉ số Vĩ mô | Mức giá hiện tại | Biến động 24h | Xu hướng & Đánh giá tác động đến Nông sản |
| :--- | :---: | :---: | :--- |
| **Dầu thô Brent (BZ=F)** | **$92.05 / thùng** | **-1.77%** | 📈 **Tích cực (Bullish):** Giá dầu duy trì ở mức cao hỗ trợ mạnh mẽ cho biofuels như Ethanol (ZC) và Biodiesel (ZS). Chi phí sản xuất neo cao tạo mức sàn hỗ trợ giá. |
| **Chỉ số DXY (USD Index)** | **98.91** | **-0.11%** | 📉 **Trung lập - Tiêu cực (Sức ép xuất khẩu):** DXY neo cao khiến hàng Mỹ kém cạnh tranh hơn ở thị trường quốc tế, cản trở xuất khẩu ngắn hạn. |


### ⚠️ CẢNH BÁO LỆCH PHA CƠ HỘI MUA (BULLISH DIVERGENCE DETECTED)
*   **Giá trị biến động 24h:** Dầu Brent giảm **`-1.77%`** | Lúa mì Chicago giảm **`-2.16%`**.
*   **Biện chứng liên thị trường:** Việc dầu thô Brent giảm mạnh (do tin tức giảm căng thẳng Trung Đông như tin đồn thảo thuận Mỹ - Iran) đã kéo theo áp lực bán tháo liên thị trường (cross-commodity selling) tự động từ các quỹ đầu cơ. Điều này ép giá Lúa mì giảm theo về vùng hỗ trợ S1 **`618.00 cents`** (sát mức **`609 cents`** tối qua).
*   **Thực tế cấu trúc nông học:** Sự sụt giảm địa chính trị này hoàn toàn không thay đổi được thực tế là cung lúa mì toàn cầu đang cực kỳ thắt chặt (Úc sụt giảm 41%, lúa mì Mỹ chất lượng kém đạt 44% Poor/Very Poor).
*   🚀 **Khuyến nghị chiến lược:** Đây là một đợt sụt giảm "lệch pha cơ hội" tuyệt vời do tâm lý ngắn hạn che mờ cung cầu vĩ mô (Asymmetrical Opportunity). Khuyến nghị **Canh Mua gom DCA dài hạn quyết liệt quanh vùng biên độ hỗ trợ `609.25 - 618.00 cents` (600 - 612)**, tuyệt đối tránh hoảng loạn bán tháo cắt lỗ.


---

## 📌 DANH MỤC LỊCH SỬ BÁO CÁO (CẬP NHẬT PHIÊN CHỐT 30/05/2026)
*Thời gian đóng cửa phiên giao dịch được đồng bộ chính xác vào lúc **1:20 AM ICT ngày 30/05/2026***

| Ngày Báo Cáo (ICT) | Mã | Giá Chốt (Close) | Tín Hiệu H1 (EMA 21/50) | Volatility | Intraday Bias | Trọng tâm thời tiết & Mùa vụ | Xem Chi Tiết |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **30/05/2026** | **ZC** | **446.75 ¢** | 🐻 Bearish (451.70 < 454.15) | 1.50 cents | Rình mua (Long on dip) | 🌽 Gieo hạt 86% đã gieo trồng, Nam Mỹ thu hoạch rộ | [Xem Ngô (ZC)](#1-báo-cáo-mã-zc-ngô---phiên-chốt-29052026) |
| **30/05/2026** | **ZW** | **610.50 ¢** | 🐻 Bearish (618.86 < 623.82) | 1.25 cents | Bán khống hồi (Short on rally) | 🌾 Lúa đông cực xấu (26% Good/Excellent); Úc/Arg trồng giảm sâu | [Xem Lúa mì (ZW)](#2-báo-cáo-mã-zw-lúa-mì---phiên-chốt-29052026) |
| **30/05/2026** | **ZS** | **1186.75 ¢** | 🐻 Bearish (1192.41 < 1192.66) | 2.50 cents | Mua đuổi (Buy on pullback) | 🌱 Gieo trồng 79% đã gieo trồng, Arg thu hoạch đậu tương | [Xem Đậu tương (ZS)](#3-báo-cáo-mã-zs-đậu-tương---phiên-chốt-29052026) |

---

## 1. BÁO CÁO MÃ ZC (NGÔ) - PHIÊN CHỐT 30/05/2026

### A. Phân Tích Kỹ Thuật (H1 & M15)
*   **Giá Chốt Phiên (Close):** 446.75 cents.
*   **Chỉ báo EMA H1:** `EMA_21` (451.70) nằm dưới `EMA_50` (454.15). Tín hiệu Bearish trung hạn. Chênh lệch: **2.45 cents**.
*   **Biến động (Volatility):** **1.50 cents**.
*   **Chỉ báo động lượng & dao động:** RSI (14) = **`24.68`** | ATR (14) = **`2.02`** cents.
*   **Hành vi giá:** Lực cầu xuất hiện quanh vùng hỗ trợ kỹ thuật Price Action. Biểu đồ ngắn hạn có dấu hiệu tạo đáy nâng cao (Higher Low) hỗ trợ cho xu hướng hồi phục.

### B. Nền Tảng Cơ Bản & Mùa Vụ Chuyên Sâu (USDA Fundamentals & Competitors)

| Chỉ tiêu Nền tảng | Số liệu mới nhất | Đánh giá & Xu hướng thị trường |
| :--- | :---: | :--- |
| **Tiến độ Gieo trồng (US Planting)** | **86% đã gieo trồng** | Nhanh hơn mức trung bình 5 năm (83%). Tỷ lệ nảy mầm đạt thuận lợi. |
| **Tiến độ Thu hoạch (US & Global Harvest)** | **Mỹ: 0% | Argentina: 66% (2/3 tiến độ)** | **Mốc định đáy chu kỳ:** Argentina đang thu hoạch rộ đạt 66%. Việc giá ngô giữ vững trên 445-450 cents bất chấp áp lực thu hoạch cho thấy ngô đã xác lập vùng đáy chu kỳ mùa vụ thành công. |
| **Tỷ lệ Sản lượng (Crop Condition)** | **Chưa có xếp hạng** | Sẽ được USDA công bố xếp hạng Good/Excellent đầu tiên vào đầu tháng 6 khi ngô nảy mầm hoàn chỉnh. |
| **Tồn kho Mỹ (US Ending Stocks)** | **1,957 triệu bushels (2026/27)** | Giảm mạnh so với niên vụ trước (giảm ~8.6%) do diện tích gieo trồng giảm 6%. |
| **Tồn kho Thế giới (Global Stocks)** | **277.5 triệu tấn (2026/27)** | **Cực kỳ tích cực (Bullish): Tồn kho ngô toàn cầu chạm mức thấp nhất 12 năm qua (kể từ niên vụ 2013/14).** |
| **Sản lượng Xuất khẩu (Exports)** | **1.58 triệu tấn / tuần** | Tăng mạnh. Các đơn hàng "flash sales" sang Mexico và Hàn Quốc duy trì đều đặn. |
| **Cập nhật Đối thủ toàn cầu** | **Brazil & Argentina** | Argentina: Dự báo sản lượng đạt kỷ lục 64 triệu tấn. Brazil: Vụ 1 kết thúc; ngô vụ 2 (Safrinha) đang chịu khô hạn cục bộ tại các bang phía Nam gây lo ngại sụt giảm năng suất. |
| **Rủi ro Thời tiết (Weather)** | **Khô hạn phía Bắc** | Xác suất chuyển pha sang El Niño đạt 82% vào tháng 7. Hiện tại đang xuất hiện vùng khô hạn cục bộ ở rìa phía Bắc (Minnesota, Northern Plains) đe dọa trực tiếp tỷ lệ nảy mầm của cây ngô non. |
| **Dòng tiền Đầu cơ (COT Report)** | **CFTC Managed Money** | Managed Money đang giảm ròng vị thế Long (liquidation). Tuy nhiên, dòng tiền đầu cơ vẫn giữ ròng mua (Net Long) đối với các hợp đồng ngô vụ mới (new-crop), cho thấy niềm tin dài hạn của các quỹ đầu tư vẫn được duy trì dù có sự điều chỉnh chốt lời ngắn hạn cuối tháng 5. |
| **Nhu cầu Nhập khẩu (Import Demand)** | **Thị trường cốt lõi** | Nhu cầu nhập khẩu cốt lõi từ Mexico (bền vững ở mức cao kỷ lục) và Hàn Quốc (flash sales gia tăng) liên tục hỗ trợ lực đỡ cho xuất khẩu Mỹ, bù đắp cho sự sụt giảm tạm thời của các thị trường khác. |
| **Thời tiết Dài hạn (El Niño/La Niña)** | **Chu kỳ vĩ mô** | Xác suất chuyển pha mạnh từ El Niño sang La Niña đạt 82% vào tháng 7/2026. Sự dịch chuyển này thường mang lại thời tiết khô hạn và nóng bất thường cho vành đai Midwest Mỹ vào giai đoạn thụ phấn then chốt tháng 7-8, tạo rủi ro mất mùa vĩ mô dài hạn. |

### C. Thời Tiết Ngắn Hạn (2-3 Ngày Qua) & Tác Động Intraday
*   **Diễn biến thời tiết ngắn hạn:** Mưa lớn kéo dài ở phía Đông Corn Belt (Illinois, Ohio).
*   **Biện chứng tác động giá:** 📉 **Tác động ngắn hạn (Neutral/Bearish Intraday):** Mưa lớn bổ sung độ ẩm đất rất tốt, khiến thị trường phản ứng bán tháo ngắn hạn do kỳ vọng cây ngô phát triển thuận lợi lúc đầu. Tuy nhiên, mưa quá lớn gây úng cục bộ và cản trở giai đoạn gieo trồng cuối cùng, buộc nông dân phải tính đến replanting (gieo lại) hoặc chuyển diện tích sang đậu tương do sát ngày hết hạn bảo hiểm. Đây là cơ hội Mua khi giá điều chỉnh sâu (Buy on Dip).

### D. Khuyến Nghị Giao Dịch Trong Ngày (Intraday Entry Matrix)
*   **Vị thế chủ đạo:** **LONG (Canh mua khi điều chỉnh giảm sát EMA 21 H1).**
*   **Điểm vào lệnh (Entry Zone):** **`451.50 - 451.70 cents (Canh mua vùng hỗ trợ)`**
*   **Cắt lỗ (Stop Loss - SL):** **`441.97 cents (Dưới cản S2 + 1.5x ATR)`**
*   **Chốt lời (Take Profit - TP):** *TP 1:* `479.50 cents`, *TP 2:* `481.75 cents`.

### E. Chiến Lược Đánh Biên Trung Hạn (Swing Trading - Pro V2)
*   **Xu Hướng Trung Hạn (1-2 Tuần):** **Đi ngang tích lũy (Sideways Accumulation)**
*   **Vùng Biên Độ Price Action:**
    *   **Hỗ trợ cứng:** S1 = **`451.50`** | S2 = **`445.00`**
    *   **Kháng cự cứng:** R1 = **`479.50`** | R2 = **`481.75`**
*   **Biện chứng Đánh Biên:** Giá ngô chốt phiên rút chân cực mạnh từ đáy S1/S2 và đang kẹp trong biên độ lớn 451.50 - 463.00. Với DXY ổn định và Brent trên $90, biên độ này cực kỳ lý tưởng cho chiến lược Đánh Biên (Swing Range) kiếm tối thiểu 10 giá.
*   **Kế hoạch Lệnh Đánh Biên (Swing Trades - Mục tiêu >= 10 giá):**
    *   🚀 **Swing Long (Mua biên dưới):** Mua tại **`445.00 - 451.50 cents`** | Dừng lỗ (SL): **`440.96 cents (Chống quét SL tuyệt đối)`** | Chốt lời (TP): **`480.75 cents (Ăn trọn biên độ ngô ~10.5 giá)`** (Lợi nhuận: **`>= 10.00 giá`**).
    *   🚀 **Swing Short (Bán biên trên):** Bán tại **`479.50 - 481.75 cents`** | Dừng lỗ (SL): **`485.79 cents`** | Chốt lời (TP): **`446.00 cents`** (Lợi nhuận: **`>= 10.00 giá`**).
*   *Nguyên tắc khớp lệnh:* Đặt lệnh Limit sát biên độ hỗ trợ S1/S2 hoặc kháng cự R1/R2. Cực kỳ ưu tiên khi có nến đảo chiều (Pinbar/Engulfing) đóng cửa trên khung H1/H4 ở vùng biên để xác nhận.

### F. Chiến Lược Gom Mùa Vụ Dài Hạn (Seasonal Accumulation Strategy)
*   **Chiến lược:** Tích lũy mua gom dài hạn (DCA Long) phòng thủ khô hạn El Niño và tồn kho thế giới thấp kỷ lục.
*   **Vùng gom chủ đạo (DCA Brackets):** Chia vốn gom quanh **`436.92 - 445.00 cents`**. Việc Argentina hoàn thành 2/3 vụ thu hoạch mà giá vẫn giữ vững trên 450 cents chứng minh đây là vùng đáy chu kỳ dài hạn lý tưởng để gom hàng.

---

## 2. BÁO CÁO MÃ ZW (LÚA MÌ) - PHIÊN CHỐT 30/05/2026

### A. Phân Tích Kỹ Thuật (H1 & M15)
*   **Giá Chốt Phiên (Close):** 610.50 cents.
*   **Chỉ báo EMA H1:** `EMA_21` (618.86) nằm dưới `EMA_50` (623.82). Tín hiệu Bearish trung hạn. Chênh lệch: **4.97 cents**.
*   **Biến động (Volatility):** **1.25 cents**.
*   **Chỉ báo động lượng & dao động:** RSI (14) = **`25.13`** | ATR (14) = **`2.91`** cents.
*   **Hành vi giá:** Giá chịu áp lực bán ngắn hạn nhưng đang có lực cầu nâng đỡ tại vùng quá bán ngắn hạn.

### B. Nền Tảng Cơ Bản & Mùa Vụ Chuyên Sâu (USDA Fundamentals & Competitors)

| Chỉ tiêu Nền tảng | Số liệu mới nhất | Đánh giá & Xu hướng thị trường |
| :--- | :--- | :--- |
| **Tiến độ Gieo trồng (US Planting)** | **Lúa xuân: 86%** | Lúa mì xuân gieo trồng phát triển thuận lợi. Lúa mì đông đã trổ bông vượt trung bình. |
| **Tiến độ Thu hoạch (US & Global Harvest)** | **Mỹ: 0% | Nam Bán Cầu: Gieo trồng** | **Mốc định đáy chu kỳ:** Mỹ chưa thu hoạch (bắt đầu từ tháng 6-8). Nam bán cầu (Úc/Argentina) đang ở giai đoạn gieo trồng ban đầu. Mốc thu hoạch của hai đối thủ này sẽ rơi vào tháng 10 - tháng 12, đây sẽ là thời điểm giá lúa mì toàn cầu chịu sức ép định đáy cuối cùng trong năm. |
| **Chất lượng mùa vụ Mỹ (Crop Condition)** | **26% Good/Excellent** | **Khủng hoảng chất lượng nghiêm trọng (Bullish): Tỷ lệ Poor/Very Poor vọt lên 44% do hạn hán nghiêm trọng kéo dài tại Southern Plains.** |
| **Tồn kho Mỹ (US Ending Stocks)** | **762 triệu bushels (2026/27)** | Giảm sâu 18.5% so với niên vụ trước, phản ánh thiệt hại sản lượng lúa mì đông nặng nề. |
| **Tồn kho Thế giới (Global Stocks)** | **275.0 triệu tấn (2026/27)** | Giảm 4.2 triệu tấn so với niên vụ trước, tiếp tục thắt chặt cung cầu toàn cầu. |
| **Sản lượng Xuất khẩu (Exports)** | **368,455 tấn / tuần** | Tăng nhẹ, lực cầu hồi phục do giá lúa mì Mỹ giảm về mức cạnh tranh hấp dẫn hơn. |
| **Cập nhật Đối thủ toàn cầu (Mới)** | **Úc & Argentina** | Úc: Diện tích gieo trồng dự kiến giảm sâu 20.4% xuống còn 9.8 triệu ha. Sản lượng dự kiến giảm mạnh 41% xuống 21.3 triệu tấn do hạn hán đầu vụ ở phía Bắc NSW/Nam Queensland. Argentina: Đã gieo trồng được 14.2% diện tích. Sản lượng dự kiến đạt 20.7 triệu tấn (giảm 25% so với mức kỷ lục niên vụ trước) do nông dân lo ngại chi phí phân bón cao và rủi ro bệnh dịch từ El Niño. |
| **Cập nhật Đối thủ Black Sea & EU** | **Nga, Ukraine & EU** | Black Sea & EU: Nga có sương giá muộn, nông dân chuyển dịch sang nhóm hạt có dầu; Ukraine dự kiến sản lượng đạt 22.4 triệu tấn; EU MARS hạ dự báo yield do khô hạn tháng 4 tại Pháp/Đức. |
| **Rủi ro Thời tiết (Weather)** | **Hạn hán vĩ mô** | Hạn hán tàn phá bang Kansas/Oklahoma (Mỹ) + Hạn hán mùa thu làm giảm 20% diện tích gieo trồng của Úc. |
| **Dòng tiền Đầu cơ (COT Report)** | **CFTC Managed Money** | Báo cáo CFTC COT ghi nhận dòng tiền đầu cơ (Managed Money) đã tiến hành bao phủ vị thế Short kỷ lục của họ, tích cực mua vào 14,224 hợp đồng Chicago Wheat, đưa vị thế Net Short giảm mạnh về mức chỉ còn -4,799 hợp đồng (gần như đưa trạng thái về Neutral). Đây là lực đẩy Short Squeeze trung hạn cực lớn khi quỹ đầu cơ buộc phải đóng lệnh bán khống trước tình trạng hạn hán Mỹ. |
| **Nhu cầu Nhập khẩu (Import Demand)** | **Thị trường cốt lõi** | Nhu cầu nhập khẩu tại khu vực Bắc Phi (Ai Cập - GASC liên tục thầu thâu mua) và Trung Đông duy trì ở mức cao do mùa màng nội địa sụt giảm, củng cố nhu cầu thu mua lúa mì toàn cầu bền vững. |
| **Thời tiết Dài hạn (El Niño/La Niña)** | **Chu kỳ vĩ mô** | Chu kỳ dịch chuyển thời tiết El Niño có xu hướng gây hạn hán nặng nề và làm nóng khu vực Đông Úc (Queensland, NSW) và Southern Plains của Mỹ, đe dọa trực tiếp năng suất và chất lượng lúa mì mùa đông. |

### C. Thời Tiết Ngắn Hạn (2-3 Ngày Qua) & Tác Động Intraday
*   **Diễn biến thời tiết ngắn hạn:** Mưa lớn bất ngờ xuất hiện tại vùng Southern Plains (Kansas, Oklahoma, Texas).
*   **Biện chứng tác động giá:** 📉 **Tác động ngắn hạn (Bearish Intraday - Rất Mạnh):** Cơn mưa bất ngờ 2-3 ngày qua đã kích hoạt đợt bán tháo/chốt lời ồ ạt trên thị trường kỳ hạn lúa mì, đẩy giá sụt giảm từ đỉnh cũ về vùng 618.50. Tuy nhiên, về mặt sinh học nông nghiệp, **cơn mưa này đến quá muộn** để cứu vãn phần lớn lúa mì đông đã bị tàn phá (44% Poor/Very Poor). Do đó, nhịp giảm kỹ thuật do mưa này là cơ hội "vàng" để Gom vị thế mua giá rẻ (DCA Long).

### D. Khuyến Nghị Giao Dịch Trong Ngày (Intraday Entry Matrix)
*   **Vị thế chủ đạo:** **SHORT (Canh bán khi giá hồi kỹ thuật chạm EMA 21/50).**
*   **Điểm vào lệnh (Entry Zone):** **`618.86 - 623.82 cents (Canh bán hồi kỹ thuật H1)`**
*   **Cắt lỗ (Stop Loss - SL):** **`683.87 cents (Trên kháng cự R2 + 1.5x ATR)`**
*   **Chốt lời (Take Profit - TP):** *TP 1:* `618.00 cents`, *TP 2:* `609.25 cents`.

### E. Chiến Lược Đánh Biên Trung Hạn (Swing Trading - Pro V2)
*   **Xu Hướng Trung Hạn (1-2 Tuần):** **Giảm điều chỉnh tích lũy (Bearish Correction & Consolidation)**
*   **Vùng Biên Độ Price Action:**
    *   **Hỗ trợ cứng:** S1 = **`618.00`** | S2 = **`609.25`**
    *   **Kháng cự cứng:** R1 = **`673.25`** | R2 = **`679.50`**
*   **Biện chứng Đánh Biên:** Lúa mì bị bán tháo mạnh từ đỉnh kháng cự lớn do tin mưa ngắn hạn, rơi về sát vùng hỗ trợ Price Action cứng. Do đó, xu hướng giảm trung hạn đang đi vào vùng quá bán cực đại (RSI sát 30), chuẩn bị cho nhịp hồi swing tối thiểu 15-20 giá khi thị trường nhận ra mưa không cứu được năng lượng lúa mì.
*   **Kế hoạch Lệnh Đánh Biên (Swing Trades - Mục tiêu >= 10 giá):**
    *   🚀 **Swing Long (Mua biên dưới):** Mua tại **`609.25 - 618.00 cents`** | Dừng lỗ (SL): **`603.43 cents`** | Chốt lời (TP): **`673.25 cents (Đón sóng hồi trung hạn ~14.5 giá)`** (Lợi nhuận: **`>= 10.00 giá`**).
    *   🚀 **Swing Short (Bán biên trên):** Bán tại **`673.25 - 679.50 cents`** | Dừng lỗ (SL): **`685.32 cents`** | Chốt lời (TP): **`609.25 cents (Thuận xu hướng giảm ngắn hạn)`** (Lợi nhuận: **`>= 10.00 giá`**).
*   *Nguyên tắc khớp lệnh:* Đặt lệnh Limit sát biên độ hỗ trợ S1/S2 hoặc kháng cự R1/R2. Cực kỳ ưu tiên khi có nến đảo chiều (Pinbar/Engulfing) đóng cửa trên khung H1/H4 ở vùng biên để xác nhận.

### F. Chiến Lược Gom Mùa Vụ Dài Hạn (Seasonal Accumulation Strategy)
*   **Chiến lược:** Mua tích trữ dài hạn (DCA Long) dựa trên sự sụt giảm sản lượng kép (Mỹ giảm 18%, Úc giảm 41%, Argentina giảm 25%).
*   **Vùng gom chủ đạo (DCA Brackets):** Mua gom quyết liệt tại vùng giá **`597.61 - 609.25 cents (Gom mua D1 phòng thủ mất mùa 41% ở Úc)`**. Sự đồng thuận giảm sản lượng từ tất cả các nước sản xuất lớn ở cả hai bán cầu sẽ đẩy ZW bứt phá lên vùng 650 - 680 cents trước khi Nam Bán Cầu bước vào thu hoạch vào tháng 10.

---

## 3. BÁO CÁO MÃ ZS (ĐẬU TƯƠNG) - PHIÊN CHỐT 30/05/2026

### A. Phân Tích Kỹ Thuật (H1 & M15)
*   **Giá Chốt Phiên (Close):** 1186.75 cents.
*   **Chỉ báo EMA H1:** `EMA_21` (1192.41) nằm dưới `EMA_50` (1192.66). Tín hiệu Bearish trung hạn. Chênh lệch: **0.25 cents**.
*   **Biến động (Volatility):** **2.50 cents**.
*   **Chỉ báo động lượng & dao động:** RSI (14) = **`37.72`** | ATR (14) = **`3.48`** cents.
*   **Hành vi giá:** Động lượng mua cực tốt, giá bật tăng hình chữ V chứng tỏ lực hấp thụ vùng giá thấp rất quyết liệt.

### B. Nền Tảng Cơ Bản & Mùa Vụ Chuyên Sâu (USDA Fundamentals & Competitors)

| Chỉ tiêu Nền tảng | Số liệu mới nhất | Đánh giá & Xu hướng thị trường |
| :--- | :---: | :--- |
| **Tiến độ Gieo trồng (US Planting)** | **79% đã gieo trồng** | Vượt xa mức trung bình 5 năm. Tiến độ trồng trọt cực kỳ thần tốc. |
| **Tiến độ Thu hoạch (US & Global Harvest)** | **Mỹ: 0% | Nam Mỹ: 75%** | **Mốc định đáy chu kỳ:** Mỹ bắt đầu thu hoạch vào tháng 9-11. Argentina đang thu hoạch đậu tương đạt 75% tiến độ. Việc Argentina sắp kết thúc thu hoạch rộ đồng nghĩa với việc áp lực bán tháo lớn nhất của Nam Mỹ đã phản ánh hoàn toàn vào giá (priced-in), tạo điều kiện cho giá đậu tương thiết lập đáy chu kỳ mùa vụ và bước vào pha tăng trưởng. |
| **Tỷ lệ Sản lượng (Crop Condition)** | **Chưa có xếp hạng** | Sẽ được USDA công bố xếp hạng Good/Excellent đầu tiên vào tháng 6. |
| **Tồn kho Mỹ (US Ending Stocks)** | **310 triệu bushels (2026/27)** | Giảm nhẹ so với niên vụ trước do nhu cầu ép dầu nội địa (Crush) sản xuất Biodiesel đạt mức cao kỷ lục. |
| **Tồn kho Thế giới (Global Stocks)** | **124.78 triệu tấn (2026/27)** | Giảm nhẹ so với niên vụ trước, cho thấy cán cân cung cầu toàn cầu duy trì trạng thái thắt chặt vừa phải. |
| **Sản lượng Xuất khẩu (Exports)** | **571,620 tấn / tuần** | Duy trì sự ổn định, nhu cầu nhập khẩu từ Trung Quốc liên tục ghi nhận các đơn hàng lớn. |
| **Cập nhật Đối thủ toàn cầu** | **Brazil & Argentina** | Brazil: Đang xuất khẩu mạnh mẽ dưới thời tiết khô ráo thuận lợi, sản lượng dự báo đạt kỷ lục 180 triệu tấn. Argentina: Thu hoạch đậu tương đạt 75% dưới thời tiết khô hanh, sản lượng ước đạt cao ở mức 50.1 triệu tấn. |
| **Rủi ro Thời tiết (Weather)** | **Ngập lụt Midwest** | Lũ lụt nghiêm trọng tại Đông Midwest (Ohio, Indiana, Illinois) đe dọa làm ngập úng hạt giống, bắt buộc gieo hạt lại (replanting) diện rộng, đe dọa năng suất thực tế. |
| **Dòng tiền Đầu cơ (COT Report)** | **CFTC Managed Money** | Managed Money giữ vị thế Net Long kỷ lục lên tới 212,200 hợp đồng Đậu tương (Futures & Options) theo CFTC mới nhất. Điều này thể hiện niềm tin tuyệt đối của dòng tiền đầu cơ lớn vào nhu cầu Biodiesel và rủi ro ngập lụt Mỹ, tuy nhiên trạng thái mua ròng quá lớn (crowded trade) cũng chứa đựng rủi ro điều chỉnh kỹ thuật khi quỹ thực hiện đóng vị thế chốt lời. |
| **Nhu cầu Nhập khẩu (Import Demand)** | **Thị trường cốt lõi** | Trung Quốc (nhà nhập khẩu đậu tương lớn nhất thế giới) liên tục duy trì tốc độ nhập khẩu ròng mạnh mẽ và bền bỉ trong tháng 5 để bổ sung tồn kho heo nội địa và tích trữ lương thực, tạo bệ đỡ vững chắc loại trừ rủi ro sụt giảm sâu cho ZS. |
| **Thời tiết Dài hạn (El Niño/La Niña)** | **Chu kỳ vĩ mô** | La Niña dự kiến xuất hiện từ quý 3/2026 sẽ gây thời tiết khô hanh cục bộ cho miền Nam nước Mỹ và Brazil, là nhân tố chủ chốt kích hoạt các đợt sóng tăng giá dài hạn cực mạnh cho đậu tương giai đoạn gieo trồng Nam Mỹ cuối năm. |

### C. Thời Tiết Ngắn Hạn (2-3 Ngày Qua) & Tác Động Intraday
*   **Diễn biến thời tiết ngắn hạn:** Bão và mưa cực lớn gây lũ lụt cục bộ tại vùng Đông Midwest (Ohio, Indiana).
*   **Biện chứng tác động giá:** 🚀 **Tác động ngắn hạn (Highly Volatile / Bullish Reversal):** Mưa bão dữ dội 2 ngày qua ban đầu gây tâm lý hoảng loạn, kích hoạt đợt quét stop-loss (rũ bỏ) sụt giảm về 1186.63 đầu phiên. Ngay sau đó, phe Mua nhận diện nguy cơ úng hạt giống và đóng váng đất (soil crusting) cản trở nảy mầm buộc phải gieo lại (replanting), đẩy giá giật ngược hình chữ V tăng vọt đóng phiên sát đỉnh 1194.25. Tín hiệu cực tốt cho phe Long.

### D. Khuyến Nghị Giao Dịch Trong Ngày (Intraday Entry Matrix)
*   **Vị thế chủ đạo:** **LONG (Canh mua khi điều chỉnh giảm về EMA 21 H1).**
*   **Điểm vào lệnh (Entry Zone):** **`1179.75 - 1192.41 cents (Canh mua khi điều chỉnh)`**
*   **Cắt lỗ (Stop Loss - SL):** **`1167.03 cents (Dưới râu quét nến cũ + 1.5x ATR)`**
*   **Chốt lời (Take Profit - TP):** *TP 1:* `1219.00 cents`, *TP 2:* `1220.75 cents`.

### E. Chiến Lược Đánh Biên Trung Hạn (Swing Trading - Pro V2)
*   **Xu Hướng Trung Hạn (1-2 Tuần):** **Tăng mạnh trung hạn (Strong Bullish Trend)**
*   **Vùng Biên Độ Price Action:**
    *   **Hỗ trợ cứng:** S1 = **`1179.75`** | S2 = **`1172.25`**
    *   **Kháng cự cứng:** R1 = **`1219.00`** | R2 = **`1220.75`**
*   **Biện chứng Đánh Biên:** Đậu tương đã kích hoạt Golden Cross H1 với xung lực nến rút chân khổng lồ 9.25 giá. Giá đã thoát ly khỏi vùng đáy tích lũy dưới và đang bám sát kênh tăng giá đi lên vùng kháng cự cao hơn. Chiến lược ưu tiên Canh mua biên dưới (Swing Long) để ăn trọn nhịp bứt phá 15-20 giá.
*   **Kế hoạch Lệnh Đánh Biên (Swing Trades - Mục tiêu >= 10 giá):**
    *   🚀 **Swing Long (Mua biên dưới):** Mua tại **`1172.25 - 1179.75 cents`** | Dừng lỗ (SL): **`1165.29 cents`** | Chốt lời (TP): **`1220.75 cents (Ăn trọn nhịp bứt phá Trend ~17 giá)`** (Lợi nhuận: **`>= 10.00 giá`**).
    *   🚀 **Swing Short (Bán biên trên):** Bán tại **`1219.00 - 1220.75 cents`** | Dừng lỗ (SL): **`1227.71 cents`** | Chốt lời (TP): **`1172.25 cents`** (Lợi nhuận: **`>= 10.00 giá`**).
*   *Nguyên tắc khớp lệnh:* Đặt lệnh Limit sát biên độ hỗ trợ S1/S2 hoặc kháng cự R1/R2. Cực kỳ ưu tiên khi có nến đảo chiều (Pinbar/Engulfing) đóng cửa trên khung H1/H4 ở vùng biên để xác nhận.

### F. Chiến Lược Gom Mùa Vụ Dài Hạn (Seasonal Accumulation Strategy)
*   **Chiến lược:** Mua tích lũy phòng thủ rủi ro replanting (gieo hạt lại) do ngập lụt tại Midwest Mỹ và nhu cầu dầu sinh học.
*   **Vùng gom chủ đạo (DCA Brackets):** Chia vốn gom từ **`1158.33 - 1172.25 cents`**. Chia vốn gom từ 1165.00 đến 1175.00 cents. Việc Argentina hoàn thành 75% thu hoạch đánh dấu áp lực cung tối đa đã trôi qua, củng cố đây là vùng đáy chu kỳ vững chắc để tích lũy.

---

*Báo cáo được tạo tự động bởi Hệ thống Phân tích CBOT Pro V2 vào ngày 30/05/2026 lúc 20:39 ICT.*
