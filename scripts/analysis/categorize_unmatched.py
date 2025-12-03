
import json
import os

def categorize():
    try:
        with open("source_unmatched_report.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        categories = {}

        for item in data:
            path = item.get("Path", "")
            parts = path.split('/')

            # Try to find the category (e.g., "Alınan Ders Notları ve Özetleri", "Çıkmış Sorular")
            category = "Other"
            for part in parts:
                if "Ders Notları" in part or "Özetleri" in part:
                    category = "Ders Notları ve Özetler"
                    break
                elif "Çıkmış Sorular" in part or "Çıkmış Sorular" in part:
                    category = "Çıkmış Sorular"
                    break
                elif "Canlı Ders" in part:
                    category = "Canlı Ders Kayıtları"
                    break
                elif "Kitap" in part:
                    category = "Kitaplar"
                    break

            if category not in categories:
                categories[category] = 0
            categories[category] += 1

        print("Unmatched Source Files Breakdown:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        # If there are any "Çıkmış Sorular", list them
        if "Çıkmış Sorular" in categories:
            print("\nUnmatched 'Çıkmış Sorular':")
            for item in data:
                if "Çıkmış Sorular" in item.get("Path", "") or "Çıkmış Sorular" in item.get("Path", ""):
                    print(f" - {item.get('UnmatchedFile')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    categorize()
