#!/usr/bin/env python3
"""
Process exam PDFs for all registered courses.
"""
import os
import json
import sys
import subprocess

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERSLER_FILE = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "anadolu", "scripts", "convert_exams_to_json.py")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process exam PDFs for courses.")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses defined in enrolled_courses.json")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--semester", choices=["guz", "bahar"], help="Filter by semester type: 'guz' (1,3,5,7) or 'bahar' (2,4,6,8)")
    parser.add_argument("--donem", type=int, choices=range(1, 9), metavar="1-8", help="Filter by specific semester number (1-8)")

    args = parser.parse_args()

    # Load all courses
    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        all_courses = json.load(f)

    # Filter out "Yabancı Dil Dersleri" and courses without DersKodu
    courses = [c for c in all_courses if c.get("CourseName") != "Yabancı Dil Dersleri" and c.get("DersKodu")]

    # If --donem filter is provided, apply it
    if args.donem:
        courses = [c for c in courses if c.get("Donem") == str(args.donem)]
        print(f"Filtered to Dönem {args.donem} courses.\n")

    # If --semester filter is provided, apply it
    if args.semester:
        if args.semester == "guz":
            # Fall semester: 1, 3, 5, 7
            courses = [c for c in courses if c.get("Donem") in ["1", "3", "5", "7"]]
            print(f"Filtered to Güz (Fall) semester courses.\n")
        elif args.semester == "bahar":
            # Spring semester: 2, 4, 6, 8
            courses = [c for c in courses if c.get("Donem") in ["2", "4", "6", "8"]]
            print(f"Filtered to Bahar (Spring) semester courses.\n")

    # If --enrolled flag is set, filter to only enrolled courses
    if args.enrolled:
        enrolled_file = os.path.join(PROJECT_ROOT, "anadolu", "enrolled_courses.json")

        if not os.path.exists(enrolled_file):
            print(f"Error: {enrolled_file} not found.")
            print("Please create enrolled_courses.json with your enrolled courses.")
            return

        with open(enrolled_file, 'r', encoding='utf-8') as f:
            enrolled_data = json.load(f)
            enrolled_codes = [c.get("kod") for c in enrolled_data]

        # Filter courses to only enrolled ones
        courses = [c for c in courses if c.get("DersKodu") in enrolled_codes]
        print(f"Found {len(courses)} enrolled courses to process.\n")
    else:
        print(f"Found {len(courses)} courses to process.\n")

    # If --course filter is provided, apply it
    if args.course:
        courses = [c for c in courses if args.course.lower() in c.get("CourseName", "").lower()]
        print(f"Filtered to {len(courses)} courses matching '{args.course}'.\n")

    if not courses:
        print("No courses found to process.")
        return

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, course in enumerate(courses, 1):
        course_name = course.get("CourseName")
        donem = course.get("Donem")

        print(f"[{i}/{len(courses)}] Processing: {course_name} (Dönem {donem})")
        print("-" * 80)

        try:
            # Run convert_exams_to_json.py for this course
            result = subprocess.run(
                [sys.executable, SCRIPT_PATH, "--course", course_name],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout per course
            )

            if result.returncode == 0:
                # Check if any files were processed
                if "Skipping" in result.stdout and "Processing" not in result.stdout:
                    print(f"  ✅ Already processed (skipped)\n")
                    skip_count += 1
                else:
                    print(f"  ✅ Success\n")
                    success_count += 1
            else:
                print(f"  ❌ Error (exit code: {result.returncode})")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                print()
                error_count += 1

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout (skipped)\n")
            error_count += 1
        except Exception as e:
            print(f"  ❌ Exception: {e}\n")
            error_count += 1

    print("=" * 80)
    print(f"Summary:")
    print(f"  Processed: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(courses)}")

if __name__ == "__main__":
    main()
