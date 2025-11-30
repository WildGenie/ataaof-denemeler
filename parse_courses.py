import re
import json
import os

def parse_html_to_json(html_content):
    courses = []

    # Map Roman numerals to semesters
    roman_to_int = {
        "I": "1", "II": "2", "III": "3", "IV": "4",
        "V": "5", "VI": "6", "VII": "7", "VIII": "8"
    }

    # Split by semester headers to handle semesters correctly
    # The HTML has <h2 class="yariyil-ad">I.YARIYIL</h2>
    semester_blocks = re.split(r'<h2 class="yariyil-ad">', html_content)

    for block in semester_blocks[1:]: # Skip the part before the first header
        # Extract semester number
        semester_match = re.match(r'([IVX]+)\.YARIYIL</h2>', block)
        if not semester_match:
            continue

        semester_roman = semester_match.group(1)
        semester = roman_to_int.get(semester_roman, semester_roman)

        # Find the table body
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', block, re.DOTALL)
        if not tbody_match:
            continue

        tbody = tbody_match.group(1)

        # Find all rows
        rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)

        for row in rows:
            # Skip header rows (containing <th>)
            if '<th>' in row:
                continue

            # Extract columns
            cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)

            if len(cols) < 5:
                # Might be a summary row or "Yabancı Dil Dersleri" row
                continue

            # 1. Ders Kodu
            code = cols[0].strip()

            # 2. Ders Adı (inside <a> tag)
            name_match = re.search(r'<a.*?>(.*?)</a>', cols[1], re.DOTALL)
            name = name_match.group(1).strip() if name_match else cols[1].strip()

            # 3. Zorunlu/Category
            category = cols[2].strip()
            is_zorunlu = "1" if "Zorunlu" in category else "0"

            # 4. Teori + Uygulama
            tu = cols[3].strip()
            teori = "0"
            uygulama = "0"
            if "+" in tu:
                parts = tu.split("+")
                teori = parts[0].strip()
                uygulama = parts[1].strip() if len(parts) > 1 else "0"

            # 5. AKTS
            akts = cols[4].strip()

            course = {
                "Donem": semester,
                "DersKodu": code,
                "CourseName": name,
                "Category": category,
                "Zorunlu": is_zorunlu,
                "Teori": teori,
                "Uygulama": uygulama,
                "ECTS": akts,
                "DersiVeren": "Anadolu"
            }
            courses.append(course)

    return courses

def main():
    input_file = "course_list.html"
    output_file = "anadolu_dersler.json"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    courses = parse_html_to_json(html_content)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=4, ensure_ascii=False)

    print(f"Successfully created {output_file} with {len(courses)} courses.")

if __name__ == "__main__":
    main()
