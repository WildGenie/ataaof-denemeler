import os
import json
import glob

def analyze_units():
    json_dir = "output/Anadolu/json"
    course_units = {}

    # Find all processed JSON files
    pattern = os.path.join(json_dir, "**", "* - Alıştırma Soruları.json")
    files = glob.glob(pattern, recursive=True)

    print(f"Found {len(files)} course files.")

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract course name from filename
            filename = os.path.basename(filepath)
            # Expected format: Anadolu - Dönem X - Course Name - Alıştırma Soruları.json
            parts = filename.split(' - ')
            if len(parts) >= 4:
                course_name = parts[2]
            else:
                course_name = filename

            units = set()
            for q in data:
                u = q.get("UniteNo") or q.get("Unite")
                if u:
                    try:
                        units.add(int(u))
                    except:
                        pass

            if units:
                course_units[course_name] = sorted(list(units))
            else:
                course_units[course_name] = []

        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    # Analyze results
    print("\n--- Unit Count Analysis ---")
    all_unit_counts = []
    for course, units in course_units.items():
        count = len(units)
        all_unit_counts.append(count)
        if count != 14: # Assuming 14 is the standard
             print(f"{course}: {count} units {units}")

    if not all_unit_counts:
        print("No data found.")
        return

    min_units = min(all_unit_counts)
    max_units = max(all_unit_counts)
    avg_units = sum(all_unit_counts) / len(all_unit_counts)

    print(f"\nTotal Courses Analyzed: {len(course_units)}")
    print(f"Min Units: {min_units}")
    print(f"Max Units: {max_units}")
    print(f"Average Units: {avg_units:.2f}")

    if min_units == max_units:
        print(f"\nCONCLUSION: All courses have exactly {min_units} units.")
    else:
        print(f"\nCONCLUSION: Unit counts vary between {min_units} and {max_units}.")

if __name__ == "__main__":
    analyze_units()
