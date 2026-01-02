import json
import os
import sys
import time
import requests
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.pipeline import QuestionPipeline
from libs.ata_lib import (
    DERSLER_FILE,
    RAW_JSON_DIR,
    OUTPUT_DIR
)

BASE_URL = "https://vtakip.ataaof.edu.tr/atametaservice.asmx/GetDenemeSoruByUnite"

class AtaPipeline(QuestionPipeline):
    def __init__(self, no_cache=False, offline=False):
        super().__init__(
            output_root=OUTPUT_DIR,
            no_cache=no_cache,
            offline=offline
        )

    def generate_dersler_json(self):
        """Generates the central dersler.json for ATA-AÖF matching the Anadolu/Auzef format."""
        if not os.path.exists(DERSLER_FILE):
            return

        with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
            courses = json.load(f)

        structured = []
        for i in range(1, 9):
            structured.append({"donem": i, "dersler": []})

        for course in courses:
            donem_raw = course.get("Donem")
            try:
                donem = int(donem_raw) if donem_raw else None
            except (ValueError, TypeError):
                donem = None

            if not donem or donem > 8:
                continue

            safe_name = self.get_safe_course_name(course)
            prefix = self.get_filename_prefix(course)

            course_entry = {
                "dersAdi": course.get("CourseName"),
                "id": str(course.get("DersId")),
                "sources": [
                    {
                        "name": "Alıştırma Soruları",
                        "url": f"json/Donem {donem}/{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları.json"
                    }
                ]
            }
            structured[donem-1]["dersler"].append(course_entry)

        output_path = os.path.join(self.output_root, "sorular", "dersler.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured, f, ensure_ascii=False, indent=4)
        tqdm.write(f"  Generated {output_path}")

    def fetch_raw_questions(self, course, unit, silent=False):
        ders_id = course.get("DersId")
        if not ders_id:
            return None

        all_questions = {}

        # Retry 7 times
        for i in range(10):
            try:
                url = f"{BASE_URL}?dersId={ders_id}&unite={unit}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        for q in data:
                            q_id = q.get("SoruID")
                            if q_id:
                                all_questions[q_id] = q
                    else:
                        if not all_questions:
                            break
            except Exception as e:
                pass

            time.sleep(0.2)

        return list(all_questions.values())

    def transform_question(self, raw_question, course, unit):
        raw_copy = raw_question.copy()
        is_web_design = "Web Tasarımının Temelleri" in course.get("CourseName", "")

        if is_web_design:
            # ONLY protect tags in options. Question text and explanations should use standard formatting.
            formatting_tags = {'b', 'strong', 'i', 'em', 'u', 'ins', 'sub', 'sup', 'hr'}

            # For options, we protect almost everything as code, EXCEPT the very basics.
            # But wait, if they have bold in options, we might want that too?
            # Usually options are just code or just text.
            fields_to_protect = ['A', 'B', 'C', 'D', 'E']
            for field in fields_to_protect:
                val = raw_copy.get(field)
                if val and isinstance(val, str):
                    # PRE-CLEAN: Normalize noisy br tags and strip trailing ones
                    # This prevents artifacts like <br type="_moz" /> from being protected.
                    val = re.sub(r'<br\b[^>]*>', '<br/>', val, flags=re.I)
                    # If it has other content, strip trailing breaks.
                    # If it's ONLY breaks, leave one so it can be protected as the answer.
                    if re.sub(r'<br/>|\s|\n', '', val):
                        val = re.sub(r'(<br/>|\s|\n)+$', '', val)

                    # Step 1: Protect escaped entities &lt;tag&gt;
                    def protect_entity(match):
                        tag_content = match.group(1).strip()
                        # Clean noisy br tags but preserve the self-closing slash if present
                        if tag_content.lower().startswith('br'):
                            # Remove attributes like type="_moz" but keep the slash if it was there
                            tag_content = 'br /' if '/' in tag_content else 'br'

                        name_match = re.search(r'([a-zA-Z0-9]+)', tag_content)
                        if name_match:
                            tag_name = name_match.group(1).lower()
                            if tag_name not in formatting_tags:
                                return f"TECHTAGLT{tag_content}TECHTAGGT"
                        elif tag_content.startswith('!'):
                            return f"TECHTAGLT{tag_content}TECHTAGGT"
                        return match.group(0)

                    val = re.sub(r'&lt;([/!?[a-zA-Z0-9].*?)&gt;', protect_entity, val, flags=re.IGNORECASE)
                    val = re.sub(r'&LT;([/!?[a-zA-Z0-9].*?)&GT;', protect_entity, val, flags=re.IGNORECASE)

                    # Step 2: Protect literal tags <tag>
                    def protect_literal(match):
                        tag_content = match.group(1).strip()
                        # Clean noisy br tags
                        if tag_content.lower().startswith('br'):
                            # Standardize literal artifacts to br / if noisy,
                            # but keep original if it was just 'br'
                            if len(tag_content) > 2: # has attributes or /
                                tag_content = 'br /'
                            else:
                                tag_content = 'br'

                        name_match = re.search(r'([a-zA-Z0-9]+)', tag_content)
                        if name_match:
                            tag_name = name_match.group(1).lower()
                            if tag_name not in formatting_tags:
                                return f"TECHTAGLT{tag_content}TECHTAGGT"
                        elif tag_content.startswith('!'):
                            return f"TECHTAGLT{tag_content}TECHTAGGT"
                        return match.group(0)

                    val = re.sub(r'<([/!?[a-zA-Z0-9][^>]*)>', protect_literal, val)
                    raw_copy[field] = val

        # Use base transformation first (cleans HTML)
        q = super().transform_question(raw_copy, course, unit)

        # Restore placeholders for Web Design course
        if is_web_design:
            fields_to_protect = ['A', 'B', 'C', 'D', 'E']
            for field in fields_to_protect:
                val = q.get(field)
                if val and isinstance(val, str):
                    q[field] = val.replace('TECHTAGLT', '&lt;').replace('TECHTAGGT', '&gt;')

        # Load external explanations lazily
        if not hasattr(self, "_aciklama_mapping"):
            mapping = {}
            import glob
            # Load from output/ATA-AÖF/json/Donem X recursively for *Cevaplar.json
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'ATA-AÖF', 'json')
            for path in glob.glob(os.path.join(base_dir, '**', '*Cevaplar.json'), recursive=True):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data:
                            sid = entry.get('SoruID')
                            aciklama = entry.get('Aciklama')
                            if sid and aciklama:
                                mapping[str(sid)] = aciklama
                except Exception:
                    pass
            self._aciklama_mapping = mapping

        sid = q.get("SoruID")
        if sid and str(sid) in self._aciklama_mapping:
            q["Aciklama"] = self._aciklama_mapping[str(sid)]

        try:
            donem = int(course.get("Donem", 0))
        except (ValueError, TypeError):
            donem = 0

        somestre = (donem - 1) % 2 + 1 if donem > 0 else 0
        q["Somestre"] = somestre
        q["Donem"] = donem
        q["DersAd"] = course.get("CourseName")
        q["Unite"] = unit

        if "DersId" not in q and "DersId" in course:
             q["DersId"] = course["DersId"]

        return q

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ATA AÖF Soru Getirici")
    parser.add_argument("--course", help="Process only specific course (name match)")
    parser.add_argument("--unit", type=int, help="Process only specific unit index (1-20)")
    parser.add_argument("--parallel", type=int, default=1, help="Number of courses to process in parallel")
    parser.add_argument("--no-cache", action="store_true", help="Ignore existing cache and re-fetch from API")
    parser.add_argument("--offline", action="store_true", help="Regenerate all files from existing Raw downloads without API calls")
    args = parser.parse_args()

    if not os.path.exists(DERSLER_FILE):
        tqdm.write(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    filtered_courses = []
    for course in courses:
        if args.course:
            c_name = course.get("CourseName", "").lower()
            search = args.course.lower()
            if search not in c_name:
                continue
        filtered_courses.append(course)

    tqdm.write(f"Found {len(courses)} courses, processing {len(filtered_courses)} courses.")

    if args.parallel > 1:
        import queue
        slot_queue = queue.Queue()
        for i in range(1, args.parallel + 1):
            slot_queue.put(i)

        def process_course_worker(course_obj):
            slot = slot_queue.get()
            try:
                pipeline = AtaPipeline(no_cache=args.no_cache, offline=args.offline)
                pipeline.process_course(course_obj, target_unit=args.unit, tqdm_position=slot)
                return True, course_obj.get('CourseName', 'Unknown')
            except Exception as e:
                return False, f"{course_obj.get('CourseName', 'Unknown')}: {str(e)}"
            finally:
                slot_queue.put(slot)

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = [executor.submit(process_course_worker, c) for c in filtered_courses]

            with tqdm(total=len(filtered_courses), desc="Total Progress", position=0) as pbar:
                for future in as_completed(futures):
                    success, name = future.result()
                    pbar.update(1)

        # Always generate dersler.json after all courses processed
        AtaPipeline(no_cache=args.no_cache, offline=args.offline).generate_dersler_json()
    else:
        pipeline = AtaPipeline(no_cache=args.no_cache, offline=args.offline)
        with tqdm(total=len(filtered_courses), desc="Processing courses", unit="course") as pbar:
            for course in filtered_courses:
                pbar.set_postfix_str(f"{course.get('CourseName', 'Unknown')[:20]}", refresh=True)
                pipeline.process_course(course, target_unit=args.unit)
                pbar.update(1)
        pipeline.generate_dersler_json()

if __name__ == "__main__":
    main()
