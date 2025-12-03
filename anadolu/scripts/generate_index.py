#!/usr/bin/env python3
"""
Generate index.md for all Markdown files.
Organizes files by Semester and Course.
"""

import os
import re
from collections import defaultdict
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MD_BASE_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")
INDEX_PATH = os.path.join(MD_BASE_DIR, "index.md")

def get_file_title(filepath):
    """Extract title from markdown file (first line) or filename."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith("# "):
                return first_line[2:].strip()
    except:
        pass

    filename = os.path.basename(filepath)
    return filename.replace(".md", "")

def load_materials_json(donem, course_name):
    """Load Materials.json for the course."""
    # Path: output/Anadolu/json/Donem X/Anadolu - Dönem X - Course Name - Materials.json
    json_path = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json", donem,
                             f"Anadolu - {donem} - {course_name} - Materials.json")

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def find_physical_materials(donem, course_name):
    """Find physical files in Materyaller directory."""
    # Path: output/Anadolu/Donem X/Course Name/Materyaller/
    materials_dir = os.path.join(MD_BASE_DIR, donem, course_name, "Materyaller")

    physical_files = []
    if os.path.exists(materials_dir):
        for f in os.listdir(materials_dir):
            if f.endswith(".pdf"):
                physical_files.append({
                    "filename": f,
                    "path": f"Materyaller/{f}"
                })
    return physical_files

def generate_course_index(donem, course_name, files):
    """Generate index.md for a specific course."""
    course_dir = os.path.join(MD_BASE_DIR, donem, course_name)
    index_path = os.path.join(course_dir, "index.md")

    content = [f"# {course_name}", "", "## Ders Materyalleri", ""]

    # Separate files by type
    past_exams = []
    other_materials = []

    for file_info in files:
        if "Çıkmış Sorular" in file_info["filename"]:
            past_exams.append(file_info)
        else:
            other_materials.append(file_info)

    # Load external materials (PDFs)
    materials_json = load_materials_json(donem, course_name)
    physical_materials = find_physical_materials(donem, course_name)

    # Add physical materials to other_materials
    for pm in physical_materials:
        # Try to find metadata in materials_json
        # This is a simple match, could be improved
        name = pm["filename"].replace(".pdf", "")
        other_materials.append({
            "filename": pm["path"],
            "title": name,
            "type": "pdf"
        })

    # Sort lists
    past_exams.sort(key=lambda x: x["filename"])
    other_materials.sort(key=lambda x: (
        0 if "Sorularla Ogrenelim" in x["filename"] else
        1 if "Alıştırma Soruları" in x["filename"] else
        2 if "Ünite Özeti" in x["title"] else 3,
        x["title"]
    ))



    # Group other materials
    groups = {
        "sorularla_ogrenelim": [],
        "alistirma_sorulari": [],
        "unite_ozetleri": [],
        "infografikler": [],
        "sinav_pdf": [],
        "diger": []
    }

    for item in other_materials:
        title = item["title"]
        filename = item["filename"]

        if "Sorularla Ogrenelim" in filename or "Sorularla Öğrenelim" in title:
            groups["sorularla_ogrenelim"].append(item)
        elif "Alıştırma Soruları" in filename or "Alıştırma Soruları" in title:
            groups["alistirma_sorulari"].append(item)
        elif "Ünite Özeti" in title:
            groups["unite_ozetleri"].append(item)
        elif "İnfografik" in title:
            groups["infografikler"].append(item)
        elif any(x in title for x in ["Sınav", "Çıkmış Sorular", "Dönem Sonu", "Yaz Okulu"]): # Raw PDFs
            groups["sinav_pdf"].append(item)
        else:
            groups["diger"].append(item)

    # Add Main Materials (Flat, no list bullets)
    # 1. Çıkmış Sorular
    if past_exams:
        for file_info in past_exams:
            filename = urllib.parse.quote(file_info["filename"].replace(".md", ""))
            title = "🎓 Çıkmış Sorular (Zenginleştirilmiş)"
            content.append(f"### [{title}]({filename})")
            content.append("")

    # 2. Sorularla Öğrenelim
    if groups["sorularla_ogrenelim"]:
        for item in groups["sorularla_ogrenelim"]:
            # Remove .md extension
            clean_filename = item["filename"].replace(".md", "")
            filename_parts = clean_filename.split("/")
            encoded_parts = [urllib.parse.quote(p) for p in filename_parts]
            encoded_filename = "/".join(encoded_parts)
            title = "📚 Sorularla Öğrenelim"
            content.append(f"### [{title}]({encoded_filename})")
            content.append("")

    # 3. Alıştırma Soruları
    if groups["alistirma_sorulari"]:
        for item in groups["alistirma_sorulari"]:
            # Remove .md extension
            clean_filename = item["filename"].replace(".md", "")
            filename_parts = clean_filename.split("/")
            encoded_parts = [urllib.parse.quote(p) for p in filename_parts]
            encoded_filename = "/".join(encoded_parts)
            title = "✏️ Alıştırma Soruları"
            content.append(f"### [{title}]({encoded_filename})")
            content.append("")

    content.append("---")
    content.append("## Diğer Materyaller")
    content.append("")

    # Helper to clean title
    def clean_title(title, group_key):
        # Remove ID at the end (e.g., " - 633936")
        # Regex: space + hyphen + space + digits at the end
        title = re.sub(r" - \d+$", "", title)

        if group_key == "unite_ozetleri":
            title = title.replace("Ünite Özeti - ", "")
        elif group_key == "infografikler":
            title = title.replace("İnfografik - ", "")

        return title

    # Helper to add a group
    def add_group(group_key, display_name, icon_default="📄"):
        items = groups[group_key]
        if not items:
            return

        # Sort items
        items.sort(key=lambda x: x["title"])

        content.append("<details>")
        content.append(f"<summary>{icon_default} <strong>{display_name}</strong></summary>")
        content.append("")

        for item in items:
            # Handle paths and remove .md
            clean_filename = item["filename"].replace(".md", "")
            filename_parts = clean_filename.split("/")
            encoded_parts = [urllib.parse.quote(p) for p in filename_parts]
            encoded_filename = "/".join(encoded_parts)

            title = clean_title(item["title"], group_key)

            # Specific icons
            icon = "📄"
            if group_key == "unite_ozetleri": icon = "📝"
            elif group_key == "infografikler": icon = "📊"
            elif group_key == "sinav_pdf": icon = "🎓"

            content.append(f"- {icon} [{title}]({encoded_filename})")

        content.append("</details>")
        content.append("")

    # Add Groups (excluding main ones)
    add_group("unite_ozetleri", "Ünite Özetleri", "📝")
    add_group("infografikler", "İnfografikler", "📊")
    add_group("sinav_pdf", "Geçmiş Sınav Soruları (PDF)", "🎓")
    add_group("diger", "Diğer Materyaller", "📂")

    content.append("")
    content.append("[🔙 Ana Sayfaya Dön](../../)")

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))

    # Remove old README.md if exists
    readme_path = os.path.join(course_dir, "README.md")
    if os.path.exists(readme_path):
        os.remove(readme_path)

    return index_path

def generate_index():
    """Generate main index.md and course index.md files."""
    print("Generating indices...")

    # Find all markdown files in Donem folders
    md_files = []
    for root, dirs, files in os.walk(MD_BASE_DIR):
        if "Donem " not in root:
            continue

        for file in files:
            # Skip index.md (both main and course ones) and README.md
            if file.endswith(".md") and file not in ["index.md", "README.md"]:
                md_files.append(os.path.join(root, file))

    if not md_files:
        print("No markdown files found.")
        return

    # Group by Semester -> Course
    structure = defaultdict(lambda: defaultdict(list))

    for filepath in md_files:
        rel_path = os.path.relpath(filepath, MD_BASE_DIR)
        parts = rel_path.split(os.sep)

        if len(parts) >= 3 and parts[0].startswith("Donem"):
            donem = parts[0]
            course_name = parts[1]
            filename = parts[-1]

            structure[donem][course_name].append({
                "path": rel_path,
                "title": get_file_title(filepath),
                "filename": filename
            })

    # Generate Course Indices
    course_index_count = 0
    for donem, courses in structure.items():
        for course_name, files in courses.items():
            generate_course_index(donem, course_name, files)
            course_index_count += 1

    # Generate Main Index
    content = ["# Anadolu AÖF - Ders Materyalleri", ""]

    sorted_semesters = sorted(structure.keys(), key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999)

    for donem in sorted_semesters:
        content.append(f"## {donem}")
        content.append("")

        courses = structure[donem]
        for course_name in sorted(courses.keys()):
            # Link to course index (directory style)
            encoded_donem = urllib.parse.quote(donem)
            encoded_course = urllib.parse.quote(course_name)
            course_link = f"{encoded_donem}/{encoded_course}/"

            content.append(f"- 📂 [{course_name}]({course_link})")

        content.append("")
        content.append("---")
        content.append("")

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))

    print(f"✅ Saved Main Index: {INDEX_PATH}")
    print(f"✅ Generated {course_index_count} Course Indices.")
    print(f"Indexed {len(md_files)} files.")

if __name__ == "__main__":
    generate_index()
