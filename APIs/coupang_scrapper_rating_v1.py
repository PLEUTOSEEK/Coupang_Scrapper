import requests, json

url = "https://www.coupang.com/next-api/review"

params = {
    'productId': '7956783044',
    'page': 1,
    'size': 10,
    'sortBy': 'ORDER_SCORE_ASC',
    'ratingSummary': 'true',
    'ratings': '',
    'market': ''
}

headers = {
  'accept': 'application/json, text/plain, */*',
  'accept-language': 'en-US,en;q=0.9',
  'cache-control': 'no-cache',
  'pragma': 'no-cache',
  'priority': 'u=1, i',
  'referer': 'https://www.coupang.com/vp/products/7790147767?itemId=21074165218&vendorItemId=89467524879&q=glo&itemsCount=36&searchId=a771eb6f1336267&rank=34&searchRank=34',
  'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
  'Cookie': 'PCID=17537082094358422061820; _fbp=fb.1.1753708209994.507078022149609960; x-coupang-target-market=KR; x-coupang-accept-language=ko-KR; sid=efb92a1875f74fa4b3da757335dee0481ccc77ee; MARKETID=17537082094358422061820; gd1=Y; bm_mi=5DB011DF2DC010D8261F3660A283BEE6~YAAQnF5qyyAuSFaYAQAABzfBYBygOnQqASJZCwLHhSrfpCS75cG1EKdZZyp1f283rJSSr7odAeWxxEiyW9HRtZWWGYOyxodmJR/6hvhhxkC5N/3j7T7h2dX1e1nOXI04/Rs/NIUgnFoDOm6JqfkoHRRq60lY4aK18dFe2ApmxiSxPY3HepIw8Gx3jtCkDMmvt+dDRzbHze05XCm+4y5V77SaNV6NM8yhJbMyr317rN71/eyMCc2IMXdkuYWMMtev3CJa5ZmiqDl197OJ4xlFu7TnSentgy+cJgMMy5lLHd08DJ94ilj9P68QPYUczMO995ncfASksweqfaG+HMFwlneJwKYm~1;'
}

response = requests.request("GET", url, headers=headers, params=params)

json_data = json.loads(response.text)

with open('Samples/coupang_rating.json', 'w') as f:
    json.dump(json_data, f, indent=4)