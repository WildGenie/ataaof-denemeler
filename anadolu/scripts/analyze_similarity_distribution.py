#!/usr/bin/env python3
"""
Analyze the distribution of similarity scores to determine optimal thresholds.
"""

import json
import sys
import os
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")

def main():
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Analyze score distribution
    score_ranges = {
        "1.000 (Tam Eşleşme)": 0,
        "0.99-0.999 (Neredeyse Aynı)": 0,
        "0.95-0.989 (Çok Benzer)": 0,
        "0.90-0.949 (Benzer)": 0,
        "0.85-0.899 (Orta Benzer)": 0,
        "< 0.85": 0
    }

    exact_matches = []
    near_duplicates = []  # 0.95-0.999
    similar_questions = []  # 0.85-0.949

    for item in data:
        score = item["similarity"]

        if score == 1.0:
            score_ranges["1.000 (Tam Eşleşme)"] += 1
            exact_matches.append(item)
        elif score >= 0.99:
            score_ranges["0.99-0.999 (Neredeyse Aynı)"] += 1
            near_duplicates.append(item)
        elif score >= 0.95:
            score_ranges["0.95-0.989 (Çok Benzer)"] += 1
            near_duplicates.append(item)
        elif score >= 0.90:
            score_ranges["0.90-0.949 (Benzer)"] += 1
            similar_questions.append(item)
        elif score >= 0.85:
            score_ranges["0.85-0.899 (Orta Benzer)"] += 1
            similar_questions.append(item)
        else:
            score_ranges["< 0.85"] += 1

    print("=" * 80)
    print("BENZERLIK SKORU DAĞILIMI")
    print("=" * 80)
    for range_name, count in score_ranges.items():
        percentage = (count / len(data) * 100) if data else 0
        print(f"{range_name:30} {count:5} ({percentage:5.1f}%)")

    print(f"\nToplam: {len(data)}")

    # Check for different answers in near-duplicates
    print("\n" + "=" * 80)
    print("FARKLI CEVAPLI NEREDEYSE AYNI SORULAR (0.95+)")
    print("=" * 80)

    different_answers = []
    for item in near_duplicates:
        ans1 = item["q1"].get("answer")
        ans2 = item["q2"].get("answer")
        if ans1 and ans2 and ans1 != ans2:
            different_answers.append(item)

    print(f"Toplam neredeyse aynı soru: {len(near_duplicates)}")
    print(f"Farklı cevaplı: {len(different_answers)}")

    if different_answers:
        print("\nÖrnekler:")
        for i, item in enumerate(different_answers[:5], 1):
            print(f"\n{i}. Benzerlik: {item['similarity']:.4f}")
            print(f"   Ders: {item['q1']['course']}")
            print(f"   Soru 1 ({item['q1']['source']}): {item['q1']['text'][:80]}...")
            print(f"   Cevap 1: {item['q1']['answer']}")
            print(f"   Soru 2 ({item['q2']['source']}): {item['q2']['text'][:80]}...")
            print(f"   Cevap 2: {item['q2']['answer']}")

    # Recommendation
    print("\n" + "=" * 80)
    print("ÖNERİ")
    print("=" * 80)
    print(f"• 1.000 benzerlik: {score_ranges['1.000 (Tam Eşleşme)']} soru - Zaten işaretli (duplicate)")
    print(f"• 0.95+ benzerlik: {score_ranges['0.99-0.999 (Neredeyse Aynı)'] + score_ranges['0.95-0.989 (Çok Benzer)']} soru - İşaretlenmeli (near-duplicate)")
    print(f"  └─ Bunlardan {len(different_answers)} tanesi farklı cevaplı (DİKKAT!)")
    print(f"• 0.85-0.94: {score_ranges['0.90-0.949 (Benzer)'] + score_ranges['0.85-0.899 (Orta Benzer)']} soru - İncelenmeli (benzer konular)")

if __name__ == "__main__":
    main()
