import json
import os
import sys
import requests

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import (
    setup_directories,
    DERSLER_FILE,
    PDF_DIR
)

BASE_URL = "https://oys.ataaof.edu.tr/ktpcik/{ders_id}.pdf"

def fetch_booklet(course):
    ders_id = course.get("DersId")
    course_name = course.get("CourseName")
    donem = course.get("Donem")

    url = BASE_URL.format(ders_id=ders_id)
    safe_course_name = "".join([c for c in course_name if c.isalnum() or c in (' ', '-', '_')]).strip()
    filename = f"{donem} - {safe_course_name} - 2025-2026 Ara Sınav (Vize) Soruları - ATA-AÖF.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    if os.path.exists(filepath):
        print(f"Skipping {course_name} (already exists).")
        return

    print(f"Downloading booklet for {course_name} ({ders_id})...")
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200 and "pdf" in response.headers.get("Content-Type", "").lower():
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

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses.")

    for course in courses:
        fetch_booklet(course)

if __name__ == "__main__":
    main()
