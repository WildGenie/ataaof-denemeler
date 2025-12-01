import json
import os

def main():
    input_file = "anadolu_dersler.json"
    output_file = "sorular-anadolu/sorular.json"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # Group by semester
    semesters = {}
    for course in courses:
        donem = int(course['Donem'])
        if donem not in semesters:
            semesters[donem] = []

        course_name = course['CourseName']
        # Filename format: Anadolu - Dönem {donem} - {course_name} - Tüm Sorular.json
        filename = f"Anadolu - Dönem {donem} - {course_name} - Tüm Sorular.json"

        semesters[donem].append({
            "dersAdi": course_name,
            "dosyaAdi": filename
        })

    # Create final structure
    final_output = []
    for donem in sorted(semesters.keys()):
        final_output.append({
            "donem": donem,
            "dersler": semesters[donem]
        })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"Successfully created {output_file} with {len(courses)} courses grouped by semester.")

if __name__ == "__main__":
    main()
