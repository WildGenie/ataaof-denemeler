import json
import os

# Determine the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(BASE_DIR, 'output', 'Auzef', 'json')

def fix_json_types():
    if not os.path.exists(AUZEF_JSON_DIR):
        print(f"Directory not found: {AUZEF_JSON_DIR}")
        return

    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if not file.endswith('.json'):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                changed = False
                if isinstance(data, list):
                    for q in data:
                        # Fix "Unite" in processed files
                        if "Unite" in q:
                            try:
                                old_val = q["Unite"]
                                new_val = int(str(old_val))
                                if old_val != new_val:
                                    q["Unite"] = new_val
                                    changed = True
                            except:
                                pass

                        # Fix "unite_id" in raw files
                        if "unite_id" in q:
                            try:
                                old_val = q["unite_id"]
                                new_val = int(str(old_val))
                                if old_val != new_val:
                                    q["unite_id"] = new_val
                                    changed = True
                            except:
                                pass

                if changed:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"Fixed types in: {file}")

            except Exception as e:
                print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    fix_json_types()
