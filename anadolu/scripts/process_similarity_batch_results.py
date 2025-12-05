#!/usr/bin/env python3
"""
Process Gemini Batch API similarity results and mark duplicates in Enriched.json files.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "Anadolu"
JSON_DIR = OUTPUT_DIR / "json"

def load_enriched(course_name: str, donem: int):
    """Load the Enriched.json for a given course and semester."""
    enriched_path = JSON_DIR / f"Donem {donem}" / f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json"
    if enriched_path.is_file():
        with open(enriched_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data, enriched_path
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse JSON in {enriched_path}")
                return {"questions": []}, enriched_path
    else:
        return {"questions": []}, enriched_path

def save_enriched(data: dict, path: Path):
    """Write the enriched data back to disk."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Saved duplicate marks for {path.parent.name}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 process_similarity_batch_results.py <path_to_results.jsonl>")
        sys.exit(1)

    results_path = sys.argv[1]
    if not os.path.exists(results_path):
        print(f"File not found: {results_path}")
        sys.exit(1)

    print(f"Processing results from {results_path}...")

    # Store updates grouped by file to minimize IO
    # format: (course, donem) -> { q_id: {mark_data} }
    updates = {}

    processed_count = 0
    duplicate_count = 0

    with open(results_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip(): continue
            try:
                obj = json.loads(line)
            except:
                print(f"Line {line_num}: Invalid JSON")
                continue

            key = obj.get("key")
            response = obj.get("response")

            if not key or not response: continue

            # Key: Course|Donem|Q1_ID|Q2_ID
            try:
                parts = key.split("|")
                # Handle course names containing pipes? Hopefully rare.
                # Assuming standard format:
                q2_id_str = parts[-1]
                q1_id_str = parts[-2]
                donem_str = parts[-3]
                course_name = "|".join(parts[:-3])

                donem = int(donem_str)
                q1_id = int(q1_id_str)
                q2_id = int(q2_id_str)
            except Exception as e:
                print(f"Line {line_num}: unexpected key format {key} ({e})")
                continue

            # Extract LLM decision
            # Similar logic to process_batch_results.py to extract JSON from text
            try:
                candidates = response.get("candidates", [])
                if not candidates: continue
                content = candidates[0].get("content", {})
                parts_content = content.get("parts", [])
                text_blob = ""
                for p in parts_content:
                    if "text" in p:
                        text_blob += p["text"]

                # Parse JSON inside text
                # clean markdown code blocks
                text_blob = text_blob.replace("```json", "").replace("```", "").strip()

                start = text_blob.find("{")
                end = text_blob.rfind("}")
                if start != -1 and end != -1:
                    json_str = text_blob[start:end+1]
                    result_data = json.loads(json_str)

                    is_duplicate = result_data.get("is_duplicate", False)
                    reason = result_data.get("reason", "")

                    if is_duplicate:
                        # Mark Q2 as duplicate of Q1
                        if (course_name, donem) not in updates:
                            updates[(course_name, donem)] = {}

                        updates[(course_name, donem)][q2_id] = {
                            "near_duplicate_of": q1_id,
                            "duplication_reason": reason
                        }
                        duplicate_count += 1

                processed_count += 1
            except Exception as e:
                # print(f"Line {line_num}: Error parsing response ({e})")
                pass

    print(f"Processed {processed_count} results, found {duplicate_count} duplicates.")

    # Apply updates
    for (course_name, donem), q_updates in updates.items():
        data, path = load_enriched(course_name, donem)
        questions = data.get("questions", [])

        modified = False
        for q in questions:
            qid = q.get("id")
            if qid in q_updates:
                upd = q_updates[qid]
                q["is_near_duplicate"] = True
                q["near_duplicate_of"] = upd["near_duplicate_of"]
                q["duplication_reason"] = upd["duplication_reason"]
                modified = True

        if modified:
            save_enriched(data, path)

if __name__ == "__main__":
    main()
