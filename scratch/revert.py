import json

with open('Data/macro_weights.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['dca_targets']['ZW']['zone1'] = "550 - 580¢"

with open('Data/macro_weights.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"650 - 680', '"550 - 580')
content = content.replace('Cơ sở định giá (Cố định): Tồn kho hụt 18.5% YoY | Dầu > 90$ | DXY ~ 102', 'Cơ sở định giá (Cố định): War Premium | Dầu thô | DXY')

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Reverted to 550-580.")
