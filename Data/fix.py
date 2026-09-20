with open('pages/6_MuaVu.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('""" + render_top_badges() + """', '{render_top_badges()}')
content = content.replace('""" + render_forecast_3m() + """', '{render_forecast_3m()}')

with open('pages/6_MuaVu.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed successfully')
