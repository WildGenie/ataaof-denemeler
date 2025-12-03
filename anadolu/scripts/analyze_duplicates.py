#!/usr/bin/env python3
"""
Analyze duplicate questions in "Çıkmış Sorular" (Past Exams).
Scans output/Anadolu/json/Donem X/ directories for *Çıkmış Sorular - Enriched.json files.
Identifies questions with identical text and generates a report.
"""

import os
import json
import re
from collections import defaultdict

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "duplicate_analysis.md")

def normalize_text(text):
    """Normalize text for comparison."""
    if not text:
        return ""
    # Lowercase, remove punctuation, collapse whitespace
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Starting duplicate question analysis...")

    if not os.path.exists(JSON_DIR):
        print(f"Error: JSON directory not found at {JSON_DIR}")
        return

    all_questions = defaultdict(list)
    file_count = 0
    question_count = 0

    # Scan directories
    for donem_dir in sorted(os.listdir(JSON_DIR)):
        donem_path = os.path.join(JSON_DIR, donem_dir)
        if not os.path.isdir(donem_path) or not donem_dir.startswith("Donem"):
            continue

        print(f"Scanning {donem_dir}...")

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" in filename:
                file_path = os.path.join(donem_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    questions = data.get("questions", [])
                    course_name = filename.split(" - ")[2] # Anadolu - Dönem X - Course Name - ...

                    for q in questions:
                        q_text = q.get("question")
                        if not q_text:
                            continue

                        norm_text = normalize_text(q_text)
                        all_questions[norm_text].append({
                            "course": course_name,
                            "source": q.get("source", "Unknown"),
                            "id": q.get("id"),
                            "original_text": q_text,
                            "options": q.get("options", []),
                            "correctIndex": q.get("correctIndex")
                        })
                        question_count += 1

                    file_count += 1
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    print(f"Scanned {file_count} files, {question_count} questions.")

    # Identify duplicates
    duplicates = {k: v for k, v in all_questions.items() if len(v) > 1}
    print(f"Found {len(duplicates)} unique questions appearing multiple times.")

    # Generate Report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write("# 🔄 Mükerrer Soru Analizi\n\n")
        f.write(f"**Tarama Tarihi:** {os.popen('date').read().strip()}\n")
        f.write(f"**Taranan Dosya Sayısı:** {file_count}\n")
        f.write(f"**Toplam Soru Sayısı:** {question_count}\n")
        f.write(f"**Mükerrer Soru Grubu Sayısı:** {len(duplicates)}\n\n")
        f.write("> **Not:** Sadece cevap metinlerinin farklı olduğu durumlar '⚠️ (Farklı Cevap!)' olarak işaretlenmiştir. Şıkların yerinin değişmesi sorun teşkil etmez.\n\n")
        f.write("---\n\n")

        # Sort by number of occurrences (descending)
        sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)

        for norm_text, occurrences in sorted_duplicates:
            first_occurrence = occurrences[0]
            question_text = first_occurrence["original_text"]
            course_name = first_occurrence["course"]

            # Check if there are any actual mismatches in this group
            has_mismatch = False
            first_correct_text = first_occurrence["options"][first_occurrence["correctIndex"]] if 0 <= first_occurrence["correctIndex"] < len(first_occurrence["options"]) else ""

            for occ in occurrences[1:]:
                current_correct_text = occ["options"][occ["correctIndex"]] if 0 <= occ["correctIndex"] < len(occ["options"]) else ""
                if normalize_text(first_correct_text) != normalize_text(current_correct_text):
                    has_mismatch = True
                    break

            # Optional: Only show groups with mismatches?
            # The user asked to analyze duplicates, but implied focus on problems.
            # Let's show all, but highlight problems clearly.

            icon = "⚠️" if has_mismatch else "✅"

            f.write(f"### {icon} {course_name}: {len(occurrences)} Kez Tekrarlandı\n\n")
            f.write(f"**Soru:** {question_text}\n\n")

            f.write("| Kaynak | ID | Cevap |\n")
            f.write("| --- | --- | --- |\n")

            for occ in occurrences:
                # Get correct answer text for both
                first_correct_text = first_occurrence["options"][first_occurrence["correctIndex"]] if 0 <= first_occurrence["correctIndex"] < len(first_occurrence["options"]) else ""
                current_correct_text = occ["options"][occ["correctIndex"]] if 0 <= occ["correctIndex"] < len(occ["options"]) else ""

                # Normalize for comparison
                answer_match = normalize_text(first_correct_text) == normalize_text(current_correct_text)

                # Check options content (ignoring order)
                first_opts_set = set(normalize_text(o) for o in first_occurrence["options"])
                current_opts_set = set(normalize_text(o) for o in occ["options"])
                options_content_match = first_opts_set == current_opts_set

                note = ""
                if not answer_match:
                     note = " ⚠️ (Farklı Cevap!)"
                elif not options_content_match:
                     note = " (Farklı Şık İçeriği)"

                correct_answer = current_correct_text if current_correct_text else "Hata"

                f.write(f"| {occ['source']} | {occ['id']} | {correct_answer}{note} |\n")

            f.write("\n---\n\n")

    print(f"Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    main()
