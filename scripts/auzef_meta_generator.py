import json
import os
import re
import shutil
import sys
from urllib.parse import quote

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shared import safe_html_to_markdown

# Paths
# Paths
AUZEF_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'Auzef')
AUZEF_JSON_DIR = os.path.join(AUZEF_ROOT, 'json')
AUZEF_SORULAR_DIR = os.path.join(AUZEF_ROOT, 'sorular')
ANADOLU_INTERAKTIF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'Anadolu', 'interaktif.html')

def load_json_files():
    courses = {} # Key: Term, Value: List of course data

    if not os.path.exists(AUZEF_JSON_DIR):
        print(f"Directory not found: {AUZEF_JSON_DIR}")
        return courses

    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if not file.endswith('.json') or file.endswith('Raw.json'):
                continue

            full_path = os.path.join(root, file)

            # Extract info from filename
            # Expected formats:
            # Auzef - Dönem {Term} - {Course} - Sorular.json
            # Auzef - Dönem {Term} - {Course} - Alıştırma Soruları.json

            term = 0
            course_name = ""
            type_label = "Sorular"

            # Try to parse filename
            parts = file.replace('.json', '').split(' - ')
            if len(parts) >= 4:
                # [Auzef, Dönem X, Course Name, Type]
                term_str = parts[1].replace('Dönem ', '')
                if term_str.isdigit():
                    term = int(term_str)

                # Fix for Course Names containing " - " like "Psikometrik - Gelişimsel ..."
                # If parts length is > 4, it means course name itself had split chars.
                # parts[0] = Auzef, parts[1] = Donem X
                # parts[-1] is the Type suffix (Sorular.json / Alıştırma Soruları.json)
                # Everything in between is Course Name

                type_suffix = parts[-1]
                course_name_parts = parts[2:-1] # From 2 to second last
                course_name = " - ".join(course_name_parts)

                if "Alıştırma" in type_suffix:
                    type_label = "Alıştırma Soruları"
                else:
                    type_label = "Çıkmış Sorular"
            else:
                 # Fallback logic
                 continue

            # Read JSON to get question count/content
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions = data # The file is a list of questions
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                questions = []

            course_info = {
                "term": term,
                "name": course_name,
                "type": type_label,
                "json_path": full_path,
                "relative_json_url": os.path.relpath(full_path, start=AUZEF_ROOT),
                "questions": questions
            }

            if term not in courses:
                courses[term] = {}

            if course_name not in courses[term]:
                courses[term][course_name] = []

            courses[term][course_name].append(course_info)

    return courses

