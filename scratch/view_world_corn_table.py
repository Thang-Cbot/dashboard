import requests

url = "https://esmis.nal.usda.gov/sites/default/release-files/795903/wasde0526v2.txt"
try:
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        text = res.text
        pos = text.find("World Corn Supply and Use")
        if pos != -1:
            print("=== Found World Corn Supply and Use Table ===")
            print(text[pos:pos+3000])
except Exception as e:
    print("Error:", e)
