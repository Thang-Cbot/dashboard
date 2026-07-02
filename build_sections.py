def build_commodity_section(
    code, emoji, name_vn, date_str,
    data, fund, cot_data_json,
    brent_price, brent_pct, dxy_price, dxy_pct,
    pred_close, pred_chg,
    act_code, sw_code, dca_code,
    intra_label, intra_entry, intra_sl, intra_tp1, intra_tp2,
    swing_long_label, swing_long_entry, swing_long_sl, swing_long_tp,
    swing_short_label, swing_short_entry, swing_short_sl, swing_short_tp,
    dca_label, dca_entry,
    candle, comb_trend, liq_trend, liq_logic,
    today_vol, prev_vol, today_oi, prev_oi, today_close, prev_close,
    short_trend_label, short_trend_logic,
    medium_trend_label, medium_trend_logic,
    fc_data=None, weather_data=None, export_data=None
) -> str:
    # 1. Prepare Macro Impacts
    brent_trend = "Tăng" if brent_pct >= 0 else "Giảm"
    dxy_trend = "Tăng" if dxy_pct >= 0 else "Giảm"
    
    macro_impact = ""
    if code == "ZC":
        brent_impact = "hỗ trợ biên lợi nhuận pha chế Ethanol, kéo theo nhu cầu ngô tích cực." if brent_pct >= 0 else "làm giảm biên lợi nhuận pha chế Ethanol, tạo sức ép lên nhu cầu ngô."
        dxy_impact = "làm giảm sức cạnh tranh xuất khẩu của ngô Mỹ so với Brazil/Argentina." if dxy_pct >= 0 else "hỗ trợ xuất khẩu ngô Mỹ cạnh tranh tốt hơn."
    elif code == "ZW":
        brent_impact = "tăng premium rủi ro địa chính trị và logistics Biển Đen, hỗ trợ giá lúa mì." if brent_pct >= 0 else "giảm bớt premium rủi ro địa chính trị, tạo áp lực chốt lời lúa mì."
        dxy_impact = "khiến lúa mì Mỹ đắt đỏ hơn đối với các khách hàng truyền thống như Ai Cập/Châu Á." if dxy_pct >= 0 else "kích thích nhu cầu nhập khẩu lúa mì Mỹ trên thị trường quốc tế."
    else: # ZS
        brent_impact = "thúc đẩy mạnh mẽ nhu cầu Biodiesel và Dầu thực vật, hỗ trợ chuỗi ép dầu đậu tương." if brent_pct >= 0 else "làm giảm nhu cầu năng lượng sinh học, tác động tiêu cực đến giá đậu tương."
        dxy_impact = "khiến Trung Quốc ưu tiên mua hàng giá rẻ từ Brazil hơn là Mỹ." if dxy_pct >= 0 else "tạo động lực cho Trung Quốc chốt các đơn hàng lớn từ Mỹ."

    macro_html = f"""
| Chỉ số | Giá trị Hiện tại | Biến động 24h | Tác động Biện chứng lên {name_vn} ({code}) |
| :--- | :---: | :---: | :--- |
| **Dầu Brent** | **${brent_price:.2f}** | **{brent_pct:+.2f}%** | Giá dầu {brent_trend} {brent_impact} |
| **USD Index** | **{dxy_price:.2f}** | **{dxy_pct:+.2f}%** | DXY {dxy_trend} {dxy_impact} |
"""

    # 2. Prepare COT Data
    cot_map = {"ZC": "002602", "ZW": "001602", "ZS": "005602"}
    cot_key = cot_map.get(code, "")
    cot_info = cot_data_json.get("commodities", {}).get(cot_key, {})
    
    if cot_info and "error" not in cot_info:
        cot_html = f"""
| Báo cáo COT Managed Money | {name_vn} ({code}) | Đánh giá & Hành động |
| :--- | :---: | :--- |
| **Ngày Báo Cáo** | **{cot_info.get('report_date', 'N/A')}** | Cập nhật mới nhất từ CFTC |
| **Trạng Thái Matrix** | **{cot_info.get('quadrant', 'Chưa rõ')}** | *{cot_info.get('action', '')}* |
| **Net Position** | **{cot_info.get('net_position', 0):,.0f}** | Hợp đồng (Long - Short) |
| **Thay đổi Tuần qua** | **{cot_info.get('change', 0):+,.0f}** | Hợp đồng thay đổi so với tuần trước |
"""
    else:
        cot_html = "> *[Lỗi] Không lấy được dữ liệu CFTC COT API cho mã này.*\n"

    # 3. Prepare Fundamentals
    fund_html = ""
    f_data = fund.get(code, {})
    
    if code == "ZC":
        fund_html = f"""
| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | {f_data.get('us_ending_stocks', {}).get('current', 'N/A')} | {f_data.get('global_ending_stocks', {}).get('action', '')} |
| **Tồn kho Thế giới** | {f_data.get('global_ending_stocks', {}).get('current', 'N/A')} | {f_data.get('global_ending_stocks', {}).get('logic', '')} |
| **Tiến độ Gieo trồng** | {f_data.get('us_planting', {}).get('latest', 'N/A')} | {f_data.get('us_planting', {}).get('action', '')} |
| **Chất lượng G/E** | {f_data.get('crop_condition', {}).get('latest', 'N/A')} | Phản ánh rủi ro thời tiết Midwest |
| **Đối thủ (Brazil)** | {f_data.get('competitors', {}).get('latest', 'N/A')} | {f_data.get('competitors', {}).get('action', '')} |
"""
    elif code == "ZW":
        fund_html = f"""
| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | {f_data.get('us_ending_stocks', {}).get('current', 'N/A')} | {f_data.get('global_ending_stocks', {}).get('action', '')} |
| **Tiến độ Thu hoạch** | {f_data.get('harvest_progress', {}).get('latest', 'N/A')} | {f_data.get('harvest_progress', {}).get('action', '')} |
| **Chất lượng G/E** | {f_data.get('crop_condition', {}).get('latest', 'N/A')} | Cực kỳ thấp, rủi ro thiếu hụt chất lượng cao |
| **Đối thủ (Australia)** | {f_data.get('competitor_weather', {}).get('australia', 'N/A')} | Tác động cung cầu Châu Á |
| **Đối thủ (Argentina)**| {f_data.get('competitor_weather', {}).get('argentina', 'N/A')} | Áp lực nguồn cung Nam Bán Cầu |
"""
    elif code == "ZS":
        fund_html = f"""
| Chỉ tiêu Cơ bản USDA | Số liệu mới nhất | Tác động |
| :--- | :--- | :--- |
| **Tồn kho Mỹ (US ES)** | {f_data.get('us_ending_stocks', {}).get('current', 'N/A')} | {f_data.get('global_ending_stocks', {}).get('action', '')} |
| **Tiến độ Gieo trồng** | {f_data.get('us_planting', {}).get('latest', 'N/A')} | {f_data.get('us_planting', {}).get('action', '')} |
| **Chất lượng G/E** | {f_data.get('crop_condition', {}).get('latest', 'N/A')} | Rủi ro ngập úng Midwest |
| **Đối thủ (Brazil)** | {f_data.get('competitors', {}).get('latest', 'N/A')} | {f_data.get('competitors', {}).get('action', '')} |
| **Nhu cầu Trung Quốc** | {f_data.get('competitor_weather', {}).get('china', 'N/A')} | Động lực cầu chính |
"""

    # 4. Prepare Future Chart
    fc_html = ""
    if fc_data:
        fc_meta = fc_data.get("meta", {})
        fc_candles = fc_data.get("candles_4h", [])
        
        fc_html += f"*(Mã hợp đồng: **{fc_meta.get('contract', '')}** | Điểm Bias Tổng Hợp: **{fc_meta.get('composite_bias', 0):+.2f}**)*\n\n"
        
        fc_html += "| Ngày Giao Dịch | Phiên (Session) | Mở (Open) | Cao (High) | Thấp (Low) | Đóng (Close) | Thay đổi | Bias |\n"
        fc_html += "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        for c in fc_candles:
            chg_str = f"{c.get('net_change', 0):+.2f}¢"
            if c.get('net_change', 0) >= 0:
                chg_str = f"**{chg_str}** 🟢"
            else:
                chg_str = f"**{chg_str}** 🔴"
                
            fc_html += f"| **{c.get('day')}** | {c.get('session')} | {c.get('open'):.2f} | {c.get('high'):.2f} | {c.get('low'):.2f} | **{c.get('close'):.2f}** | {chg_str} | {c.get('bias', '')} |\n"
            
        fc_html += "\n**Kịch bản theo ngày:**\n"
        for day, sum_data in fc_data.get("daily_summary", {}).items():
            fc_html += f"- **{day}:** {sum_data.get('scenario', '')} — *{sum_data.get('logic', '')}*\n"
    else:
        fc_html = "*(Hệ thống Future Chart AI không tạo được dữ liệu hoặc đang bảo trì)*\n"

    # Sinh HTML cho Thoi tiet (E)
    weather_html = ""
    if weather_data and "regions" in weather_data:
        weather_html += f"*   **Trạng thái ENSO (NOAA):** {weather_data.get('long_term', {}).get('enso_status', 'N/A')}\n"
        
        vn_map = {"ZC": "Ngo", "ZW": "Lua mi", "ZS": "Dau tuong"}
        search_kw = vn_map.get(code, code)
        
        for reg_name, reg_data in weather_data["regions"].items():
            if search_kw.lower() in reg_data.get("desc", "").lower():
                weather_html += f"*   **{reg_name} ({reg_data.get('desc')}):** {reg_data.get('risk_assessment', 'Binh thuong')} (Rain: {reg_data.get('total_3d_rain_mm', 0)}mm | Max Temp: {reg_data.get('max_temp_C', 0)}C)\n"
    if not weather_html:
        weather_html = f"*   **Trạng thái ENSO (Chung):** {f_data.get('weather_long_term', {}).get('latest', 'La Nina transition')}\n"
        weather_html += f"*   **Thời tiết Nội địa Mỹ ({code}):** {f_data.get('short_term_weather', '')}\n"
        weather_html += f"*   **Biện chứng thời tiết ({code}):** {f_data.get('weather', {}).get('action', '')}\n"

    # Assemble section
    section = f"""
## {emoji} BÁO CÁO MÃ {code} ({name_vn.upper()}) — HỒ SƠ ĐỘC LẬP | PHIÊN CHỐT {date_str}

### A. Tóm tắt Nhanh & Bias Tổng Hợp Hôm Nay

| Khung thời gian | Xu hướng | Trạng thái kỹ thuật / Logic | Vai trò thực chiến |
| :---: | :---: | :--- | :--- |
| **Dài hạn (Xu hướng chính)** | 🐂 **Tăng (Bullish)** | La Niña rủi ro vĩ mô | Định hướng gom DCA dài hạn |
| **Trung hạn** | {medium_trend_label} | {medium_trend_logic} | Giao dịch Swing trading biên độ |
| **Ngắn hạn** | {short_trend_label} | {short_trend_logic} | Canh vào lệnh ngắn hạn (Intraday) |

*   **Giá Chốt Phiên (Close):** {data.get('close', 0):.2f} cents | **Dự báo Chốt Phiên:** **`{pred_close:.2f} cents`** ({pred_chg:+.2f}).
*   **Thanh khoản phiên chốt:** Volume: **`{today_vol:,.0f}`** (Chênh lệch: **`{today_vol - prev_vol:+,.0f}`**) | OI: **`{today_oi:,.0f}`** (Chênh lệch: **`{today_oi - prev_oi:+,.0f}`**)
*   **Mô hình nến H1:** **`{candle}`**
*   **Dòng tiền (Volume + OI):** **`{liq_trend}`**
*   **Đánh giá xu hướng kết hợp:** {comb_trend}

---

### B. Bối Cảnh Vĩ Mô & Dòng Tiền COT (Smart Money Matrix)
*(Dữ liệu chung đồng bộ tự động từ `macro_tracker.py`)*

{macro_html}

{cot_html}

---

### C. Phân Tích Kỹ Thuật H1/M15 (HĐ {act_code})
*   **Chỉ báo EMA H1:** `EMA_21` ({data.get('ema_21', 0):.2f}) {'<' if data.get('ema_21', 0) < data.get('ema_50', 0) else '>'} `EMA_50` ({data.get('ema_50', 0):.2f}).
*   **Động lượng & Dao động:** RSI (14) = **`{data.get('rsi', 0):.2f}`** | ATR (14) = **`{data.get('atr', 0):.2f}`** cents | Volatility = **`{data.get('volatility', 0):.2f} cents`**.
*   **Vùng cản Pivot:** Hỗ trợ S1: **`{data.get('s1', 0):.2f}`** | S2: **`{data.get('s2', 0):.2f}`** || Kháng cự R1: **`{data.get('r1', 0):.2f}`** | R2: **`{data.get('r2', 0):.2f}`**

---

### D. Cơ Bản, Tồn Kho USDA & Xuất Khẩu (Export Sales)

{fund_html}
*   **Export Sales (Báo Cáo Mới Nhất):** {(export_data or {}).get('status', 'Chờ cập nhật từ esrd1.html (CSV)')}

---

### E. Thời Tiết & Mùa Vụ (Tự động từ Open-Meteo / NOAA)
{weather_html}

---

### F. Khuyến Nghị Giao Dịch Chuyên Sâu ({code})

*   🚀 **{intra_label} (Ngắn hạn - HĐ {act_code}):**
    *   *Chiến lược:* Giao dịch chớp nhoáng theo biên độ H1.
    *   *Thiết lập:* Entry: **`{intra_entry}`** | SL: **`{intra_sl}`** | TP: `{intra_tp1}` / `{intra_tp2}`.
*   🚀 **Trung hạn (Swing Trades - HĐ {sw_code}):**
    *   *Long:* Entry: **`{swing_long_entry}`** | SL: **`{swing_long_sl}`** | TP: **`{swing_long_tp}`**.
    *   *Short:* Entry: **`{swing_short_entry}`** | SL: **`{swing_short_sl}`** | TP: **`{swing_short_tp}`**.
*   🚀 **{dca_label} (Dài hạn - HĐ {dca_code}):**
    *   *Chiến lược:* Mua tích lũy phòng thủ rủi ro địa chính trị và thời tiết vĩ mô.
    *   *Thiết lập:* Entry gom: **`{dca_entry}`**

---

### G. 🤖 Dự Báo Future Chart AI (Simulation 5 Ngày)
{fc_html}

=====================================================================================

"""
    return section
