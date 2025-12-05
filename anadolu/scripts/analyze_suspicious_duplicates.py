#!/usr/bin/env python3
"""
Analyze questions marked as duplicates but having significantly different options.
This helps identify false positives where question text is similar but options differ (indicating different questions).

Generates a Markdown report: output/Anadolu/suspicious_duplicates_report.md
"""

import os
import json
import difflib
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
REPORT_FILE = os.path.join(PROJECT_ROOT, "output", "Anadolu", "suspicious_duplicates_report.md")

def normalize_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_options_similarity(opts1, opts2):
    """
    Calculate similarity between two lists of options.
    Returns a score between 0.0 and 1.0.
    Logic: For each option in opts1, find the best match in opts2. Average the best match scores.
    """
    if not opts1 or not opts2:
        return 0.0

    # Normalize options
    norm1 = [normalize_text(o) for o in opts1]
    norm2 = [normalize_text(o) for o in opts2]

    total_score = 0
    for o1 in norm1:
        best_match = 0
        for o2 in norm2:
            sim = difflib.SequenceMatcher(None, o1, o2).ratio()
            if sim > best_match:
                best_match = sim
        total_score += best_match

    return total_score / len(norm1)

def main():
    print("Analyzing suspicious duplicates (similar text, different options)...")

    suspicious_cases = []
    total_checked = 0

    for donem_dir in sorted(os.listdir(JSON_DIR)):
        if not donem_dir.startswith("Donem"): continue
        donem_path = os.path.join(JSON_DIR, donem_dir)

        for filename in os.listdir(donem_path):
            if "Çıkmış Sorular - Enriched.json" not in filename: continue

            file_path = os.path.join(donem_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                questions = data.get("questions", [])
                q_map = {q["id"]: q for q in questions}

                for q in questions:
                    if q.get("is_duplicate"):
                        total_checked += 1
                        root_id = q.get("duplicate_of")

                        # Find root (handle chains if any, though finalize script tried to flatten)
                        root = q_map.get(root_id)
                        if not root: continue

                        # Calculate option similarity
                        opts1 = q.get("options", [])
                        opts2 = root.get("options", [])

                        sim_score = calculate_options_similarity(opts1, opts2)

                        # Threshold: If options are less than 60% similar, flag it.
                        # Exact text matches usually have identical options (sim=1.0).
                        # Fuzzy matches might have different options.
                        if sim_score < 0.60:
                            suspicious_cases.append({
                                "file": filename,
                                "q_id": q.get("id"),
                                "root_id": root_id,
                                "q_text": q.get("question"),
                                "root_text": root.get("question"),
                                "q_opts": opts1,
                                "root_opts": opts2,
                                "sim_score": sim_score,
                                "reason": q.get("duplication_reason", "Unknown")
                            })

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Generate Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Şüpheli Duplicate Raporu\n\n")
        f.write("Bu rapor, `is_duplicate` olarak işaretlenmiş ancak şıkları (options) birbirinden önemli ölçüde farklı olan soruları listeler.\n")
        f.write("Bu soruların 'Duplicate' olup olmadığı tekrar incelenmelidir.\n\n")
        f.write(f"**Toplam Taranan Duplicate Sayısı:** {total_checked}\n")
        f.write(f"**Bulunan Şüpheli Vaka Sayısı:** {len(suspicious_cases)}\n\n")

        if not suspicious_cases:
            f.write("✅ Hiçbir şüpheli vaka bulunamadı. Tüm duplicate'lerin şıkları uyumlu.\n")
        else:
            for case in suspicious_cases:
                f.write(f"## Dosya: {case['file']}\n")
                f.write(f"**Duplicate ID:** {case['q_id']} -> **Root ID:** {case['root_id']}\n")
                f.write(f"**Sebep:** {case['reason']} (Option Similarity: {case['sim_score']:.2f})\n\n")

                f.write("| Tip | Soru Metni | Şıklar |\n")
                f.write("| --- | --- | --- |\n")
                f.write(f"| **Root** | {case['root_text']} | {', '.join(case['root_opts'])} |\n")
                f.write(f"| **Dup** | {case['q_text']} | {', '.join(case['q_opts'])} |\n\n")
                f.write("---\n")

    print(f"Analysis complete. Found {len(suspicious_cases)} suspicious cases.")
    print(f"Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    main()
