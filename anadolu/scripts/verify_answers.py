#!/usr/bin/env python3
"""
Verify exam answers by extracting the official answer key from the PDF using Gemini.
Compares the extracted key with the answers in the JSON files.
"""

import os
import json
import sys
import time
import glob
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from libs.genai_files_manager import GenAIFilesManager

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")
JSON_DIR = os.path.join(OUTPUT_DIR, "json")
REPORT_PATH = os.path.join(OUTPUT_DIR, "answer_verification_report.md")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

# Configure SDKs
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Files Manager
files_manager = GenAIFilesManager()

def find_pdf_for_material(donem, course_name, material_id):
    """Find the PDF file corresponding to a material ID."""
    materials_dir = os.path.join(OUTPUT_DIR, f"Donem {donem}", course_name, "Materyaller")
    if not os.path.exists(materials_dir):
        return None

    # Search for file containing material_id
    for filename in os.listdir(materials_dir):
        if material_id in filename and filename.endswith(".pdf"):
            return os.path.join(materials_dir, filename)

    return None

# Cache file for extracted keys
KEYS_CACHE_PATH = os.path.join(OUTPUT_DIR, "answer_keys_cache.json")

def load_keys_cache():
    if os.path.exists(KEYS_CACHE_PATH):
        try:
            with open(KEYS_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_keys_cache(cache):
    with open(KEYS_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)
    print(f"  💾 Saved answer keys cache ({len(cache)} keys)")

def extract_answer_key(pdf_path, cache):
    """Upload PDF and extract answer key using Gemini, with caching."""
    pdf_hash = f"{os.path.basename(pdf_path)}_{os.path.getsize(pdf_path)}"

    # Consensus logic: Try up to 3 times, look for 2 matching results
    results = []

    # Check cache first
    if pdf_hash in cache:
        print(f"  Using cached key as Attempt 1.")
        results.append(cache[pdf_hash])

    # Initialize uploaded_file outside the loop
    uploaded_file = None

    # Determine how many more attempts we need.
    # If we have cache, we have 1 result. We need 1 more match.
    # We can try up to 2 more times (total 3 results considered).
    # If no cache, we try up to 2 times.

    max_attempts = 2
    start_attempt = 1 if results else 0

    for attempt in range(start_attempt, max_attempts):
        try:
            # Upload file if not already uploaded
            if uploaded_file is None:
                # Extract material_id from filename if possible
                filename = os.path.basename(pdf_path)
                material_id = None
                try:
                    parts = filename.rsplit(" - ", 1)
                    if len(parts) > 1 and parts[1].replace(".pdf", "").isdigit():
                        material_id = parts[1].replace(".pdf", "")
                except:
                    pass

                uploaded_file = files_manager.upload_file(
                    local_path=pdf_path,
                    material_id=material_id,
                    display_name=filename
                )

                if not uploaded_file:
                    print("  Upload failed.")
                    return {}

            print(f"  Extracting answer key (Attempt {attempt+1}/{max_attempts})...")

            prompt = """
            Bu PDF bir sınav kitapçığıdır. Belgenin EN SONUNDA genellikle bir "Cevap Anahtarı" tablosu veya listesi bulunur.

            GÖREVİN:
            1. Sadece "Cevap Anahtarı" bölümünü bul.
            2. Bu bölümdeki 1'den 20'ye kadar olan soru numaralarını ve karşılık gelen doğru şıkkı (A, B, C, D, E) çıkar.
            3. Soruları KENDİN ÇÖZME. Sadece anahtarda yazan harfi oku.
            4. Eğer bir soru için "İptal" veya benzeri bir ifade varsa, cevabı "X" olarak işaretle.

            DİKKAT:
            - Bazen cevap anahtarı yatay, bazen dikey olabilir.
            - Bazen "A Kitapçığı", "B Kitapçığı" ayrımı olabilir. Eğer varsa, genellikle ilk sütun veya "A" kitapçığı varsayılır ama belgede hangisi baskınsa onu al. Genellikle tek bir anahtar vardır.
            - Harfleri (A, B, C, D, E) doğru okuduğundan emin ol.

            Çıktı formatı SADECE şu JSON yapısında olmalıdır:
            {
                "answers": [
                    {"q": 1, "a": "A"},
                    {"q": 2, "a": "C"},
                    {"q": 3, "a": "X"},
                    ...
                ]
            }
            """

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(file_uri=uploaded_file.uri, mime_type="application/pdf"),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]

            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "answers": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(
                                type=types.Type.OBJECT,
                                properties={
                                    "q": types.Schema(type=types.Type.INTEGER),
                                    "a": types.Schema(type=types.Type.STRING)
                                },
                                required=["q", "a"]
                            )
                        )
                    },
                    required=["answers"]
                )
            )

            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
                config=generate_content_config
            )

            result = json.loads(response.text)

            # Convert list to dict
            answer_dict = {}
            if "answers" in result:
                for item in result["answers"]:
                    answer_dict[str(item["q"])] = item["a"]

            if answer_dict:
                results.append(answer_dict)
            else:
                print("  ⚠️ Empty result.")

            # Check for consensus
            if len(results) >= 2:
                # Compare last result with previous ones
                current_res = results[-1]
                # Check against all previous results
                for prev_res in results[:-1]:
                    if current_res == prev_res:
                        print("  ✅ Consensus reached.")
                        # Save to cache (update if needed)
                        cache[pdf_hash] = current_res
                        save_keys_cache(cache)
                        return current_res

        except Exception as e:
            print(f"  Error extracting key (Attempt {attempt+1}): {e}")
            time.sleep(2)

    if results:
        print("  ⚠️ No consensus reached, using the last result.")
        return results[-1]

    return {}

