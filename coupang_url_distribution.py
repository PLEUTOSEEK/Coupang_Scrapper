import pandas as pd
import os, json

rootPath = os.path.dirname(os.path.abspath(__file__))

def read_excel_and_save_json_chunks(file_path, output_dir='URLs', chunk_size=5, sheet_name="Sample_Input"):
    """
    Reads the 'Sample_Input' sheet from an Excel file, converts it to JSON,
    and saves the data in multiple JSON files with 5 records each.

    Parameters:
        file_path (str): Path to the Excel file.
        output_dir (str): Directory where JSON files will be saved.
        chunk_size (int): Number of records per JSON file.

    Returns:
        None
    """
    try:
        # Create output directory if it doesn't exist
        save_path = os.path.join(rootPath, output_dir)
            
        # Read the sheet into a DataFrame
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')

        # Convert DataFrame to a list of dictionaries
        records = df.to_dict(orient='records')

        # Split into chunks of `chunk_size`
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i+chunk_size]
            file_name = f"chunk_{i//chunk_size + 1}.json"
            file_path_out = os.path.join(save_path, file_name)

            # Save JSON file
            with open(file_path_out, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=4)

            print(f"Saved: {file_path_out}")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

read_excel_and_save_json_chunks("Input.xlsx")