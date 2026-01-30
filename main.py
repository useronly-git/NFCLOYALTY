import requests
import json
import uuid

url = 'http://api.posterix.pro/v2'
headers = {'Content-Type': 'application/json'}

data = {
    "jsonrpc": "2.0",
    "method": "ListOrders",
    "params": {
        "token": "1048fbcff8b534cb83c602f652ec3c6a4d0d8807",
        "company": 1599,
        "filters": {
            "from": "1769753331",
            "till": "1769800131"
            },
    },
    "id": str(uuid.uuid4())
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(json.dumps(result, indent=2))