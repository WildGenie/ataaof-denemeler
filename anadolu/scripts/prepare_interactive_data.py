#!/usr/bin/env python3
"""
Prepare data for interaktif.html
Scans output/Anadolu/json/Donem X/ directories.
Generates output/Anadolu/sorular/dersler.json index file.
Does NOT modify or copy question JSON files.
"""

import os
import json
import urllib.parse

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
TARGET_DIR = os.path.join(OUTPUT_DIR, "sorular")

def main():
    print(f"Generating index in {TARGET_DIR}...")

    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    # Structure for dersler.json
    courses_by_semester = {}

    # Scan directories
    if not os.path.exists(JSON_DIR):
        print(f"Error: JSON directory not found at {JSON_DIR}")
        return

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        try:
            donem_num = int(donem_dir.split(" ")[1])
        except:
            continue

        if donem_num not in courses_by_semester:
            courses_by_semester[donem_num] = []

        print(f"Processing {donem_dir}...")

        # Group files by course name
        course_files = {}
        for filename in os.listdir(donem_path):
            if not filename.endswith(".json"):
                continue

            # Expected format: Anadolu - Dönem X - Ders Adı - Suffix.json
            parts = filename.split(" - ")
            if len(parts) < 4:
                continue

            course_name = parts[2]

            if course_name not in course_files:
                course_files[course_name] = []

            course_files[course_name].append(filename)

        # Process each course
        for course_name, files in course_files.items():
            sources = []

            # 1. Exams (Enriched or Raw)
            exam_files = [f for f in files if "Çıkmış Sorular" in f]
            enriched_exam = next((f for f in exam_files if "Enriched" in f), None)
            raw_exam = next((f for f in exam_files if "Raw" in f), None)

            # Prefer enriched, fallback to raw
            if enriched_exam:
                sources.append({
                    "name": "Çıkmış Sorular (AI)",
                    "url": f"json/{donem_dir}/{enriched_exam}"
                })
            elif raw_exam:
                sources.append({
                    "name": "Çıkmış Sorular",
                    "url": f"json/{donem_dir}/{raw_exam}"
                })

            # 2. Practice Questions
            # Prefer processed over raw if both exist (though usually we only have one or the other in final output?)
            # Actually, we usually have "Alıştırma Soruları.json" and "Alıştırma Soruları - Raw.json"
            # We prefer the non-raw one if available.
            practice_file = next((f for f in files if "Alıştırma Soruları.json" in f), None)
            if not practice_file:
                 practice_file = next((f for f in files if "Alıştırma Soruları - Raw.json" in f), None)

            if practice_file:
                sources.append({
                    "name": "Alıştırma Soruları",
                    "url": f"json/{donem_dir}/{practice_file}"
                })

            # 3. Learn Questions
            learn_file = next((f for f in files if "Sorularla Ogrenelim.json" in f), None)
            if not learn_file:
                learn_file = next((f for f in files if "Sorularla Ogrenelim - Raw.json" in f), None)

            if learn_file:
                sources.append({
                    "name": "Sorularla Öğrenelim",
                    "url": f"json/{donem_dir}/{learn_file}"
                })

            if not sources:
                continue

            courses_by_semester[donem_num].append({
                "dersAdi": course_name,
                "sources": sources
            })

    # Generate dersler.json
    output_data = []
    for donem in sorted(courses_by_semester.keys()):
        output_data.append({
            "donem": donem,
            "dersler": sorted(courses_by_semester[donem], key=lambda x: x["dersAdi"])
        })

    with open(os.path.join(TARGET_DIR, "dersler.json"), "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print(f"Successfully generated index for {len(output_data)} semesters.")

if __name__ == "__main__":
    main()
