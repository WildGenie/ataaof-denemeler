#!/usr/bin/env python3
"""
Orchestrate the reprocessing of problematic exams.
1. Reads problematic_exams.json.
2. For each course:
    - Runs convert_exams_to_json.py with specific material IDs.
    - Runs enrich_questions.py (re-enriches updated questions).
3. Updates embeddings (generate_batch_embeddings.py).
4. Re-runs global analysis (analyze_similar_questions_embeddings.py).
5. Re-runs duplicate marking (mark_near_duplicates.py).
6. Regenerates all markdown (process_all_markdown.py).
"""

import os
import json
import sys
import subprocess

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

PROBLEMATIC_EXAMS_FILE = os.path.join(PROJECT_ROOT, "output", "Anadolu", "problematic_exams.json")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "anadolu", "scripts")

def run_command(command, description):
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*80}\n")

    try:
        result = subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {e}")
        return False

def get_donem_for_course(course_name):
    """Find the semester for a course."""
    # This is a bit hacky, but we can look at the directory structure
    json_dir = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
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
    parser = argparse.ArgumentParser(description="Orchestrate the reprocessing of problematic exams.")
    parser.add_argument("--course", help="Process only a specific course")
    args = parser.parse_args()

    if not os.path.exists(PROBLEMATIC_EXAMS_FILE):
        print(f"Error: {PROBLEMATIC_EXAMS_FILE} not found. Run identify_problematic_exams.py first.")
        sys.exit(1)

    with open(PROBLEMATIC_EXAMS_FILE, 'r', encoding='utf-8') as f:
        targets = json.load(f)

    # Filter by course if requested
    if args.course:
        targets = [t for t in targets if args.course.lower() in t["course"].lower()]
        if not targets:
            print(f"No problematic exams found for course: {args.course}")
            return

    print(f"Found {len(targets)} courses to reprocess.")

    # 1. Reprocess Exams (PDF -> JSON)
    courses_to_enrich = []
    for item in targets:
        course_name = item["course"]
        material_ids = item["material_ids"]
        courses_to_enrich.append(course_name)

        print(f"\nProcessing course: {course_name}")
        print(f"  Target Material IDs: {material_ids}")

        # Convert PDF to JSON (Use cache)
        cmd_convert = [
            sys.executable,
            os.path.join(SCRIPTS_DIR, "convert_exams_to_json.py"),
            "--course", course_name,
            "--material-ids", ",".join(material_ids)
        ]
        if not run_command(cmd_convert, f"Convert Exams for {course_name}"):
            continue

    # 2. Enrich Questions (Batch Mode - Global, Use cache)
    print("\nStarting Batch Enrichment...")
    cmd_enrich = [
        sys.executable,
        os.path.join(SCRIPTS_DIR, "enrich_questions_batch.py")
    ]

    # Pass all courses that were just reprocessed via PDF conversion
    cmd_enrich.extend(["--courses", ",".join(courses_to_enrich)])

    run_command(cmd_enrich, "Batch Enrich Questions")

    # 3. Update Embeddings (Global)
    # We run this globally to ensure all new questions get embeddings
    # Since we updated the JSONs, the hashes might have changed, so new embeddings will be generated.
    run_command([
        sys.executable,
        os.path.join(SCRIPTS_DIR, "generate_batch_embeddings.py"),
        "--all"
    ], "Update Embeddings")

    # 3. Global Analysis
    run_command([
        sys.executable,
        os.path.join(SCRIPTS_DIR, "analyze_similar_questions_embeddings.py")
    ], "Global Similarity Analysis")

    # 4. Mark Duplicates
    run_command([
        sys.executable,
        os.path.join(SCRIPTS_DIR, "mark_near_duplicates.py")
    ], "Mark Duplicates")

    # 5. Regenerate Markdown
    run_command([
        sys.executable,
        os.path.join(SCRIPTS_DIR, "process_all_markdown.py")
    ], "Regenerate All Markdown")

    print("\n✅ Reprocessing Pipeline Complete!")

if __name__ == "__main__":
    main()
