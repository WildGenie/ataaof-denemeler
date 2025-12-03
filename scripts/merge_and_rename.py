import os
import shutil
import re
import json

BASE_DIR = "output/Anadolu"
MD_DIR = os.path.join(BASE_DIR, "md")
JSON_DIR = os.path.join(BASE_DIR, "json")

def merge_and_rename():
    # 1. Rename and Move MD Files
    # Source: output/Anadolu/md/Anadolu - Dönem X - Course Name - Sorular.md
    # Target: output/Anadolu/Donem X/Course Name/Alıştırma Soruları.md

    if os.path.exists(MD_DIR):
        print("Processing MD files...")
        for filename in os.listdir(MD_DIR):
            if not filename.endswith("Sorular.md"):
                continue

            filepath = os.path.join(MD_DIR, filename)

            # Regex to parse filename
            # Anadolu - Dönem 1 - Görsel Estetik - Sorular.md
            match = re.search(r"Anadolu - Dönem (\d+) - (.+) - Sorular\.md", filename)
            if match:
                donem = match.group(1)
                course_name = match.group(2)

                target_dir = os.path.join(BASE_DIR, f"Donem {donem}", course_name)
                os.makedirs(target_dir, exist_ok=True)

                target_path = os.path.join(target_dir, "Alıştırma Soruları.md")
                shutil.move(filepath, target_path)
                print(f"Moved MD: {filename} -> {target_path}")
            else:
                print(f"Skipping MD: {filename} (Pattern mismatch)")

    # 2. Merge Raw JSON Files
    # Source: output/Anadolu/json/Anadolu - Dönem X - Course Name - Unite YY.json
    # Target: output/Anadolu/json/Donem X/Anadolu - Dönem X - Course Name - Alıştırma Soruları - Raw.json

    if os.path.exists(JSON_DIR):
        print("\nProcessing JSON files...")
        files = os.listdir(JSON_DIR)
        course_groups = {}

        # Group files by course
        for filename in files:
            # Anadolu - Dönem 1 - Görsel Estetik - Unite 01.json
            match = re.search(r"Anadolu - Dönem (\d+) - (.+) - Unite \d+\.json", filename)
            if match:
                donem = match.group(1)
                course_name = match.group(2)
                key = (donem, course_name)

                if key not in course_groups:
                    course_groups[key] = []
                course_groups[key].append(filename)

        for (donem, course_name), filenames in course_groups.items():
            merged_data = []
            filenames.sort() # Ensure order

            for filename in filenames:
                filepath = os.path.join(JSON_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            merged_data.extend(data)
                        else:
                            print(f"Warning: {filename} is not a list, skipping merge.")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

            # Save merged file
            target_dir = os.path.join(JSON_DIR, f"Donem {donem}")
            os.makedirs(target_dir, exist_ok=True)

            merged_filename = f"Anadolu - Dönem {donem} - {course_name} - Alıştırma Soruları - Raw.json"
            merged_filepath = os.path.join(target_dir, merged_filename)

            with open(merged_filepath, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=4, ensure_ascii=False)
            print(f"Merged {len(filenames)} files into {merged_filepath}")

            # Remove original files
            for filename in filenames:
                os.remove(os.path.join(JSON_DIR, filename))
                # print(f"Deleted {filename}")

if __name__ == "__main__":
    merge_and_rename()
