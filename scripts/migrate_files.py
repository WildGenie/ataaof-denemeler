import os
import shutil
import re

BASE_DIR = "output/anadolu"
OLD_MATERIALS_DIR = os.path.join(BASE_DIR, "materials")
NEW_JSON_DIR = os.path.join(BASE_DIR, "json")
NEW_MD_DIR = os.path.join(BASE_DIR, "md")

def migrate():
    if not os.path.exists(OLD_MATERIALS_DIR):
        print(f"Source directory {OLD_MATERIALS_DIR} does not exist.")
        return

    files = os.listdir(OLD_MATERIALS_DIR)

    for filename in files:
        filepath = os.path.join(OLD_MATERIALS_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        # Extract Semester (Donem)
        match = re.search(r"Dönem (\d+)", filename)
        if match:
            donem = match.group(1)
            donem_folder_name = f"Donem {donem}"
        else:
            print(f"Could not determine semester for {filename}, skipping.")
            continue

        # Determine target directory (JSON or MD)
        if filename.endswith(".json"):
            target_base = NEW_JSON_DIR
        elif filename.endswith(".md"):
            target_base = NEW_MD_DIR
        else:
            print(f"Unknown file type {filename}, skipping.")
            continue

        # Create target folder
        target_dir = os.path.join(target_base, donem_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        # Move file
        target_path = os.path.join(target_dir, filename)
        shutil.move(filepath, target_path)
        print(f"Moved {filename} -> {target_path}")

    # Optionally remove the old directory if empty
    if not os.listdir(OLD_MATERIALS_DIR):
        os.rmdir(OLD_MATERIALS_DIR)
        print(f"Removed empty directory {OLD_MATERIALS_DIR}")
    else:
        print(f"Directory {OLD_MATERIALS_DIR} is not empty, not removing.")

if __name__ == "__main__":
    migrate()
