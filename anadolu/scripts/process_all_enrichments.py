#!/usr/bin/env python3
"""
Process enrichments for all courses (or filtered courses).
"""
import os
import json
import sys
import subprocess

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERSLER_FILE = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "anadolu", "scripts", "enrich_questions.py")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enrich exam questions for courses.")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses")
    parser.add_argument("--course", help="Filter by course name (partial match)")
    parser.add_argument("--semester", choices=["guz", "bahar"], help="Filter by semester type")
    parser.add_argument("--donem", type=int, choices=range(1, 9), metavar="1-8", help="Filter by semester number")
    parser.add_argument("--no-cache", action="store_true", help="Force re-processing")

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

    print(f"Found {len(courses)} courses to enrich.\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, course in enumerate(courses, 1):
        course_name = course.get("CourseName")
        donem = course.get("Donem")

        print(f"[{i}/{len(courses)}] Enriching: {course_name} (Dönem {donem})")
        print("-" * 80)

        try:
            cmd = [sys.executable, SCRIPT_PATH, "--course", course_name, "--donem", donem]
            if args.no_cache:
                cmd.append("--no-cache")

            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                # capture_output=False, # Let output flow to console
                text=True,
                timeout=1800  # 30 minutes timeout per course
            )

            if result.returncode == 0:
                print(f"\n  ✅ Success\n")
                success_count += 1
            else:
                print(f"\n  ❌ Error (exit code: {result.returncode})\n")
                error_count += 1

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout (skipped)\n")
            error_count += 1
        except Exception as e:
            print(f"  ❌ Exception: {e}\n")
            error_count += 1

    print("=" * 80)
    print(f"Summary:")
    print(f"  Enriched: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(courses)}")

if __name__ == "__main__":
    main()
