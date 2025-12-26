import json
import os
import re
from collections import defaultdict
import glob

# Source file
SOURCE_FILE = 'output/Auzef/user-courses.json'
# Base output dir
BASE_OUTPUT_DIR = 'output/Auzef/json'

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower()
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove special characters and spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

from difflib import SequenceMatcher

def fuzzy_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

def natural_sort_key(s):
    """Natural sort key for strings with numbers (e.g., '6.3' before '6.10')."""
    if s is None:
        return []
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]

def main():
    if not os.path.exists(SOURCE_FILE):
        # Try relative to script location if not found
        script_dir = os.path.dirname(os.path.abspath(__file__))
        SOURCE_FILE_ALT = os.path.join(os.path.dirname(script_dir), SOURCE_FILE)
        if os.path.exists(SOURCE_FILE_ALT):
            source_path = SOURCE_FILE_ALT
            output_base = os.path.join(os.path.dirname(script_dir), BASE_OUTPUT_DIR)
        else:
            print(f"Source file not found: {SOURCE_FILE}")
            return
    else:
        source_path = SOURCE_FILE
        output_base = BASE_OUTPUT_DIR

    with open(source_path, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    for course in courses:
        course_name = course.get('name')
        term_str = course.get('term') # e.g. "7. Dönem"

        # Skip Period 1 as requested
        if term_str and "1. Dönem" in term_str:
            print(f"Skipping {course_name} (Period 1)")
            continue
        if term_str:
            match = re.search(r'(\d+)', term_str)
            if match:
                term_num = match.group(1)
            else:
                term_num = "Other"
        else:
             term_num = "Other"

        term_dir_name = "Other" if term_num == "Other" else f"Donem {term_num}"
        output_dir = os.path.join(output_base, term_dir_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Construct filename
        # Pattern matching Anadolu: Auzef - Dönem {N} - {CourseName} - Sorular.json
        safe_course_name = course_name.replace('/', '-').replace(':', '')
        filename = f"Auzef - Dönem {term_num} - {safe_course_name} - Sorular.json"
        output_path = os.path.join(output_dir, filename)

        # Prepare data
        questions = course.get('questions', [])

        # --- Deduplication & Fuzzy Filtering ---
        # 1. First Pass: Group by exact normalized text
        text_map = defaultdict(list)
        for q in questions:
            norm = normalize_text(q.get("question", ""))
            text_map[norm].append(q)

        # 2. Extract unique candidates
        candidates = []
        for norm_text, group in text_map.items():
            group.sort(key=lambda x: x.get("id", 0))
            original = group[0]
            original["occurrence_count"] = len(group)
            original["norm"] = norm_text
            candidates.append(original)

        # 3. Second Pass: Fuzzy matching among candidates
        # We sort them by ID to ensure stability
        candidates.sort(key=lambda x: x.get("id", 0))
        final_list = []
        skip_indices = set()

        fuzzy_threshold = 0.95 # Higher than 95% is usually a copy with typo/formatting

        for i in range(len(candidates)):
            if i in skip_indices:
                continue

            curr = candidates[i]
            for j in range(i + 1, len(candidates)):
                if j in skip_indices:
                    continue

                target = candidates[j]
                if fuzzy_ratio(curr["norm"], target["norm"]) > fuzzy_threshold:
                    # Found a fuzzy duplicate
                    curr["occurrence_count"] += target["occurrence_count"]
                    skip_indices.add(j)

            final_list.append(curr)

        # --- Sorting Final Results ---
            # Numeric sorting for unit and topic, then id for stability
            unit = q.get("unit", "")
            topic = q.get("topic", "")
            q_id = q.get("id", 0)
            return (natural_sort_key(unit), natural_sort_key(topic), q_id)

        final_list.sort(key=sort_key)

        # Clean up temporary "norm" field before saving
        for q in final_list:
            if "norm" in q:
                del q["norm"]
            q["is_duplicate"] = False # All in final list are unique originals

        # Structure wrapper similar to Anadolu files which have "questions": [...]
        # I will also add some metadata if it fits, though strict Anadolu format might just be {"questions": []}
        # Anadolu Raw files just have {"questions": [...]}.
        # Enriched files also have {"questions": [...]}.
        # I'll stick to {"questions": [...]} and put course info in meta fields inside questions if needed,
        # but user-courses.json questions already have source info.
        # However, preserving the course-level metadata (university, department) might be useful.
        # But to be "like Anadolu", maybe I should just keep questions.
        # Let's add a separate "meta" key, it won't hurt.

        data = {
            "questions": final_list,
            "meta": {
                "course_name": course_name,
                "term": term_str,
                "university": course.get('university'),
                "department": course.get('department')
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Created/Updated {output_path} with {len(final_list)} unique questions.")


if __name__ == "__main__":
    main()
