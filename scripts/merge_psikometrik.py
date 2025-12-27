import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(BASE_DIR, 'output', 'Auzef', 'json', 'Donem 5')

def merge_psikometrik():
    # File patterns
    bad_prefix = "Auzef - Dönem 5 - Psikometrik  Gelişimsel Ölçme ve Değerlendirme"
    good_prefix = "Auzef - Dönem 5 - Psikometrik - Gelişimsel Ölçme ve Değerlendirme"

    suffixes = [" - Alıştırma Soruları.json", " - Alıştırma Soruları - Raw.json"]

    for suffix in suffixes:
        bad_file = os.path.join(JSON_DIR, bad_prefix + suffix)
        good_file = os.path.join(JSON_DIR, good_prefix + suffix)

        if os.path.exists(bad_file):
            print(f"Merging {bad_file} into {good_file}...")

            with open(bad_file, 'r', encoding='utf-8') as f:
                bad_data = json.load(f)

            if os.path.exists(good_file):
                with open(good_file, 'r', encoding='utf-8') as f:
                    good_data = json.load(f)
            else:
                good_data = []

            # Merge logic: Add only unique questions
            # Use QuestionId for Raw, and something similar for processed
            existing_ids = set()
            id_key = "QuestionId" if "Raw" in suffix else "SoruID"

            for q in good_data:
                existing_ids.add(q.get(id_key))

            new_count = 0
            for q in bad_data:
                if q.get(id_key) not in existing_ids:
                    good_data.append(q)
                    existing_ids.add(q.get(id_key))
                    new_count += 1

            print(f"Added {new_count} new questions.")

            # Save merged file
            with open(good_file, 'w', encoding='utf-8') as f:
                json.dump(good_data, f, indent=4, ensure_ascii=False)

            # Remove bad file
            os.remove(bad_file)
            print(f"Removed {bad_file}")

if __name__ == "__main__":
    merge_psikometrik()
