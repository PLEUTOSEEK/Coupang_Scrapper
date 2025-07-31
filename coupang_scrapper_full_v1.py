import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime

rootPath = os.path.dirname(os.path.abspath(__file__))


def get_current_date_mdy():
    """
    Returns the current date formatted as M/D/YYYY (e.g., 7/30/2025).

    Returns:
        str: Current date in 'M/D/YYYY' format.
    """
    now = datetime.now()
    return f"{now.month}/{now.day}/{now.year}"

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
  'Cookie': 'PCID=17537999749610774344667; bm_s=YAAQC8gwF8t2tVWYAQAAaeGfVgNa37aCiCUSS2kWZQ9VVAxylJET8PseDEA9wwKftdEVTds8u255V+Jnqj43bWj3Uhb0UfD3glTEmtNq25goohggVSD9DrbsLmUejcds74UaHUwyKXa1SLvzKHWTXbR8jbc93l1f1ooTXOKDsRlCRkHmyTXrpf6hCUPoDeK5VgH66sGBFppFhbU262+LJ1ZOnqyBe3XzrDeZCUjTvwuRIvyvJLK0F4ykFbWkTGFLzAZjWky/efUiA16l5O8AKxAkinTKbhUeU3SQ28ZCqmpB1Oaa+inAuwQ15uxfgj5L7Z9Mbj5+5JnIP1oH1zZRel3xj73V11sbfnKcmdks/9Pc0D9zl7zAP7pY1zhGRwkP2etb2FgB5AuMzhaknVBH+bzwJujLY8vZ8ZNYiLq40Jfm2/QpOf1XwA3DyCSfASfcBf0lDuDqw3ah9lCA9fYFXPw1b1Abld2OAw0gFOTN0FE1dtgZUUvmFYI2jcumq8iw31gOGy2PAyjdIMOBxSIN2dUNkGRjurRtAZen++kETk7ShR9eTQqJ; bm_ss=ab8e18ef4e; bm_sz=C8D56E2B9EF1D5E4C9C9461DB365BA35~YAAQC8gwF8x2tVWYAQAAaeGfVhzPgU8+l3IpMYnQQBPAPn2uBlj73BuYSXNpTGH92qmnrRPjeb8lT48nGBQ1XF0Xb3e9N23jYcgl9DHRULbr5/2jFTCLUby/wGWsYVXiXzEsyP5OvCVm//gnKvB3rGKQWyDKHznXTd0ckR7XqxG0A/W2rSTHDPY+WDEG/VGovbMEiWt7Bc5CgoLtnYBTlx6TGHVj/Lv1WGCCKwG9ABzNj4dycqkO42IAZ97TntPpJZe22DSJyzoyOQ9PUQ6tcO2nsjIadXYUvn/3jjGt9XKGqxgeO5LIaoJQO3Iqpqud5RctlU6RZKLF3RHRBpun3II7oXxEZFzvXAIUjS6e~3556408~4342081; x-coupang-accept-language=ko-KR; x-coupang-target-market=KR'
}

def extract_data(params):
    url = "https://www.coupang.com/next-api/products/vendor-items"

    # params = {
    #     'productId': '8230650647',
    #     'vendorItemId': '87687654341',
    #     'landingItemId': '23687652709',
    #     'landingProductId': '8230650647',
    #     'landingVendorItemId': '87687654341',
    #     'defaultSelection': '',
    #     'deliveryToggle': 'true'
    # }

    response = requests.request("GET", url, headers=headers, params=params)

    json_data = json.loads(response.text)

    return json_data

def extract_rating(productID):
    url = "https://www.coupang.com/next-api/review"

    params = {
        'productId': productID,
        'page': 1,
        'size': 10,
        'sortBy': 'ORDER_SCORE_ASC',
        'ratingSummary': 'true',
        'ratings': '',
        'market': ''
    }

    response = requests.request("GET", url, headers=headers, params=params)

    json_data = json.loads(response.text)

    return json_data

def extract_coupang_params(url):
    """
    Extracts product-related parameters from a Coupang product URL.

    Parameters:
        url (str): The Coupang product URL.

    Returns:
        dict: Dictionary with required params.
    """
    parsed_url = urlparse(url)
    
    # Extract path parts to get productId
    path_parts = parsed_url.path.strip('/').split('/')
    product_id = path_parts[-1] if path_parts[-2] == 'products' else None

    # Extract query parameters
    query_params = parse_qs(parsed_url.query)
    vendor_item_id = query_params.get('vendorItemId', [''])[0]
    landing_item_id = query_params.get('itemId', [''])[0]
    
    # Construct the expected param object
    params = {
        'productId': product_id,
        'vendorItemId': vendor_item_id,
        'landingItemId': landing_item_id,
        'landingProductId': product_id,
        'landingVendorItemId': vendor_item_id,
        'defaultSelection': '',
        'deliveryToggle': 'true'
    }

    return params

def load_all_json_from_folder(folder_path):
    """
    Loops through all JSON files in a folder and loads them into Python objects.

    Parameters:
        folder_path (str): Path to the folder containing JSON files.

    Returns:
        list: A list of data from each JSON file (each item is typically a list of dicts).
    """
    
    # Loop through files in folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    extracted_data = []

                    for url_obj in data:
                        try:
                          input_params = extract_coupang_params(url_obj['URL'])

                          extracted_product = extract_data(input_params)
                          
                          extracted_product["rating"] = extract_rating(input_params["productId"])
                          extracted_product["input_obj"] = url_obj
                          extracted_product["thomas_error"] = False
                          extracted_product["review_date"] = get_current_date_mdy()

                          extracted_data.append(extracted_product)
                        except:
                          extracted_data.append({
                              'input_obj': url_obj,
                              'thomas_error': True
                              })
                          
                    save_path = os.path.join(rootPath, 'JSONs',  f'coupang_data_{uuid.uuid1()}.json')
                    with open(save_path, 'w') as f:
                        json.dump(extracted_data, f, indent=4)

                    print(f"Saved {filename} to {save_path}")

                shutil.move(file_path, os.path.join(rootPath, "URLs_Converted", filename))

            except Exception as e:
                print(f"Failed to load {filename}: {e}")

json_data_list = load_all_json_from_folder('URLs')