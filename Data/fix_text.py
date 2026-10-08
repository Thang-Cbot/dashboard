with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('f"Điểm tự đánh giá: {score}/10"', 'f"Phân tích Chuyên gia: {score}/10"')

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
