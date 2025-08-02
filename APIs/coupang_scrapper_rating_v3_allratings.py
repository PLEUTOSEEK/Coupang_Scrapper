from playwright.async_api import async_playwright
import asyncio
import json

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

async def _extract_rating_playwright(productID, page_num=1):
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
    print(productID)
    for retry in range(3):
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()

                response = await page.request.get(url, headers=headers, params=params)
                json_data = await response.json()
                await browser.close()
                print(f"DONE_rating for page {page_num}")
                return json_data

        except Exception as e:
            print(f"Error in extract_rating (attempt {retry+1}): {e}")

    return None

async def get_all_ratings(productID):
    all_reviews = []
    first_page_data = await _extract_rating_playwright(productID, page_num=1)
    if not first_page_data:
        return []

    try:
        with open('first_page_data.json', 'w') as f:
            json.dump(first_page_data, f)
        total_pages = first_page_data['rData']['paging']['totalPage']
        all_reviews.extend(first_page_data['rData']['paging']['contents'])
    except KeyError:
        print("Invalid structure in response")
        return []

    # Start from page 2 (page 1 is already done)
    page = 2
    while page <= total_pages:
        batch = []
        for i in range(3):
            if page + i <= total_pages:
                batch.append(_extract_rating_playwright(productID, page_num=page + i))
        results = await asyncio.gather(*batch)

        for result in results:
            if result:
                contents = result['rData']['paging']['contents']
                all_reviews.extend(contents)
        page += 3

    # Replace contents with the combined results
    first_page_data['rData']['paging']['contents'] = all_reviews
    return first_page_data

if __name__ == "__main__":
    productID = "7513418427"  # Replace with your product ID
    reviews = asyncio.run(get_all_ratings(productID))

    #save to json file
    with open('reviews.json', 'w') as f:
        json.dump(reviews, f)
    
    # print(f"Total reviews fetched: {len(reviews)}")
    # for review in reviews:
    #     print(review)