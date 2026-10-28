#!/usr/bin/env python3
"""
Reorganize output folder structure for acik-ogretim.github.io

Current structure:
    output/Anadolu/Donem 1/Ders/...
    output/ATA-AÖF/Donem 1/Ders/...
    output/Auzef/Donem 1/Ders/...

New structure:
    output/anadolu-aof/gorsel-iletisim/donem-1/ders-adi/...
    output/ataturk-aof/grafik-sanatlar/donem-1/ders-adi/...
    output/auzef/cocuk-gelisimi/donem-1/ders-adi/...
"""

import os
import shutil
import re
import json
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
OUTPUT_DIR = Path("output")
BACKUP_DIR = Path("output_backup")

# Mapping: old_name -> (new_university, new_department)
STRUCTURE_MAP = {
    "Anadolu": ("anadolu-aof", "gorsel-iletisim"),
    "ATA-AÖF": ("ataturk-aof", "grafik-sanatlar"),
    "Auzef": ("auzef", "cocuk-gelisimi"),
}

# Department metadata
DEPARTMENT_META = {
    "anadolu-aof": {
        "name": "Anadolu Üniversitesi",
        "faculty": "Açıköğretim Fakültesi",
        "short": "Anadolu AÖF",
        "url": "https://www.anadolu.edu.tr/acikogretim",
        "departments": {
            "gorsel-iletisim": {
                "name": "Görsel İletişim Tasarımı",
                "code": "GIT",
                "semesters": 8
            }
        }
    },
    "ataturk-aof": {
        "name": "Atatürk Üniversitesi",
        "faculty": "Açıköğretim Fakültesi",
        "short": "ATA-AÖF",
        "url": "https://atauzem.atauni.edu.tr",
        "departments": {
            "grafik-sanatlar": {
                "name": "Grafik Sanatlar",
                "code": "GS",
                "semesters": 8
            }
        }
    },
    "auzef": {
        "name": "İstanbul Üniversitesi",
        "faculty": "Açık ve Uzaktan Eğitim Fakültesi",
        "short": "AUZEF",
        "url": "https://auzef.istanbul.edu.tr",
        "departments": {
            "cocuk-gelisimi": {
                "name": "Çocuk Gelişimi",
                "code": "CG",
                "semesters": 8
            }
        }
    }
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Turkish character replacements
    tr_map = {
        'ç': 'c', 'Ç': 'C',
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'I': 'I',
        'İ': 'I', 'i': 'i',
        'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S',
        'ü': 'u', 'Ü': 'U',
    }

    for tr_char, en_char in tr_map.items():
        text = text.replace(tr_char, en_char)

    # Convert to lowercase and replace spaces/special chars with hyphens
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text)  # Remove multiple hyphens
    text = text.strip('-')

    return text


def convert_donem_folder(name: str) -> str:
    """Convert 'Donem 1' to 'donem-1'."""
    match = re.match(r'Donem\s*(\d+)', name)
    if match:
        return f"donem-{match.group(1)}"
    return slugify(name)


