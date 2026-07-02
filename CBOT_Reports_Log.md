# NHẬT KÝ BÁO CÁO PHÂN TÍCH HỆ THỐNG CBOT PRO V3 (ZC - ZW - ZS)
*Hệ thống phân tích tự động tích hợp Kỹ thuật H1/M15, Vĩ mô toàn cầu (Brent/DXY) và Nền tảng Nông nghiệp USDA*

Tài liệu được lưu trữ trực tiếp tại thư mục làm việc:
`c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\CBOT_Reports_Log.md`

---

# PHẦN I: THÔNG TIN TỔNG QUAN & VĨ MÔ

## 🌐 1. TỔNG QUAN VĨ MÔ TOÀN CẦU (MACRO INDICATORS OVERVIEW)
*Cập nhật tự động qua `macro_tracker.py` vào lúc 17:16 ICT ngày 02/07/2026*

| Chỉ số Vĩ mô | Mức giá hiện tại | Biến động 24h | Xu hướng & Đánh giá tác động đến Nông sản |
| :--- | :---: | :---: | :--- |
| **Dầu thô Brent (BZ=F)** | **$71.18 / thùng** | **-2.39%** | 📉 **Trung lập:** Giá dầu duy trì ở mức cao hỗ trợ mạnh mẽ cho biofuels như Ethanol (ZC) và Biodiesel (ZS). Chi phí sản xuất neo cao tạo mức sàn hỗ trợ giá. |
| **Chỉ số DXY (USD Index)** | **101.41** | **+0.22%** | 📉 **Trung lập - Tiêu cực (Sức ép xuất khẩu):** DXY neo cao khiến hàng Mỹ kém cạnh tranh hơn ở thị trường quốc tế, cản trở xuất khẩu ngắn hạn. |


## 💰 DÒNG TIỀN COT (SMART MONEY MATRIX)
*Cập nhật từ nguồn CFTC Public API (Ngày báo cáo chốt sổ: **2026-06-16**)*

### Bảng Dòng Tiền Managed Money

| Mã | Commodity | Net Position | Tuần Qua | Trạng Thái Matrix | Điểm Bias |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **ZC** | 002602 | **0** | **+0** | **NEUTRAL**<br>*Cho tin hieu ro rang.* | ⚪ **+0.0** |
| **ZW** | 001602 | **0** | **+0** | **NEUTRAL**<br>*Cho tin hieu ro rang.* | ⚪ **+0.0** |




### ✅ TƯƠNG QUAN VĨ MÔ ỔN ĐỊNH (NORMAL CORRELATION)
*   **Giá trị biến động 24h:** Dầu Brent: **`$71.18` (-2.39%)** | DXY: **`101.41` (+0.22%)** | Lúa mì CBOT: **`602.75¢` (+3.49%)**.
*   **Biện chứng liên thị trường:** Liên thị trường giao dịch ổn định, giá lúa mì bám sát các chỉ tiêu cung cầu cơ bản và không có hiện tượng bán tháo chéo quá mức từ nhóm năng lượng.
*   🚀 **Khuyến nghị chiến lược:** Tiếp tục duy trì kế hoạch giao dịch trong ngày (Intraday) và đánh biên (Swing) theo cản kỹ thuật đã hoạch định.


---

## 🌡️ 2. BẢN TIN THỜI TIẾT & MÙA VỤ TOÀN CẦU (WEATHER INTELLIGENCE REPORT)
*Cập nhật tự động lúc 17:16 ICT ngày 02/07/2026 — Nguồn: NOAA, USDA, BOM Australia*

### 🇺🇸 Thời tiết Nội địa Mỹ (US Domestic Weather)

