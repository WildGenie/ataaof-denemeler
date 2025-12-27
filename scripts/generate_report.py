import json
import os
from collections import Counter

# Determine the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(BASE_DIR, 'output', 'Auzef', 'json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'output', 'Auzef', 'soru_sayilari.md')

def generate_full_report():
    summary = {}

    if not os.path.exists(AUZEF_JSON_DIR):
        print(f"Directory not found: {AUZEF_JSON_DIR}")
        return

    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if not file.endswith('.json') or file.endswith('Raw.json'):
                continue

            # Correct splitting logic:
            # Format: Auzef - Dönem {Term} - {CourseName} - {Type}.json
            # Use maxsplit for the first two and rsplit for the last one

            # 1. Remove .json
            fname_no_ext = file.replace('.json', '')

            # 2. Split fixed prefix "Auzef - Dönem {Term} - "
            # Actually, let's just use re or smarter split
            if not fname_no_ext.startswith("Auzef - "): continue

            try:
                # [Auzef, Dönem X, {Rest}]
                parts = fname_no_ext.split(' - ', 2)
                term = parts[1]
                remainder = parts[2]

                # Split remainder from right to separate Type ("Alıştırma Soruları" or "Sorular")
                # [{CourseName}, {Type}]
                sub_parts = remainder.rsplit(' - ', 1)
                course_name = sub_parts[0]
                q_type_raw = sub_parts[1]

                if "Alıştırma" in q_type_raw:
                    q_type = "Alıştırma"
                elif "Sorular" in q_type_raw:
                    q_type = "Genel"
                else:
                    q_type = q_type_raw
            except:
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                unit_counts = Counter()
                for q in data:
                    unit = q.get('Unite', q.get('unite_id', 'Bilinmiyor'))
                    try:
                        unit = int(str(unit))
                    except:
                        pass
                    unit_counts[unit] += 1

                if term not in summary:
                    summary[term] = {}
                if course_name not in summary[term]:
                    summary[term][course_name] = {}

                summary[term][course_name][q_type] = unit_counts

            except Exception as e:
                print(f"Error processing {file}: {e}")

    # Generate Markdown Content
    md = "# AUZEF Soru Sayıları Raporu\n\n"
    md += "Bu dosya, tüm dönemlerdeki derslerin ünite bazlı soru sayılarını gösterir.\n\n"

    for term in sorted(summary.keys()):
        md += f"## {term}\n\n"
        md += "| Ders Adı | Tip | Toplam | Ünite Dağılımı |\n"
        md += "| :--- | :--- | :--- | :--- |\n"

        for course in sorted(summary[term].keys()):
            for q_type in sorted(summary[term][course].keys()):
                counts = summary[term][course][q_type]
                total = sum(counts.values())

                # Sort units logically
                def unit_sort(u):
                    try: return int(str(u))
                    except: return 999

                sorted_units = sorted(counts.keys(), key=unit_sort)
                dist_str = ", ".join([f"U{u}: {counts[u]}" for u in sorted_units])

                md += f"| {course} | {q_type} | **{total}** | {dist_str} |\n"
        md += "\n"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_full_report()
