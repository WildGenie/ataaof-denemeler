#!/usr/bin/env python3
"""
Mark near-duplicate questions (0.95+ similarity, same answer) in enriched JSON files.
Adds 'is_near_duplicate' and 'near_duplicate_of' fields.
"""

import os
import json
import sys
from collections import defaultdict

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
SIMILARITY_REPORT = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")

def normalize_answer(answer):
    """Normalize answer for comparison."""
    if not answer:
        return ""
    return answer.lower().strip()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mark near-duplicate questions in enriched JSON files.")
    parser.add_argument("--donem", type=int, help="Filter by semester (e.g., 1, 7)")
    args = parser.parse_args()

    print("Marking near-duplicate questions (0.95+ similarity, same answer)...")

    # Load similarity analysis
    with open(SIMILARITY_REPORT, 'r', encoding='utf-8') as f:
        similarity_data = json.load(f)

    # Filter for near-duplicates with same answer
    near_duplicates = []
    for item in similarity_data:
        if item["similarity"] >= 0.95:
            ans1 = normalize_answer(item["q1"].get("answer", ""))
            ans2 = normalize_answer(item["q2"].get("answer", ""))

            # Only mark if answers are the same
            if ans1 and ans2 and ans1 == ans2:
                near_duplicates.append(item)

    print(f"Found {len(near_duplicates)} near-duplicate pairs with same answers.")

    # Group by course and file
    updates_by_file = defaultdict(lambda: defaultdict(dict))

    for item in near_duplicates:
        course1 = item["q1"]["course"]
        course2 = item["q2"]["course"]

        # Only process if same course
        if course1 != course2:
            continue

        q1_id = item["q1"]["id"]
        q2_id = item["q2"]["id"]

        # Determine which is "original" (lower ID)
        if q1_id < q2_id:
            original_id = q1_id
            duplicate_id = q2_id
        else:
            original_id = q2_id
            duplicate_id = q1_id

        # Mark duplicate
        updates_by_file[course1][duplicate_id] = {
            "is_duplicate": True,
            "duplicate_of": original_id,
            "similarity_score": item["similarity"]
        }

    # Apply updates to JSON files
    total_updated = 0

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        # Filter by donem
        if args.donem:
            try:
                current_donem = int(donem_dir.split(" ")[1])
                if current_donem != args.donem:
                    continue
            except (IndexError, ValueError):
                continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename:
                continue

            file_path = os.path.join(donem_path, filename)
            course_name = filename.split(" - ")[2]

            if course_name not in updates_by_file:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                modified = False
                updates = updates_by_file[course_name]

                for q in data.get("questions", []):
                    # Clean up previous "near_duplicate" fields if they exist
                    if "is_near_duplicate" in q:
                        del q["is_near_duplicate"]
                        modified = True
                    if "near_duplicate_of" in q:
                        del q["near_duplicate_of"]
                        modified = True

                    q_id = q.get("id")
                    if q_id in updates:
                        for key, value in updates[q_id].items():
                            if q.get(key) != value:
                                q[key] = value
                                modified = True

                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                    count = len([q for q in data["questions"] if q.get("is_duplicate") and q.get("similarity_score")])
                    print(f"  ✅ {course_name}: {count} duplicates marked (from similarity analysis)")
                    total_updated += count

            except Exception as e:
                print(f"  ❌ Error processing {filename}: {e}")

    print(f"\nTotal near-duplicates marked: {total_updated}")

if __name__ == "__main__":
    main()
