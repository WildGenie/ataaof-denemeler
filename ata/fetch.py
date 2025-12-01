import json
import os
import sys
import time
import requests

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.pipeline import QuestionPipeline
from libs.ata_lib import (
    DERSLER_FILE,
    RAW_JSON_DIR,
    JSON_DIR,
    FULL_JSON_DIR,
    MD_DIR
)

BASE_URL = "https://vtakip.ataaof.edu.tr/atametaservice.asmx/GetDenemeSoruByUnite"

class AtaPipeline(QuestionPipeline):
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
                        # Empty list returned.
                        # For Ata, this usually means no questions for this unit.
                        # We can stop retrying immediately.
                        if not all_questions:
                            # print(f"      Unit {unit} returned empty list. Stopping retries.")
                            break
            except Exception as e:
                pass

            time.sleep(0.2)

        return list(all_questions.values())

    def transform_question(self, raw_question, course, unit):
        # Use base transformation first (cleans HTML)
        q = super().transform_question(raw_question, course, unit)

        # Load external explanations lazily (cache in instance)
        if not hasattr(self, "_aciklama_mapping"):
            mapping = {}
            import glob
            # Path to data/aciklamalar relative to this file
            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'aciklamalar')
            for path in glob.glob(os.path.join(base_dir, '*.json')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data:
                            sid = entry.get('SoruID')
                            aciklama = entry.get('Aciklama')
                            if sid and aciklama:
                                mapping[sid] = aciklama
                except Exception:
                    pass
            self._aciklama_mapping = mapping

        # Merge external Aciklama if available
        sid = q.get("SoruID")
        if sid and sid in self._aciklama_mapping:
            q["Aciklama"] = self._aciklama_mapping[sid]

        # Inject metadata from course/args
        # Ensure Donem is an integer
        try:
            donem = int(course.get("Donem", 0))
        except (ValueError, TypeError):
            donem = 0

        # Somestre is 1 (Fall) or 2 (Spring)
        # Donem 1, 3, 5, 7 -> Fall (1)
        # Donem 2, 4, 6, 8 -> Spring (2)
        somestre = (donem - 1) % 2 + 1 if donem > 0 else 0

        q["Somestre"] = somestre
        q["Donem"] = donem
        q["DersAd"] = course.get("CourseName")
        q["Unite"] = unit

        # Ensure other fields are present/consistent if needed
        if "DersId" not in q and "DersId" in course:
             q["DersId"] = course["DersId"]

        return q

    # get_filename_prefix uses default implementation (DersiVeren or ATA-AÖF)

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def process_course_wrapper(pipeline, course, args):
    """Wrapper function for parallel course processing"""
    try:
        pipeline.process_course(course, target_unit=args.unit)
        return True, course.get('CourseName', 'Unknown')
    except Exception as e:
        return False, f"{course.get('CourseName', 'Unknown')}: {str(e)}"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ATA AÖF Soru Getirici")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--unit", type=int, help="Fetch specific unit only")
    parser.add_argument("--parallel", type=int, default=1, metavar="N",
                       help="Number of parallel workers (default: 1, sequential)")
    parser.add_argument("--no-cache", action="store_true", help="Force fetch from API and merge with cache")
    args = parser.parse_args()

    if not os.path.exists(DERSLER_FILE):
        tqdm.write(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # Filter courses
    filtered_courses = []
    for course in courses:
        if args.course:
            c_name = course.get("CourseName", "").lower()
            search = args.course.lower()
            if search not in c_name:
                continue
        filtered_courses.append(course)

    tqdm.write(f"Found {len(courses)} courses, processing {len(filtered_courses)} courses.")

    pipeline = AtaPipeline(RAW_JSON_DIR, JSON_DIR, FULL_JSON_DIR, MD_DIR, no_cache=args.no_cache)

    if args.parallel > 1:
        # Parallel processing
        tqdm.write(f"Using {args.parallel} parallel workers...")

        # Create a queue of available slots (1 to N) for progress bars
        # Slot 0 is reserved for the main progress bar
        import queue
        slot_queue = queue.Queue()
        for i in range(1, args.parallel + 1):
            slot_queue.put(i)

        def process_course_with_slots(pipeline, course, args):
            # Get a slot
            slot = slot_queue.get()
            try:
                pipeline.process_course(course, target_unit=args.unit, tqdm_position=slot)
                return True, course.get('CourseName', 'Unknown')
            except Exception as e:
                return False, f"{course.get('CourseName', 'Unknown')}: {str(e)}"
            finally:
                # Return slot
                slot_queue.put(slot)

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_course_with_slots, pipeline, course, args): course
                for course in filtered_courses
            }

            # Process results as they complete with progress bar
            # Position 0 is for the main bar
            with tqdm(total=len(filtered_courses), desc="Total Progress", unit="course", position=0, leave=True) as pbar:
                for future in as_completed(futures):
                    success, result = future.result()
                    if success:
                        # pbar.set_postfix_str(f"✓ {result}", refresh=False)
                        pass
                    else:
                        pbar.set_postfix_str(f"✗ {result}", refresh=False)
                    pbar.update(1)
    else:
        # Sequential processing
        with tqdm(total=len(filtered_courses), desc="Processing courses", unit="course") as pbar:
            for course in filtered_courses:
                pbar.set_postfix_str(f"Processing {course.get('CourseName', 'Unknown')}", refresh=True)
                pipeline.process_course(course, target_unit=args.unit)
                pbar.update(1)

if __name__ == "__main__":
    main()
