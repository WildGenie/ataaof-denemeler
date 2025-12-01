#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Kısa özet PDF indirici
# Parametre istemez, çerez/UA istemez.
# 5 dersi tek tek indirir ve ./OYS_KISA_OZET klasörüne kaydeder.

import os
import re
import sys
import requests

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import SHORT_SUMMARY_DIR as OUT_DIR

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Ders listesi (Ad, DersId)
COURSES = [
    ("Bilgilendirme Tasarımı", "82529"),
    ("Dijital Kültür ve Sosyal Medya", "73370"),
    ("Görsel Kimlik ve Marka Tasarımı", "82528"),
    ("Tanıtım Fotoğrafı", "82527"),
    ("Tasarımda Kurgu ve Analiz", "82530"),
]

URL_TPL = "https://oys.ataaof.edu.tr/kisaozetpdf/{ders_id}-kisaozet.pdf"

def safe_name(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*\n\r\t]', "_", s).strip()

def download_pdf(course_name: str, ders_id: str) -> None:
    url = URL_TPL.format(ders_id=ders_id)
    out_path = os.path.join(OUT_DIR, safe_name(f"{course_name} - Kısa Özet.pdf"))
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", "").lower():
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"[OK] {course_name} -> {out_path}")
        else:
            print(f"[ERR] {course_name}: HTTP {r.status_code}, Content-Type={r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"[ERR] {course_name}: {e}")

def main():
    for course_name, ders_id in COURSES:
        download_pdf(course_name, ders_id)

if __name__ == "__main__":
    main()
