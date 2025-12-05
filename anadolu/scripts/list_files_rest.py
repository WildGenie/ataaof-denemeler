import os
import json
import requests
from dotenv import load_dotenv

# Add project root to sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "Anadolu", "genai_files_list.json")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/files"

def fetch_all_files():
    all_files = []
    page_token = None
    page_size = 100

    print(f"Fetching files from {BASE_URL} (Page Size: {page_size})...")

    while True:
        params = {
            "key": GEMINI_API_KEY,
            "pageSize": page_size
        }
        if page_token:
            params["pageToken"] = page_token

        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            files = data.get("files", [])
            if not files:
                print("  No more files found in this page.")
                break

            all_files.extend(files)
            print(f"  Fetched {len(files)} files. Total: {len(all_files)}")

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        except Exception as e:
            print(f"Error fetching files: {e}")
            break

    return all_files

def main():
    files = fetch_all_files()

    if files:
        # Create directory if not exists
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved {len(files)} files to: {OUTPUT_PATH}")

        # Check for duplicates (optional, based on previous context)
        material_id_counts = {}
        for f in files:
            display_name = f.get("displayName", "")
            if display_name.endswith(".pdf"):
                try:
                    parts = display_name[:-4].split(" - ")
                    if parts and parts[-1].isdigit():
                        mid = parts[-1]
                        material_id_counts[mid] = material_id_counts.get(mid, 0) + 1
                except:
                    pass

        duplicates = {k: v for k, v in material_id_counts.items() if v > 1}
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} material IDs with duplicate files.")
            # for mid, count in duplicates.items():
            #     print(f"  Material {mid}: {count} copies")
    else:
        print("No files fetched.")

if __name__ == "__main__":
    main()
