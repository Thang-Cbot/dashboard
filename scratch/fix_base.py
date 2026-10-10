with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("fv = 520 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + war_premium", "fv = 550 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + war_premium")

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated base to 550")
