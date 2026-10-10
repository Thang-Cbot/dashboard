import json

with open('Data/macro_weights.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

with open('Data/macro_weights.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"550 - 580', '"650 - 680')

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed BOM and fallback!")
