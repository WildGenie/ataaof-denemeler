#!/usr/bin/env python3
"""
Mark EXACT duplicates (based on normalized text) in Enriched.json files.
This complements the semantic similarity analysis done via Gemini Batch.
It uses simple text normalization to find identical questions.
"""

import os
import json
import re
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def normalize_text(text):
    """Normalize text for comparison (remove punctuation, lowercase)."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Starting exact duplicate marking...")

    # Store updates: (course_name, donem_int) -> list of questions to update
    file_updates = {}

    total_marked = 0

    # Scan directories
    for donem_dir in sorted(os.listdir(JSON_DIR)):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(JSON_DIR, donem_dir)
        try:
            donem = int(donem_dir.split(" ")[1])
        except: continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename: continue

            file_path = os.path.join(donem_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                questions = data.get("questions", [])
                if not questions: continue

                # Group by normalized text
                groups = defaultdict(list)
                for q in questions:
                    # Skip if already marked as duplicate (by batch process)
                    # OR we can re-evaluate. Let's process everything to be sure.
                    text = normalize_text(q.get("question"))
                    if text:
                        groups[text].append(q)

                # Identify duplicates
                modified = False
                file_duplicates = 0

                for text, group in groups.items():
                    if len(group) > 1:
                        # Sort by ID to keep the first one stable
                        group.sort(key=lambda x: x.get("id"))

                        # Keep the first one
                        original = group[0]
                        original_id = original.get("id")

                        # Update occurrence count
                        original["occurrence_count"] = len(group)
                        modified = True # Ensure we save even if duplicates were already marked but count wasn't set

                        # Mark others
                        for duplicate in group[1:]:
                            # Update fields
                            if not duplicate.get("is_near_duplicate"):
                                duplicate["is_near_duplicate"] = True
                                duplicate["near_duplicate_of"] = original_id
                                duplicate["duplication_reason"] = "Exact Text Match (Normalized)"
                                modified = True
                                file_duplicates += 1
                                total_marked += 1
                            else:
                                # Already marked, maybe update reason or link?
                                # If it was marked by similarity, Exact Match is stronger reason.
                                if duplicate.get("near_duplicate_of") != original_id:
                                    # Link to this one instead?
                                    # Let's trust exact match more than similarity
                                    duplicate["near_duplicate_of"] = original_id
                                    duplicate["duplication_reason"] = "Exact Text Match (Normalized)"
                                    modified = True

                if modified:
                    print(f"  {filename}: Marked {file_duplicates} exact duplicates.")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"\nTotal marked exact duplicates: {total_marked}")

if __name__ == "__main__":
    main()
