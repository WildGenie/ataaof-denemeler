import os
import json
import time
from abc import ABC, abstractmethod
from libs.shared import clean_html, questions_to_markdown
from tqdm import tqdm

class QuestionPipeline(ABC):
    def __init__(self, raw_dir, json_dir, full_json_dir, md_dir, no_cache=False):
        self.raw_dir = raw_dir
        self.json_dir = json_dir
        self.full_json_dir = full_json_dir
        self.md_dir = md_dir
        self.no_cache = no_cache
        self.setup_directories()

    def setup_directories(self):
        for d in [self.raw_dir, self.json_dir, self.full_json_dir, self.md_dir]:
            if d and not os.path.exists(d):
                os.makedirs(d)

    @abstractmethod
    def fetch_raw_questions(self, course, unit):
        """
        Fetch raw questions for a specific unit of a course.
        Must return a list of dictionaries or None/empty list.
        """
        pass

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
        return course.get("DersiVeren", "ATA-AÖF")

    def get_safe_course_name(self, course):
        return "".join([c for c in course.get("CourseName", "") if c.isalnum() or c in (' ', '-', '_')]).strip()

    def process_course(self, course, target_unit=None):
        """
        Process a single course.
        Fetches, transforms, saves raw/clean/full data, and generates Markdown.
        If target_unit is specified, only that unit is processed.
        """
        course_name = course.get("CourseName")
        donem = course.get("Donem")

        tqdm.write(f"Processing {course_name} (Dönem: {donem})...")

        tum_sorular = []
        consecutive_empty_units = 0

        # Determine unit range
        if target_unit:
            units_to_process = [target_unit]
        else:
            units_to_process = range(1, 15)

        for unit in units_to_process:
            questions = self.process_unit(course, unit)
            if questions:
                tum_sorular.extend(questions)
                consecutive_empty_units = 0
            else:
                consecutive_empty_units += 1
                if not target_unit and consecutive_empty_units >= 3:
                    tqdm.write(f"  Stopping after {consecutive_empty_units} consecutive empty units.")
                    break

        if tum_sorular:
            self.save_full_course(course, tum_sorular)
        else:
            tqdm.write(f"  No questions found for {course_name}.")

    def process_unit(self, course, unit):
        # 1. Get Raw
        raw_questions = self.get_or_fetch_raw(course, unit)
        if not raw_questions:
            return []

        # 2. Transform
        cleaned_questions = []
        for q in raw_questions:
            cleaned_q = self.transform_question(q, course, unit)
            if cleaned_q:
                cleaned_questions.append(cleaned_q)

        # 3. Save Unit JSON
        if cleaned_questions:
            self.save_unit_json(course, unit, cleaned_questions)

        return cleaned_questions

    def get_or_fetch_raw(self, course, unit):
        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Unite {unit:02d} - Raw.json"
        path = os.path.join(self.raw_dir, filename)

        # Try to load from cache (unless no_cache is set)
        if not self.no_cache and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        tqdm.write(f"    Unit {unit}: Loaded {len(data)} raw questions from cache.")
                        return data
            except Exception as e:
                tqdm.write(f"    Unit {unit}: Error loading cache {path}: {e}. Will re-fetch.")

        # Fetch from API
        raw_data = self.fetch_raw_questions(course, unit)

        # Save to cache if we got data
        if raw_data:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=4)
                tqdm.write(f"    Unit {unit}: Fetched and saved {len(raw_data)} raw questions.")
            except Exception as e:
                tqdm.write(f"    Unit {unit}: Error saving raw cache: {e}")
        else:
            tqdm.write(f"    Unit {unit}: No questions found.")

        return raw_data or []

    def save_unit_json(self, course, unit, questions):
        # Sort by SoruID safely
        questions.sort(key=lambda x: int(x.get("SoruID", 0)) if str(x.get("SoruID", "")).isdigit() else 0)

        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Unite {unit:02d}.json"
        path = os.path.join(self.json_dir, filename)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

    def save_full_course(self, course, questions):
        # Deduplicate by SoruID
        unique = {}
        for q in questions:
            qid = q.get('SoruID')
            if qid:
                unique[qid] = q

        questions = list(unique.values())

        # Sort by Unit, then SoruID
        questions.sort(key=lambda x: (
            int(x.get("Unite", 0)) if str(x.get("Unite", "")).isdigit() else 0,
            int(x.get("SoruID", 0)) if str(x.get("SoruID", "")).isdigit() else 0
        ))

        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")

        # Save Full JSON
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Tüm Sorular.json"
        path = os.path.join(self.full_json_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

        # Generate Markdown
        md_filename = f"{prefix} - Dönem {donem} - {safe_name} - Sorular.md"
        md_path = os.path.join(self.md_dir, md_filename)

        md_content = f"# {course.get('CourseName')} (Dönem {donem}) - Tüm Sorular\n\n"
        current_unit = None
        for q in questions:
            unit = q.get('Unite')
            # Try to convert unit to int for display
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

        tqdm.write(f"  Saved {len(questions)} unique questions to {filename} and {md_filename}")
