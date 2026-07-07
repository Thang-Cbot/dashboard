import requests
def test_api():
    url = "https://apps.fas.usda.gov/OpenData/api/esr/datareleasedates"
    headers = {"API_KEY": "vmHWTJlbC6VseSH2K64NTcXq2EqIgQeZv1hUx28B"}
    print("Testing with API_KEY header...")
    res = requests.get(url, headers=headers, timeout=15)
    print("Status:", res.status_code)
    if res.status_code == 200:
        print("Success! Data:", res.text[:200])
        return

    print("Testing with X-Api-Key header...")
    headers = {"X-Api-Key": "vmHWTJlbC6VseSH2K64NTcXq2EqIgQeZv1hUx28B"}
    res = requests.get(url, headers=headers, timeout=15)
    print("Status:", res.status_code)
    if res.status_code == 200:
        print("Success! Data:", res.text[:200])

test_api()
