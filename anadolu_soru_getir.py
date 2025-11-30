import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
import markdownify
import re
from dotenv import load_dotenv

# Configuration
DERSLER_FILE = "anadolu_dersler.json"
OUTPUT_DIR = "output"
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
RAW_JSON_DIR = os.path.join(OUTPUT_DIR, "json_raw") # New raw directory
MD_DIR = os.path.join("sorular-anadolu", "md")
FULL_JSON_DIR = "sorular-anadolu"

# Load environment variables
load_dotenv()

HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://ekampus.anadolu.edu.tr',
    'accept': '*/*',
    'authorization': os.getenv('ANADOLU_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYXCOeM'),
}

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    if not os.path.exists(RAW_JSON_DIR): # Create raw dir
        os.makedirs(RAW_JSON_DIR)
    if not os.path.exists(FULL_JSON_DIR):
        os.makedirs(FULL_JSON_DIR)
    if not os.path.exists(MD_DIR):
        os.makedirs(MD_DIR)

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                print(f"Error: Status code {response.status} for URL: {url}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error for {url}: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_unit_questions(course_code, unit):
    # Updated to create/10 based on JS reference
    url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/create/20/{urllib.parse.quote(course_code)}/{unit}"
    return fetch_url(url)

def fetch_vize_questions(course_code):
    # Vize is '1'
    url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/createvizefinal/20/{urllib.parse.quote(course_code)}/1"
    return fetch_url(url)

def fetch_final_questions(course_code):
    # Final is '0' (implied else block in JS)
    url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/createvizefinal/20/{urllib.parse.quote(course_code)}/0"
    return fetch_url(url)

def get_or_fetch_raw_unit_questions(course_code, course_name, unit, donem):
    # Construct raw filename
    # Filename format: Anadolu - Dönem {donem} - {course_name} - Unite {unit} - Raw.json
    safe_course_name = "".join([c for c in course_name if c.isalnum() or c in (' ', '-', '_')]).strip()
    raw_filename = f"Anadolu - Dönem {donem} - {safe_course_name} - Unite {unit:02d} - Raw.json"
    raw_filepath = os.path.join(RAW_JSON_DIR, raw_filename)

    # 1. Try to load from file
    if os.path.exists(raw_filepath):
        try:
            with open(raw_filepath, 'r', encoding='utf-8') as f:
                raw_questions = json.load(f)
            print(f"    Loaded {len(raw_questions)} raw questions from cache.")
            return raw_questions
        except Exception as e:
            print(f"    Error loading raw cache: {e}. Will re-fetch.")

    # 2. Fetch from API if not found or error
    raw_questions_map = {} # Use map to deduplicate by ID within this fetch session

    # Retry/Accumulate logic (7 times)
    for i in range(7):
        data = fetch_unit_questions(course_code, unit)
        if data and "Questions" in data and data["Questions"] is not None:
            for q in data["Questions"]:
                q_id = q["QuestionId"]
                raw_questions_map[q_id] = q
        time.sleep(0.2) # Small delay to be nice

    raw_questions = list(raw_questions_map.values())

    # 3. Save to file
    try:
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(raw_questions, f, ensure_ascii=False, indent=4)
        print(f"    Fetched and saved {len(raw_questions)} raw questions.")
    except Exception as e:
        print(f"    Error saving raw cache: {e}")

    return raw_questions

def process_question_list(raw_questions, course_name, unit_val, donem, seen_ids, all_questions, fetched_ids_in_run):
    new_count = 0
    total_count = len(raw_questions)

    for q in raw_questions:
        q_id = q["QuestionId"]
        fetched_ids_in_run.add(q_id)
        if q_id not in seen_ids:
            # Use unit_val for the JSON field "Unite"
            mapped_q = map_to_old_format(q, course_name, unit_val, donem)
            all_questions.append(mapped_q)
            seen_ids.add(q_id)
            new_count += 1

    return new_count, total_count

def main():
    setup_directories()

    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses to process.")

    for course in courses:
        course_code = course['DersKodu']
        course_name = course['CourseName']
        donem = course['Donem']

        if not course_code:
            continue

        print(f"Processing {course_code} - {course_name} (Dönem {donem})...")

        all_questions = []
        seen_ids = set()
        fetched_ids_in_run = set()

        # Load existing questions if available
        all_filename = f"Anadolu - Dönem {donem} - {course_name} - Tüm Sorular.json"
        all_path = os.path.join(FULL_JSON_DIR, all_filename)

        if os.path.exists(all_path):
            try:
                with open(all_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        all_questions = existing_data
                        for q in all_questions:
                            if "SoruID" in q:
                                seen_ids.add(q["SoruID"])
                        print(f"  Loaded {len(all_questions)} existing questions.")
            except Exception as e:
                print(f"  Error loading existing questions: {e}")

        initial_count = len(all_questions)

        # 1. Fetch Unit Questions
        for unit in range(1, 15): # Units 1 to 14
            print(f"  Fetching Unit {unit}...", end="", flush=True)

            # Get raw questions (from cache or API)
            raw_questions = get_or_fetch_raw_unit_questions(course_code, course_name, unit, donem)

            # Process them
            nc, tc = process_question_list(raw_questions, course_name, unit, donem, seen_ids, all_questions, fetched_ids_in_run)

            print(f" Found {nc} new questions (Total fetched: {tc}).")

            # Save Unit JSON (cleaned)
            # Only if we have questions for this unit? Or always?
            # The original code saved unit json inside the loop if questions were found.
            # But here we are accumulating all_questions.
            # We can filter all_questions for this unit to save the unit file.

            unit_qs = [q for q in all_questions if q.get('Unite') == unit]
            if unit_qs:
                # Sort by SoruID
                unit_qs.sort(key=lambda x: int(x.get("SoruID", 0)))

                safe_course_name = "".join([c for c in course_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                unit_filename = f"Anadolu - Dönem {donem} - {safe_course_name} - Unite {unit:02d}.json"
                unit_path = os.path.join(JSON_DIR, unit_filename)

                with open(unit_path, 'w', encoding='utf-8') as f:
                    json.dump(unit_qs, f, ensure_ascii=False, indent=4)

            # Break if no questions found for this unit (and it's likely end of units)
            # Original logic: if total_fetched == 0.
            if tc == 0:
                print(f"  No questions found for Unit {unit}. Assuming end of units for this course.")
                break

        # Summary and Save All
        newly_added = len(all_questions) - initial_count

        # Check for removed questions
        # (Logic remains same as original)

        print(f"  Summary for {course_name}:")
        print(f"    - Loaded Existing: {initial_count}")
        print(f"    - Newly Added: {newly_added}")
        print(f"    - Total Unique: {len(all_questions)}")

        # Sort all questions
        all_questions.sort(key=lambda x: (int(x.get("Somestre", 0)), int(x.get("Unite", 0)), int(x.get("SoruID", 0))))

        # Save All JSON
        with open(all_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=4)

        # Generate Markdown
        md_content = f"# {course_name} (Dönem {donem}) - Tüm Sorular\n\n"
        current_unit = None
        for q in all_questions:
            unit = q.get('Unite')
            # Ensure unit is treated consistently (as int if possible)
            try:
                unit_val = int(unit)
            except (ValueError, TypeError):
                unit_val = unit

            if unit_val != current_unit:
                md_content += f"## Unite {unit_val}\n"
                current_unit = unit_val
            md_content += questions_to_markdown([q])

        md_filename = f"Anadolu - Dönem {donem} - {course_name} - Sorular.md"
        md_path = os.path.join(MD_DIR, md_filename)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Saved {len(all_questions)} total questions for {course_name} to sorular-anadolu and sorular-anadolu/md.")

import html

from bs4 import BeautifulSoup, NavigableString, Tag

def clean_html(text):
    if not text:
        return ""

    # Decode entities first
    text = html.unescape(text)

    # Pre-process newlines to <br> to preserve them
    text = text.replace('\n', '<br>')

    soup = BeautifulSoup(text, 'html.parser')

    # 1. Handle o:p and other specific tags
    # Replace <o:p> with space (block-like)
    # Use strict regex to avoid matching 'strong', 'body', etc.
    for tag in soup.find_all(re.compile(r'^o(:p)?$', re.I)):
        # Replace with space + content
        tag.insert_before(" ")
        tag.unwrap()

    # 2. Unwrap noisy block tags with space
    # div, article, body, html, head
    for tag_name in ['div', 'article', 'body', 'html', 'head']:
        for tag in soup.find_all(tag_name):
            tag.insert_before(" ")
            tag.unwrap()

    # 3. Unwrap noisy inline tags (no space)
    # font
    for tag in soup.find_all('font'):
        tag.unwrap()

    # 4. Strip attributes from strict tags
    strict_tags = ['strong', 'b', 'i', 'em', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'ul', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'sup', 'sub']
    for tag_name in strict_tags:
        for tag in soup.find_all(tag_name):
            tag.attrs = {}

    # 5. Smart strip for ol, p, u, span
    allowed_attrs = {
        'ol': ['type', 'start', 'style'],
        'p': ['style'],
        'u': ['style'],
        'span': ['style']
    }
    for tag_name, allowed in allowed_attrs.items():
        for tag in soup.find_all(tag_name):
            attrs = dict(tag.attrs)
            tag.attrs = {}
            for key in allowed:
                if key in attrs:
                    tag[key] = attrs[key]

    # 6. Remove empty tags
    for tag in soup.find_all():
        # Check if tag is not img/br/a and has no text content
        if tag.name not in ['img', 'br', 'a'] and not tag.get_text(strip=True):
            # Check if it has no children tags (like <img>)
            if not tag.find(['img', 'br', 'a']):
                tag.decompose()

    # 7. Convert <p> tags to <br>
    # Append <br> to each <p> content and unwrap
    for p in soup.find_all('p'):
        p.append(soup.new_tag('br'))
        p.unwrap()

    # Get string
    cleaned_text = str(soup).strip()

    # 8. Remove trailing <br> tags
    # Regex to remove <br>, <br/>, <br /> at the end of string
    cleaned_text = re.sub(r'\s*<br\s*/?>\s*$', '', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text

def map_to_old_format(api_question, course_name, unit_or_type, donem):
    # Map API response to the structure expected by the existing system (Soru class)
    return {
        "SoruID": api_question.get("QuestionId"),
        "SoruMetni": clean_html(api_question.get("Text")),
        "A": clean_html(api_question.get("A")),
        "B": clean_html(api_question.get("B")),
        "C": clean_html(api_question.get("C")),
        "D": clean_html(api_question.get("D")),
        "E": clean_html(api_question.get("E")),
        "DogruCevap": api_question.get("CorrectAnswer"),
        "DersAd": course_name,
        "Unite": unit_or_type,
        "Somestre": donem,
        "DogruCevapSirasi": None,
        "OlusturmaTarihi": datetime.now().isoformat(),
        "GelYer": 0,
        "DersId": 0,
        "OBSDersId": 0,
        "CevapSira": None,
        "Aciklama": clean_html(api_question.get("AnswerExplanation"))
    }

class HTMLPreservingConverter(markdownify.MarkdownConverter):
    def convert_sup(self, el, text, parent_tags=None):
        return str(el)
    def convert_sub(self, el, text, parent_tags=None):
        return str(el)

def questions_to_markdown(questions):
    md = ""
    converter = HTMLPreservingConverter()

    for i, q in enumerate(questions, 1):
        # Use custom converter to preserve HTML content like sup/sub
        q_text_raw = converter.convert(q['SoruMetni']).strip()
        # Replace newlines with <br /> for questions, but ensure no double <br />
        q_text_formatted = q_text_raw.replace('\n', '<br />')
        # Collapse multiple <br /> and remove surrounding spaces
        q_text_formatted = re.sub(r'\s*(<br\s*/?>\s*)+', '<br />', q_text_formatted)

        md += f"1. {q_text_formatted}\n"

        options = ['A', 'B', 'C', 'D', 'E']
        for opt in options:
            is_correct = q['DogruCevap'] == opt
            prefix = "**Cevap " if is_correct else ""
            suffix = "**" if is_correct else ""

            # Construct the list item prefix: "    - A-) "
            list_item_prefix = f"    - {prefix}{opt}-) "

            opt_content = q.get(opt, "")
            if opt_content:
                opt_text_raw = converter.convert(opt_content).strip()
                # Replace newlines with space in options
                opt_text_formatted = opt_text_raw.replace('\n', ' ')
                # Aggressively remove any remaining <br> tags
                opt_text_formatted = re.sub(r'<br\s*/?>', ' ', opt_text_formatted)
            else:
                opt_text_formatted = ""

            md += f"{list_item_prefix}{opt_text_formatted}{suffix}\n"

        if q.get('Aciklama'):
            explanation = converter.convert(q['Aciklama']).strip()
            # Ensure every line of explanation is quoted and indented
            exp_lines = explanation.split('\n')
            md += f"\n    > **Açıklama:** {exp_lines[0].strip()}\n"
            if len(exp_lines) > 1:
                # Add subsequent lines with prefix
                for line in exp_lines[1:]:
                    clean_line = line.strip()
                    if clean_line:
                        md += f"    > {clean_line}\n"
            md += "\n" # Extra newline after blockquote

        md += "    ***\n"
    return md

def process_question_list(raw_questions, course_name, unit_val, donem, seen_ids, all_questions, fetched_ids_in_run):
    new_count = 0
    total_count = len(raw_questions)

    for q in raw_questions:
        q_id = q["QuestionId"]
        fetched_ids_in_run.add(q_id)
        if q_id not in seen_ids:
            # Use unit_val for the JSON field "Unite"
            mapped_q = map_to_old_format(q, course_name, unit_val, donem)
            all_questions.append(mapped_q)
            seen_ids.add(q_id)
            new_count += 1

    return new_count, total_count

def main():
    setup_directories()

    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses to process.")

    for course in courses:
        course_code = course['DersKodu']
        course_name = course['CourseName']
        donem = course['Donem']

        if not course_code:
            continue

        print(f"Processing {course_code} - {course_name} (Dönem {donem})...")

        all_questions = []
        seen_ids = set()
        fetched_ids_in_run = set()

        # Load existing questions if available
        all_filename = f"Anadolu - Dönem {donem} - {course_name} - Tüm Sorular.json"
        all_path = os.path.join(FULL_JSON_DIR, all_filename)

        if os.path.exists(all_path):
            try:
                with open(all_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        all_questions = existing_data
                        for q in all_questions:
                            if "SoruID" in q:
                                seen_ids.add(q["SoruID"])
                        print(f"  Loaded {len(all_questions)} existing questions.")
            except Exception as e:
                print(f"  Error loading existing questions: {e}")

        initial_count = len(all_questions)

        # 1. Fetch Unit Questions
        for unit in range(1, 15): # Units 1 to 14
            print(f"  Fetching Unit {unit}...", end="", flush=True)

            # Get raw questions (from cache or API)
            raw_questions = get_or_fetch_raw_unit_questions(course_code, course_name, unit, donem)

            # Process them
            nc, tc = process_question_list(raw_questions, course_name, unit, donem, seen_ids, all_questions, fetched_ids_in_run)

            print(f" Found {nc} new questions (Total fetched: {tc}).")

            # Save Unit JSON (cleaned)
            unit_qs = [q for q in all_questions if q.get('Unite') == unit]
            if unit_qs:
                # Sort by SoruID
                unit_qs.sort(key=lambda x: int(x.get("SoruID", 0)))

                safe_course_name = "".join([c for c in course_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                unit_filename = f"Anadolu - Dönem {donem} - {safe_course_name} - Unite {unit:02d}.json"
                unit_path = os.path.join(JSON_DIR, unit_filename)

                with open(unit_path, 'w', encoding='utf-8') as f:
                    json.dump(unit_qs, f, ensure_ascii=False, indent=4)

            # Break if no questions found for this unit (and it's likely end of units)
            if tc == 0:
                print(f"  No questions found for Unit {unit}. Assuming end of units for this course.")
                break

        # Summary and Save All
        newly_added = len(all_questions) - initial_count

        # Check for removed questions
        existing_not_seen = 0
        for q in all_questions:
            if q['SoruID'] in seen_ids and q['SoruID'] not in fetched_ids_in_run:
                # Only count if it was in the initial set (which we didn't explicitly track separately,
                # but seen_ids started with initial).
                # However, seen_ids grows.
                # Simplification: just report what we didn't see this run.
                existing_not_seen += 1

        # Actually, let's just use the simple count
        existing_not_seen = 0
        for q in all_questions:
             if q['SoruID'] not in fetched_ids_in_run:
                 existing_not_seen += 1

        print(f"  Summary for {course_name}:")
        print(f"    - Loaded Existing: {initial_count}")
        print(f"    - Newly Added: {newly_added}")
        print(f"    - Total Unique: {len(all_questions)}")
        print(f"    - Existing questions NOT seen in this run: {existing_not_seen}")

        # Sort all questions
        all_questions.sort(key=lambda x: (int(x.get("Somestre", 0)), int(x.get("Unite", 0)), int(x.get("SoruID", 0))))

        # Save All JSON
        with open(all_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=4)

        # Generate Markdown
        md_content = f"# {course_name} (Dönem {donem}) - Tüm Sorular\n\n"
        md_content += questions_to_markdown(all_questions)

        md_filename = f"Anadolu - Dönem {donem} - {course_name} - Sorular.md"
        md_path = os.path.join(MD_DIR, md_filename)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"Saved {len(all_questions)} total questions for {course_name} to sorular-anadolu and sorular-anadolu/md.")

if __name__ == "__main__":
    main()
