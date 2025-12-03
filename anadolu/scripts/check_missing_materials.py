#!/usr/bin/env python3
"""
Check for missing materials (summaries or infographics) by comparing Materials.json definitions
against the actual files in the output directory.
"""

import os
import json
import sys
import argparse
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

from libs.anadolu_lib import OUTPUT_DIR, JSON_DIR

# Material Types Configuration
MATERIAL_CONFIG = {
    "summary": {
        "json_type": "CHAPTER_SUMMARY",
        "filename_prefix": "Ünite Özeti - Ünite",
        "report_title": "MISSING SUMMARIES REPORT"
    },
    "infographic": {
        "json_type": "INFOGRAPHIC",
        "filename_prefix": "İnfografik - Ünite",
        "report_title": "MISSING INFOGRAPHICS REPORT"
    }
}

def check_missing_materials(material_type):
    config = MATERIAL_CONFIG[material_type]
    json_type = config["json_type"]
    filename_prefix = config["filename_prefix"]
    report_title = config["report_title"]

    print("=" * 80)
    print(f"Checking for missing {material_type}s...")
    print("=" * 80)

    total_expected = 0
    total_found = 0
    missing_list = []

    # Walk through JSON directory to find Materials.json files
    for root, dirs, files in os.walk(JSON_DIR):
        for filename in files:
            if filename.endswith("- Materials.json"):
                json_path = os.path.join(root, filename)

                # Parse filename to get Dönem and Course Name
                # Format: Anadolu - Dönem X - Course Name - Materials.json
                try:
                    parts = filename.replace("Anadolu - ", "").replace(" - Materials.json", "").split(" - ")
                    if len(parts) >= 2:
                        donem_str = parts[0] # "Dönem X"
                        course_name = " - ".join(parts[1:]) # Handle course names with dashes

                        # Construct path to course output directory
                        # output/Anadolu/Donem X/Course Name/Materyaller
                        course_mat_dir = os.path.join(OUTPUT_DIR, donem_str.replace("Dönem ", "Donem "), course_name, "Materyaller")

                        # Read JSON file
                        with open(json_path, 'r', encoding='utf-8') as f:
                            materials_data = json.load(f)

                        # Find target group
                        for group in materials_data:
                            if group.get("Type") == json_type:
                                for material in group.get("Materials", []):
                                    total_expected += 1

                                    material_id = material.get("MaterialId")
                                    chapter_num = material.get("ChapterNumber")

                                    # Expected filename format
                                    expected_filename = f"{filename_prefix} {chapter_num} - {material_id}.pdf"
                                    expected_path = os.path.join(course_mat_dir, expected_filename)

                                    if os.path.exists(expected_path):
                                        total_found += 1
                                    else:
                                        missing_list.append({
                                            "donem": donem_str,
                                            "course": course_name,
                                            "unit": chapter_num,
                                            "id": material_id,
                                            "expected_file": expected_filename
                                        })
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    print(f"\nTotal {material_type.capitalize()}s Expected: {total_expected}")
    print(f"Total {material_type.capitalize()}s Found:    {total_found}")
    print(f"Total Missing:            {len(missing_list)}")

    if missing_list:
        print("\n" + "=" * 80)
        print(report_title)
        print("=" * 80)

        current_course = ""
        for item in sorted(missing_list, key=lambda x: (x['donem'], x['course'], x['unit'])):
            if item['course'] != current_course:
                print(f"\n📁 {item['donem']} - {item['course']}")
                current_course = item['course']

            print(f"  ❌ Missing: Ünite {item['unit']} (ID: {item['id']})")

def main():
    parser = argparse.ArgumentParser(description="Check for missing materials")
    parser.add_argument("--type", choices=["summary", "infographic"], required=True, help="Type of material to check")
    args = parser.parse_args()

    check_missing_materials(args.type)

if __name__ == "__main__":
    main()