# Cache file for verification results
RESULTS_CACHE_PATH = os.path.join(OUTPUT_DIR, "verification_results_cache.json")

def load_results_cache():
    if os.path.exists(RESULTS_CACHE_PATH):
        try:
            with open(RESULTS_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_results_cache(cache):
    with open(RESULTS_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

# Import enrichment functions
try:
    from anadolu.scripts.enrich_questions import load_summaries, upload_all_summaries, enrich_questions_batch
except ImportError:
    # Fallback if running from script dir
    sys.path.append(os.path.join(PROJECT_ROOT, "anadolu", "scripts"))
    from enrich_questions import load_summaries, upload_all_summaries, enrich_questions_batch

def main():
    print("Starting Answer Verification & Correction...")

    keys_cache = load_keys_cache()
    results_cache = load_results_cache()
    report_content = ["# ✅ Cevap Anahtarı Doğrulama Raporu", "", f"**Tarih:** {time.strftime('%Y-%m-%d %H:%M')}", "", "---", ""]

    # Iterate through Enriched JSONs
    files = glob.glob(os.path.join(JSON_DIR, "Donem *", "*Çıkmış Sorular - Enriched.json"))

    processed_materials = set()

    # Load enrolled courses
    enrolled_courses_path = os.path.join(PROJECT_ROOT, "anadolu", "enrolled_courses.json")
    dersler_path = os.path.join(PROJECT_ROOT, "anadolu", "dersler.json")

    enrolled_course_names = set()
    if os.path.exists(enrolled_courses_path) and os.path.exists(dersler_path):
        try:
            with open(enrolled_courses_path, 'r', encoding='utf-8') as f:
                enrolled_data = json.load(f)
                enrolled_codes = {c.get("kod") for c in enrolled_data}

            with open(dersler_path, 'r', encoding='utf-8') as f:
                dersler_data = json.load(f)

            for ders in dersler_data:
                if ders.get("DersKodu") in enrolled_codes:
                    enrolled_course_names.add(ders.get("CourseName"))

            print(f"Loaded {len(enrolled_course_names)} enrolled courses.")
        except Exception as e:
            print(f"Error loading enrolled courses: {e}")
            enrolled_course_names = set()

    for json_file in sorted(files):
        try:
            # Extract course info from filename
            filename = os.path.basename(json_file)
            parts = filename.split(" - ")
            if len(parts) < 3:
                continue

            donem_str = parts[1] # "Dönem X"
            donem = donem_str.split(" ")[1]
            course_name = parts[2]

            # Filter by enrolled courses
            if enrolled_course_names and course_name not in enrolled_course_names:
                continue

            # Filter for Donem 5 only (User Request) - REMOVED
            # if donem != "5":
            #     continue

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = data.get("questions", [])
            if not questions:
                continue

            print(f"Processing {course_name} ({donem_str})...")

            # Group questions by material_id
            questions_by_material = {}
            for q in questions:
                mid = q.get("material_id")
                if mid:
                    if mid not in questions_by_material:
                        questions_by_material[mid] = []
                    questions_by_material[mid].append(q)

            # Iterate over materials
            for mid, q_list in questions_by_material.items():
                if mid in processed_materials:
                    continue

                pdf_path = find_pdf_for_material(donem, course_name, mid)
                if not pdf_path:
                    continue

                print(f"  Processing Material: {mid} (PDF: {os.path.basename(pdf_path)})")

                # Extract Key
                official_key = extract_answer_key(pdf_path, keys_cache)

                if not official_key:
                    print("  ⚠️ Could not extract key.")
                    continue

                processed_materials.add(mid)

                # Compare and Correct
                source_name = q_list[0].get("source", "Unknown Source")
                mismatches = []
                questions_to_update = [] # List of (question_id, new_correct_index, new_text_suffix)

                for q in q_list:
                    q_num = str(q.get("exam_question_number", q.get("id")))

                    if q_num not in official_key:
                        continue

                    official_answer = official_key[q_num].upper()

                    # Convert current correctIndex to Letter
                    options_letters = ["A", "B", "C", "D", "E"]
                    current_idx = q.get("correctIndex")

                    if current_idx == -1:
                        current_answer = "X"
                    elif current_idx is None or not (0 <= current_idx < 5):
                        current_answer = "N/A"
                    else:
                        current_answer = options_letters[current_idx]

                    # Check for mismatch
                    if official_answer != current_answer:
                        # Logic for X (Cancel)
                        if official_answer == "X":
                            if current_answer != "X": # If not already marked as cancelled
                                print(f"    Correcting Q{q['id']} ({q_num}): {current_answer} -> İPTAL")
                                questions_to_update.append({
                                    "id": q["id"],
                                    "correctIndex": -1,
                                    "append_text": " <br><b>(BU SORU İPTAL EDİLMİŞTİR)</b>",
                                    "explanation": "Bu soru resmi cevap anahtarına göre iptal edilmiştir."
                                })
                                mismatches.append({
                                    "id": q.get("id"),
                                    "q_num": q_num,
                                    "current": current_answer,
                                    "official": "İPTAL",
                                    "text": q.get("question")[:50]
                                })

                        # Logic for Letter Change
                        elif official_answer in options_letters:
                            new_idx = options_letters.index(official_answer)
                            print(f"    Correcting Q{q['id']} ({q_num}): {current_answer} -> {official_answer}")
                            questions_to_update.append({
                                "id": q["id"],
                                "correctIndex": new_idx,
                                "append_text": None,
                                "explanation": None
                            })
                            mismatches.append({
                                "id": q.get("id"),
                                "q_num": q_num,
                                "current": current_answer,
                                "official": official_answer,
                                "text": q.get("question")[:50]
                            })

                if mismatches:
                    # 1. Update Raw JSON First
                    raw_json_path = json_file.replace(" - Enriched.json", " - Raw.json")
                    if os.path.exists(raw_json_path):
                        try:
                            with open(raw_json_path, 'r', encoding='utf-8') as f:
                                raw_data = json.load(f)

                            raw_questions_map = {q["id"]: q for q in raw_data.get("questions", [])}
                            raw_changed = False

                            for update in questions_to_update:
                                q_id = update["id"]
                                if q_id in raw_questions_map:
                                    rq = raw_questions_map[q_id]
                                    rq["correctIndex"] = update["correctIndex"]
                                    if update["append_text"] and update["append_text"] not in rq["question"]:
                                        rq["question"] += update["append_text"]
                                    raw_changed = True

                            if raw_changed:
                                with open(raw_json_path, 'w', encoding='utf-8') as f:
                                    json.dump(raw_data, f, indent=4, ensure_ascii=False)
                                print(f"  � Updated Raw JSON: {os.path.basename(raw_json_path)}")

                            # 2. Re-read Raw JSON
                            print("  📖 Re-reading Raw JSON for enrichment...")
                            with open(raw_json_path, 'r', encoding='utf-8') as f:
                                reloaded_raw_data = json.load(f)

                            reloaded_map = {q["id"]: q for q in reloaded_raw_data.get("questions", [])}

                            # 3. Prepare questions for enrichment from Reloaded Raw Data
                            questions_to_enrich_from_raw = []
                            for update in questions_to_update:
                                q_id = update["id"]
                                if q_id in reloaded_map:
                                    # If it was cancelled, we might not need to enrich, just set explanation
                                    if update["correctIndex"] == -1:
                                        # Manually update enriched data for cancelled
                                        for eq in data["questions"]:
                                            if eq["id"] == q_id:
                                                eq["correctIndex"] = -1
                                                if update["append_text"] and update["append_text"] not in eq["question"]:
                                                    eq["question"] += update["append_text"]
                                                eq["explanation"] = update["explanation"]
                                    else:
                                        questions_to_enrich_from_raw.append(reloaded_map[q_id])

                            # 4. Enrich
                            if questions_to_enrich_from_raw:
                                print(f"  🔄 Re-enriching {len(questions_to_enrich_from_raw)} questions...")
                                summaries = load_summaries(course_name, donem)
                                if summaries:
                                    summary_uris = upload_all_summaries(summaries)
                                    if summary_uris:
                                        enrichment_results = enrich_questions_batch(questions_to_enrich_from_raw, summary_uris)

                                        # Update Enriched Data (in memory 'data')
                                        for eq in data["questions"]:
                                            if eq["id"] in enrichment_results:
                                                res = enrichment_results[eq["id"]]
                                                eq["UniteNo"] = res.get("UniteNo")
                                                eq["topic"] = res.get("topic")
                                                eq["explanation"] = res.get("explanation")
                                                # Also ensure correctIndex is synced
                                                for update in questions_to_update:
                                                    if update["id"] == eq["id"]:
                                                        eq["correctIndex"] = update["correctIndex"]

                            # 5. Save Enriched JSON
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)
                            print(f"  💾 Saved Enriched JSON: {os.path.basename(json_file)}")

                        except Exception as e:
                            print(f"  ❌ Error updating/enriching: {e}")
                            import traceback
                            traceback.print_exc()

                    report_content.append(f"### {course_name} - {source_name}")
                    report_content.append(f"**PDF:** `{os.path.basename(pdf_path)}`")
                    report_content.append("")
                    report_content.append("| Soru No | Eski | Yeni | Soru Metni |")
                    report_content.append("| --- | --- | --- | --- |")
                    for m in mismatches:
                        report_content.append(f"| {m['q_num']} | {m['current']} | {m['official']} | {m['text']} |")
                    report_content.append("")

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            import traceback
            traceback.print_exc()

    # Save Report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))

    print(f"\nReport saved to {REPORT_PATH}")

if __name__ == "__main__":
    main()
