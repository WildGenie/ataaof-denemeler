#!/usr/bin/env python3
"""
Test script for enriching ATA AÖF questions using Gemini AI.
Independent of GenAIFilesManager to avoid tracker usage.
"""

import os
import json
import sys
import time
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not found. Please install it.")
    sys.exit(1)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ATA_JSON_DIR = os.path.join(OUTPUT_DIR, "ATA-AÖF", "json")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def load_summary_file(course_name, donem):
    """Load the single unit summary PDF for a course."""
    materials_dir = os.path.join(OUTPUT_DIR, "ATA-AÖF", f"Donem {donem}", course_name, "Materyaller")
    summary_path = os.path.join(materials_dir, "Ünite Özeti.pdf")

    if os.path.exists(summary_path):
        return summary_path

    return None

def upload_summary_direct(path):
    """Uploads the summary PDF directly to Gemini without tracking."""
    if not path:
        return None

    # We use a display name based on course, but we don't check a persistent tracker.
    # However, to be nice to the API during repeated tests, we *could* check list_files,
    # but for this test script, we will just upload.
    display_name = os.path.basename(os.path.dirname(os.path.dirname(path))) + " - Ünite Özeti"

    print(f"  Uploading summary to Gemini: {path}")
    try:
        with open(path, "rb") as f:
            response = client.files.upload(
                file=f,
                config=types.UploadFileConfig(display_name=display_name)
            )

        # Wait for ACTIVE state
        while True:
            file_obj = client.files.get(name=response.name)
            if file_obj.state.name == "ACTIVE":
                print(f"  ✅ Upload Complete: {file_obj.uri}")
                return file_obj.uri
            elif file_obj.state.name == "FAILED":
                print("  ❌ Upload Failed.")
                return None
            time.sleep(1)

    except Exception as e:
        print(f"  Error uploading summary: {e}")
        return None

def enrich_questions_sample(questions, summary_uri):
    """
    Enrich a sample of questions using the summary URI.
    """
    question_texts = []
    for q in questions:
        full_text = f"Soru {q.get('SoruID', q.get('id', '?'))}: {q.get('SoruMetni', q.get('question'))}\n"
        options = q.get("Cevaplar", q.get("options", []))
        correct_idx = q.get("DogruCevap", q.get("correctIndex"))

        # Determine correct index integer
        c_idx = -1
        if isinstance(correct_idx, int):
            c_idx = correct_idx
        elif isinstance(correct_idx, str):
            # If "A", "B", etc.
            if correct_idx.upper() in "ABCDE":
                c_idx = ord(correct_idx.upper()) - 65

        if isinstance(options, list):
            for idx, opt in enumerate(options):
                marker = ""
                if idx == c_idx:
                    marker = " <<< BU ŞIK DOĞRU KABUL EDİLECEK"
                full_text += f"{chr(65+idx)}) {opt}{marker}\n"

        question_texts.append(full_text)

    questions_text = "\n\n".join(question_texts)

    prompt = f"""
    Aşağıda ders ünite özeti ve sınav soruları var.

    Her soru için:
    1. Sorunun hangi üniteye ait olduğunu belirle (UniteNo: 1-14 arası tahmin et)
    2. Sorunun konusunu (topic) belirle (kısa, 2-5 kelime)
    3. Sorunun doğru cevabını ve neden doğru olduğunu açıklayan detaylı bir açıklama (explanation) yaz.

    ÖNEMLİ:
    - Verilen sorudaki işaretli doğru şıkkı (<<< ...) KESİN DOĞRU kabul et.
    - Açıklamayı özetteki bilgilere dayandır.

    SORULAR:
    {questions_text}
    """

    try:
        parts = []
        if summary_uri:
            parts.append(types.Part.from_uri(file_uri=summary_uri, mime_type="application/pdf"))

        parts.append(types.Part.from_text(text=prompt))

        contents = [types.Content(role="user", parts=parts)]

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                required=["enrichments"],
                properties={
                    "enrichments": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            required=["question_id", "UniteNo", "topic", "explanation"],
                            properties={
                                "question_id": types.Schema(type=types.Type.STRING), # ID might be string in ATA
                                "UniteNo": types.Schema(type=types.Type.INTEGER),
                                "topic": types.Schema(type=types.Type.STRING),
                                "explanation": types.Schema(type=types.Type.STRING)
                            }
                        )
                    )
                }
            )
        )

        print("  Sending request to Gemini...")
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=contents,
            config=generate_content_config
        )
        print("  Response received.")

        return json.loads(response.text)

    except Exception as e:
        print(f"Error during generation: {e}")
        return {}

def main():
    # Test Parameters
    course_name = "Bilgilendirme Tasarımı"
    donem = 8

    print(f"Testing enrichment for: {course_name} (Dönem {donem})")

    # Load JSON
    # Note: Filename format might differ, need to find it
    donem_dir = os.path.join(ATA_JSON_DIR, f"Donem {donem}")
    # glob or find file
    json_path = None
    if os.path.exists(donem_dir):
        for f in os.listdir(donem_dir):
            if course_name in f and "Alıştırma Soruları.json" in f and "Raw" not in f:
                json_path = os.path.join(donem_dir, f)
                break

    if not json_path:
        print("JSON file not found.")
        return

    print(f"Found JSON: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        questions = data # It's a list in ATA structure

    print(f"Total questions: {len(questions)}")

    # Pick 5 random or first 5
    sample_questions = questions[:5]

    # Load and Upload Summary
    summary_path = load_summary_file(course_name, donem)
    if summary_path:
        print(f"Found Summary: {summary_path}")
        summary_uri = upload_summary_direct(summary_path)
    else:
        print("Summary PDF not found! Logic will fail/be poor.")
        summary_uri = None

    # Enrich
    results = enrich_questions_sample(sample_questions, summary_uri)

    print("\n--- RESULTS ---\n")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
