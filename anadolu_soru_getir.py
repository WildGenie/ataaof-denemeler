import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
import markdownify
import re

# Configuration
DERSLER_FILE = "anadolu_dersler.json"
OUTPUT_DIR = "output"
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
MD_DIR = os.path.join("sorular-anadolu", "md") # Updated to subfolder in sorular-anadolu
FULL_JSON_DIR = "sorular-anadolu"

# Headers from the curl command
HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://ekampus.anadolu.edu.tr',
    'accept': '*/*',
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYXCOeM',
}

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
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

import html

def clean_html(text):
    if not text:
        return text
    text = text.strip()
    # Check if it looks like a single paragraph wrapper
    # We check if it starts with <p, ends with </p>, and has exactly one </p> (at the end).
    # This avoids breaking <p>A</p><p>B</p> or removing tags from non-wrapped content.
    if text.lower().startswith('<p') and text.lower().endswith('</p>'):
        # Count closing tags to ensure we don't have siblings like <p>A</p><p>B</p>
        if text.lower().count('</p>') == 1:
            # Remove start tag (handling attributes)
            text = re.sub(r'^<p[^>]*>', '', text, flags=re.IGNORECASE)
            # Remove end tag
            text = re.sub(r'</p>$', '', text, flags=re.IGNORECASE)
    return text

def map_to_old_format(api_question, course_name, unit_or_type, donem):
    # Map API response to the structure expected by the existing system (Soru class)
    return {
        "SoruID": api_question.get("QuestionId"),
        "SoruMetni": clean_html(api_question.get("Text")),
        "A": clean_html(api_question.get("A")),
        "B": clean_html(api_question.get("B"),),
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

def questions_to_markdown(questions):
    md = ""
    for i, q in enumerate(questions, 1):
        # Use markdownify to convert HTML content
        q_text_raw = markdownify.markdownify(q['SoruMetni']).strip()
        # Replace newlines with <br> as requested by the user to prevent formatting issues
        q_text_formatted = q_text_raw.replace('\n', '<br>')

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
                opt_text_raw = markdownify.markdownify(opt_content).strip()
                # Replace newlines with <br> in options as well
                opt_text_formatted = opt_text_raw.replace('\n', '<br>')
            else:
                opt_text_formatted = ""

            md += f"{list_item_prefix}{opt_text_formatted}{suffix}\n"

        if q.get('Aciklama'):
            explanation = markdownify.markdownify(q['Aciklama']).strip()
            # Ensure every line of explanation is quoted and indented
            exp_lines = explanation.split('\n')
            md += f"\n    > **Açıklama:** {exp_lines[0]}\n"
            if len(exp_lines) > 1:
                # Add subsequent lines with prefix
                for line in exp_lines[1:]:
                    md += f"    > {line}\n"
            md += "\n" # Extra newline after blockquote

        md += "    ***\n"
    return md

def process_questions(data, course_name, unit_val, donem, seen_ids, all_questions, fetched_ids_in_run):
    if data and "Questions" in data and data["Questions"] is not None:
        new_count = 0
        total_count = len(data["Questions"])
        for q in data["Questions"]:
            q_id = q["QuestionId"]
            fetched_ids_in_run.add(q_id)
            if q_id not in seen_ids:
                # Use unit_val for the JSON field "Unite"
                mapped_q = map_to_old_format(q, course_name, unit_val, donem)
                all_questions.append(mapped_q)
                seen_ids.add(q_id)
                new_count += 1

        return new_count, total_count
    return 0, 0

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

            count = 0
            total_fetched = 0
            for _ in range(7): # Retry/Accumulate logic
                data = fetch_unit_questions(course_code, unit)
                nc, tc = process_questions(data, course_name, unit, donem, seen_ids, all_questions, fetched_ids_in_run)
                count += nc
                total_fetched += tc
                time.sleep(0.1)
            print(f" Found {count} new questions (Total fetched: {total_fetched}).")

            if total_fetched == 0:
                print(f"  No questions found for Unit {unit}. Assuming end of units for this course.")
                break

            # Save Unit JSON if questions found (filtering from all_questions for this unit)
            unit_qs = [q for q in all_questions if q['Unite'] == unit]
            if unit_qs:
                 # Sort unit questions by SoruID
                 try:
                     unit_qs.sort(key=lambda x: int(x['SoruID']) if str(x['SoruID']).isdigit() else x['SoruID'])
                 except:
                     unit_qs.sort(key=lambda x: x['SoruID'])

                 unit_filename = f"Anadolu - Dönem {donem} - {course_name} - Unite {unit:02d}.json"
                 with open(os.path.join(JSON_DIR, unit_filename), 'w', encoding='utf-8') as f:
                     json.dump(unit_qs, f, indent=4, ensure_ascii=False)



        # Report stats
        total_now = len(all_questions)
        newly_added = total_now - initial_count
        # Calculate how many existing questions were NOT seen in this run
        # We need to check which of the 'initial' seen_ids were not in 'fetched_ids_in_run'
        # Note: seen_ids grows during the run, so we should have captured initial_seen_ids if we wanted exact set diff.
        # But we can approximate or just report what we have.
        # Let's just report the totals.

        print(f"  Summary for {course_name}:")
        print(f"    - Loaded Existing: {initial_count}")
        print(f"    - Newly Added: {newly_added}")
        print(f"    - Total Unique: {total_now}")

        # Identify questions that were in existing but not fetched this time (optional but requested)
        # We can't easily do this with just sets because seen_ids is mixed.
        # But we can iterate over all_questions and check if SoruID is in fetched_ids_in_run
        not_seen_count = 0
        for q in all_questions:
            if q.get("SoruID") not in fetched_ids_in_run:
                not_seen_count += 1
        print(f"    - Existing questions NOT seen in this run: {not_seen_count}")


        if all_questions:
            # Sort questions by Donem then SoruID
            # Sort questions by Donem then Unite then SoruID
            try:
                all_questions.sort(key=lambda x: (
                    x['Somestre'],
                    int(x.get('Unite', 0)) if str(x.get('Unite', '0')).isdigit() else x.get('Unite', 0),
                    int(x['SoruID']) if str(x['SoruID']).isdigit() else x['SoruID']
                ))
            except:
                all_questions.sort(key=lambda x: (x['Somestre'], x.get('Unite', 0), x['SoruID']))

            # Save All Questions JSON
            # all_path is already defined
            with open(all_path, 'w', encoding='utf-8') as f:
                json.dump(all_questions, f, indent=4, ensure_ascii=False)

            # Generate Markdown from sorted questions
            course_md = [f"# {course_name}\n\n"] # Reset MD content
            current_unit = None
            for q in all_questions:
                if q['Unite'] != current_unit:
                    course_md[0] += f"## Unite {q['Unite']}\n"
                    current_unit = q['Unite']
                course_md[0] += questions_to_markdown([q])

            # Save Markdown
            md_filename = f"Anadolu - Dönem {donem} - {course_name} - Sorular.md"
            md_path = os.path.join(MD_DIR, md_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(course_md[0])

            print(f"Saved {len(all_questions)} total questions for {course_name} to {FULL_JSON_DIR} and {MD_DIR}.")
        else:
            print(f"No questions found for {course_name}.")

if __name__ == "__main__":
    main()
