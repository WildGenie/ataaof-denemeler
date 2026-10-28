import json
import os
import sys
import requests

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import (
    setup_directories,
    DERSLER_FILE,
    OUTPUT_DIR
)

BASE_URL = "https://oys.ataaof.edu.tr/ktpcik/{ders_id}.pdf"

def get_safe_course_name(name):
    # Remove characters that might be invalid in filenames
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()

def fetch_booklet(course, target_dir):
    ders_id = course.get("DersId")
    course_name = course.get("CourseName")
    donem = course.get("Donem")

    url = BASE_URL.format(ders_id=ders_id)
    safe_course_name = get_safe_course_name(course_name)

    # New filename: Donem X - Course Name - 2025-2026 Final Soruları.pdf
    filename = f"Donem {donem} - {safe_course_name} - 2025-2026 Final Soruları.pdf"
    filepath = os.path.join(target_dir, filename)

    if os.path.exists(filepath):
        if os.path.getsize(filepath) > 0:
            print(f"Skipping {course_name} (already exists).")
            return

    print(f"Downloading booklet for {course_name} ({ders_id})...")
    try:
        response = requests.get(url, timeout=60)
        # Check content type and length
        if response.status_code == 200 and "pdf" in response.headers.get("Content-Type", "").lower():
            if len(response.content) < 1000: # Some empty PDFs are small
                 print(f"  Warning: Small PDF ({len(response.content)} bytes) for {course_name}.")

            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"  Saved to {filename}")
        else:
            print(f"  Failed: HTTP {response.status_code} or not PDF.")
    except Exception as e:
        print(f"  Error: {e}")

def main():
    setup_directories()

    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    # Create a single directory for all books
    kitaplar_dir = os.path.join(OUTPUT_DIR, "Kitaplar")
    os.makedirs(kitaplar_dir, exist_ok=True)

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # Filter for odd semesters (1, 3, 5, 7)
    odd_semester_courses = [c for c in courses if c.get("Donem") and int(c.get("Donem")) % 2 != 0]

    print(f"Found {len(odd_semester_courses)} odd-semester courses out of {len(courses)}.")

    for course in odd_semester_courses:
        fetch_booklet(course, kitaplar_dir)

if __name__ == "__main__":
    main()
