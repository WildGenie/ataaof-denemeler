#!/usr/bin/env python3
"""
Analyze similar questions (near-duplicates) in "Çıkmış Sorular".
Uses SequenceMatcher to find questions with high text similarity (> 85%) but not identical.
Generates a JSON report with diffs, option comparisons, and answer checks.
"""

import os
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
import difflib
import concurrent.futures

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
JSON_REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "similarity_analysis.json")

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()

def process_course_questions(course_name, questions):
    """
    Compare questions within a course to find similarities.
    Returns a list of similar pairs.
    """
    similar_pairs = []
    # Deduplicate by exact text first to avoid redundant comparisons
    unique_questions = {}
    for q in questions:
        norm = normalize_text(q['question'])
        if norm not in unique_questions:
            unique_questions[norm] = q

    unique_list = list(unique_questions.values())
    n = len(unique_list)

    for i in range(n):
        for j in range(i + 1, n):
            q1 = unique_list[i]
            q2 = unique_list[j]

            text1 = normalize_text(q1['question'])
            text2 = normalize_text(q2['question'])

            # Optimization: Skip if length difference is huge
            if abs(len(text1) - len(text2)) > len(text1) * 0.3:
                continue

            score = calculate_similarity(text1, text2)

            if 0.85 <= score < 1.0: # High similarity but not identical
                similar_pairs.append({
                    'score': score,
                    'q1': q1,
                    'q2': q2
                })

    return course_name, similar_pairs

def main():
    print("Starting similarity analysis...")

    if not os.path.exists(JSON_DIR):
        print(f"Error: JSON directory not found at {JSON_DIR}")
        return

    questions_by_course = defaultdict(list)
    file_count = 0
    total_questions = 0

    # Scan directories
    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" in filename:
                file_path = os.path.join(donem_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    course_name = filename.split(" - ")[2]

                    for q in data.get("questions", []):
                        if q.get("question"):
                            q['source_file'] = filename
                            questions_by_course[course_name].append(q)
                            total_questions += 1

                    file_count += 1
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    print(f"Scanned {file_count} files, {total_questions} questions.")
    print(f"Analyzing {len(questions_by_course)} courses for internal similarities...")

    all_similarities = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_course_questions, name, qs): name for name, qs in questions_by_course.items()}

        for future in concurrent.futures.as_completed(futures):
            course_name, pairs = future.result()
            if pairs:
                all_similarities.extend([(course_name, p) for p in pairs])
                print(f"  Found {len(pairs)} similar pairs in {course_name}")

    # Sort by score descending
    all_similarities.sort(key=lambda x: x[1]['score'], reverse=True)

    json_output = []

    for course_name, item in all_similarities:
        q1 = item['q1']
        q2 = item['q2']

        # Generate diff for question text
        text1 = q1['question']
        text2 = q2['question']

        # Character based diff
        diff = list(difflib.ndiff(text1, text2))
        diff_str = "".join(diff)

        # Compare Options (Sort and Compare)
        opts1 = q1.get('options', [])
        opts2 = q2.get('options', [])

        norm_opts1 = sorted([normalize_text(o) for o in opts1])
        norm_opts2 = sorted([normalize_text(o) for o in opts2])

        options_match = (norm_opts1 == norm_opts2)

        # Compare Correct Answer
        ans1 = opts1[q1['correctIndex']] if opts1 and 0 <= q1.get('correctIndex', -1) < len(opts1) else None
        ans2 = opts2[q2['correctIndex']] if opts2 and 0 <= q2.get('correctIndex', -1) < len(opts2) else None

        answer_match = False
        if ans1 and ans2:
            answer_match = (normalize_text(ans1) == normalize_text(ans2))
        elif ans1 is None and ans2 is None:
            answer_match = True

        json_output.append({
            "course": course_name,
            "similarity_score": item['score'],
            "question1": {
                "id": q1.get("id"),
                "text": q1.get("question"),
                "source": q1.get("source"),
                "answer": ans1,
                "options": opts1
            },
            "question2": {
                "id": q2.get("id"),
                "text": q2.get("question"),
                "source": q2.get("source"),
                "answer": ans2,
                "options": opts2
            },
            "analysis": {
                "text_diff": diff_str,
                "options_match": options_match,
                "answer_match": answer_match
            }
        })

    with open(JSON_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=4, ensure_ascii=False)

    print(f"Similarity JSON report generated at {JSON_REPORT_PATH}")

if __name__ == "__main__":
    main()
