import requests
def test_api():
    base = "https://apps.fas.usda.gov/OpenData/api/esr"
    headers = {"API_KEY": "vmHWTJlbC6VseSH2K64NTcXq2EqIgQeZv1hUx28B", "Accept": "application/json"}
    
    endpoints = [
        "/commodities",
        "/regions",
        "/exportsales/commodity/101",
        "/exportsales/commodity/201",
        "/countries"
    ]
    
    for ep in endpoints:
        print(f"Testing {ep}...")
        res = requests.get(base + ep, headers=headers, timeout=15)
        print("Status:", res.status_code)
        if res.status_code == 200:
            print("Data:", str(res.json())[:200])
test_api()
