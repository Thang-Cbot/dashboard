import requests

token = "8723627742:AAEpZFbfd8RSOGi9jxoh2tKQ8TdFViXivc0"

r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 10, "timeout": 3},
    timeout=8
)
data = r.json()
updates = data.get("result", [])
print(f"So updates dang cho xu ly: {len(updates)}")
for u in updates:
    uid = u.get("update_id")
    if "callback_query" in u:
        cb = u["callback_query"]
        print(f"  [{uid}] CALLBACK: data={cb.get('data')} | from={cb['from'].get('username')}")
    elif "message" in u:
        msg = u["message"]
        print(f"  [{uid}] MESSAGE: text={msg.get('text','')[:40]}")
    else:
        print(f"  [{uid}] other: {list(u.keys())}")
