import random
import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN
import threading

vpn_lock = threading.Lock()
rootPath = os.path.dirname(os.path.abspath(__file__))
instructions = initialize_VPN(area_input=["South Korea"]) # ,Brazil,Croatia,Denmark,
vpn_rotated = False
stop_event = threading.Event()

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
    'Cookie': 'PCID=17537082094358422061820; _fbp=fb.1.1753708209994.507078022149609960; x-coupang-target-market=KR',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers'
}

def extract_data_with_selenium(params):
    global vpn_rotated
    url = f"https://www.coupang.com/next-api/products/vendor-items?productId={params['productId']}&vendorItemId={params['vendorItemId']}&landingItemId={params['landingItemId']}&landingProductId={params['landingProductId']}&landingVendorItemId={params['landingVendorItemId']}&defaultSelection={params['defaultSelection']}&deliveryToggle={params['deliveryToggle']}"

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        for retry in range(3):
            try:
                driver.get(url)
                time.sleep(4)
                
                # Parse the page source with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Find the pre tag containing JSON data
                pre_tag = soup.find('pre')
                
                if pre_tag:
                    # Extract the text content and parse as JSON
                    json_data = json.loads(pre_tag.text)
                    print("Successfully extracted JSON data:")
                    vpn_rotated = False
                    return json_data
                else:
                    print("No <pre> tag found in the response")
                    print("Page source:", driver.page_source)
                    with vpn_lock:
                        if not vpn_rotated:
                            vpn_rotated = True
                            rotate_VPN(instructions)
                            time.sleep(20)
                        else:
                            print(f"Skipping VPN rotation — already handled")
                    # return None

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print("Raw content:", pre_tag.text if pre_tag else "No pre tag")
                return None
            except Exception as e:
                print(f"Attempt {retry + 1} failed: {str(e)}")
                with vpn_lock:
                    if not vpn_rotated:
                        vpn_rotated = True
                        rotate_VPN(instructions)
                        time.sleep(20)
                    else:
                        print(f"Skipping VPN rotation — already handled")
    
    finally:
        driver.quit()
    
    return None


def extract_all_ratings_selenium(productID):
    stop_event.clear() 
    all_reviews = []

    # Step 1: Get first page to determine totalPages
    first_page_data = extract_rating_with_selenium(productID, page_num=1)
    if not first_page_data:
        return []

    try:
        total_pages = first_page_data['rData']['paging']['totalPage']
        all_reviews.extend(first_page_data['rData']['paging']['contents'])
    except KeyError:
        print("Invalid structure in first page")
        return []

    def extract_rating_with_selenium_wrapped(productID, page_num):
        if stop_event.is_set():
            print(f"[Page {page_num}] Skipped due to early stop")
            return None

        data = extract_rating_with_selenium(productID, page_num)

        if data:
            try:
                contents = data['rData']['paging']['contents']
                if not contents:
                    print(f"[Page {page_num}] Empty contents — setting stop event")
                    stop_event.set()
            except KeyError:
                print(f"[Page {page_num}] Invalid data format")

        return data

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for start_page in range(2, total_pages + 1, 3):
            for page_num in range(start_page, min(start_page + 3, total_pages + 1)):
                if stop_event.is_set():
                    break
                futures.append(executor.submit(extract_rating_with_selenium_wrapped, productID, page_num))

        for future in as_completed(futures):
            data = future.result()
            if data:
                try:
                    contents = data['rData']['paging']['contents']
                    all_reviews.extend(contents)
                except KeyError:
                    continue

    # Replace contents in first_page_data with all combined reviews
    first_page_data['rData']['paging']['contents'] = all_reviews
    return first_page_data


def extract_rating_with_selenium(productID, page_num=1):
    global vpn_rotated

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

    # Construct full URL
    query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v != ''])
    full_url = f"{url}?{query_string}"

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless=new")  # Uncomment if needed

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(full_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        pre_tag = soup.find('pre')

        if pre_tag:
            try:
                json_data = json.loads(pre_tag.text)
                print(f"[Page {page_num}] Successfully extracted")
                vpn_rotated = False
                return json_data
            except json.JSONDecodeError as e:
                print(f"[Page {page_num}] JSON decode error: {e}")
        else:
            print(f"[Page {page_num}] No <pre> tag found")
            with vpn_lock:
                if not vpn_rotated:
                    vpn_rotated = True
                    rotate_VPN(instructions)
                    time.sleep(20)
                else:
                    print(f"[Page {page_num}] Skipping VPN rotation — already handled")

    except Exception as e:
        print(f"[Page {page_num}] Error: {e}")
        with vpn_lock:
            if not vpn_rotated:
                vpn_rotated = True
                rotate_VPN(instructions)
                time.sleep(20)
            else:
                print(f"[Page {page_num}] Skipping VPN rotation — already handled")

    finally:
        driver.quit()

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

def process_url(url_obj):
    try:
        # time.sleep(random.uniform(6, 10))  # Random wait between 3 to 5 seconds
        input_params = extract_coupang_params(url_obj['URL'])
        print(input_params)

        if input_params is not None:
            extracted_product = extract_data_with_selenium(input_params)
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
                        return extracted_product
                    else:
                        # out of stock
                        extracted_product["status"] = "out of stock"

                extracted_product["rating"] = extract_all_ratings_selenium(input_params["productId"])
                return extracted_product

        print("Come to here else")
        return {
            'input_obj': url_obj,
            'thomas_error': True
        }
    except Exception as e:
        print(e)
        return {
            'input_obj': url_obj,
            'thomas_error': True
        }

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
                    
                    # Process URLs in batches of 3 using ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        futures = [executor.submit(process_url, url_obj) for url_obj in data]
                        
                        for future in as_completed(futures):
                            result = future.result()
                            extracted_data.append(result)
                    
                    save_path = os.path.join(rootPath, 'JSONs', f'coupang_data_{uuid.uuid1()}.json')
                    with open(save_path, 'w') as f:
                        json.dump(extracted_data, f, indent=4)

                    print(f"Saved {filename} to {save_path}")

                shutil.move(file_path, os.path.join(rootPath, "URLs_Converted", filename))

            except Exception as e:
                print(f"Failed to load {filename}: {e}")

if __name__ == "__main__":
    

    json_data_list = load_all_json_from_folder('URLs')