| Vùng trồng trọt | Cây trồng chính | Diễn biến thời tiết | Tác động mùa vụ |
| :--- | :---: | :--- | :--- |
| **Midwest phía Đông** *(IL, IN, OH)* | 🌽🌱 Ngô/Đậu | Mưa lớn kéo dài ở phía Đông Corn Belt (Illinois, Ohio). | Vành đai phía Bắc vẫn khô hạn cục bộ |
| **Midwest phía Tây & Bắc** *(IA, MN, Dakotas)* | 🌽 Ngô | Trời nóng tại Midwest, mưa rải rác — Rủi ro: Khô hạn đe dọa nảy mầm -> Gom Long dài hạn (DCA) | Xác suất chuyển pha sang El Niño đạt 82% vào tháng 7. Hiện tại đang xuất hiện vùng khô hạn cục bộ ở rìa phía Bắc (Minnes... |
| **Southern Plains** *(KS, OK, TX)* | 🌾 Lúa mì đông | Mưa lớn bất ngờ xuất hiện tại vùng Southern Plains (Kansas, Oklahoma, Texas). | Mưa ngắn hạn -> Canh Short ngắn hạn / Gom Long dài hạn (DCA) |
| **Northern Plains** *(ND, SD, MT)* | 🌾 Lúa mì xuân | Lúa mì đông đã thu hoạch (25%), Xuân 95% gieo | Lúa mì xuân gieo trồng phát triển thuận lợi. Lúa mì đông đã trổ bông vượt trung bình. |

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

## 📌 3. DANH MỤC LỊCH SỬ BÁO CÁO (CẬP NHẬT PHIÊN CHỐT 02/07/2026)
*Thời gian đóng cửa phiên giao dịch được đồng bộ chính xác vào lúc **1:20 AM ICT ngày 02/07/2026***

| Ngày Báo Cáo (ICT) | Mã | Giá Chốt (Close) | Dự báo Chốt Phiên | Tín Hiệu H1 (EMA 21/50) | Volatility | Intraday Bias | Xem Chi Tiết |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **02/07/2026** | **ZC** | **424.75 ¢** | **425.45 ¢ (+0.70)** | 🐂 Bullish (422.29 > 419.73) | 0.50 cents | Rình mua (Long on dip) | [Xem Ngô (ZC)](#2-báo-cáo-mã-zc-ngô---phiên-chốt-02072026) |
| **02/07/2026** | **ZW** | **602.75 ¢** | **604.99 ¢ (+2.24)** | 🐂 Bullish (599.40 > 595.44) | 0.50 cents | Bán khống hồi (Short on rally) | [Xem Lúa mì (ZW)](#3-báo-cáo-mã-zw-lúa-mì---phiên-chốt-02072026) |
| **02/07/2026** 
---

# PHẦN II: TỔNG HỢP LỆNH & CHIẾN LƯỢC MÙA VỤ

## 🎯 1. TỔNG HỢP KHUYẾN NGHỊ HÀNH ĐỘNG THỰC CHIẾN (EXECUTIVE ACTION SUMMARY)
*Trang tổng hợp nhanh các lệnh và vị thế giao dịch cần thực hiện đón đầu cho cả 3 mã hàng hóa*

| Mã | Loại chiến lược | Điểm vào lệnh (Entry Zone) | Cắt lỗ (Stop Loss - SL) | Chốt lời (Take Profit - TP) | Vị thế chủ đạo & Ghi chú thực chiến |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZC** | **Long ngắn hạn (Intraday) (ZCU26)** | **423.00 - 422.29 cents (Canh mua vùng hỗ trợ)** | **404.11 cents (Dưới cản S2 + 1.5x ATR)** | TP1: `425.50 cents` \| TP2: `467.25 cents` | CANH LONG ngắn hạn tại vùng hỗ trợ kỹ thuật H1 khi giá điều chỉnh sâu. |
| **ZC** | **Long trung hạn (Swing) (ZCU26)** | **421.50 - 423.00 cents** | **404.83 cents (Chống quét SL tuyệt đối)** | **466.25 cents (Ăn trọn biên độ ngô ~10.5 giá)** | LỆNH LONG trung hạn ở hỗ trợ S2 Price Action cứng (biên dưới). |
| **ZC** | **Short trung hạn (Swing) (ZCU26)** | **425.50 - 427.00 cents** | **426.92 cents** | **407.25 cents** | LỆNH SHORT trung hạn ở kháng cự R2 Price Action (biên trên). |
| **ZC** | **Long dài hạn (DCA) (ZCZ26)** | **420.16 - 425.75 cents** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng thủ La Niña và tồn kho thấp kỷ lục. |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZW** | **Short ngắn hạn (Intraday) (ZWU26)** | **599.40 - 595.44 cents (Canh bán hồi kỹ thuật H1)** | **644.58 cents (Trên kháng cự R2 + 1.5x ATR)** | TP1: `601.50 cents` \| TP2: `574.00 cents` | LỆNH SHORT ngắn hạn thuận xu hướng khi hồi kỹ thuật H1. |
| **ZW** | **Long trung hạn (Swing) (ZWU26)** | **599.50 - 601.50 cents** | **571.61 cents** | **604.75 cents (Đón sóng hồi trung hạn ~14.5 giá)** | LỆNH LONG trung hạn ở hỗ trợ S1/S2 đón sóng hồi trung hạn ~14.5 giá. |
| **ZW** | **Short trung hạn (Swing) (ZWU26)** | **604.75 - 606.75 cents** | **607.14 cents** | **574.00 cents (Thuận xu hướng giảm ngắn hạn)** | LỆNH SHORT trung hạn thuận xu hướng ngắn hạn khi chạm kháng cự R1/R2. |
| **ZW** | **Long dài hạn (DCA) (ZWZ26)** | **581.75 - 590.50 cents** | Không áp dụng | Mục tiêu dài hạn | Canh mua DCA dài hạn quyết liệt (lệch pha cơ hội vĩ mô). |
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
| **ZC** | Gieo trồng | **97% đã gieo trồng** | 92% | 89% | **67% Good to Excellent** | Tiến độ nhanh -> Canh Short ngắn hạn - Trung bình 5 năm đạt 96%. Tiến độ hiện tại được cập nhật mới nhất. |
| **ZW** | Lúa đông | **Mỹ: 48% lúa đông đã thu hoạch** | 3% | 2% | **26% Good to Excellent** | Bắt đầu thu hoạch -> Canh Short ngắn hạn - Trung bình 5 năm đạt 6%. Báo cáo tiến độ thu hoạch mới nhất. |
| **ZW** | Lúa xuân | **Lúa mì đông đã thu hoạch (25%), Xuân 95% gieo** | 91% | 88% | Chưa xếp hạng | Tiến độ ổn định -> Canh Short ngắn hạn - Lúa mì xuân gieo trồng phát triển thuận lợi. Lúa mì đông đã trổ bông vượt trung bình. |

#### 2. Báo cáo Cung cầu & Tồn kho USDA (USDA WASDE)
| Mã nông sản | Thông số Tồn kho | Mỹ (US Ending Stocks) | Thế giới (Global) | Lần cập nhật tới | Tác động biện chứng WASDE |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **ZC** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | 2,122 triệu bu<br>**1,960 triệu bushels (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 312.3 triệu tấn<br>**281.22 triệu tấn (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 10/07/2026 lúc 23:00 (VN) | Tồn kho thấp nhất 12 năm -> Gom Long dài hạn (DCA) - Tồn kho ngô toàn cầu chạm mức thấp nhất 12 năm qua (kể từ niên vụ 2013/14). |
| **ZW** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | 2,122 triệu bu<br>**744 triệu bushels (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 312.3 triệu tấn<br>**275.42 triệu tấn (2026/27)**<br>*Chưa có dự báo (Đợi AI cập nhật trước kỳ báo cáo)* | 10/07/2026 lúc 23:00 (VN) | Cung toàn cầu giảm -> Gom Long dài hạn (DCA) - Giảm 4.2 triệu tấn so với niên vụ trước, tiếp tục thắt chặt cung cầu toàn cầu. |

#### 3. Báo cáo Bán hàng & Giao hàng Xuất khẩu (USDA Weekly Export Sales & Inspections)
| Mã nông sản | Báo cáo | Số liệu trước đó | Số liệu mới nhất | Dự báo kỳ tiếp theo | Lần cập nhật tới | Tác động biện chứng xuất khẩu |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Bán hàng & Giao hàng | Giao hàng (Inspections): 1,454,252 tấn (Tuần kết thúc Jun 22, 2026) | **Giao hàng (Inspections): 1,786,167 tấn (Tuần kết thúc Jun 29, 2026)** | 900,000 tấn (Dự báo tăng trưởng) | 06/07/2026 lúc 22:00 (VN) | Xuất khẩu ổn định -> Gom Long trung hạn - Báo cáo ngày 04/06 ghi nhận doanh số ròng 883,332 tấn ngô. Nhật Bản mua ròng lớn nhất với 336,300 tấn. Mặc dù doanh số giảm nhẹ 13% so với tuần trước, lượng giao hàng thực tế (exports) tăng 7% lên 1.72 triệu tấn. |
| **ZW** | Bán hàng & Giao hàng | Giao hàng (Inspections): 393,150 tấn (Tuần kết thúc Jun 22, 2026) | **Giao hàng (Inspections): 358,253 tấn (Tuần kết thúc Jun 29, 2026)** | 350,000 tấn (Dự kiến phục hồi) | 06/07/2026 lúc 22:00 (VN) | Xuất khẩu giảm cơ học -> Gom Long trung hạn - Tuần cuối niên vụ cũ ghi nhận mức âm ròng -642,239 tấn do các điều chỉnh hủy hàng/chuyển niên vụ. Tuy nhiên, doanh số niên vụ mới (2026/27) đạt mức rất cao là 838,500 tấn nhờ nhu cầu tăng mạnh trước lo ngại sụt giảm sản lượng. |

#### 4. Báo cáo Sản lượng Cây trồng & Đối thủ Nam Mỹ (USDA Crop Production & Competitors)
| Mã nông sản | Thu hoạch Mỹ / Vụ mùa | Sản lượng Đối thủ Nam Mỹ | Lần cập nhật tới | Tác động biện chứng cung cầu |
| :---: | :--- | :--- | :---: | :--- |
| **ZC** | Thu hoạch: Mỹ: 0% | Argentina: 66% (2/3 tiến độ) | Brazil & Argentina (Khô hạn Safrinha Brazil; Argentina đạt 64M tấn) | Liên tục (Cập nhật hàng ngày) | Brazil vụ 2 khô hạn -> Gom Long trung hạn - Argentina: Dự báo sản lượng đạt kỷ lục 64 triệu tấn. Brazil: Vụ 1 kết thúc; ngô vụ 2 (Safrinha) đang chịu khô hạn cục bộ tại các bang phía Nam gây lo ngại sụt giảm năng suất. |
| **ZW** | Thu hoạch: Mỹ: 48% lúa đông đã thu hoạch | Úc & Argentina (Úc giảm 41% sản lượng, Arg giảm 25%) | Liên tục (Cập nhật hàng tuần) | Thiệt hại kép -> Gom Long dài hạn (DCA) - Úc: Diện tích gieo trồng dự kiến giảm sâu 20.4% xuống còn 9.8 triệu ha. Sản lượng dự kiến giảm mạnh 41% xuống 21.3 triệu tấn do hạn hán đầu vụ ở phía Bắc NSW/Nam Queensland. Argentina: Đã gieo trồng được 14.2% diện tích. Sản lượng dự kiến đạt 20.7 triệu tấn (giảm 25% so với mức kỷ lục niên vụ trước) do nông dân lo ngại chi phí phân bón cao và rủi ro bệnh dịch từ El Niño. |

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

## 🌽 BÁO CÁO MÃ ZC (NGÔ) — HỒ SƠ ĐỘC LẬP | PHIÊN CHỐT 02/07/2026

### A. Tóm tắt Nhanh & Bias Tổng Hợp Hôm Nay

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | La Niña rủi ro vĩ mô | Định hướng gom DCA dài hạn |
| **Trung hạn** | ↕️ **Đi ngang (Sideways)** | Đi ngang tích lũy (Sideways Accumulation) | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | 🐂 **Tăng (Bullish)** | EMA_21 H1 > EMA_50 H1 (Hội tụ động lượng tăng) | Canh vào lệnh ngắn hạn (Intraday) |

*   **Giá Chốt Phiên (Close):** 424.75 cents | **Dự báo Chốt Phiên:** **`425.45 cents`** (+0.70).
*   **Thanh khoản phiên chốt:** Volume: **`14,401`** (Chênh lệch: **`-197,596`**) | OI: **`651,628`** (Chênh lệch: **`+0`**)
*   **Mô hình nến H1:** **`Không phát hiện mô hình nến đặc biệt`**
*   **Dòng tiền (Volume + OI):** **`Tăng yếu / Rủi ro đảo chiều (Short Covering Rally)`**
*   **Đánh giá xu hướng kết hợp:** 📈 **TÍCH LŨY TÍCH CỰC (Accumulation):** Nến đi ngang nhưng dòng tiền âm thầm gia tăng (OI tăng), báo hiệu chuẩn bị có nhịp bứt phá tăng.

---

### B. Bối Cảnh Vĩ Mô & Dòng Tiền COT (Smart Money Matrix)
*(Dữ liệu chung đồng bộ tự động từ `macro_tracker.py`)*


| Chỉ số | Giá trị Hiện tại | Biến động 24h | Tác động Biện chứng lên Ngô (ZC) |
| :--- | :---: | :---: | :--- |
| **Dầu Brent** | **$71.18** | **-2.39%** | Giá dầu Giảm làm giảm biên lợi nhuận pha chế Ethanol, tạo sức ép lên nhu cầu ngô. |
| **USD Index** | **101.41** | **+0.22%** | DXY Tăng làm giảm sức cạnh tranh xuất khẩu của ngô Mỹ so với Brazil/Argentina. |


> *[Lỗi] Không lấy được dữ liệu CFTC COT API cho mã này.*


---

### C. Phân Tích Kỹ Thuật H1/M15 (HĐ ZCU26)
*   **Chỉ báo EMA H1:** `EMA_21` (422.29) > `EMA_50` (419.73).
*   **Động lượng & Dao động:** RSI (14) = **`66.16`** | ATR (14) = **`1.42`** cents | Volatility = **`0.50 cents`**.
*   **Vùng cản Pivot:** Hỗ trợ S1: **`423.00`** | S2: **`406.25`** || Kháng cự R1: **`425.50`** | R2: **`467.25`**

---

### D. Cơ Bản, Tồn Kho USDA & Xuất Khẩu (Export Sales)


| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | 1,960 triệu bushels (2026/27) | Tồn kho thấp nhất 12 năm -> Gom Long dài hạn (DCA) |
| **Tồn kho Thế giới** | 281.22 triệu tấn (2026/27) | Tồn kho ngô toàn cầu chạm mức thấp nhất 12 năm qua (kể từ niên vụ 2013/14). |
| **Tiến độ Gieo trồng** | 97% đã gieo trồng | Tiến độ nhanh -> Canh Short ngắn hạn |
| **Chất lượng G/E** | 67% Good to Excellent | Phản ánh rủi ro thời tiết Midwest |
| **Đối thủ (Brazil)** | Brazil & Argentina | Brazil vụ 2 khô hạn -> Gom Long trung hạn |

*   **Export Sales (Báo Cáo Mới Nhất):** NoData

---

### E. Thời Tiết & Mùa Vụ (Tự động từ Open-Meteo / NOAA)
*   **Trạng thái ENSO (NOAA):** El Niño Advisory


---

### F. Khuyến Nghị Giao Dịch Chuyên Sâu (ZC)

*   🚀 **Long ngắn hạn (Intraday) (Ngắn hạn - HĐ ZCU26):**
    *   *Chiến lược:* Giao dịch chớp nhoáng theo biên độ H1.
    *   *Thiết lập:* Entry: **`423.00 - 422.29 cents (Canh mua vùng hỗ trợ)`** | SL: **`404.11 cents (Dưới cản S2 + 1.5x ATR)`** | TP: `425.50 cents` / `467.25 cents`.
*   🚀 **Trung hạn (Swing Trades - HĐ ZCU26):**
    *   *Long:* Entry: **`421.50 - 423.00 cents`** | SL: **`404.83 cents (Chống quét SL tuyệt đối)`** | TP: **`466.25 cents (Ăn trọn biên độ ngô ~10.5 giá)`**.
    *   *Short:* Entry: **`425.50 - 427.00 cents`** | SL: **`426.92 cents`** | TP: **`407.25 cents`**.
*   🚀 **Long dài hạn (DCA) (Dài hạn - HĐ ZCZ26):**
    *   *Chiến lược:* Mua tích lũy phòng thủ rủi ro địa chính trị và thời tiết vĩ mô.
    *   *Thiết lập:* Entry gom: **`420.16 - 425.75 cents`**

---

### G. 🤖 Dự Báo Future Chart AI (Simulation 5 Ngày)
*(Mã hợp đồng: **ZCU26 (September 2026)** | Điểm Bias Tổng Hợp: **+3.60**)*

| Ngày Giao Dịch | Phiên (Session) | Mở (Open) | Cao (High) | Thấp (Low) | Đóng (Close) | Thay đổi | Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mon 29/06** | Asia 07-11 | 424.75 | 428.50 | 421.50 | **425.00** | **+0.25¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | Asia 11-15 | 425.00 | 427.75 | 421.25 | **424.50** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Mon 29/06** | London 15-19 | 424.50 | 427.50 | 420.50 | **425.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | Pre-NY 19-21 | 425.25 | 429.75 | 420.25 | **426.00** | **+0.75¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | NY Open 21-23 | 426.00 | 431.50 | 419.75 | **428.25** | **+2.25¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | NY Close 23-01 | 428.25 | 431.25 | 424.00 | **428.50** | **+0.25¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Asia 07-11 | 428.50 | 431.75 | 422.00 | **429.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Asia 11-15 | 429.25 | 432.25 | 424.75 | **428.75** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Tue 30/06** | London 15-19 | 428.75 | 432.75 | 423.00 | **429.25** | **+0.50¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Pre-NY 19-21 | 429.25 | 431.75 | 426.00 | **429.75** | **+0.50¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | NY Open 21-23 | 429.75 | 433.25 | 423.75 | **430.75** | **+1.00¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | NY Close 23-01 | 430.75 | 433.50 | 428.25 | **430.75** | **+0.00¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | Asia 07-11 | 430.75 | 433.50 | 428.25 | **430.25** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Wed 01/07** | Asia 11-15 | 430.25 | 433.25 | 427.00 | **430.00** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Wed 01/07** | London 15-19 | 430.00 | 434.00 | 424.75 | **430.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | Pre-NY 19-21 | 430.50 | 435.25 | 423.50 | **432.50** | **+2.00¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | NY Open 21-23 | 432.50 | 440.50 | 425.50 | **434.00** | **+1.50¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | NY Close 23-01 | 434.00 | 438.50 | 429.75 | **433.50** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Thu 02/07** | Asia 07-11 | 433.50 | 435.75 | 430.75 | **433.25** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Thu 02/07** | Asia 11-15 | 433.25 | 435.25 | 428.75 | **433.50** | **+0.25¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | London 15-19 | 433.50 | 437.25 | 430.75 | **434.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | Pre-NY 19-21 | 434.00 | 437.00 | 429.50 | **434.25** | **+0.25¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | NY Open 21-23 | 434.25 | 438.50 | 431.00 | **435.00** | **+0.75¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | NY Close 23-01 | 435.00 | 438.50 | 432.75 | **435.00** | **+0.00¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | Asia 07-11 | 435.00 | 438.75 | 431.50 | **434.75** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 03/07** | Asia 11-15 | 434.75 | 438.25 | 431.50 | **434.50** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 03/07** | London 15-19 | 434.50 | 437.50 | 431.75 | **434.75** | **+0.25¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | Pre-NY 19-21 | 434.75 | 437.75 | 432.00 | **434.75** | **+0.00¢** 🟢 | 🔴 BEAR |
| **Fri 03/07** | NY Open 21-23 | 434.75 | 438.75 | 431.25 | **435.25** | **+0.50¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | NY Close 23-01 | 435.25 | 439.25 | 433.50 | **435.00** | **-0.25¢** 🔴 | 🔴 BEAR |

**Kịch bản theo ngày:**
- **Mon 29/06:** USDA G/E 68% + Silking Window Bắt Đầu — *USDA Crop Progress: G/E Ngô 68% (ổn định). QUAN TRỌNG HƠN: Silking (thụ phấn) bắt đầu tại Iowa/Illinois — đây là giai đoạn NHẠY CẢM NHẤT với nhiệt độ. Mỗi ngày >35°C trong tuần này có thể phá hủy 2-5% năng suất. Pollination Risk Premium được xây dựng từ phiên NY.*
- **Tue 30/06:** Phản ứng USDA Ngô — *Thị trường tiêu hóa USDA Crop Progress. Pollination Risk Premium duy trì lực mua. Giá kiểm tra vùng R1 422.00.*
- **Wed 01/07:** EIA Ethanol + 7-Day Heat Forecast Update — *EIA Ethanol Production (thứ 4): Kỳ vọng ~1.05 triệu thùng/ngày (tốt hơn 1.04 tuần trước). QUAN TRỌNG HƠN: 7-Day weather model GFS/Euro cập nhật — nếu dự báo nhiệt độ >35°C tại Iowa trong 5-7 ngày tới trong giai đoạn Silking peak → Pollination Risk Premium tăng đột biến 5-10¢. Đây là phiên biến động nhất tuần cho ZC.*
- **Thu 02/07:** Export Sales Weekly - Trung Bình — *Export Sales ngô tuần này ổn định. Brazil vẫn cạnh tranh nhưng Pollination Risk Premium hỗ trợ floor giá. Thị trường chờ xác nhận từ weather model.*
- **Fri 03/07:** Đóng vị thế cuối tuần — *Ngô không có catalyst mới cuối tuần. Giá dao động hẹp. Weather outlook tuần tới sẽ quyết định hướng đi tiếp theo của Pollination Risk Premium.*


=====================================================================================


## 🌾 BÁO CÁO MÃ ZW (LÚA MÌ) — HỒ SƠ ĐỘC LẬP | PHIÊN CHỐT 02/07/2026

### A. Tóm tắt Nhanh & Bias Tổng Hợp Hôm Nay

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | La Niña rủi ro vĩ mô | Định hướng gom DCA dài hạn |
| **Trung hạn** | 🐻 **Giảm (Bearish)** | Giảm điều chỉnh tích lũy (Bearish Correction & Consolidation) | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | 🐂 **Tăng (Bullish)** | EMA_21 H1 > EMA_50 H1 (Hội tụ động lượng tăng) | Canh vào lệnh ngắn hạn (Intraday) |

*   **Giá Chốt Phiên (Close):** 602.75 cents | **Dự báo Chốt Phiên:** **`604.99 cents`** (+2.24).
*   **Thanh khoản phiên chốt:** Volume: **`9,403`** (Chênh lệch: **`-103,534`**) | OI: **`215,998`** (Chênh lệch: **`+0`**)
*   **Mô hình nến H1:** **`Không phát hiện mô hình nến đặc biệt`**
*   **Dòng tiền (Volume + OI):** **`Tăng yếu / Rủi ro đảo chiều (Short Covering Rally)`**
*   **Đánh giá xu hướng kết hợp:** 📈 **TÍCH LŨY TÍCH CỰC (Accumulation):** Nến đi ngang nhưng dòng tiền âm thầm gia tăng (OI tăng), báo hiệu chuẩn bị có nhịp bứt phá tăng.

---

### B. Bối Cảnh Vĩ Mô & Dòng Tiền COT (Smart Money Matrix)
*(Dữ liệu chung đồng bộ tự động từ `macro_tracker.py`)*


| Chỉ số | Giá trị Hiện tại | Biến động 24h | Tác động Biện chứng lên Lúa Mì (ZW) |
| :--- | :---: | :---: | :--- |
| **Dầu Brent** | **$71.18** | **-2.39%** | Giá dầu Giảm giảm bớt premium rủi ro địa chính trị, tạo áp lực chốt lời lúa mì. |
| **USD Index** | **101.41** | **+0.22%** | DXY Tăng khiến lúa mì Mỹ đắt đỏ hơn đối với các khách hàng truyền thống như Ai Cập/Châu Á. |


> *[Lỗi] Không lấy được dữ liệu CFTC COT API cho mã này.*


---

### C. Phân Tích Kỹ Thuật H1/M15 (HĐ ZWU26)
*   **Chỉ báo EMA H1:** `EMA_21` (599.40) > `EMA_50` (595.44).
*   **Động lượng & Dao động:** RSI (14) = **`63.14`** | ATR (14) = **`2.39`** cents | Volatility = **`0.50 cents`**.
*   **Vùng cản Pivot:** Hỗ trợ S1: **`601.50`** | S2: **`574.00`** || Kháng cự R1: **`604.75`** | R2: **`641.00`**

---

### D. Cơ Bản, Tồn Kho USDA & Xuất Khẩu (Export Sales)


| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | 744 triệu bushels (2026/27) | Cung toàn cầu giảm -> Gom Long dài hạn (DCA) |
| **Tiến độ Thu hoạch** | Mỹ: 48% lúa đông đã thu hoạch | Bắt đầu thu hoạch -> Canh Short ngắn hạn |
| **Chất lượng G/E** | 26% Good to Excellent | Cực kỳ thấp, rủi ro thiếu hụt chất lượng cao |
| **Đối thủ (Australia)** | Hạn hán El Nino đe dọa mùa màng, sản lượng có thể giảm mạnh | Tác động cung cầu Châu Á |
| **Đối thủ (Argentina)**| Đã gieo trồng 14.2% diện tích lúa mì. Sản lượng dự kiến giảm 25% do chi phí phân bón cao và rủi ro El Niño. | Áp lực nguồn cung Nam Bán Cầu |

*   **Export Sales (Báo Cáo Mới Nhất):** NoData

---

### E. Thời Tiết & Mùa Vụ (Tự động từ Open-Meteo / NOAA)
*   **Trạng thái ENSO (NOAA):** El Niño Advisory


---

### F. Khuyến Nghị Giao Dịch Chuyên Sâu (ZW)

*   🚀 **Short ngắn hạn (Intraday) (Ngắn hạn - HĐ ZWU26):**
    *   *Chiến lược:* Giao dịch chớp nhoáng theo biên độ H1.
    *   *Thiết lập:* Entry: **`599.40 - 595.44 cents (Canh bán hồi kỹ thuật H1)`** | SL: **`644.58 cents (Trên kháng cự R2 + 1.5x ATR)`** | TP: `601.50 cents` / `574.00 cents`.
*   🚀 **Trung hạn (Swing Trades - HĐ ZWU26):**
    *   *Long:* Entry: **`599.50 - 601.50 cents`** | SL: **`571.61 cents`** | TP: **`604.75 cents (Đón sóng hồi trung hạn ~14.5 giá)`**.
    *   *Short:* Entry: **`604.75 - 606.75 cents`** | SL: **`607.14 cents`** | TP: **`574.00 cents (Thuận xu hướng giảm ngắn hạn)`**.
*   🚀 **Long dài hạn (DCA) (Dài hạn - HĐ ZWZ26):**
    *   *Chiến lược:* Mua tích lũy phòng thủ rủi ro địa chính trị và thời tiết vĩ mô.
    *   *Thiết lập:* Entry gom: **`581.75 - 590.50 cents`**

---

### G. 🤖 Dự Báo Future Chart AI (Simulation 5 Ngày)
*(Mã hợp đồng: **ZWU26 (September 2026)** | Điểm Bias Tổng Hợp: **+5.90**)*

| Ngày Giao Dịch | Phiên (Session) | Mở (Open) | Cao (High) | Thấp (Low) | Đóng (Close) | Thay đổi | Bias |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mon 29/06** | Asia 07-11 | 602.75 | 614.00 | 597.25 | **602.00** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Mon 29/06** | Asia 11-15 | 602.00 | 609.50 | 596.00 | **601.50** | **-0.50¢** 🔴 | 🔴 BEAR |
| **Mon 29/06** | London 15-19 | 601.50 | 615.25 | 586.75 | **603.50** | **+2.00¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | Pre-NY 19-21 | 603.50 | 616.75 | 595.25 | **604.75** | **+1.25¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | NY Open 21-23 | 604.75 | 621.25 | 594.25 | **609.25** | **+4.50¢** 🟢 | 🟢 BULL |
| **Mon 29/06** | NY Close 23-01 | 609.25 | 617.00 | 598.25 | **610.50** | **+1.25¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Asia 07-11 | 610.50 | 618.75 | 600.00 | **612.25** | **+1.75¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Asia 11-15 | 612.25 | 624.50 | 602.50 | **611.25** | **-1.00¢** 🔴 | 🔴 BEAR |
| **Tue 30/06** | London 15-19 | 611.25 | 621.75 | 596.50 | **613.50** | **+2.25¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | Pre-NY 19-21 | 613.50 | 624.00 | 607.25 | **614.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | NY Open 21-23 | 614.25 | 628.50 | 599.50 | **616.25** | **+2.00¢** 🟢 | 🟢 BULL |
| **Tue 30/06** | NY Close 23-01 | 616.25 | 622.75 | 609.50 | **616.50** | **+0.25¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | Asia 07-11 | 616.50 | 626.75 | 608.50 | **617.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | Asia 11-15 | 617.00 | 624.00 | 611.00 | **616.25** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Wed 01/07** | London 15-19 | 616.25 | 629.75 | 603.25 | **618.00** | **+1.75¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | Pre-NY 19-21 | 618.00 | 627.25 | 607.25 | **618.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Wed 01/07** | NY Open 21-23 | 618.50 | 630.75 | 604.25 | **617.00** | **-1.50¢** 🔴 | 🔴 BEAR |
| **Wed 01/07** | NY Close 23-01 | 617.00 | 624.00 | 607.50 | **617.50** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | Asia 07-11 | 617.50 | 628.00 | 610.25 | **617.25** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Thu 02/07** | Asia 11-15 | 617.25 | 627.00 | 607.50 | **617.75** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | London 15-19 | 617.75 | 628.50 | 610.50 | **618.50** | **+0.75¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | Pre-NY 19-21 | 618.50 | 625.00 | 610.00 | **619.00** | **+0.50¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | NY Open 21-23 | 619.00 | 630.00 | 607.25 | **622.50** | **+3.50¢** 🟢 | 🟢 BULL |
| **Thu 02/07** | NY Close 23-01 | 622.50 | 628.00 | 614.75 | **623.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | Asia 07-11 | 623.25 | 632.50 | 616.75 | **622.50** | **-0.75¢** 🔴 | 🔴 BEAR |
| **Fri 03/07** | Asia 11-15 | 622.50 | 630.00 | 616.50 | **621.50** | **-1.00¢** 🔴 | 🔴 BEAR |
| **Fri 03/07** | London 15-19 | 621.50 | 628.50 | 608.00 | **622.25** | **+0.75¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | Pre-NY 19-21 | 622.25 | 631.50 | 615.00 | **622.00** | **-0.25¢** 🔴 | 🔴 BEAR |
| **Fri 03/07** | NY Open 21-23 | 622.00 | 630.50 | 608.00 | **623.75** | **+1.75¢** 🟢 | 🟢 BULL |
| **Fri 03/07** | NY Close 23-01 | 623.75 | 630.00 | 617.25 | **623.00** | **-0.75¢** 🔴 | 🔴 BEAR |

**Kịch bản theo ngày:**
- **Mon 29/06:** USDA Crop Progress + Hấp Thụ Short-Covering — *USDA Crop Progress: G/E lúa mì duy trì 27%. LƯU Ý: Đà tăng tuần qua đã xả bớt phần lớn vị thế Short của Quỹ. Không nên kỳ vọng một cú Squeeze sốc mới, thị trường sẽ tăng chậm lại hoặc có nhịp Pullback chốt lời.*
- **Tue 30/06:** El Niño + Australia Planting Risk — *El Niño xác nhận tháng 6/2026 → dự báo hạn hán tại Australia mùa gieo hạt Jul-Sep. Lịch sử: El Niño + Australia hạn hán = giảm 15-20% sản lượng lúa mì Australia. Đây là yếu tố cung dài hạn cực kỳ bullish cho ZW Q4 2026.*
- **Wed 01/07:** Nga Khô Hạn + Consolidation — *Báo cáo vệ tinh xác nhận hạn hán cục bộ tại Krasnodar/Rostov (Nga) — khu vực sản xuất lúa mì chất lượng cao. Nga vẫn là nguồn cung lớn nhất thế giới, bất kỳ giảm sản lượng nào cũng tác động mạnh đến giá. Thị trường consolidate chờ Export Sales thứ Năm.*
- **Thu 02/07:** Export Sales + Egypt Tender - QUAN TRỌNG — *Export Sales lúa mì tuần 23-27/06: Kỳ vọng Egypt, Philippines và Bangladesh quay lại mua lúa mì Mỹ khi giá HRW cạnh tranh hơn so với Nga (Nga vừa tăng thuế xuất khẩu). Data ~20:30 ICT là catalyst lớn nhất tuần. G/E 27% đảm bảo supply tight dài hạn.*
- **Fri 03/07:** Quarterly Options Expiry — Chốt tuần — *Quarterly options expiry tạo biến động xung quanh các mức strike lớn (~610¢, ~620¢). Fund đóng một phần Long để book profit. Nhưng nền tảng cơ bản vẫn bullish: G/E 27%, El Niño Australia, Nga khô hạn — dự kiến tuần tiếp theo tiếp tục tăng.*


=====================================================================================

