#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Kısa Özet PDF -> Markdown indirici
# Parametre istemez. Aşağıdaki 5 dersin "kısa özet" PDF'lerini indirir
# ve metni basit bir biçimde Markdown'a dönüştürüp kaydeder.
#
# Gereken paketler:
#   pip install requests pdfminer.six
#
# Kaynak URL şablonu:
#   https://oys.ataaof.edu.tr/kisaozetpdf/<DersId>-kisaozet.pdf
#
# Çıktılar:
#   ./OYS_KISA_OZET/<Ders Adı> - Kısa Özet.md

import os
import re
import sys
from io import BytesIO
from urllib.error import URLError
import requests
from pdfminer.high_level import extract_text

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import SHORT_SUMMARY_MD_DIR as OUT_DIR

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Bu dönem belirttiğin 5 ders
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

def pdf_to_text(pdf_bytes: bytes) -> str:
    # pdfminer ile yalın metin çıkar
    with BytesIO(pdf_bytes) as bio:
        text = extract_text(bio) or ""
    return text

def text_to_markdown(course_name: str, text: str) -> str:
    # Basit bir Markdown başlık ve temel temizlik
    # Fazla boşlukları sadeleştir, satır sonlarını normalize et
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # Bazı muhtemel başlık satırlarını ## ile işaretle (heuristic)
    lines = []
    for line in t.split("\n"):
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if s.endswith(":") or (s.isupper() and len(s) > 3):
            lines.append("## " + s)
        else:
            lines.append(s)
    body = "\n".join(lines)

    md = f"# {course_name} — Kısa Özet\n\n{body}\n"
    return md

def download_short_summary(course_name: str, ders_id: str) -> None:
    url = URL_TPL.format(ders_id=ders_id)
    out_md = os.path.join(OUT_DIR, safe_name(f"{course_name} - Kısa Özet.md"))
    try:
        resp = requests.get(url, timeout=60)
        ct = resp.headers.get("Content-Type", "").lower()
        if resp.status_code == 200 and ("pdf" in ct or url.lower().endswith(".pdf")):
            text = pdf_to_text(resp.content)
            if not text.strip():
                print(f"[WARN] PDF metne dönüştürülemedi veya boş: {course_name}")
            md = text_to_markdown(course_name, text)
            with open(out_md, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[OK]  {course_name}: {url} -> {out_md}")
        else:
            print(f"[ERR] {course_name}: HTTP {resp.status_code} / {ct} (PDF değil ya da indirilemedi)")
    except (requests.RequestException, URLError) as e:
        print(f"[ERR] {course_name}: {e}")

def main():
    for course_name, ders_id in COURSES:
        download_short_summary(course_name, ders_id)

if __name__ == "__main__":
    # pdfminer.six yoksa anlaşılır hata verelim
    try:
        main()
    except ImportError as e:
        print("pdfminer.six gerekli. Yüklemek için:\n  pip install pdfminer.six", file=sys.stderr)
        raise
