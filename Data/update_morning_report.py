# -*- coding: utf-8 -*-
"""
Script cập nhật ai_news.json, ai_analysis.json và .streamlit_trigger
cho phiên sáng thứ Sáu, ngày 13/11/2026.
Tập trung vào:
1. Cú sốc Lúa Mì Argentina (BAGE/BCR: 23.8 - 24.3 MMT, FOB $200-207/tấn).
2. CBOT ZWZ26 lập đáy mới trong năm tại 582.4 ¢/bu trước áp lực Rollover.
3. Đàm phán Moscow Putin - Witkoff/Kushner bất đồng lãnh thổ.
4. DXY tăng vọt 103.17, Brent tăng 95.77 USD.
5. VSA/Wyckoff Selling Climax / Phase C Spring test và tín hiệu M15 bật nảy quanh 605c (kỳ H).
"""
import json
import datetime
from pathlib import Path

OUTPUT_DIR = Path("D:/0_Thang_Drive/Antigravity/Cbot/Data/output")
TRIGGER_FILE = Path("D:/0_Thang_Drive/Antigravity/Cbot/.streamlit_trigger")

now_str = "2026-11-13 06:30:00"

# 1. AI NEWS
news_data = {
    "timestamp": now_str,
    "news": [
        {
            "title": "Cú sốc lúa mì Argentina: BAGE & BCR nâng sản lượng lên 23.8 - 24.3 triệu tấn",
            "details": [
                "Sàn Giao dịch Ngũ cốc Buenos Aires (BAGE) và Rosario (BCR) đồng loạt nâng dự báo sản lượng lúa mì niên vụ 2026/27 của Argentina lên mức kỷ lục 23.8 – 24.3 triệu tấn (tăng hơn 2.8 triệu tấn so với dự báo trước).",
                "Năng suất lúa mì tại các vùng trọng điểm Buenos Aires, Cordoba và Santa Fe tăng đột biến nhờ lượng mưa lý tưởng trong tháng 10.",
                "Đây là vụ mùa lúa mì lớn thứ 2 trong lịch sử Argentina, tạo ra làn sóng nguồn cung dồi dào trên thị trường xuất khẩu quốc tế."
            ],
            "link": "https://www.bcr.com.ar/es/mercados/estimaciones-agricolas",
            "source": "12 Nov 2026 - Rosario Board of Trade / BAGE",
            "category": "san_luong_dien_tich"
        },
        {
            "title": "Argentina đại hạ giá xuất khẩu: Lúa mì FOB Up River rớt xuống 200 - 207 USD/tấn",
            "details": [
                "Áp lực thu hoạch cao điểm cùng nhu cầu thu ngoại tệ USD khiến các nhà xuất khẩu Argentina chào bán lúa mì FOB Up River (Rosario) ở mức siêu rẻ 200 – 207 USD/tấn (tương đương 545 – 565 ¢/bu).",
                "Mức giá này cạnh tranh khốc liệt và rẻ hơn 35 – 50 USD/tấn so với lúa mì Mỹ (SRW Gulf ~255 USD/tấn) và lúa mì Nga (~235 USD/tấn).",
                "Lúa mì Argentina đang độc chiếm thị trường Brazil và xâm lấn mạnh sang Bắc Phi, Đông Nam Á, tạo sức ép giảm giá dây chuyền lên sàn CBOT."
            ],
            "link": "https://www.reuters.com/markets/commodities/argentina-grains",
            "source": "12 Nov 2026 - Reuters Grains Desk",
            "category": "cung_cau_nhan_dinh"
        },
        {
            "title": "CBOT ZWZ26 lao dốc lập đáy mới trong năm tại 582.4 ¢/bu trước áp lực Rollover",
            "details": [
                "Hợp đồng lúa mì CBOT kỳ hạn tháng 12/2026 (ZWZ26) giảm sâu -18.1 cent trong phiên ngày 12/11, xuyên thủng đáy cũ 590c để chạm mức thấp kỷ lục năm tại 582.4 ¢/bu.",
                "Áp lực bán tháo đến từ sự kết hợp của lúa mì giá rẻ Argentina, chỉ số DXY tăng vọt lên 103.17 và các quỹ đầu cơ thanh lý vị thế Long trước ngày First Notice Day (30/11).",
                "Tuy nhiên, lực cầu bắt đáy hấp thụ (Absorption) xuất hiện mạnh cuối phiên Mỹ tại vùng 582 - 585c kỳ Z và 603 - 605c kỳ H (ZWH27)."
            ],
            "link": "https://www.barchart.com/futures/quotes/ZWZ26",
            "source": "13 Nov 2026 - CBOT Pit Wire",
            "category": "cung_cau_nhan_dinh"
        },
        {
            "title": "Đàm phán Moscow: Putin nêu bất đồng lãnh thổ với phái đoàn Mỹ (Witkoff & Kushner)",
            "details": [
                "Tổng thống Nga Vladimir Putin đã tiếp phái đoàn đặc phái viên Mỹ (Steve Witkoff và Jared Kushner) tại Điện Kremlin để thảo luận về triển vọng ngừng bắn.",
                "Ông Putin nhấn mạnh hai bên có 'cách giải thích khác nhau về các vấn đề lãnh thổ' (đặc biệt là Donetsk và Luhansk), đồng thời tái khẳng định sự hiện diện của lực lượng nước ngoài tại Ukraine là mối đe dọa an ninh quốc gia.",
                "Chưa có đột phá hòa bình ngay lập tức; rủi ro xung đột quân sự tại khu vực Biển Đen vẫn duy trì ở mức cao."
            ],
            "link": "https://www.reuters.com/world/europe/putin-us-envoys-talks",
            "source": "12 Nov 2026 - Kremlin / Reuters Wire",
            "category": "dia_chinh_tri"
        },
        {
            "title": "Cảng Baltic Ust-Luga bị tấn công drone; SovEcon hạ dự báo xuất khẩu lúa mì Nga xuống 36 triệu tấn",
            "details": [
                "Hạ tầng tại cảng xuất khẩu dầu và ngũ cốc Ust-Luga ở vùng Baltic của Nga bị hư hại sau đợt tấn công bằng thiết bị bay không người lái.",
                "Hãng tư vấn nông nghiệp SovEcon tiếp tục hạ ước tính xuất khẩu lúa mì Nga niên vụ 2026/27 xuống còn 36.0 triệu tấn (thấp hơn nhiều so với con số 39.0 triệu tấn của USDA).",
                "Lithuania tuyên bố bắt đầu áp dụng các biện pháp kiểm soát chặt chẽ hàng hóa quá cảnh từ Nga qua ngả Kaliningrad từ ngày 16/11, gây khó khăn thêm cho logistics Baltic."
            ],
            "link": "https://www.world-grain.com/articles/sovecon-russia-wheat-export-cut",
            "source": "12 Nov 2026 - SovEcon / World Grain",
            "category": "logistics"
        },
        {
            "title": "Dầu thô Brent tăng vọt lên 95.77 USD/thùng (+3.24%) trong khi DXY lên 103.17",
            "details": [
                "Giá dầu Brent giao sau bật tăng mạnh hơn 3 USD/thùng lên 95.77 USD do lo ngại căng thẳng địa chính trị Trung Đông và rủi ro gián đoạn nguồn cung năng lượng Nga.",
                "Đồng USD mạnh lên với chỉ số DXY đạt 103.17 (+0.25%), tạo áp lực tỷ giá khiến nông sản Mỹ kém cạnh tranh trong ngắn hạn.",
                "Giá dầu cao tiếp tục neo giữ chi phí phân bón, vận tải biển và hỗ trợ nhu cầu chế biến ethanol từ ngô."
            ],
            "link": "https://finance.yahoo.com/quote/BZ=F",
            "source": "13 Nov 2026 - Bloomberg / Yahoo Finance",
            "category": "cung_cau_nhan_dinh"
        },
        {
            "title": "Đấu thầu quốc tế: Algeria (OAIC) mua hơn 700.000 tấn lúa mì; Jordan mở thầu",
            "details": [
                "Cơ quan ngũ cốc nhà nước Algeria (OAIC) đã chốt mua hơn 700.000 tấn lúa mì xay xát trong đợt thầu quốc tế lớn nhất tháng 11, tận dụng vùng giá thấp toàn cầu.",
                "Jordan tiếp tục phát hành hồ sơ mời thầu quốc tế mua 120.000 tấn lúa mì giao hàng tháng 1 và tháng 2/2027.",
                "Các nước nhập khẩu lớn tại Trung Đông và Bắc Phi đang tích cực tích trữ lương thực chiến lược khi nhận định giá lúa mì thế giới đang ở vùng đáy hấp dẫn."
            ],
            "link": "https://www.reuters.com/markets/commodities/algeria-wheat-tender",
            "source": "12 Nov 2026 - Reuters Tenders Desk",
            "category": "cung_cau_nhan_dinh"
        },
        {
            "title": "Thời tiết nông nghiệp: US Plains ẩm tốt; Cảnh báo phân tách xoáy cực Polar Vortex",
            "details": [
                "Các đợt mưa gần đây trên khắp vùng đồng bằng phía Nam Mỹ (Kansas, Oklahoma, Texas) đã cải thiện đáng kể độ ẩm đất cho lúa mì vụ đông sinh trưởng tốt.",
                "Vùng Rostov và Nam Nga ghi nhận mưa rào 33.8mm giúp giảm bớt hạn hán cục bộ trước khi bước vào kỳ ngủ đông.",
                "Các mô hình khí tượng cảnh báo hiện tượng phân tách xoáy cực (Polar Vortex Split) có thể mang đợt rét kỷ lục đến Bắc Mỹ và châu Âu vào cuối tháng 11."
            ],
            "link": "https://climatelligence.substack.com/p/what-is-a-split-in-the-polar-vortex",
            "source": "11 Nov 2026 - BestWeather / Jim Roemer",
            "category": "san_luong_dien_tich"
        }
    ]
}

