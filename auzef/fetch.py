import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.auzef_pipeline import AuzefPipeline
from libs.auzef_lib import (
    DERSLER_FILE,
    JSON_DIR,
    RAW_DIR,
    setup_directories
)

# Load environment variables
load_dotenv()

def process_course_wrapper(pipeline, course, args, tqdm_position=None):
    """Wrapper function for parallel course processing"""
    try:
        pipeline.process_course(course, target_unit=args.unit, tqdm_position=tqdm_position)
        return True, course.get('CourseName', 'Unknown')
    except Exception as e:
        return False, f"{course.get('CourseName', 'Unknown')}: {str(e)}"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AUZEF Soru Getirici")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--unit", type=int, help="Fetch specific unit only (if supported)")
    parser.add_argument("--parallel", type=int, default=1, metavar="N",
                       help="Number of parallel workers (default: 1, sequential)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and force API fetch")

    args = parser.parse_args()

    setup_directories()

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

    if not filtered_courses:
        tqdm.write("No courses found matching the filter.")
        return

    tqdm.write(f"Found {len(courses)} courses, processing {len(filtered_courses)} courses.")

    pipeline = AuzefPipeline(raw_dir=RAW_DIR, json_dir=JSON_DIR, no_cache=args.no_cache)

    if args.parallel > 1:
        tqdm.write(f"Using {args.parallel} parallel workers...")

        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            # Submit all tasks
            futures = {}
            for i, course in enumerate(filtered_courses):
                # Assign a position from 1 to N (leaving 0 for main bar)
                position = (i % args.parallel) + 1
                future = executor.submit(process_course_wrapper, pipeline, course, args, tqdm_position=position)
                futures[future] = course

            # Process results with progress bar
            with tqdm(total=len(filtered_courses), desc="Total Progress", unit="course", position=0, leave=True) as pbar:
                for future in as_completed(futures):
                    course = futures[future]
                    try:
                        success, result = future.result()
                        if not success:
                            tqdm.write(f"Error processing {course.get('CourseName', 'Unknown')}: {result}")
                    except Exception as exc:
                        tqdm.write(f"Exception processing {course.get('CourseName', 'Unknown')}: {exc}")
                    pbar.update(1)
    else:
        # Sequential processing with progress bar
        with tqdm(filtered_courses, desc="Processing AUZEF Courses") as pbar:
            for course in pbar:
                pbar.set_postfix_str(f"Course: {course.get('CourseName', 'Unknown')}", refresh=True)
                pipeline.process_course(course, target_unit=args.unit)

if __name__ == "__main__":
    main()
