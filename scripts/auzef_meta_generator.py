import json
import os
import re
import shutil
from urllib.parse import quote

# Paths
AUZEF_ROOT = '/Users/wildgenie/Projects/ATA-AOF-Grafik-Sanatlar/auzef'
AUZEF_JSON_DIR = os.path.join(AUZEF_ROOT, 'json')
AUZEF_SORULAR_DIR = os.path.join(AUZEF_ROOT, 'sorular')
ANADOLU_INTERAKTIF_PATH = '/Users/wildgenie/Projects/ATA-AOF-Grafik-Sanatlar/anadolu/interaktif.html'

def load_json_files():
    courses = {} # Key: Term, Value: List of course data

    if not os.path.exists(AUZEF_JSON_DIR):
        print(f"Directory not found: {AUZEF_JSON_DIR}")
        return courses

    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if file.endswith('.json'):
                full_path = os.path.join(root, file)

                # Extract info from filename: Auzef - Dönem {Term} - {Course} - Sorular.json
                # or similar.
                match = re.search(r'Auzef - Dönem (\d+) - (.+) - Sorular\.json', file)
                if match:
                    term = int(match.group(1))
                    course_name = match.group(2)
                else:
                    # Fallback if naming is different, try to guess or skip
                    # Attempt to extract term from directory name
                    parent_dir = os.path.basename(root)
                    term_match = re.search(r'Donem (\d+)', parent_dir)
                    if term_match:
                        term = int(term_match.group(1))
                    else:
                        term = 99 # Misc

                    course_name = file.replace('.json', '')

                # Read JSON to get question count/content
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        questions = data.get('questions', [])
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")
                    questions = []

                course_info = {
                    "term": term,
                    "name": course_name,
                    "json_path": full_path,
                    "relative_json_url": os.path.relpath(full_path, start=AUZEF_ROOT), # Relative to interaktif.html
                    "questions": questions
                }

                if term not in courses:
                    courses[term] = []
                courses[term].append(course_info)

    return courses

