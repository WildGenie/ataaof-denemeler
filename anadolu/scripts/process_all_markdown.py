#!/usr/bin/env python3
"""
Process all Enriched JSON files and convert them to Markdown.
"""
import os
import json
import sys
import subprocess

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERSLER_FILE = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "anadolu", "scripts", "convert_to_markdown.py")
JSON_BASE_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def find_course_files():
    """Find all course JSON files (Enriched preferred, then Raw)."""
    import glob

    # Find all Enriched and Raw files
    enriched_pattern = os.path.join(JSON_BASE_DIR, "**", "*Enriched.json")
    raw_pattern = os.path.join(JSON_BASE_DIR, "**", "*Raw.json")

    enriched_files = glob.glob(enriched_pattern, recursive=True)
    raw_files = glob.glob(raw_pattern, recursive=True)

    # Map course_name -> filepath
    course_files = {}

    # First process Raw files
    for filepath in raw_files:
        course_name, donem = extract_course_info(filepath)
        if course_name:
            course_files[course_name] = filepath

    # Then overwrite with Enriched files (so Enriched takes precedence)
    for filepath in enriched_files:
        course_name, donem = extract_course_info(filepath)
        if course_name:
            course_files[course_name] = filepath

    return list(course_files.values())

def extract_course_info(filepath):
    """Extract course name and donem from filepath."""
    # Format: .../Donem X/Anadolu - Dönem X - Course Name - Çıkmış Sorular - [Enriched|Raw].json
    parts = filepath.split(os.sep)

    for part in parts:
        if part.startswith("Donem "):
            donem = part.replace("Donem ", "")
            break
    else:
        return None, None

    filename = os.path.basename(filepath)
    # Remove prefix
    name_part = filename.replace("Anadolu - ", "")
    # Remove suffix (handle both Enriched and Raw)
    name_part = name_part.replace(" - Çıkmış Sorular - Enriched.json", "")
    name_part = name_part.replace(" - Çıkmış Sorular - Raw.json", "")

    # Remove "Dönem X - "
    course_name = name_part.split(" - ", 1)[1] if " - " in name_part else name_part

    return course_name, donem

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert all JSON files to Markdown.")
    parser.add_argument("--enrolled", action="store_true", help="Process only enrolled courses")

    args = parser.parse_args()

    # Find all course files
    files_to_process = find_course_files()

    if not files_to_process:
        print("No JSON files found.")
        return

    # Filter by enrollment if requested
    if args.enrolled:
        enrolled_file = os.path.join(PROJECT_ROOT, "anadolu", "enrolled_courses.json")

        if os.path.exists(enrolled_file):
            with open(enrolled_file, 'r', encoding='utf-8') as f:
                enrolled_data = json.load(f)
                enrolled_codes = [c.get("kod") for c in enrolled_data]

            # Load all courses to map names to codes
            with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
                all_courses = json.load(f)

            # Create name to code mapping
            name_to_code = {c.get("CourseName"): c.get("DersKodu") for c in all_courses}

            # Filter files
            filtered_files = []
            for filepath in files_to_process:
                course_name, donem = extract_course_info(filepath)
                if course_name and name_to_code.get(course_name) in enrolled_codes:
                    filtered_files.append(filepath)

            files_to_process = filtered_files
            print(f"Filtered to {len(files_to_process)} enrolled courses.\n")

    print(f"Found {len(files_to_process)} JSON files to convert.\n")

    success_count = 0
    error_count = 0

    for i, filepath in enumerate(files_to_process, 1):
        course_name, donem = extract_course_info(filepath)

        if not course_name or not donem:
            print(f"[{i}/{len(files_to_process)}] ❌ Could not extract info from: {filepath}")
            error_count += 1
            continue

        print(f"[{i}/{len(files_to_process)}] Converting: {course_name} (Dönem {donem})")
        print("-" * 80)

        try:
            result = subprocess.run(
                [sys.executable, SCRIPT_PATH, "--course", course_name, "--donem", donem],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print(f"  ✅ Success\n")
                success_count += 1
            else:
                print(f"  ❌ Error (exit code: {result.returncode})")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                print()
                error_count += 1

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout\n")
            error_count += 1
        except Exception as e:
            print(f"  ❌ Exception: {e}\n")
            error_count += 1

    print("=" * 80)
    print(f"Summary:")
    print(f"  Converted: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(files_to_process)}")

if __name__ == "__main__":
    main()
