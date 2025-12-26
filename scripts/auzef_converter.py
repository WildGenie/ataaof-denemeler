import json
import os
import re

# Source file
SOURCE_FILE = './Auzef/user-courses.json'
# Base output dir
BASE_OUTPUT_DIR = './Auzef/json'

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"Source file not found: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    for course in courses:
        course_name = course.get('name')
        term_str = course.get('term') # e.g. "7. Dönem"

        # Extract term number
        if term_str:
            match = re.search(r'(\d+)', term_str)
            if match:
                term_num = match.group(1)
            else:
                 # Default or fallback if needed, but safe to skip or put in misc
                print(f"Warning: Could not extract term number from '{term_str}' for course '{course_name}'. Using 'Other'")
                term_num = "Other"
        else:
             term_num = "Other"

        if term_num == "Other":
             term_dir_name = "Other"
        else:
             term_dir_name = f"Donem {term_num}"

        output_dir = os.path.join(BASE_OUTPUT_DIR, term_dir_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Construct filename
        # Pattern matching Anadolu: Auzef - Dönem {N} - {CourseName} - Sorular.json
        safe_course_name = course_name.replace('/', '-').replace(':', '')
        filename = f"Auzef - Dönem {term_num} - {safe_course_name} - Sorular.json"
        output_path = os.path.join(output_dir, filename)

        # Prepare data
        questions = course.get('questions', [])

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
            "questions": questions,
            "meta": {
                "course_name": course_name,
                "term": term_str,
                "university": course.get('university'),
                "department": course.get('department')
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Created {output_path} with {len(questions)} questions.")

if __name__ == "__main__":
    main()
