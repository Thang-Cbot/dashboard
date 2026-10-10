import json
macro_data = json.load(open('Data/output/macro_data.json', encoding='utf-8'))
o_val = macro_data['brent']['price']
d_val = macro_data['dxy']['price']

# find f8 score
try:
    macro_zw = json.load(open('Data/output/macro_scores_zw.json', encoding='utf-8'))
    f8 = macro_zw['breakdown']['F8']['score_1_to_10']
except:
    f8 = 5

print(f"Oil: {o_val}, DXY: {d_val}, F8: {f8}")

fv = 520 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + f8*5.0
print(f"Code FV: {fv}, Zone: {fv-15:.0f} - {fv+15:.0f}")

fv_user = 550 + (o_val - 70)*2.0 + (100 - d_val)*5.0 + f8*5.0
print(f"User FV: {fv_user}, Zone: {fv_user-15:.0f} - {fv_user+15:.0f}")
