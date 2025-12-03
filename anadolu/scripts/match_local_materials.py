#!/usr/bin/env python3
"""
Match and copy local materials (summaries or infographics) from Google Drive to the project structure.
Uses Materials.json to match files by ChapterNumber and MaterialId.
"""

import os
import json
import shutil
import sys
import re
import unicodedata
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

from libs.anadolu_lib import OUTPUT_DIR, JSON_DIR, DOWNLOAD_TRACKER_FILE, clean_filename

# Dönem mapping (Yarıyıl -> Dönem)
YARIVIL_TO_DONEM = {
    "I": 1, "II": 2, "III": 3, "IV": 4,
    "V": 5, "VI": 6, "VII": 7, "VIII": 8
}

# Configuration
LOCAL_MATERIALS_ROOT = os.getenv("LOCAL_MATERIALS_ROOT")
if not LOCAL_MATERIALS_ROOT:
    print("Warning: LOCAL_MATERIALS_ROOT not set in .env")
    LOCAL_MATERIALS_ROOT = ""

GOOGLE_DRIVE_BASE = LOCAL_MATERIALS_ROOT
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURSE_MAPPING_FILE = os.path.join(PROJECT_ROOT, "config", "course_mapping.json")

# Material Types Configuration
MATERIAL_CONFIG = {
    "summary": {
        "json_type": "CHAPTER_SUMMARY",
        "filename_prefix": "Ünite Özeti - Ünite",
        "folder_names": [
            "Özetler", "Ozetler", "Özetler", "Özetler ",
            "Alınan Ders Notları ve Özetleri", "Kitaplar ve Özetler"
        ],
        "folder_match_mode": "exact_or_normalized"
    },
    "infographic": {
        "json_type": "INFOGRAPHIC",
        "filename_prefix": "İnfografik - Ünite",
        "folder_names": ["infografik"], # keyword to search
        "folder_match_mode": "contains_clean"
    }
}

