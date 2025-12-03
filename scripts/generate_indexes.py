import os
import urllib.parse

BASE_DIR = "output/Anadolu"

def generate_indexes():
    # Main Index
    main_index_content = "# Anadolu AÖF Ders Notları\n\n"

    donem_folders = sorted([d for d in os.listdir(BASE_DIR) if d.startswith("Donem") and os.path.isdir(os.path.join(BASE_DIR, d))], key=lambda x: int(x.split(" ")[1]))

    for donem in donem_folders:
        main_index_content += f"## [{donem}]({urllib.parse.quote(donem)}/index.md)\n"

        # Semester Index
        donem_path = os.path.join(BASE_DIR, donem)
        semester_index_content = f"# {donem}\n\n"

        course_folders = sorted([c for c in os.listdir(donem_path) if os.path.isdir(os.path.join(donem_path, c)) and c != "Materyaller"])

        for course in course_folders:
            semester_index_content += f"- [{course}]({urllib.parse.quote(course)}/index.md)\n"
            main_index_content += f"- [{course}]({urllib.parse.quote(donem)}/{urllib.parse.quote(course)}/index.md)\n"

            # Course Index
            course_path = os.path.join(donem_path, course)
            course_index_content = f"# {course}\n\n"

            # List MD files
            md_files = sorted([f for f in os.listdir(course_path) if f.endswith(".md") and f != "index.md"])
            if md_files:
                course_index_content += "## Ders İçerikleri\n"
                for md_file in md_files:
                    course_index_content += f"- [{md_file}]({urllib.parse.quote(md_file)})\n"

            # List Materials (PDFs)
            materials_path = os.path.join(course_path, "Materyaller")
            if os.path.exists(materials_path):
                course_index_content += "\n## Materyaller\n"
                pdf_files = sorted([f for f in os.listdir(materials_path) if f.endswith(".pdf")])
                for pdf in pdf_files:
                    course_index_content += f"- [{pdf}](Materyaller/{urllib.parse.quote(pdf)})\n"

            with open(os.path.join(course_path, "index.md"), "w", encoding="utf-8") as f:
                f.write(course_index_content)

        with open(os.path.join(donem_path, "index.md"), "w", encoding="utf-8") as f:
            f.write(semester_index_content)

    with open(os.path.join(BASE_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write(main_index_content)

    print("Indexes generated successfully.")

if __name__ == "__main__":
    generate_indexes()
