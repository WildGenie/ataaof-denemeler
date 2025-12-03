import os
import json
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_lib import JSON_DIR

def migrate_raw_files():
    print(f"Scanning directory: {JSON_DIR}")

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for root, dirs, files in os.walk(JSON_DIR):
        for file in files:
            if file.endswith(" - Raw.json"):
                filepath = os.path.join(root, file)
                try:
                    process_file(filepath)
                    migrated_count += 1
                except ValueError:
                    skipped_count += 1
                except Exception as e:
                    print(f"Error processing {file}: {e}")
                    error_count += 1

    print(f"\nMigration complete.")
    print(f"Processed/Migrated: {migrated_count}")
    print(f"Skipped (Already correct or empty): {skipped_count}")
    print(f"Errors: {error_count}")

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        # Not a list? Unknown format.
        raise ValueError("Not a list")

    if not data:
        raise ValueError("Empty list")

    # Check if it needs migration
    # Old format (Learn Questions): List of objects with "Data" key (which is a list of questions)
    # Old format (Generic Iteration): List of objects with "Questions" key

    needs_migration = False

    # Check the first item to guess format
    first_item = data[0]

    if "Data" in first_item:
        if isinstance(first_item["Data"], list):
            needs_migration = True
        elif isinstance(first_item["Data"], dict) and "QuestionAnswer" in first_item["Data"]:
            needs_migration = True

    elif "Questions" in first_item and isinstance(first_item["Questions"], list):
        needs_migration = True

    # Also check if it's ALREADY a list of questions
    # A question usually has "QuestionId", "SoruID", or "Index"
    if not needs_migration:
        if "QuestionId" in first_item or "SoruID" in first_item or "Index" in first_item:
            # Already in merged format
            raise ValueError("Already merged")

        # If it doesn't have Data/Questions AND doesn't look like a question,
        # it might be a list of something else or a weird format.
        # But if we are here, we assume it doesn't need migration based on our criteria.
        raise ValueError("Unknown format, skipping")

    if needs_migration:
        print(f"Migrating: {os.path.basename(filepath)}")
        all_questions_map = {}

        for item in data:
            # Extract questions list from the item
            questions_list = []
            if "Data" in item:
                if isinstance(item["Data"], list):
                    questions_list = item["Data"]
                elif isinstance(item["Data"], dict) and "QuestionAnswer" in item["Data"]:
                    questions_list = item["Data"]["QuestionAnswer"]
            elif "Questions" in item and isinstance(item["Questions"], list):
                questions_list = item["Questions"]

            # Add to map
            for q in questions_list:
                # Determine ID
                q_id = q.get("QuestionId") or q.get("SoruID") or q.get("Index")

                # If no ID, try to generate one or skip?
                # Learn questions usually have Index.
                if q_id:
                    all_questions_map[q_id] = q

        # Convert map to list
        merged_questions = list(all_questions_map.values())

        # Save back
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(merged_questions, f, indent=4, ensure_ascii=False)

        print(f"  -> Saved {len(merged_questions)} unique questions.")

if __name__ == "__main__":
    migrate_raw_files()
