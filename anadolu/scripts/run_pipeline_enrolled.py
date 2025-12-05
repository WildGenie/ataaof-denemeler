#!/usr/bin/env python3
"""
Run the full data pipeline for all enrolled courses.
Steps:
1. Fetch Materials, Exams, and Summaries
2. Convert Exams to JSON
3. Verify Answers
4. Enrich Questions
5. Convert to Markdown
"""
import os
import sys
import subprocess
import time

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

def run_command(command, description):
    print(f"\n{'='*80}")
    print(f"🚀 Starting: {description}")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        # Use sys.executable to ensure we use the same python interpreter (e.g. venv)
        cmd_list = [sys.executable] + command.split()

        # Special handling for scripts in anadolu/scripts vs anadolu/
        # Adjust paths relative to PROJECT_ROOT

        result = subprocess.run(
            cmd_list,
            cwd=PROJECT_ROOT,
            check=True
        )

        duration = time.time() - start_time
        print(f"\n✅ Completed: {description} in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed: {description}")
        print(f"Exit Code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {description}")
        print(f"Exception: {e}")
        return False

def main():
    print("Starting Full Pipeline for Enrolled Courses...")

    # 1. Fetch Materials
    if not run_command("anadolu/fetch.py --enrolled --materials --download-exams --summaries", "Fetch Materials & Exams"):
        return

    # 2. Convert Exams to JSON
    if not run_command("anadolu/scripts/process_all_courses.py --enrolled", "Convert Exams to JSON"):
        return

    # 3. Verify Answers
    # verify_answers.py filters enrolled courses internally
    if not run_command("anadolu/scripts/verify_answers.py", "Verify Answers"):
        return

    # 4. Enrich Questions
    if not run_command("anadolu/scripts/process_all_enrichments.py --enrolled", "Enrich Questions"):
        return

    # 5. Convert to Markdown
    if not run_command("anadolu/scripts/process_all_markdown.py --enrolled", "Convert to Markdown"):
        return

    print(f"\n{'='*80}")
    print("🎉 All steps completed successfully!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
