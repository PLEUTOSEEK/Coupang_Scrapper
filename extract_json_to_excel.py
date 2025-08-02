import os
import json
import pandas as pd
from datetime import datetime
rootPath = os.path.dirname(os.path.abspath(__file__))

def convert_long_to_date(timestamp_ms):
    try:
        # Try to convert and format the timestamp
        timestamp_sec = int(timestamp_ms) / 1000
        dt = datetime.fromtimestamp(timestamp_sec)
    except (ValueError, TypeError, OSError):
        # If error, fallback to current time
        dt = datetime.now()
    return dt.strftime('%#m/%#d/%Y')

def save_unscrapped_in_chunks(data, target_folder, chunk_size=5):
    """
    Splits data into chunks and saves each chunk as a separate JSON file.

    Parameters:
        data (list): List of dictionaries to split.
        chunk_size (int): Number of items per chunk.
        target_folder (str): Folder where JSON files will be saved.
    """
    os.makedirs(target_folder, exist_ok=True)

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        filename = f"unscrapped_chunk_{i // chunk_size + 1}.json"
        path = os.path.join(target_folder, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=4)

    print(f"✅ {len(data)} unscrapped records split into {len(data) // chunk_size + (1 if len(data) % chunk_size else 0)} files.")

def extract_data_from_json(json_folder):
    """
    Extracts structured data from multiple JSON files and saves to an Excel file.

    Parameters:
        json_folder (str): Folder path where JSON files are stored.

    Output:
        Creates 'output.xlsx' in the current directory.
    """
    results = []

    unscrapped_results = []

    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(json_folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data_list = json.load(f)

                    for item in data_list:

                        if item["thomas_error"] == False:
                            try:

                                inner_item = item

                                if inner_item.get('quantityBase', None) == None:
                                    price = -1
                                else:
                                    price = inner_item.get('quantityBase', [{}])[0].get('moduleData', [{}])[0].get('priceLogData', {}).get('finalPrice', -1)

                                all_comments = []
                                
                                if inner_item.get('rating', {}) is not None:
                                    
                                    for comment in inner_item.get('rating', {}).get('rData', {}).get("paging", {}).get("contents", []):
                                        print("INN here")
                                        timestamp = comment.get("reviewAt", "")
                                        formatted_date = convert_long_to_date(timestamp)

                                        all_comments.append(
                                            {
                                                # "review_id": comment.get("reviewId", ""),
                                                # "product_id": comment.get("productId", ""),
                                                "rating": comment.get("rating", ""), 
                                                # "title": comment.get("title", ""),
                                                "content": re.sub(r'[^\x00-\x7F]+', '', comment.get("content", "")),
                                                "comment_date": formatted_date
                                            }
                                        )
                                    for comment in all_comments:
                                        result = {
                                            'Country Code': inner_item.get('input_obj', {}).get('er', ''),
                                            'Category': inner_item.get('input_obj', {}).get('Category', ''),
                                            'Brand': '',
                                            'Product': inner_item.get('itemName', ''),
                                            'Flavour': '',
                                            'Price': price,
                                            # 'Rating': item.get('rating', {}).get('rData', {}).get('ratingSummaryTotal', {}).get('ratingAverage', ''),
                                            'Rating': comment.get("rating", ""),
                                            'Page URL': inner_item.get('input_obj', {}).get('URL', ''),
                                            'Review Date': comment.get("comment_date", ""), #item.get('review_date', '') if isinstance(item.get('review_date', ''), str) else '',
                                            'Message': comment.get("content", ""), #all_comments,
                                            'Website Name': 'https://www.coupang.com/',
                                            'Site Type': 'https://www.coupang.com/',
                                            "Status": inner_item.get('status', '')
                                        }
                                        results.append(result)

                                else:
                                    
                                    result = {
                                        'Country Code': inner_item.get('input_obj', {}).get('er', ''),
                                        'Category': inner_item.get('input_obj', {}).get('Category', ''),
                                        'Brand': '',
                                        'Product': inner_item.get('itemName', ''),
                                        'Flavour': '',
                                        'Price': price,
                                        'Rating': "",
                                        'Page URL': inner_item.get('input_obj', {}).get('URL', ''),
                                        'Review Date': "", #item.get('review_date', '') if isinstance(item.get('review_date', ''), str) else '',
                                        'Message': "", #all_comments,
                                        'Website Name': 'https://www.coupang.com/',
                                        'Site Type': 'https://www.coupang.com/',
                                        "Status": inner_item.get('status', '')
                                    }
                                    results.append(result)
                            except Exception as item_err:
                                print(f"Skipping item in {filename} due to structure error: {item_err}")
                        else:
                            unscrapped_results.append(inner_item.get('input_obj', {}))
            except Exception as file_err:
                print(f"Failed to read {filename}: {file_err}")

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(results)

    save_path = os.path.join(rootPath, f"output_{get_current_date_filename_format()}.xlsx")

    df.to_excel(save_path, index=False)

    print("✅ output.xlsx saved successfully.")

    save_path = os.path.join(rootPath, f"URLs")

    save_unscrapped_in_chunks(unscrapped_results, save_path)

def get_current_date_filename_format():
    """
    Returns the current date in the format 'DD_MONTHNAME_YYYY' with the month in uppercase.

    Returns:
        str: Formatted date string (e.g., '30_JULY_2025')
    """
    now = datetime.now()
    return now.strftime('%d_%B_%Y').upper()

# Example usage:
open_path = os.path.join(rootPath, f"JSONs")
extract_data_from_json(open_path)