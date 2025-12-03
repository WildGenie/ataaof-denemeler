
import json

def analyze():
    try:
        with open("source_unmatched_report.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Total unmatched source files: {len(data)}")

        exam_files = []
        for item in data:
            path = item.get("Path", "").lower()
            if "çıkmış sorular" in path or "cikmis sorular" in path:
                exam_files.append(item)

        print(f"Unmatched 'Çıkmış Sorular' files: {len(exam_files)}")

        if exam_files:
            print("\nSample unmatched exams:")
            for item in exam_files[:20]:
                print(f" - {item.get('UnmatchedFile')} ({item.get('Course')})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
