import random
import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime
import time
rootPath = os.path.dirname(os.path.abspath(__file__))
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_current_date_mdy():
    """
    Returns the current date formatted as M/D/YYYY (e.g., 7/30/2025).

    Returns:
        str: Current date in 'M/D/YYYY' format.
    """
    now = datetime.now()
    return f"{now.month}/{now.day}/{now.year}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Referer': 'https://www.coupang.com/vp/products/7790147767?itemId=21074165216&vendorItemId=89467524871&q=glo&itemsCount=36&searchId=a771eb6f1336267&rank=34&searchRank=34',
    'Cookie': 'PCID=17539803162143273098918; _fbp=fb.1.1753981126246.494816719557364037; x-coupang-target-market=KR',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers'
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

    for retry in range(3):
        try:
            response = requests.request("GET", url, headers=headers, params=params)

            json_data = json.loads(response.text)
            print("DONE")
            return json_data
        except Exception as e:
            print("Error in extract_data")
    
    return None

def extract_rating(productID, page_num=1):
    url = "https://www.coupang.com/next-api/review"

    params = {
        'productId': productID,
        'page': page_num,
        'size': 30,
        'sortBy': 'ORDER_SCORE_ASC',
        'ratingSummary': 'true',
        'ratings': '',
        'market': ''
    }

    for retry in range(3):
        # time.sleep(random.uniform(2, 4))  # 随机等待 1 到 5 秒
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"DONE {page_num}")
            return response.json()
        except Exception as e:
            print(f"Error in extract_rating page {page_num}: {e}")
    
    return None

def extract_all_ratings(productID):
    all_reviews = []

    # Step 1: Get first page and total pages
    first_page_data = extract_rating(productID, page_num=1)
    if not first_page_data:
        return []

    try:
        total_pages = first_page_data['rData']['paging']['totalPage']
        all_reviews.extend(first_page_data['rData']['paging']['contents'])
    except KeyError:
        print("Invalid structure in first page")
        return []
    total_pages = 10
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for start_page in range(2, total_pages + 1):
            futures.append(executor.submit(extract_rating, productID, start_page))

        for future in as_completed(futures):
            data = future.result()
            if data:
                try:
                    contents = data['rData']['paging']['contents']
                    all_reviews.extend(contents)
                except KeyError:
                    continue

    first_page_data['rData']['paging']['contents'] = all_reviews
    return first_page_data



def extract_coupang_params(url):
    """
    Extracts product-related parameters from a Coupang product URL.

    Parameters:
        url (str): The Coupang product URL.

    Returns:
        dict: Dictionary with required params.
    """

    try:
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

    except Exception as e:
        print("error in extract_coupang_params")

    return None

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

                    print(f"processing {file_path}")
                    data = json.load(f)

                    extracted_data = []

                    for url_obj in data:
                        # time.sleep(random.uniform(3, 5))  # 随机等待 1 到 5 秒
                        try:
                            input_params = extract_coupang_params(url_obj['URL'])
                            print(input_params)

                            if input_params is not None:
                                
                                extracted_product = extract_data(input_params)
                                extracted_product["input_obj"] = url_obj
                                extracted_product["status"] = "normal"
                                extracted_product["thomas_error"] = False
                                extracted_product["rating"] = None
                                if extracted_product is not None:

                                    if (extracted_product["almostSoldOut"] is None and 
                                        extracted_product["easePayment"] is None and 
                                        extracted_product["quantityBase"] is None and 
                                        extracted_product["memberInfo"] is None and 
                                        extracted_product["roleCode"] is None):

                                        if extracted_product["itemName"] is None:
                                            # NA
                                            extracted_product["status"] = "not applicable"
                                            extracted_data.append(extracted_product)
                                            continue
                                            
                                        else:
                                            # out of stock
                                            extracted_product["status"] = "out of stock"

                                    extracted_product["rating"] = extract_all_ratings(input_params["productId"])
                                    extracted_data.append(extracted_product)
                                    continue

                            print("Come to here else")

                            extracted_data.append({
                                'input_obj': url_obj,
                                'thomas_error': True
                                })
                        except Exception as e:
                          print(e)
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