def load_tracker():
    """Load download tracker."""
    if os.path.exists(DOWNLOAD_TRACKER_FILE):
        try:
            with open(DOWNLOAD_TRACKER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tracker(tracker):
    """Save download tracker."""
    try:
        with open(DOWNLOAD_TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(tracker, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving tracker: {e}")

def load_course_mapping():
    """Load course mapping from config file."""
    if not os.path.exists(COURSE_MAPPING_FILE):
        print(f"Error: Course mapping file not found at {COURSE_MAPPING_FILE}")
        return {}

    try:
        with open(COURSE_MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading course mapping: {e}")
        return {}

def remove_accents(input_str):
    """Remove accents from string (NFKD normalization)."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_material_folder(base_path, config):
    """Find the material folder based on configuration."""
    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        return None

    mode = config["folder_match_mode"]
    target_names = config["folder_names"]

    if mode == "exact_or_normalized":
        for folder_name in target_names:
            # Try exact match
            path = os.path.join(base_path, folder_name)
            if os.path.exists(path) and os.path.isdir(path):
                return path

            # Try NFD normalization
            path = os.path.join(base_path, unicodedata.normalize('NFD', folder_name))
            if os.path.exists(path) and os.path.isdir(path):
                return path

            # Try NFC normalization
            path = os.path.join(base_path, unicodedata.normalize('NFC', folder_name))
            if os.path.exists(path) and os.path.isdir(path):
                return path

    elif mode == "contains_clean":
        # Scan directory for any folder containing keyword (case-insensitive, accent-removed)
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    item_clean = remove_accents(item).lower()
                    for target in target_names:
                        if target in item_clean:
                            return item_path
        except Exception as e:
            print(f"Error scanning directory {base_path}: {e}")

    return None

def get_local_materials(course_mapping, material_type):
    """Scan Google Drive for materials using course mapping."""
    local_materials = {}  # {course_name: {chapter_number: local_file_path}}
    config = MATERIAL_CONFIG[material_type]

    for course_name, relative_path in course_mapping.items():
        # Extract Dönem from relative path
        match = re.match(r'([IVX]+)\.\s*Yarıyıl', relative_path)
        if not match:
            continue

        roman_numeral = match.group(1)
        donem = YARIVIL_TO_DONEM.get(roman_numeral)

        if not donem:
            continue

        # Construct path to material folder
        base_path = os.path.join(GOOGLE_DRIVE_BASE, relative_path)

        material_path = find_material_folder(base_path, config)

        if not material_path:
            # Try finding course with normalized name if not found directly
            # This handles cases where course name in mapping differs by normalization
            # But here we iterate over mapping keys, so relative_path is what we have.
            # The issue might be that relative_path itself is not found?
            # No, relative_path comes from mapping values.
            continue

        # Scan PDF files and extract chapter numbers
        try:
            pdf_files = [f for f in os.listdir(material_path) if f.endswith('.pdf')]
        except Exception as e:
            print(f"Error listing files in {material_path}: {e}")
            continue

        if not pdf_files:
            continue

        course_files = {}
        for filename in pdf_files:
            # Normalize filename for Unicode handling
            filename_normalized = unicodedata.normalize('NFC', filename)

            # Extract chapter number from filename
            # Patterns: "ünite1.pdf", "ünite 1.pdf", "ÜNİTE 1 -...pdf"
            match = re.search(r'[uü]nite\s*(\d+)', filename_normalized, re.IGNORECASE)
            if match:
                chapter_num = int(match.group(1))
                full_path = os.path.join(material_path, filename)
                course_files[chapter_num] = full_path

        if course_files:
            local_materials[course_name] = {
                'donem': donem,
                'files': course_files
            }
            print(f"Found: Dönem {donem} - {course_name} ({len(course_files)} files)")

    return local_materials

def process_course_materials(course_name, donem, local_files, material_type, dry_run=True):
    """Process materials for a single course."""
    config = MATERIAL_CONFIG[material_type]
    json_type = config["json_type"]
    filename_prefix = config["filename_prefix"]

    # Load materials file
    materials_filename = f"Anadolu - Dönem {donem} - {course_name} - Materials.json"
    materials_filepath = os.path.join(JSON_DIR, f"Donem {donem}", materials_filename)

    if not os.path.exists(materials_filepath):
        print(f"  ❌ Materials file not found: {materials_filename}")
        return 0, 0

    try:
        with open(materials_filepath, 'r', encoding='utf-8') as f:
            materials_data = json.load(f)
    except Exception as e:
        print(f"  ❌ Error reading materials file: {e}")
        return 0, 0

    # Find group
    target_group = None
    for group in materials_data:
        if group.get("Type") == json_type:
            target_group = group
            break

    if not target_group:
        print(f"  ⚠️  No {json_type} group found in materials")
        return 0, 0

    # Create Materyaller directory
    course_mat_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name, "Materyaller")
    if not dry_run and not os.path.exists(course_mat_dir):
        os.makedirs(course_mat_dir)

    tracker = load_tracker()
    copied = 0
    skipped = 0

    for material in target_group.get("Materials", []):
        material_id = str(material.get("MaterialId"))
        chapter_number = material.get("ChapterNumber")
        updated_at = material.get("UpdatedAt")

        # Check if we have a local file for this chapter
        if chapter_number not in local_files:
            continue

        local_file_path = local_files[chapter_number]

        # Generate destination filename
        dest_filename = f"{filename_prefix} {chapter_number} - {material_id}.pdf"
        dest_filepath = os.path.join(course_mat_dir, dest_filename)

        # Check if already exists and up to date
        if material_id in tracker:
            tracker_entry = tracker[material_id]
            if tracker_entry.get("UpdatedAt") == updated_at:
                existing_filename = tracker_entry.get("Filename")
                if existing_filename:
                    existing_filepath = os.path.join(course_mat_dir, existing_filename)
                    if os.path.exists(existing_filepath):
                        print(f"  ⏭️  Skipped (already exists): {dest_filename}")
                        skipped += 1
                        continue

        # Copy file
        if dry_run:
            print(f"  📋 Would copy: Ünite {chapter_number} -> {dest_filename}")
        else:
            try:
                # Use copy() instead of copy2() to avoid copying readonly permissions
                shutil.copy(local_file_path, dest_filepath)

                # Ensure the file is writable
                os.chmod(dest_filepath, 0o644)

                print(f"  ✅ Copied: Ünite {chapter_number} -> {dest_filename}")

                # Update tracker
                tracker[material_id] = {
                    "UpdatedAt": updated_at,
                    "DownloadedAt": datetime.now().isoformat(),
                    "Filename": dest_filename,
                    "Course": course_name,
                    "Source": "local"
                }
                copied += 1
            except Exception as e:
                print(f"  ❌ Error copying {dest_filename}: {e}")

    if not dry_run and copied > 0:
        save_tracker(tracker)

    return copied, skipped

def main():
    parser = argparse.ArgumentParser(description="Match and copy local materials from Google Drive")
    parser.add_argument("--type", choices=["summary", "infographic"], required=True, help="Type of material to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying")
    args = parser.parse_args()

    print("=" * 80)
    print(f"Loading course mapping for {args.type}...")
    print("=" * 80)

    course_mapping = load_course_mapping()

    if not course_mapping:
        print("Error: No course mapping loaded. Cannot proceed.")
        return

    print(f"Loaded {len(course_mapping)} course mappings")

    print("\n" + "=" * 80)
    print(f"Scanning Google Drive for local {args.type}s...")
    print("=" * 80)

    local_materials = get_local_materials(course_mapping, args.type)

    if not local_materials:
        print(f"No local {args.type}s found in Google Drive.")
        return

    print(f"\nFound {len(local_materials)} courses with local {args.type}s")

    print("\n" + "=" * 80)
    print(f"Processing and copying {args.type}s...")
    print("=" * 80)

    total_copied = 0
    total_skipped = 0
    processed_count = 0

    for course_name, data in local_materials.items():
        donem = data['donem']
        local_files = data['files']

        print(f"\n📁 Dönem {donem} - {course_name}")

        copied, skipped = process_course_materials(course_name, donem, local_files, args.type, dry_run=args.dry_run)
        total_copied += copied
        total_skipped += skipped

        if copied > 0 or skipped > 0:
            processed_count += 1

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Courses with local {args.type}s: {len(local_materials)}")
    print(f"Courses processed: {processed_count}")
    print(f"Files copied: {total_copied}")
    print(f"Files skipped: {total_skipped}")

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN. Use without --dry-run to actually copy files.")

if __name__ == "__main__":
    main()
