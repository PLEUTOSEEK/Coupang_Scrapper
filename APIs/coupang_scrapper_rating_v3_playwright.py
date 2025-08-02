from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

def extract_rating_with_selenium(productID):
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
    
    # Construct the full URL with parameters
    query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v])
    full_url = f"{url}?{query_string}"

    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        for retry in range(3):
            try:
                driver.get(full_url)
                time.sleep(3)  # Wait for the response
                time.sleep(2)
                
                # Parse the page source with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Find the pre tag containing JSON data
                pre_tag = soup.find('pre')
                
                if pre_tag:
                    try:
                        json_data = json.loads(pre_tag.text)
                        print("Successfully extracted rating data")
                        return json_data
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON: {str(e)}")
                        print("Raw content:", pre_tag.text)
                else:
                    print("No <pre> tag found in the response")
                    print("Page source:", driver.page_source)
                
            except Exception as e:
                print(f"Attempt {retry + 1} failed: {str(e)}")
                time.sleep(2)
    
    finally:
        driver.quit()
    
    return None

# Example usage
product_id = "8230650647"  # Example product ID
rating_data = extract_rating_with_selenium(product_id)
if rating_data:
    #save to json sample data
    with open('Samples/rating_data.json', 'w', encoding='utf-8') as f:
        json.dump(rating_data, f, indent=2, ensure_ascii=False)