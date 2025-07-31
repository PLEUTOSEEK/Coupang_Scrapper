import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict, Any

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

async def extract_multiple_data(params_list: List[Dict]) -> List[Dict]:
    """
    Extract data for multiple URLs concurrently.
    
    Args:
        params_list: List of parameter dictionaries for each URL
        
    Returns:
        List of extracted data dictionaries
    """
    return await asyncio.gather(*[_extract_data_playwright(params) for params in params_list])

async def _extract_data_playwright(params: Dict) -> Dict:
    """
    Internal function to extract data for a single URL using Playwright.
    """
    url = "https://www.coupang.com/next-api/products/vendor-items"
    
    for retry in range(3):
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                response = await page.request.get(url, headers=headers, params=params)
                json_data = await response.json()
                await browser.close()
                return json_data

        except Exception as e:
            print(f"Error in extract_data (attempt {retry+1}): {e}")
            if retry == 2:  # Last attempt failed
                return {"error": str(e), "params": params}
    
    return {"error": "Max retries reached", "params": params}

async def extract_multiple_ratings(product_ids: List[str]) -> List[Dict]:
    """
    Extract ratings for multiple product IDs concurrently.
    
    Args:
        product_ids: List of product IDs
        
    Returns:
        List of rating data dictionaries
    """
    return await asyncio.gather(*[_extract_rating_playwright(pid) for pid in product_ids])

async def _extract_rating_playwright(productID: str) -> Dict:
    """
    Internal function to extract rating data for a single product using Playwright.
    """
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
                return json_data

        except Exception as e:
            print(f"Error in extract_rating (attempt {retry+1}): {e}")
            if retry == 2:  # Last attempt failed
                return {"error": str(e), "productID": productID}
    
    return {"error": "Max retries reached", "productID": productID}

def extract_coupang_params(url: str) -> Dict:
    """
    Extracts product-related parameters from a Coupang product URL.

    Parameters:
        url (str): The Coupang product URL.

    Returns:
        dict: Dictionary with required params or None if extraction fails.
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
        print(f"Error in extract_coupang_params: {e}")
        return None

async def process_url_batch(url_batch: List[Dict]) -> List[Dict]:
    """
    Process a batch of URLs (3 at a time) concurrently.
    
    Args:
        url_batch: List of URL dictionaries to process
        
    Returns:
        List of processed results
    """
    # Extract parameters for all URLs in batch
    params_list = [extract_coupang_params(url_obj['URL']) for url_obj in url_batch]
    
    # Get product data for all URLs concurrently
    product_data_list = await extract_multiple_data(params_list)
    
    # Get ratings for all products concurrently
    product_ids = [params['productId'] for params in params_list if params]
    rating_data_list = await extract_multiple_ratings(product_ids)
    
    # Combine results
    results = []
    for url_obj, params, product_data, rating_data in zip(url_batch, params_list, product_data_list, rating_data_list):
        result = {
            "input_obj": url_obj,
            "params": params,
            "product_data": product_data,
            "rating_data": rating_data,
            "status": "normal",
            "thomas_error": False
        }
        
        # Check product status
        if product_data and not product_data.get("error"):
            if (product_data.get("almostSoldOut") is None and 
                product_data.get("easePayment") is None and 
                product_data.get("quantityBase") is None and 
                product_data.get("memberInfo") is None and 
                product_data.get("roleCode") is None):
                
                if product_data.get("itemName") is None:
                    result["status"] = "not applicable"
                else:
                    result["status"] = "out of stock"
        
        results.append(result)
    
    return results

def load_all_json_from_folder(folder_path: str):
    """
    Process all JSON files in a folder, scraping 3 URLs at a time.
    """
    # Create necessary directories if they don't exist
    os.makedirs(os.path.join(rootPath, 'JSONs'), exist_ok=True)
    os.makedirs(os.path.join(rootPath, "URLs_Converted"), exist_ok=True)
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    print(f"Processing {file_path}")
                    data = json.load(f)
                    
                    # Process URLs in batches of 3
                    batch_size = 3
                    all_results = []
                    
                    for i in range(0, len(data), batch_size):
                        batch = data[i:i + batch_size]
                        batch_results = asyncio.run(process_url_batch(batch))
                        all_results.extend(batch_results)
                        print(f"Processed batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}")
                    
                    # Save results
                    save_path = os.path.join(rootPath, 'JSONs', f'coupang_data_{uuid.uuid1()}.json')
                    with open(save_path, 'w') as f:
                        json.dump(all_results, f, indent=4)
                    
                    print(f"Saved {filename} to {save_path}")
                
                # Move processed file
                shutil.move(file_path, os.path.join(rootPath, "URLs_Converted", filename))
                
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

# Run the scraper
if __name__ == "__main__":
    load_all_json_from_folder('URLs')