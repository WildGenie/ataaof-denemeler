#!/usr/bin/env python3
"""
Automates the embedding, analysis, marking, and markdown generation pipeline for a specific semester.
"""

import os
import sys
import argparse
import subprocess
import json

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

def run_command(command):
    """Run a shell command and print output."""
    print(f"\nRunning: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Process a semester: Embed -> Analyze -> Mark -> Markdown")
    parser.add_argument("--donem", type=int, required=True, help="Semester number (e.g., 1, 7)")
    args = parser.parse_args()

    donem = args.donem
    print(f"Starting processing for Semester {donem}...")

    # 1. Generate Embeddings
    print(f"\n{'='*50}\nStep 1: Generate Embeddings\n{'='*50}")
    run_command(f"python3 anadolu/scripts/generate_batch_embeddings.py --donem {donem}")

    # 2. Analyze Similar Questions
    print(f"\n{'='*50}\nStep 2: Analyze Similar Questions\n{'='*50}")
    run_command(f"python3 anadolu/scripts/analyze_similar_questions_embeddings.py --donem {donem}")

    # 3. Mark Duplicates
    print(f"\n{'='*50}\nStep 3: Mark Duplicates\n{'='*50}")
    run_command(f"python3 anadolu/scripts/mark_near_duplicates.py --donem {donem}")

    # 4. Generate Markdown
    print(f"\n{'='*50}\nStep 4: Generate Markdown\n{'='*50}")

    # Find courses in the semester directory
    json_dir = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json", f"Donem {donem}")
    if not os.path.exists(json_dir):
        print(f"Error: Directory not found: {json_dir}")
        sys.exit(1)

    courses = set()
    for filename in os.listdir(json_dir):
        if "Çıkmış Sorular - Enriched.json" in filename:
            # Filename format: Anadolu - Dönem X - Course Name - Çıkmış Sorular - Enriched.json
            parts = filename.split(" - ")
            if len(parts) >= 3:
                course_name = parts[2]
                courses.add(course_name)

    print(f"Found {len(courses)} courses to process: {', '.join(courses)}")

    for course in sorted(courses):
        print(f"  Processing markdown for: {course}")
        # Quote course name to handle spaces
        run_command(f'python3 anadolu/scripts/convert_to_markdown.py --course "{course}" --donem {donem}')

    print(f"\n{'='*50}\nProcessing Complete for Semester {donem}!\n{'='*50}")

if __name__ == "__main__":
    main()
