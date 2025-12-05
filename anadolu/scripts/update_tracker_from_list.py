import json
import os
import sys

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES_LIST_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "genai_files_list.json")
TRACKER_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "download_tracker.json")

def update_tracker():
    # 1. Load Files List
    if not os.path.exists(FILES_LIST_PATH):
        print(f"Error: Files list not found at {FILES_LIST_PATH}")
        return

    with open(FILES_LIST_PATH, 'r', encoding='utf-8') as f:
        files_list = json.load(f)

    print(f"Loaded {len(files_list)} files from list.")

    # 2. Group by Material ID and find the latest for each
    material_files = {} # material_id -> list of file objects

    for file_obj in files_list:
        display_name = file_obj.get("displayName", "")
        # Extract Material ID
        if display_name.endswith(".pdf"):
            try:
                parts = display_name[:-4].split(" - ")
                if parts and parts[-1].isdigit():
                    mid = parts[-1]
                    if mid not in material_files:
                        material_files[mid] = []
                    material_files[mid].append(file_obj)
            except:
                pass

    print(f"Found {len(material_files)} unique material IDs.")

    # 3. Load existing tracker (or create new)
    tracker_data = {}
    if os.path.exists(TRACKER_PATH):
        try:
            with open(TRACKER_PATH, 'r', encoding='utf-8') as f:
                tracker_data = json.load(f)
            print(f"Loaded existing tracker with {len(tracker_data)} entries.")
        except Exception as e:
            print(f"Error loading tracker: {e}. Starting fresh.")

    # 4. Update tracker with latest file info
    updated_count = 0

    for mid, files in material_files.items():
        # Sort by createTime descending (newest first)
        # createTime format: "2025-12-05T02:23:08.889405Z"
        files.sort(key=lambda x: x.get("createTime", ""), reverse=True)

        latest_file = files[0]

        # Prepare info to save
        file_info = {
            "genai_name": latest_file.get("name"),
            "genai_uri": latest_file.get("uri"),
            "size_bytes": latest_file.get("sizeBytes"),
            "sha256_hash": latest_file.get("sha256Hash"),
            "display_name": latest_file.get("displayName"),
            "create_time": latest_file.get("createTime")
        }

        # Update tracker
        # We store it under the material_id key.
        # Existing tracker might have other data?
        # The user request implies updating/saving this specific info.
        # If tracker has other structure, we should be careful.
        # Assuming simple key-value or we extend the dict for that material.

        if mid not in tracker_data:
            tracker_data[mid] = {}

        # Update fields
        tracker_data[mid].update(file_info)
        updated_count += 1

    # 5. Save Tracker
    with open(TRACKER_PATH, 'w', encoding='utf-8') as f:
        json.dump(tracker_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Updated tracker with {updated_count} materials.")
    print(f"💾 Saved to: {TRACKER_PATH}")

if __name__ == "__main__":
    update_tracker()
