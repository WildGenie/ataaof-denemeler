import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRICULUM_FILE = os.path.join(BASE_DIR, 'auzef', 'curriculum_courses.json')
JSON_ROOT = os.path.join(BASE_DIR, 'output', 'Auzef', 'json')

def cleanup_filenames():
    if not os.path.exists(CURRICULUM_FILE):
        print("Curriculum file not found.")
        return

    with open(CURRICULUM_FILE, 'r', encoding='utf-8') as f:
        curriculum = json.load(f)

    # Create a canonical map: lowercase_name -> Correct Case Name
    canonical_map = {}
    for course in curriculum:
        name = course['name']
        canonical_map[name.lower().strip()] = name

    # Scan all JSON files
    for root, dirs, files in os.walk(JSON_ROOT):
        for file in files:
            if not file.endswith('.json'): continue

            # Extract current course name from filename
            if not file.startswith("Auzef - Dönem "): continue

            try:
                fname_no_ext = file.replace('.json', '')
                parts = fname_no_ext.split(' - ', 2)
                term_part = parts[1]
                remainder = parts[2]

                sub_parts = remainder.rsplit(' - ', 1)
                current_course_name = sub_parts[0]
                q_type_suffix = sub_parts[1]

                # Check if we have a better name
                clean_name = current_course_name.lower().strip()
                if clean_name in canonical_map:
                    correct_name = canonical_map[clean_name]
                    if correct_name != current_course_name:
                        # Rename!
                        new_fname = f"Auzef - {term_part} - {correct_name} - {q_type_suffix}.json"

                        old_path = os.path.normpath(os.path.join(root, file))
                        new_path = os.path.normpath(os.path.join(root, new_fname))

                        # Case-insensitive filesystem check:
                        # If paths are same but different casing, it's just a casing rename.
                        # On Mac/Windows, os.path.exists(new_path) will be true if old_path exists.

                        if old_path.lower() == new_path.lower():
                            if old_path != new_path:
                                print(f"Casing-only rename: {file} -> {new_fname}")
                                # Safe rename on Mac: Move to temp, then to final
                                temp_path = old_path + ".tmp"
                                os.rename(old_path, temp_path)
                                os.rename(temp_path, new_path)
                            continue

                        if os.path.exists(new_path):
                            # Real merge (different names entirely)
                            print(f"Merging {file} into {new_fname}...")
                            with open(old_path, 'r', encoding='utf-8') as f_old:
                                old_data = json.load(f_old)
                            with open(new_path, 'r', encoding='utf-8') as f_new:
                                new_data = json.load(f_new)

                            # Simple merge (unique by ID)
                            existing_ids = set()
                            id_key = "QuestionId" if "Raw" in file else "SoruID"
                            for q in new_data: existing_ids.add(q.get(id_key))

                            added = 0
                            for q in old_data:
                                if q.get(id_key) not in existing_ids:
                                    new_data.append(q)
                                    existing_ids.add(q.get(id_key))
                                    added += 1

                            with open(new_path, 'w', encoding='utf-8') as f_out:
                                json.dump(new_data, f_out, indent=4, ensure_ascii=False)
                            os.remove(old_path)
                            print(f"Merged and removed old file. Added {added} questions.")
                        else:
                            print(f"Renaming {file} -> {new_fname}")
                            os.rename(old_path, new_path)
            except Exception as e:
                print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    cleanup_filenames()
