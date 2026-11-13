#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Kısa özet PDF indirici
# Ders listesini dersler.json'dan okur, paralel indirir ve Materyaller klasörüne kaydeder.

import os
import re
import sys
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import (
    DERSLER_FILE,
    OUTPUT_DIR
)

URL_TPL = "https://oys.ataaof.edu.tr/kisaozetpdf/{ders_id}-kisaozet.pdf"

def get_safe_course_name(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()

def download_summary(course):
    course_name = course.get("CourseName")
    ders_id = course.get("DersId")
    donem = course.get("Donem")

    if not ders_id or not donem:
        return False, f"Skipped invalid course data for {course_name}"

    safe_course_name = get_safe_course_name(course_name)
    course_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", safe_course_name)
    materyaller_dir = os.path.join(course_dir, "Materyaller")

    if not os.path.exists(materyaller_dir):
        # We assume folders are mostly there, but create if missing to be safe
        os.makedirs(materyaller_dir, exist_ok=True)

    filename = "Ünite Özeti.pdf"
    out_path = os.path.join(materyaller_dir, filename)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return True, f"Exists: {course_name}"

    url = URL_TPL.format(ders_id=ders_id)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", "").lower():
            if len(r.content) < 1000:
                return False, f"Small file ignored for {course_name}"

            with open(out_path, "wb") as f:
                f.write(r.content)
            return True, f"Downloaded: {course_name}"
        else:
            return False, f"HTTP {r.status_code} for {course_name}"
    except Exception as e:
        return False, f"Error {course_name}: {str(e)}"

def main():
    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses. Starting parallel download...")

    # Determine max workers
    max_workers = 10

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_summary, c) for c in courses]

        with tqdm(total=len(courses), desc="Downloading Summaries") as pbar:
            for future in as_completed(futures):
                success, msg = future.result()
                # Uncomment to see detailed logs if needed, otherwise keep clean
                # if not success:
                #     tqdm.write(msg)
                pbar.update(1)

if __name__ == "__main__":
    main()
