import os
import shutil
import re

BASE_DIR = "output/Anadolu"
MD_DIR = os.path.join(BASE_DIR, "md")
JSON_DIR = os.path.join(BASE_DIR, "json")
PAST_EXAMS_DIR = os.path.join(BASE_DIR, "past_exams")

def restructure():
    if not os.path.exists(MD_DIR):
        print(f"MD directory {MD_DIR} does not exist.")
        return

    # Iterate through Donem folders in md/
    for donem_folder in os.listdir(MD_DIR):
        donem_path = os.path.join(MD_DIR, donem_folder)
        if not os.path.isdir(donem_path):
            continue

        print(f"Processing {donem_folder}...")

        # Target Donem folder in BASE_DIR (e.g., output/Anadolu/Donem 1)
        target_donem_path = os.path.join(BASE_DIR, donem_folder)
        os.makedirs(target_donem_path, exist_ok=True)

        for filename in os.listdir(donem_path):
            filepath = os.path.join(donem_path, filename)
            if not os.path.isfile(filepath):
                continue

            # Extract Course Name
            # Format: Anadolu - Dönem X - Course Name - Suffix.md
            # Example: Anadolu - Dönem 3 - Türk Dili I - Sorularla Ogrenelim.md
            match = re.search(r"Anadolu - Dönem \d+ - (.+) - (.+)\.md", filename)
            if match:
                course_name = match.group(1)
                suffix = match.group(2) # e.g., "Sorularla Ogrenelim"

                # Create Course folder
                course_dir = os.path.join(target_donem_path, course_name)
                os.makedirs(course_dir, exist_ok=True)

                # Move file
                # Rename to simpler name? User said "Alıştırma Soruları ve Sorularla Öğrenelim'in md dosyası olsun"
                # Let's keep the suffix as filename for clarity, or just "Sorularla Ogrenelim.md"
                new_filename = f"{suffix}.md"
                target_path = os.path.join(course_dir, new_filename)

                shutil.move(filepath, target_path)
                print(f"Moved {filename} -> {target_path}")

                # Check for PDFs in past_exams and move them to Materyaller
                # past_exams structure: output/Anadolu/past_exams/Course Name/
                # We want: output/Anadolu/Donem X/Course Name/Materyaller/

                old_course_pdf_dir = os.path.join(PAST_EXAMS_DIR, course_name)
                if os.path.exists(old_course_pdf_dir):
                    materials_dir = os.path.join(course_dir, "Materyaller")
                    os.makedirs(materials_dir, exist_ok=True)

                    for pdf_file in os.listdir(old_course_pdf_dir):
                        src_pdf = os.path.join(old_course_pdf_dir, pdf_file)
                        dst_pdf = os.path.join(materials_dir, pdf_file)
                        if os.path.isfile(src_pdf):
                             shutil.move(src_pdf, dst_pdf)
                             print(f"Moved PDF {pdf_file} -> {dst_pdf}")

                    # Remove empty old dir
                    if not os.listdir(old_course_pdf_dir):
                        os.rmdir(old_course_pdf_dir)

            else:
                print(f"Could not parse filename {filename}, skipping.")

    # Remove empty md directory
    # shutil.rmtree(MD_DIR) # Be careful, maybe keep for now?
    # print(f"Processed MD files. You can remove {MD_DIR} if empty.")

if __name__ == "__main__":
    restructure()