def generate_dersler_json(courses):
    if not os.path.exists(AUZEF_SORULAR_DIR):
        os.makedirs(AUZEF_SORULAR_DIR)

    output_list = []

    # Sort terms
    sorted_terms = sorted(courses.keys())

    for term in sorted_terms:
        term_courses = courses[term]
        # Sort courses by name
        term_courses.sort(key=lambda x: x['name'])

        dersler_list = []
        for course in term_courses:
            dersler_list.append({
                "dersAdi": course['name'],
                "sources": [
                    {
                        "name": "Sorular",
                        "url": course['relative_json_url']
                    }
                ]
            })

        output_list.append({
            "donem": term,
            "dersler": dersler_list
        })

    output_path = os.path.join(AUZEF_SORULAR_DIR, 'dersler.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, ensure_ascii=False, indent=4)
    print(f"Generated dersler.json at {output_path}")

def generate_markdown_file(course_info):
    questions = course_info['questions']
    course_name = course_info['name']
    term = course_info['term']

    content = f"# {course_name} - Sorular\n\n"

    # Logic to normalize unit key
    def get_unit_key(unit_val):
        if not unit_val:
            return "Genel"
        s = str(unit_val).strip()
        # If it looks like a number, prefix with Ünite
        if s.isdigit():
             return f"Ünite {s}"
        # If it starts with "Ünite", keep it, but normalize spacing/case
        if s.lower().startswith("ünite"):
             # Normalize spacing if needed, e.g. "Ünite  1" -> "Ünite 1"
             parts = s.split()
             if len(parts) >= 2 and parts[1].isdigit():
                 return f"Ünite {parts[1]}"
             return s.capitalize()
        return f"Ünite {s}" # Fallback

    # Group by Unit
    grouped_by_unit = {}
    for q in questions:
        unit = q.get('unit')
        unit_key = get_unit_key(unit)
        if unit_key not in grouped_by_unit:
            grouped_by_unit[unit_key] = []
        grouped_by_unit[unit_key].append(q)

    # Sort units
    def sort_key(k):
        m = re.search(r'(\d+)', k)
        return int(m.group(1)) if m else 999

    sorted_units = sorted(grouped_by_unit.keys(), key=sort_key)

    for unit in sorted_units:
        content += f"## {unit}\n\n"
        unit_questions = grouped_by_unit[unit]

        # Group by Topic within Unit
        grouped_by_topic = {}
        no_topic_questions = []

        for q in unit_questions:
            topic = q.get('topic')
            if topic:
                if topic not in grouped_by_topic:
                    grouped_by_topic[topic] = []
                grouped_by_topic[topic].append(q)
            else:
                no_topic_questions.append(q)

        # Sort topics
        def topic_sort_key(t):
             # parse 1.1.1 or 10.1.1
             # Split by dots or other non-digits
             nums = []
             # Find sequence of digits
             # Example: "10.1.1. Topic" -> [10, 1, 1]
             # We want to match dotted numbers at start
             m = re.match(r'^([\d\.]+)', t)
             if m:
                 parts = m.group(1).split('.')
                 for p in parts:
                     if p.isdigit():
                         nums.append(int(p))
             else:
                 # Try finding any numbers
                 parts = re.findall(r'\d+', t)
                 for p in parts:
                     nums.append(int(p))

             return nums if nums else [999]

        sorted_topics = sorted(grouped_by_topic.keys(), key=lambda t: (topic_sort_key(t), t))

        # Process topics
        for topic in sorted_topics:
            q_list = grouped_by_topic[topic]
            content += f"### {topic}\n\n"
            for idx, q in enumerate(q_list, 1):
               content += format_question_md(q, idx)

        # Then questions without topics
        if no_topic_questions:
            if grouped_by_topic:
                content += f"### Diğer\n\n"
            for idx, q in enumerate(no_topic_questions, 1):
                content += format_question_md(q, idx)

    return content

def format_question_md(q, idx):
    q_text = q.get('question', '').replace('<br>', '\n')
    options = q.get('options', [])
    correct_idx = q.get('correctIndex', -1)
    explanation = q.get('explanation', '')

    md = f"{idx}. {q_text}\n"

    letters = ['A', 'B', 'C', 'D', 'E']
    for i, opt in enumerate(options):
        prefix = letters[i] if i < len(letters) else '?'
        is_correct = (i == correct_idx)

        if is_correct:
            md += f"    - **Cevap {prefix}-) {opt}**\n"
        else:
            md += f"    - {prefix}-) {opt}\n"

    md += "\n"

    if explanation:
        md += f"    > **Açıklama:** {explanation}\n\n"

    md += "    <hr />\n\n"
    return md

def generate_structure_and_mds(courses):
    # Root index content
    root_index_content = "# Auzef - Ders Materyalleri\n\n"

    sorted_terms = sorted(courses.keys())
    for term in sorted_terms:
        root_index_content += f"## Dönem {term}\n\n"

        term_courses = courses[term]
        term_courses.sort(key=lambda x: x['name'])

        for course in term_courses:
            # Create Course Directory
            # Format: auzef/Donem X/CourseName/
            course_dir_name = course['name'].replace('/', '-')
            term_dir_name = f"Donem {term}"
            course_path = os.path.join(AUZEF_ROOT, term_dir_name, course_dir_name)

            if not os.path.exists(course_path):
                os.makedirs(course_path)

            # Generate MD content
            md_content = generate_markdown_file(course)
            md_filename = "Sorular.md"
            md_file_path = os.path.join(course_path, md_filename)

            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Generate Course Index MD
            # URL encoding for links
            md_url = quote(md_filename)
            course_index_content = f"# {course['name']}\n\n## Ders Materyalleri\n\n### [📝 Sorular]({md_url})\n\n[🔙 Ana Sayfaya Dön](../../)\n"

            with open(os.path.join(course_path, 'index.md'), 'w', encoding='utf-8') as f:
                f.write(course_index_content)

            # Add entry to Root Index
            # Link format: Donem%20{Term}/{CourseEncoded}/

            # Need strict URL encoding for markdown links to work on file system or github pages
            # Path relative to root index
            rel_path = f"{term_dir_name}/{course_dir_name}/"
            # Encode each component
            rel_path_encoded = "/".join([quote(part) for part in rel_path.split('/') if part])

            root_index_content += f"- 📂 [{course['name']}]({rel_path_encoded}/)\n"

        root_index_content += "\n---\n\n"

    with open(os.path.join(AUZEF_ROOT, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(root_index_content)
    print("Generated root index.md and course MDs.")

def copy_interaktif_html():
    if os.path.exists(ANADOLU_INTERAKTIF_PATH):
        dest = os.path.join(AUZEF_ROOT, 'interaktif.html')
        shutil.copy2(ANADOLU_INTERAKTIF_PATH, dest)
        print(f"Copied interaktif.html to {dest}")
    else:
        print("Could not find source interaktif.html")

def main():
    print("Starting Auzef Metadata Generation...")
    courses = load_json_files()
    if not courses:
        print("No courses found.")
        return

    generate_dersler_json(courses)
    generate_structure_and_mds(courses)
    copy_interaktif_html()
    print("Done.")

if __name__ == "__main__":
    main()
