import unittest
import os
import json
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions to test
# Note: We need to make sure convert_exams_to_json is importable without running main
from anadolu.scripts.convert_exams_to_json import (
    find_materials_json,
    find_file_by_id,
    clean_filename,
    OUTPUT_DIR
)

class TestExamConversionLogic(unittest.TestCase):
    def setUp(self):
        self.course_name = "Görsel Estetik"

    def test_find_materials_json(self):
        """Test if Materials.json can be found."""
        path = find_materials_json(self.course_name)
        print(f"\nFound Materials.json: {path}")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

    def test_exam_identification_and_file_location(self):
        """
        Test parsing Materials.json, identifying exams, and locating files.
        """
        materials_json_path = find_materials_json(self.course_name)
        if not materials_json_path:
            self.fail("Materials.json not found")

        with open(materials_json_path, 'r', encoding='utf-8') as f:
            materials_data = json.load(f)

        exam_records = []
        for group in materials_data:
            materials = group.get("Materials", [])
            for item in materials:
                if "PAST_EXAMS_" in item.get("Type", ""):
                    exam_records.append(item)

        print(f"\nIdentified {len(exam_records)} exam records in JSON.")
        self.assertGreater(len(exam_records), 0)

        found_files_count = 0
        for item in exam_records:
            material_id = item.get("MaterialId")
            name = item.get("Name")

            # Test finding file by ID
            found_path = find_file_by_id(self.course_name, material_id)

            if found_path:
                found_files_count += 1

                # Test source name extraction logic (same as in script)
                filename_on_disk = os.path.basename(found_path)
                name_part = os.path.splitext(filename_on_disk)[0]

                if str(material_id) in name_part:
                     parts = name_part.split(str(material_id))
                     extracted_name = parts[0].strip().rstrip("-").strip()
                elif " - " in name_part:
                     extracted_name, _ = name_part.rsplit(" - ", 1)
                else:
                    extracted_name = name_part

                cleaned_name = clean_filename(extracted_name)
                print(f"  [OK] ID: {material_id} -> File: {filename_on_disk} -> Source: {cleaned_name}")
            else:
                print(f"  [FAIL] ID: {material_id} ({name}) -> File NOT FOUND")

        print(f"\nFound {found_files_count} / {len(exam_records)} files on disk.")

if __name__ == '__main__':
    unittest.main()
