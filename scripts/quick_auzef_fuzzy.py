from difflib import SequenceMatcher
import os
import json
import glob
import re
from collections import defaultdict
from tqdm import tqdm

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Auzef", "json")

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def main():
    print("Collecting questions for fuzzy matching...")
    json_files = glob.glob(os.path.join(AUZEF_JSON_DIR, "**", "*.json"), recursive=True)

    questions_by_course = defaultdict(list)
    for file_path in json_files:
        if "user-courses.json" in file_path: continue
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            course_name = data.get("meta", {}).get("course_name", "Unknown")
            for q in data.get("questions", []):
                questions_by_course[course_name].append({
                    "id": q.get("id"),
                    "text": q.get("question"),
                    "norm": normalize_text(q.get("question"))
                })

    print("\nFUZZY MATCHING REPORT (Ratio > 0.85)")
    print("="*50)

    found = False
    for course, questions in questions_by_course.items():
        if len(questions) < 2: continue

        for i in range(len(questions)):
            for j in range(i + 1, len(questions)):
                q1 = questions[i]
                q2 = questions[j]

                # If they were exact normalized matches, they would have been removed.
                # So we check for high similarity but not exact.
                if q1["norm"] == q2["norm"]: continue

                ratio = similarity(q1["norm"], q2["norm"])
                if ratio > 0.85:
                    found = True
                    print(f"Course: {course}")
                    print(f"Similarity Ratio: {ratio:.4f}")
                    print(f"  Q1 ({q1['id']}): {q1['text'][:100]}...")
                    print(f"  Q2 ({q2['id']}): {q2['text'][:100]}...")
                    print("-" * 30)

    if not found:
        print("No fuzzy near-duplicates found in the same course.")

if __name__ == "__main__":
    main()
