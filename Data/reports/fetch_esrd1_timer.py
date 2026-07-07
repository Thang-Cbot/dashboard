import time
from datetime import datetime, timezone, timedelta
import urllib.request
import os

# VN timezone UTC+7
vn_tz = timezone(timedelta(hours=7))

now = datetime.now(vn_tz)
# Set target time to today at 22:00:03
target = now.replace(hour=22, minute=0, second=3, microsecond=0)

if now > target:
    print('Target time has already passed for today.')
else:
    wait_seconds = (target - now).total_seconds()
    print(f'Sleeping for {wait_seconds} seconds until {target}...')
    time.sleep(wait_seconds)

    print('Awake! Fetching esrd1.html...')
    try:
        req = urllib.request.Request('https://apps.fas.usda.gov/export-sales/esrd1.html', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, timeout=30).read()
        out_path = os.path.join(os.path.dirname(__file__), 'esrd1_latest.html')
        with open(out_path, 'wb') as f:
            f.write(html)
        print(f'Successfully saved to {out_path}')
    except Exception as e:
        print(f'Failed to fetch: {e}')
        # Fallback to saving error
        out_path = os.path.join(os.path.dirname(__file__), 'esrd1_error.txt')
        with open(out_path, 'w') as f:
            f.write(str(e))
