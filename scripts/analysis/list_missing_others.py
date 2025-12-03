
import json

def list_missing_exams():
    try:
        with open("report_unmatched_targets.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        missing_others = []
        for item in data:
            if "Yaz Okulu" not in item['TargetFile']:
                missing_others.append(item)

        print(f"Found {len(missing_others)} missing files that are NOT Yaz Okulu:\n")
        for item in missing_others:
            print(f"Course: {item['Course']}")
            print(f"File:   {item['TargetFile']}")
            print("-" * 30)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_missing_exams()
