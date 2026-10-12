# NHẬT KÝ BÁO CÁO PHÂN TÍCH HỆ THỐNG CBOT PRO V3 (ZC - ZW - ZS)
*Hệ thống phân tích tự động tích hợp Kỹ thuật H1/M15, Vĩ mô toàn cầu (Brent/DXY) và Nền tảng Nông nghiệp USDA*

Tài liệu được lưu trữ trực tiếp tại thư mục làm việc:
`c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\CBOT_Reports_Log.md`

---

# PHẦN I: THÔNG TIN TỔNG QUAN & VĨ MÔ

## 🌐 1. TỔNG QUAN VĨ MÔ TOÀN CẦU (MACRO INDICATORS OVERVIEW)
*Cập nhật tự động qua `macro_tracker.py` vào lúc 04:01 ICT ngày 13/10/2026*

| Chỉ số Vĩ mô | Mức giá hiện tại | Biến động 24h | Xu hướng & Đánh giá tác động đến Nông sản |
| :--- | :---: | :---: | :--- |
| **Dầu thô Brent (BZ=F)** | **$106.08 / thùng** | **+0.00%** | 📈 **Tích cực (Bullish):** Giá dầu duy trì ở mức cao hỗ trợ mạnh mẽ cho biofuels như Ethanol (ZC) và Biodiesel (ZS). Chi phí sản xuất neo cao tạo mức sàn hỗ trợ giá. |
| **Chỉ số DXY (USD Index)** | **102.59** | **+0.00%** | 📉 **Trung lập - Tiêu cực (Sức ép xuất khẩu):** DXY neo cao khiến hàng Mỹ kém cạnh tranh hơn ở thị trường quốc tế, cản trở xuất khẩu ngắn hạn. |


## 💰 DÒNG TIỀN COT (SMART MONEY MATRIX)
*Cập nhật từ nguồn CFTC Public API (Ngày báo cáo chốt sổ: **2026-10-06**)*

### Bảng Dòng Tiền Managed Money

| Mã | Commodity | Net Position | Tuần Qua | Trạng Thái Matrix | Điểm Bias |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **002602** | ZC | **329,839** | **-51,381** | **Q2 (DO NHAT) - XA LONG**<br>*Cam bat day. Canh gia hoi de danh SHORT.* | 🔴 **-1.0** |
| **001602** | ZW | **-28,830** | **-6,721** | **Q3 (DO DAM) - NHOI SHORT**<br>*Uu tien SHORT thuan xu huong.* | 🔴 **-1.5** |




### ✅ TƯƠNG QUAN VĨ MÔ ỔN ĐỊNH (NORMAL CORRELATION)
*   **Giá trị biến động 24h:** Dầu Brent: **`$106.08` (+0.00%)** | DXY: **`102.59` (+0.00%)** | Lúa mì CBOT: **`672.75¢` (+0.00%)**.
*   **Biện chứng liên thị trường:** Liên thị trường giao dịch ổn định, giá lúa mì bám sát các chỉ tiêu cung cầu cơ bản và không có hiện tượng bán tháo chéo quá mức từ nhóm năng lượng.
*   🚀 **Khuyến nghị chiến lược:** Tiếp tục duy trì kế hoạch giao dịch trong ngày (Intraday) và đánh biên (Swing) theo cản kỹ thuật đã hoạch định.


---

## 🌡️ 2. BẢN TIN THỜI TIẾT & MÙA VỤ TOÀN CẦU (WEATHER INTELLIGENCE REPORT)
*Cập nhật tự động lúc 04:01 ICT ngày 13/10/2026 — Nguồn: NOAA, USDA, BOM Australia*

### 🇺🇸 Thời tiết Nội địa Mỹ (US Domestic Weather)

