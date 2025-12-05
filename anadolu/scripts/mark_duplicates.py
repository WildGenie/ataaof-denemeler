#!/usr/bin/env python3
"""
Mark duplicate questions in enriched JSON files.
Includes both exact matches (text-based) and near-duplicates (embedding-based, 0.95+ similarity).
Adds 'is_duplicate' (boolean) and 'duplicate_of' (ID of the original question) fields.
Also adds 'occurrence_count' to the original question.
"""

import os
import json
import re
from collections import defaultdict
import glob

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
SIMILARITY_REPORT = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_answer(answer):
    """Normalize answer for comparison."""
    if not answer:
        return ""
    return answer.lower().strip()

def main():
    print("Marking duplicate questions (exact + near-duplicates)...")

    if not os.path.exists(JSON_DIR):
        print(f"Error: JSON directory not found at {JSON_DIR}")
        return

    # Load embedding similarity data
    near_duplicate_pairs = []
    if os.path.exists(SIMILARITY_REPORT):
        print("Loading embedding similarity data...")
        with open(SIMILARITY_REPORT, 'r', encoding='utf-8') as f:
            similarity_data = json.load(f)

        # Filter for near-duplicates (0.95+, same answer)
        for item in similarity_data:
            if item["similarity"] >= 0.95:
                ans1 = normalize_answer(item["q1"].get("answer", ""))
                ans2 = normalize_answer(item["q2"].get("answer", ""))

                if ans1 and ans2 and ans1 == ans2:
                    near_duplicate_pairs.append(item)

        print(f"Found {len(near_duplicate_pairs)} near-duplicate pairs from embeddings.")

    # Find all course files
    course_files = glob.glob(os.path.join(JSON_DIR, "**", "*Çıkmış Sorular - Enriched.json"), recursive=True)

    # Group files by course name
    files_by_course = defaultdict(list)
    for file_path in course_files:
        filename = os.path.basename(file_path)
        parts = filename.split(" - ")
        if len(parts) >= 3:
            course_name = parts[2]
            files_by_course[course_name].append(file_path)

    print(f"Found {len(files_by_course)} courses to process.")

    for course_name, files in files_by_course.items():
        print(f"Processing {course_name} ({len(files)} files)...")

        # Load all questions for this course
        all_questions = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for idx, q in enumerate(data.get('questions', [])):
                        q['_file_path'] = file_path
                        q['_index'] = idx
                        all_questions.append(q)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # Find duplicates by text
        text_map = defaultdict(list)
        for q in all_questions:
            q_text = q.get('question')
            if q_text:
                norm = normalize_text(q_text)
                text_map[norm].append(q)

        # Build duplicate groups (combining text-based and embedding-based)
        duplicate_groups = {}  # original_id -> [duplicate_ids]

        # 1. Text-based duplicates
        for norm_text, questions in text_map.items():
            if len(questions) > 1:
                def sort_key(q):
                    src = q.get('source', '')
                    years = re.findall(r'\d{4}', src)
                    year = int(years[0]) if years else 0
                    term_score = 0
                    if 'Ara' in src: term_score = 1
                    if 'Dönem' in src: term_score = 2
                    if 'Yaz' in src: term_score = 3
                    if 'Tek' in src: term_score = 4
                    return (year, term_score)

                questions.sort(key=sort_key)
                original = questions[0]
                original_id = original.get('id')

                if original_id not in duplicate_groups:
                    duplicate_groups[original_id] = []

                for dup in questions[1:]:
                    duplicate_groups[original_id].append(dup.get('id'))

        # 2. Embedding-based near-duplicates
        for item in near_duplicate_pairs:
            if item["q1"]["course"] != course_name:
                continue

            q1_id = item["q1"]["id"]
            q2_id = item["q2"]["id"]

            # Find which one should be original (lower ID or already marked as original)
            if q1_id in duplicate_groups:
                # q1 is already an original
                if q2_id not in duplicate_groups[q1_id]:
                    duplicate_groups[q1_id].append(q2_id)
            elif q2_id in duplicate_groups:
                # q2 is already an original
                if q1_id not in duplicate_groups[q2_id]:
                    duplicate_groups[q2_id].append(q1_id)
            else:
                # Neither is marked, use lower ID as original
                if q1_id < q2_id:
                    if q1_id not in duplicate_groups:
                        duplicate_groups[q1_id] = []
                    duplicate_groups[q1_id].append(q2_id)
                else:
                    if q2_id not in duplicate_groups:
                        duplicate_groups[q2_id] = []
                    duplicate_groups[q2_id].append(q1_id)

        # Prepare updates
        updates_by_file = defaultdict(dict)

        # Mark originals with occurrence_count
        for original_id, duplicate_ids in duplicate_groups.items():
            # Find original question
            for q in all_questions:
                if q.get('id') == original_id:
                    updates_by_file[q['_file_path']][q['_index']] = {
                        'occurrence_count': len(duplicate_ids) + 1,
                        'is_duplicate': False
                    }
                    break

        # Mark duplicates
        all_duplicate_ids = set()
        for original_id, duplicate_ids in duplicate_groups.items():
            all_duplicate_ids.update(duplicate_ids)

        for q in all_questions:
            q_id = q.get('id')
            if q_id in all_duplicate_ids:
                # Find which original this belongs to
                for original_id, dup_list in duplicate_groups.items():
                    if q_id in dup_list:
                        # Find original question to get source
                        original_source = None
                        for orig_q in all_questions:
                            if orig_q.get('id') == original_id:
                                original_source = orig_q.get('source')
                                break

                        updates_by_file[q['_file_path']][q['_index']] = {
                            'is_duplicate': True,
                            'duplicate_of': original_id,
                            'original_source': original_source
                        }
                        break

        # Mark unique questions
        for q in all_questions:
            q_id = q.get('id')
            if q_id not in duplicate_groups and q_id not in all_duplicate_ids:
                updates_by_file[q['_file_path']][q['_index']] = {
                    'is_duplicate': False,
                    'occurrence_count': 1
                }

        # Save changes to files
        for file_path, updates in updates_by_file.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                modified = False
                for idx, update_data in updates.items():
                    if idx < len(data['questions']):
                        q = data['questions'][idx]
                        for k, v in update_data.items():
                            if q.get(k) != v:
                                q[k] = v
                                modified = True

                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error updating {file_path}: {e}")

    print("Duplicate marking complete.")

if __name__ == "__main__":
    main()
