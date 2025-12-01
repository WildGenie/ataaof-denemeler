import json
import os
import sys
import glob
from tqdm import tqdm

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.ata_lib import DERSLER_FILE, RAW_JSON_DIR

def load_courses():
    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return {}
    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    return {c['CourseName']: c for c in courses}

def get_filename_prefix(course):
    return course.get("DersiVeren") or "ATA-AÖF"

def import_legacy():
    legacy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "legacy", "SoruGetir", "output", "json")
    if not os.path.exists(legacy_dir):
        print(f"Error: Legacy directory {legacy_dir} not found.")
        return

    courses_map = load_courses()
    legacy_files = glob.glob(os.path.join(legacy_dir, "* - Tüm Sorular.json"))

    print(f"Found {len(legacy_files)} legacy files.")

    if not os.path.exists(RAW_JSON_DIR):
        os.makedirs(RAW_JSON_DIR)

    total_imported = 0
    total_merged = 0

    for legacy_file in tqdm(legacy_files, desc="Importing Legacy Files"):
        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)

            if not questions:
                continue

            # Group by Unit
            questions_by_unit = {}
            # Parse metadata from filename
            # Format: PREFIX - Dönem X - Course Name - Tüm Sorular.json
            basename = os.path.basename(legacy_file)
            parts = basename.split(' - ')

            if len(parts) >= 4:
                # parts[0] = Prefix (ATA-AÖF)
                # parts[1] = Dönem X
                # parts[2] = Course Name
                # parts[-1] = Tüm Sorular.json

                donem_str = parts[1].replace("Dönem ", "").replace("Dönem ", "") # Handle normalization
                try:
                    donem = int(donem_str)
                except ValueError:
                    donem = 0

                course_name = parts[2]
            else:
                # Fallback to file content if filename parsing fails
                course_name = questions[0].get("DersAd")
                donem = questions[0].get("Somestre", 0)

            # Still look up course to get other metadata if needed, but trust filename for Donem/Name
            course = courses_map.get(course_name, {"DersiVeren": "ATA-AÖF"})
            prefix = get_filename_prefix(course)

            for q in questions:
                unit = q.get("Unite")
                if unit is None:
                    continue
                if unit not in questions_by_unit:
                    questions_by_unit[unit] = []
                questions_by_unit[unit].append(q)

            # Save/Merge
            for unit, unit_questions in questions_by_unit.items():
                filename = f"{prefix} - Dönem {donem} - {course_name} - Unite {unit:02d} - Raw.json"
                filepath = os.path.join(RAW_JSON_DIR, filename)

                existing_questions = {}
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            for q in existing_data:
                                existing_questions[q['SoruID']] = q
                    except Exception as e:
                        print(f"Error reading existing file {filename}: {e}")

                # Merge
                merged_count = 0
                new_count = 0
                for q in unit_questions:
                    if q['SoruID'] in existing_questions:
                        # Optional: Update existing? Or keep existing?
                        # Legacy might be older, so maybe keep existing if conflict?
                        # But legacy might have "cleaner" data?
                        # Let's assume existing raw (from API) is better if recent.
                        # But if existing is just what we fetched (which might be partial), and legacy has it too...
                        # Actually, we just want to ADD missing questions.
                        pass
                    else:
                        existing_questions[q['SoruID']] = q
                        new_count += 1
                        total_imported += 1

                if new_count > 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(list(existing_questions.values()), f, ensure_ascii=False, indent=4)
                    # tqdm.write(f"  Imported {new_count} questions to {filename}")

        except Exception as e:
            print(f"Error processing {legacy_file}: {e}")

    print(f"Import complete. Imported {total_imported} new questions.")

if __name__ == "__main__":
    import_legacy()
