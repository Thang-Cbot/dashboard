import glob
import re
import os

files = glob.glob('pages/*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Thay thế các page_icon="emoji" bằng page_icon="favicon.png"
    new_content = re.sub(r'page_icon=[\'"].*?[\'"]', 'page_icon="favicon.png"', content)
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
