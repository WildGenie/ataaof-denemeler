#!/usr/bin/env python3
"""
Identify exams containing questions that are semantically similar (>0.95) but have different answers.
Outputs a JSON list of target exams (course name and material ID) to reprocess.
"""

import os
import json
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

SIMILARITY_REPORT = os.path.join(PROJECT_ROOT, "output", "Anadolu", "embedding_similarity_analysis.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "Anadolu", "problematic_exams.json")

def normalize_answer(answer):
    """Normalize answer for comparison."""
    if not answer:
        return ""
    return answer.lower().strip()

def main():
    print("Identifying problematic exams (0.95+ similarity, different answers)...")

    if not os.path.exists(SIMILARITY_REPORT):
        print(f"Error: Similarity report not found at {SIMILARITY_REPORT}")
        sys.exit(1)

    with open(SIMILARITY_REPORT, 'r', encoding='utf-8') as f:
        similarity_data = json.load(f)

    problematic_exams = {} # Key: (course_name, material_id), Value: list of question IDs

    count = 0
    for item in similarity_data:
        if item["similarity"] >= 0.95:
            ans1 = normalize_answer(item["q1"].get("answer", ""))
            ans2 = normalize_answer(item["q2"].get("answer", ""))

            # Check for DIFFERENT answers
            if ans1 and ans2 and ans1 != ans2:
                # Add both exams to the list

                # Q1
                course1 = item["q1"]["course"]
                # We need to find material_id. It's not in the report directly, but we can infer or find it.
                # Actually, the report structure I defined earlier didn't include material_id.
                # I need to fetch it from the Enriched JSONs or add it to the report generator.
                # For now, let's load the enriched JSONs to find material_ids for these question IDs.
                pass
                count += 1

    print(f"Found {count} pairs with high similarity but different answers.")

    # Since the report doesn't have material_id, we need a lookup map.
    # Let's build a quick map of (course, question_id) -> material_id
    print("Building question lookup map...")
    question_map = {}

    json_dir = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
    for donem_dir in os.listdir(json_dir):
        donem_path = os.path.join(json_dir, donem_dir)
        if not os.path.isdir(donem_path): continue

        for filename in os.listdir(donem_path):
            if "Enriched.json" in filename:
                course_name = filename.split(" - ")[2]
                try:
                    with open(os.path.join(donem_path, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for q in data.get("questions", []):
                            qid = q.get("id")
                            mat_id = q.get("material_id")
                            if qid and mat_id:
                                question_map[(course_name, qid)] = mat_id
                except:
                    pass

    # Now process again
    targets = {} # course_name -> set of material_ids

    for item in similarity_data:
        if item["similarity"] >= 0.95:
            ans1 = normalize_answer(item["q1"].get("answer", ""))
            ans2 = normalize_answer(item["q2"].get("answer", ""))

            if ans1 and ans2 and ans1 != ans2:
                # Q1
                c1 = item["q1"]["course"]
                id1 = item["q1"]["id"]
                mat1 = question_map.get((c1, id1))

                # Q2
                c2 = item["q2"]["course"]
                id2 = item["q2"]["id"]
                mat2 = question_map.get((c2, id2))

                if mat1:
                    if c1 not in targets: targets[c1] = set()
                    targets[c1].add(mat1)

                if mat2:
                    if c2 not in targets: targets[c2] = set()
                    targets[c2].add(mat2)

    # Convert sets to lists for JSON
    output_data = []
    for course, materials in targets.items():
        output_data.append({
            "course": course,
            "material_ids": list(materials)
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print(f"Identified {len(output_data)} courses with problematic exams.")
    print(f"List saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
