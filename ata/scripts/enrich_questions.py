#!/usr/bin/env python3
"""
Enrich ATA AÖF questions using Gemini AI (Production Version).
Based on the structure of ata/fetch.py and supporting libraries.
Does NOT use GenAIFilesManager/tracker.
"""

import os
import json
import sys
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.ata_lib import DERSLER_FILE, OUTPUT_DIR, JSON_DIR

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not found. Please install it.")
    sys.exit(1)

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

class AtaEnricher:
    def __init__(self, no_cache=False):
        self.output_root = OUTPUT_DIR
        self.no_cache = no_cache
        self.json_dir = JSON_DIR

    def get_filename_prefix(self, course):
        # Replicated from pipeline.py logic approx
        return "ATA-AÖF"

    def get_safe_course_name(self, course):
        # Simple safe name logic
        name = course.get("CourseName", "")
        return name.replace("/", "-").replace(":", "").strip()

    def load_summary_file(self, course_name, donem):
        """Load the single unit summary PDF for a course."""
        materials_dir = os.path.join(self.output_root, f"Donem {donem}", course_name, "Materyaller")
        summary_path = os.path.join(materials_dir, "Ünite Özeti.pdf")

        if os.path.exists(summary_path):
            return summary_path
        return None

    def upload_summary_direct(self, path):
        """Uploads the summary PDF directly to Gemini without tracking."""
        if not path:
            return None

        display_name = os.path.basename(os.path.dirname(os.path.dirname(path))) + " - Ünite Özeti"

        try:
            with open(path, "rb") as f:
                response = client.files.upload(
                    file=f,
                    config=types.UploadFileConfig(display_name=display_name)
                )

            # Wait for ACTIVE state
            # Simple retry mechanism
            for _ in range(10):
                file_obj = client.files.get(name=response.name)
                if file_obj.state.name == "ACTIVE":
                    return file_obj.uri
                elif file_obj.state.name == "FAILED":
                    return None
                time.sleep(2)

            return None # Timeout or not ready
        except Exception:
            return None

    def enrich_batch(self, questions, summary_uri):
        """
        Enrich a list of questions using the summary URI.
        """
        question_texts = []
        for q in questions:
            full_text = f"Soru {q.get('SoruID', q.get('id', '?'))}: {q.get('SoruMetni', q.get('question'))}\n"
            options = q.get("Cevaplar", q.get("options", []))
            correct_idx = q.get("DogruCevap", q.get("correctIndex"))

            c_idx = -1
            if isinstance(correct_idx, int):
                c_idx = correct_idx
            elif isinstance(correct_idx, str):
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
        - Açıklamada önemli kavramları, tanımları veya anahtar kelimeleri <b>kalın</b> (bold) html etiketiyle vurgula.
        - Gerekirse yeni satır için <br> kullan.

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
                                    "question_id": types.Schema(type=types.Type.STRING),
                                    "UniteNo": types.Schema(type=types.Type.INTEGER),
                                    "topic": types.Schema(type=types.Type.STRING),
                                    "explanation": types.Schema(type=types.Type.STRING)
                                }
                            )
                        )
                    }
                )
            )

            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=contents,
                config=generate_content_config
            )

            return json.loads(response.text)

        except Exception:
            return {}

    def process_course(self, course, tqdm_position=0):
        course_name = course.get("CourseName")
        donem_raw = course.get("Donem")
        try:
            donem = int(donem_raw)
        except:
            return # Skip invalid course

        safe_name = self.get_safe_course_name(course)
        prefix = self.get_filename_prefix(course)

        # Target Files
        json_donem_dir = os.path.join(self.json_dir, f"Donem {donem}")

        # We work on "Alıştırma Soruları.json" (Enriched version) OR create one from Raw/Base
        # Actually ATA structure saves "Alıştırma Soruları.json" directly.
        # We should enrich the existing file "in-place" or save as new?
        # Standard: overwrite/augment "Alıştırma Soruları.json"

        base_filename = f"{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları.json"
        json_path = os.path.join(json_donem_dir, base_filename)

        if not os.path.exists(json_path):
            return # Nothing to enrich

        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        if not questions:
            print(f"No questions found for {course_name}")
            return

        # Check if already enriched
        # We work ONLY on questions that lack an explanation.
        needs_enrichment = []
        skipped_count = 0

        for q in questions:
            # Skip if it has an explanation AND we are not forcing no-cache
            if not self.no_cache and (q.get("Aciklama") or q.get("explanation")):
                skipped_count += 1
                continue
            needs_enrichment.append(q)

        if needs_enrichment:
            print(f"Enriching {course_name}: {len(needs_enrichment)} new, {skipped_count} skipped.")

            # Load Summary
            summary_path = self.load_summary_file(course_name, donem)
            summary_uri = None
            if summary_path:
                 summary_uri = self.upload_summary_direct(summary_path)

            # Group by Unit
            from collections import defaultdict
            questions_by_unit = defaultdict(list)
            for q in needs_enrichment:
                # Default to 'General' if no unit found
                u = q.get("Unite", "General")
                questions_by_unit[u].append(q)

            print(f"  > Processing {len(questions_by_unit)} units in parallel...")

            # Helper to process a unit batch
            def process_unit_batch(unit_key, batch_questions):
                results_list = []
                batch_size = 20
                for i in range(0, len(batch_questions), batch_size):
                    sub_batch = batch_questions[i:i+batch_size]
                    res = self.enrich_batch(sub_batch, summary_uri)
                    if res and "enrichments" in res:
                        results_list.extend(res["enrichments"])
                    time.sleep(1)
                return results_list

            # Run parallel execution for units
            all_enrichments = []
            # Max workers limited to avoid hitting API limits too hard
            with ThreadPoolExecutor(max_workers=min(len(questions_by_unit), 15)) as executor:
                futures = {executor.submit(process_unit_batch, u, qs): u for u, qs in questions_by_unit.items()}

                for future in as_completed(futures):
                    try:
                        unit_results = future.result()
                        all_enrichments.extend(unit_results)
                    except Exception as e:
                        print(f"Error processing unit batch: {e}")

            # Map back results
            enrichment_map = {str(e.get("question_id")): e for e in all_enrichments}

            # Update objects in memory
            updated_count = 0
            for q in questions:
                q_id = str(q.get("SoruID", q.get("id")))
                if q_id in enrichment_map:
                    data = enrichment_map[q_id]
                    q["Aciklama"] = data.get("explanation")
                    q["Konu"] = data.get("topic")
                    if not q.get("Unite"):
                        q["Unite"] = data.get("UniteNo")
                    updated_count += 1

            print(f"  > Received {updated_count} enrichments.")

            # PRIORITY SAVE: Save external explanations immediately
            self.save_external_explanations(questions, donem, safe_name, prefix)

            # Save to main JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=4)
        else:
            print(f"Skipping enrichment for {course_name}: All questions already enriched.")
            # Ensure external file exists even if skipped
            self.save_external_explanations(questions, donem, safe_name, prefix)

    def save_external_explanations(self, questions, donem, safe_name, prefix):
        """Helper to save explanations to data/aciklamalar"""
        explanation_export = []
        for q in questions:
            if q.get("Aciklama"):
                explanation_export.append({
                    "SoruID": q.get("SoruID"),
                    "Aciklama": q.get("Aciklama")
                })

        if explanation_export:
            # Save directly to JSON Directory: output/ATA-AÖF/json/Donem X

            json_donem_dir = os.path.join(self.json_dir, f"Donem {donem}")
            if not os.path.exists(json_donem_dir):
                os.makedirs(json_donem_dir)

            target_filename = f"{prefix} - Dönem {donem} - {safe_name} - Alıştırma Soruları - Cevaplar.json"
            target_path = os.path.join(json_donem_dir, target_filename)

            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(explanation_export, f, ensure_ascii=False, indent=4)
            # print(f"Saved answers to: {target_filename}")

        # After processing all batches for the course, save the explanations to data/aciklamalar

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ATA AÖF Soru Zenginleştirici")
    parser.add_argument("--course", help="Process only specific course")
    parser.add_argument("--donem", type=int, help="Process only specific semester")
    parser.add_argument("--parallel", type=int, default=1, help="Parallel workers")
    parser.add_argument("--no-cache", action="store_true", help="Force re-enrichment")

    args = parser.parse_args()

    if not os.path.exists(DERSLER_FILE):
        print("Dersler file not found.")
        return

    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # Filter
    filtered_courses = []
    for c in courses:
        if args.course and args.course.lower() not in c.get("CourseName", "").lower():
            continue
        if args.donem and int(c.get("Donem", 0)) != args.donem:
            continue
        filtered_courses.append(c)

    print(f"Processing {len(filtered_courses)} courses for enrichment...")

    if args.parallel > 1:
        # Multi-threaded
        enricher = AtaEnricher(no_cache=args.no_cache)
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = [executor.submit(enricher.process_course, c) for c in filtered_courses]
            for _ in tqdm(as_completed(futures), total=len(filtered_courses)):
                pass
    else:
        # Sequential
        enricher = AtaEnricher(no_cache=args.no_cache)
        for c in tqdm(filtered_courses):
            enricher.process_course(c)

if __name__ == "__main__":
    main()
