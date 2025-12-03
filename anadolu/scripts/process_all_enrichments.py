#!/usr/bin/env python3
"""
Process enrichments for all courses (or filtered courses).
"""
import os
import json
import sys
import subprocess
import argparse
import concurrent.futures
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERSLER_FILE = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "anadolu", "scripts", "enrich_questions.py")

def process_course(course_info):
    """
    Process a single course.
    Returns (success, skipped, error_msg)
    """
    course_name = course_info.get("CourseName")
    donem = course_info.get("Donem")
    no_cache = course_info.get("no_cache", False)

    print(f"Starting: {course_name} (Dönem {donem})")

    try:
        cmd = [sys.executable, SCRIPT_PATH, "--course", course_name, "--donem", donem]
        if no_cache:
            cmd.append("--no-cache")

        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True, # Capture output to avoid interleaving in parallel
            text=True,
            timeout=1800  # 30 minutes timeout per course
        )

        if result.returncode == 0:
            # Check output to see if it was skipped or actually processed
            if "Already enriched" in result.stdout:
                print(f"  ⏭️  Skipped (Already Done): {course_name}")
                return (False, True, None)
            else:
                print(f"  ✅ Completed: {course_name}")
                # Print relevant output for user visibility
                # We filter for lines starting with "  " to show progress/stats
                for line in result.stdout.splitlines():
                    if "Enriched" in line or "Saved" in line:
                        print(f"     [{course_name}] {line.strip()}")
                return (True, False, None)
        else:
            print(f"  ❌ Error: {course_name} (Exit Code: {result.returncode})")
            print(f"     [{course_name}] Stderr: {result.stderr[:200]}...")
            return (False, False, f"Exit code {result.returncode}")

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout: {course_name}")
        return (False, False, "Timeout")
    except Exception as e:
        print(f"  ❌ Exception: {course_name} - {e}")
        return (False, False, str(e))

def main():
    parser = argparse.ArgumentParser(description="Enrich exam questions for courses.")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--semester", choices=["guz", "bahar"], help="Filter by semester type")
    parser.add_argument("--donem", type=int, choices=range(1, 9), metavar="1-8", help="Filter by semester number")
    parser.add_argument("--no-cache", action="store_true", help="Force re-processing")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers")

    args = parser.parse_args()

    # Load all courses
    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        all_courses = json.load(f)

    # Filter courses
    courses = [c for c in all_courses if c.get("CourseName") != "Yabancı Dil Dersleri" and c.get("DersKodu")]

    if args.donem:
        courses = [c for c in courses if c.get("Donem") == str(args.donem)]
        print(f"Filtered to Dönem {args.donem} courses.\n")

    if args.semester:
        if args.semester == "guz":
            courses = [c for c in courses if c.get("Donem") in ["1", "3", "5", "7"]]
            print(f"Filtered to Güz (Fall) semester courses.\n")
        elif args.semester == "bahar":
            courses = [c for c in courses if c.get("Donem") in ["2", "4", "6", "8"]]
            print(f"Filtered to Bahar (Spring) semester courses.\n")

    if args.enrolled:
        enrolled_file = os.path.join(PROJECT_ROOT, "anadolu", "enrolled_courses.json")

        if not os.path.exists(enrolled_file):
            print(f"Error: {enrolled_file} not found.")
            return

        with open(enrolled_file, 'r', encoding='utf-8') as f:
            enrolled_data = json.load(f)
            enrolled_codes = [c.get("kod") for c in enrolled_data]

        courses = [c for c in courses if c.get("DersKodu") in enrolled_codes]
        print(f"Filtered to enrolled courses.\n")

    if args.course:
        courses = [c for c in courses if args.course.lower() in c.get("CourseName", "").lower()]
        print(f"Filtered to courses matching '{args.course}'.\n")

    if not courses:
        print("No courses found to process.")
        return

    print(f"Found {len(courses)} courses to enrich.")
    print(f"Processing with {args.workers} workers...\n")

    # Prepare course info objects
    course_infos = []
    for c in courses:
        info = c.copy()
        info['no_cache'] = args.no_cache
        course_infos.append(info)

    success_count = 0
    skip_count = 0
    error_count = 0

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_course = {executor.submit(process_course, info): info for info in course_infos}

        for future in concurrent.futures.as_completed(future_to_course):
            course_info = future_to_course[future]
            try:
                success, skipped, error = future.result()
                if success:
                    success_count += 1
                elif skipped:
                    skip_count += 1
                else:
                    error_count += 1
            except Exception as exc:
                print(f"Generated an exception: {exc}")
                error_count += 1

    duration = time.time() - start_time

    print("=" * 80)
    print(f"Summary:")
    print(f"  Enriched: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(courses)}")
    print(f"  Time: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
