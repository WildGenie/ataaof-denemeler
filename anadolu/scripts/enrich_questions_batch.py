#!/usr/bin/env python3
"""
Enrich exam questions with explanations using Gemini Batch API.
Supports processing multiple courses in a single batch job.
"""

import os
import json
import sys
import time
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tqdm import tqdm

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from libs.genai_files_manager import GenAIFilesManager

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
JSON_BASE_DIR = os.path.join(OUTPUT_DIR, "Anadolu", "json")
BATCH_REQUESTS_FILE = os.path.join(OUTPUT_DIR, "Anadolu", "batch_requests.jsonl")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

# Configure SDK
client = genai.Client(api_key=GEMINI_API_KEY)
files_manager = GenAIFilesManager()

def load_summaries(course_name, donem):
    """Load unit summaries for a course."""
    summaries_dir = os.path.join(OUTPUT_DIR, "Anadolu", f"Donem {donem}", course_name, "Materyaller")

    if not os.path.exists(summaries_dir):
        return {}

    summaries = {}
    for filename in os.listdir(summaries_dir):
        if "Özet" in filename and filename.endswith(".pdf"):
            try:
                if "Ünite Özeti - Ünite" in filename:
                    unit_num = int(filename.split("Ünite Özeti - Ünite")[1].split()[0])
                elif "Ünite" in filename and "Özet" in filename:
                    unit_num = int(filename.split("Ünite")[1].split()[0])
                else:
                    continue
                summaries[unit_num] = os.path.join(summaries_dir, filename)
            except:
                continue
    return summaries

def upload_all_summaries(summaries):
    """Upload all summary PDFs and return their URIs."""
    summary_uris = {}
    for unit_num in sorted(summaries.keys()):
        summary_path = summaries[unit_num]
        try:
            # Extract material_id from filename if possible
            filename = os.path.basename(summary_path)
            material_id = None
            try:
                parts = filename.rsplit(" - ", 1)
                if len(parts) > 1 and parts[1].replace(".pdf", "").isdigit():
                    material_id = parts[1].replace(".pdf", "")
            except:
                pass

            summary_file = files_manager.upload_file(
                local_path=summary_path,
                material_id=material_id,
                display_name=filename
            )
            summary_uris[unit_num] = summary_file.uri
        except Exception as e:
            print(f"    Error uploading summary {unit_num}: {e}")
    return summary_uris

def create_prompt(questions):
    """Create the text prompt for a batch of questions."""
    question_texts = []
    for q in questions:
        # Include metadata in the prompt
        full_text = f"Soru ID: {q['id']}\n"
        full_text += f"Sınav Soru No: {q.get('exam_question_number', 0)}\n"
        full_text += f"Kaynak: {q.get('source', '')}\n"
        full_text += f"Materyal ID: {q.get('material_id', '')}\n"
        full_text += f"Soru Metni: {q['question']}\n"

        options = q.get("options", [])
        correct_idx = q.get("correctIndex")

        for idx, opt in enumerate(options):
            marker = ""
            if idx == correct_idx:
                marker = " <<< BU ŞIK DOĞRU KABUL EDİLECEK"
            full_text += f"{chr(65+idx)}) {opt}{marker}\n"
        question_texts.append(full_text)

    questions_text = "\n\n".join(question_texts)

    prompt = f"""
    Aşağıda ders ünite özetleri ve sınav soruları var.

    Her soru için:
    1. Sorunun hangi üniteye ait olduğunu belirle (UniteNo: 1-8 arası)
    2. Sorunun konusunu (topic) belirle (kısa, 2-5 kelime)
    3. Sorunun doğru cevabını ve neden doğru olduğunu açıklayan detaylı bir açıklama (explanation) yaz.
    4. Sana verilen "Sınav Soru No", "Kaynak" ve "Materyal ID" bilgilerini AYNEN geri döndür.

    ÖNEMLİ:
    - Sana verilen sorudaki "correctIndex" (veya işaretlenmiş şık) KESİN DOĞRUDUR.
    - Eğer özetlerdeki bilgiyle çelişiyor gibi görünse bile, AÇIKLAMAYI BU CEVABA GÖRE YAZ.
    - Cevabın neden o şık olduğunu mantıklı bir şekilde gerekçelendir.

    KURALLAR:
    - UniteNo: Sorunun içeriğine en uygun ünite numarasını belirle (1-8 arası)
    - Açıklama, ünite özetlerindeki bilgileri kullanarak doğru cevabı açıklamalı
    - Açıklama Türkçe, net ve anlaşılır olmalı
    - Topic kısa ve öz olmalı (örn: "Algı Psikolojisi", "Renk Teorisi")
    - Açıklama, sorunun cevabını ve mantığını içermeli
    - exam_question_number, source ve material_id alanları soruda verildiği gibi aynen döndürülmeli.

    SORULAR:
    {questions_text}
    """
    return prompt