| Vùng trồng trọt | Cây trồng chính | Diễn biến thời tiết | Tác động mùa vụ |
| :--- | :---: | :--- | :--- |
| **Midwest phía Đông** *(IL, IN, OH)* | 🌽🌱 Ngô/Đậu | Mưa lớn kéo dài ở phía Đông Corn Belt (Illinois, Ohio). | Vành đai phía Bắc vẫn khô hạn cục bộ |
| **Midwest phía Tây & Bắc** *(IA, MN, Dakotas)* | 🌽 Ngô | Trời nóng tại Midwest, mưa rải rác — Rủi ro: Khô hạn đe dọa nảy mầm -> Gom Long dài hạn (DCA) | Xác suất chuyển pha sang El Niño đạt 82% vào tháng 7. Hiện tại đang xuất hiện vùng khô hạn cục bộ ở rìa phía Bắc (Minnes... |
| **Southern Plains** *(KS, OK, TX)* | 🌾 Lúa mì đông | Mưa lớn bất ngờ xuất hiện tại vùng Southern Plains (Kansas, Oklahoma, Texas). | Mưa ngắn hạn -> Canh Short ngắn hạn / Gom Long dài hạn (DCA) |
| **Northern Plains** *(ND, SD, MT)* | 🌾 Lúa mì xuân | Đông 36% gieo, Xuân N/A | Lúa mì xuân gieo trồng phát triển thuận lợi. Lúa mì đông đã trổ bông vượt trung bình. |

### 🌍 Thời tiết Đối thủ Cạnh tranh & Liên Thị trường (Global Competitor Weather)

| Khu vực | Mã liên quan | Diễn biến thời tiết | Tác động cung cầu toàn cầu |
| :--- | :---: | :--- | :--- |
| **🇧🇷 Brazil (Safrinha)** | ZC | Bắt đầu thu hoạch, dự báo 107.8 triệu tấn | Hỗ trợ giá ngô Mỹ nếu năng suất Safrinha giảm. |
| **🇦🇷 Argentina (Ngô)** | ZC | Khô ráo thuận lợi cho thu hoạch ngô (đạt 66%). Sản lượng dự kiến 64 triệu tấn. | Áp lực cung ngắn hạn đang giảm dần. |
| **🇦🇺 Australia** | ZW | Hạn hán El Nino đe dọa mùa màng, sản lượng có thể giảm mạnh | Bullish dài hạn cho lúa mì toàn cầu. |
| **🇦🇷 Argentina (Lúa mì)** | ZW | Đã gieo trồng 14.2% diện tích lúa mì. Sản lượng dự kiến giảm 25% do chi phí phân bón cao và rủi ro El Niño. | Nguồn cung Nam Mỹ thắt chặt. |
| **🇷🇺🇪🇺 Black Sea & EU** | ZW | Nga: Sản lượng nâng lên 91.5 triệu tấn. Sương giá muộn cục bộ. EU MARS hạ yield do khô hạn tháng 4 tại Pháp/Đức. | Ảnh hưởng cạnh tranh xuất khẩu. |
| **🇧🇷 Brazil (Đậu tương)** | ZS | Thời tiết khô ráo thuận lợi cho xuất khẩu. Sản lượng dự báo đạt kỷ lục 180 triệu tấn. | Áp lực cung từ vụ kỷ lục Brazil. |
| **🇦🇷 Argentina (Đậu tương)** | ZS | Thu hoạch đậu tương đạt 75% dưới thời tiết khô hanh. Sản lượng 50.1 triệu tấn. | Áp lực thu hoạch sắp qua đỉnh. |
| **🇨🇳 Trung Quốc (Cầu)** | ZS | Trung Quốc nhập khẩu ròng mạnh liên tục để bổ sung tồn kho heo nội địa. | Bệ đỡ nhu cầu vững chắc. |

### 🌊 Trạng thái ENSO (El Niño / La Niña)
*   **Trạng thái hiện tại:** El Nino đang diễn ra (chính thức)
*   **Dự báo:** Xác suất La Niña đạt 82% vào tháng 7
*   **Tác động:** La Niña vĩ mô -> Gom Long dài hạn (DCA)

---

## 📌 3. DANH MỤC LỊCH SỬ BÁO CÁO (CẬP NHẬT PHIÊN CHỐT 13/10/2026)
*Thời gian đóng cửa phiên giao dịch được đồng bộ chính xác vào lúc **1:20 AM ICT ngày 13/10/2026***

| Ngày Báo Cáo (ICT) | Mã | Giá Chốt (Close) | Dự báo Chốt Phiên | Tín Hiệu H1 (EMA 21/50) | Volatility | Intraday Bias | Xem Chi Tiết |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **13/10/2026** | **ZC** | **483.50 ¢** | **483.17 ¢ (-0.33)** | 🐻 Bearish (484.07 < 489.77) | 1.50 cents | Rình mua (Long on dip) | [Xem Ngô (ZC)](#2-báo-cáo-mã-zc-ngô---phiên-chốt-13102026) |
| **13/10/2026** | **ZW** | **672.75 ¢** | **673.15 ¢ (+0.40)** | 🐻 Bearish (672.55 < 677.31) | 1.75 cents | Bán khống hồi (Short on rally) | [Xem Lúa mì (ZW)](#3-báo-cáo-mã-zw-lúa-mì---phiên-chốt-13102026) |
| **13/10/2026** 
---

# PHẦN II: TỔNG HỢP LỆNH & CHIẾN LƯỢC MÙA VỤ

## 🎯 1. TỔNG HỢP KHUYẾN NGHỊ HÀNH ĐỘNG THỰC CHIẾN (EXECUTIVE ACTION SUMMARY)
*Trang tổng hợp nhanh các lệnh và vị thế giao dịch cần thực hiện đón đầu cho cả 3 mã hàng hóa*

| Mã | Loại chiến lược | Điểm vào lệnh (Entry Zone) | Cắt lỗ (Stop Loss - SL) | Chốt lời (Take Profit - TP) | Vị thế chủ đạo & Ghi chú thực chiến |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZC** | **Long ngắn hạn (Intraday) (ZCZ26)** | **479.25 - 484.07 cents (Canh mua vùng hỗ trợ)** | **466.47 cents (Dưới cản S2 + 1.5x ATR)** | TP1: `500.25 cents` \| TP2: `544.75 cents` | CANH LONG ngắn hạn tại vùng hỗ trợ kỹ thuật H1 khi giá điều chỉnh sâu. |
| **ZC** | **Long trung hạn (Swing) (ZCH27)** | **492.00 - 493.50 cents** | **482.84 cents (Chống quét SL tuyệt đối)** | **559.00 cents (Ăn trọn biên độ ngô ~10.5 giá)** | LỆNH LONG trung hạn ở hỗ trợ S2 Price Action cứng (biên dưới). |
| **ZC** | **Short trung hạn (Swing) (ZCH27)** | **514.75 - 516.25 cents** | **517.16 cents** | **486.25 cents** | LỆNH SHORT trung hạn ở kháng cự R2 Price Action (biên trên). |
| **ZC** | **Long dài hạn (DCA) (ZCZ26)** | **460.16 - 470.25 cents** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng thủ La Niña và tồn kho thấp kỷ lục. |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZW** | **Short ngắn hạn (Intraday) (ZWZ26)** | **672.55 - 677.31 cents (Canh bán hồi kỹ thuật H1)** | **768.08 cents (Trên kháng cự R2 + 1.5x ATR)** | TP1: `670.75 cents` \| TP2: `661.50 cents` | LỆNH SHORT ngắn hạn thuận xu hướng khi hồi kỹ thuật H1. |
| **ZW** | **Long trung hạn (Swing) (ZWZ26)** | **668.75 - 670.75 cents** | **658.11 cents** | **676.00 cents (Đón sóng hồi trung hạn ~14.5 giá)** | LỆNH LONG trung hạn ở hỗ trợ S1/S2 đón sóng hồi trung hạn ~14.5 giá. |
| **ZW** | **Short trung hạn (Swing) (ZWZ26)** | **676.00 - 678.00 cents** | **679.39 cents** | **661.50 cents (Thuận xu hướng giảm ngắn hạn)** | LỆNH SHORT trung hạn thuận xu hướng ngắn hạn khi chạm kháng cự R1/R2. |
| **ZW** | **Long dài hạn (DCA) (ZWZ26)** | **647.95 - 661.50 cents** | Không áp dụng | Mục tiêu dài hạn | Canh mua DCA dài hạn quyết liệt (lệch pha cơ hội vĩ mô). |
| :---: | :---: | :---: | :---: | :---: | :--- |

---

## 🌾 2. CHIẾN LƯỢC ĐẶC BIỆT: MÙA VỤ 2026
*Phân tích toàn diện: Địa chính trị, Tồn kho WASDE, Thời tiết NOAA và Điểm vào lệnh Độc lập dựa trên Giá thành sản xuất*

### A. Phân tích Biện chứng Vĩ mô & Địa chính trị (Geopolitics & Maritime Logistics)
*   **Hành lang Biển Đen & Thuế Nga:** Rủi ro quân sự tại Biển Đen làm tăng bảo hiểm tàu biển. Thuế xuất khẩu lúa mì biến động linh hoạt của Nga kìm hãm nguồn cung giá rẻ, buộc người mua dịch chuyển sang lúa mì Mỹ (ZW).
*   **Tắc nghẽn Biển Đỏ & Kênh Suez:** Tàu chở ngũ cốc từ Biển Đen/Châu Âu sang Á phải đi vòng qua Mũi Hảo Vọng (+10-15 ngày vận chuyển, cước tăng 30-40%). Điều này làm giảm khả năng cạnh tranh của lúa mì Pháp/Nga tại Châu Á, tạo lợi thế lớn cho lúa mì xuất khẩu từ bờ Tây nước Mỹ (Pacific Northwest - PNW) đi thẳng qua Thái Bình Dương.
*   **Hạn hán Kênh đào Panama:** Giới hạn số lượt quá cảnh của các tàu chở Ngô/Đậu tương Mỹ từ vịnh Gulf sang Trung Quốc, làm tăng phí bảo hiểm tắc nghẽn và giá xuất khẩu tại cảng (FOB Gulf).
*   **USD/BRL & Căng thẳng Mỹ-Trung:** Đồng Real Brazil (BRL) mất giá khiến nông dân Brazil bán hàng mạnh. Tuy nhiên, sự tắc nghẽn hạ tầng tại cảng Santos/Paranagua trong mùa cao điểm thu hoạch sẽ đẩy dòng tiền mua đậu thô của Trung Quốc quay lại Mỹ trong cửa sổ tháng 9-12.

### B. Biện chứng Cân đối Tồn kho & Biên an toàn (USDA WASDE Niên vụ 2026/27)
*   **Đậu tương (ZS): Tỷ lệ Stocks-to-Use giảm mạnh xuống 6.9%** (dưới ngưỡng an toàn 8%). Brent neo cao ở `$95.5` thúc đẩy nhu cầu ép dầu nội địa (Biodiesel và SAF) lên đỉnh lịch sử, triệt tiêu rủi ro dư thừa nguồn cung thô.
*   **Ngô (ZC): Tỷ lệ Stocks-to-Use giảm xuống 12.1%** (sát ranh giới báo động 12%), tồn kho thế giới thấp nhất 12 năm (`277.5M tấn`). Không có biên an toàn cho bất kỳ sự cố thời tiết thụ phấn nào trong tháng 7.
*   **Lúa mì (ZW): Tỷ lệ Stocks-to-Use giảm mạnh từ 46.1% xuống 40.7%**, tồn kho thế giới giảm liên tiếp năm thứ 4.

### C. Cơ chế truyền dẫn thời tiết NOAA & Động học Sinh trưởng
*   **Mưa bão ngập úng Midwest:** Khiến nông dân Mỹ phải gieo hạt lại (replanting) đậu tương, rút ngắn chu kỳ sinh trưởng của cây non và đẩy giai đoạn điền hạt nhạy cảm nhất (tháng 8) vào đúng đỉnh khô hạn cuối hè của chu kỳ La Niña (xác suất chuyển pha **82%**).
*   **Khô hạn phía Bắc Mỹ:** Gió khô kéo độ ẩm đất bề mặt xuống thấp, đe dọa trực tiếp tỷ lệ nảy mầm và thiết lập bộ rễ của ngô non ở Northern Plains (Minnesota, Dakotas).

### D. Hệ thống Báo cáo Nông nghiệp USDA (USDA Agricultural Reports)
*Tổng hợp chi tiết 4 loại báo cáo nông nghiệp cốt lõi chi phối thị trường tương lai CBOT*

#### 1. Báo cáo Tiến độ Mùa vụ (USDA Crop Progress)
| Mã nông sản | Chỉ tiêu | Tiến độ tuần này | Cùng kỳ năm ngoái | Trung bình 5 năm | Xếp hạng chất lượng (Good/Excellent) | Tác động biện chứng mùa vụ |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Gieo trồng | **97% đã gieo trồng** | 92% | 89% | **54% Good to Excellent** | Tiến độ nhanh -> Canh Short ngắn hạn - Trung bình 5 năm đạt 96%. Tiến độ hiện tại được cập nhật mới nhất. |
| **ZW** | Lúa đông | **Đông N/A, Xuân N/A** | 3% | 2% | **Đông N/A (Cuối vụ), Xuân N/A** | Bắt đầu thu hoạch -> Canh Short ngắn hạn - Trung bình 5 năm đạt 6%. Báo cáo tiến độ thu hoạch mới nhất. |
| **ZW** | Lúa xuân | **Đông 36% gieo, Xuân N/A** | 91% | 88% | Chưa xếp hạng | Tiến độ ổn định -> Canh Short ngắn hạn - Lúa mì xuân gieo trồng phát triển thuận lợi. Lúa mì đông đã trổ bông vượt trung bình. |

#### 2. Báo cáo Cung cầu & Tồn kho USDA (USDA WASDE)
| Mã nông sản | Thông số Tồn kho | Mỹ (US Ending Stocks) | Thế giới (Global) | Lần cập nhật tới | Tác động biện chứng WASDE |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **ZC** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | 1,567 triệu bushels (2026/27)<br>**1,849 triệu bushels (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 272.10 triệu tấn (2026/27)<br>**280.44 triệu tấn (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 11/11/2026 lúc 00:00 (VN) | Tồn kho thấp nhất 12 năm -> Gom Long dài hạn (DCA) - Tồn kho ngô toàn cầu chạm mức thấp nhất 12 năm qua (kể từ niên vụ 2013/14). |
| **ZW** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | 717 triệu bushels (2026/27)<br>**740 triệu bushels (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 276.29 triệu tấn (2026/27)<br>**276.04 triệu tấn (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 11/11/2026 lúc 00:00 (VN) | Cung toàn cầu giảm -> Gom Long dài hạn (DCA) - Giảm 4.2 triệu tấn so với niên vụ trước, tiếp tục thắt chặt cung cầu toàn cầu. |

#### 3. Báo cáo Bán hàng & Giao hàng Xuất khẩu (USDA Weekly Export Sales & Inspections)
| Mã nông sản | Báo cáo | Số liệu trước đó | Số liệu mới nhất | Dự báo kỳ tiếp theo | Lần cập nhật tới | Tác động biện chứng xuất khẩu |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Bán hàng & Giao hàng | Net Sales (Tuần trước): 536,000 MT (09/24/2026) | **Net Sales (Bán hàng): 769,500 MT (Kỳ 10/01/2026)** | N/A | Thứ 5 hàng tuần, 21:30 (VN) | N/A - Ngô niên vụ 2025/26 đạt 769.5 nghìn tấn, đưa lũy kế lên 7.402 triệu tấn, cao hơn 8.5% so với cùng kỳ năm ngoái. |
| **ZW** | Bán hàng & Giao hàng | Net Sales (Tuần trước): 289,300 MT (09/24/2026) | **Net Sales (Bán hàng): 451,600 MT (Kỳ 10/01/2026)** | N/A | Thứ 5 hàng tuần, 21:30 (VN) | N/A - Lúa Mì niên vụ 2026/27 đạt 451.6 nghìn tấn, đưa lũy kế lên 6.822 triệu tấn, thấp hơn 31.8% so với cùng kỳ năm ngoái. |

#### 4. Báo cáo Sản lượng Cây trồng & Đối thủ Nam Mỹ (USDA Crop Production & Competitors)
| Mã nông sản | Thu hoạch Mỹ / Vụ mùa | Sản lượng Đối thủ Nam Mỹ | Lần cập nhật tới | Tác động biện chứng cung cầu |
| :---: | :--- | :--- | :---: | :--- |
| **ZC** | Thu hoạch: Mỹ: 23% thu hoạch | Brazil & Argentina (Khô hạn Safrinha Brazil; Argentina đạt 64M tấn) | Liên tục (Cập nhật hàng ngày) | Brazil vụ 2 khô hạn -> Gom Long trung hạn - Argentina: Dự báo sản lượng đạt kỷ lục 64 triệu tấn. Brazil: Vụ 1 kết thúc; ngô vụ 2 (Safrinha) đang chịu khô hạn cục bộ tại các bang phía Nam gây lo ngại sụt giảm năng suất. |
| **ZW** | Thu hoạch: Đông N/A, Xuân N/A | Úc & Argentina (Úc giảm 41% sản lượng, Arg giảm 25%) | Liên tục (Cập nhật hàng tuần) | Thiệt hại kép -> Gom Long dài hạn (DCA) - Úc: Diện tích gieo trồng dự kiến giảm sâu 20.4% xuống còn 9.8 triệu ha. Sản lượng dự kiến giảm mạnh 41% xuống 21.3 triệu tấn do hạn hán đầu vụ ở phía Bắc NSW/Nam Queensland. Argentina: Đã gieo trồng được 14.2% diện tích. Sản lượng dự kiến đạt 20.7 triệu tấn (giảm 25% so với mức kỷ lục niên vụ trước) do nông dân lo ngại chi phí phân bón cao và rủi ro bệnh dịch từ El Niño. |

### E. Thiết lập Vùng Entry Độc lập dựa trên Giá thành Sản xuất & Thống kê 5 năm
Chúng tôi không sử dụng hỗ trợ kỹ thuật S2 của V3 Pro làm điểm vào lệnh chính thức, mà thiết lập các vùng mua độc lập dựa trên **Giá thành sản xuất của nông dân Mỹ (US Production Cost)** và **Thống kê phân bổ giá 5 năm gần nhất**:

*   **Ngô (Corn):**
    *   **Leg 1 (ZCU26 Tháng 09/2026):** 
        *   *Vị thế:* **Long Hold (Ngắn hạn)**.
        *   *Biện chứng:* Tấn công trực diện Weather Premium của chu kỳ thụ phấn tháng 7. HĐ ZCU26 rẻ hơn ZCZ26 giúp tối ưu dòng vốn.
        *   *Thiết lập:* **Entry: `420.00 - 433.00` | SL: `413.00` | TP1: `475.00` | TP2: `495.00`**.
        *   *Thời điểm Tất toán:* **15/07 - 25/07/2026** (Tất toán chốt lời trước FND ngày 31/08).
    *   **Leg 2 (ZCZ26 Tháng 12/2026):** 
        *   *Vị thế:* **Long Hold (Dài hạn)**.
        *   *Biện chứng:* Đón đầu rủi ro mất mùa vĩ mô kéo dài sang mùa đông do La Niña. Áp dụng Entry thấp hơn để bù đắp phí Contango.
        *   *Thiết lập:* **Entry: `430.00 - 438.00` | SL: `422.00` | TP1: `510.00` | TP2: `535.00`**.
        *   *Thời điểm Tất toán:* **15/11 - 30/11/2026**.
*   **Đậu tương (Soybeans - ZSX26 Tháng 11/2026):**
    *   *Vị thế:* **Long Accumulation (Mua gom tích sản chốt 2 đợt)**.
    *   *Biện chứng:* Giao dịch duy nhất HĐ Tháng 11 do Contango cực thấp (`0.5`), nhưng phân bổ chốt lời thành 2 đợt.
    *   *Thiết lập:* **Entry: `1125.00 - 1140.00` | SL: `1105.00` | TP1: `1200.00` (Đợt 1) | TP2: `1320.00` (Đợt 2)**.
    *   *Thời điểm Tất toán:*
        *   *Đợt 1 (50% vị thế):* **20/08 - 05/09/2026** (Đỉnh điểm khô hạn điền hạt cuối hè).
        *   *Đợt 2 (50% vị thế):* **15/10 - 30/10/2026** (Sóng khô hạn gieo trồng sớm Nam Mỹ).
*   **Lúa mì (Wheat):**
    *   **Leg 1 (ZWU26 Tháng 09/2026):**
        *   *Vị thế:* **Accumulative Long (Ngắn hạn)**.
        *   *Biện chứng:* Ăn nhịp phục hồi sau thu hoạch mùa hè (Post-Harvest Bounce). ZWU26 rẻ hơn ZWZ26 `17.25` là lựa chọn tối ưu.
        *   *Thiết lập:* **Entry: `580.00 - 595.00` | SL: `565.00` | TP1: `645.00` | TP2: `675.00`**.
        *   *Thời điểm Tất toán:* **10/08 - 20/08/2026** (Tất toán trước FND ngày 31/08).
    *   **Leg 2 (ZWZ26 Tháng 12/2026):**
        *   *Vị thế:* **Accumulative Long (Dài hạn)**.
        *   *Biện chứng:* Phòng thủ rủi ro mất mùa diện rộng ở Úc/Argentina và mùa đông khắc nghiệt tại Bắc Mỹ.
        *   *Thiết lập:* **Entry: `590.00 - 605.00` | SL: `575.00` | TP1: `690.00` | TP2: `720.00`**.
        *   *Thời điểm Tất toán:* **15/11 - 30/11/2026**.

### F. Ma trận Giao dịch "MÙA VỤ 2026" - Cấu trúc 2 Giai đoạn (Dual-Leg Setup)

| HĐ Chỉ định | Chiến lược & Phân nhóm | Điểm vào lệnh Độc lập | Cắt lỗ bảo vệ vốn | Chốt lời & Tất toán | Phân bổ vốn |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **ZCU26** (Corn) | Long Hold (Leg 1 - Ngắn hạn) | **`420.00 - 433.00`**<br>*(Tháng 6 - 7)* | **`413.00`** | **`475.00`** \| **`495.00`**<br>*(Tất toán: 15/07 - 25/07)* | **10%** |
| **ZCZ26** (Corn) | Long Hold (Leg 2 - Dài hạn) | **`430.00 - 438.00`**<br>*(Tháng 6 - 7)* | **`422.00`** | **`510.00`** \| **`535.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |
| **ZWU26** (Wheat)| Accumulative Long (Leg 1 - Ngắn hạn)| **`580.00 - 595.00`**<br>*(Tháng 6)* | **`565.00`** | **`645.00`** \| **`675.00`**<br>*(Tất toán: 10/08 - 20/08)* | **10%** |
| **ZWZ26** (Wheat)| Accumulative Long (Leg 2 - Dài hạn) | **`590.00 - 605.00`**<br>*(Tháng 6)* | **`575.00`** | **`690.00`** \| **`720.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |

### G. Định nghĩa Chiến thuật & Ma trận Phân bổ vốn Chi tiết (Capital Allocation Guide)

#### 1. Biện chứng Chiến thuật "Long Hold" vs "Long Accumulation"
*   **Long Hold (Mua và Nắm giữ Vị thế):** Mở vị thế Long tại vùng giá chỉ định và giữ chặt xuyên suốt thời kỳ nhạy cảm của mùa vụ (ví dụ: giai đoạn ngô thụ phấn pollination kéo dài 2-3 tuần của tháng 7). Không thực hiện DCA thêm nếu giá chạy trong biên độ. Chiến thuật này nhằm ăn trọn con sóng tăng sốc khi "Phí bảo hiểm thời tiết" (Weather Premium) được kích hoạt do nắng nóng đỉnh hè của La Niña (xác suất 82%).
*   **Long Accumulation (Mua gom Tích lũy):** Chủ động chia nguồn vốn làm 3-4 phần để gom mua dần (DCA Long) khi giá điều chỉnh sâu vào vùng chiết khấu. Chiến thuật này phù hợp với Đậu tương (ZSX26) khi tiến độ nảy mầm kéo dài và nông dân phải gieo hạt lại (replanting) do ngập úng Đông Midwest. Nó tối ưu hóa giá vốn trung bình (average entry price) nằm sát vùng giá thành sản xuất gieo trồng của nông dân.

#### 2. Phân bổ Vốn & Quản trị rủi ro Ký quỹ (Portfolio Money Management)
*   **Bộ đệm Ký quỹ tự do (Margin Buffer - 50%):** Giữ dưới dạng tiền mặt/ký quỹ tự do để tài khoản chịu đựng được các đợt rung lắc mạnh (noise) của thị trường tương lai CBOT mà không bị kích hoạt gọi ký quỹ (Margin Call).
*   **Vốn giải ngân thực chiến (Active Capital - 50%):** Phân bổ cụ thể vào các chiến dịch:
    *   🌽 **Ngô (Corn): Phân bổ 15% tổng vốn.** (Tập trung 10% cho Leg 1 - Long Hold ZCU26 tại vùng `420.00 - 433.00`; phân bổ 5% cho Leg 2 - Long Hold ZCZ26 tích lũy sâu hơn tại `430.00 - 438.00`).
    *   🌱 **Đậu tương (Soybeans): Phân bổ 20% tổng vốn.** (Vào vị thế Long Accumulation ZSX26 chia đều thành 3 đợt mua gom giá tốt. Chốt lời 10% vốn giải ngân ở đợt 1 và giữ 10% còn lại cho sóng quý 4).
    *   🌾 **Lúa mì (Wheat): Phân bổ 15% tổng vốn.** (Tập trung 10% cho Leg 1 - Accumulative Long ZWU26 tại vùng `580.00 - 595.00`; phân bổ 5% cho Leg 2 - Accumulative Long ZWZ26 gom sâu hơn tại `590.00 - 605.00`).

#### 3. Quy tắc Tất toán & Đóng vị thế theo mùa vụ (Seasonal Liquidation Protocol)
*   **Nguyên lý hao mòn phí bảo hiểm thời tiết (Weather Premium Decay):** Phí bảo hiểm thời tiết là giá trị hao mòn nhanh. Khi cây trồng vượt qua giai đoạn nhạy cảm nhất mà không xảy ra thiên tai nghiêm trọng hơn, hoặc khi mùa gặt cận kề, Weather Premium sẽ bốc hơi. Việc đóng vị thế đúng thời điểm chốt lời quan trọng hơn cố chờ giá chạm mục tiêu kỹ thuật tối đa.
*   **Lịch trình đóng vị thế chi tiết:**
    - **🌽 Với Ngô:**
        *   *Leg 1 - Long Hold (ZCU26):* Bắt buộc tất toán trước ngày **25/07/2026** (trước FND ngày 31/08).
        *   *Leg 2 - Long Hold (ZCZ26):* Tất toán trong cửa sổ từ **15/11 - 30/11/2026** khi mùa đông Bắc Mỹ cận kề thúc đẩy nhu cầu sưởi ấm và năng lượng.
    - **🌱 Với Đậu tương (ZSX26):**
        *   *Đợt 1 - Long Accumulation (50% vị thế):* Chốt lời từ ngày **20/08 - 05/09/2026** khi đậu tương hoàn thành điền hạt.
        *   *Đợt 2 - Long Accumulation (50% vị thế):* Chốt lời hoàn toàn từ ngày **15/10 - 30/10/2026** khi Nam Mỹ bắt đầu hạn hán gieo trồng.
    - **🌾 Với Lúa mì:**
        *   *Leg 1 - Accumulative Long (ZWU26):* Tất toán trước ngày **20/08/2026** (trước FND ngày 31/08).
        *   *Leg 2 - Accumulative Long (ZWZ26):* Tất toán trong cửa sổ từ **15/11 - 30/11/2026** đón đỉnh giá của chu kỳ khô hạn mùa đông Bắc Bán Cầu.

---


# PHẦN III: HỒ SƠ ĐỘC LẬP TỪNG MÃ NÔNG SẢN
*Mỗi mã được phân tích hoàn toàn độc lập. Dữ liệu chung (Brent, DXY) đồng bộ tự động từ cùng một nguồn.*

## 🌽 BÁO CÁO MÃ ZC (NGÔ) — HỒ SƠ ĐỘC LẬP | PHIÊN CHỐT 13/10/2026

### A. Tóm tắt Nhanh & Bias Tổng Hợp Hôm Nay

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | La Niña rủi ro vĩ mô | Định hướng gom DCA dài hạn |
| **Trung hạn** | ↕️ **Đi ngang (Sideways)** | Đi ngang tích lũy (Sideways Accumulation) | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | 🐻 **Giảm (Bearish)** | EMA_21 H1 < EMA_50 H1 (Áp lực bán duy trì) | Canh vào lệnh ngắn hạn (Intraday) |

*   **Giá Chốt Phiên (Close):** 483.50 cents | **Dự báo Chốt Phiên:** **`483.17 cents`** (-0.33).
*   **Thanh khoản phiên chốt:** Volume: **`203,794`** (Chênh lệch: **`+180,048`**) | OI: **`866,535`** (Chênh lệch: **`-20,986`**)
*   **Mô hình nến H1:** **`Doji (Nến lưỡng lự thế trận)`**
*   **Dòng tiền (Volume + OI):** **`Tăng do phe Short chốt lời (Short Covering)`**
*   **Đánh giá xu hướng kết hợp:** 📈 **TÍCH LŨY TÍCH CỰC (Accumulation):** Nến đi ngang nhưng dòng tiền âm thầm gia tăng (OI tăng), báo hiệu chuẩn bị có nhịp bứt phá tăng.

---

### B. Bối Cảnh Vĩ Mô & Dòng Tiền COT (Smart Money Matrix)
*(Dữ liệu chung đồng bộ tự động từ `macro_tracker.py`)*


| Chỉ số | Giá trị Hiện tại | Biến động 24h | Tác động Biện chứng lên Ngô (ZC) |
| :--- | :---: | :---: | :--- |
| **Dầu Brent** | **$106.08** | **+0.00%** | Giá dầu Tăng hỗ trợ biên lợi nhuận pha chế Ethanol, kéo theo nhu cầu ngô tích cực. |
| **USD Index** | **102.59** | **+0.00%** | DXY Tăng làm giảm sức cạnh tranh xuất khẩu của ngô Mỹ so với Brazil/Argentina. |



| Báo cáo COT Managed Money | Ngô (ZC) | Đánh giá & Hành động |
| :--- | :---: | :--- |
| **Ngày Báo Cáo** | **2026-10-06** | Cập nhật mới nhất từ CFTC |
| **Trạng Thái Matrix** | **Q2 (DO NHAT) - XA LONG** | *Cam bat day. Canh gia hoi de danh SHORT.* |
| **Net Position** | **329,839** | Hợp đồng (Long - Short) |
| **Thay đổi Tuần qua** | **-51,381** | Hợp đồng thay đổi so với tuần trước |


---

### C. Phân Tích Kỹ Thuật H1/M15 (HĐ ZCZ26)
*   **Chỉ báo EMA H1:** `EMA_21` (484.07) < `EMA_50` (489.77).
*   **Động lượng & Dao động:** RSI (14) = **`44.95`** | ATR (14) = **`2.52`** cents | Volatility = **`1.50 cents`**.
*   **Vùng cản Pivot:** Hỗ trợ S1: **`479.25`** | S2: **`470.25`** || Kháng cự R1: **`500.25`** | R2: **`544.75`**

---

### D. Cơ Bản, Tồn Kho USDA & Xuất Khẩu (Export Sales)


| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | 1,849 triệu bushels (2026/27) | Tồn kho thấp nhất 12 năm -> Gom Long dài hạn (DCA) |
| **Tồn kho Thế giới** | 280.44 triệu tấn (2026/27) | Tồn kho ngô toàn cầu chạm mức thấp nhất 12 năm qua (kể từ niên vụ 2013/14). |
| **Tiến độ Gieo trồng** | 97% đã gieo trồng | Tiến độ nhanh -> Canh Short ngắn hạn |
| **Chất lượng G/E** | 54% Good to Excellent | Phản ánh rủi ro thời tiết Midwest |
| **Đối thủ (Brazil)** | Brazil & Argentina | Brazil vụ 2 khô hạn -> Gom Long trung hạn |

*   **Export Sales (Báo Cáo Mới Nhất):** NoData

---

### E. Thời Tiết & Mùa Vụ (Tự động từ Open-Meteo / NOAA)
*   **Trạng thái ENSO (NOAA):** El Niño Advisory


---

### F. Khuyến Nghị Giao Dịch Chuyên Sâu (ZC)

*   🚀 **Long ngắn hạn (Intraday) (Ngắn hạn - HĐ ZCZ26):**
    *   *Chiến lược:* Giao dịch chớp nhoáng theo biên độ H1.
    *   *Thiết lập:* Entry: **`479.25 - 484.07 cents (Canh mua vùng hỗ trợ)`** | SL: **`466.47 cents (Dưới cản S2 + 1.5x ATR)`** | TP: `500.25 cents` / `544.75 cents`.
*   🚀 **Trung hạn (Swing Trades - HĐ ZCH27):**
    *   *Long:* Entry: **`492.00 - 493.50 cents`** | SL: **`482.84 cents (Chống quét SL tuyệt đối)`** | TP: **`559.00 cents (Ăn trọn biên độ ngô ~10.5 giá)`**.
    *   *Short:* Entry: **`514.75 - 516.25 cents`** | SL: **`517.16 cents`** | TP: **`486.25 cents`**.
*   🚀 **Long dài hạn (DCA) (Dài hạn - HĐ ZCZ26):**
    *   *Chiến lược:* Mua tích lũy phòng thủ rủi ro địa chính trị và thời tiết vĩ mô.
    *   *Thiết lập:* Entry gom: **`460.16 - 470.25 cents`**

---

### G. 🤖 Dự Báo Future Chart AI (Simulation 5 Ngày)
*(Mã hợp đồng: **ZCU26 (September 2026)** | Điểm Bias Tổng Hợp: **+3.60**)*

| Ngày Giao Dịch | Phiên (Session) | Mở (Open) | Cao (High) | Thấp (Low) | Đóng (Close) | Thay đổi | Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mon 12/10** | Asia 07-11 | 483.50 | 487.25 | 480.25 | **483.75** | **+0.25¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | Asia 11-15 | 483.75 | 486.50 | 480.00 | **483.25** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Mon 12/10** | London 15-19 | 483.25 | 486.25 | 479.25 | **484.00** | **+0.75¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | Pre-NY 19-21 | 484.00 | 488.50 | 479.00 | **484.75** | **+0.75¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | NY Open 21-23 | 484.75 | 490.25 | 478.50 | **487.00** | **+2.25¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | NY Close 23-01 | 487.00 | 490.00 | 482.75 | **487.25** | **+0.25¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Asia 07-11 | 487.25 | 490.50 | 480.75 | **488.00** | **+0.75¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Asia 11-15 | 488.00 | 491.00 | 483.50 | **487.50** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Tue 13/10** | London 15-19 | 487.50 | 491.50 | 481.75 | **488.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Pre-NY 19-21 | 488.00 | 490.50 | 484.75 | **488.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | NY Open 21-23 | 488.50 | 492.00 | 482.50 | **489.50** | **+1.00¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | NY Close 23-01 | 489.50 | 492.25 | 487.00 | **489.50** | **+0.00¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | Asia 07-11 | 489.50 | 492.25 | 487.00 | **489.00** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Wed 14/10** | Asia 11-15 | 489.00 | 492.00 | 485.75 | **488.75** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Wed 14/10** | London 15-19 | 488.75 | 492.75 | 483.50 | **489.25** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | Pre-NY 19-21 | 489.25 | 494.00 | 482.25 | **491.25** | **+2.00¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | NY Open 21-23 | 491.25 | 499.25 | 484.25 | **492.75** | **+1.50¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | NY Close 23-01 | 492.75 | 497.25 | 488.50 | **492.25** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Thu 15/10** | Asia 07-11 | 492.25 | 494.50 | 489.50 | **492.00** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Thu 15/10** | Asia 11-15 | 492.00 | 494.00 | 487.50 | **492.25** | **+0.25¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | London 15-19 | 492.25 | 496.00 | 489.50 | **492.75** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | Pre-NY 19-21 | 492.75 | 495.75 | 488.25 | **493.00** | **+0.25¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | NY Open 21-23 | 493.00 | 497.25 | 489.75 | **493.75** | **+0.75¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | NY Close 23-01 | 493.75 | 497.25 | 491.50 | **493.75** | **+0.00¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | Asia 07-11 | 493.75 | 497.50 | 490.25 | **493.50** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 16/10** | Asia 11-15 | 493.50 | 497.00 | 490.25 | **493.25** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 16/10** | London 15-19 | 493.25 | 496.25 | 490.50 | **493.50** | **+0.25¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | Pre-NY 19-21 | 493.50 | 496.50 | 490.75 | **493.50** | **+0.00¢** 🟢 | 🔴 BEAR |
| **Fri 16/10** | NY Open 21-23 | 493.50 | 497.50 | 490.00 | **494.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | NY Close 23-01 | 494.00 | 498.00 | 492.25 | **493.75** | **-0.25¢** 🔴 | 🔴 BEAR |

**Kịch bản theo ngày:**
- **Mon 12/10:** USDA G/E 68% + Silking Window Bắt Đầu — *USDA Crop Progress: G/E Ngô 68% (ổn định). QUAN TRỌNG HƠN: Silking (thụ phấn) bắt đầu tại Iowa/Illinois — đây là giai đoạn NHẠY CẢM NHẤT với nhiệt độ. Mỗi ngày >35°C trong tuần này có thể phá hủy 2-5% năng suất. Pollination Risk Premium được xây dựng từ phiên NY.*
- **Tue 13/10:** Phản ứng USDA Ngô — *Thị trường tiêu hóa USDA Crop Progress. Pollination Risk Premium duy trì lực mua. Giá kiểm tra vùng R1 422.00.*
- **Wed 14/10:** EIA Ethanol + 7-Day Heat Forecast Update — *EIA Ethanol Production (thứ 4): Kỳ vọng ~1.05 triệu thùng/ngày (tốt hơn 1.04 tuần trước). QUAN TRỌNG HƠN: 7-Day weather model GFS/Euro cập nhật — nếu dự báo nhiệt độ >35°C tại Iowa trong 5-7 ngày tới trong giai đoạn Silking peak → Pollination Risk Premium tăng đột biến 5-10¢. Đây là phiên biến động nhất tuần cho ZC.*
- **Thu 15/10:** Export Sales Weekly - Trung Bình — *Export Sales ngô tuần này ổn định. Brazil vẫn cạnh tranh nhưng Pollination Risk Premium hỗ trợ floor giá. Thị trường chờ xác nhận từ weather model.*
- **Fri 16/10:** Đóng vị thế cuối tuần — *Ngô không có catalyst mới cuối tuần. Giá dao động hẹp. Weather outlook tuần tới sẽ quyết định hướng đi tiếp theo của Pollination Risk Premium.*


=====================================================================================


## 🌾 BÁO CÁO MÃ ZW (LÚA MÌ) — HỒ SƠ ĐỘC LẬP | PHIÊN CHỐT 13/10/2026

### A. Tóm tắt Nhanh & Bias Tổng Hợp Hôm Nay

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | La Niña rủi ro vĩ mô | Định hướng gom DCA dài hạn |
| **Trung hạn** | 🐻 **Giảm (Bearish)** | Giảm điều chỉnh tích lũy (Bearish Correction & Consolidation) | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | 🐻 **Giảm (Bearish)** | EMA_21 H1 < EMA_50 H1 (Áp lực bán duy trì) | Canh vào lệnh ngắn hạn (Intraday) |

*   **Giá Chốt Phiên (Close):** 672.75 cents | **Dự báo Chốt Phiên:** **`673.15 cents`** (+0.40).
*   **Thanh khoản phiên chốt:** Volume: **`69,904`** (Chênh lệch: **`+64,826`**) | OI: **`252,568`** (Chênh lệch: **`+1,168`**)
*   **Mô hình nến H1:** **`Không phát hiện mô hình nến đặc biệt`**
*   **Dòng tiền (Volume + OI):** **`Tăng mạnh mẽ (Strong Bullish / Long Buildup)`**
*   **Đánh giá xu hướng kết hợp:** 📈 **TÍCH LŨY TÍCH CỰC (Accumulation):** Nến đi ngang nhưng dòng tiền âm thầm gia tăng (OI tăng), báo hiệu chuẩn bị có nhịp bứt phá tăng.

---

### B. Bối Cảnh Vĩ Mô & Dòng Tiền COT (Smart Money Matrix)
*(Dữ liệu chung đồng bộ tự động từ `macro_tracker.py`)*


| Chỉ số | Giá trị Hiện tại | Biến động 24h | Tác động Biện chứng lên Lúa Mì (ZW) |
| :--- | :---: | :---: | :--- |
| **Dầu Brent** | **$106.08** | **+0.00%** | Giá dầu Tăng tăng premium rủi ro địa chính trị và logistics Biển Đen, hỗ trợ giá lúa mì. |
| **USD Index** | **102.59** | **+0.00%** | DXY Tăng khiến lúa mì Mỹ đắt đỏ hơn đối với các khách hàng truyền thống như Ai Cập/Châu Á. |



| Báo cáo COT Managed Money | Lúa Mì (ZW) | Đánh giá & Hành động |
| :--- | :---: | :--- |
| **Ngày Báo Cáo** | **2026-10-06** | Cập nhật mới nhất từ CFTC |
| **Trạng Thái Matrix** | **Q3 (DO DAM) - NHOI SHORT** | *Uu tien SHORT thuan xu huong.* |
| **Net Position** | **-28,830** | Hợp đồng (Long - Short) |
| **Thay đổi Tuần qua** | **-6,721** | Hợp đồng thay đổi so với tuần trước |


---

### C. Phân Tích Kỹ Thuật H1/M15 (HĐ ZWZ26)
*   **Chỉ báo EMA H1:** `EMA_21` (672.55) < `EMA_50` (677.31).
*   **Động lượng & Dao động:** RSI (14) = **`48.52`** | ATR (14) = **`3.39`** cents | Volatility = **`1.75 cents`**.
*   **Vùng cản Pivot:** Hỗ trợ S1: **`670.75`** | S2: **`661.50`** || Kháng cự R1: **`676.00`** | R2: **`763.00`**

---

### D. Cơ Bản, Tồn Kho USDA & Xuất Khẩu (Export Sales)


| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | 740 triệu bushels (2026/27) | Cung toàn cầu giảm -> Gom Long dài hạn (DCA) |
| **Tiến độ Thu hoạch** | Đông N/A, Xuân N/A | Bắt đầu thu hoạch -> Canh Short ngắn hạn |
| **Chất lượng G/E** | Đông N/A (Cuối vụ), Xuân N/A | Cực kỳ thấp, rủi ro thiếu hụt chất lượng cao |
| **Đối thủ (Australia)** | Hạn hán El Nino đe dọa mùa màng, sản lượng có thể giảm mạnh | Tác động cung cầu Châu Á |
| **Đối thủ (Argentina)**| Đã gieo trồng 14.2% diện tích lúa mì. Sản lượng dự kiến giảm 25% do chi phí phân bón cao và rủi ro El Niño. | Áp lực nguồn cung Nam Bán Cầu |

*   **Export Sales (Báo Cáo Mới Nhất):** NoData

---

### E. Thời Tiết & Mùa Vụ (Tự động từ Open-Meteo / NOAA)
*   **Trạng thái ENSO (NOAA):** El Niño Advisory


---

### F. Khuyến Nghị Giao Dịch Chuyên Sâu (ZW)

*   🚀 **Short ngắn hạn (Intraday) (Ngắn hạn - HĐ ZWZ26):**
    *   *Chiến lược:* Giao dịch chớp nhoáng theo biên độ H1.
    *   *Thiết lập:* Entry: **`672.55 - 677.31 cents (Canh bán hồi kỹ thuật H1)`** | SL: **`768.08 cents (Trên kháng cự R2 + 1.5x ATR)`** | TP: `670.75 cents` / `661.50 cents`.
*   🚀 **Trung hạn (Swing Trades - HĐ ZWZ26):**
    *   *Long:* Entry: **`668.75 - 670.75 cents`** | SL: **`658.11 cents`** | TP: **`676.00 cents (Đón sóng hồi trung hạn ~14.5 giá)`**.
    *   *Short:* Entry: **`676.00 - 678.00 cents`** | SL: **`679.39 cents`** | TP: **`661.50 cents (Thuận xu hướng giảm ngắn hạn)`**.
*   🚀 **Long dài hạn (DCA) (Dài hạn - HĐ ZWZ26):**
    *   *Chiến lược:* Mua tích lũy phòng thủ rủi ro địa chính trị và thời tiết vĩ mô.
    *   *Thiết lập:* Entry gom: **`647.95 - 661.50 cents`**

---

### G. 🤖 Dự Báo Future Chart AI (Simulation 5 Ngày)
*(Mã hợp đồng: **ZWU26 (September 2026)** | Điểm Bias Tổng Hợp: **+5.90**)*

| Ngày Giao Dịch | Phiên (Session) | Mở (Open) | Cao (High) | Thấp (Low) | Đóng (Close) | Thay đổi | Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mon 12/10** | Asia 07-11 | 672.75 | 684.00 | 667.25 | **672.00** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Mon 12/10** | Asia 11-15 | 672.00 | 679.50 | 666.00 | **671.50** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Mon 12/10** | London 15-19 | 671.50 | 685.25 | 656.75 | **673.50** | **+2.00¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | Pre-NY 19-21 | 673.50 | 686.75 | 665.25 | **674.75** | **+1.25¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | NY Open 21-23 | 674.75 | 691.25 | 664.25 | **679.25** | **+4.50¢** 🟢 | 🟢 BULL |
| **Mon 12/10** | NY Close 23-01 | 679.25 | 687.00 | 668.25 | **680.50** | **+1.25¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Asia 07-11 | 680.50 | 688.75 | 670.00 | **682.25** | **+1.75¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Asia 11-15 | 682.25 | 694.50 | 672.50 | **681.25** | **-1.00¢** 🔴 | 🔴 BEAR |
| **Tue 13/10** | London 15-19 | 681.25 | 691.75 | 666.50 | **683.50** | **+2.25¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | Pre-NY 19-21 | 683.50 | 694.00 | 677.25 | **684.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | NY Open 21-23 | 684.25 | 698.50 | 669.50 | **686.25** | **+2.00¢** 🟢 | 🟢 BULL |
| **Tue 13/10** | NY Close 23-01 | 686.25 | 692.75 | 679.50 | **686.50** | **+0.25¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | Asia 07-11 | 686.50 | 696.75 | 678.50 | **687.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | Asia 11-15 | 687.00 | 694.00 | 681.00 | **686.25** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Wed 14/10** | London 15-19 | 686.25 | 699.75 | 673.25 | **688.00** | **+1.75¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | Pre-NY 19-21 | 688.00 | 697.25 | 677.25 | **688.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 14/10** | NY Open 21-23 | 688.50 | 700.75 | 674.25 | **687.00** | **-1.50¢** 🔴 | 🔴 BEAR |
| **Wed 14/10** | NY Close 23-01 | 687.00 | 694.00 | 677.50 | **687.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | Asia 07-11 | 687.50 | 698.00 | 680.25 | **687.25** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Thu 15/10** | Asia 11-15 | 687.25 | 697.00 | 677.50 | **687.75** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | London 15-19 | 687.75 | 698.50 | 680.50 | **688.50** | **+0.75¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | Pre-NY 19-21 | 688.50 | 695.00 | 680.00 | **689.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | NY Open 21-23 | 689.00 | 700.00 | 677.25 | **692.50** | **+3.50¢** 🟢 | 🟢 BULL |
| **Thu 15/10** | NY Close 23-01 | 692.50 | 698.00 | 684.75 | **693.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | Asia 07-11 | 693.25 | 702.50 | 686.75 | **692.50** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Fri 16/10** | Asia 11-15 | 692.50 | 700.00 | 686.50 | **691.50** | **-1.00¢** 🔴 | 🔴 BEAR |
| **Fri 16/10** | London 15-19 | 691.50 | 698.50 | 678.00 | **692.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | Pre-NY 19-21 | 692.25 | 701.50 | 685.00 | **692.00** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 16/10** | NY Open 21-23 | 692.00 | 700.50 | 678.00 | **693.75** | **+1.75¢** 🟢 | 🟢 BULL |
| **Fri 16/10** | NY Close 23-01 | 693.75 | 700.00 | 687.25 | **693.00** | **-0.75¢** 🔴 | 🔴 BEAR |

**Kịch bản theo ngày:**
- **Mon 12/10:** USDA Crop Progress + Hấp Thụ Short-Covering — *USDA Crop Progress: G/E lúa mì duy trì 27%. LƯU Ý: Đà tăng tuần qua đã xả bớt phần lớn vị thế Short của Quỹ. Không nên kỳ vọng một cú Squeeze sốc mới, thị trường sẽ tăng chậm lại hoặc có nhịp Pullback chốt lời.*
- **Tue 13/10:** El Niño + Australia Planting Risk — *El Niño xác nhận tháng 6/2026 → dự báo hạn hán tại Australia mùa gieo hạt Jul-Sep. Lịch sử: El Niño + Australia hạn hán = giảm 15-20% sản lượng lúa mì Australia. Đây là yếu tố cung dài hạn cực kỳ bullish cho ZW Q4 2026.*
- **Wed 14/10:** Nga Khô Hạn + Consolidation — *Báo cáo vệ tinh xác nhận hạn hán cục bộ tại Krasnodar/Rostov (Nga) — khu vực sản xuất lúa mì chất lượng cao. Nga vẫn là nguồn cung lớn nhất thế giới, bất kỳ giảm sản lượng nào cũng tác động mạnh đến giá. Thị trường consolidate chờ Export Sales thứ Năm.*
- **Thu 15/10:** Export Sales + Egypt Tender - QUAN TRỌNG — *Export Sales lúa mì tuần 23-27/06: Kỳ vọng Egypt, Philippines và Bangladesh quay lại mua lúa mì Mỹ khi giá HRW cạnh tranh hơn so với Nga (Nga vừa tăng thuế xuất khẩu). Data ~20:30 ICT là catalyst lớn nhất tuần. G/E 27% đảm bảo supply tight dài hạn.*
- **Fri 16/10:** Quarterly Options Expiry — Chốt tuần — *Quarterly options expiry tạo biến động xung quanh các mức strike lớn (~610¢, ~620¢). Fund đóng một phần Long để book profit. Nhưng nền tảng cơ bản vẫn bullish: G/E 27%, El Niño Australia, Nga khô hạn — dự kiến tuần tiếp theo tiếp tục tăng.*


=====================================================================================

