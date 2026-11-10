#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Basit OYS PDF indirici
# Ders listesini dersler.json'dan okur ve üniteleri indirir.

import os
import sys
import ssl
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import (
    DERSLER_FILE,
    OUTPUT_DIR
)

BASE_URL = "https://oys.ataaof.edu.tr/file/{ders_id}-{unit_id}.pdf"

# Bazı sistemlerde SSL doğrulama hatalarını önlemek için (gerekirse)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def get_safe_course_name(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()

def download_pdf(ders_id: str, unit_id: int, out_path: str) -> bool:
    url = BASE_URL.format(ders_id=ders_id, unit_id=unit_id)
    try:
        # Basit istek (UA/çerez yok)
        req = Request(url)
        with urlopen(req, context=CTX, timeout=30) as resp:
            ct = resp.headers.get("Content-Type", "").lower()
            if "pdf" not in ct:
                # PDF yerine HTML (giriş sayfası vs.) döndüyse atla
                # print(f"[SKIP] {url} -> Content-Type: {ct}")
                return False
            data = resp.read()
            if len(data) < 1000: # Ignore very small files (empty/error pages)
                return False

            with open(out_path, "wb") as f:
                f.write(data)
        print(f"[OK]   Unit {unit_id} -> {out_path}")
        return True
    except HTTPError as e:
        # 404 vb. durumlar - Sessizce geç, her dersin her ünitesi olmayabilir
        # print(f"[ERR]  {url} -> HTTP {e.code}")
        pass
    except URLError as e:
        print(f"[ERR]  {url} -> {e.reason}")
    except Exception as e:
        print(f"[ERR]  {url} -> {e}")
    return False

def process_course_units(course):
    ders_id = course.get("DersId")
    course_name = course.get("CourseName")
    donem = course.get("Donem")

    safe_course_name = get_safe_course_name(course_name)
    course_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", safe_course_name)
    materyaller_dir = os.path.join(course_dir, "Materyaller")

    if not os.path.exists(materyaller_dir):
        os.makedirs(materyaller_dir, exist_ok=True)

    # tq = tqdm(range(1, 15), desc=f"{course_name[:15]}..", leave=False)

    found_any = False
    consecutive_errors = 0
    downloaded_count = 0

    for unit_id in range(1, 15):
        filename = f"Ünite {unit_id:02d}.pdf"
        out_path = os.path.join(materyaller_dir, filename)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            found_any = True
            consecutive_errors = 0
            continue

        success = download_pdf(ders_id, unit_id, out_path)
        if success:
            found_any = True
            consecutive_errors = 0
            downloaded_count += 1
        else:
            consecutive_errors += 1

        # Stop if we miss too many units in a row
        if consecutive_errors > 3:
            break

    return downloaded_count

def main():
    if not os.path.exists(DERSLER_FILE):
        print(f"Error: {DERSLER_FILE} not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Found {len(courses)} courses. Starting parallel download...")

    max_workers = 5 # Moderate concurrency for files

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_course_units, c) for c in courses]

        with tqdm(total=len(courses), desc="Courses") as pbar:
            for future in as_completed(futures):
                count = future.result()
                # if count > 0:
                #     tqdm.write(f"Downloaded {count} new files.")
                pbar.update(1)

if __name__ == "__main__":
    main()
