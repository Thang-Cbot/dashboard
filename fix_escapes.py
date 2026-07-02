import os

file_path = r"c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot\run_pro_plus.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all occurrences of literal \\n inside the string definitions with \n
content = content.replace(r'**{bias:+.2f}***\\n"', r'**{bias:+.2f}***\n"')
content = content.replace(r'bias_explanation})*\\n\\n"', r'bias_explanation})*\n\n"')
content = content.replace(r'Giá Đóng | Thay đổi |\\n"', r'Giá Đóng | Thay đổi |\n"')
content = content.replace(r':---: | :---: |\\n"', r':---: | :---: |\n"')
content = content.replace(r'**{chg_str}¢** |\\n"', r'**{chg_str}¢** |\n"')

content = content.replace(r'| Kịch bản dự báo |\\n"', r'| Kịch bản dự báo |\n"')
content = content.replace(r':---: | :--- |\\n"', r':---: | :--- |\n"')
content = content.replace(r'| {scenario} |\\n"', r'| {scenario} |\n"')
content = content.replace(r'fc_md += "\\n"', 'fc_md += "\\n"')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
