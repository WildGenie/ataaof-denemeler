import os
import json
from libs.shared import clean_html
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERSLER_FILE = os.path.join(BASE_DIR, "auzef", "dersler.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "Auzef")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
RAW_DIR = os.path.join(OUTPUT_DIR, "fetched_raw")

# Headers for AUZEF API
def get_auzef_headers(exam_id, token=None):
    cookie = os.getenv("AUZEF_COOKIE")
    env_token = os.getenv("AUZEF_TOKEN")

    if not cookie:
        raise ValueError("AUZEF_COOKIE not found in .env file.")

    actual_token = token or env_token
    if not actual_token:
        raise ValueError("AUZEF_TOKEN not provided and not found in .env file.")

    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "auzefdeneme.istanbul.edu.tr",
        "Origin": "https://auzefdeneme.istanbul.edu.tr",
        "Referer": f"https://auzefdeneme.istanbul.edu.tr/denemesinavi/f/{exam_id}?token={actual_token}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)",
        "Cookie": cookie
    }

BASE_API_URL = "https://auzefdeneme.istanbul.edu.tr/examProcessor.php"

def setup_directories():
    for d in [OUTPUT_DIR, JSON_DIR, RAW_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

def map_to_standard_format(q, course_name, unit_id):
    """Map Auzef question to standard format."""
    # Auzef raw API keys:
    # QuestionId: str
    # Text: str (HTML)
    # A, B, C, D, E: str (HTML)
    # CorrectAnswer: str (A, B, C, D, E)
    # unite_id: int / str

    raw_u_id = q.get("unite_id")
    if raw_u_id is None:
        raw_u_id = unit_id

    try:
        final_unit = int(str(raw_u_id))
    except (ValueError, TypeError):
        final_unit = 0

    return {
        "SoruID": q.get("QuestionId"),
        "SoruMetni": clean_html(q.get("Text")),
        "A": clean_html(q.get("A", "")),
        "B": clean_html(q.get("B", "")),
        "C": clean_html(q.get("C", "")),
        "D": clean_html(q.get("D", "")),
        "E": clean_html(q.get("E", "")),
        "DogruCevap": q.get("CorrectAnswer", ""),
        "DersAd": course_name,
        "Unite": final_unit,
        "Somestre": 0,
        "Aciklama": clean_html(q.get("Explanation", ""))
    }
