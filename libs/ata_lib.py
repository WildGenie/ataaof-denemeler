import os
from libs.shared import clean_html, questions_to_markdown

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERSLER_FILE = os.path.join(BASE_DIR, "ata", "dersler.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "ata")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
RAW_JSON_DIR = os.path.join(OUTPUT_DIR, "raw")
FULL_JSON_DIR = os.path.join(OUTPUT_DIR, "full")
MD_DIR = os.path.join(OUTPUT_DIR, "md")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdf")
SHORT_SUMMARY_DIR = os.path.join(OUTPUT_DIR, "short_summary")
SHORT_SUMMARY_MD_DIR = os.path.join(OUTPUT_DIR, "short_summary_md")
UNIT_PDF_DIR = os.path.join(OUTPUT_DIR, "units_pdf")

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    if not os.path.exists(RAW_JSON_DIR):
        os.makedirs(RAW_JSON_DIR)
    if not os.path.exists(FULL_JSON_DIR):
        os.makedirs(FULL_JSON_DIR)
    if not os.path.exists(MD_DIR):
        os.makedirs(MD_DIR)
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
    if not os.path.exists(SHORT_SUMMARY_DIR):
        os.makedirs(SHORT_SUMMARY_DIR)
    if not os.path.exists(SHORT_SUMMARY_MD_DIR):
        os.makedirs(SHORT_SUMMARY_MD_DIR)
    if not os.path.exists(UNIT_PDF_DIR):
        os.makedirs(UNIT_PDF_DIR)
