#!/usr/bin/env python3
"""
Enrich exam questions with explanations and topics.
Uses all unit summaries to generate detailed explanations for each question.
"""

import os
import json
import sys
import time
from dotenv import load_dotenv
import google.generativeai as genai_old  # For file upload
from google import genai
from google.genai import types

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
JSON_BASE_DIR = os.path.join(OUTPUT_DIR, "Anadolu", "json")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

# Configure old SDK for file upload
genai_old.configure(api_key=GEMINI_API_KEY)

# Configure new SDK for content generation
client = genai.Client(api_key=GEMINI_API_KEY)

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
    print("  Uploading unit summaries...")
    summary_uris = {}

    for unit_num in sorted(summaries.keys()):
        summary_path = summaries[unit_num]
        print(f"    Unit {unit_num}...", end="", flush=True)

        try:
            summary_file = genai_old.upload_file(path=summary_path)

            while summary_file.state.name == "PROCESSING":
                time.sleep(1)
                summary_file = genai_old.get_file(summary_file.name)

            if summary_file.state.name == "FAILED":
                print(" Failed.")
                continue

            summary_uris[unit_num] = summary_file.uri
            print(" Done.")
        except Exception as e:
            print(f" Error: {e}")

    return summary_uris

def enrich_questions_batch(questions, summary_uris):
    """
    Enrich a batch of questions with explanations using all unit summaries.

    Args:
        questions: List of question dicts
        summary_uris: Dict mapping unit_num to summary URI

    Returns:
        Dict mapping question_id to enrichment data (topic, explanation)
    """
    # Prepare question list with options and correct answer marked
    question_texts = []
    for q in questions:
        full_text = f"Soru {q['id']}: {q['question']}\n"
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

    SORULAR:
    {questions_text}
    """

    try:
        # Prepare content with all summaries
        parts = []

        # Add all summary PDFs
        for unit_num in sorted(summary_uris.keys()):
            parts.append(types.Part.from_uri(file_uri=summary_uris[unit_num], mime_type="application/pdf"))

        # Add prompt
        parts.append(types.Part.from_text(text=prompt))

        contents = [types.Content(role="user", parts=parts)]

        # Define response schema
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                required=["enrichments"],
                properties={
                    "enrichments": types.Schema(
                        type=types.Type.ARRAY,
                        description="Enrichment data for each question",
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            required=["question_id", "UniteNo", "topic", "explanation"],
                            properties={
                                "question_id": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="ID of the question"
                                ),
                                "UniteNo": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Unit number (1-8) that this question belongs to"
                                ),
                                "topic": types.Schema(
                                    type=types.Type.STRING,
                                    description="Short topic/subject of the question (2-5 words)"
                                ),
                                "explanation": types.Schema(
                                    type=types.Type.STRING,
                                    description="Detailed explanation of the correct answer in Turkish"
                                )
                            }
                        )
                    )
                }
            )
        )

        print(f"  Generating enrichments for {len(questions)} questions...", end="", flush=True)
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=contents,
            config=generate_content_config
        )

        print(" Done.")

        result = json.loads(response.text)

        # Handle both dict and list responses
        if isinstance(result, list):
            enrichments = result
        elif isinstance(result, dict):
            enrichments = result.get("enrichments", [])
        else:
            print(f"  ⚠️  Unexpected response type: {type(result)}")
            return {}

        # Convert to dict mapping question_id to enrichment
        enrichment_map = {}
        for e in enrichments:
            if not isinstance(e, dict):
                continue

            qid = e.get("question_id")
            if qid:
                enrichment_map[qid] = {
                    "UniteNo": e.get("UniteNo"),
                    "topic": e.get("topic"),
                    "explanation": e.get("explanation")
                }

        return enrichment_map

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def enrich_course_questions(course_name, donem, no_cache=False):
    """
    Enrich all questions for a course with explanations.
    """
    # Find Raw JSON file
    raw_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}",
                                  f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Raw.json")

    if not os.path.exists(raw_json_path):
        print(f"Raw JSON not found: {raw_json_path}")
        return

    # Output path
    enriched_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}",
                                       f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json")

    # Check if already enriched (and complete)
    if not no_cache and os.path.exists(enriched_json_path):
        try:
            with open(enriched_json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

            existing_questions = existing_data.get("questions", [])

            # Check if all questions have enrichment data
            all_enriched = all(
                q.get("UniteNo") is not None and
                q.get("topic") and
                q.get("explanation")
                for q in existing_questions
            )

            if all_enriched and len(existing_questions) > 0:
                print(f"Already enriched (use --no-cache to force): {course_name}\n")
                return
            else:
                print(f"Incomplete enrichment found. Re-processing: {course_name}")
        except Exception as e:
            print(f"Error reading existing enriched file: {e}")

    print(f"Enriching: {course_name} (Dönem {donem})")

    # Load existing enriched data if available to preserve progress
    existing_questions = []
    if os.path.exists(enriched_json_path):
        try:
            with open(enriched_json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_questions = existing_data.get("questions", [])
        except:
            pass

    # Load raw questions
    with open(raw_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    raw_questions = raw_data.get("questions", [])

    if not raw_questions:
        print("  No questions found.")
        return

    # Merge existing enrichments into raw questions
    # We assume the order is the same, or we match by question text/options if needed.
    # For simplicity, we'll use the index if lengths match, otherwise we might need a smarter merge.
    # But typically Raw and Enriched should match in length and order.

    questions = raw_questions
    if len(existing_questions) == len(raw_questions):
        questions = existing_questions
    elif len(existing_questions) > 0:
        print("  Warning: Mismatch in question counts between Raw and Enriched. Using Enriched where possible.")
        # Try to map by some unique property if possible, but here we'll just use what we have
        # Or better, just stick to Raw and try to copy over enrichments?
        # Let's assume we use Raw as base and copy enrichments if text matches
        for i, rq in enumerate(questions):
            for eq in existing_questions:
                if rq.get("SoruMetni") == eq.get("SoruMetni"):
                    if eq.get("explanation"):
                        questions[i] = eq
                    break

    # Identify questions that need enrichment
    questions_to_process = []
    indices_to_process = []

    for i, q in enumerate(questions):
        if not (q.get("UniteNo") and q.get("topic") and q.get("explanation")):
            questions_to_process.append(q)
            indices_to_process.append(i)

    if not questions_to_process:
        print("  All questions are already enriched.")
        # Ensure we save the file anyway if it was just loaded from Raw
        if not os.path.exists(enriched_json_path):
             with open(enriched_json_path, 'w', encoding='utf-8') as f:
                json.dump({"questions": questions}, f, indent=4, ensure_ascii=False)
        return

    print(f"  {len(questions_to_process)} questions need enrichment out of {len(questions)}.")

    # Load summaries
    summaries = load_summaries(course_name, donem)

    if not summaries:
        print("  No summaries found. Skipping enrichment.")
        return

    print(f"  Found {len(summaries)} unit summaries.")

    # Upload all summaries once
    summary_uris = upload_all_summaries(summaries)

    if not summary_uris:
        print("  Failed to upload summaries.")
        return

    # Process questions in batches
    batch_size = 20

    from tqdm import tqdm

    # Calculate total batches
    total_batches = (len(questions_to_process) + batch_size - 1) // batch_size

    with tqdm(total=len(questions_to_process), desc="Enriching Questions", unit="q") as pbar:
        for i in range(0, len(questions_to_process), batch_size):
            batch = questions_to_process[i:i+batch_size]
            batch_indices = indices_to_process[i:i+batch_size]

            # print(f"\n  Batch {i//batch_size + 1}/{total_batches}") # tqdm handles this

            # Prepare batch with temporary IDs for mapping
            # The API returns enrichments keyed by 'question_id'.
            # We need to ensure these IDs map back to our batch indices (0..N).
            temp_batch = []
            for idx, q in enumerate(batch):
                temp_q = q.copy()
                temp_q['id'] = idx # 0, 1, 2...
                temp_batch.append(temp_q)

            try:
                batch_enrichments = enrich_questions_batch(temp_batch, summary_uris)
            except Exception as e:
                print(f"\n❌ Critical Error in batch {i//batch_size + 1}: {e}")
                import traceback
                traceback.print_exc()
                batch_enrichments = {}

            # Update main questions list immediately
            for local_id, data in batch_enrichments.items():
                try:
                    local_idx = int(local_id)
                    if 0 <= local_idx < len(batch_indices):
                        global_idx = batch_indices[local_idx]
                        questions[global_idx].update(data)
                except ValueError:
                    continue

            # Save progress after each batch
            try:
                with open(enriched_json_path, 'w', encoding='utf-8') as f:
                    json.dump({"questions": questions}, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"\n❌ Error saving progress: {e}")

            # print(f"  Saved progress to {os.path.basename(enriched_json_path)}")

            pbar.update(len(batch))

            # Rate limiting
            time.sleep(3)
    enriched_questions = []
    enriched_count = len([q for q in questions if q.get('explanation')])
    print(f"\n  ✅ Saved: {enriched_json_path}")
    print(f"  Enriched {enriched_count}/{len(questions)} questions with explanations.\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich exam questions with explanations.")
    parser.add_argument("--course", required=True, help="Course name")
    parser.add_argument("--donem", type=int, required=True, help="Semester number (1-8)")
    parser.add_argument("--no-cache", action="store_true", help="Force re-processing")

    args = parser.parse_args()

    enrich_course_questions(args.course, args.donem, args.no_cache)
