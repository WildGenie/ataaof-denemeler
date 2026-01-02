import os
import json
import time
from abc import ABC, abstractmethod
from libs.shared import clean_html, questions_to_markdown
from tqdm import tqdm

class QuestionPipeline(ABC):
    def __init__(self, output_root, no_cache=False, offline=False):
        self.output_root = output_root
        self.raw_dir = os.path.join(output_root, "raw")
        self.no_cache = no_cache
        self.offline = offline
        self.setup_directories()

    def setup_directories(self):
        if not os.path.exists(self.raw_dir):
            os.makedirs(self.raw_dir)

        # Other directories are created dynamically based on semester

    @abstractmethod
    def fetch_raw_questions(self, course, unit, silent=False):
        """
        Fetch raw questions for a specific unit of a course.
        Must return a list of dictionaries or None/empty list.
        """
        raise NotImplementedError

    def transform_question(self, raw_question, course, unit):
        """
        Transform a raw question into the standardized format.
        Default implementation cleans HTML from standard fields.
        Override this if you need to map fields (e.g. Anadolu).
        """
        q = raw_question.copy()
        q['SoruMetni'] = clean_html(q.get('SoruMetni'))
        for opt in ['A', 'B', 'C', 'D', 'E']:
            q[opt] = clean_html(q.get(opt))
        if q.get('Aciklama'):
            q['Aciklama'] = clean_html(q.get('Aciklama'))
        return q

    def get_filename_prefix(self, course):
        """
        Return the prefix for filenames (e.g. "ATA-AÖF" or "Anadolu").
        Default attempts to use 'DersiVeren' from course dict, fallback to 'ATA-AÖF'.
        """
        return course.get("DersiVeren") or "ATA-AÖF"

    def get_safe_course_name(self, course):
        return "".join([c for c in course.get("CourseName", "") if c.isalnum() or c in (' ', '-', '_')]).strip()

    def process_course(self, course, target_unit=None, tqdm_position=None):
        """
        Process a single course.
        Fetches, transforms, saves raw/clean/full data, and generates Markdown.
        If target_unit is specified, only that unit is processed.
        If tqdm_position is specified, uses a positioned progress bar.
        """
        course_name = course.get("CourseName")
        donem = course.get("Donem")

        if tqdm_position is None:
            tqdm.write(f"Processing {course_name} (Dönem: {donem})...")

        tum_sorular = []
        tum_raw_sorular = []
        consecutive_empty_units = 0

        # Determine unit range
        if target_unit:
            units_to_process = [target_unit]
        else:
            units_to_process = range(1, 21)

        iterator = units_to_process
        pbar = None
        if tqdm_position is not None:
            # Shorten course name for display
            display_name = (course_name[:25] + '..') if len(course_name) > 25 else course_name
            pbar = tqdm(total=len(units_to_process), position=tqdm_position,
                       desc=f"{display_name:<27}", leave=False,
                       bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]")
            iterator = range(len(units_to_process)) # Iterate by index to manage pbar manually

        for i, unit in enumerate(units_to_process):
            raw_qs, cleaned_qs = self.process_unit(course, unit, silent=(tqdm_position is not None))

            if raw_qs:
                 tum_raw_sorular.extend(raw_qs)

            if cleaned_qs:
                tum_sorular.extend(cleaned_qs)
                consecutive_empty_units = 0
                if pbar:
                    pbar.set_postfix_str(f"U{unit}: {len(cleaned_qs)}", refresh=False)
            else:
                consecutive_empty_units += 1
                if pbar:
                    pbar.set_postfix_str(f"U{unit}: Empty", refresh=False)

                if not target_unit and consecutive_empty_units >= 10:
                    if tqdm_position is None:
                        tqdm.write(f"  Stopping after {consecutive_empty_units} consecutive empty units.")
                    break

            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

        if tum_sorular:
            self.save_full_course(course, tum_sorular, tum_raw_sorular)
        else:
            if tqdm_position is None:
                tqdm.write(f"  No questions found for {course_name}.")

    def process_unit(self, course, unit, silent=False):
        # 1. Get Raw
        raw_questions = self.get_or_fetch_raw(course, unit, silent=silent)
        if not raw_questions:
            return [], []

        # 2. Transform
        cleaned_questions = []
        for q in raw_questions:
            cleaned_q = self.transform_question(q, course, unit)
            if cleaned_q:
                cleaned_questions.append(cleaned_q)

        return raw_questions, cleaned_questions

    def get_question_id(self, question):
        """Helper to get ID from raw question (supports Anadolu and Ata formats)"""
        return question.get("SoruID") or question.get("QuestionId")

    def get_or_fetch_raw(self, course, unit, silent=False):
        # Construct path to the Combined Raw JSON
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        prefix = self.get_filename_prefix(course)

        json_donem_dir = os.path.join(self.output_root, "json", f"Donem {donem}")
        raw_filename = f"{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları - Raw.json"
        raw_path = os.path.join(json_donem_dir, raw_filename)

        cached_data = []
        if os.path.exists(raw_path):
            try:
                # TODO: Implement memory caching for this file to avoid re-reading 14 times
                with open(raw_path, 'r', encoding='utf-8') as f:
                    all_raw_data = json.load(f) or []

                # Filter for the specific unit
                # Questions usually have "Unite" field.
                # Need to handle string/int types leniently.
                target_unit_str = str(unit)
                for q in all_raw_data:
                    q_unit = q.get("Unite")
                    # Handle "3" vs 3 vs "03"
                    if str(q_unit).lstrip("0") == target_unit_str.lstrip("0"):
                        cached_data.append(q)

            except Exception as e:
                tqdm.write(f"    Unit {unit}: Error loading combined cache {raw_path}: {e}")

        if self.offline:
            return cached_data

        if not self.no_cache and cached_data:
            return cached_data

        # Fetch from API
        fetched_data = self.fetch_raw_questions(course, unit, silent=silent)

        # We do NOT save to individual unit file anymore.
        # The fetched data will be aggregated by process_course calls and saved to the combined file at the end.

        if fetched_data:
            return fetched_data
        else:
            return cached_data

    def save_full_course(self, course, questions, raw_questions=None):
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        prefix = self.get_filename_prefix(course)

        # 1. Save Full JSON to json/Donem X/
        json_donem_dir = os.path.join(self.output_root, "json", f"Donem {donem}")
        if not os.path.exists(json_donem_dir):
            os.makedirs(json_donem_dir)

        # Standard filename: [Prefix] - Dönem [X] - [Course Name] - Alıştırma Soruları.json
        json_filename = f"{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları.json"
        json_path = os.path.join(json_donem_dir, json_filename)

        # Standard Raw Filename
        raw_filename = f"{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları - Raw.json"
        raw_path = os.path.join(json_donem_dir, raw_filename)

        # Save Raw Questions Merger
        if raw_questions:
             # Merge raw logic similar to processed
             unique_raw = {}
             if os.path.exists(raw_path):
                 try:
                    with open(raw_path, 'r', encoding='utf-8') as f:
                        existing_raw = json.load(f)
                        for q in existing_raw:
                            qid = self.get_question_id(q)
                            if qid:
                                unique_raw[qid] = q
                 except: pass

             for q in raw_questions:
                 qid = self.get_question_id(q)
                 if qid:
                     unique_raw[qid] = q

             final_raw = list(unique_raw.values())
             # Sort Raw
             final_raw.sort(key=lambda x: (
                int(x.get("Unite", 0)) if str(x.get("Unite", "")).isdigit() else 0,
                int(str(self.get_question_id(x))) if str(self.get_question_id(x)).isdigit() else 0
             ))

             with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(final_raw, f, ensure_ascii=False, indent=4)


        unique = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for q in existing_data:
                        qid = q.get('SoruID')
                        if qid:
                            unique[qid] = q
            except Exception:
                pass

        # Update with new processed questions
        for q in questions:
            qid = q.get('SoruID')
            if qid:
                if qid in unique and unique[qid].get('OlusturmaTarihi'):
                    q['OlusturmaTarihi'] = unique[qid]['OlusturmaTarihi']
                unique[qid] = q

        questions = list(unique.values())
        questions.sort(key=lambda x: (
            int(x.get("Unite", 0)) if str(x.get("Unite", "")).isdigit() else 0,
            int(x.get("SoruID", 0)) if str(x.get("SoruID", "")).isdigit() else 0
        ))

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

        # 2. Save Markdown to Donem X/Course/Alıştırma Soruları.md
        course_dir = os.path.join(self.output_root, f"Donem {donem}", safe_name)
        if not os.path.exists(course_dir):
            os.makedirs(course_dir)

        materyaller_dir = os.path.join(course_dir, "Materyaller")
        if not os.path.exists(materyaller_dir):
            os.makedirs(materyaller_dir)

        md_path = os.path.join(course_dir, "Alıştırma Soruları.md")

        md_content = f"# {course.get('CourseName')} (Dönem {donem}) - Alıştırma Soruları\n\n"
        current_unit = None
        for q in questions:
            unit = q.get('Unite')
            try:
                unit_val = int(unit)
            except (ValueError, TypeError):
                unit_val = unit

            if unit_val != current_unit:
                md_content += f"## Unite {unit_val}\n"
                current_unit = unit_val
            md_content += questions_to_markdown([q])

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # 3. Create Materyaller/index.md
        if os.path.exists(materyaller_dir):
             files = sorted(os.listdir(materyaller_dir))
             pdf_files = [f for f in files if f.endswith(".pdf")]

             if pdf_files:
                 mat_index_path = os.path.join(materyaller_dir, "index.md")
                 mat_index_content = f"# {course.get('CourseName')} - Ders Materyalleri\n\n"
                 mat_index_content += "[🔙 Derse Dön](../index.md)\n\n"

                 for f in pdf_files:
                     safe_f = f.replace(" ", "%20")
                     if "Ünite Özeti" in f:
                         mat_index_content += f"### [📕 {f.replace('.pdf', '')}]( {safe_f} )\n\n"
                     elif "Ara Sınav" in f:
                         mat_index_content += f"### [📄 {f.replace('.pdf', '')}]( {safe_f} )\n\n"

                 # Add specific section for Units if they exist
                 unit_pdfs = [f for f in pdf_files if f.startswith("Ünite") and "Özeti" not in f]
                 if unit_pdfs:
                     mat_index_content += "### Ünite Kitapçıkları\n"
                     # Sort numerically by unit number
                     try:
                         unit_pdfs.sort(key=lambda x: int(x.split()[1].split('.')[0]))
                     except:
                         unit_pdfs.sort()

                     for f in unit_pdfs:
                         safe_f = f.replace(" ", "%20")
                         mat_index_content += f"- [📄 {f.replace('.pdf', '')}]( {safe_f} )\n"
                     mat_index_content += "\n"

                 with open(mat_index_path, 'w', encoding='utf-8') as f:
                     f.write(mat_index_content)

        # 4. Save Main index.md
        index_path = os.path.join(course_dir, "index.md")
        index_content = f"# {course.get('CourseName')}\n\n"
        index_content += "## Ders İçeriği\n\n"
        index_content += "### [📝 Alıştırma Soruları](Al%C4%B1%C5%9Ft%C4%B1rma%20Sorular%C4%B1.md)\n\n"

        if os.path.exists(materyaller_dir) and any(f.endswith(".pdf") for f in os.listdir(materyaller_dir)):
            index_content += "### [📂 Ders Materyalleri (PDF)](Materyaller/index.md)\n\n"

        index_content += "---\n"
        index_content += "[🔙 Ana Sayfaya Dön](../../)\n"

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)


        tqdm.write(f"  Saved {len(questions)} unique questions to {json_filename} and {safe_name}/Alıştırma Soruları.md")
