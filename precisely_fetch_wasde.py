import os
import time
import datetime
import urllib.request
import re

def fetch_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def download_file(url, save_path):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            with open(save_path, 'wb') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    out_dir = "Daily Reports"
    os.makedirs(out_dir, exist_ok=True)
    status_file = os.path.join(out_dir, "wasde_status.txt")
    raw_file = os.path.join(out_dir, "wasde_raw.txt")
    
    with open(status_file, "w") as f:
        f.write("RUNNING")
        
    print("Precisely Fetch WASDE started...")
    
    # Target time: 23:00:00 VN time on June 11, 2026.
    # That is 16:00:00 UTC.
    # Let's wait until 23:00:00 VN time (16:00:00 UTC) minus 2 seconds.
    target_utc_hour = 16
    target_utc_minute = 0
    target_utc_second = 0
    
    # Precise sleep loop
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        # Check if we are on June 11, 2026 (or just check the hour/minute/second to be safe)
        # If we are before 16:00:00 UTC, sleep
        if now.hour < target_utc_hour or (now.hour == target_utc_hour and now.minute == target_utc_minute and now.second < target_utc_second):
            time.sleep(1)
        else:
            break
            
    print("Reached target time! Starting polling...")
    
    # Polling loop (checks every 0.5 seconds for up to 60 seconds)
    landing_url = "https://www.usda.gov/oce/commodity/wasde"
    guesses = [
        "https://www.usda.gov/oce/commodity/wasde/wasde061126.txt",
        "https://www.usda.gov/oce/commodity/wasde/wasde06112026.txt"
    ]
    
    success = False
    for attempt in range(600): # 600 attempts * 0.5s = 300 seconds (5 minutes)
        print(f"Attempt {attempt+1}...")
        
        # 1. Try landing page scraping
        html = fetch_url(landing_url)
        if html:
            # Find all links ending in .txt containing wasde
            links = re.findall(r'href=["\'](.*?wasde.*?\.txt)["\']', html, re.IGNORECASE)
            for link in links:
                # We expect June 2026 report link (containing '06' and '26' or '2026')
                if ('06' in link) and ('26' in link or '2026' in link) and ('11' in link):
                    # Resolve relative link
                    full_url = link
                    if link.startswith('/'):
                        full_url = "https://www.usda.gov" + link
                    elif not link.startswith('http'):
                        full_url = "https://www.usda.gov/oce/commodity/wasde/" + link
                        
                    print(f"Found match on page: {full_url}. Downloading...")
                    if download_file(full_url, raw_file):
                        success = True
                        break
            if success:
                break
                
        # 2. Try direct URL guesses as fallback
        for guess in guesses:
            print(f"Trying guess: {guess}")
            # Try a quick HEAD request or direct download
            if download_file(guess, raw_file):
                print(f"Direct download success: {guess}")
                success = True
                break
        if success:
            break
            
        time.sleep(0.5)
        
    if success:
        with open(status_file, "w") as f:
            f.write("SUCCESS")
        print("WASDE report successfully downloaded.")
    else:
        with open(status_file, "w") as f:
            f.write("FAILED")
        print("WASDE report download failed after 60 seconds.")

if __name__ == "__main__":
    main()
