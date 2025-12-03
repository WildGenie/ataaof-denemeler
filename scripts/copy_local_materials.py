import os
import json
import shutil
import argparse
import sys
import difflib
from difflib import SequenceMatcher

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_lib import OUTPUT_DIR, JSON_DIR, DOWNLOAD_TRACKER_FILE, clean_filename

import unicodedata
import re

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
    year_match = re.search(r'20\d{2}-20\d{2}', filename_clean)
    year_range = year_match.group(0) if year_match else None

    # Extract single year (for Yaz Okulu)
    single_year_match = re.search(r'20\d{2}(?!-)', filename_clean)
    single_year = single_year_match.group(0) if single_year_match else None

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

def normalize_name(name):
    """Normalize unicode characters to NFC form and lowercase."""
    return unicodedata.normalize('NFC', name).lower().replace(" ", "")

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def index_source_files(source_dir):
    """
    Recursively index all files in the source directory.
    Returns a dict: { normalized_filename: (full_path, original_filename) }
    """
    index = {}
    print(f"Indexing source directory: {source_dir}...")
    count = 0
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.startswith("."): continue

            # Normalize the filename for key
            norm_name = normalize_name(file)
            full_path = os.path.join(root, file)

            # Store full path and original filename
            # Note: If multiple files normalize to the same name, only the last one will be stored.
            index[norm_name] = (full_path, file)
            count += 1

    print(f"Indexed {count} files.")
    return index

def find_file_in_index(file_index, target_name, threshold=0.85):
    target_name_norm = normalize_name(target_name)

    # Exact match on normalized name
    if target_name_norm in file_index:
        # Return the first one found
        return file_index[target_name_norm][0], 1.0

    # Fuzzy match against keys
    # This is still somewhat expensive if keys are many, but better than walking IO
    matches = difflib.get_close_matches(target_name_norm, file_index.keys(), n=1, cutoff=threshold)

    if matches:
        best_key = matches[0]
        ratio = SequenceMatcher(None, target_name_norm, best_key).ratio()
        return file_index[best_key][0], ratio

    return None, 0

