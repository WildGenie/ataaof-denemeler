#!/usr/bin/env python3
"""
Process Gemini Batch API results and merge enrichments into per-course Enriched.json files.

Expected input file: output/Anadolu/batch_results.jsonl
Each line is a JSON object with a "key" field formatted as "Course|Donem|StartIndex"
and a "response" containing "enrichments" list.

The script will:
1. Iterate over each result line.
2. Parse the key to identify the target course and the start index.
3. Load the existing Enriched.json for that course (output/Anadolu/<Course>/Enriched.json).
4. For each enrichment entry, locate the corresponding question in the Enriched.json
   by matching the global question index (start_index + question_id).
5. Insert/replace the enrichment data (topic & explanation) into the question.
6. Save the updated Enriched.json back to disk.

The script is idempotent – running it multiple times will not duplicate enrichments.
"""

import json
import os
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # two levels up from this script
OUTPUT_DIR = PROJECT_ROOT / "output" / "Anadolu"
BATCH_RESULTS_FILE = OUTPUT_DIR / "batch_results.jsonl"

if not BATCH_RESULTS_FILE.is_file():
    print(f"Error: batch results file not found at {BATCH_RESULTS_FILE}")
    sys.exit(1)

def load_enriched(course_name: str, donem: int):
    """Load the Enriched.json for a given course and semester.
    Returns a dict with 'questions' list (or empty structure if file missing)."""
    enriched_path = OUTPUT_DIR / "json" / f"Donem {donem}" / f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json"
    if enriched_path.is_file():
        with open(enriched_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Expecting a dict with "questions" key
                if isinstance(data, dict) and "questions" in data:
                    return data, enriched_path
                elif isinstance(data, list):
                    # Convert list to dict format
                    return {"questions": data}, enriched_path
                else:
                    print(f"Warning: Unexpected format in {enriched_path}, treating as empty.")
                    return {"questions": []}, enriched_path
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse JSON in {enriched_path}, treating as empty.")
                return {"questions": []}, enriched_path
    else:
        # No enriched file yet – create an empty placeholder
        return {"questions": []}, enriched_path

def save_enriched(data: dict, path: Path):
    """Write the enriched data back to the given path.
    The file will contain a JSON object with 'questions' array."""
    # Ensure parent directory exists
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    questions_count = len(data.get("questions", []))
    print(f"Saved updated Enriched.json for {path.parent.name} ({questions_count} questions).")

# Main processing loop
with open(BATCH_RESULTS_FILE, "r", encoding="utf-8") as results_f:
    for line_num, raw_line in enumerate(results_f, start=1):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            result_obj = json.loads(raw_line)
        except json.JSONDecodeError as e:
            print(f"Line {line_num}: Failed to parse JSON – {e}")
            continue
        # Extract key and response
        key = result_obj.get("key")
        response = result_obj.get("response")
        if not key or not response:
            print(f"Line {line_num}: Missing key or response, skipping.")
            continue
        # Key format: Course|Donem|StartIndex
        try:
            course_name, donem_str, start_index_str = key.split("|")
            donem = int(donem_str)
            start_index = int(start_index_str)
        except ValueError:
            print(f"Line {line_num}: Unexpected key format '{key}', skipping.")
            continue
        # Extract enrichments list from response
        enrichments = []
        # The response structure may vary depending on model version.
        # We look for a top‑level "enrichments" field inside the model's answer text.
        # The model usually returns a JSON string inside the "text" part.
        # Navigate safely:
        candidates = response.get("candidates", [])
        if not candidates:
            print(f"Line {line_num}: No candidates in response, skipping.")
            continue
        # Assume first candidate contains the answer.
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            print(f"Line {line_num}: No parts in candidate content, skipping.")
            continue
        # The part may have either "text" or "thoughtSignature" + "text".
        # We'll look for a "text" field that contains a JSON string.
        text_blob = None
        for part in parts:
            if "text" in part:
                text_blob = part["text"]
                break
        if not text_blob:
            print(f"Line {line_num}: No text part found, skipping.")
            continue
        # The text_blob itself is a JSON string representing a dict with "enrichments".
        try:
            inner_json = json.loads(text_blob)
            enrichments = inner_json.get("enrichments", [])
        except json.JSONDecodeError:
            # Sometimes the model returns a raw string without proper JSON quoting.
            # Attempt a fallback: look for a substring that starts with '{"enrichments":'.
            start = text_blob.find('{"enrichments":')
            if start != -1:
                try:
                    inner_json = json.loads(text_blob[start:])
                    enrichments = inner_json.get("enrichments", [])
                except json.JSONDecodeError:
                    pass
        if not enrichments:
            print(f"Line {line_num}: No enrichments extracted, skipping.")
            continue
        # Load existing enriched data for the course
        data, enriched_path = load_enriched(course_name, donem)
        questions = data.get("questions", [])

        # Apply each enrichment
        for enr in enrichments:
            qid = enr.get("question_id")
            unite_no = enr.get("UniteNo")
            topic = enr.get("topic")
            explanation = enr.get("explanation")

            # Robust matching fields
            exam_q_num = enr.get("exam_question_number")
            source = enr.get("source")
            material_id = enr.get("material_id")

            target_question = None

            # Try robust matching first if metadata is available
            if exam_q_num and source and material_id:
                # Find matching question in the list
                for q in questions:
                    # Convert to string for comparison to be safe
                    if (str(q.get("exam_question_number")) == str(exam_q_num) and
                        q.get("source") == source and
                        str(q.get("material_id")) == str(material_id)):
                        target_question = q
                        break

            # Fallback to index-based matching if not found or metadata missing
            if not target_question and qid is not None:
                global_idx = start_index + qid
                # Ensure list is long enough
                while len(questions) <= global_idx:
                    questions.append({})
                target_question = questions[global_idx]

            if not target_question:
                print(f"  Warning: Could not match enrichment for QID {qid}")
                continue

            # Clean up old fields if they exist
            target_question.pop("enrichments", None)
            target_question.pop("EnrichedTopic", None)
            target_question.pop("EnrichedExplanation", None)

            # Add new fields
            if unite_no is not None:
                target_question["UniteNo"] = unite_no
            if topic:
                target_question["topic"] = topic
            if explanation:
                target_question["explanation"] = explanation

        # Update the data dict and save
        data["questions"] = questions
        save_enriched(data, enriched_path)

print("Batch result processing completed.")
