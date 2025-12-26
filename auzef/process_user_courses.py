import json
import os
import re
from libs.auzef_lib import JSON_DIR, OUTPUT_DIR
from libs.shared import clean_html

# Load dersler.json to have a source of truth for course names
DERSLER_PATH = os.path.join(os.path.dirname(__file__), 'dersler.json')
course_mapping = {}
if os.path.exists(DERSLER_PATH):
    with open(DERSLER_PATH, 'r', encoding='utf-8') as f:
        dersler = json.load(f)
        for d in dersler:
            # Map normalized (lowercase) name to original CourseName from dersler.json
            name = d.get("CourseName")
            if name:
                course_mapping[name.lower()] = name

def get_mapped_course_name(name):
    if not name: return ""
    return course_mapping.get(name.lower(), name)

def process_user_courses():
    user_courses_path = os.path.join(OUTPUT_DIR, 'user-courses.json')
    if not os.path.exists(user_courses_path):
        print(f"File not found: {user_courses_path}")
        return

    with open(user_courses_path, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    for course in courses:
        raw_name = course.get('name')
        # Use mapped name if possible to ensure consistency with dersler.json
        course_name = get_mapped_course_name(raw_name)

        term_str = course.get('term', '')
        donem_match = re.search(r'(\d+)', term_str)
        donem = donem_match.group(1) if donem_match else "0"

        # Filter out Donem 1
        if donem == "1":
            continue

        questions = course.get('questions', [])
        if not questions:
            continue

        standard_questions = []
        chars = ['A', 'B', 'C', 'D', 'E']

        seen_ids = set()

        for q in questions:
            q_id = str(q.get('id', ''))
            if q_id in seen_ids:
                continue
            seen_ids.add(q_id)

            opts = q.get('options', [])
            opt_map = {chars[i]: clean_html(opts[i]) if i < len(opts) else "" for i in range(5)}

            correct_idx = q.get('correctIndex')
            dogru_cevap = chars[correct_idx] if correct_idx is not None and 0 <= correct_idx < 5 else ""

            # Map topic to Konu
            topic = q.get('topic', '')

            std_q = {
                "SoruID": str(q.get('id', '')),
                "SoruMetni": clean_html(q.get('question', '')),
                "A": opt_map.get('A', ''),
                "B": opt_map.get('B', ''),
                "C": opt_map.get('C', ''),
                "D": opt_map.get('D', ''),
                "E": opt_map.get('E', ''),
                "DogruCevap": dogru_cevap,
                "DersAd": course_name,
                "Unite": q.get('unit', 0),
                "Konu": topic,
                "Somestre": 0,
                "Aciklama": clean_html(q.get('explanation', '')),
                "Kaynak": q.get('source', '')
            }
            standard_questions.append(std_q)

        target_dir = os.path.join(JSON_DIR, f"Donem {donem}")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        filename = f"Auzef - Dönem {donem} - {course_name} - Sorular.json"
        filepath = os.path.join(target_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(standard_questions, f, ensure_ascii=False, indent=4)

        print(f"Processed {len(standard_questions)} questions for {course_name} (Donem {donem})")

if __name__ == "__main__":
    process_user_courses()
