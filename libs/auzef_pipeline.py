import os
import json
import requests
import time
import re
from tqdm import tqdm
from libs.pipeline import QuestionPipeline
from libs.shared import clean_html, questions_to_markdown
from libs.auzef_lib import (
    BASE_API_URL,
    get_auzef_headers,
    map_to_standard_format,
    RAW_DIR,
    JSON_DIR,
    OUTPUT_DIR
)
import shutil

def turkish_title(text):
    if not text: return ""
    words = text.split()
    result = []
    for i, word in enumerate(words):
        if not word: continue

        # Special case for 've', 'ile' etc if not first word
        if i > 0 and word.lower() in ['ve', 'ile', 'veya']:
            result.append(word.lower())
            continue

        # Handle first letter
        first = word[0]
        if first == 'i': first = 'İ'
        elif first == 'ı': first = 'I'
        else: first = first.upper()

        # Handle rest
        rest = word[1:]
        fixed_rest = ""
        for char in rest:
            if char == 'İ': fixed_rest += 'i'
            elif char == 'I': fixed_rest += 'ı'
            else: fixed_rest += char.lower()
        result.append(first + fixed_rest)
    return " ".join(result)

class AuzefPipeline(QuestionPipeline):
    def __init__(self, raw_dir=RAW_DIR, json_dir=JSON_DIR, full_json_dir=None, md_dir=None, no_cache=False):
        super().__init__(raw_dir, json_dir, full_json_dir, md_dir, no_cache)
        self.session = requests.Session()

    def fetch_raw_questions(self, course, unit=0, silent=False):
        exam_id = course.get("exam_id")
        token = course.get("token")
        if not exam_id:
            return None

        headers = get_auzef_headers(exam_id, token)
        data = f"ders={exam_id}&sinav_turu=final"

        try:
            response = self.session.post(BASE_API_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "Questions" in result:
                time.sleep(0.5) # Added sleep here as per instruction
                return result["Questions"]
            return []
        except Exception as e:
            if not silent:
                tqdm.write(f"      Error fetching {course.get('CourseName')}: {e}")
            return None

    def transform_question(self, raw_question, course, unit):
        course_name = course.get("CourseName", "")
        unit_id = raw_question.get("unite_id", unit)
        std = map_to_standard_format(raw_question, course_name, unit_id)
        if "Konu" not in std:
            std["Konu"] = raw_question.get("Konu", "")
        return std

    def get_filename_prefix(self, course):
        return "Auzef"

    def get_content_key(self, q):
        # Normalize content to detect duplicates with different IDs
        import html
        def normalize(text):
            if not text: return ""
            # Strip tags and normalize spaces for comparison
            text = html.unescape(text)
            text = re.sub(r'<[^>]*>', '', text)
            return " ".join(text.lower().split())

        parts = []
        parts.append(normalize(q.get("Text") or q.get("SoruMetni") or ""))
        for opt in ['A', 'B', 'C', 'D', 'E']:
            parts.append(normalize(q.get(opt, "")))
        # Include correct answer
        parts.append(str(q.get("CorrectAnswer") or q.get("DogruCevap") or "").strip().upper())
        return "|".join(parts)

    def process_course(self, course, target_unit=None, tqdm_position=None):
        course_name = course.get("CourseName")
        raw_course_name = course_name # for compatibility with old code block below if needed
        donem = course.get("Donem", 0)

        # No longer filtering out Donem 1

        exam_id = course.get("exam_id")

        # Paths
        filename_base = f"Auzef - Dönem {donem} - {course_name} - Alıştırma Soruları"
        json_target_dir = os.path.join(self.json_dir, f"Donem {donem}")
        if not os.path.exists(json_target_dir):
            os.makedirs(json_target_dir)

        # Move/Rename directory if it exists with DIFFERENT CASE
        course_md_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name)
        parent_dir = os.path.dirname(course_md_dir)
        if os.path.exists(parent_dir):
            for existing in os.listdir(parent_dir):
                if existing.lower() == course_name.lower() and existing != course_name:
                    old_path = os.path.join(parent_dir, existing)
                    try:
                        # If the new path doesn't exist, we can rename.
                        # If it does, we should probably merge or delete old.
                        if not os.path.exists(course_md_dir):
                            os.rename(old_path, course_md_dir)
                        else:
                            shutil.rmtree(old_path)
                    except:
                        pass

        filepath_processed = os.path.join(json_target_dir, f"{filename_base}.json")
        filepath_raw = os.path.join(json_target_dir, f"{filename_base} - Raw.json")

        # Load existing raw questions
        raw_questions_map = {}
        content_map = {}

        if os.path.exists(filepath_raw):
            try:
                with open(filepath_raw, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for q in data:
                        q_id = q["QuestionId"]
                        ckey = self.get_content_key(q)
                        if ckey not in content_map:
                            raw_questions_map[q_id] = q
                            content_map[ckey] = q_id
            except:
                pass

        initial_count = len(raw_questions_map)
        new_count = 0

        # Load Çıkmış (Past) questions if they exist
        cikmis_questions = []
        filepath_cikmis = os.path.join(json_target_dir, f"Auzef - Dönem {donem} - {course_name} - Sorular.json")
        if os.path.exists(filepath_cikmis):
            try:
                with open(filepath_cikmis, 'r', encoding='utf-8') as f:
                    cikmis_questions = json.load(f)
            except:
                pass

        # Iteration logic: AUZEF might return random questions, so we try multiple times
        # We use a patience counter: if we see no new questions for 30 attempts, we stop.
        attempts = 300 if exam_id else 0
        patience = 30
        no_new_strikes = 0

        for i in range(attempts):
            batch = self.fetch_raw_questions(course, silent=(tqdm_position is not None))
            if not batch: break

            batch_new = 0
            for q in batch:
                q_id = q["QuestionId"]
                content_key = self.get_content_key(q)

                # Check both ID and Content
                if q_id not in raw_questions_map and content_key not in content_map:
                    raw_questions_map[q_id] = q
                    content_map[content_key] = q_id
                    batch_new += 1
                    new_count += 1

            if batch_new == 0:
                no_new_strikes += 1
            else:
                no_new_strikes = 0 # Reset patience if we find something new

            if no_new_strikes >= patience and i > 2: # Give it at least 3 tries
                break

            time.sleep(0.5)

        if len(raw_questions_map) > 0 or len(cikmis_questions) > 0:
            # Save raw if we fetched anything
            if new_count > 0 or (self.no_cache and initial_count == 0 and len(raw_questions_map) > 0):
                final_raw = list(raw_questions_map.values())
                # Sort by unit and ID
                final_raw.sort(key=lambda x: (int(str(x.get("unite_id", 0)) or 0), x.get("QuestionId", "")))
                with open(filepath_raw, 'w', encoding='utf-8') as f:
                    json.dump(final_raw, f, indent=4, ensure_ascii=False)

            # Transform Alıştırma (Practice) questions
            alistirma_questions = []
            for q in raw_questions_map.values():
                u_id = q.get("unite_id", 0)
                try:
                    u_id = int(str(u_id))
                except:
                    u_id = 0
                alistirma_questions.append(self.transform_question(q, course, u_id))

            # Sort by unit and ID
            alistirma_questions.sort(key=lambda x: (int(str(x.get("Unite", 0)) or 0), x.get("SoruID", "")))

            # cikmis_questions is already loaded above
            # Ensure it's also sorted and units are ints
            if cikmis_questions:
                 for q in cikmis_questions:
                     try: q["Unite"] = int(str(q.get("Unite", 0)))
                     except: q["Unite"] = 0
                 cikmis_questions.sort(key=lambda x: (int(str(x.get("Unite", 0)) or 0), x.get("SoruID", "")))

            # Save processed Alıştırma
            if alistirma_questions:
                with open(filepath_processed, 'w', encoding='utf-8') as f:
                    json.dump(alistirma_questions, f, indent=4, ensure_ascii=False)

            # Generate Markdown
            if not os.path.exists(course_md_dir):
                os.makedirs(course_md_dir)

            def generate_separate_md(questions, title, filename):
                if not questions: return False

                # Sort questions by Unit then Konu then Text
                def sort_key(q):
                    u = q.get("Unite", 0)
                    k = str(q.get("Konu", ""))
                    try:
                        unit_score = 999
                        if str(u).startswith("Ünite "): unit_score = int(str(u).replace("Ünite ", ""))
                        elif str(u).isdigit(): unit_score = int(u)
                        return (unit_score, k, q.get("SoruMetni", ""))
                    except:
                        return (999, k, q.get("SoruMetni", ""))

                sorted_qs = sorted(questions, key=sort_key)

                # Group by Unit
                qs_by_unit = {}
                for q in sorted_qs:
                    u = q.get("Unite", 0)
                    if u not in qs_by_unit: qs_by_unit[u] = []
                    qs_by_unit[u].append(q)

                # Sort unit keys naturally
                def u_key(u):
                    try:
                        if str(u).startswith("Ünite "): return int(str(u).replace("Ünite ", ""))
                        return int(u)
                    except:
                        return 999

                sorted_units = sorted(qs_by_unit.keys(), key=u_key)

                md_path = os.path.join(course_md_dir, filename)
                md_content = f"# {course_name} - {title}\n\n"

                for u in sorted_units:
                    unit_label = f"Ünite {u}" if (isinstance(u, int) and u > 0) or str(u).isdigit() else "Karma / Final Soruları"
                    if str(u).startswith("Ünite "): unit_label = u

                    md_content += f"## {unit_label}\n\n"

                    # Group by Topic within Unit
                    unit_qs = qs_by_unit[u]
                    qs_by_topic = {}
                    for q in unit_qs:
                        k = q.get("Konu", "") or ""
                        if k not in qs_by_topic: qs_by_topic[k] = []
                        qs_by_topic[k].append(q)

                    # Sort topics alphabetically
                    sorted_topics = sorted(qs_by_topic.keys())

                    for topic in sorted_topics:
                        if topic:
                            md_content += f"### {topic}\n\n"
                        md_content += questions_to_markdown(qs_by_topic[topic])
                        md_content += "\n"

                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                return True

            # Çıkmış Sorular -> Sorular.md
            has_cikmis = generate_separate_md(cikmis_questions, "Çıkmış Sorular", "Sorular.md")
            # Alıştırma Soruları -> Alıştırma Soruları.md
            has_alistirma = generate_separate_md(alistirma_questions, "Alıştırma Soruları", "Alıştırma Soruları.md")

            # Update index.md
            index_path = os.path.join(course_md_dir, "index.md")
            index_content = f"# {course_name}\n\n## Ders Materyalleri\n\n"
            if has_cikmis:
                index_content += f"### [📝 Çıkmış Sorular](Sorular.md)\n\n"
            if has_alistirma:
                index_content += f"### [📝 Alıştırma Soruları](Al%C4%B1%C5%9Ft%C4%B1rma%20Sorular%C4%B1.md)\n\n"

            index_content += "[🔙 Ana Sayfaya Dön](../../)\n"

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)


            if tqdm_position is None:
                print(f"      Total: {len(alistirma_questions)} alıştırma, {len(cikmis_questions)} çıkmış questions for {course_name}")
            return True
        return False
