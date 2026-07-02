import re
import os

filepath = 'run_pro_plus.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'from build_sections import' not in content:
    content = content.replace('from technical_analysis import analyze_cbot_data, detect_candlestick_pattern', 'from technical_analysis import analyze_cbot_data, detect_candlestick_pattern\nfrom build_sections import build_commodity_section')

# Replace PHẦN III block
pattern = r'# PHẦN III: DỰ BÁO AI & PHÂN TÍCH KỸ THUẬT CHI TIẾT TỪNG MÃ.*?except Exception as e:\n\s*print\(f\"Error appending Future Chart: \{e\}\"\)'

replacement = '''# --- PHẦN III: INDEPENDENT COMMODITY PROFILES ---
    # Run future chart first to get data
    fc_data = {}
    try:
        import subprocess
        fc_path = os.path.join(os.path.dirname(__file__), 'Future chart', 'future_chart.py')
        subprocess.run(['python', fc_path], check=True, capture_output=True)
        fc_json_path = os.path.join(os.path.dirname(__file__), 'Future chart', 'future_chart_data.json')
        with open(fc_json_path, 'r', encoding='utf-8') as f:
            fc_data = json.load(f)
    except Exception as e:
        print(f'Future Chart error: {e}')

    phan3_header = '\\n# PHẦN III: HỒ SƠ ĐỘC LẬP TỪNG MÃ NÔNG SẢN\\n'
    phan3_header += '*Mỗi mã được phân tích hoàn toàn độc lập. Dữ liệu chung (Brent, DXY) đồng bộ tự động từ cùng một nguồn.*\\n'
    
    section_zc = build_commodity_section(
        code='ZC', emoji='🌽', name_vn='Ngô', date_str=date_str,
        data=zc, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zc_pred_close, pred_chg=zc_pred_chg,
        act_code=zc_act_code, sw_code=zc_sw_code, dca_code=zc_dca_code,
        intra_label=zc_intra_label, intra_entry=zc_intra_entry, intra_sl=zc_intra_sl,
        intra_tp1=zc_intra_tp1, intra_tp2=zc_intra_tp2,
        swing_long_label=zc_swing_long_label, swing_long_entry=zc_swing_long_entry,
        swing_long_sl=zc_swing_long_sl, swing_long_tp=zc_swing_long_tp,
        swing_short_label=zc_swing_short_label, swing_short_entry=zc_swing_short_entry,
        swing_short_sl=zc_swing_short_sl, swing_short_tp=zc_swing_short_tp,
        dca_label=zc_dca_label, dca_entry=zc_dca,
        candle=zc_candle, comb_trend=zc_comb_trend, liq_trend=zc_liq_trend, liq_logic='',
        today_vol=zc_today_vol, prev_vol=zc_prev_vol, today_oi=zc_today_oi, prev_oi=zc_prev_oi,
        today_close=zc_today_close, prev_close=zc_prev_close,
        short_trend_label=zc_short_trend_label, short_trend_logic=zc_short_trend_logic,
        medium_trend_label=zc_medium_trend_label, medium_trend_logic=zc_medium_trend_logic,
        fc_data=fc_data.get('ZC')
    )
    section_zw = build_commodity_section(
        code='ZW', emoji='🌾', name_vn='Lúa Mì', date_str=date_str,
        data=zw, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zw_pred_close, pred_chg=zw_pred_chg,
        act_code=zw_act_code, sw_code=zw_sw_code, dca_code=zw_dca_code,
        intra_label=zw_intra_label, intra_entry=zw_intra_entry, intra_sl=zw_intra_sl,
        intra_tp1=zw_intra_tp1, intra_tp2=zw_intra_tp2,
        swing_long_label=zw_swing_long_label, swing_long_entry=zw_swing_long_entry,
        swing_long_sl=zw_swing_long_sl, swing_long_tp=zw_swing_long_tp,
        swing_short_label=zw_swing_short_label, swing_short_entry=zw_swing_short_entry,
        swing_short_sl=zw_swing_short_sl, swing_short_tp=zw_swing_short_tp,
        dca_label=zw_dca_label, dca_entry=zw_dca,
        candle=zw_candle, comb_trend=zw_comb_trend, liq_trend=zw_liq_trend, liq_logic='',
        today_vol=zw_today_vol, prev_vol=zw_prev_vol, today_oi=zw_today_oi, prev_oi=zw_prev_oi,
        today_close=zw_today_close, prev_close=zw_prev_close,
        short_trend_label=zw_short_trend_label, short_trend_logic=zw_short_trend_logic,
        medium_trend_label=zw_medium_trend_label, medium_trend_logic=zw_medium_trend_logic,
        fc_data=fc_data.get('ZW')
    )
    section_zs = build_commodity_section(
        code='ZS', emoji='🌱', name_vn='Đậu Tương', date_str=date_str,
        data=zs, fund=fund, cot_data_json=cot_data_json,
        brent_price=brent_price, brent_pct=brent_pct, dxy_price=dxy_price, dxy_pct=dxy_pct,
        pred_close=zs_pred_close, pred_chg=zs_pred_chg,
        act_code=zs_act_code, sw_code=zs_sw_code, dca_code=zs_dca_code,
        intra_label=zs_intra_label, intra_entry=zs_intra_entry, intra_sl=zs_intra_sl,
        intra_tp1=zs_intra_tp1, intra_tp2=zs_intra_tp2,
        swing_long_label=zs_swing_long_label, swing_long_entry=zs_swing_long_entry,
        swing_long_sl=zs_swing_long_sl, swing_long_tp=zs_swing_long_tp,
        swing_short_label=zs_swing_short_label, swing_short_entry=zs_swing_short_entry,
        swing_short_sl=zs_swing_short_sl, swing_short_tp=zs_swing_short_tp,
        dca_label=zs_dca_label, dca_entry=zs_dca,
        candle=zs_candle, comb_trend=zs_comb_trend, liq_trend=zs_liq_trend, liq_logic='',
        today_vol=zs_today_vol, prev_vol=zs_prev_vol, today_oi=zs_today_oi, prev_oi=zs_prev_oi,
        today_close=zs_today_close, prev_close=zs_prev_close,
        short_trend_label=zs_short_trend_label, short_trend_logic=zs_short_trend_logic,
        medium_trend_label=zs_medium_trend_label, medium_trend_logic=zs_medium_trend_logic,
        fc_data=fc_data.get('ZS')
    )
    
    report_content += phan3_header + section_zc + section_zw + section_zs'''

new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
if count > 0:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Replaced successfully. Occurrences: {count}')
else:
    print('Pattern not found')
