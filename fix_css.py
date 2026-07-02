import glob
import os

old_str = '[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 220px !important; max-width: 220px !important; width: 220px !important; }
[data-testid="stSidebarNav"] { display: none !important; }'
new_str = '''[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d45; min-width: 220px !important; max-width: 220px !important; width: 220px !important; }
[data-testid="stSidebarNav"] { display: none !important; }'''

for file in glob.glob('*.py') + glob.glob('pages/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_str in content:
        content = content.replace(old_str, new_str)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', file)
    else:
        # Check if the new_str is already there
        if "stSidebarNav" not in content:
            print("String not found in", file)