# 2. AI ANALYSIS (6-Part Framework)
analysis_data = {
    "timestamp": now_str,
    "model": "gemini-2.5-flash",
    "version": "run_tin_tuc_6_parts_v1",
    "structured": {
        "header_context": {
            "report_time": "2026-11-13 06:30 (Giờ VN)",
            "zw_price_str": "582.40 ¢/bu (Đáy mới trong năm, -18.1c | Fair Value gốc: 670c)",
            "zc_price_str": "442.25 ¢/bu (Fair Value gốc: 480c)",
            "cot_summary": "ZW Net Est: -91,443 HĐ (Short kỷ lục) | ZC Net Est: +6,289 HĐ",
            "macro_summary": "DXY: 103.17 (+0.25%) | Brent: $95.77 (+3.24%)"
        },
        "table_parts": [
            {
                "part_num": "PHẦN 1",
                "part_title": "Phiên Đêm, Cấu Trúc Giá (VSA/Wyckoff) & Vị Thế COT",
                "core_content": "Phiên đêm 12/11 chứng kiến đợt bán tháo dữ dội trên thị trường lúa mì CBOT. Hợp đồng ZWZ26 bị xả mạnh xuyên thủng mốc hỗ trợ tâm lý 590c, chạm mức đáy sâu nhất trong năm tại 582.4 ¢/bu (-18.1c). Đây là hành vi Selling Climax điển hình trong giai đoạn Phase C Wyckoff (hoặc Spring Test đáy lớn). Nguyên nhân chủ yếu đến từ áp lực thanh lý ép dồn vị thế Long trước kỳ hạn First Notice Day (30/11) kết hợp hiệu ứng tin tức nguồn cung Argentina. Tuy nhiên, khối lượng giao dịch tăng vọt ở vùng 582 - 585c và xuất hiện cây nến rút chân M15 tại 605c trước khi trượt về chốt phiên 597.4c trên kỳ hạn ZWH27 cho thấy lực cầu của Smart Money đã nhập cuộc hấp thụ (Absorption). Vị thế COT ước tính Net Short của Managed Money vẫn neo ở mức cực đại (-91,443 HĐ), khiến độ nén lò xo ngày càng khổng lồ. Ngô (ZCZ26) điều chỉnh nhẹ về 442.25c, tiếp tục vận động trong biên độ tích lũy mùa vụ sát sàn chi phí sản xuất (440 - 450c).",
                "zw_impact": "ZWZ26 chạm đáy sâu mới 582.4c, bước vào trạng thái siêu quá bán (Extreme Oversold). Giá đang nằm sâu dưới sàn chi phí nông dân Mỹ (600 - 620c). Nến M15 rút chân kỳ H tại 605c xác nhận lực đỡ ban đầu; rủi ro Short-Squeeze bùng nổ khi áp lực rollover hạ nhiệt.",
                "zw_badge": "SELLING CLIMAX / SPRING TEST 582.4c",
                "zc_impact": "ZCZ26 lùi về 442.25c nhưng giữ vững sàn hỗ trợ cứng 440c. Áp lực bán từ đợt thu hoạch đỉnh điểm tại Mỹ đang cạn kiệt dần. Vùng giá 440 - 445c là đệm đỡ vững chắc.",
                "zc_badge": "TÍCH LŨY SÀN CHI PHÍ SẢN XUẤT"
            },
            {
                "part_num": "PHẦN 2",
                "part_title": "Cung Cầu Thực Tế, Báo Cáo USDA & Cú Sốc Lúa Mì Argentina",
                "core_content": "Tâm điểm rung lắc thị trường phiên vừa qua bắt nguồn từ Nam Bán Cầu: Sàn Rosario (BCR) và Sàn Buenos Aires (BAGE) đồng loạt công bố nâng dự báo sản lượng lúa mì Argentina vụ 2026/27 lên mức kỷ lục 23.8 – 24.3 triệu tấn (+2.8 triệu tấn so với kỳ vọng trước đó). Với việc bước vào đỉnh điểm thu hoạch tháng 11-12 và nhu cầu giải phóng kho thu USD, các nhà xuất khẩu Argentina ồ ạt chào bán lúa mì FOB Up River ở mức giá rẻ khó tin: 200 – 207 USD/tấn (~545 – 565 ¢/bu), rẻ hơn lúa mì Mỹ 40-50 USD/tấn. Nguồn cung này lập tức chiếm lĩnh toàn bộ thị trường Brazil và chèn ép thị trường Bắc Phi. Ở chiều ngược lại, hãng SovEcon tiếp tục cắt giảm ước tính xuất khẩu lúa mì Nga xuống 36.0 triệu tấn (thấp hơn nhiều so với mức 39.0 triệu tấn của USDA). Algeria (OAIC) vừa chốt mua hơn 700.000 tấn lúa mì và Jordan mời thầu 120.000 tấn, cho thấy người mua tiền mặt toàn cầu đang tranh thủ gom hàng giá rẻ.",
                "zw_impact": "Áp lực 'dội chợ' của lúa mì Argentina trong ngắn hạn đẩy giá CBOT về đáy 582.4c để chiết khấu cạnh tranh. Tuy nhiên, sản lượng vụ mùa Argentina (~24 MMT) chỉ bằng 1/3 Nga và không thể bù đắp được khoảng trống xuất khẩu Biển Đen khi Nga siết hạn ngạch từ mùa đông.",
                "zw_badge": "SỐC CUNG ARGENTINA VS THỦNG BIỂN ĐEN",
                "zc_impact": "Ngô Mỹ xuất khẩu duy trì ổn định, tiến độ thu hoạch tại Corn Belt đã vượt 92%. Áp lực bán ngô vụ mới của nông dân Mỹ đang giảm nhanh khi nông dân chuyển sang tích trữ trong silo chờ giá phục hồi.",
                "zc_badge": "TIẾN ĐỘ THU HOẠCH CUỐI VỤ"
            },
            {
                "part_num": "PHẦN 3",
                "part_title": "Địa Chính Trị, Biển Đen, Tàu Biển & Năng Lượng / Vĩ Mô",
                "core_content": "Về mặt địa chính trị, cuộc gặp tại Moscow giữa Tổng thống Nga Putin và hai đặc phái viên Mỹ (Steve Witkoff và Jared Kushner) đã kết thúc mà không đạt được thỏa thuận ngừng bắn tức thời. Ông Putin thẳng thắn nêu rõ hai bên có 'cách giải thích khác nhau về các vấn đề lãnh thổ' (Nga yêu cầu kiểm soát toàn bộ Donetsk và Luhansk) và nhấn mạnh quân đội nước ngoài tại Ukraine là mục tiêu hợp pháp. Cùng lúc, cảng chiến lược Ust-Luga của Nga ở biển Baltic bị drone tấn công làm hư hại hạ tầng năng lượng, và Lithuania siết chặt kiểm soát hàng hóa quá cảnh từ 16/11. Trên thị trường vĩ mô, dầu thô Brent tăng vọt +3.24% lên 95.77 USD/thùng do căng thẳng Trung Đông và đe dọa chuỗi cung ứng dầu Nga. Tuy nhiên, chỉ số DXY cũng tăng lên 103.17 (+0.25%), tạo áp lực ghìm giá các mặt hàng tính bằng USD.",
                "zw_impact": "Bế tắc đàm phán Nga - Mỹ và rủi ro cảng biển Baltic bị tấn công duy trì 'phí bảo hiểm rủi ro chiến tranh' (war risk premium) cho ngũ cốc Biển Đen. Chi phí vận tải biển và bảo hiểm tàu tăng cao, hỗ trợ giá sàn lúa mì thế giới.",
                "zw_badge": "CĂNG THẲNG ĐỊA CHÍNH TRỊ BIỂN ĐEN",
                "zc_impact": "Giá dầu Brent leo dốc lên 95.77 USD/thùng mang lại lợi nhuận biên cực lớn cho các nhà máy ethanol Mỹ, kích hoạt lực cầu nội địa tiêu thụ ngô xay xát mạnh mẽ.",
                "zc_badge": "BRENT $95.77 HỖ TRỢ ETHANOL"
            },
            {
                "part_num": "PHẦN 4",
                "part_title": "Thời Tiết Nông Nghiệp Chuyên Sâu (US Plains, Nga, Nam Mỹ)",
                "core_content": "Thời tiết toàn cầu đang có những diễn biến phân hóa rõ nét. Tại Mỹ, dải mưa mùa thu vừa qua tại Southern Plains (Kansas, Oklahoma, Texas) đã bổ sung độ ẩm đất quý giá, giúp lúa mì HRW nảy mầm tốt và tỷ lệ Good/Excellent cải thiện. Tại Nga, khu vực Rostov và miền Nam ghi nhận lượng mưa 33.8mm, giúp cây lúa mì phát triển rễ trước khi tuyết rơi. Tại Argentina, thời tiết vùng Pampas khô ráo và nắng ấm với lượng mưa vừa phải (5.0mm) tạo điều kiện tối ưu để đẩy nhanh tiến độ gặt lúa mì vụ mới. Đáng chú ý, các chuyên gia khí tượng (Jim Roemer - Climatelligence) cảnh báo hiện tượng phân tách xoáy cực (Polar Vortex Split) bất thường vào tháng 11 có thể kéo theo các đợt rét cắt da cắt thịt và nguy cơ Winterkill cho lúa mì vụ đông Mỹ nếu thiếu lớp tuyết che phủ (snow cover).",
                "zw_impact": "Mưa tại Mỹ và Nga tạo áp lực tâm lý giảm giá ngắn hạn (Bearish thời tiết), nhưng rủi ro rét đậm Polar Vortex cuối tháng 11 và đầu tháng 12 sẽ là ẩn số thời tiết kích hoạt đà bật mạnh.",
                "zw_badge": "ẨM ĐẤT TỐT / THEO DÕI POLAR VORTEX",
                "zc_impact": "Thời tiết Midwest hanh khô giúp nông dân Mỹ dọn sạch những cánh đồng ngô cuối cùng. Mưa thuận lợi tại Brazil hỗ trợ gieo trồng đậu tương và ngô vụ 1.",
                "zc_badge": "THUẬN LỢI THU HOẠCH"
            },
            {
                "part_num": "PHẦN 5",
                "part_title": "Chuyên Mục AgWeb Market Analysis (Góc Nhìn Chuyên Gia Mỹ)",
                "core_content": "Các chuyên gia phân tích hàng đầu trên AgWeb tiếp tục mổ xẻ hiện tượng thị trường bị bán quá đà. Jim Roemer (BestWeather) nhận định giá nông sản đang phản ánh tiêu cực quá mức nguồn cung Nam Mỹ mà bỏ quên rủi ro thời tiết cực đoan El Niño và xoáy cực Polar Vortex. Brad Kooima (Kooima Kooima Varilek) lưu ý mô hình đảo chiều Wyckoff thường hình thành sau một đợt rũ bỏ kinh hoàng (Shakeout) khi các vị thế yếu (weak hands) bị quét sạch lệnh dừng lỗ tại vùng đáy cũ. Randy Martinson (Martinson Ag) cho rằng đợt giảm xuống 582.4c của lúa mì mang tính chất kỹ thuật ép thanh lý kỳ hạn tháng 12 (December liquidation) hơn là thay đổi về bức tranh cán cân cung cầu dài hạn. Các chuyên gia thống nhất rằng mức giá dưới 590c của lúa mì đã rơi vào vùng siêu định giá thấp (Deep Discount), tạo tỷ lệ Risk:Reward vượt trội cho phe Mua trung-dài hạn.",
                "zw_impact": "Đồng thuận từ các chuyên gia Mỹ: Lúa mì đã chạm vùng định giá cực đoan. Cú rũ bỏ về 582.4c là cơ hội gom hàng trung-dài hạn cho kỳ hạn năm 2027.",
                "zw_badge": "SHAKEOUT ĐÁY CỰC ĐOAN",
                "zc_impact": "Ngô đang ở vùng đáy mùa vụ điển hình (Harvest Low), các chuyên gia khuyến nghị hạn chế bán đuổi và chuẩn bị cho nhịp hồi phục sau khi nông dân hoàn tất thu hoạch.",
                "zc_badge": "CHỜ NHỊP PHỤC HỒI HẬU THU HOẠCH"
            }
        ],
        "daily_trend_conclusion": {
            "summary_label": "Tổng hợp trọng số từ 5 Phần trên cho phiên giao dịch hôm nay:",
            "zw_trend_title": "RŨ BỎ TẠO ĐÁY HOÀN TẤT / HỒI PHỤC KỸ THUẬT VÙNG 582 – 595c",
            "zw_range": "ZWZ26: 580.0 – 595.0 ¢/bu | ZWH27: 595.0 – 610.0 ¢/bu",
            "zw_rationale": "Cú đạp về 582.4c đã rũ bỏ sạch lượng stoploss tại đáy cũ. Nến rút chân M15 tại 605c kỳ H và lực gom của các nhà nhập khẩu quốc tế (Algeria) mở ra nhịp hồi phục kỹ thuật vững chắc.",
            "zc_trend_title": "TÍCH LŨY SÀN CHI PHÍ SẢN XUẤT (440 – 448c)",
            "zc_range": "ZCZ26: 440.0 – 448.0 ¢/bu",
            "zc_rationale": "Giá dầu Brent tăng vọt lên 95.77 USD cùng sàn chi phí sản xuất 440c sẽ bảo vệ vững chắc vùng đáy của ngô."
        },
        "part6_strategy": {
            "executive_verdict": "Thị trường nông sản CBOT ngày 13/11/2026 ghi nhận cú sốc kép từ vụ mùa kỷ lục Argentina (23.8 - 24.3 MMT, FOB $200/tấn) và áp lực thanh lý rollover hợp đồng ZWZ26 trước ngày FND (30/11), đẩy giá ZWZ26 xuống đáy mới trong năm tại 582.4 ¢/bu. Tuy nhiên, đây là cấu trúc Wyckoff Spring / Selling Climax điển hình khi vị thế Net Short của quỹ vẫn ở mức kỷ lục (-91k HĐ) và giá đã nằm sâu dưới sàn chi phí nông dân Mỹ. Với việc nến M15 đã bật nảy từ 602.4c lên 605.4c trên kỳ hạn ZWH27, chiến thuật tối ưu lúc này là: Giữ vững kỷ luật kho hàng, nhồi thêm Lot 2 cho kỳ hạn ZWH27 quanh vùng 605c để đón sóng dài hạn, đồng thời tận dụng các nhịp hồi phục kỹ thuật sắp tới để chốt bớt kỳ hạn cận ZWZ26 nhằm giảm tải áp lực giao nhận.",
            "golden_rules": [
                "Không hoảng loạn bán tháo tại đáy Selling Climax (dưới 585c ZWZ26 / dưới 605c ZWH27) khi nông dân toàn cầu đang lỗ nặng ở mức giá này.",
                "Phân tách rõ ràng mục tiêu giữa 2 kỳ hạn: Kỳ ZWZ26 ưu tiên thoát bớt khi hồi phục để tránh rủi ro Rollover FND; Kỳ ZWH27 giữ vững vị thế gom dài hạn đón sóng mùa đông và El Niño 2027.",
                "Kiểm soát tuyệt đối tỷ trọng lệnh, không mở thêm đòn bẩy quá mức khi thị trường đang trong pha xác nhận tạo đáy."
            ],
            "zw_tactical": {
                "intraday_contract": "ZWZ26 (HĐ Tháng 12/2026)",
                "intraday_plan": "Ưu tiên theo dõi nhịp hồi phục kỹ thuật. Đặt sẵn lệnh Sell Limit quanh vùng 605.0 – 615.0 ¢/bu (hoặc giữ nguyên lệnh Sell Limit 2 Lots @ 617'4) để hạ tỷ trọng hàng cận tháng trước First Notice Day 30/11.",
                "support_zone": "580.0 – 582.5 ¢/bu",
                "resistance_zone": "595.0 – 605.0 ¢/bu",
                "macro_dca_contract": "ZWH27 (HĐ Tháng 03/2027)",
                "macro_dca_plan": "Đã thực hiện nhồi Lot 2 quanh 605.0 – 605.4 ¢/bu khi nến M15 rút chân và RSI chạm 20 đảo chiều. Nắm giữ chặt vị thế ZWH27 kỳ hạn tháng 3/2027 với mục tiêu trung-dài hạn 640 – 670 ¢/bu đón mùa đông và hạn ngạch Biển Đen."
            },
            "zc_tactical": {
                "intraday_contract": "ZCZ26 (HĐ Tháng 12/2026)",
                "intraday_plan": "Canh mua thăm dò ngắn hạn tại vùng hỗ trợ 440.0 – 442.0 ¢/bu khi giá test sàn chi phí sản xuất, chốt lời ngắn tại 448.0 – 450.0 ¢/bu. Cắt lỗ nếu thủng 438.0 ¢/bu.",
                "support_zone": "440.0 – 442.0 ¢/bu",
                "resistance_zone": "448.0 – 452.0 ¢/bu",
                "macro_dca_contract": "ZCZ26 / ZCH27",
                "macro_dca_plan": "Rải vốn tích lũy kỳ hạn ZCH27 quanh 450 – 455c khi nông dân Mỹ kết thúc vụ thu hoạch và nhu cầu ethanol bùng nổ theo giá dầu Brent $95.77."
            }
        }
    }
}

# Write files
with open(OUTPUT_DIR / "ai_news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)
print("Updated ai_news.json successfully!")

with open(OUTPUT_DIR / "ai_analysis.json", "w", encoding="utf-8") as f:
    json.dump(analysis_data, f, ensure_ascii=False, indent=2)
print("Updated ai_analysis.json successfully!")

with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
    f.write(now_str)
print("Updated .streamlit_trigger successfully!")
