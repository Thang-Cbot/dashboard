import re
with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = """if dxy >= 104: score = 2
        elif dxy >= 102: score = 3
        elif dxy >= 100.5: score = 4
        elif dxy >= 99: score = 5
        elif dxy >= 97: score = 7
        else: score = 8"""

content = re.sub(r'if dxy > 105: score = 2.*?elif dxy > 95: score = 8', new_logic, content, flags=re.DOTALL)

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
