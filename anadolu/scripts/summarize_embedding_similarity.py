#!/usr/bin/env python3
"""
Create a human-readable summary of embedding similarity analysis results.
"""

import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")
SUMMARY_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_summary.md")

def main():
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group by course
    by_course = {}
    for item in data:
        course = item["q1"]["course"]
        if course not in by_course:
            by_course[course] = []
        by_course[course].append(item)

    # Create summary
    md = "# Benzer Soru Analizi (Embedding Tabanlı)\n\n"
    md += f"**Toplam Benzer Çift:** {len(data)}\n\n"
    md += f"**Benzerlik Eşiği:** 0.85 (Cosine Similarity)\n\n"
    md += "---\n\n"

    for course in sorted(by_course.keys()):
        pairs = by_course[course]
        md += f"## {course}\n\n"
        md += f"**Benzer Çift Sayısı:** {len(pairs)}\n\n"

        # Show top 5
        top_pairs = sorted(pairs, key=lambda x: x["similarity"], reverse=True)[:5]

        for i, pair in enumerate(top_pairs, 1):
            sim = pair["similarity"]
            q1 = pair["q1"]
            q2 = pair["q2"]

            md += f"### {i}. Benzerlik: {sim:.3f}\n\n"
            md += f"**Soru 1** (ID: {q1['id']}, Kaynak: {q1['source']}):\n"
            md += f"> {q1['text'][:200]}...\n\n"
            md += f"**Cevap:** {q1['answer']}\n\n"

            md += f"**Soru 2** (ID: {q2['id']}, Kaynak: {q2['source']}):\n"
            md += f"> {q2['text'][:200]}...\n\n"
            md += f"**Cevap:** {q2['answer']}\n\n"

            if q1['answer'] != q2['answer']:
                md += "⚠️ **FARKLI CEVAPLAR!**\n\n"

            md += "---\n\n"

    with open(SUMMARY_PATH, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Summary saved to {SUMMARY_PATH}")

if __name__ == "__main__":
    main()
