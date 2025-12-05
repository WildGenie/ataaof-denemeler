#!/usr/bin/env python3
"""
Convert exam PDFs to JSON using Google Gemini API (google-genai library).
Aggregates all exam questions for a SPECIFIC COURSE into a single JSON file.
Uses the course's 'Materials.json' file to identify exam files.
Filters for EXAM files only (Type contains 'PAST_EXAMS_').
Locates files by searching for MATERIAL ID in the filename, ensuring robustness against naming variations.
Does NOT create unit-specific files.
Does NOT generate explanations, topics, or units.
Manages 'source' and 'material_id' via Python.
Ensures clean question text and options.
Uses HTML tags for formatting.
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.anadolu_lib import clean_filename
from libs.genai_files_manager import GenAIFilesManager

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
JSON_BASE_DIR = os.path.join(OUTPUT_DIR, "Anadolu", "json")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

# Configure new SDK for generation
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Files Manager
files_manager = GenAIFilesManager()

def get_target_info(pdf_path):
    """
    Extracts target JSON path and exam info from PDF path.
    Returns: (json_path, exam_name, material_id)
    """
    try:
        pdf_path = os.path.normpath(pdf_path)
        parts = pdf_path.split(os.sep)

        donem_idx = -1
        for i, part in enumerate(parts):
            if part.startswith("Donem "):
                donem_idx = i
                break

        if donem_idx == -1:
            return None, None, None

        donem_str = parts[donem_idx]
        course_name = parts[donem_idx + 1]
        filename = parts[-1]

        # Extract exam name and material_id
        name_part = os.path.splitext(filename)[0]

        if " - " in name_part:
            exam_name, material_id = name_part.rsplit(" - ", 1)
        else:
            exam_name = name_part
            material_id = "unknown"

        donem_num = donem_str.replace("Donem ", "")
        new_filename = f"Anadolu - Dönem {donem_num} - {course_name} - Çıkmış Sorular - Raw.json"

        target_dir = os.path.join(JSON_BASE_DIR, donem_str)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        return os.path.join(target_dir, new_filename), exam_name, material_id

    except Exception as e:
        print(f"Error constructing target path for {pdf_path}: {e}")
        return None, None, None

def upload_file_cached(path):
    """Uploads a file using the GenAIFilesManager."""
    try:
        # Extract material_id if possible
        _, _, material_id = get_target_info(path)

        uploaded_file = files_manager.upload_file(
            local_path=path,
            material_id=material_id,
            display_name=os.path.basename(path)
        )
        return uploaded_file.uri
    except Exception as e:
        print(f" Error uploading: {e}")
        return None

def update_json_file(json_path, new_questions, exam_name, material_id):
    """
    Updates the JSON file with new questions.
    Merges based on material_id.
    """
    data = {"questions": []}

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ⚠️  Error reading existing JSON: {e}")

    # Remove existing questions from this material_id
    original_count = len(data["questions"])
    data["questions"] = [q for q in data["questions"] if q.get("material_id") != material_id]
    filtered_count = len(data["questions"])

    if original_count != filtered_count:
        print(f"  Removed {original_count - filtered_count} existing questions for material '{material_id}'")

    # Add new questions and inject metadata
    for q in new_questions:
        q["source"] = exam_name
        q["material_id"] = material_id

        if "exam_question_number" in q and isinstance(q["exam_question_number"], str):
             try:
                 q["exam_question_number"] = int(q["exam_question_number"])
             except:
                 pass

    all_questions = data["questions"] + new_questions

    # Re-assign IDs sequentially
    for i, q in enumerate(all_questions, 1):
        q["id"] = i

    data["questions"] = all_questions

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  ✅ Updated {os.path.basename(json_path)} (Total: {len(all_questions)} questions)")

def find_materials_json(course_name):
    """
    Finds the Materials.json file for the given course.
    """
    search_pattern = os.path.join(JSON_BASE_DIR, "**", f"*{course_name}*Materials.json")
    files = glob.glob(search_pattern, recursive=True)

    if not files:
        return None

    return files[0]

def find_file_by_id(course_name, material_id):
    """
    Finds a file containing the material_id in its name within the course directories.
    Searches across all terms (Donem 1-8).
    """
    for i in range(1, 9):
        term_dir = os.path.join(OUTPUT_DIR, "Anadolu", f"Donem {i}", course_name, "Materyaller")
        if not os.path.exists(term_dir):
            continue

        try:
            files = os.listdir(term_dir)
            for f in files:
                if str(material_id) in f and f.endswith(".pdf"):
                    return os.path.join(term_dir, f)
        except OSError:
            continue

    return None

def process_pdfs_from_materials_json(target_course=None, no_cache=False, target_material_ids=None):
    if not target_course:
        print("Error: Target course must be specified.")
        return

    materials_json_path = find_materials_json(target_course)

    if not materials_json_path:
        print(f"Error: Materials.json not found for course '{target_course}'")
        return

    print(f"Using materials file: {materials_json_path}")

    with open(materials_json_path, 'r', encoding='utf-8') as f:
        try:
            materials_data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to parse Materials.json")
            return

    print(f"Loaded {len(materials_data)} groups from materials file.")

    # Filter for exams
    exam_records = []

    for group in materials_data:
        materials = group.get("Materials", [])
        if not materials:
            continue

        for item in materials:
            item_type = item.get("Type", "")
            if "PAST_EXAMS_" not in item_type:
                continue

            name = item.get("Name", "").strip()
            material_id = str(item.get("MaterialId"))

            if not name or not material_id:
                continue

            # Filter by target material IDs if specified
            if target_material_ids and material_id not in target_material_ids:
                continue

            item["ExamName"] = clean_filename(name) # Keep cleaned name for display/sourcend(item)
            exam_records.append(item)

    print(f"Found {len(exam_records)} exam records.")

    for item in exam_records:
        material_id = str(item.get("MaterialId", "unknown"))
        exam_name = item.get("ExamName")

        # Find the file by ID
        found_path = find_file_by_id(target_course, material_id)

        if not found_path:
            print(f"  ⚠️  File not found for ID {material_id} ({exam_name})")
            continue

        # Extract exam name from filename on disk
        filename_on_disk = os.path.basename(found_path)
        exam_name_full = os.path.splitext(filename_on_disk)[0]

        # Remove material ID from exam name for cleaner source field
        # Format is typically "Exam Name - MaterialID"
        if " - " in exam_name_full and str(material_id) in exam_name_full:
            exam_name = exam_name_full.rsplit(" - ", 1)[0]
        else:
            exam_name = exam_name_full

        json_path, _, _ = get_target_info(found_path)

        if not json_path:
            continue

        # Check if we already have questions for this exam
        if not no_cache and os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

                existing_questions = [q for q in existing_data.get("questions", []) if str(q.get("material_id")) == str(material_id)]

                if len(existing_questions) >= 20:
                    print(f"Skipping {exam_name} (Already has {len(existing_questions)} questions). Use --no-cache to force update.")
                    continue
            except Exception as e:
                print(f"  ⚠️  Error checking cache: {e}")

        print(f"Processing {os.path.basename(found_path)}...")
        print(f"  Exam: {exam_name}")
        print(f"  Material ID: {material_id}")

        # 1. Upload Exam PDF
        exam_uri = upload_file_cached(found_path)
        if not exam_uri:
            print("  Skipping (Exam upload failed)")
            continue

        # 2. Prepare Content
        print("  Generating JSON...", end="", flush=True)

        model = "gemini-flash-latest"

        prompt = f"""
        Bu sınav belgesindeki ({exam_name}) tüm çoktan seçmeli soruları çıkar.
        Bu belgede toplam 20 adet soru bulunmaktadır. Hepsini eksiksiz çıkar.

        Her soru için JSON formatında çıktı ver.

        ÖNEMLİ KURALLAR:
        1. Soru metninin başında ASLA soru numarası (1., 2. gibi) olmamalıdır.
        2. Seçeneklerin başında ASLA şık harfi (A), B) gibi) olmamalıdır.
        3. METİN TEMİZLİĞİ: PDF'ten kaynaklanan gereksiz satır sonlarını (line break) MUTLAKA KALDIR ve boşluk ile değiştir. Cümleler tek bir satırda akıcı olmalı. Sadece maddeli listelerde <br> kullan.
           - YANLIŞ: "Felsefesi, felsefe tarihinde ilk sistemli felsefi<br>düşüncenin kaynağı..."
           - DOĞRU: "Felsefesi, felsefe tarihinde ilk sistemli felsefi düşüncenin kaynağı..."
        4. OLUMSUZLUK VURGUSU: Soru kökündeki "değildir", "olamaz", "yanlıştır", "yoktur", "beklenmez", "söylenemez", "ulaşılamaz" gibi olumsuz ifadelerin altını çizmek için <u> etiketi kullan.
           - Örnek: ...hangisi <u>yanlıştır</u>?
        5. Vurgulamalar için <b>, <u> gibi HTML etiketleri kullan.

        Cevap anahtarı belgenin sonundaysa, doğru cevabı oradan al.
        Eğer cevap anahtarı yoksa, soruyu çözmeye çalış ve en mantıklı cevabı işaretle.
        Eğer cevap anahtarında soru için "İptal" veya benzeri bir ifade varsa, cevabı "X" olarak işaretle ve 'correctIndex' değerini -1 yap.
        'exam_question_number' alanına sorunun belgedeki numarasını yaz (1-20 arası).
        """

        parts = []

        # Add exam PDF
        parts.append(types.Part.from_uri(file_uri=exam_uri, mime_type="application/pdf"))

        # Add prompt
        parts.append(types.Part.from_text(text=prompt))

        contents = [types.Content(role="user", parts=parts)]

        try:
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type = types.Type.OBJECT,
                    required = ["questions"],
                    properties = {
                        "questions": types.Schema(
                            type = types.Type.ARRAY,
                            description = "Sınavdaki tam olarak 20 adet sorunun listesi.",
                            items = types.Schema(
                                type = types.Type.OBJECT,
                                required = ["id", "question", "options", "correctIndex", "exam_question_number"],
                                properties = {
                                    "id": types.Schema(
                                        type = types.Type.INTEGER,
                                        description = "Sorunun sistemdeki benzersiz ve sıralı tam sayı kimliği.",
                                    ),
                                    "question": types.Schema(
                                        type = types.Type.STRING,
                                        description = "HTML formatındaki soru metni. Gereksiz satır sonları kaldırılmış, akıcı metin. Olumsuz ifadeler <u> ile vurgulanmış.",
                                    ),
                                    "options": types.Schema(
                                        type = types.Type.ARRAY,
                                        description = "Soru için sunulan tam olarak 5 adet cevap seçeneği.",
                                        items = types.Schema(
                                            type = types.Type.STRING,
                                        ),
                                    ),
                                    "correctIndex": types.Schema(
                                        type = types.Type.INTEGER,
                                        description = "Doğru seçeneğin 0 tabanlı indeksi (0-4 arası).",
                                    ),
                                    "exam_question_number": types.Schema(
                                        type = types.Type.INTEGER,
                                        description = "Sorunun sınav kitapçığındaki numarası (1-20 arası).",
                                    ),
                                },
                            ),
                        ),
                    },
                ),
            )

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )

            print(" Done.")

            try:
                result = json.loads(response.text)
                new_questions = result.get("questions", [])

                if new_questions:
                    update_json_file(json_path, new_questions, exam_name, material_id)
                else:
                    print("  ⚠️  No questions extracted.")

            except json.JSONDecodeError:
                print(f"  ❌ Failed to parse JSON response.")

        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert exam PDFs to JSON.")
    parser.add_argument("--course", default="Görsel Estetik", help="Target course name")
    parser.add_argument("--no-cache", action="store_true", help="Force re-processing of all files")
    parser.add_argument("--material-ids", help="Comma-separated list of material IDs to process")

    args = parser.parse_args()

    material_ids = None
    if args.material_ids:
        material_ids = [m.strip() for m in args.material_ids.split(",")]

    process_pdfs_from_materials_json(target_course=args.course, no_cache=args.no_cache, target_material_ids=material_ids)
