import re
with open('Data/macro_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken lines
content = content.replace("elif dxy >= 101: score = 4`n          elif dxy >= 99: score = 5`n          elif dxy >= 97: score = 6\n        elif dxy > 98: score = 8", 
"""elif dxy >= 101: score = 4
        elif dxy >= 99: score = 5
        elif dxy >= 97: score = 6
        elif dxy > 95: score = 8""")

with open('Data/macro_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
