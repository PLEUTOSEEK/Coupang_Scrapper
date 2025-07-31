import requests
import json

url = "https://shop.coupang.com/api/v2/store/individualInfo/products"

headers = {
  'accept': '*/*',
  'accept-language': 'en-US,en;q=0.9',
  'cache-control': 'no-cache',
  'pragma': 'no-cache',
  'priority': 'u=1, i',
  'referer': 'https://gum.criteo.com/syncframe?topUrl=shop.coupang.com&origin=onetag',
  'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-storage-access': 'active',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
  'content-type': 'application/json',
  'origin': 'https://shop.coupang.com'
  }

payload = json.dumps({
    "vendorItemIds": [
        92866985106,
        92103799229,
        92103799198,
        91342047664,
        91342047679,
        91349740407,
        90737916117,
        90737916146,
        90782768101,
        90782768096,
        90889633029,
        90133544195,
        90133544352,
        90133544363,
        88738735066,
        91801220176
    ],
    "isVIBased": True,
    "storeId": 109702,
    "vendorId": "A00054860",
    "ignoreAdultCheck": False,
    "pageType": 3
})


response = requests.request("POST", url, headers=headers, data=(payload))

json_data = json.loads(response.text)

with open('coupang.json', 'w') as f:
    json.dump(json_data, f, indent=4)
