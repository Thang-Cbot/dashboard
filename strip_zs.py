import re

with open('run_pro_plus.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove ZS variables section
content = re.sub(r'# ZS \(Đậu tương\) đã được gỡ bỏ khỏi hệ thống\s*', '', content)
content = re.sub(r'\s*zs_act_code = [^\n]+\n\s*zs_sw_code = [^\n]+\n\s*zs_dca_code = [^\n]+\n', '', content)
content = re.sub(r'\s*zs_act_name = [^\n]+\n\s*zs_sw_name = [^\n]+\n\s*zs_dca_name = [^\n]+\n', '', content)

# Remove ZS assignment from data_zs
content = re.sub(r'\s*zs = data_zs\["active"\]\n\s*zs_sw = data_zs\["swing"\]\n\s*zs_dc = data_zs\["dca"\]\n', '', content)

# Remove pred close
content = re.sub(r'\s*zs_pred_close, zs_pred_chg = predict_closing_price\("ZS", zs, brent_pct, dxy_pct, fund\)\n', '', content)

# Remove intra entries
content = re.sub(r'\s*zs_intra_entry = [^\n]+\n\s*zs_intra_sl = [^\n]+\n\s*zs_intra_tp1 = [^\n]+\n\s*zs_intra_tp2 = [^\n]+\n', '', content)
content = re.sub(r'\s*zs_swing_long_entry = [^\n]+\n\s*zs_swing_long_sl = [^\n]+\n\s*zs_swing_long_tp = [^\n]+\n\s*zs_swing_short_entry = [^\n]+\n\s*zs_swing_short_sl = [^\n]+\n\s*zs_swing_short_tp = [^\n]+\n', '', content)
content = re.sub(r'\s*zs_dca = [^\n]+\n', '', content)

# Remove labels
content = re.sub(r'\s*zs_intra_label = [^\n]+\n\s*zs_swing_long_label = [^\n]+\n\s*zs_swing_short_label = [^\n]+\n\s*zs_dca_label = [^\n]+\n', '', content)

# Remove trend
content = re.sub(r'\s*zs_short_trend_label, zs_short_trend_logic = [^\n]+\n\s*zs_medium_trend_label, zs_medium_trend_logic = [^\n]+\n', '', content)

# Remove section_zs build_commodity_section
content = re.sub(r'\s*section_zs = build_commodity_section\([\s\S]*?weather_data=weather_data, export_data=export_data\n\s*\)', '', content)

# Update report_content +=
content = re.sub(r'report_content \+= phan3_header \+ section_zc \+ section_zw \+ section_zs', 'report_content += phan3_header + section_zc + section_zw', content)

with open('run_pro_plus.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done stripping ZS vars from run_pro_plus.py")
