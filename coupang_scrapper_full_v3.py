import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime

import asyncio
from playwright.async_api import async_playwright

rootPath = os.path.dirname(os.path.abspath(__file__))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Referer': 'https://www.coupang.com/vp/products/7790147767?itemId=21074165216&vendorItemId=89467524871&q=glo&itemsCount=36&searchId=a771eb6f1336267&rank=34&searchRank=34',
    'Cookie': 'PCID=17537082094358422061820; _fbp=fb.1.1753708209994.507078022149609960; x-coupang-target-market=KR',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers'
}

def get_current_date_mdy():
    """
    Returns the current date formatted as M/D/YYYY (e.g., 7/30/2025).

    Returns:
        str: Current date in 'M/D/YYYY' format.
    """
    now = datetime.now()
    return f"{now.month}/{now.day}/{now.year}"



def extract_data(params):
    return asyncio.run(_extract_data_playwright(params))

async def _extract_data_playwright(params):
    url = "https://www.coupang.com/next-api/products/vendor-items"

    for retry in range(3):
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                response = await page.request.get(url, headers=headers, params=params)
                json_data = await response.json()
                await browser.close()

                print("DONE")
                return json_data

        except Exception as e:
            print(f"Error in extract_data: {e}")

    return None

def extract_rating(productID):
    return asyncio.run(_extract_rating_playwright(productID))

async def _extract_rating_playwright(productID):
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

    for retry in range(3):
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                response = await page.request.get(url, headers=headers, params=params)
                json_data = await response.json()
                await browser.close()
                print("DONE_rating")
                return json_data

        except Exception as e:
            print(f"Error in extract_rating (attempt {retry+1}): {e}")
    
    return None

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

                                    extracted_product["rating"] = extract_rating(input_params["productId"])
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