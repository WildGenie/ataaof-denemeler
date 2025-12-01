import json
import os
import sys
import time
import requests
import urllib.parse
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.pipeline import QuestionPipeline
from libs.anadolu_lib import (
    map_to_old_format,
    DERSLER_FILE,
    RAW_JSON_DIR,
    JSON_DIR,
    FULL_JSON_DIR,
    MD_DIR
)

# Load environment variables
load_dotenv()

HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://ekampus.anadolu.edu.tr',
    'accept': '*/*',
    'authorization': os.getenv('ANADOLU_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYyCOeM'),
}

class AnadoluPipeline(QuestionPipeline):
    def fetch_raw_questions(self, course, unit):
        course_code = course.get('DersKodu')
        if not course_code:
            return None

        url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/create/20/{urllib.parse.quote(course_code)}/{unit}"

        raw_questions_map = {}
        error_count = 0

        # Retry/Accumulate logic
        # Anadolu API returns random questions. We try 20 times to get as many unique questions as possible.
        # However, if the API explicitly returns an empty list or indicates "no questions" in a valid response,
        # we should probably stop early to avoid wasting time.
        # But Anadolu API might just return a random set, so empty list MIGHT mean no questions for this unit.

        for i in range(20):
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "Questions" in data and data["Questions"]:
                        for q in data["Questions"]:
                            raw_questions_map[q["QuestionId"]] = q
                    else:
                        # If we get a valid response but no questions, it's likely this unit has no questions.
                        # To be safe, we can count consecutive empty responses.
                        # If we get 3 empty responses in a row, we assume the unit is empty.
                        error_count += 1
                        if error_count >= 3 and not raw_questions_map:
                             tqdm.write(f"      Unit {unit} seems empty (3 empty responses). Stopping.")
                             break
                else:
                    error_count += 1
            except Exception as e:
                # tqdm.write(f"Error: {e}")
                error_count += 1

            time.sleep(0.1)

        return list(raw_questions_map.values())

    def transform_question(self, raw_question, course, unit):
        # Use map_to_old_format
        course_name = course.get("CourseName")
        donem = course.get("Donem")
        return map_to_old_format(raw_question, course_name, unit, donem)

    def get_filename_prefix(self, course):
        return "Anadolu"

    def fetch_pdf(self, course, unit):
        course_code = course.get('DersKodu')
        if not course_code:
            return

        # 1. Call Create API to get RandPart
        url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/create/20/{urllib.parse.quote(course_code)}/{unit}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rand_part = data.get("RandPart")
                if not rand_part:
                    tqdm.write(f"      Unit {unit}: Could not get RandPart for PDF.")
                    return

                # 2. Construct PDF URLs
                # Exam PDF: create-10-{course_code}-{unit}/{RandPart}
                # Solution PDF: ...?withsolution=1

                base_pdf_url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/examservice/getpdf/create-10-{course_code}-{unit}/{rand_part}"

                self.download_pdf(base_pdf_url, course, unit, "Soru")
                self.download_pdf(base_pdf_url + "?withsolution=1", course, unit, "Cevap")

            else:
                tqdm.write(f"      Unit {unit}: API Error {response.status_code} while fetching RandPart.")
        except Exception as e:
            tqdm.write(f"      Unit {unit}: Error fetching PDF info: {e}")

    def download_pdf(self, url, course, unit, suffix):
        from libs.anadolu_lib import PDF_DIR

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
                tqdm.write(f"      Downloaded PDF: {filename}")
            else:
                tqdm.write(f"      Failed to download PDF {suffix}: {response.status_code}")
        except Exception as e:
            tqdm.write(f"      Error downloading PDF {suffix}: {e}")

    def fetch_chapters(self, course_code):
        """Fetch chapter information for a given course code using the Anadolu API.
        Endpoint: https://ets-ws.anadolu.edu.tr/v2filikaapi/courseservice/getchapters/{course_code}?type=2
        Returns the parsed JSON response or None on failure.
        """
        url = f"https://ets-ws.anadolu.edu.tr/v2filikaapi/courseservice/getchapters/{urllib.parse.quote(course_code)}?type=2"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tqdm.write(f"      Fetched chapters for {course_code}: {len(data.get('Chapters', []))} items")
                return data
            else:
                tqdm.write(f"      Error fetching chapters for {course_code}: {response.status_code}")
                return None
        except Exception as e:
            tqdm.write(f"      Exception fetching chapters for {course_code}: {e}")
            return None


def process_course_wrapper(pipeline, course, args):
    """Wrapper function for parallel course processing"""
    try:
        pipeline.process_course(course, target_unit=args.unit)

        if args.pdf:
            if args.unit:
                pipeline.fetch_pdf(course, args.unit)
            else:
                for u in range(1, 15):
                    pipeline.fetch_pdf(course, u)

        if args.chapters:
            course_code = course.get('DersKodu')
            if course_code:
                pipeline.fetch_chapters(course_code)

        return True, course.get('CourseName', 'Unknown')
    except Exception as e:
        return False, f"{course.get('CourseName', 'Unknown')}: {str(e)}"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Anadolu AÖF Soru Getirici")
    parser.add_argument("--course", help="Filter by course name or code (partial match)")
    parser.add_argument("--unit", type=int, help="Fetch specific unit only")
    parser.add_argument("--pdf", action="store_true", help="Fetch PDFs (Exam and Solution)")
    parser.add_argument("--chapters", action="store_true", help="Fetch chapters for the selected course(s)")
    parser.add_argument("--parallel", type=int, default=1, metavar="N",
                       help="Number of parallel workers (default: 1, sequential)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and force API fetch")
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
            c_code = course.get("DersKodu", "").lower()
            search = args.course.lower()
            if search not in c_name and search not in c_code:
                continue
        filtered_courses.append(course)

    tqdm.write(f"Found {len(courses)} courses, processing {len(filtered_courses)} courses.")

    pipeline = AnadoluPipeline(RAW_JSON_DIR, JSON_DIR, FULL_JSON_DIR, MD_DIR, no_cache=args.no_cache)

    if args.parallel > 1:
        # Parallel processing with progress bar
        tqdm.write(f"Using {args.parallel} parallel workers...")

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_course_wrapper, pipeline, course, args): course
                for course in filtered_courses
            }

            # Process results with progress bar
            with tqdm(total=len(filtered_courses), desc="Processing courses", unit="course") as pbar:
                for future in as_completed(futures):
                    success, result = future.result()
                    if success:
                        pbar.set_postfix_str(f"✓ {result}")
                    else:
                        pbar.set_postfix_str(f"✗ {result}")
                    pbar.update(1)
    else:
        # Sequential processing with progress bar
        for course in tqdm(filtered_courses, desc="Processing courses", unit="course"):
            course_name = course.get('CourseName', 'Unknown')
            tqdm.write(f"Processing {course_name}...")

            pipeline.process_course(course, target_unit=args.unit)

            if args.pdf:
                if args.unit:
                    pipeline.fetch_pdf(course, args.unit)
                else:
                    for u in tqdm(range(1, 15), desc=f"  Fetching PDFs", leave=False, unit="unit"):
                        pipeline.fetch_pdf(course, u)

            if args.chapters:
                course_code = course.get('DersKodu')
                if course_code:
                    pipeline.fetch_chapters(course_code)

if __name__ == "__main__":
    main()
