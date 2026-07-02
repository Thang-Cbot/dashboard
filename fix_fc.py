import os
import re

file_path = r"c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\run_pro_plus.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to capture everything from # Load Future Chart Output down to report_content += fc_md
pattern = re.compile(r'        # Load Future Chart Output.*?        report_content \+= fc_md', re.DOTALL)

new_text = r'''        # Load Future Chart Output
        fc_json_path = os.path.join(os.path.dirname(__file__), "Future chart", "future_chart_data.json")
        with open(fc_json_path, "r", encoding="utf-8") as f:
            fc_data = json.load(f)
            
        fc_md = "\n## 🤖 4. DỰ BÁO FUTURE CHART (AI SIMULATION 5 NGÀY)\n"
        
        # Determine if it's the old format or new format
        if "meta" in fc_data and "daily_summary" in fc_data:
            # OLD FORMAT (just ZW)
            meta = fc_data.get("meta", {})
            model_inputs = meta.get("model_inputs", {})
            bias = model_inputs.get("composite_bias", 0.0)
            detailed = model_inputs.get("detailed_scores", {})
            contract = meta.get("contract", "ZW")
            
            bias_components = [f"{k} ({v:+.1f})" for k, v in detailed.items()]
            bias_explanation = " + ".join(bias_components) if bias_components else "Chưa có thông tin"
                
            fc_md += f"*Mã hợp đồng: {contract} | Điểm Bias Tổng Hợp: **{bias:+.2f}***\n"
            fc_md += f"*(Tổng điểm = {bias_explanation})*\n\n"
            fc_md += "| Ngày giao dịch | Giá Mở | Đỉnh (High) | Đáy (Low) | Giá Đóng | Thay đổi |\n"
            fc_md += "| :--- | :---: | :---: | :---: | :---: | :---: |\n"
            
            daily_summary = fc_data.get("daily_summary", {})
            for day_str, day_data in daily_summary.items():
                chg = day_data['close'] - day_data['open']
                chg_str = f"{chg:+.2f}" if chg != 0 else "0.00"
                fc_md += f"| **{day_str}** | {day_data['open']:.2f} | {day_data['high']:.2f} | {day_data['low']:.2f} | **{day_data['close']:.2f}** | **{chg_str}¢** |\n"
        else:
            # NEW FORMAT (ZC, ZW, ZS)
            for code in ["ZC", "ZW", "ZS"]:
                if code not in fc_data:
                    continue
                c_data = fc_data[code]
                meta = c_data.get("meta", {})
                bias = meta.get("composite_bias", 0.0)
                detailed = meta.get("detailed_scores", {})
                contract = meta.get("symbol", code)
                
                bias_components = [f"{k} ({v:+.1f})" for k, v in detailed.items()]
                bias_explanation = " + ".join(bias_components) if bias_components else "Chưa có thông tin"
                    
                fc_md += f"### Kịch bản AI Mô phỏng - Mã {contract} | Điểm Bias: **{bias:+.2f}**\n"
                fc_md += f"*(Tổng điểm = {bias_explanation})*\n\n"
                fc_md += "| Ngày giao dịch | Giá Mở | Đỉnh (High) | Đáy (Low) | Giá Đóng | Thay đổi | Kịch bản dự báo |\n"
                fc_md += "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n"
                
                daily_summary = c_data.get("daily_summary", {})
                for day_str, day_data in daily_summary.items():
                    chg = day_data['close'] - day_data['open']
                    chg_str = f"{chg:+.2f}" if chg != 0 else "0.00"
                    scenario = day_data.get('scenario', '')
                    fc_md += f"| **{day_str}** | {day_data['open']:.2f} | {day_data['high']:.2f} | {day_data['low']:.2f} | **{day_data['close']:.2f}** | **{chg_str}¢** | {scenario} |\n"
                
                fc_md += "\n"
        
        report_content += fc_md'''

new_content = pattern.sub(new_text, content)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
