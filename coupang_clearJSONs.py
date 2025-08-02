import os
import glob

root_path = os.path.dirname(os.path.abspath(__file__))

def clear_folder(folder_path):
    """
    Clears all files in the specified folder.
    
    Args:
        folder_path (str): Path to the folder to clear
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Verify the folder exists
        if not os.path.isdir(folder_path):
            return False, f"Folder does not exist: {folder_path}"
        
        # Get all .json files in the folder (excluding subdirectories)
        json_files = glob.glob(os.path.join(folder_path, '*.json'))
        
        # Remove each JSON file
        for file in json_files:
            if os.path.isfile(file):
                os.remove(file)
        
        return True, f"Successfully cleared {len(json_files)} JSON files from {folder_path}"
    
    except Exception as e:
        return False, f"Error clearing JSON files: {str(e)}"

def clear_folders():
    folders = [
        os.path.join(root_path, "JSONs"),
        os.path.join(root_path, "URLs"),
        os.path.join(root_path, "URLs_Converted")
    ]

    for folder in folders:
        success, message = clear_folder(folder)
        print(message)

# Example usage:
if __name__ == "__main__":
    clear_folders()
