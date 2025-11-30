import os
import json
from anadolu_soru_getir import questions_to_markdown

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "sorular-anadolu")
MD_DIR = os.path.join(OUTPUT_DIR, "md")
UNIT_JSON_DIR = os.path.join(BASE_DIR, "output", "json")

def sort_and_regenerate():
    if not os.path.exists(OUTPUT_DIR):
        print(f"Directory not found: {OUTPUT_DIR}")
        return

    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json") and "Tüm Sorular" in f]
    print(f"Found {len(files)} JSON files to process.")

    for filename in files:
        json_path = os.path.join(OUTPUT_DIR, filename)

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)

            if not questions:
                print(f"Skipping empty file: {filename}")
                continue

            print(f"Processing {filename} ({len(questions)} questions)...")

            # Sort questions
            # Sort questions by Semester, Unit, then SoruID
            try:
                questions.sort(key=lambda x: (
                    x.get('Somestre', '0'),
                    int(x.get('Unite', 0)) if str(x.get('Unite', '0')).isdigit() else x.get('Unite', 0),
                    int(x['SoruID']) if str(x.get('SoruID', '')).isdigit() else x.get('SoruID', 0)
                ))
            except Exception as e:
                print(f"  Error sorting {filename}: {e}")
                # Fallback sort
                questions.sort(key=lambda x: (x.get('Somestre', '0'), x.get('Unite', 0), x.get('SoruID', 0)))

            # Save sorted JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=4, ensure_ascii=False)

            # Generate Markdown
            # Extract course info from filename or first question
            # Filename format: Anadolu - Dönem {donem} - {course_name} - Tüm Sorular.json
            parts = filename.split(' - ')
            if len(parts) >= 4:
                donem = parts[1].replace('Dönem ', '')
                course_name = parts[2]
            else:
                course_name = questions[0].get('DersAd', 'Unknown Course')
                donem = questions[0].get('Somestre', 'Unknown')

            md_filename = f"Anadolu - Dönem {donem} - {course_name} - Sorular.md"
            md_path = os.path.join(MD_DIR, md_filename)

            md_content = f"# {course_name}\n\n"
            current_unit = None
            for q in questions:
                unit = q.get('Unite')
                if unit != current_unit:
                    md_content += f"## Unite {unit}\n"
                    current_unit = unit
                md_content += questions_to_markdown([q])

            # Ensure MD directory exists
            if not os.path.exists(MD_DIR):
                os.makedirs(MD_DIR)

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"  Saved sorted JSON and regenerated Markdown.")

        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    # Process Unit JSON files in output/json
    if os.path.exists(UNIT_JSON_DIR):
        unit_files = [f for f in os.listdir(UNIT_JSON_DIR) if f.endswith(".json")]
        print(f"\nFound {len(unit_files)} Unit JSON files to process in {UNIT_JSON_DIR}.")

        for filename in unit_files:
            json_path = os.path.join(UNIT_JSON_DIR, filename)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    questions = json.load(f)

                if not questions:
                    continue

                # Sort unit questions by SoruID
                # Unit files contain questions for a single unit, so just sort by ID
                try:
                    questions.sort(key=lambda x: int(x['SoruID']) if str(x.get('SoruID', '')).isdigit() else x.get('SoruID', 0))
                except Exception as e:
                    # Fallback
                    questions.sort(key=lambda x: x.get('SoruID', 0))

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(questions, f, indent=4, ensure_ascii=False)

                # print(f"Sorted {filename}") # Optional: reduce verbosity
            except Exception as e:
                print(f"Error processing unit file {filename}: {e}")
        print("Finished processing Unit JSON files.")
    else:
        print(f"Directory not found: {UNIT_JSON_DIR}")

if __name__ == "__main__":
    sort_and_regenerate()
