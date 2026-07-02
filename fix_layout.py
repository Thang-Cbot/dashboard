import os
import re

file_path = r"c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\run_pro_plus.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to capture everything from report_content = f"""... down to report_content += mua_vu_report
pattern = re.compile(r'    # 6\. Thiết kế tệp báo cáo tổng hợp\n    report_content = f"""# NHẬT KÝ BÁO CÁO PHÂN TÍCH.*?    report_content \+= mua_vu_report', re.DOTALL)

new_text = r'''    # 6. Thiết kế tệp báo cáo tổng hợp
    report_content = f"""# NHẬT KÝ BÁO CÁO PHÂN TÍCH HỆ THỐNG CBOT PRO V3 (ZC - ZW - ZS)
*Hệ thống phân tích tự động tích hợp Kỹ thuật H1/M15, Vĩ mô toàn cầu (Brent/DXY) và Nền tảng Nông nghiệp USDA*

Tài liệu được lưu trữ trực tiếp tại thư mục làm việc:
`c:\\Users\\Admin\\OneDrive - w2kfp\\Thang_Docs\\Dau tu thu dong\\hang hoa tai sinh\\Antigravity\\Cbot\\CBOT_Reports_Log.md`

---

# PHẦN I: THÔNG TIN TỔNG QUAN & VĨ MÔ

## 🌐 1. TỔNG QUAN VĨ MÔ TOÀN CẦU (MACRO INDICATORS OVERVIEW)
*Cập nhật tự động qua `macro_tracker.py` vào lúc {time_str} ICT ngày {date_str}*

| Chỉ số Vĩ mô | Mức giá hiện tại | Biến động 24h | Xu hướng & Đánh giá tác động đến Nông sản |
| :--- | :---: | :---: | :--- |
| **Dầu thô Brent (BZ=F)** | **${brent_price:.2f} / thùng** | **{brent_pct:+.2f}%** | {'📈 **Tích cực (Bullish):**' if brent_price > 90 else '📉 **Trung lập:**'} Giá dầu duy trì ở mức cao hỗ trợ mạnh mẽ cho biofuels như Ethanol (ZC) và Biodiesel (ZS). Chi phí sản xuất neo cao tạo mức sàn hỗ trợ giá. |
| **Chỉ số DXY (USD Index)** | **{dxy_price:.2f}** | **{dxy_pct:+.2f}%** | {'📉 **Trung lập - Tiêu cực (Sức ép xuất khẩu):**' if dxy_price > 98 else '📈 **Thuận lợi:**'} DXY neo cao khiến hàng Mỹ kém cạnh tranh hơn ở thị trường quốc tế, cản trở xuất khẩu ngắn hạn. |

{cot_alert}

{divergence_alert}

---

## 🌡️ 2. BẢN TIN THỜI TIẾT & MÙA VỤ TOÀN CẦU (WEATHER INTELLIGENCE REPORT)
*Cập nhật tự động lúc {time_str} ICT ngày {date_str} — Nguồn: NOAA, USDA, BOM Australia*

### 🇺🇸 Thời tiết Nội địa Mỹ (US Domestic Weather)

| Vùng trồng trọt | Cây trồng chính | Diễn biến thời tiết | Tác động mùa vụ |
| :--- | :---: | :--- | :--- |
| **Midwest phía Đông** *(IL, IN, OH)* | 🌽🌱 Ngô/Đậu | {fund['ZC']['short_term_weather']} | {fund['ZC']['weather']['forecast']} |
| **Midwest phía Tây & Bắc** *(IA, MN, Dakotas)* | 🌽 Ngô | {fund['ZC']['weather']['latest']} — Rủi ro: {fund['ZC']['weather']['action']} | {fund['ZC']['weather']['logic'][:120]}... |
| **Southern Plains** *(KS, OK, TX)* | 🌾 Lúa mì đông | {fund['ZW']['short_term_weather']} | {fund['ZW']['weather']['action']} |
| **Northern Plains** *(ND, SD, MT)* | 🌾 Lúa mì xuân | {fund['ZW']['us_planting']['latest']} | {fund['ZW']['us_planting']['logic']} |

### 🌍 Thời tiết Đối thủ Cạnh tranh & Liên Thị trường (Global Competitor Weather)

| Khu vực | Mã liên quan | Diễn biến thời tiết | Tác động cung cầu toàn cầu |
| :--- | :---: | :--- | :--- |
| **🇧🇷 Brazil (Safrinha)** | ZC | {fund['ZC'].get('competitor_weather', dict()).get('brazil_safrinha', 'Chưa cập nhật')} | Hỗ trợ giá ngô Mỹ nếu năng suất Safrinha giảm. |
| **🇦🇷 Argentina (Ngô)** | ZC | {fund['ZC'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Áp lực cung ngắn hạn đang giảm dần. |
| **🇦🇺 Australia** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('australia', 'Chưa cập nhật')} | Bullish dài hạn cho lúa mì toàn cầu. |
| **🇦🇷 Argentina (Lúa mì)** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Nguồn cung Nam Mỹ thắt chặt. |
| **🇷🇺🇪🇺 Black Sea & EU** | ZW | {fund['ZW'].get('competitor_weather', dict()).get('black_sea_eu', 'Chưa cập nhật')} | Ảnh hưởng cạnh tranh xuất khẩu. |
| **🇧🇷 Brazil (Đậu tương)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('brazil', 'Chưa cập nhật')} | Áp lực cung từ vụ kỷ lục Brazil. |
| **🇦🇷 Argentina (Đậu tương)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('argentina', 'Chưa cập nhật')} | Áp lực thu hoạch sắp qua đỉnh. |
| **🇨🇳 Trung Quốc (Cầu)** | ZS | {fund['ZS'].get('competitor_weather', dict()).get('china', 'Chưa cập nhật')} | Bệ đỡ nhu cầu vững chắc. |

### 🌊 Trạng thái ENSO (El Niño / La Niña)
*   **Trạng thái hiện tại:** {fund['ZC']['weather_long_term']['latest']}
*   **Dự báo:** {fund['ZC']['weather_long_term']['forecast']}
*   **Tác động:** {fund['ZC']['weather_long_term']['action']}

---

## 📌 3. DANH MỤC LỊCH SỬ BÁO CÁO (CẬP NHẬT PHIÊN CHỐT {date_str})
*Thời gian đóng cửa phiên giao dịch được đồng bộ chính xác vào lúc **1:20 AM ICT ngày {date_str}***

| Ngày Báo Cáo (ICT) | Mã | Giá Chốt (Close) | Dự báo Chốt Phiên | Tín Hiệu H1 (EMA 21/50) | Volatility | Intraday Bias | Xem Chi Tiết |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **{date_str}** | **ZC** | **{zc['close']:.2f} ¢** | **{zc_pred_close:.2f} ¢ ({zc_pred_chg:+.2f})** | {'🐂 Bullish' if zc['signal'] == 'Bullish' else '🐻 Bearish'} ({zc['ema_21']:.2f} {'<' if zc['ema_21'] < zc['ema_50'] else '>'} {zc['ema_50']:.2f}) | {zc['volatility']:.2f} cents | Rình mua (Long on dip) | [Xem Ngô (ZC)](#2-báo-cáo-mã-zc-ngô---phiên-chốt-{date_str.replace('/', '')}) |
| **{date_str}** | **ZW** | **{zw['close']:.2f} ¢** | **{zw_pred_close:.2f} ¢ ({zw_pred_chg:+.2f})** | {'🐂 Bullish' if zw['signal'] == 'Bullish' else '🐻 Bearish'} ({zw['ema_21']:.2f} {'<' if zw['ema_21'] < zw['ema_50'] else '>'} {zw['ema_50']:.2f}) | {zw['volatility']:.2f} cents | Bán khống hồi (Short on rally) | [Xem Lúa mì (ZW)](#3-báo-cáo-mã-zw-lúa-mì---phiên-chốt-{date_str.replace('/', '')}) |
| **{date_str}** | **ZS** | **{zs['close']:.2f} ¢** | **{zs_pred_close:.2f} ¢ ({zs_pred_chg:+.2f})** | {'🐂 Bullish' if zs['signal'] == 'Bullish' else '🐻 Bearish'} ({zs['ema_21']:.2f} {'<' if zs['ema_21'] < zs['ema_50'] else '>'} {zs['ema_50']:.2f}) | {zs['volatility']:.2f} cents | Mua đuổi (Buy on pullback) | [Xem Đậu tương (ZS)](#4-báo-cáo-mã-zs-đậu-tương---phiên-chốt-{date_str.replace('/', '')}) |

---

# PHẦN II: TỔNG HỢP LỆNH & CHIẾN LƯỢC MÙA VỤ

## 🎯 1. TỔNG HỢP KHUYẾN NGHỊ HÀNH ĐỘNG THỰC CHIẾN (EXECUTIVE ACTION SUMMARY)
*Trang tổng hợp nhanh các lệnh và vị thế giao dịch cần thực hiện đón đầu cho cả 3 mã hàng hóa*

| Mã | Loại chiến lược | Điểm vào lệnh (Entry Zone) | Cắt lỗ (Stop Loss - SL) | Chốt lời (Take Profit - TP) | Vị thế chủ đạo & Ghi chú thực chiến |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZC** | **{zc_intra_label} ({zc_act_code})** | **{zc_intra_entry}** | **{zc_intra_sl}** | TP1: `{zc_intra_tp1}` \\| TP2: `{zc_intra_tp2}` | CANH LONG ngắn hạn tại vùng hỗ trợ kỹ thuật H1 khi giá điều chỉnh sâu. |
| **ZC** | **{zc_swing_long_label} ({zc_sw_code})** | **{zc_swing_long_entry}** | **{zc_swing_long_sl}** | **{zc_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ S2 Price Action cứng (biên dưới). |
| **ZC** | **{zc_swing_short_label} ({zc_sw_code})** | **{zc_swing_short_entry}** | **{zc_swing_short_sl}** | **{zc_swing_short_tp}** | LỆNH SHORT trung hạn ở kháng cự R2 Price Action (biên trên). |
| **ZC** | **{zc_dca_label} ({zc_dca_code})** | **{zc_dca}** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng thủ La Niña và tồn kho thấp kỷ lục. |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZW** | **{zw_intra_label} ({zw_act_code})** | **{zw_intra_entry}** | **{zw_intra_sl}** | TP1: `{zw_intra_tp1}` \\| TP2: `{zw_intra_tp2}` | LỆNH SHORT ngắn hạn thuận xu hướng khi hồi kỹ thuật H1. |
| **ZW** | **{zw_swing_long_label} ({zw_sw_code})** | **{zw_swing_long_entry}** | **{zw_swing_long_sl}** | **{zw_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ S1/S2 đón sóng hồi trung hạn ~14.5 giá. |
| **ZW** | **{zw_swing_short_label} ({zw_sw_code})** | **{zw_swing_short_entry}** | **{zw_swing_short_sl}** | **{zw_swing_short_tp}** | LỆNH SHORT trung hạn thuận xu hướng ngắn hạn khi chạm kháng cự R1/R2. |
| **ZW** | **{zw_dca_label} ({zw_dca_code})** | **{zw_dca}** | Không áp dụng | Mục tiêu dài hạn | Canh mua DCA dài hạn quyết liệt (lệch pha cơ hội vĩ mô). |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **ZS** | **{zs_intra_label} ({zs_act_code})** | **{zs_intra_entry}** | **{zs_intra_sl}** | TP1: `{zs_intra_tp1}` \\| TP2: `{zs_intra_tp2}` | CANH LONG ngắn hạn tại vùng hỗ trợ EMA 21 H1 khi giá điều chỉnh nhẹ. |
| **ZS** | **{zs_swing_long_label} ({zs_sw_code})** | **{zs_swing_long_entry}** | **{zs_swing_long_sl}** | **{zs_swing_long_tp}** | LỆNH LONG trung hạn ở hỗ trợ Price Action cứng (biên dưới). |
| **ZS** | **{zs_swing_short_label} ({zs_sw_code})** | **{zs_swing_short_entry}** | **{zs_swing_short_sl}** | **{zs_swing_short_tp}** | LỆNH SHORT trung hạn tại kháng cự đỉnh R2 (biên trên). |
| **ZS** | **{zs_dca_label} ({zs_dca_code})** | **{zs_dca}** | Không áp dụng | Mục tiêu dài hạn | Mua gom dài hạn phòng ngập lụt Midwest và nhu cầu Biodiesel. |

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
| **ZC** | Gieo trồng | **{fund['ZC']['us_planting']['latest']}** | 92% | 89% | **{fund['ZC']['crop_condition']['latest']}** | {fund['ZC']['us_planting']['action']} - {fund['ZC']['us_planting']['logic']} |
| **ZS** | Gieo trồng | **{fund['ZS']['us_planting']['latest']}** | 81% | 78% | **{fund['ZS']['crop_condition']['latest']}** | {fund['ZS']['us_planting']['action']} - {fund['ZS']['us_planting']['logic']} |
| **ZW** | Lúa đông | **{fund['ZW']['harvest_progress']['latest']}** | 3% | 2% | **{fund['ZW']['crop_condition']['latest']}** | {fund['ZW']['harvest_progress']['action']} - {fund['ZW']['harvest_progress']['logic']} |
| **ZW** | Lúa xuân | **{fund['ZW']['us_planting']['latest']}** | 91% | 88% | Chưa xếp hạng | {fund['ZW']['us_planting']['action']} - {fund['ZW']['us_planting']['logic']} |

#### 2. Báo cáo Cung cầu & Tồn kho USDA (USDA WASDE)
| Mã nông sản | Thông số Tồn kho | Mỹ (US Ending Stocks) | Thế giới (Global) | Lần cập nhật tới | Tác động biện chứng WASDE |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **ZC** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZC']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZC']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZC']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZC']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZC']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZC']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZC']['us_ending_stocks']['next_date']} | {fund['ZC']['global_ending_stocks']['action']} - {fund['ZC']['global_ending_stocks']['logic']} |
| **ZW** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZW']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZW']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZW']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZW']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZW']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZW']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZW']['us_ending_stocks']['next_date']} | {fund['ZW']['global_ending_stocks']['action']} - {fund['ZW']['global_ending_stocks']['logic']} |
| **ZS** | **Kỳ trước**<br>**Kỳ hiện tại**<br>***Dự báo kỳ tới*** | {fund['ZS']['us_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZS']['us_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZS']['us_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZS']['global_ending_stocks'].get('previous', 'N/A')}<br>**{fund['ZS']['global_ending_stocks'].get('current', 'N/A')}**<br>*{fund['ZS']['global_ending_stocks'].get('forecast_next', 'Chưa có')}* | {fund['ZS']['us_ending_stocks']['next_date']} | {fund['ZS']['global_ending_stocks']['action']} - {fund['ZS']['global_ending_stocks']['logic']} |

#### 3. Báo cáo Bán hàng & Giao hàng Xuất khẩu (USDA Weekly Export Sales & Inspections)
| Mã nông sản | Báo cáo | Số liệu trước đó | Số liệu mới nhất | Dự báo kỳ tiếp theo | Lần cập nhật tới | Tác động biện chứng xuất khẩu |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **ZC** | Bán hàng & Giao hàng | {fund['ZC']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZC']['exports']['latest'].replace('|', '\\|')}** | {fund['ZC']['exports']['forecast']} | {fund['ZC']['exports']['next_date']} | {fund['ZC']['exports']['action']} - {fund['ZC']['exports']['logic']} |
| **ZW** | Bán hàng & Giao hàng | {fund['ZW']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZW']['exports']['latest'].replace('|', '\\|')}** | {fund['ZW']['exports']['forecast']} | {fund['ZW']['exports']['next_date']} | {fund['ZW']['exports']['action']} - {fund['ZW']['exports']['logic']} |
| **ZS** | Bán hàng & Giao hàng | {fund['ZS']['exports'].get('previous', 'N/A').replace('|', '\\|')} | **{fund['ZS']['exports']['latest'].replace('|', '\\|')}** | {fund['ZS']['exports']['forecast']} | {fund['ZS']['exports']['next_date']} | {fund['ZS']['exports']['action']} - {fund['ZS']['exports']['logic']} |

#### 4. Báo cáo Sản lượng Cây trồng & Đối thủ Nam Mỹ (USDA Crop Production & Competitors)
| Mã nông sản | Thu hoạch Mỹ / Vụ mùa | Sản lượng Đối thủ Nam Mỹ | Lần cập nhật tới | Tác động biện chứng cung cầu |
| :---: | :--- | :--- | :---: | :--- |
| **ZC** | Thu hoạch: {fund['ZC']['harvest_progress']['latest']} | {fund['ZC']['competitors']['latest']} ({fund['ZC']['competitors']['forecast']}) | {fund['ZC']['competitors']['next_date']} | {fund['ZC']['competitors']['action']} - {fund['ZC']['competitors']['logic']} |
| **ZW** | Thu hoạch: {fund['ZW']['harvest_progress']['latest']} | {fund['ZW']['competitors']['latest']} ({fund['ZW']['competitors']['forecast']}) | {fund['ZW']['competitors']['next_date']} | {fund['ZW']['competitors']['action']} - {fund['ZW']['competitors']['logic']} |
| **ZS** | Thu hoạch: {fund['ZS']['harvest_progress']['latest']} | {fund['ZS']['competitors']['latest']} ({fund['ZS']['competitors']['forecast']}) | {fund['ZS']['competitors']['next_date']} | {fund['ZS']['competitors']['action']} - {fund['ZS']['competitors']['logic']} |

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
| **ZCU26** (Corn) | Long Hold (Leg 1 - Ngắn hạn) | **`420.00 - 433.00`**<br>*(Tháng 6 - 7)* | **`413.00`** | **`475.00`** \\| **`495.00`**<br>*(Tất toán: 15/07 - 25/07)* | **10%** |
| **ZCZ26** (Corn) | Long Hold (Leg 2 - Dài hạn) | **`430.00 - 438.00`**<br>*(Tháng 6 - 7)* | **`422.00`** | **`510.00`** \\| **`535.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 1 - 50%) | **`1125.00 - 1140.00`**<br>*(Tháng 6 - 7)* | **`1105.00`** | **`1200.00`** \\| **`1240.00`**<br>*(Tất toán: 20/08 - 05/09)* | **10%** |
| **ZSX26** (Soy) | Long Accumulation (Leg 2 - 50%) | **`1125.00 - 1140.00`**<br>*(Tháng 6 - 7)* | **`1105.00`** | **`1280.00`** \\| **`1320.00`**<br>*(Tất toán: 15/10 - 30/10)* | **10%** |
| **ZWU26** (Wheat)| Accumulative Long (Leg 1 - Ngắn hạn)| **`580.00 - 595.00`**<br>*(Tháng 6)* | **`565.00`** | **`645.00`** \\| **`675.00`**<br>*(Tất toán: 10/08 - 20/08)* | **10%** |
| **ZWZ26** (Wheat)| Accumulative Long (Leg 2 - Dài hạn) | **`590.00 - 605.00`**<br>*(Tháng 6)* | **`575.00`** | **`690.00`** \\| **`720.00`**<br>*(Tất toán: 15/11 - 30/11)* | **5%** |

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

# PHẦN III: DỰ BÁO AI & PHÂN TÍCH KỸ THUẬT CHI TIẾT TỪNG MÃ

## 2. BÁO CÁO MÃ ZC (NGÔ) - PHIÊN CHỐT {date_str}

### A. Phân loại Xu hướng Đa Khung thời gian (Multi-timeframe Trend Classification)

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | Chu kỳ đáy mùa vụ + La Niña vĩ mô dài hạn | Định hướng gom DCA dài hạn |
| **Trung hạn** | {zc_medium_trend_label} | {zc_medium_trend_logic} | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | {zc_short_trend_label} | {zc_short_trend_logic} | Canh vào lệnh ngắn hạn (Intraday) |

### B. Phân Tích Kỹ Thuật (H1 & M15 - {zc_act_name})
*   **Giá Chốt Phiên (Close):** {zc['close']:.2f} cents | **Dự báo Chốt Phiên (Predicted Close):** **`{zc_pred_close:.2f} cents`** ({zc_pred_chg:+.2f}).
*   **Vùng cản Pivot:** Hỗ trợ S1: **`{zc_sw['s1']:.2f}`** | S2: **`{zc_sw['s2']:.2f}`** || Kháng cự R1: **`{zc_sw['r1']:.2f}`** | R2: **`{zc_sw['r2']:.2f}`**
*   **Chỉ báo EMA H1:** `EMA_21` ({zc['ema_21']:.2f}) {'<' if zc['ema_21'] < zc['ema_50'] else '>'} `EMA_50` ({zc['ema_50']:.2f}) -> Tín hiệu {'Bullish' if zc['signal'] == 'Bullish' else 'Bearish'}.
*   **Động lượng & Dao động:** RSI (14) = **`{zc['rsi']:.2f}`** | ATR (14) = **`{zc['atr']:.2f}`** cents | Volatility = **`{zc['volatility']:.2f} cents`**.
*   **Thanh khoản ngày trước:** Volume: **`{zc_prev_vol:,.0f}`** | Open Interest (OI): **`{zc_prev_oi:,.0f}`**
*   **Thanh khoản phiên chốt:** Volume: **`{zc_today_vol:,.0f}`** (Chênh lệch: **`{zc_today_vol - zc_prev_vol:+,.0f}`**) | Open Interest (OI): **`{zc_today_oi:,.0f}`** (Chênh lệch: **`{zc_today_oi - zc_prev_oi:+,.0f}`**)
*   **Mô hình nến H1:** **`{zc_candle}`**
*   **Đánh giá xu hướng dòng tiền (Volume + OI):** **`{zc_liq_trend}`** — {zc_liq_logic}
*   **Đánh giá xu hướng kết hợp (Nến + Thanh khoản):** {zc_comb_trend}

### C. Nền Tảng Cơ Bản & Mùa Vụ Cốt Lõi (USDA Fundamentals Takeaways)
*   **Tồn kho & Cung cầu:** Tồn kho ngô toàn cầu chạm đáy 12 năm (`277.5M tấn`). Tồn kho Mỹ niên vụ 2026/27 giảm 8.6% xuống `1,957M bushels` do diện tích gieo trồng giảm 6%.
*   **Tiến độ gieo trồng & chất lượng:** Gieo trồng đạt **93%** (vượt trung bình 89%), chất lượng đầu mùa đạt **67% G/E**. Tiến độ nhanh kìm hãm giá ngắn hạn, tạo vùng gom dài hạn.
*   **Thời tiết & Đối thủ:** Khô hạn rìa phía Bắc (Minnesota, Northern Plains) đe dọa nảy mầm. Brazil vụ 2 (Safrinha) khô hạn cục bộ phía Nam làm tăng lo ngại sụt giảm năng suất.

### D. Thời Tiết Ngắn Hạn & Tác Động Intraday
*   **Diễn biến ngắn hạn (2-3 ngày qua):** {fund['ZC']['short_term_weather']}
*   **Biện chứng tác động giá:** {fund['ZC']['short_term_weather_logic']}

### E. Khuyến Nghị Giao Dịch Tổng Hợp (ZC Trading Strategies)
*   🚀 **{zc_intra_label} (Ngắn hạn):**
    *   *Chiến lược:* **{fund['ZC']['intraday_strategy']}**
    *   *Thiết lập:* Entry: **`{zc_intra_entry}`** | SL: **`{zc_intra_sl}`** | TP: `{zc_intra_tp1}` / `{zc_intra_tp2}`.
*   🚀 **Trung hạn (Swing Trades):**
    *   *Long (Mua biên dưới S1/S2):* Entry: **`{zc_swing_long_entry}`** | SL: **`{zc_swing_long_sl}`** | TP: **`{zc_swing_long_tp}`** (Lợi nhuận `>= 10.00 giá`).
    *   *Short (Bán biên trên R1/R2):* Entry: **`{zc_swing_short_entry}`** | SL: **`{zc_swing_short_sl}`** | TP: **`{zc_swing_short_tp}`** (Lợi nhuận `>= 10.00 giá`).
*   🚀 **{zc_dca_label} (Dài hạn):**
    *   *Chiến lược:* {fund['ZC']['seasonal_strategy']}
    *   *Thiết lập:* Entry gom: **`{zc_dca}`** | Logic: {fund['ZC']['dca_logic']}

---

## 3. BÁO CÁO MÃ ZW (LÚA MÌ) - PHIÊN CHỐT {date_str}

### A. Phân loại Xu hướng Đa Khung thời gian (Multi-timeframe Trend Classification)

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | Thiệt hại sản lượng kép toàn cầu (Úc -41%, Mỹ -18%) | Định hướng gom DCA dài hạn |
| **Trung hạn** | {zw_medium_trend_label} | {zw_medium_trend_logic} | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | {zw_short_trend_label} | {zw_short_trend_logic} | Canh vào lệnh ngắn hạn (Intraday) |

### B. Phân Tích Kỹ Thuật (H1 & M15 - {zw_act_name})
*   **Giá Chốt Phiên (Close):** {zw['close']:.2f} cents | **Dự báo Chốt Phiên (Predicted Close):** **`{zw_pred_close:.2f} cents`** ({zw_pred_chg:+.2f}).
*   **Vùng cản Pivot:** Hỗ trợ S1: **`{zw_sw['s1']:.2f}`** | S2: **`{zw_sw['s2']:.2f}`** || Kháng cự R1: **`{zw_sw['r1']:.2f}`** | R2: **`{zw_sw['r2']:.2f}`**
*   **Chỉ báo EMA H1:** `EMA_21` ({zw['ema_21']:.2f}) {'<' if zw['ema_21'] < zw['ema_50'] else '>'} `EMA_50` ({zw['ema_50']:.2f}) -> Tín hiệu {'Bullish' if zw['signal'] == 'Bullish' else 'Bearish'}.
*   **Động lượng & Dao động:** RSI (14) = **`{zw['rsi']:.2f}`** | ATR (14) = **`{zw['atr']:.2f}`** cents | Volatility = **`{zw['volatility']:.2f} cents`**.
*   **Thanh khoản ngày trước:** Volume: **`{zw_prev_vol:,.0f}`** | Open Interest (OI): **`{zw_prev_oi:,.0f}`**
*   **Thanh khoản phiên chốt:** Volume: **`{zw_today_vol:,.0f}`** (Chênh lệch: **`{zw_today_vol - zw_prev_vol:+,.0f}`**) | Open Interest (OI): **`{zw_today_oi:,.0f}`** (Chênh lệch: **`{zw_today_oi - zw_prev_oi:+,.0f}`**)
*   **Mô hình nến H1:** **`{zw_candle}`**
*   **Đánh giá xu hướng dòng tiền (Volume + OI):** **`{zw_liq_trend}`** — {zw_liq_logic}
*   **Đánh giá xu hướng kết hợp (Nến + Thanh khoản):** {zw_comb_trend}

### C. Nền Tảng Cơ Bản & Mùa Vụ Cốt Lõi (USDA Fundamentals Takeaways)
*   **Tồn kho & Cung cầu:** Tồn kho thế giới giảm liên tiếp năm thứ 4. Tồn kho Mỹ giảm 18.5% xuống `762M bushels` phản ánh thiệt hại sản lượng lúa mì đông nặng nề.
*   **Tiến độ gieo trồng & chất lượng:** Lúa đông gieo trồng thu hoạch đạt 5%. Xếp hạng chất lượng cực kỳ tệ hại: Chỉ **26% G/E** (trong khi **44% Poor/Very Poor**) do hạn hán tàn phá bang Kansas/Oklahoma.
*   **Thời tiết & Đối thủ:** Úc sụt giảm sản lượng 41% xuống `21.3M tấn` do hạn hán đầu vụ. Argentina sản lượng dự kiến giảm 25% do rủi ro bệnh dịch. Black Sea có sương giá muộn.

### D. Thời Tiết Ngắn Hạn & Tác Động Intraday
*   **Diễn biến ngắn hạn (2-3 ngày qua):** {fund['ZW']['short_term_weather']}
*   **Biện chứng tác động giá:** {fund['ZW']['short_term_weather_logic']}

### E. Khuyến Nghị Giao Dịch Tổng Hợp (ZW Trading Strategies)
*   🚀 **{zw_intra_label} (Ngắn hạn):**
    *   *Chiến lược:* **{fund['ZW']['intraday_strategy']}**
    *   *Thiết lập:* Entry: **`{zw_intra_entry}`** | SL: **`{zw_intra_sl}`** | TP: `{zw_intra_tp1}` / `{zw_intra_tp2}`.
*   🚀 **Trung hạn (Swing Trades):**
    *   *Long (Mua biên dưới S1/S2):* Entry: **`{zw_swing_long_entry}`** | SL: **`{zw_swing_long_sl}`** | TP: **`{zw_swing_long_tp}`** (Lợi nhuận `>= 14.00 giá`).
    *   *Short (Bán biên trên R1/R2):* Entry: **`{zw_swing_short_entry}`** | SL: **`{zw_swing_short_sl}`** | TP: **`{zw_swing_short_tp}`** (Lợi nhuận `>= 14.00 giá`).
*   🚀 **{zw_dca_label} (Dài hạn):**
    *   *Chiến lược:* {fund['ZW']['seasonal_strategy']}
    *   *Thiết lập:* Entry gom: **`{zw_dca}`** | Logic: {fund['ZW']['dca_logic']}

---

## 4. BÁO CÁO MÃ ZS (ĐẬU TƯƠNG) - PHIÊN CHỐT {date_str}

### A. Phân loại Xu hướng Đa Khung thời gian (Multi-timeframe Trend Classification)

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | Biodiesel đạt kỷ lục + La Niña quý 3 | Định hướng gom DCA dài hạn |
| **Trung hạn** | {zs_medium_trend_label} | {zs_medium_trend_logic} | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | {zs_short_trend_label} | {zs_short_trend_logic} | Canh vào lệnh ngắn hạn (Intraday) |

### B. Phân Tích Kỹ Thuật (H1 & M15 - {zs_act_name})
*   **Giá Chốt Phiên (Close):** {zs['close']:.2f} cents | **Dự báo Chốt Phiên (Predicted Close):** **`{zs_pred_close:.2f} cents`** ({zs_pred_chg:+.2f}).
*   **Vùng cản Pivot:** Hỗ trợ S1: **`{zs_sw['s1']:.2f}`** | S2: **`{zs_sw['s2']:.2f}`** || Kháng cự R1: **`{zs_sw['r1']:.2f}`** | R2: **`{zs_sw['r2']:.2f}`**
*   **Chỉ báo EMA H1:** `EMA_21` ({zs['ema_21']:.2f}) {'<' if zs['ema_21'] < zs['ema_50'] else '>'} `EMA_50` ({zs['ema_50']:.2f}) -> Tín hiệu {'Bullish' if zs['signal'] == 'Bullish' else 'Bearish'}.
*   **Động lượng & Dao động:** RSI (14) = **`{zs['rsi']:.2f}`** | ATR (14) = **`{zs['atr']:.2f}`** cents | Volatility = **`{zs['volatility']:.2f} cents`**.
*   **Thanh khoản ngày trước:** Volume: **`{zs_prev_vol:,.0f}`** | Open Interest (OI): **`{zs_prev_oi:,.0f}`**
*   **Thanh khoản phiên chốt:** Volume: **`{zs_today_vol:,.0f}`** (Chênh lệch: **`{zs_today_vol - zs_prev_vol:+,.0f}`**) | Open Interest (OI): **`{zs_today_oi:,.0f}`** (Chênh lệch: **`{zs_today_oi - zs_prev_oi:+,.0f}`**)
*   **Mô hình nến H1:** **`{zs_candle}`**
*   **Đánh giá xu hướng dòng tiền (Volume + OI):** **`{zs_liq_trend}`** — {zs_liq_logic}
*   **Đánh giá xu hướng kết hợp (Nến + Thanh khoản):** {zs_comb_trend}

### C. Nền Tảng Cơ Bản & Mùa Vụ Cốt Lõi (USDA Fundamentals Takeaways)
*   **Tồn kho & Cung cầu:** Tồn kho Mỹ giảm nhẹ xuống `310M bushels` do nhu cầu ép dầu nội địa (Crush) làm Biodiesel đạt mức cao kỷ lục. Cung cầu toàn cầu duy trì thắt chặt vừa phải.
*   **Tiến độ gieo trồng & chất lượng:** Gieo trồng đạt **87%** (vượt trung bình 78%), chất lượng đầu mùa đạt **66% G/E**. Tiến độ gieo nhanh nhưng ngập lụt Đông Midwest buộc phải gieo lại.
*   **Thời tiết & Đối thủ:** Ngập lụt nghiêm trọng Đông Midwest (Ohio, Indiana, Illinois) đe dọa úng hạt giống. Brazil xuất khẩu mạnh, sản lượng đạt kỷ lục `180M tấn`, Argentina đạt `50.1M tấn`.

### D. Thời Tiết Ngắn Hạn & Tác Động Intraday
*   **Diễn biến ngắn hạn (2-3 ngày qua):** {fund['ZS']['short_term_weather']}
*   **Biện chứng tác động giá:** {fund['ZS']['short_term_weather_logic']}

### E. Khuyến Nghị Giao Dịch Tổng Hợp (ZS Trading Strategies)
*   🚀 **{zs_intra_label} (Ngắn hạn):**
    *   *Chiến lược:* **{fund['ZS']['intraday_strategy']}**
    *   *Thiết lập:* Entry: **`{zs_intra_entry}`** | SL: **`{zs_intra_sl}`** | TP: `{zs_intra_tp1}` / `{zs_intra_tp2}`.
*   🚀 **Trung hạn (Swing Trades):**
    *   *Long (Mua biên dưới S1/S2):* Entry: **`{zs_swing_long_entry}`** | SL: **`{zs_swing_long_sl}`** | TP: **`{zs_swing_long_tp}`** (Lợi nhuận `>= 15.00 giá`).
    *   *Short (Bán biên trên R1/R2):* Entry: **`{zs_swing_short_entry}`** | SL: **`{zs_swing_short_sl}`** | TP: **`{zs_swing_short_tp}`** (Lợi nhuận `>= 15.00 giá`).
*   🚀 **{zs_dca_label} (Dài hạn):**
    *   *Chiến lược:* {fund['ZS']['seasonal_strategy']}
    *   *Thiết lập:* Entry gom: **`{zs_dca}`** | Logic: {fund['ZS']['dca_logic']}
"""
'''
new_content = pattern.sub(new_text, content)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
