#!/usr/bin/env python3
"""
Match and copy local infographics from Google Drive to project structure.
Uses Materials.json to match by ChapterNumber and MaterialId.
"""

import os
import json
import shutil
import sys
import re
import unicodedata
from datetime import datetime
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from libs.anadolu_lib import OUTPUT_DIR, JSON_DIR, DOWNLOAD_TRACKER_FILE, clean_filename

# Paths
GOOGLE_DRIVE_BASE = os.getenv('LOCAL_MATERIALS_ROOT')

if not GOOGLE_DRIVE_BASE:
    print("Error: LOCAL_MATERIALS_ROOT not set in .env file")
    sys.exit(1)

# Dönem mapping (Yarıyıl -> Dönem)
YARIVIL_TO_DONEM = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8
}

def load_course_mapping():
    """Load course mapping from config file."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'course_mapping.json')

    if not os.path.exists(config_path):
        print(f"Warning: Course mapping file not found: {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading course mapping: {e}")
        return {}

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

def get_local_infographics(course_mapping):
    """Scan Google Drive for infographic files using course mapping."""
    local_infographics = {}  # {course_name: {chapter_number: local_file_path}}

    for course_name, relative_path in course_mapping.items():
        # Extract Dönem from relative path
        match = re.match(r'([IVX]+)\.\s*Yarıyıl', relative_path)
        if not match:
            continue

        roman_numeral = match.group(1)
        donem = YARIVIL_TO_DONEM.get(roman_numeral)

        if not donem:
            continue

        # Construct path to infographic folder
        infografik_path = os.path.join(GOOGLE_DRIVE_BASE, relative_path, "İnfografik")

        if not os.path.exists(infografik_path) or not os.path.isdir(infografik_path):
            continue

        # Scan PDF files and extract chapter numbers
        pdf_files = [f for f in os.listdir(infografik_path) if f.endswith('.pdf')]

        if not pdf_files:
            continue

        course_infographics = {}
        for filename in pdf_files:
            # Normalize filename for Unicode handling
            filename_normalized = unicodedata.normalize('NFC', filename)

            # Extract chapter number from filename
            # Patterns: "ünite1.pdf", "ünite 1.pdf", "ÜNİTE 1 -...pdf"
            match = re.search(r'[uü]nite\s*(\d+)', filename_normalized, re.IGNORECASE)
            if match:
                chapter_num = int(match.group(1))
                full_path = os.path.join(infografik_path, filename)
                course_infographics[chapter_num] = full_path

        if course_infographics:
            local_infographics[course_name] = {
                'donem': donem,
                'files': course_infographics
            }
            print(f"Found: Dönem {donem} - {course_name} ({len(course_infographics)} files)")

    return local_infographics

def process_course_infographics(course_name, donem, local_files, dry_run=True):
    """Process infographics for a single course."""
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

    # Find INFOGRAPHIC group
    infographic_group = None
    for group in materials_data:
        if group.get("Type") == "INFOGRAPHIC":
            infographic_group = group
            break

    if not infographic_group:
        print(f"  ⚠️  No INFOGRAPHIC group found in materials")
        return 0, 0

    # Create Materyaller directory
    course_mat_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name, "Materyaller")
    if not dry_run and not os.path.exists(course_mat_dir):
        os.makedirs(course_mat_dir)

    tracker = load_tracker()
    copied = 0
    skipped = 0

    for material in infographic_group.get("Materials", []):
        material_id = str(material.get("MaterialId"))
        chapter_number = material.get("ChapterNumber")
        updated_at = material.get("UpdatedAt")

        # Check if we have a local file for this chapter
        if chapter_number not in local_files:
            continue

        local_file_path = local_files[chapter_number]

        # Generate destination filename (same as download_infographics)
        dest_filename = f"İnfografik - Ünite {chapter_number} - {material_id}.pdf"
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
    import argparse

    parser = argparse.ArgumentParser(description="Match and copy local infographics")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying")
    args = parser.parse_args()

    print("=" * 80)
    print("Loading course mapping...")
    print("=" * 80)

    course_mapping = load_course_mapping()

    if not course_mapping:
        print("Error: No course mapping loaded. Cannot proceed.")
        return

    print(f"Loaded {len(course_mapping)} course mappings")

    print("\n" + "=" * 80)
    print("Scanning Google Drive for local infographics...")
    print("=" * 80)

    local_infographics = get_local_infographics(course_mapping)

    if not local_infographics:
        print("No local infographics found in Google Drive.")
        return

    print(f"\nFound {len(local_infographics)} courses with local infographics")

    print("\n" + "=" * 80)
    print("Processing and copying infographics...")
    print("=" * 80)

    total_copied = 0
    total_skipped = 0
    processed_count = 0

    for course_name, data in local_infographics.items():
        donem = data['donem']
        local_files = data['files']

        print(f"\n📁 Dönem {donem} - {course_name}")

        copied, skipped = process_course_infographics(course_name, donem, local_files, dry_run=args.dry_run)
        total_copied += copied
        total_skipped += skipped

        if copied > 0 or skipped > 0:
            processed_count += 1

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Courses with local infographics: {len(local_infographics)}")
    print(f"Courses processed: {processed_count}")
    print(f"Files copied: {total_copied}")
    print(f"Files skipped: {total_skipped}")

    if args.dry_run:
        print("\n⚠️  This was a DRY RUN. Use without --dry-run to actually copy files.")

if __name__ == "__main__":
    main()
