#!/usr/bin/env python3
"""
Clean up old near_duplicate fields from JSON files.
Removes 'is_near_duplicate', 'near_duplicate_of', and 'similarity_score' fields
since they're now integrated into the main duplicate system.
"""

import os
import json
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def main():
    print("Cleaning up old near_duplicate fields...")

    # Find all enriched JSON files
    json_files = glob.glob(os.path.join(JSON_DIR, "**", "*Enriched.json"), recursive=True)

    total_cleaned = 0
    files_modified = 0

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            modified = False
            cleaned_count = 0

            for q in data.get('questions', []):
                # Remove old near_duplicate fields
                if 'is_near_duplicate' in q:
                    del q['is_near_duplicate']
                    modified = True
                    cleaned_count += 1

                if 'near_duplicate_of' in q:
                    del q['near_duplicate_of']
                    modified = True

                if 'similarity_score' in q:
                    del q['similarity_score']
                    modified = True

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                course_name = os.path.basename(file_path).split(" - ")[2]
                print(f"  ✅ {course_name}: Cleaned {cleaned_count} questions")
                files_modified += 1
                total_cleaned += cleaned_count

        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")

    print(f"\nCleaned {total_cleaned} old fields from {files_modified} files.")
    print("Now re-running mark_duplicates.py to ensure consistency...")

if __name__ == "__main__":
    main()
