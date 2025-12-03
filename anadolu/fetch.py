import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_pipeline import AnadoluPipeline
from libs.anadolu_lib import (
    DERSLER_FILE,
    JSON_DIR,
    setup_directories,
    DEFAULT_UNIT_COUNT,
    DEFAULT_FETCH_ATTEMPTS,
    DEFAULT_LEARN_ATTEMPTS
)

# Load environment variables
load_dotenv()
def process_course_wrapper(pipeline, course, args, tqdm_position=None):
    """Wrapper function for parallel course processing"""
    try:
        silent = (tqdm_position is not None)

        # Fetch materials only if needed for download_exams, infographics, summaries or if explicitly requested
        if args.materials or args.download_exams or args.infographics or args.summaries:
            pipeline.fetch_and_save_materials(course, silent=silent)

        if args.download_exams:
            pipeline.download_past_exams(course, silent=silent)

        if args.infographics:
            pipeline.download_infographics(course, silent=silent)

        if args.summaries:
            pipeline.download_summaries(course, silent=silent)

        if args.learn_questions:
            pipeline.process_learn_questions(course, silent=False, tqdm_position=tqdm_position)

        if args.questions:
            pipeline.process_course(course, target_unit=args.unit, tqdm_position=tqdm_position)

        if args.pdf:
            if args.unit:
                pipeline.fetch_pdf(course, args.unit, silent=silent)
            else:
                for u in range(1, pipeline.unit_count + 1):
                    pipeline.fetch_pdf(course, u, silent=silent)

        if args.chapters:
            course_code = course.get('DersKodu')
            if course_code:
                pipeline.fetch_chapters(course_code, silent=silent)

        return True, course.get('CourseName', 'Unknown')
    except Exception as e:
        return False, f"{course.get('CourseName', 'Unknown')}: {str(e)}"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Anadolu AÖF Soru Getirici")
    parser.add_argument("--course", help="Filter by course name or code (partial match)")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses defined in enrolled_courses.json")
    parser.add_argument("--unit", type=int, help="Fetch specific unit only")
    parser.add_argument("--pdf", action="store_true", help="Fetch PDFs (Exam and Solution)")
    parser.add_argument("--chapters", action="store_true", help="Fetch chapters for the selected course(s)")
    parser.add_argument("--materials", action="store_true", help="Fetch materials list for the selected course(s)")
    parser.add_argument("--download-exams", action="store_true", help="Download past exams based on materials list")
    parser.add_argument("--infographics", action="store_true", help="Download infographics based on materials list")
    parser.add_argument("--summaries", action="store_true", help="Download unit summaries based on materials list")
    parser.add_argument("--learn-questions", action="store_true", help="Fetch 'Sorularla Öğrenelim' questions and PDFs")
    parser.add_argument("--questions", action="store_true", help="Fetch standard question bank")
    parser.add_argument("--parallel", type=int, default=1, metavar="N",
                       help="Number of parallel workers (default: 1, sequential)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and force API fetch")

    parser.add_argument("--local-only", action="store_true", help="Skip fetching from API, only process existing local files")
    parser.add_argument("--learn-attempts", type=int, default=DEFAULT_LEARN_ATTEMPTS, help=f"Number of API attempts per unit for 'Sorularla Öğrenelim' (default: {DEFAULT_LEARN_ATTEMPTS})")
    parser.add_argument("--fetch-attempts", type=int, default=DEFAULT_FETCH_ATTEMPTS, help=f"Number of API attempts per unit for standard questions (default: {DEFAULT_FETCH_ATTEMPTS})")
    parser.add_argument("--unit-count", type=int, default=DEFAULT_UNIT_COUNT, help=f"Number of units to process (default: {DEFAULT_UNIT_COUNT})")

    args = parser.parse_args()

    # Default behavior: If no specific action flags are set, fetch standard questions (legacy behavior)
    if not (args.download_exams or args.learn_questions or args.questions or args.materials or args.chapters or args.pdf or args.infographics or args.summaries):
        args.questions = True

    setup_directories() # Keep this if it's still needed for general setup

    if not os.path.exists(DERSLER_FILE):
        tqdm.write(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # Filter courses
    if args.course:
        # Assuming 'Ad' is the course name field, and 'DersKodu' is the course code
        courses = [c for c in courses if args.course.lower() in c.get('DersKodu', '').lower() or args.course.lower() in c.get('CourseName', '').lower()]

    if args.enrolled:
        enrolled_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrolled_courses.json")
        if os.path.exists(enrolled_file):
            try:
                with open(enrolled_file, 'r', encoding='utf-8') as f:
                    enrolled_data = json.load(f)
                    # Extract codes. enrolled_data is a list of dicts with "kod" key.
                    enrolled_codes = [c.get("kod") for c in enrolled_data]

                    # Filter main courses list
                    courses = [c for c in courses if c.get("DersKodu") in enrolled_codes]
                    tqdm.write(f"Filtered to {len(courses)} enrolled courses.")
            except Exception as e:
                tqdm.write(f"Error reading enrolled courses: {e}")
                return
        else:
            tqdm.write(f"Error: {enrolled_file} not found. Please create it first.")
            return

    if not courses:
        tqdm.write("No courses found.")
        return

    tqdm.write(f"Found {len(courses)} courses, processing {len(courses)} courses.")

    # Assuming AnadoluPipeline is defined/imported
    # Correct instantiation of AnadoluPipeline
    # Directories are now handled internally or via updated anadolu_lib constants
    # We pass None or dummy values if the constructor still expects them, or update the constructor.
    # Let's check QuestionPipeline constructor. It expects (raw_json_dir, json_dir, full_json_dir, md_dir, no_cache=False)
    # We should probably update QuestionPipeline or pass the new JSON_DIR for all of them as a fallback,
    # but since we override saving logic in fetch.py, it might be fine.
    # Let's pass JSON_DIR for all dir arguments for now, as they are mostly unused in the overridden methods or handled dynamically.
    pipeline = AnadoluPipeline(JSON_DIR, JSON_DIR, JSON_DIR, JSON_DIR, no_cache=args.no_cache,
                               fetch_attempts=args.fetch_attempts,
                               learn_attempts=args.learn_attempts,
                               unit_count=args.unit_count,
                               local_only=args.local_only)

    if args.parallel > 1:
        tqdm.write(f"Using {args.parallel} parallel workers...")

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            # Submit all tasks
            futures = {}
            for i, course in enumerate(courses):
                # Assign a position from 1 to N (leaving 0 for main bar)
                position = (i % args.parallel) + 1
                future = executor.submit(process_course_wrapper, pipeline, course, args, tqdm_position=position)
                futures[future] = course

            # Process results with progress bar
            for future in tqdm(as_completed(futures), total=len(courses), desc="Processing courses"):
                course = futures[future]
                try:
                    success, result = future.result()
                    if not success:
                        tqdm.write(f"Error processing {course.get('DersKodu', 'Unknown')}: {result}")
                except Exception as exc:
                    tqdm.write(f"Exception processing {course.get('DersKodu', 'Unknown')}: {exc}")
    else:
        # Sequential processing with progress bar
        for course in tqdm(courses, desc="Processing courses"):
            # Fetch materials only if needed for download_exams, infographics, summaries or if explicitly requested
            if args.materials or args.download_exams or args.infographics or args.summaries:
                pipeline.fetch_and_save_materials(course)

            if args.download_exams:
                pipeline.download_past_exams(course)

            if args.infographics:
                pipeline.download_infographics(course)

            if args.summaries:
                pipeline.download_summaries(course)

            if args.learn_questions:
                pipeline.process_learn_questions(course)

            if args.questions:
                pipeline.process_course(course, target_unit=args.unit)

            if args.pdf:
                if args.unit:
                    pipeline.fetch_pdf(course, args.unit)
                else:
                    for u in tqdm(range(1, 9), desc=f"  Fetching PDFs", leave=False, unit="unit"):
                        pipeline.fetch_pdf(course, u)

            if args.chapters:
                course_code = course.get('DersKodu')
                if course_code:
                    pipeline.fetch_chapters(course_code)

if __name__ == "__main__":
    main()
