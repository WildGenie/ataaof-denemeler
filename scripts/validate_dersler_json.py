
import json
import os
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERSLER_JSON_PATH = os.path.join(BASE_DIR, 'output/Auzef/sorular/dersler.json')
# URLs in dersler.json are relative to 'output/Auzef/'.
# e.g. "json/Donem 1/..." means "output/Auzef/json/Donem 1/..."
AUZEF_ROOT = os.path.join(BASE_DIR, 'output/Auzef')

def check_files():
    if not os.path.exists(DERSLER_JSON_PATH):
        print(f"Error: {DERSLER_JSON_PATH} not found.")
        return

    try:
        with open(DERSLER_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parse JSON: {e}")
        return

    missing_count = 0
    total_refs = 0

    print("Checking referenced files in dersler.json...")

    for term_data in data:
        term = term_data.get('donem')
        for course in term_data.get('dersler', []):
            for source in course.get('sources', []):
                total_refs += 1
                rel_url = source.get('url', '')

                # If relative, construct full path
                if not rel_url.startswith('http'):
                    full_path = os.path.join(AUZEF_ROOT, rel_url)

                    if not os.path.exists(full_path):
                        print(f"[MISSING] Term {term} - {course['dersAdi']}: {rel_url}")
                        # Try to find if a file exists with different casing
                        dirname = os.path.dirname(full_path)
                        basename = os.path.basename(full_path)
                        if os.path.exists(dirname):
                            candidates = os.listdir(dirname)
                            for c in candidates:
                                if c.lower() == basename.lower():
                                    print(f"   -> FOUND CASE MISMATCH: {c}")
                        else:
                            print(f"   -> Directory not found: {dirname}")

                        missing_count += 1

    if missing_count == 0:
        print(f"All {total_refs} file references are valid! Files on disk match dersler.json.")
    else:
        print(f"Found {missing_count} missing files out of {total_refs}.")

if __name__ == "__main__":
    check_files()
