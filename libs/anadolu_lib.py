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
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "anadolu")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
RAW_JSON_DIR = os.path.join(OUTPUT_DIR, "raw")
FULL_JSON_DIR = os.path.join(OUTPUT_DIR, "full")
MD_DIR = os.path.join(OUTPUT_DIR, "md")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdf")
UNIT_JSON_DIR = JSON_DIR

HEADERS = {
    'Connection': 'keep-alive',
    'Origin': 'https://ekampus.anadolu.edu.tr',
    'accept': '*/*',
    'authorization': os.getenv('ANADOLU_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJldHMtd2Vic2VydmljZXMifQ.EuhtnmabJ9H67LLgchAt6Z75oGjjIXmB3HksUYyCOeM'),
}

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

def map_to_old_format(api_question, course_name, unit_or_type, donem):
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
        "OlusturmaTarihi": datetime.now().isoformat(),
        "GelYer": 0,
        "DersId": 0,
        "OBSDersId": 0,
        "CevapSira": None,
        "Aciklama": explanation
    }
