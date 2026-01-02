#!/usr/bin/env python3
"""
Organize explanation files in data/aciklamalar into semester folders.
"""
import os
import shutil
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACIKLAMALAR_DIR = os.path.join(PROJECT_ROOT, "data", "aciklamalar")

def organize():
    if not os.path.exists(ACIKLAMALAR_DIR):
        print("No aciklamalar directory found.")
        return

    files = [f for f in os.listdir(ACIKLAMALAR_DIR) if f.endswith(".json")]

    print(f"Found {len(files)} files to organize in {ACIKLAMALAR_DIR}")

    for filename in files:
        # Expected format: "ATA-AÖF - Dönem X - Course Name - Tüm Sorular.json"
        # Extract Donem
        match = re.search(r"Dönem (\d+)", filename)
        if match:
            donem = match.group(1)
            target_dir = os.path.join(ACIKLAMALAR_DIR, f"Donem {donem}")

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            src_path = os.path.join(ACIKLAMALAR_DIR, filename)
            dst_path = os.path.join(target_dir, filename)

            # Move
            shutil.move(src_path, dst_path)
            print(f"Moved {filename} -> Donem {donem}/")
        else:
            print(f"Skipping {filename} (Could not parse Donem)")

if __name__ == "__main__":
    organize()
