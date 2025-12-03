
import json

def analyze():
    try:
        with open("reverse_match_report.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        course = "Temel Sanat ve Tasarım Eğitimi"
        print(f"Analyzing {course}...")

        found = False
        for item in data:
            if item.get("Course") == course:
                found = True
                print(f"File: {item.get('SourceFile')}")
                print(f"  Status: {item.get('Status')}")
                print(f"  Type: {item.get('ExamType')}")
                print(f"  Year: {item.get('YearRange')} / {item.get('SingleYear')}")
                print("-" * 20)

        if not found:
            print(f"No entries found for {course}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
