import json
import urllib.request
import urllib.error
from decouple import config

TOKEN = config("TELEGRAM_BOT_TOKEN", default=None)
if not TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env or environment")
    exit(1)

URL = f"https://api.telegram.org/bot{TOKEN}/createInvoiceLink"

def test_invoice():
    payload = {
        "title": "Test 10 Coins",
        "description": "Buy 10 coins",
        "payload": "test_10",
        "currency": "XTR",
        "prices": [
            {"label": "10 Coins", "amount": 10}
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(URL, data=data, headers=headers, method='POST')

    print(f"Sending request to {URL}...")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = response.read().decode('utf-8')
            print("\n✅ Success!")
            print(json.dumps(json.loads(res_data), indent=2))
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_invoice()
