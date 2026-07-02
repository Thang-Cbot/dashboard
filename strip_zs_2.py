import re

with open('run_pro_plus.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove remaining zs references in strings or dictionary outputs
content = re.sub(r'\|\s*\*\*ZS\*\*.*?\[Xem D\?u tuong \(ZS\)\][^\n]+\n', '', content)
content = re.sub(r'\|\s*\*\*ZS\*\*\s*\|.*?\|.*?\|.*?\|.*?\|.*?\n', '', content)
content = re.sub(r'\|\s*\*\*ZSX26\*\*\s*\(Soy\).*?\n', '', content)
content = re.sub(r'\*\s*\*\*D\?u tuong \(ZS\):.*?\n', '', content)
content = re.sub(r'\*\s*\*\*D\?u tuong \(Soybeans - ZSX26.*?\n', '', content)
content = re.sub(r'\*   \?\? \*\*D\?u tuong \(Soybeans\):.*?\n', '', content)
content = re.sub(r'\-\s*\*\*.*?V\?i D\?u tuong \(ZSX26\):.*?\n\s*\*.*?\n', '', content)

# Remove from dictionary mapping
content = re.sub(r'\s*"ZS":\s*\{[\s\S]*?\},', '', content)
content = re.sub(r'\s*"zs":\s*data_zs\.get\("rsi_pack", \{\}\)', '', content)
content = re.sub(r'\s*elif commodity_code == "ZS":\s*return\s*\[.*?\]', '', content)
content = re.sub(r'\s*-\s*D\?u tuong \(ZS\).*?\n', '\n', content)
content = re.sub(r'if code in \["ZC", "ZS"\]:', 'if code == "ZC":', content)
content = re.sub(r'for code in \["ZC", "ZW", "ZS"\]:', 'for code in ["ZC", "ZW"]:', content)

# Fix commas
content = re.sub(r',\s*\}', '\n            }', content)

with open('run_pro_plus.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done stripping more ZS vars from run_pro_plus.py")