def create_backup():
    """Create backup of current output folder."""
    if BACKUP_DIR.exists():
        print(f"⚠️  Backup already exists at {BACKUP_DIR}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            return False
        shutil.rmtree(BACKUP_DIR)

    print(f"📦 Creating backup at {BACKUP_DIR}...")
    shutil.copytree(OUTPUT_DIR, BACKUP_DIR)
    print("✅ Backup created")
    return True


def get_publishable_files(src_dir: Path) -> List[Path]:
    """Get list of files that should be published (md, html, css, js)."""
    publishable_extensions = {'.md', '.html', '.css', '.js'}
    files = []

    for file in src_dir.rglob('*'):
        if file.is_file() and file.suffix in publishable_extensions:
            files.append(file)

    return files


def reorganize_structure(dry_run: bool = True):
    """Reorganize the output folder structure."""

    print("\n🔄 Starting reorganization...")
    print(f"   Mode: {'DRY RUN' if dry_run else 'ACTUAL'}\n")

    new_output = OUTPUT_DIR / "_new" if dry_run else OUTPUT_DIR

    for old_name, (new_uni, new_dept) in STRUCTURE_MAP.items():
        old_path = OUTPUT_DIR / old_name

        if not old_path.exists():
            print(f"⚠️  Skipping {old_name} - directory not found")
            continue

        new_base = new_output / new_uni / new_dept
        print(f"\n📁 {old_name} → {new_uni}/{new_dept}")

        # Process each Donem folder
        for item in old_path.iterdir():
            if item.is_dir() and item.name.startswith("Donem"):
                old_donem = item
                new_donem_name = convert_donem_folder(item.name)
                new_donem_path = new_base / new_donem_name

                print(f"   📂 {item.name} → {new_donem_name}")

                if not dry_run:
                    new_donem_path.mkdir(parents=True, exist_ok=True)

                # Process each course folder
                for course_dir in old_donem.iterdir():
                    if course_dir.is_dir():
                        new_course_name = slugify(course_dir.name)
                        new_course_path = new_donem_path / new_course_name

                        print(f"      📄 {course_dir.name} → {new_course_name}")

                        if not dry_run:
                            # Copy only publishable files
                            for file in get_publishable_files(course_dir):
                                rel_path = file.relative_to(course_dir)
                                new_file_path = new_course_path / rel_path
                                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(file, new_file_path)

        # Copy root files (index.md, interaktif.html)
        for root_file in ['index.md', 'interaktif.html']:
            src_file = old_path / root_file
            if src_file.exists():
                dest_file = new_base / root_file
                print(f"   📄 {root_file}")
                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)

    # Create metadata files
    if not dry_run:
        create_metadata_files(new_output)

    print("\n✅ Reorganization complete!")
    if dry_run:
        print("   (This was a dry run. Run with --apply to make changes)")


def create_metadata_files(output_dir: Path):
    """Create _meta.json files for each university and department."""

    for uni_slug, uni_data in DEPARTMENT_META.items():
        uni_path = output_dir / uni_slug
        if not uni_path.exists():
            continue

        # University metadata
        uni_meta = {
            "type": "university",
            "name": uni_data["name"],
            "faculty": uni_data["faculty"],
            "short": uni_data["short"],
            "url": uni_data["url"]
        }

        with open(uni_path / "_meta.json", 'w', encoding='utf-8') as f:
            json.dump(uni_meta, f, ensure_ascii=False, indent=2)

        # Department metadata
        for dept_slug, dept_data in uni_data["departments"].items():
            dept_path = uni_path / dept_slug
            if not dept_path.exists():
                continue

            dept_meta = {
                "type": "department",
                "name": dept_data["name"],
                "code": dept_data["code"],
                "semesters": dept_data["semesters"],
                "university": uni_data["short"]
            }

            with open(dept_path / "_meta.json", 'w', encoding='utf-8') as f:
                json.dump(dept_meta, f, ensure_ascii=False, indent=2)


def create_new_index_files(output_dir: Path):
    """Create new index.md files with proper navigation."""

    # Main index
    main_index = """---
layout: default
title: Ana Sayfa
---

# 📚 Açık Öğretim Soru ve Çalışma Portalı

Türkiye'deki açık öğretim fakülteleri için hazırlanmış kapsamlı çalışma materyalleri.

## 🎓 Üniversiteler

"""

    for uni_slug, uni_data in DEPARTMENT_META.items():
        uni_path = output_dir / uni_slug
        if uni_path.exists():
            main_index += f"### [{uni_data['short']}]({uni_slug}/)\n"
            main_index += f"{uni_data['name']} - {uni_data['faculty']}\n\n"

            for dept_slug, dept_data in uni_data["departments"].items():
                dept_path = uni_path / dept_slug
                if dept_path.exists():
                    main_index += f"- 📂 [{dept_data['name']}]({uni_slug}/{dept_slug}/)\n"

            main_index += "\n"

    with open(output_dir / "index.md", 'w', encoding='utf-8') as f:
        f.write(main_index)

    print("✅ Created main index.md")


def main():
    import sys

    print("=" * 60)
    print("📁 Açık Öğretim Klasör Yapısı Yeniden Düzenleme Aracı")
    print("=" * 60)

    if not OUTPUT_DIR.exists():
        print(f"❌ Error: {OUTPUT_DIR} not found!")
        sys.exit(1)

    # Check for --apply flag
    apply_changes = "--apply" in sys.argv

    if not apply_changes:
        print("\n⚠️  Running in DRY RUN mode. Use --apply to make actual changes.\n")
    else:
        print("\n⚠️  APPLY mode - Changes will be made!\n")
        if not create_backup():
            print("Aborting.")
            sys.exit(1)

    reorganize_structure(dry_run=not apply_changes)


if __name__ == "__main__":
    main()
