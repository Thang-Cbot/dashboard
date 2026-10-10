import re

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any weird replacement characters with ¢
content = content.replace('', '¢')

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed cent symbols!")
