#!/usr/bin/env python3
"""
Reverse matching: Find all files in 'Çıkmış Sorular' folders and check if they match any target files.
"""

import os
import json
import re
import unicodedata
from dotenv import load_dotenv

load_dotenv()

def normalize_name(name):
    """Normalize unicode characters to NFC form and lowercase."""
    return unicodedata.normalize('NFC', name).lower().replace(" ", "")

def turkish_to_ascii(text):
    """Convert Turkish characters to ASCII equivalents."""
    turkish_map = {
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'I': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u'
    }
    for turkish_char, ascii_char in turkish_map.items():
        text = text.replace(turkish_char, ascii_char)
    return text

def extract_year_and_type(filename):
    """Extract year range and exam type from filename."""
    # Normalize Unicode first!
    filename_normalized = unicodedata.normalize('NFC', filename)
    # Convert Turkish chars to ASCII
    filename_ascii = turkish_to_ascii(filename_normalized)
    # Remove spaces and lowercase
    filename_clean = filename_ascii.lower().replace(" ", "")

    # Extract year range
    # Matches 20xx-20xx or 20xx/20xx (just in case)
    year_match = re.search(r'20\d{2}-20\d{2}', filename_clean)
    year_range = year_match.group(0) if year_match else None

    # Extract single year (for Yaz Okulu)
    # Look for 20xx that isn't part of a range
    # Since we removed spaces, we need to be careful not to match the first part of a range as a single year if the range check failed?
    # Actually, if year_match found something, we might want to exclude it.
    # But let's stick to simple regex.
    single_year_match = re.search(r'20\d{2}(?!-)', filename_clean)
    single_year = single_year_match.group(0) if single_year_match else None

    # If we found a range, the single year might be one of the years in the range.
    # Usually we want single year only if no range, or if it's distinct.
    # But for now let's keep logic similar to before.

    # Determine exam type - check space-less patterns
    exam_type = None
    if 'donemsonu' in filename_clean or 'final' in filename_clean:
        exam_type = 'Dönem Sonu'
    elif 'arasinav' in filename_clean or 'vize' in filename_clean or 'baharara' in filename_clean or 'guzara' in filename_clean:
        exam_type = 'Ara Sınav'
    elif 'yazokulu' in filename_clean:
        exam_type = 'Yaz Okulu'
    elif 'tekders' in filename_clean:
        exam_type = 'Tek Ders'
    elif 'ucders' in filename_clean:
        exam_type = 'Üç Ders'

    return year_range, single_year, exam_type

def main():
    source_dir = os.getenv("LOCAL_MATERIALS_ROOT")
    if not source_dir or not os.path.exists(source_dir):
        print(f"Error: Source directory not found: {source_dir}")
        return

    # Load course mapping
    # Load course mapping
    with open("config/course_mapping.json", 'r', encoding='utf-8') as f:
        course_mapping = json.load(f)

    # Load Materials.json files to get expected targets
    expected_files = {}  # {course_name: [list of expected filenames]}

    json_dir = "output/Anadolu/json"
    for root, dirs, files in os.walk(json_dir):
        for file in files:
            if file.endswith("Materials.json"):
                materials_path = os.path.join(root, file)
                parts = file.split(" - ")
                if len(parts) >= 3:
                    course_name = parts[2]

                    try:
                        with open(materials_path, 'r', encoding='utf-8') as f:
                            materials_data = json.load(f)

                        if course_name not in expected_files:
                            expected_files[course_name] = []

                        for group in materials_data:
                            if group.get("Type", "").startswith("PAST_EXAMS"):
                                for material in group.get("Materials", []):
                                    name = material.get("Name", "Unknown")
                                    description = material.get("Description", "")
                                    material_id = str(material.get("MaterialId"))

                                    if description and description != name:
                                        filename_base = f"{name} - {description}"
                                    else:
                                        filename_base = f"{name} - {material_id}"

                                    expected_files[course_name].append(filename_base + ".pdf")
                    except Exception as e:
                        print(f"Error reading {file}: {e}")

    # Now scan all "Çıkmış Sorular" folders
    reverse_matches = []
    potential_matches = []

    for course_name, rel_path in course_mapping.items():
        course_path = os.path.join(source_dir, rel_path)
        cikmis_sorular_path = os.path.join(course_path, "Çıkmış Sorular")

        if not os.path.exists(cikmis_sorular_path):
            continue

        print(f"Scanning: {course_name}")

        for root, dirs, files in os.walk(cikmis_sorular_path):
            for file in files:
                if file.startswith(".") or not file.lower().endswith('.pdf'):
                    continue

                full_path = os.path.join(root, file)
                rel_to_cikmis = os.path.relpath(full_path, cikmis_sorular_path)

                # Extract info from filename
                year_range, single_year, exam_type = extract_year_and_type(file)

                # Check if this file is in expected list
                found_in_expected = False
                matched_target = None

                if course_name in expected_files:
                    for expected_file in expected_files[course_name]:
                        # Normalize and compare
                        if normalize_name(file) == normalize_name(expected_file):
                            found_in_expected = True
                            matched_target = expected_file
                            break

                        # Check if expected file contains year and type info
                        exp_year, exp_single, exp_type = extract_year_and_type(expected_file)

                        if exam_type and exp_type and exam_type == exp_type:
                            if year_range and exp_year and year_range == exp_year:
                                potential_matches.append({
                                    "Course": course_name,
                                    "SourceFile": file,
                                    "SourcePath": rel_to_cikmis,
                                    "PotentialTarget": expected_file,
                                    "Reason": f"Same type ({exam_type}) and year ({year_range})"
                                })
                            elif single_year and exp_year:
                                # Check if single year matches end of range
                                if single_year in exp_year:
                                    potential_matches.append({
                                        "Course": course_name,
                                        "SourceFile": file,
                                        "SourcePath": rel_to_cikmis,
                                        "PotentialTarget": expected_file,
                                        "Reason": f"Same type ({exam_type}) and year match ({single_year} in {exp_year})"
                                    })

                if found_in_expected:
                    reverse_matches.append({
                        "Course": course_name,
                        "SourceFile": file,
                        "SourcePath": rel_to_cikmis,
                        "MatchedTarget": matched_target,
                        "Status": "Exact Match"
                    })
                else:
                    # This is a file we have but not expecting
                    reverse_matches.append({
                        "Course": course_name,
                        "SourceFile": file,
                        "SourcePath": rel_to_cikmis,
                        "YearRange": year_range,
                        "SingleYear": single_year,
                        "ExamType": exam_type,
                        "Status": "Not in expected list"
                    })

    # Save results
    # Save reports to reports/ directory
    os.makedirs("reports", exist_ok=True)

    with open("reports/reverse_match_report.json", "w", encoding="utf-8") as f:
        json.dump(reverse_matches, f, ensure_ascii=False, indent=2)
    print("✅ Reverse match report saved to reports/reverse_match_report.json")

    with open("reports/potential_matches_report.json", "w", encoding="utf-8") as f:
        json.dump(potential_matches, f, ensure_ascii=False, indent=2)
    print("✅ Potential matches saved to reports/potential_matches_report.json")
    print(f"\nTotal files in Çıkmış Sorular folders: {len(reverse_matches)}")
    print(f"Potential new matches found: {len(potential_matches)}")

if __name__ == "__main__":
    main()
