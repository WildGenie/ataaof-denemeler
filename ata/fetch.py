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
    def fetch_raw_questions(self, course, unit):
        ders_id = course.get("DersId")
        if not ders_id:
            return None

        all_questions = {}

        # Retry 7 times
        for i in range(7):
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

    # transform_question uses default implementation (clean_html)
    # get_filename_prefix uses default implementation (DersiVeren or ATA-AÖF)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ATA AÖF Soru Getirici")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--unit", type=int, help="Fetch specific unit only")
    args = parser.parse_args()

    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses.")

    pipeline = AtaPipeline(RAW_JSON_DIR, JSON_DIR, FULL_JSON_DIR, MD_DIR)

    for course in courses:
        # Filter by course name if provided
        if args.course:
            c_name = course.get("CourseName", "").lower()
            search = args.course.lower()
            if search not in c_name:
                continue

        pipeline.process_course(course, target_unit=args.unit)

if __name__ == "__main__":
    main()
