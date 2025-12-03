import json
import os
import time
import requests
import urllib.parse
from datetime import datetime
from tqdm import tqdm
from libs.pipeline import QuestionPipeline
from libs.shared import clean_html
from libs.anadolu_lib import (
    map_to_old_format,
    OUTPUT_DIR,
    JSON_DIR,
    PDF_DIR,
    URL_CREATE_EXAM,
    URL_GET_PDF,
    URL_GET_CHAPTERS,
    URL_GET_LEARN_QUESTIONS,
    URL_GET_LEARN_PDF,
    URL_GET_MATERIAL_BY_ID,
    DEFAULT_UNIT_COUNT,
    DEFAULT_FETCH_ATTEMPTS,
    DEFAULT_LEARN_ATTEMPTS,
    DEFAULT_EMPTY_UNIT_THRESHOLD,
    DEFAULT_EMPTY_UNIT_THRESHOLD,
    DOWNLOAD_TRACKER_FILE,
    clean_filename
)

HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://lmsstuff.anadolu.edu.tr',
    'Referer': 'https://lmsstuff.anadolu.edu.tr/',
    'accept': '*/*',
    'authorization': os.getenv('ANADOLU_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYyCOeM'),
}

class AnadoluPipeline(QuestionPipeline):
    def __init__(self, raw_dir, json_dir, full_json_dir, md_dir, no_cache=False,
                 fetch_attempts=DEFAULT_FETCH_ATTEMPTS,
                 learn_attempts=DEFAULT_LEARN_ATTEMPTS,
                 unit_count=DEFAULT_UNIT_COUNT,
                 local_only=False):
        super().__init__(raw_dir, json_dir, full_json_dir, md_dir, no_cache)
        self.fetch_attempts = fetch_attempts
        self.learn_attempts = learn_attempts
        self.unit_count = unit_count
        self.local_only = local_only

    def fetch_raw_questions(self, course, unit, silent=False):
        course_code = course.get('DersKodu')
        if not course_code:
            return None

        url = f"{URL_CREATE_EXAM}/{urllib.parse.quote(course_code)}/{unit}"

        raw_questions_map = {}
        error_count = 0

        # Retry/Accumulate logic
        # Anadolu API returns random questions. We try 20 times to get as many unique questions as possible.
        # However, if the API explicitly returns an empty list or indicates "no questions" in a valid response,
        # we should probably stop early to avoid wasting time.
        # But Anadolu API might just return a random set, so empty list MIGHT mean no questions for this unit.

        for i in range(self.fetch_attempts):
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "Questions" in data and data["Questions"]:
                        for q in data["Questions"]:
                            q.pop("QuestionNumber", None) # Remove volatile field
                            raw_questions_map[q["QuestionId"]] = q
                    else:
                        # If we get a valid response but no questions, it's likely this unit has no questions.
                        # To be safe, we can count consecutive empty responses.
                        # If we get 3 empty responses in a row, we assume the unit is empty.
                        error_count += 1
                        if error_count >= DEFAULT_EMPTY_UNIT_THRESHOLD and not raw_questions_map:
                             if not silent:
                                 tqdm.write(f"      Unit {unit} seems empty (3 empty responses). Stopping.")
                             break
                else:
                    error_count += 1
            except Exception as e:
                # tqdm.write(f"Error: {e}")
                error_count += 1

            time.sleep(0.1)

        return list(raw_questions_map.values())

    def transform_question(self, raw_question, course, unit, existing_dates_map=None):
        # Use map_to_old_format
        course_name = course.get("CourseName")
        donem = course.get("Donem")

        q_id = raw_question.get("QuestionId")
        existing_date = existing_dates_map.get(q_id) if existing_dates_map and q_id else None

        return map_to_old_format(raw_question, course_name, unit, donem, existing_date)

    def get_filename_prefix(self, course):
        return "Anadolu"

    def fetch_pdf(self, course, unit, silent=False):
        course_code = course.get('DersKodu')
        if not course_code:
            return

        # 1. Call Create API to get RandPart
        url = f"{URL_CREATE_EXAM}/{urllib.parse.quote(course_code)}/{unit}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rand_part = data.get("RandPart")
                if not rand_part:
                    if not silent:
                        tqdm.write(f"      Unit {unit}: Could not get RandPart for PDF.")
                    return

                # 2. Construct PDF URLs
                # Exam PDF: create-10-{course_code}-{unit}/{RandPart}
                # Solution PDF: ...?withsolution=1

                base_pdf_url = f"{URL_GET_PDF}/create-10-{course_code}-{unit}/{rand_part}"

                self.download_pdf(base_pdf_url, course, unit, "Soru", silent=silent)
                self.download_pdf(base_pdf_url + "?withsolution=1", course, unit, "Cevap", silent=silent)

            else:
                if not silent:
                    tqdm.write(f"      Unit {unit}: API Error {response.status_code} while fetching RandPart.")
        except Exception as e:
            if not silent:
                tqdm.write(f"      Unit {unit}: Error fetching PDF info: {e}")

    def download_pdf(self, url, course, unit, suffix, silent=False):

        course_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        filename = f"Anadolu - Dönem {donem} - {course_name} - Unite {unit:02d} - {suffix}.pdf"
        filepath = os.path.join(PDF_DIR, filename)

        if os.path.exists(filepath):
            # tqdm.write(f"      PDF already exists: {filename}")
            return

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                if not silent:
                    tqdm.write(f"      Downloaded PDF: {filename}")
            else:
                if not silent:
                    tqdm.write(f"      Failed to download PDF {suffix}: {response.status_code}")
        except Exception as e:
            if not silent:
                tqdm.write(f"      Error downloading PDF {suffix}: {e}")
    def process_course(self, course, target_unit=None, tqdm_position=None):
        course_name = self.get_safe_course_name(course)
        donem = course.get("Donem")

        # Setup directories
        # JSONs -> json/Donem X/
        # MDs -> Anadolu/Donem X/Course Name/

        course_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name)
        if not os.path.exists(course_dir):
            os.makedirs(course_dir)

        # JSON Target Directory
        json_target_dir = os.path.join(JSON_DIR, f"Donem {donem}")
        if not os.path.exists(json_target_dir):
            os.makedirs(json_target_dir)

        # File paths
        filename_processed = f"Anadolu - Dönem {donem} - {course_name} - Alıştırma Soruları.json"
        filepath_processed = os.path.join(json_target_dir, filename_processed)

        filename_raw = f"Anadolu - Dönem {donem} - {course_name} - Alıştırma Soruları - Raw.json"
        filepath_raw = os.path.join(json_target_dir, filename_raw)

        filename_md = "Alıştırma Soruları.md"
        filepath_md = os.path.join(course_dir, filename_md)

        # Load existing raw questions if any
        all_raw_questions = []
        if os.path.exists(filepath_raw):
            try:
                with open(filepath_raw, 'r', encoding='utf-8') as f:
                    all_raw_questions = json.load(f)
            except:
                pass

        # Load existing processed questions to preserve OlusturmaTarihi
        existing_dates_map = {}
        if os.path.exists(filepath_processed):
            try:
                with open(filepath_processed, 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
                    if isinstance(processed_data, list):
                        for q in processed_data:
                            q_id = q.get("SoruID")
                            date = q.get("OlusturmaTarihi")
                            if q_id and date:
                                existing_dates_map[q_id] = date
            except:
                pass

        # Map existing raw questions by ID to avoid duplicates
        # Note: The merged 'Raw' file might actually contain processed questions (SoruID) if it was created from old 'Unite X.json' files.
        # We need to handle both cases.
        raw_questions_map = {}
        for q in all_raw_questions:
            q_id = q.get("QuestionId") or q.get("SoruID")
            if q_id:
                raw_questions_map[q_id] = q

        initial_count = len(raw_questions_map)

        units_to_process = [target_unit] if target_unit else range(1, self.unit_count + 1)

        # Progress bar setup
        if tqdm_position is not None:
            iterator = tqdm(units_to_process, desc=f"Processing {course_name}", position=tqdm_position, leave=False)
        else:
            iterator = units_to_process

        if not self.local_only:
            for unit in iterator:
                # Fetch raw questions
                new_raw_questions = self.fetch_raw_questions(course, unit, silent=(tqdm_position is not None))

                if new_raw_questions:
                    for q in new_raw_questions:
                        raw_questions_map[q["QuestionId"]] = q

        # Save merged raw questions
        final_raw_questions = list(raw_questions_map.values())

        # Redact PII
        cleaned_raw_data = self.redact_pii(final_raw_questions)

        with open(filepath_raw, 'w', encoding='utf-8') as f:
            json.dump(cleaned_raw_data, f, indent=4, ensure_ascii=False)

        # Transform and Save Processed Questions
        processed_questions = []
        for q in final_raw_questions:
             if "SoruID" in q:
                 # Already processed
                 processed_questions.append(q)
             else:
                 # Raw question, needs transformation
                 unit = q.get("UniteNo", 0)
                 # Fallback to target_unit if UniteNo is missing or 0, though it should be there from API
                 # But wait, if we fetched it, we know the unit from the loop, but here we are iterating all questions.
                 # If UniteNo is missing in raw data, we might have an issue.
                 # However, usually API returns it.
                 processed_questions.append(self.transform_question(q, course, unit, existing_dates_map))

        # Sort by Unit then Index (if available) or Question text
        # Processed questions have "Unite", Raw/Transformed have "Unite"
        processed_questions.sort(key=lambda x: (int(x.get("Unite") or 0), x.get("SoruMetni", "")))

        with open(filepath_processed, 'w', encoding='utf-8') as f:
            json.dump(processed_questions, f, indent=4, ensure_ascii=False)

        # Generate Markdown
        from libs.shared import questions_to_markdown
        md_content = f"# {course_name} - Alıştırma Soruları\n\n"
        md_content += questions_to_markdown(processed_questions)

        with open(filepath_md, 'w', encoding='utf-8') as f:
            f.write(md_content)

        new_count = len(raw_questions_map) - initial_count
        if (new_count > 0 or self.local_only) and tqdm_position is None:
             tqdm.write(f"      Saved {len(processed_questions)} questions ({new_count} new) for {course_name}")
    def fetch_chapters(self, course_code, silent=False):
        """Fetch chapter information for a given course code using the Anadolu API.
        Endpoint: https://ets-ws.anadolu.edu.tr/v2filikaapi/courseservice/getchapters/{course_code}?type=2
        Returns the parsed JSON response or None on failure.
        """
        url = f"{URL_GET_CHAPTERS}/{urllib.parse.quote(course_code)}?type=2"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not silent:
                    count = 0
                    if isinstance(data, list):
                        for item in data:
                            count += len(item.get('Materials', []))
                    tqdm.write(f"      Fetched chapters/materials for {course_code}: {count} items")
                return data
            else:
                if not silent:
                    tqdm.write(f"      Error fetching chapters for {course_code}: {response.status_code}")
                return None
            return None
        except Exception as e:
            if not silent:
                tqdm.write(f"      Exception fetching chapters for {course_code}: {e}")
            return None

    def fetch_and_save_materials(self, course, silent=False):
        course_code = course.get('DersKodu')
        if not course_code:
            return

        data = self.fetch_chapters(course_code, silent=silent)
        if data:
            course_name = self.get_safe_course_name(course)
            donem = course.get("Donem")
            filename = f"Anadolu - Dönem {donem} - {course_name} - Materials.json"

            # Materials list goes to JSON_DIR/Donem X/
            target_dir = os.path.join(JSON_DIR, f"Donem {donem}")
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            filepath = os.path.join(target_dir, filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                if not silent:
                    tqdm.write(f"      Saved materials list: {filename}")
            except Exception as e:
                if not silent:
                    tqdm.write(f"      Error saving materials list for {course_name}: {e}")

    def load_tracker(self):
        if os.path.exists(DOWNLOAD_TRACKER_FILE):
            try:
                with open(DOWNLOAD_TRACKER_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_tracker(self, tracker):
        try:
            with open(DOWNLOAD_TRACKER_FILE, 'w', encoding='utf-8') as f:
                json.dump(tracker, f, indent=4, ensure_ascii=False)
        except Exception as e:
            tqdm.write(f"Error saving tracker: {e}")

    def download_past_exams(self, course, silent=False):
        course_name = self.get_safe_course_name(course)
        donem = course.get("Donem")

        # Load materials file
        materials_filename = f"Anadolu - Dönem {donem} - {course_name} - Materials.json"
        # Materials list is in JSON_DIR/Donem X/
        materials_filepath = os.path.join(JSON_DIR, f"Donem {donem}", materials_filename)

        if not os.path.exists(materials_filepath):
            if not silent:
                tqdm.write(f"      Materials file not found for {course_name}. Run --materials first.")
            return

        try:
            with open(materials_filepath, 'r', encoding='utf-8') as f:
                materials_data = json.load(f)
        except Exception as e:
            if not silent:
                tqdm.write(f"      Error reading materials file for {course_name}: {e}")
            return

        tracker = self.load_tracker()

        # Create course directory in Materyaller
        # New structure: Anadolu/Donem X/Course Name/Materyaller/
        course_exam_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name, "Materyaller")
        if not os.path.exists(course_exam_dir):
            os.makedirs(course_exam_dir)

        download_count = 0

        for group in materials_data:
            if not group.get("Type", "").startswith("PAST_EXAMS"):
                continue

            for material in group.get("Materials", []):
                material_id = str(material.get("MaterialId"))
                updated_at = material.get("UpdatedAt")
                name = material.get("Name", "Unknown").replace("/", "-").replace(":", "-")
                description = material.get("Description", "").replace("/", "-").replace(":", "-")

                if description and description != name:
                    base = f"{name} - {description}"
                else:
                    base = name

                if material_id not in base:
                    base = f"{base} - {material_id}"

                filename_base = clean_filename(base)

                # Check tracker
                if material_id in tracker:
                    tracker_entry = tracker[material_id]
                    if tracker_entry.get("UpdatedAt") == updated_at:
                        # Check if file actually exists
                        existing_filename = tracker_entry.get("Filename")
                        if existing_filename:
                            existing_filepath = os.path.join(course_exam_dir, existing_filename)
                            if os.path.exists(existing_filepath):
                                # Already downloaded and up to date, and file exists
                                continue

                # Download
                token = HEADERS.get('authorization', '')
                download_url = f"{URL_GET_MATERIAL_BY_ID}/{material_id}?Authorization={token}"
                file_ext = ".pdf" # Default to pdf as these are exams
                if material.get("FileExtension") == "application/pdf":
                    file_ext = ".pdf"

                filename = f"{filename_base}{file_ext}"
                filepath = os.path.join(course_exam_dir, filename)

                try:
                    if not silent:
                        tqdm.write(f"      Downloading {filename}...")

                    response = requests.get(download_url, headers=HEADERS, timeout=60)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)

                        # Update tracker
                        tracker[material_id] = {
                            "UpdatedAt": updated_at,
                            "DownloadedAt": datetime.now().isoformat(),
                            "Filename": filename,
                            "Course": course_name
                        }
                        download_count += 1
                    else:
                        if not silent:
                            tqdm.write(f"      Failed to download {filename}: {response.status_code}")
                            tqdm.write(f"      Response: {response.text[:200]}")
                except Exception as e:
                    if not silent:
                        tqdm.write(f"      Exception downloading {filename}: {e}")

        if download_count > 0:
            self.save_tracker(tracker)
            if not silent:
                tqdm.write(f"      Downloaded {download_count} new/updated exams for {course_name}")
        elif not silent:
             tqdm.write(f"      No new exams to download for {course_name}")
    def fetch_learn_questions(self, course_code, unit):
        """
        Fetches 'Sorularla Öğrenelim' questions for a specific unit.
        """
        url = f"{URL_GET_LEARN_QUESTIONS}/{urllib.parse.quote(course_code)}/{unit}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("QuestionAnswer", [])
            else:
                return []
        except Exception as e:
            tqdm.write(f"      Exception fetching learn questions for Unit {unit}: {e}")
            return []

    def download_learn_questions_pdf(self, course_code, unit, output_dir):
        """
        Downloads the PDF version of 'Sorularla Öğrenelim' for a specific unit.
        """
        url = f"{URL_GET_LEARN_PDF}/{urllib.parse.quote(course_code)}/{unit}"
        filename = f"Unit_{unit}_Sorularla_Ogrenelim.pdf"

        # output_dir is passed from process_learn_questions, which should now be the Materyaller folder
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            return # Skip if already exists

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200 and len(response.content) > 0:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            tqdm.write(f"      Exception downloading PDF for Unit {unit}: {e}")

    def process_learn_questions(self, course, silent=False, tqdm_position=None):
        course_code = course.get('DersKodu')
        if not course_code:
            return

        course_name = self.get_safe_course_name(course)
        donem = course.get("Donem")

        # Setup directory for PDFs (Materyaller)
        # New structure: Anadolu/Donem X/Course Name/Materyaller/

        course_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name)
        if not os.path.exists(course_dir):
            os.makedirs(course_dir)

        materials_dir = os.path.join(course_dir, "Materyaller")
        if not os.path.exists(materials_dir):
            os.makedirs(materials_dir)

        # JSON paths
        # JSONs -> json/Donem X/
        json_target_dir = os.path.join(JSON_DIR, f"Donem {donem}")
        if not os.path.exists(json_target_dir):
            os.makedirs(json_target_dir)

        filename_prefix = self.get_filename_prefix(course)
        # Filename: Anadolu - Dönem X - Course Name - Sorularla Ogrenelim.json
        filename_base = f"{filename_prefix} - Dönem {donem} - {course_name} - Sorularla Ogrenelim"
        filepath_processed = os.path.join(json_target_dir, f"{filename_base}.json")
        filepath_raw = os.path.join(json_target_dir, f"{filename_base} - Raw.json")
        filepath_md = os.path.join(course_dir, "Sorularla Ogrenelim.md")

        # Cleanup existing PDFs
        # ... (cleanup code)

        all_questions_map = {}

        # Load existing raw data
        # Load existing raw data
        if os.path.exists(filepath_raw):
            try:
                with open(filepath_raw, 'r', encoding='utf-8') as f:
                    existing_raw_data = json.load(f)
                    if isinstance(existing_raw_data, list):
                        for item in existing_raw_data:
                            # Check if it's the old format (list of iterations)
                            if "Data" in item and isinstance(item["Data"], dict) and "QuestionAnswer" in item["Data"]:
                                 questions = item["Data"]["QuestionAnswer"]
                                 for q in questions:
                                     key = q.get("Index")
                                     if key:
                                         all_questions_map[key] = q
                            else:
                                 # New format: Item is a question object
                                 key = item.get("Index")
                                 if key:
                                     all_questions_map[key] = item
            except:
                pass

        new_questions_count = 0

        # Progress bar for learn questions per unit
        if not silent:
            learn_tqdm = tqdm(total=self.unit_count, desc=f"Processing {course_name} (Learn)", leave=False, unit="unit")
        empty_unit_count = 0
        for unit in range(1, self.unit_count + 1):
            if self.local_only:
                continue

            unit_has_questions = False

            # Loop multiple times to accumulate questions (random subset logic)
            # Try 5 times per unit
            for attempt in range(self.learn_attempts):  # use configurable attempts
                url = f"{URL_GET_LEARN_QUESTIONS}/{urllib.parse.quote(course_code)}/{unit}"
                try:
                    response = requests.get(url, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        questions = data.get("QuestionAnswer", [])

                        if questions:
                            unit_has_questions = True

                            # Process questions
                            for q in questions:
                                key = q.get("Index")
                                if key and key not in all_questions_map:
                                    all_questions_map[key] = q
                                    new_questions_count += 1

                        # If we got questions, we might want to download the PDF once
                        # PDF download disabled for faster processing
                        # if attempt == 0 and questions:
                        #      self.download_learn_questions_pdf(course_code, unit, materials_dir)

                    else:
                        pass
                except Exception as e:
                    tqdm.write(f"      Exception fetching learn questions for Unit {unit}: {e}")

                # Small delay between attempts
                time.sleep(0.2)

            if not unit_has_questions:
                empty_unit_count += 1
            else:
                empty_unit_count = 0

            # Save incrementally if we found new questions or just periodically
            if unit_has_questions:
                 self.save_learn_questions(course_name, filepath_processed, filepath_raw, filepath_md, all_questions_map, list(all_questions_map.values()), silent, new_questions_count)

            if empty_unit_count >= DEFAULT_EMPTY_UNIT_THRESHOLD:
                break
            # Update progress bar
            if not silent:
                learn_tqdm.update(1)
        # Final save
        self.save_learn_questions(course_name, filepath_processed, filepath_raw, filepath_md, all_questions_map, list(all_questions_map.values()), silent, new_questions_count)

    def redact_pii(self, data):
        """Recursively remove potential PII keys from data."""
        if isinstance(data, dict):
            return {k: self.redact_pii(v) for k, v in data.items() if k not in ["StudentId", "Name", "Surname", "TcKimlikNo", "Email", "Phone", "Token", "Authorization"]}
        elif isinstance(data, list):
            return [self.redact_pii(i) for i in data]
        else:
            return data

    def save_learn_questions(self, course_name, filepath_processed, filepath_raw, filepath_md, all_questions_map, all_raw_data, silent, new_questions_count):
        if not all_questions_map:
            if not silent:
                 tqdm.write(f"      No 'Sorularla Öğrenelim' questions found for {course_name}")
            return

        # Convert map back to list and sort
        all_questions = list(all_questions_map.values())
        # Sort by Unit, Title (empty string if None), then Index
        all_questions.sort(key=lambda x: (
            int(x.get("UniteNo") or 0),
            str(x.get("Title") or ""),
            int(x.get("Index") or 0)
        ))



        try:
            with open(filepath_processed, 'w', encoding='utf-8') as f:
                json.dump(all_questions, f, indent=4, ensure_ascii=False)

            # Redact PII from raw data before saving
            cleaned_raw_data = self.redact_pii(all_raw_data)
            with open(filepath_raw, 'w', encoding='utf-8') as f:
                json.dump(cleaned_raw_data, f, indent=4, ensure_ascii=False)

            # Generate Markdown
            md_content = f"# {course_name} - Sorularla Öğrenelim\n\n"

            questions_by_unit = {}
            for q in all_questions:
                u = q.get("UniteNo", "Diğer")
                if u not in questions_by_unit:
                    questions_by_unit[u] = []
                questions_by_unit[u].append(q)

            sorted_units = sorted(questions_by_unit.keys(), key=lambda x: int(x) if isinstance(x, int) or (isinstance(x, str) and x.isdigit()) else 999)

            for u in sorted_units:
                md_content += f"## Ünite {u}\n\n"
                current_title = None
                for q in questions_by_unit[u]:
                    question_text = clean_html(q.get("Question", ""))
                    answer_text = clean_html(q.get("Answer", ""))
                    title = clean_html(q.get("Title", ""))

                    if title and title != current_title:
                        md_content += f"### {title}\n\n"
                        current_title = title

                    md_content += f"**Soru:** {question_text}\n\n"
                    md_content += f"**Cevap:** {answer_text}\n\n"
                    md_content += "---\n\n"

            with open(filepath_md, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Only print if we actually saved something new or it's the final save?
            # Let's just print.
            if not silent:
               tqdm.write(f"      Saved {len(all_questions)} learn questions ({new_questions_count} new) for {course_name}")
        except Exception as e:
            if not silent:
                tqdm.write(f"      Error saving learn questions for {course_name}: {e}")
