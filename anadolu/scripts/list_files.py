import os
import json
from dotenv import load_dotenv
from google import genai

# Add project root to sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing files...")
try:
    # Pagination loop
    page_size = 50
    files = client.files.list(config={"page_size": page_size})
    count = 0
    material_id_map = {} # material_id -> list of (file.name, display_name, uri)
    all_files_list = []

    print("Analyzing files for duplicates...")

    for file in files:
        count += 1
        display_name = file.display_name

        # Store basic info for all files
        file_info = {
            "name": file.name,
            "display_name": display_name,
            "uri": file.uri,
            "create_time": str(file.create_time),
            "mime_type": file.mime_type,
            "state": str(file.state)
        }
        all_files_list.append(file_info)

        # Extract Material ID
        # Format usually: "... - <MaterialID>.pdf"
        try:
            if display_name.endswith(".pdf"):
                name_without_ext = display_name[:-4]
                parts = name_without_ext.split(" - ")
                if parts:
                    material_id = parts[-1]

                    # Basic validation: Material ID should be digits
                    if material_id.isdigit():
                        if material_id not in material_id_map:
                            material_id_map[material_id] = []
                        material_id_map[material_id].append(file_info)
        except Exception:
            pass

    print(f"Total files scanned: {count}")
    print("-" * 30)

    # Save to JSON
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "Anadolu", "genai_files_list.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_files_list, f, indent=4, ensure_ascii=False)
    print(f"💾 Saved full file list to: {output_path}")

    duplicates_found = False
    for mid, file_list in material_id_map.items():
        if len(file_list) > 1:
            duplicates_found = True
            print(f"🔴 Duplicate Material ID: {mid} ({len(file_list)} copies)")
            for f in file_list:
                print(f"   - {f['display_name']} | {f['name']} | {f['create_time']}")
            print("-" * 30)

    if not duplicates_found:
        print("✅ No duplicate material IDs found.")
    else:
        print("⚠️  Duplicates found (see above).")

except Exception as e:
    print(f"Error listing files: {e}")
