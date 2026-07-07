import requests
def search_esmis():
    print("Fetching publications from ESMIS...")
    res = requests.get("https://esmis.nal.usda.gov/api/v1/publications", timeout=15)
    if res.status_code == 200:
        pubs = res.json()
        for p in pubs:
            if "Export" in p.get("title", "") and "Sales" in p.get("title", ""):
                print("Found:", p.get("title"), p.get("pubId"))
search_esmis()
