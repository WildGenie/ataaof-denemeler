import json
import os
from collections import Counter

# Determine the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(BASE_DIR, 'output', 'Auzef', 'json')

def summarize_unit_counts():
    summary = {}

    if not os.path.exists(AUZEF_JSON_DIR):
        print(f"Directory not found: {AUZEF_JSON_DIR}")
        return

    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if not file.endswith('.json') or file.endswith('Raw.json'):
                continue

            # We are interested in "Alıştırma Soruları" files
            if "Alıştırma Soruları" not in file:
                continue

            # Extract course name from filename
            # Format: Auzef - Dönem {Term} - {CourseName} - Alıştırma Soruları.json
            parts = file.replace('.json', '').split(' - ')
            if len(parts) < 4: continue

            course_name = parts[2]
            term = parts[1]

            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                unit_counts = Counter()
                for q in data:
                    unit = q.get('Unite', 'Unknown')
                    unit_counts[unit] += 1

                # Sort units by number if possible
                sorted_units = {}
                for u in sorted(unit_counts.keys(), key=lambda x: int(str(x)) if str(x).isdigit() else 999):
                    sorted_units[u] = unit_counts[u]

                if term not in summary:
                    summary[term] = {}
                summary[term][course_name] = sorted_units

            except Exception as e:
                print(f"Error processing {file}: {e}")

    # Print summary
    for term in sorted(summary.keys()):
        print(f"\n=== {term} ===")
        for course, units in sorted(summary[term].items()):
            unit_str = ", ".join([f"U{u}: {c}" for u, c in units.items()])
            total = sum(units.values())
            print(f"- {course}: {unit_str} (Total: {total})")

if __name__ == "__main__":
    summarize_unit_counts()
