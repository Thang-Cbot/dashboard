import os

files_to_patch = [
    'pages/1_Overview.py',
    'pages/2_Profiles.py',
    'pages/3_News.py',
    'pages/4_Weather.py',
    'pages/5_AgriMap.py',
    'pages/5_Macro_Matrix.py',
    'pages/7_System_Logs.py',
    'app.py',
]

for fp in files_to_patch:
    try:
        content = open(fp, encoding='utf-8').read()
        new_content = content.replace('Mùa Vụ 2026', 'Mùa Vụ')
        if new_content != content:
            open(fp, 'w', encoding='utf-8').write(new_content)
            print(f'Patched: {fp}')
        else:
            print(f'No change: {fp}')
    except Exception as e:
        print(f'Skip {fp}: {e}')
print('Done')
