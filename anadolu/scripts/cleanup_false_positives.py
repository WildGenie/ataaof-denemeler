#!/usr/bin/env python3
"""
Cleanup duplicate false positives.
Validation Logic:
- Target ONLY duplicates marked via 'Fuzzy Match' or 'Semantic Similarity'. (Ignore 'Exact Text Match')
- Compare options of the duplicate vs root.
- If Option Similarity < 0.60:
    - UNMARK as duplicate.
    - Restore original state (is_duplicate=False).
    - Recalculate occurrence_count locally.
"""

import os
import json
import difflib
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def normalize_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_options_similarity(opts1, opts2):
    if not opts1 or not opts2: return 0.0
    norm1 = [normalize_text(o) for o in opts1]
    norm2 = [normalize_text(o) for o in opts2]

    total_score = 0
    for o1 in norm1:
        best_match = 0
        for o2 in norm2:
            sim = difflib.SequenceMatcher(None, o1, o2).ratio()
            if sim > best_match: best_match = sim
        total_score += best_match
    return total_score / len(norm1)

def main():
    print("Cleaning up False Positive Duplicates (Low Option Similarity)...")

    total_unmarked = 0
    total_files = 0

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(JSON_DIR, donem_dir)

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename: continue
            file_path = os.path.join(donem_path, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                questions = data.get("questions", [])
                if not questions: continue

                q_map = {q["id"]: q for q in questions}
                modified = False

                # Step 1: Unmark false positives
                for q in questions:
                    if q.get("is_duplicate"):
                        reason = q.get("duplication_reason", "")
                        # Only check Fuzzy and Semantic
                        if "Exact Text Match" in reason:
                            continue

                        root_id = q.get("duplicate_of")
                        root = q_map.get(root_id)

                        if not root:
                             # Orphaned duplicate? Unmark logic could apply but let's be safe.
                             continue

                        opts1 = q.get("options", [])
                        opts2 = root.get("options", [])

                        sim = calculate_options_similarity(opts1, opts2)

                        # Threshold 0.90
                        if sim < 0.90:
                            print(f"Unmarking {filename} ID:{q['id']} (Reason: {reason}, OptSim: {sim:.2f})")
                            del q["is_duplicate"]
                            del q["duplicate_of"]
                            if "duplication_reason" in q: del q["duplication_reason"]
                            q["occurrence_count"] = 1 # Reset to 1 (will be recalc/summed if needed, but autonomous now)
                            modified = True
                            total_unmarked += 1

                # Step 2: Recalculate occurrence counts for File
                # Because we broke some links, root counts might be wrong.
                if modified:
                    # Reset all counts
                    for q in questions:
                        q["occurrence_count"] = 0

                    # Recalculate
                    # Logic: Everyone contributes 1 to their root (or self if no root)
                    for q in questions:
                        # Find root
                        curr = q
                        seen = {q.get("id")}
                        while curr.get("is_duplicate") and curr.get("duplicate_of") in q_map:
                            pid = curr.get("duplicate_of")
                            if pid in seen: break
                            seen.add(pid)
                            curr = q_map[pid]

                        root_id = curr.get("id")
                        q_map[root_id]["occurrence_count"] = q_map[root_id].get("occurrence_count", 0) + 1

                    # Fix self-counts for duplicates (optional, usually ignored)

                    # Save file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    total_files += 1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nCleanup Complete.")
    print(f"Files modified: {total_files}")
    print(f"Total duplicates unmarked (False Positives): {total_unmarked}")

if __name__ == "__main__":
    main()