def generate_dersler_json(courses):
    if not os.path.exists(AUZEF_SORULAR_DIR):
        os.makedirs(AUZEF_SORULAR_DIR)

    output_list = []

    # Sort terms
    sorted_terms = sorted(courses.keys())

    # Load dersler.json for canonical names if possible (Legacy)
    canonical_names = {}
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auzef', 'dersler.json'), 'r') as f:
            dersler_ref = json.load(f)
            for d in dersler_ref:
                n = d.get('CourseName')
                if n: canonical_names[n.lower()] = n
    except:
        pass

    # Load Official Curriculum (Generated from parse_curriculum.py)
    curriculum_map = {} # Key: normalized_lower_name -> {name: OfficialName, term: OfficialTerm}
    curriculum_courses = []
    try:
         with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auzef', 'curriculum_courses.json'), 'r', encoding='utf-8') as f:
             curriculum_courses = json.load(f)
             for c in curriculum_courses:
                 # Normalize regex-like for better matching
                 # Remove spaces, Turkish chars normalization if needed (simple lower for now)
                 norm_name = c['name'].lower().strip()
                 curriculum_map[norm_name] = c
    except Exception as e:
        print(f"Warning: Could not load curriculum_courses.json: {e}")

    # Helper for normalization
    def normalize_name(n):
        return n.lower().strip()


    for term in sorted_terms:
        term_courses_map = courses[term]

        # Consolidate courses with case-insensitive naming
        # Merging Logic:
        # 1. Use existing scanned courses.
        # 2. Add missing curriculum courses for this term.

        # We need a new map that includes everything.
        final_term_courses = {}

        def fix_course_name(text):
            words = text.split()
            res = []
            for i, w in enumerate(words):
                if i > 0 and w.lower() in ['ve', 'ile', 'veya', 'de', 'da']:
                    res.append(w.lower())
                else:
                    res.append(w.title())
            return " ".join(res)

        # Process Scanned Courses
        for c_name_raw, info_list in term_courses_map.items():
            lower_name = c_name_raw.lower().strip()

            # Try to match with curriculum
            official_name = c_name_raw # Default

            # 1. Direct match
            if lower_name in curriculum_map:
                official_name = curriculum_map[lower_name]['name']

            # 2. Fuzzy/Canonical match fallback
            elif lower_name in canonical_names:
                official_name = canonical_names[lower_name]

            # Apply "Ve" fix if no official match found (or even if found, just to be safe if official has different casing preference?)
            # Actually official dict should have correct casing.
            if lower_name not in curriculum_map:
                 official_name = fix_course_name(official_name)

            if official_name not in final_term_courses:
                final_term_courses[official_name] = []
            final_term_courses[official_name].extend(info_list)

        # Add Missing Curriculum Courses for THIS Term
        # Only add if not already present (fuzzy check)
        existing_normalized = set(k.lower().strip() for k in final_term_courses.keys())

        for c in curriculum_courses:
            if c['term'] == term:
                official_name = c['name']
                norm_official = official_name.lower().strip()

                if norm_official not in existing_normalized:
                    # Add as a placeholder course with no sources
                    final_term_courses[official_name] = []

        # Sort course names
        sorted_course_names = sorted(final_term_courses.keys())

        dersler_list = []
        for course_name in sorted_course_names:
            info_list = final_term_courses[course_name]

            # Sort sources (Sorular first)
            def source_sort(info):
                if "Çıkmış" in info['type']: return 0
                return 1

            info_list.sort(key=source_sort)

            sources = []
            for info in info_list:
                # Deduplicate sources based on type? Or just list all?
                # Let's list all unique by type to be safe
                if any(s['name'] == info['type'] for s in sources):
                    continue

                sources.append({
                    "name": info['type'],
                    "url": info['relative_json_url']
                })

            # Get ID from curriculum map if available
            course_id = None
            lower_name = course_name.lower().strip()
            if lower_name in curriculum_map:
                course_id = curriculum_map[lower_name].get('id')

            dersler_list.append({
                "dersAdi": course_name,
                "id": course_id,
                "sources": sources
            })

        output_list.append({
            "donem": term,
            "dersler": dersler_list
        })

    # Add Terms from Curriculum that might have NO scanned files (e.g. Terms that were totally missing)
    # Check if we missed any terms present in curriculum
    curriculum_terms = set(c['term'] for c in curriculum_courses)
    processed_terms = set(sorted_terms)
    missing_terms = curriculum_terms - processed_terms

    for term in sorted(list(missing_terms)):
        # Don't skip term 1 if it's in curriculum

        term_courses = [c for c in curriculum_courses if c['term'] == term]
        dersler_list = []
        for c in term_courses:
             dersler_list.append({
                "dersAdi": c['name'],
                "id": c.get('id'),
                "sources": [] # No sources
            })

        # Insert in order? output_list is sorted by term.
        # Just append and sort later.
        output_list.append({
            "donem": term,
            "dersler": sorted(dersler_list, key=lambda x: x['dersAdi'])
        })

    # Re-sort output_list by donem
    output_list.sort(key=lambda x: x['donem'])

    output_path = os.path.join(AUZEF_SORULAR_DIR, 'dersler.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, indent=4, ensure_ascii=False)

    # Also save to the project root auzef/dersler.json as requested
    root_dersler_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auzef', 'dersler.json')
    with open(root_dersler_path, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, indent=4, ensure_ascii=False)

    print(f"Generated dersler.json with {len(output_list)} semesters.")
    return output_list

def generate_markdown_file(course_info, include_units=None):
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
    for idx, q in enumerate(questions):
        unit = q.get('unit') or q.get('Unite')

        unit_key = get_unit_key(unit)
        if unit_key not in grouped_by_unit:
            grouped_by_unit[unit_key] = []
        grouped_by_unit[unit_key].append(q)

    # Sort units
    def sort_key(k):
        # Extract unit number
        m = re.search(r'(\d+)', str(k))
        return int(m.group(1)) if m else 999

    sorted_units = sorted(grouped_by_unit.keys(), key=sort_key)

    for unit in sorted_units:
        # Check explicit inclusions
        # Extract unit number for filtering
        unit_num_match = re.search(r'(\d+)', unit)
        unit_num = int(unit_num_match.group(1)) if unit_num_match else 0

        # If include_units is specified (not None/Empty) and unit_num is NOT in it, skip
        if include_units and unit_num not in include_units:
             continue

        content += f"## {unit}\n\n"
        unit_questions = grouped_by_unit[unit]

        # Group by Topic within Unit
        grouped_by_topic = {}
        no_topic_questions = []

        for q in unit_questions:
            topic = q.get('topic') or q.get('Konu')
            if topic:
                if topic not in grouped_by_topic:
                    grouped_by_topic[topic] = []
                grouped_by_topic[topic].append(q)
            else:
                no_topic_questions.append(q)

        # Sort topics
        def topic_sort_key(t):
             m = re.match(r'^([\d\.]+)', t)
             if m:
                 # Remove trailing dot if present to avoid empty string at end
                 clean_ver = m.group(1).strip('.')
                 parts = clean_ver.split('.')
                 nums = []
                 for p in parts:
                     if p.isdigit():
                         nums.append(int(p))
                 # print(f"DEBUG TOPIC SORT: '{t}' -> {nums}")
                 return nums
             # print(f"DEBUG TOPIC SORT (NO MATCH): '{t}' -> [999]")
             return [999]

        sorted_topics = sorted(grouped_by_topic.keys(), key=topic_sort_key)

        for topic in sorted_topics:
            content += f"### {topic}\n\n"
            for idx, q in enumerate(grouped_by_topic[topic], 1):
                content += format_question_md(q, idx)

        if no_topic_questions:
            if sorted_topics: # Only add header if there were other topics
                content += "### Diğer\n\n"
            for idx, q in enumerate(no_topic_questions, 1):
                content += format_question_md(q, idx)

    return content

def format_question_md(q, idx):
    # Try different key formats (Normal vs AUZEF Standard)
    q_text_content = q.get('question') or q.get('SoruMetni', '')
    # Use shared converter for consistency and escaping/HTML preservation
    q_text = safe_html_to_markdown(str(q_text_content))
    q_text = q_text.replace('\n', '<br />') # Use br for newlines

    explanation_content = q.get('explanation') or q.get('Aciklama', '')
    explanation = safe_html_to_markdown(str(explanation_content))
    explanation = explanation.replace('\n', '<br />')

    # Handle Options and Correct Answer
    # Format 1: 'options' list + 'correctIndex'
    options = q.get('options', [])
    correct_idx = q.get('correctIndex', -1)

    # Format 2: 'A', 'B', 'C', 'D', 'E' keys + 'DogruCevap' string
    dogru_cevap = q.get('DogruCevap', '')

    if not options and (q.get('A') or q.get('B')):
        options = [
            q.get('A', ''),
            q.get('B', ''),
            q.get('C', ''),
            q.get('D', ''),
            q.get('E', '')
        ]
        # Remove empty options at the end if any (though usually 5 options exist)
        # Convert DogruCevap 'A' -> 0, 'B' -> 1 etc.
        letter_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
        correct_idx = letter_map.get(dogru_cevap, -1)

    md = f"{idx}. {q_text}\n"

    letters = ['A', 'B', 'C', 'D', 'E']
    for i, opt in enumerate(options):
        # Skip if option text is empty and we are past valid options?
        if not opt: continue

        prefix = letters[i] if i < len(letters) else '?'
        is_correct = (i == correct_idx)

        opt_text = safe_html_to_markdown(opt)
        opt_text = opt_text.replace('\n', ' ')

        bold_wrapper = "**" if is_correct else ""
        ans_prefix = "**Cevap " if is_correct else ""

        md += f"    - {ans_prefix}{prefix}-) {opt_text}{bold_wrapper}\n"

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

        term_courses_map = courses[term]

        # Sort course names
        sorted_course_names = sorted(term_courses_map.keys())

        for course_name in sorted_course_names:
            info_list = term_courses_map[course_name]

            # We need to pick ONE primary source to generate the main MD structure or combine them?
            # For now, let's pick "Çıkmış Sorular" or the first available one as the representative for MD content
            # BUT actually, the markdown generation Logic in generate_markdown_file takes ONE "course_info" object.
            # If we have multiple (Sorular + Alıştırma), we might want to generate separate MDs or just one combined?
            # The current pipeline actually generates separate MDs (Sorular.md, Alıştırma Soruları.md) in the pipeline code.
            # This script seems to be re-doing that work or doing it for static export.

            # Let's prioritize "Sorular" (Çıkmış) for the main "Sorular.md" if available,
            # but ideally we should probably iterate and generate both if we want to be complete.
            # For the purpose of "Root Index", we link to the FOLDER.

            # Let's use the first one to get name/path info
            primary_info = info_list[0]
            for info in info_list:
                if "Çıkmış" in info['type']:
                    primary_info = info
                    break

            # Create Course Directory
            # Format: auzef/Donem X/CourseName/
            course_dir_name = course_name.replace('/', '-')
            term_dir_name = f"Donem {term}"
            course_path = os.path.join(AUZEF_ROOT, term_dir_name, course_dir_name)

            # Apply fix for "Ve" capitalized inside sentence for directory names/links
            def fix_course_name(text):
                words = text.split()
                res = []
                for i, w in enumerate(words):
                    if i > 0 and w.lower() in ['ve', 'ile', 'veya', 'de', 'da']:
                        res.append(w.lower())
                    else:
                        res.append(w)
                return " ".join(res)

            folder_name = fix_course_name(course_name)
            folder_name_encoded = quote(folder_name)

            # Update root index with FIXED name
            root_index_content += f"- 📂 [{folder_name}]({term_dir_name}/{folder_name_encoded}/)\n"

            if not os.path.exists(course_path):
                os.makedirs(course_path)

            # Prepare Course Index content
            course_index_content = f"# {folder_name}\n\n## Ders Materyalleri\n\n"
            course_index_content += "[🔙 Ana Sayfaya Dön](../../)\n\n"

            # Generate MD content for ALL sources in the info_list
            for info in info_list:
                md_content = generate_markdown_file(info)

                # Determine filename based on type
                if "Alıştırma" in info['type']:
                    md_filename = "Alıştırma Soruları.md"
                    label = "📝 Alıştırma Soruları"
                else:
                    md_filename = "Sorular.md"
                    label = "📝 Çıkmış Sorular"

                md_file_path = os.path.join(course_path, md_filename)
                with open(md_file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                # Add link to course index
                md_url = quote(md_filename)
                course_index_content += f"- [{label}]({md_url})\n"

            with open(os.path.join(course_path, 'index.md'), 'w', encoding='utf-8') as f:
                f.write(course_index_content)

            # Link to FOLDER in Root Index (Already done above with FIXED name)
            # Remove duplicate logic if present below

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