def load_tracker():
    if os.path.exists(DOWNLOAD_TRACKER_FILE):
        try:
            with open(DOWNLOAD_TRACKER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tracker(tracker):
    with open(DOWNLOAD_TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracker, f, indent=4, ensure_ascii=False)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Copy local materials to project structure")
    parser.add_argument("--source-dir", help="Source directory containing materials (defaults to LOCAL_MATERIALS_ROOT in .env)")
    parser.add_argument("--report-only", action="store_true", help="Generate a match report without copying")
    parser.add_argument("--exams-only", action="store_true", help="Only copy past exams")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without copying")
    parser.add_argument("--fuzzy-threshold", type=float, default=1.0, help="Score threshold for fuzzy matches (0.0-1.0). Default 1.0 (Exact only)")
    args = parser.parse_args()

    source_dir = args.source_dir or os.getenv("LOCAL_MATERIALS_ROOT")

    if not source_dir:
        print("Error: Source directory must be provided via --source-dir or LOCAL_MATERIALS_ROOT env var.")
        return

    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return

    tracker = load_tracker()

    # Load course mapping
    mapping_file = "config/course_mapping.json"
    if not os.path.exists(mapping_file):
        print(f"Mapping file not found: {mapping_file}. Please run scripts/map_courses.py first.")
        return

    with open(mapping_file, 'r', encoding='utf-8') as f:
        course_mapping = json.load(f)

    exact_matches = []
    partial_matches = []
    unmatched_targets = []

    unmatched_report = []
    source_structure = []
    matched_source_files = set()

    IGNORE_TERMS = [
        "çıkmış sınav soruları",
        "çıkmış sorular",
        "aöf",
        "yaz okulu",
        "ders notları",
        "özet",
        "final",
        "bütünleme",
        "vize",
        "bahar",
        "güz",
        "- a",
        "- b",
        "- c"
    ]

    def clean_name(name):
        n = normalize_name(name)
        # Remove extra spaces
        n = re.sub(r'\s+', '', n)
        for term in IGNORE_TERMS:
            n = n.replace(normalize_name(term), "")
        return n

    # Find all Materials.json files
    for root, dirs, files in os.walk(JSON_DIR):
        for file in files:
            if file.endswith("Materials.json"):
                materials_path = os.path.join(root, file)

                # Extract course info from filename or path
                parts = file.split(" - ")
                if len(parts) >= 3:
                    donem_str = parts[1]
                    course_name = parts[2]
                else:
                    continue

                # Get folder from mapping
                matched_folder_rel = course_mapping.get(course_name)

                if matched_folder_rel:
                    matched_folder = os.path.join(source_dir, matched_folder_rel)
                    if os.path.exists(matched_folder):
                        print(f"Processing {course_name}...")
                        file_index = index_source_files(matched_folder)
                    else:
                        print(f"Processing {course_name} -> Mapped folder not found: {matched_folder_rel}")
                        continue
                else:
                    continue

                try:
                    with open(materials_path, 'r', encoding='utf-8') as f:
                        materials_data = json.load(f)
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    continue

                donem_folder = donem_str.replace("Dönem", "Donem")
                target_dir = os.path.join(OUTPUT_DIR, donem_folder, course_name, "Materyaller")

                if not args.dry_run and not args.report_only and not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                for group in materials_data:
                    if args.exams_only and not group.get("Type", "").startswith("PAST_EXAMS"):
                        continue

                    for material in group.get("Materials", []):
                        material_id = str(material.get("MaterialId"))
                        name = material.get("Name", "Unknown").replace("/", "-").replace(":", "-")
                        description = material.get("Description")
                        if description is None:
                            description = ""
                        description = description.replace("/", "-").replace(":", "-")

                        if description and description != name:
                            filename_base = f"{name} - {description}"
                            search_name = f"{name} - {description}"
                        else:
                            filename_base = name
                            search_name = name

                        if material_id not in filename_base:
                            filename_base = f"{filename_base} - {material_id}"

                        # Clean filename
                        filename_base = clean_filename(filename_base)

                        file_ext = ".pdf"
                        if material.get("FileExtension") == "application/pdf":
                            file_ext = ".pdf"
                        elif material.get("FileExtension") == "application/epub+zip":
                            file_ext = ".epub"

                        target_filename = f"{filename_base}{file_ext}"
                        target_filepath = os.path.join(target_dir, target_filename)

                        exists = os.path.exists(target_filepath)
                        if exists and not args.report_only:
                            continue

                        candidates = [f"{search_name}{file_ext}"]

                        found_path = None
                        match_score = 0.0
                        match_type = "None"

                        # Strategy 1: Exact Match (Normalized)
                        for candidate in candidates:
                            candidate_norm = normalize_name(candidate)
                            if candidate_norm in file_index:
                                found_path = file_index[candidate_norm][0]
                                match_score = 1.0
                                match_type = "Exact"
                                break

                        # Strategy 2: Cleaned Exact Match (Ignore Terms)
                        if not found_path:
                            search_key_clean = clean_name(f"{search_name}{file_ext}")
                            for norm_name, (full_path, orig_name) in file_index.items():
                                if clean_name(orig_name) == search_key_clean:
                                    found_path = full_path
                                    match_score = 0.95
                                    match_type = "CleanedExact"
                                    break

                        # Strategy 3: Substring Match
                        if not found_path:
                            search_key_ext = normalize_name(f"{search_name}{file_ext}")

                            for norm_name, (full_path, orig_name) in file_index.items():
                                if search_key_ext in norm_name:
                                    found_path = full_path
                                    match_score = 0.90
                                    match_type = "Substring"
                                    break

                        # Strategy 5: ID Match
                        if not found_path:
                            # Target filename format: "Name - ID.pdf" or "Name - Description.pdf"
                            # We extracted material_id earlier.
                            if material_id and material_id != "None":
                                for norm_name, (full_path, orig_name) in file_index.items():
                                    if material_id in orig_name:
                                        found_path = full_path
                                        match_score = 1.0
                                        match_type = "IDMatch"
                                        break

                        # Strategy 6: Year + Type Match (Advanced)
                        if not found_path:
                            # Extract info from target filename
                            target_year_range, target_single_year, target_exam_type = extract_year_and_type(search_name)

                            if target_exam_type:
                                for norm_name, (full_path, orig_name) in file_index.items():
                                    # Extract info from source filename
                                    source_year_range, source_single_year, source_exam_type = extract_year_and_type(orig_name)

                                    # Check Type
                                    if target_exam_type != source_exam_type:
                                        continue

                                    # Check Year
                                    year_match = False

                                    if target_year_range and source_year_range:
                                        if target_year_range == source_year_range:
                                            year_match = True
                                    elif target_single_year and source_year_range:
                                        # Check if single year matches end of range (common for Yaz Okulu)
                                        if target_single_year in source_year_range:
                                            year_match = True
                                    elif target_year_range and source_single_year:
                                         if source_single_year in target_year_range:
                                             year_match = True
                                    elif target_single_year and source_single_year:
                                        if target_single_year == source_single_year:
                                            year_match = True

                                    if year_match:
                                        found_path = full_path
                                        match_score = 0.95
                                        match_type = "YearTypeMatch"
                                        break

                        # Strategy 4: Fuzzy Match (Last resort)
                        if not found_path:
                            search_key = normalize_name(f"{search_name}{file_ext}")
                            matches = difflib.get_close_matches(search_key, file_index.keys(), n=1, cutoff=0.6)

                            if matches:
                                best_key = matches[0]
                                score = difflib.SequenceMatcher(None, search_key, best_key).ratio()

                                if score >= args.fuzzy_threshold:
                                    found_path = file_index[best_key][0]
                                    match_score = score
                                    match_type = "Fuzzy"

                        subfolder = ""
                        if found_path:
                            try:
                                rel_path = os.path.relpath(found_path, matched_folder)
                                subfolder = os.path.dirname(rel_path)
                            except ValueError:
                                subfolder = "External"

                        match_entry = {
                            "Course": course_name,
                            "TargetFile": target_filename,
                            "FoundFile": os.path.basename(found_path) if found_path else None,
                            "Subfolder": subfolder,
                            "Score": round(match_score, 2),
                            "Type": match_type,
                            "Exists": exists
                        }

                        if found_path:
                            matched_source_files.add(found_path)
                            if match_type in ["Exact", "IDMatch"]:
                                exact_matches.append(match_entry)
                                print(f"  [{match_type}] {target_filename} -> {subfolder}/{os.path.basename(found_path)}")
                            else:
                                partial_matches.append(match_entry)
                                print(f"  [{match_type}] {target_filename} -> {subfolder}/{os.path.basename(found_path)} ({match_score:.2f})")

                            if not args.dry_run and not args.report_only:
                                try:
                                    shutil.copyfile(found_path, target_filepath)
                                    tracker[material_id] = {
                                        "UpdatedAt": material.get("UpdatedAt"),
                                        "DownloadedAt": "2023-01-01T00:00:00",
                                        "Filename": target_filename,
                                        "Course": course_name,
                                        "Source": "Local Copy"
                                    }
                                except Exception as e:
                                    print(f"  [Error] Copy failed: {e}")
                        else:
                            unmatched_targets.append(match_entry)
                            # print(f"  [Missing] {target_filename}")

                # After processing course, check for unmatched source files
                if args.report_only:
                    for norm_name, (full_path, orig_name) in file_index.items():
                        # Populate source_structure (only Yarıyıl folders)
                        if "Yarıyıl" in full_path or "Yariyil" in full_path:
                             source_structure.append({
                                 "Course": course_name,
                                 "File": orig_name,
                                 "Path": os.path.relpath(full_path, source_dir)
                             })

                        # Filter for source_unmatched_report: Only exams
                        if full_path not in matched_source_files:
                            if "Çıkmış Sorular" in full_path or "Çıkmış Sorular" in full_path:
                                unmatched_report.append({
                                    "Course": course_name,
                                    "UnmatchedFile": orig_name,
                                    "Path": os.path.relpath(full_path, source_dir)
                                })

    if args.report_only:
        # Save reports to reports/ directory
        os.makedirs("reports", exist_ok=True)

        with open("reports/report_exact_matches.json", "w", encoding="utf-8") as f:
            json.dump(exact_matches, f, ensure_ascii=False, indent=2)
        print("Exact matches saved to reports/report_exact_matches.json")

        with open("reports/report_partial_matches.json", "w", encoding="utf-8") as f:
            json.dump(partial_matches, f, ensure_ascii=False, indent=2)
        print("Partial matches saved to reports/report_partial_matches.json")

        with open("reports/report_unmatched_targets.json", "w", encoding="utf-8") as f:
            json.dump(unmatched_targets, f, ensure_ascii=False, indent=2)
        print("Unmatched targets saved to reports/report_unmatched_targets.json")

        with open("reports/source_unmatched_report.json", "w", encoding="utf-8") as f:
            json.dump(unmatched_report, f, ensure_ascii=False, indent=2)
        print("Unmatched source files report saved to reports/source_unmatched_report.json")

        with open("reports/source_structure.json", "w", encoding="utf-8") as f:
            json.dump(source_structure, f, ensure_ascii=False, indent=2)
        print("Source structure report saved to reports/source_structure.json")

    elif not args.dry_run:
        save_tracker(tracker)
        print("Tracker updated.")

if __name__ == "__main__":
    main()
