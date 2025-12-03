import os
import json
import urllib.request
import urllib.error
import urllib.parse
import re
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from libs.shared import clean_html, questions_to_markdown

# Load environment variables
load_dotenv()

# Directories
# libs/anadolu_lib.py -> libs/ -> project_root/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERSLER_FILE = os.path.join(BASE_DIR, "anadolu", "dersler.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "Anadolu")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
# RAW_JSON_DIR, FULL_JSON_DIR, MD_DIR, PDF_DIR, MATERIALS_DIR, PAST_EXAMS_DIR are largely handled dynamically now or obsolete in their old form
# Keeping some for compatibility or re-defining
MATERIALS_DIR = JSON_DIR # Materials list now goes to json folder
PDF_DIR = os.path.join(OUTPUT_DIR, "pdf")
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)
PAST_EXAMS_DIR = os.path.join(OUTPUT_DIR, "past_exams")
DOWNLOAD_TRACKER_FILE = os.path.join(OUTPUT_DIR, "download_tracker.json")

HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://ekampus.anadolu.edu.tr',
    'accept': '*/*',
    'authorization': os.getenv('ANADOLU_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYyCOeM'),
}

# API Endpoints
API_BASE_URL = "https://ets-ws.anadolu.edu.tr/v2filikaapi"
API_V3_BASE_URL = "https://ets-ws.anadolu.edu.tr/v3filikaapi"

URL_CREATE_EXAM = f"{API_BASE_URL}/examservice/create/20"
URL_GET_PDF = f"{API_BASE_URL}/examservice/getpdf"
URL_GET_CHAPTERS = f"{API_BASE_URL}/courseservice/getchapters"
URL_GET_LEARN_QUESTIONS = f"{API_BASE_URL}/getlearnwithquestionsbychapter"
URL_GET_LEARN_PDF = f"{API_BASE_URL}/examservice/getsorucevappdf"
URL_GET_MATERIAL_BY_ID = f"{API_V3_BASE_URL}/materials/getmaterialbyid"

# Configuration Defaults
DEFAULT_UNIT_COUNT = 8
DEFAULT_FETCH_ATTEMPTS = 20
DEFAULT_LEARN_ATTEMPTS = 5
DEFAULT_EMPTY_UNIT_THRESHOLD = 3

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                print(f"Error: Status code {response.status} for URL: {url}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error for {url}: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_text_content(html_content):
    if not html_content: return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return re.sub(r'\s+', ' ', text).lower().strip()

def map_to_old_format(api_question, course_name, unit_or_type, donem, existing_date=None):
    # Map API response to the structure expected by the existing system (Soru class)
    explanation = clean_html(api_question.get("AnswerExplanation"))
    title = clean_html(api_question.get("Title"))

    if title:
        if explanation:
            # Normalize for comparison using text content only
            t_norm = get_text_content(title)
            e_norm = get_text_content(explanation)

            if t_norm and e_norm and (t_norm in e_norm):
                # Title is contained in explanation, use explanation (it's longer or equal)
                pass
            elif t_norm and e_norm and (e_norm in t_norm):
                # Explanation is contained in title, use title (it's longer)
                explanation = title
            else:
                # Distinct content, concatenate
                explanation = f"{title}<br/>{explanation}"
        else:
            explanation = title

    return {
        "SoruID": api_question.get("QuestionId"),
        "SoruMetni": clean_html(api_question.get("Text")),
        "A": clean_html(api_question.get("A")),
        "B": clean_html(api_question.get("B")),
        "C": clean_html(api_question.get("C")),
        "D": clean_html(api_question.get("D")),
        "E": clean_html(api_question.get("E")),
        "DogruCevap": api_question.get("CorrectAnswer"),
        "DersAd": course_name,
        "Unite": unit_or_type,
        "Somestre": donem,
        "DogruCevapSirasi": None,
        "OlusturmaTarihi": existing_date if existing_date else datetime.now().isoformat(),
        "GelYer": 0,
        "DersId": 0,
        "OBSDersId": 0,
        "CevapSira": None,
        "Aciklama": explanation
    }

PREFIXES_TO_REMOVE = [
    "Çıkmış Sınav Soruları AÖF Yaz Okulu - ",
    "Çıkmış Sınav Soruları AÖF ",
    "AÖF "
]

def clean_filename(filename):
    """Remove unwanted prefixes from filename."""
    for prefix in PREFIXES_TO_REMOVE:
        if filename.startswith(prefix):
            return filename[len(prefix):]
    return filename
