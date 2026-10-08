with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"Nhập thủ công"', '"Dữ liệu Chuyên gia"')

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