def get_donem_for_course(course_name):
    """Find the semester for a course."""
    json_dir = os.path.join(OUTPUT_DIR, "Anadolu", "json")
    for donem_dir in os.listdir(json_dir):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(json_dir, donem_dir)
        for filename in os.listdir(donem_path):
            if f"- {course_name} -" in filename:
                try:
                    return int(donem_dir.split(" ")[1])
                except:
                    pass
    return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich exam questions using Gemini Batch API.")
    parser.add_argument("--courses", help="Comma-separated list of courses")
    parser.add_argument("--problematic-exams-file", help="Path to problematic exams JSON file")
    parser.add_argument("--no-cache", action="store_true", help="Force re-processing")

    args = parser.parse_args()

    target_courses = set()
    if args.courses:
        target_courses.update([c.strip() for c in args.courses.split(",")])

    if args.problematic_exams_file and os.path.exists(args.problematic_exams_file):
        with open(args.problematic_exams_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                target_courses.add(item["course"])

    if not target_courses:
        print("Error: No courses specified.")
        return

    print(f"Preparing batch job for {len(target_courses)} courses...")

    batch_requests = []
    course_data_map = {} # Store loaded JSON data to update later: key=(course, donem)

    for course_name in target_courses:
        donem = get_donem_for_course(course_name)
        if not donem:
            print(f"  ⚠️ Could not determine semester for {course_name}, skipping.")
            continue

        # Paths
        raw_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}", f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Raw.json")
        enriched_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}", f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json")

        if not os.path.exists(raw_json_path):
            print(f"  ⚠️ Raw JSON not found for {course_name}")
            continue

        # Load Data
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        questions = raw_data.get("questions", [])

        # Merge existing enrichments if available and not --no-cache
        existing_questions = []
        if not args.no_cache and os.path.exists(enriched_json_path):
            try:
                with open(enriched_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_questions = existing_data.get("questions", [])
            except:
                pass

        if len(existing_questions) == len(questions):
            questions = existing_questions
        elif len(existing_questions) > 0:
            # Simple merge by index
            for i in range(min(len(questions), len(existing_questions))):
                if existing_questions[i].get("explanation"):
                    questions[i] = existing_questions[i]

        course_data_map[(course_name, donem)] = questions

        # Identify questions needing enrichment
        questions_to_process = []
        indices_to_process = []
        for i, q in enumerate(questions):
            if args.no_cache or not (q.get("UniteNo") and q.get("topic") and q.get("explanation")):
                questions_to_process.append(q)
                indices_to_process.append(i)

        if not questions_to_process:
            print(f"  {course_name}: All questions enriched.")
            continue

        print(f"  {course_name}: {len(questions_to_process)} questions to enrich.")

        # Load and Upload Summaries
        summaries = load_summaries(course_name, donem)
        if not summaries:
            print(f"  ⚠️ No summaries found for {course_name}. Skipping.")
            continue

        summary_uris = upload_all_summaries(summaries)

        # Create Batches
        batch_size = 20
        for i in range(0, len(questions_to_process), batch_size):
            batch = questions_to_process[i:i+batch_size]
            batch_indices = indices_to_process[i:i+batch_size]

            # Create temp batch with IDs 0..N for the prompt
            temp_batch = []
            for idx, q in enumerate(batch):
                temp_q = q.copy()
                temp_q['id'] = idx
                temp_batch.append(temp_q)

            prompt_text = create_prompt(temp_batch)

            # Construct Request
            parts = []
            for unit_num in sorted(summary_uris.keys()):
                parts.append({"file_data": {"file_uri": summary_uris[unit_num], "mime_type": "application/pdf"}})
            parts.append({"text": prompt_text})

            # Define Schema (Simplified for JSONL)
            response_schema = {
                "type": "OBJECT",
                "required": ["enrichments"],
                "properties": {
                    "enrichments": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "required": ["question_id", "UniteNo", "topic", "explanation", "exam_question_number", "source", "material_id"],
                            "properties": {
                                "question_id": {"type": "INTEGER"},
                                "UniteNo": {"type": "INTEGER"},
                                "topic": {"type": "STRING"},
                                "explanation": {"type": "STRING"},
                                "exam_question_number": {"type": "INTEGER"},
                                "source": {"type": "STRING"},
                                "material_id": {"type": "STRING"}
                            }
                        }
                    }
                }
            }

            request_body = {
                "contents": [{"role": "user", "parts": parts}],
                "generation_config": {
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                }
            }

            # Key format: course|donem|start_index
            # We store start_index to map back to batch_indices
            key = f"{course_name}|{donem}|{i}"

            batch_requests.append({
                "key": key,
                "request": request_body
            })

    if not batch_requests:
        print("No requests to process.")
        return

    print(f"\nCreated {len(batch_requests)} batch requests.")

    # Write JSONL
    with open(BATCH_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        for req in batch_requests:
            f.write(json.dumps(req) + "\n")

    # Upload JSONL
    print("Uploading batch request file...")
    uploaded_file = client.files.upload(
        file=BATCH_REQUESTS_FILE,
        config=types.UploadFileConfig(mime_type='application/jsonl')
    )

    # Wait for file to be active
    while True:
        uploaded_file = client.files.get(name=uploaded_file.name)
        if uploaded_file.state.name == "ACTIVE":
            break
        elif uploaded_file.state.name == "FAILED":
            print("Error: Batch file upload failed.")
            return
        time.sleep(1)

    # Create Batch Job
    print("Creating batch job...")
    batch_job = client.batches.create(
        model="gemini-flash-latest",
        src=uploaded_file.name,
        config=types.CreateBatchJobConfig(display_name=f"enrichment_job_{int(time.time())}")
    )

    print(f"Batch Job Created: {batch_job.name}")
    print("Waiting for completion (this may take a while)...")

    # Poll
    pbar = tqdm(total=100, desc="Processing") # Fake progress initially
    completed_states = ["JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]

    while True:
        job = client.batches.get(name=batch_job.name)
        state = str(job.state) # Ensure string comparison

        if state in completed_states:
            break

        # Update description with state
        pbar.set_description(f"Status: {state}")
        time.sleep(30)

    pbar.close()
    print(f"Job finished with state: {state}")

    if state != "JOB_STATE_SUCCEEDED":
        print("Job failed or cancelled.")
        if hasattr(job, 'error'):
            print(f"Error: {job.error}")
        return

    # Download Results
    print("Downloading results...")
    result_filename = job.dest.file_name
    results_content = client.files.download(file=result_filename).decode('utf-8')

    # Process Results
    print("Processing results...")
    success_count = 0

    # Parse JSONL results
    results_map = {} # key -> result_dict
    for line in results_content.splitlines():
        if not line: continue
        res = json.loads(line)
        # res has 'custom_id' (which maps to our 'key') and 'response'
        # Wait, the SDK example says the output JSONL has 'custom_id' matching the input 'custom_id' (or 'key'?)
        # The input used "key", the output usually uses "custom_id" or the same key field.
        # Let's check the SDK output format. The example output shows the order matches or keys match.
        # The Python SDK example uses "key" in input.
        # The output example shows: `{"custom_id": "request-1", "response": ...}` usually.
        # But let's assume it preserves the key field or uses custom_id.
        # Actually, the user provided example output:
        # `{"recipe_name": ...}` directly in inline response.
        # For file output, it says "The result file is also a JSONL file".
        # It usually wraps it. Let's look at `res`.
        # It likely has `custom_id` matching our `key`.

        key = res.get("custom_id") # Standard Batch API field
        if not key and "key" in res: key = res["key"] # Fallback

        if key:
            results_map[key] = res

    # Update Questions
    for key, res in results_map.items():
        try:
            course_name, donem_str, start_idx_str = key.split("|")
            donem = int(donem_str)
            start_idx = int(start_idx_str)

            questions = course_data_map.get((course_name, donem))
            if not questions: continue

            # Extract enrichments
            if "response" in res and "candidates" in res["response"]:
                text = res["response"]["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(text)
                enrichments = data.get("enrichments", [])

                # We need to map these back to the original questions.
                # We know the start_idx in the filtered list (questions_to_process).
                # But wait, we need the indices in the ORIGINAL list.
                # We didn't store the mapping in the key, only the start index in the *processed* list?
                # No, in the loop above: `for i in range(0, len(questions_to_process), batch_size):`
                # `i` is the index in `questions_to_process`.
                # We need to reconstruct `indices_to_process` to map back.

                # Re-calculate indices_to_process for this course to ensure consistency
                # (This assumes the list hasn't changed, which it shouldn't have)
                q_indices = []
                for idx, q in enumerate(questions):
                    if args.no_cache or not (q.get("UniteNo") and q.get("topic") and q.get("explanation")):
                        q_indices.append(idx)

                batch_indices = q_indices[start_idx : start_idx + 20]

                for e in enrichments:
                    local_id = e.get("question_id") # 0..19
                    if local_id is not None and local_id < len(batch_indices):
                        global_idx = batch_indices[local_id]

                        # Update question
                        questions[global_idx]["UniteNo"] = e.get("UniteNo")
                        questions[global_idx]["topic"] = e.get("topic")
                        questions[global_idx]["explanation"] = e.get("explanation")
                        success_count += 1

        except Exception as e:
            print(f"Error processing result for key {key}: {e}")

    # Save Updated Files
    print("Saving updated files...")
    for (course_name, donem), questions in course_data_map.items():
        enriched_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}", f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json")
        try:
            with open(enriched_json_path, 'w', encoding='utf-8') as f:
                json.dump({"questions": questions}, f, indent=4, ensure_ascii=False)
            print(f"  ✅ Updated: {os.path.basename(enriched_json_path)}")
        except Exception as e:
            print(f"  ❌ Error saving {course_name}: {e}")

    print(f"\nSuccessfully enriched {success_count} questions.")

if __name__ == "__main__":
    main()
