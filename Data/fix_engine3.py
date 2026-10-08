with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"last_updated": "Thủ công"', '"last_updated": ov.get("updated_at", "Thủ công")')

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("replaced!")
