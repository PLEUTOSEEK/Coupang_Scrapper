import os
import json
import re
import pandas as pd
from datetime import datetime
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

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

                    # To keep track of the items to remove
                    items_to_remove = []

                    for index, item in enumerate(data_list):

                        if item["thomas_error"] == False:
                            try:
                                inner_item = item

                                if inner_item.get('quantityBase', None) is None:
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
                                                "rating": comment.get("rating", ""),
                                                "content": ILLEGAL_CHARACTERS_RE.sub(r'', comment.get("content", "")),
                                                "comment_date": formatted_date
                                            }
                                        )
                                    for comment in all_comments:
                                        result = {
                                            'Country Code': inner_item.get('input_obj', {}).get('er', ''),
                                            'Category': ILLEGAL_CHARACTERS_RE.sub(r'', inner_item.get('input_obj', {}).get('Category', '')),
                                            'Brand': '',
                                            'Product':  ILLEGAL_CHARACTERS_RE.sub(r'',  inner_item.get('itemName', '')), 
                                            'Flavour': '',
                                            'Price': price,
                                            'Rating': comment.get("rating", ""),
                                            'Page URL': inner_item.get('input_obj', {}).get('URL', ''),
                                            'Review Date': comment.get("comment_date", ""),
                                            'Message': comment.get("content", ""),
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
                                        'Review Date': "",
                                        'Message': "",
                                        'Website Name': 'https://www.coupang.com/',
                                        'Site Type': 'https://www.coupang.com/',
                                        "Status": inner_item.get('status', '')
                                    }
                                    results.append(result)
                            except Exception as item_err:
                                print(f"Skipping item in {filename} due to structure error: {item_err}")
                        else:
                            items_to_remove.append(index)
                            unscrapped_results.append(inner_item.get('input_obj', {}))
                    
                    # Remove the problematic items from data_list
                    for index in reversed(items_to_remove):  # Remove in reverse to avoid index shifting
                        del data_list[index]

                # Write the cleaned data back to the JSON file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_list, f, ensure_ascii=False, indent=4)

            except Exception as file_err:
                print(f"Failed to read {filename}: {file_err}")

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(results)
    save_path = os.path.join(rootPath, "Outputs",f"output_{get_current_date_filename_format()}.xlsx")
    df.to_excel(save_path, index=False)

    print("✅ output.xlsx saved successfully.")

    # Save unscrapped results if needed
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