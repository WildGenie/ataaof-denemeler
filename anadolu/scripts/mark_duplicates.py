#!/usr/bin/env python3
"""
Mark duplicate questions in enriched JSON files.
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

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Marking duplicate questions in enriched JSON files...")

    if not os.path.exists(JSON_DIR):
        print(f"Error: JSON directory not found at {JSON_DIR}")
        return

    # 1. Collect all questions by course to find duplicates
    # We process one course at a time to avoid memory issues and keep context local

    # Find all course files
    course_files = glob.glob(os.path.join(JSON_DIR, "**", "*Çıkmış Sorular - Enriched.json"), recursive=True)

    # Group files by course name
    files_by_course = defaultdict(list)
    for file_path in course_files:
        filename = os.path.basename(file_path)
        # Assuming filename format: Anadolu - Dönem X - Course Name - ...
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
                    # Store file path and index to update later
                    for idx, q in enumerate(data.get('questions', [])):
                        q['_file_path'] = file_path
                        q['_index'] = idx
                        all_questions.append(q)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # Find duplicates
        # Map normalized text to list of questions
        text_map = defaultdict(list)
        for q in all_questions:
            q_text = q.get('question')
            if q_text:
                norm = normalize_text(q_text)
                text_map[norm].append(q)

        # Mark duplicates
        updates_by_file = defaultdict(dict) # file_path -> {index -> updates}

        for norm_text, questions in text_map.items():
            if len(questions) > 1:
                # Sort by year/term (source) to keep the "latest" or "earliest" as original?
                # Let's keep the one that appears first in our list (which depends on file loading order)
                # Or better, keep the one with the most complete data?
                # For now, just take the first one as "original" and others as duplicates.

                # Sort by source to be deterministic (e.g. "Ara Sınav 2021" comes before "Dönem Sonu 2024")
                # Actually, usually we want to keep the LATEST one as the main one if we are updating content,
                # but for "hiding duplicates", we might want to show the first occurrence and hide subsequent ones?
                # The user said "Sadece ilkine göstermesi için not et".
                # So we treat the first one (chronologically) as the original.

                # Simple heuristic for sorting sources: Year then Term
                def sort_key(q):
                    src = q.get('source', '')
                    # Extract year
                    years = re.findall(r'\d{4}', src)
                    year = int(years[0]) if years else 0
                    # Term priority: Güz < Bahar < Yaz ? Or Ara < Dönem < Yaz?
                    term_score = 0
                    if 'Ara' in src: term_score = 1
                    if 'Dönem' in src: term_score = 2
                    if 'Yaz' in src: term_score = 3
                    if 'Tek' in src: term_score = 4
                    return (year, term_score)

                questions.sort(key=sort_key)

                original = questions[0]
                duplicates = questions[1:]

                # Update original
                updates_by_file[original['_file_path']][original['_index']] = {
                    'occurrence_count': len(questions),
                    'is_duplicate': False
                }

                # Update duplicates
                for dup in duplicates:
                    updates_by_file[dup['_file_path']][dup['_index']] = {
                        'is_duplicate': True,
                        'duplicate_of': original.get('id'),
                        'original_source': original.get('source')
                    }
            else:
                # Unique question
                q = questions[0]
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
                        # Only update if changed
                        q = data['questions'][idx]
                        for k, v in update_data.items():
                            if q.get(k) != v:
                                q[k] = v
                                modified = True

                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    # print(f"Updated {os.path.basename(file_path)}")

            except Exception as e:
                print(f"Error updating {file_path}: {e}")

    print("Duplicate marking complete.")

if __name__ == "__main__":
    main()
