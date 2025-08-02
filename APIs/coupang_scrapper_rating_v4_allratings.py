import time
import random
import shutil
import requests, json, os
import pandas as pd
from urllib.parse import urlparse, parse_qs
import uuid
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_data_with_selenium(params):
    url = f"https://www.coupang.com/next-api/products/vendor-items?productId={params['productId']}&vendorItemId={params['vendorItemId']}&landingItemId={params['landingItemId']}&landingProductId={params['landingProductId']}&landingVendorItemId={params['landingVendorItemId']}&defaultSelection={params['defaultSelection']}&deliveryToggle={params['deliveryToggle']}"

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Firefox(options=chrome_options)

    try:
        for retry in range(3):
            try:
                driver.get(url)
                time.sleep(4)

                print(driver.page_source)
                time.sleep(5)
                
                # Parse the page source with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # save into html
                with open("page_source.html", "w", encoding="utf-8") as file:
                    file.write(soup.prettify())
                
                # Find the pre tag containing JSON data
                pre_tag = soup.find('pre')
                
                if pre_tag:
                    # Extract the text content and parse as JSON
                    json_data = json.loads(pre_tag.text)
                    print("Successfully extracted JSON data:")
                    return json_data
                else:
                    print("No <pre> tag found in the response")
                    print("Page source:", driver.page_source)
                    return None
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print("Raw content:", pre_tag.text if pre_tag else "No pre tag")
                return None
            except Exception as e:
                print(f"Attempt {retry + 1} failed: {str(e)}")
                time.sleep(2)
    
    finally:
        driver.quit()
    
    return None

params = {
    'productId': '8230650647',
    'vendorItemId': '87687654341',
    'landingItemId': '23687652709',
    'landingProductId': '8230650647',
    'landingVendorItemId': '87687654341',
    'defaultSelection': '',
    'deliveryToggle': 'true'
}

result = extract_data_with_selenium(params)
print(result)