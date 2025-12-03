
import json

def check_other_years():
    try:
        with open("report_unmatched_targets.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        others = []
        for item in data:
            target = item.get('TargetFile', '')
            # Check if 2024-2025 is NOT in the filename
            if "2024-2025" not in target:
                others.append(item)

        if not others:
            print("No unmatched files found outside of 2024-2025.")
        else:
            print(f"Found {len(others)} unmatched files from other years:")
            for item in others:
                print(f" - {item['Course']}: {item['TargetFile']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_other_years()
