import os
from libs.shared import clean_html, questions_to_markdown

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERSLER_FILE = os.path.join(BASE_DIR, "ata", "dersler.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "ATA-AÖF")

# Core directories matching Anadolu/Auzef
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
SORULAR_DIR = os.path.join(OUTPUT_DIR, "sorular")
RAW_JSON_DIR = os.path.join(OUTPUT_DIR, "raw")

def setup_directories():
    for d in [OUTPUT_DIR, RAW_JSON_DIR, SORULAR_DIR, JSON_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

    # Create Donem folders in both root and json
    for i in range(1, 9):
        for parent in [OUTPUT_DIR, JSON_DIR]:
            donem_dir = os.path.join(parent, f"Donem {i}")
            if not os.path.exists(donem_dir):
                os.makedirs(donem_dir)
