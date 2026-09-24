with open('pages/3_News.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find the block and replace the st.markdown calls
def strip_fstring_lines(match):
    s = match.group(1)
    s = '\n'.join([line.strip() for line in s.split('\n')])
    return f"st.markdown(f'''{s}''', unsafe_allow_html=True)"

# We can just write a quick string replacement for the two st.markdown blocks we just added.
# It's safer to just rewrite the file exactly.
with open('pages/3_News.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_block = """
        # 3. Lịch sử Báo Cáo & Sắp Tới (Grain Stocks)
        st.markdown("<div style='font-size:15px; font-weight:800; color:#38bdf8; margin-top:20px; margin-bottom:10px;'>📊 Chuỗi Dữ Liệu Tồn Kho Ngũ Cốc (Grain Stocks 4 Kỳ Gần Nhất)</div>", unsafe_allow_html=True)
        
        # Load grain stocks history
        try:
            import json
            from pathlib import Path
            gs_path = Path(__file__).parent.parent / "Data" / "output" / "grain_stocks_history.json"
            with open(gs_path, 'r', encoding='utf-8') as f:
                gs_hist = json.load(f)
        except Exception as e:
            gs_hist = {"ZW": [], "ZC": []}

        next_rep = acreage_data.get("next_report")
        
        gs_tabs = st.tabs(["🌾 Lúa Mì (ZW)", "🌽 Ngô (ZC)"])
        
        for i, (tab, ticker) in enumerate(zip(gs_tabs, ["ZW", "ZC"])):
            with tab:
                data_list = gs_hist.get(ticker, [])
                if data_list:
                    # Bố cục 4 cột (thể hiện 4 quý)
                    cols = st.columns(4)
                    for col_idx, item in enumerate(data_list):
                        with cols[col_idx]:
                            bg_color = "#1e293b"
                            border_color = "#334155"
                            if item.get('status') == "Mới nhất":
                                bg_color = "rgba(34,197,94,0.1)"
                                border_color = "#22c55e"
                            
                            html_str = f'''<div style="background:{bg_color}; border:1px solid {border_color}; border-radius:8px; padding:12px; height:100%;">
<div style="font-size:12px; color:#94a3b8; font-weight:600;">{item.get('quarter')}</div>
<div style="font-size:11px; color:#cbd5e1; margin-bottom:8px;">Ngày BC: {item.get('report_date')}</div>
<div style="font-size:14px; font-weight:700; color:#e2e8f0;">{item.get('stocks')}</div>
<div style="font-size:12px; font-weight:600; color: #34d399;">YoY: {item.get('yoy_change')}</div>
<div style="font-size:10px; color:#fbbf24; margin-top:6px; font-style:italic;">Trạng thái: {item.get('status')}</div>
</div>'''
                            st.markdown(html_str, unsafe_allow_html=True)
                
                # Hiển thị báo cáo sắp tới ở dưới
                if next_rep:
                    html_str2 = f'''<div class="card" style="background:rgba(59,130,246,0.1); border-color:#3b82f6; margin-top:16px;">
<div style="font-size:13px; color:#93c5fd; font-weight:700;">📅 ĐANG CHỜ BÁO CÁO MỚI: {next_rep.get('name')}</div>
<div style="font-size:15px; color:#e2e8f0; font-weight:700; margin:4px 0;">Thời gian công bố: {next_rep.get('publish_vn')}</div>
<div style="font-size:13px; color:#cbd5e1;">{next_rep.get('description')}</div>
<div style="font-size:13px; color:#f87171; font-weight:600; margin-top:4px;">⚠️ {next_rep.get('impact')}</div>
</div>'''
                    st.markdown(html_str2, unsafe_allow_html=True)
"""

content = "".join(lines[:598]) + new_block + "".join(lines[646:])

with open('pages/3_News.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated 3_News.py without indentation successfully')
