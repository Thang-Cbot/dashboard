import requests
def test_zip():
    url = "https://apps.fas.usda.gov/export-sales/high/esrData.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.head(url, headers=headers, timeout=15)
    print("Status:", res.status_code)
test_zip()
