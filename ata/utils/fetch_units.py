#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Basit OYS PDF indirici
# Parametre yok, çerez yok, user-agent yok.
# Aşağıdaki ders listesi için 1..14 üniteleri indirir ve
# "ATA-AÖF - Dönem X - <Ders Adı> - Ünite 01.pdf" olarak kaydeder.

import os
import sys
import ssl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import UNIT_PDF_DIR as OUT_DIR

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

BASE_URL = "https://oys.ataaof.edu.tr/file/{ders_id}-{unit_id}.pdf"

# İndirilmesini istediğin dersler (Dönem, Ders Adı, DersId)
COURSES = [
    (8, "Dijital Kültür ve Sosyal Medya", "73370"),
    (7, "Görsel Kimlik ve Marka Tasarımı", "82528"),
    (7, "Tanıtım Fotoğrafı", "82527"),
    (8, "Tasarımda Kurgu ve Analiz", "82530"),
    (8, "Bilgilendirme Tasarımı", "82529"),
]

# Bazı sistemlerde SSL doğrulama hatalarını önlemek için (gerekirse)
CTX = ssl.create_default_context()

def safe_name(s: str) -> str:
    # Dosya adı için sorunlu karakterleri temizle
    bad = '<>:"/\\|?*\n\r\t'
    for ch in bad:
        s = s.replace(ch, "_")
    return s.strip()

def download_pdf(ders_id: str, unit_id: int, out_path: str) -> bool:
    url = BASE_URL.format(ders_id=ders_id, unit_id=unit_id)
    try:
        # Basit istek (UA/çerez yok)
        req = Request(url)
        with urlopen(req, context=CTX, timeout=60) as resp:
            ct = resp.headers.get("Content-Type", "").lower()
            if "pdf" not in ct:
                # PDF yerine HTML (giriş sayfası vs.) döndüyse atla
                print(f"[SKIP] {url} -> Content-Type: {ct}")
                return False
            data = resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
        print(f"[OK]   {url} -> {out_path}")
        return True
    except HTTPError as e:
        # 404 vb. durumlar
        print(f"[ERR]  {url} -> HTTP {e.code}")
    except URLError as e:
        print(f"[ERR]  {url} -> {e.reason}")
    except Exception as e:
        print(f"[ERR]  {url} -> {e}")
    return False

def main():
    for donem, ders_adi, ders_id in COURSES:
        for unit_id in range(1, 15):  # 1..14
            file_name = f"ATA-AÖF - Dönem {donem} - {ders_adi} - Ünite {unit_id:02d}.pdf"
            out_path = os.path.join(OUT_DIR, safe_name(file_name))
            # Zaten varsa yeniden indirmeyi atla
            if os.path.exists(out_path):
                print(f"[SKIP] Var: {out_path}")
                continue
            download_pdf(ders_id, unit_id, out_path)

if __name__ == "__main__":
    main()
