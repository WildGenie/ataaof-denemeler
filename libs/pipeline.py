import os
import json
import time
from abc import ABC, abstractmethod
from libs.shared import clean_html, questions_to_markdown
from tqdm import tqdm

class QuestionPipeline(ABC):
    def __init__(self, raw_dir, json_dir, full_json_dir, md_dir, no_cache=False, offline=False):
        self.raw_dir = raw_dir
        self.json_dir = json_dir
        self.full_json_dir = full_json_dir
        self.md_dir = md_dir
        self.no_cache = no_cache
        self.offline = offline
        self.setup_directories()

    def setup_directories(self):
        for d in [self.raw_dir, self.json_dir, self.full_json_dir, self.md_dir]:
            if d and not os.path.exists(d):
                os.makedirs(d)

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
            questions = self.process_unit(course, unit, silent=(tqdm_position is not None))
            if questions:
                tum_sorular.extend(questions)
                consecutive_empty_units = 0
                if pbar:
                    pbar.set_postfix_str(f"U{unit}: {len(questions)}", refresh=False)
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
            self.save_full_course(course, tum_sorular)
        else:
            if tqdm_position is None:
                tqdm.write(f"  No questions found for {course_name}.")

    def process_unit(self, course, unit, silent=False):
        # 1. Get Raw
        # In offline mode, skip even checking cache existence if we want it to be strict,
        # but usually get_or_fetch_raw handles it.
        raw_questions = self.get_or_fetch_raw(course, unit, silent=silent)
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

    def get_question_id(self, question):
        """Helper to get ID from raw question (supports Anadolu and Ata formats)"""
        return question.get("SoruID") or question.get("QuestionId")

    def get_or_fetch_raw(self, course, unit, silent=False):
        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Unite {unit:02d} - Raw.json"
        path = os.path.join(self.raw_dir, filename)

        cached_data = []
        # Always try to load from cache first to preserve existing data
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f) or []
            except Exception as e:
                tqdm.write(f"    Unit {unit}: Error loading cache {path}: {e}. Will re-fetch.")

        if self.offline:
            if not silent:
                if cached_data:
                    tqdm.write(f"    Unit {unit}: Offline mode. Loaded {len(cached_data)} raw questions from cache.")
                else:
                    tqdm.write(f"    Unit {unit}: Offline mode. No cached questions found.")
            return cached_data

        # If cache exists and we are NOT ignoring it, return it
        if not self.no_cache and cached_data:
            if not silent:
                tqdm.write(f"    Unit {unit}: Loaded {len(cached_data)} raw questions from cache.")
            return cached_data

        # Fetch from API (because no_cache=True or cache was empty)
        fetched_data = self.fetch_raw_questions(course, unit, silent=silent)

        if fetched_data:
            # Merge fetched data into cached data
            # Create a map of existing questions by ID
            merged_map = {self.get_question_id(q): q for q in cached_data if self.get_question_id(q)}

            # Update/Add fetched questions
            new_count = 0
            for q in fetched_data:
                qid = self.get_question_id(q)
                if qid:
                    if qid not in merged_map:
                        new_count += 1
                    merged_map[qid] = q

            final_data = list(merged_map.values())

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=4)

                if not silent:
                    msg = f"    Unit {unit}: Fetched {len(fetched_data)} questions."
                    if cached_data:
                        msg += f" Merged with {len(cached_data)} existing. Total: {len(final_data)}."
                    else:
                        msg += f" Saved {len(final_data)} questions."
                    tqdm.write(msg)
            except Exception as e:
                tqdm.write(f"    Unit {unit}: Error saving raw cache: {e}")

            return final_data
        else:
            # If fetch returned nothing, but we have cache, keep cache?
            # User said "soruları çekip eklemesi lazım" -> implies we want to add to cache.
            # If API returns nothing, we probably shouldn't delete cache.
            if cached_data:
                if not silent:
                    tqdm.write(f"    Unit {unit}: API returned no questions, keeping {len(cached_data)} cached questions.")
                return cached_data
            else:
                if not silent:
                    tqdm.write(f"    Unit {unit}: No questions found.")
                return []

    def save_unit_json(self, course, unit, questions):
        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Unite {unit:02d}.json"
        path = os.path.join(self.json_dir, filename)

        # Load existing questions to preserve OlusturmaTarihi
        existing_questions = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for q in existing_data:
                        qid = q.get('SoruID')
                        if qid and q.get('OlusturmaTarihi'):
                            existing_questions[qid] = q.get('OlusturmaTarihi')
            except Exception as e:
                tqdm.write(f"  Warning: Could not load existing unit file: {e}")

        # Update OlusturmaTarihi for existing questions
        for q in questions:
            qid = q.get('SoruID')
            if qid and qid in existing_questions:
                q['OlusturmaTarihi'] = existing_questions[qid]

        # Sort by SoruID safely
        questions.sort(key=lambda x: int(x.get("SoruID", 0)) if str(x.get("SoruID", "")).isdigit() else 0)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

    def save_full_course(self, course, questions):
        prefix = self.get_filename_prefix(course)
        safe_name = self.get_safe_course_name(course)
        donem = course.get("Donem")

        # Load existing questions to preserve OlusturmaTarihi and merge data
        filename = f"{prefix} - Dönem {donem} - {safe_name} - Tüm Sorular.json"
        path = os.path.join(self.full_json_dir, filename)

        unique = {}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for q in existing_data:
                        qid = q.get('SoruID')
                        if qid:
                            unique[qid] = q
            except Exception as e:
                tqdm.write(f"  Warning: Could not load existing file: {e}")

        # Update with new questions
        for q in questions:
            qid = q.get('SoruID')
            if qid:
                # If question already exists, preserve its OlusturmaTarihi
                if qid in unique and unique[qid].get('OlusturmaTarihi'):
                    q['OlusturmaTarihi'] = unique[qid]['OlusturmaTarihi']
                unique[qid] = q

        questions = list(unique.values())

        # Sort by Unit, then SoruID
        questions.sort(key=lambda x: (
            int(x.get("Unite", 0)) if str(x.get("Unite", "")).isdigit() else 0,
            int(x.get("SoruID", 0)) if str(x.get("SoruID", "")).isdigit() else 0
        ))

        # Save Full JSON
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
