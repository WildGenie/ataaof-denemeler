#!/usr/bin/env python3
"""
Cleanup legacy folders in output/Anadolu.
We migrated to 'output/Anadolu/json/Donem X' structure.
Folders named directly after courses (e.g. 'output/Anadolu/Anadolu Kültür Tarihi') are obsolete.
"""

import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANADOLU_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu")

# Folders to KEEP
KEEP_DIRS = {
    "json",
    "embeddings",
    "pdf",
    "sorular",
    "__pycache__"
}

def is_legacy_folder(name):
    if name in KEEP_DIRS:
        return False
    if name.startswith("Donem "): # Keep Markdown output folders
        return False
    if name.startswith("."): # Hidden folders
        return False
    return True

def main():
    print(f"Scanning {ANADOLU_DIR} for legacy folders...")

    deleted_count = 0

    if not os.path.exists(ANADOLU_DIR):
        print("Anadolu dir not found.")
        return

    for item in os.listdir(ANADOLU_DIR):
        path = os.path.join(ANADOLU_DIR, item)
        if os.path.isdir(path):
            if is_legacy_folder(item):
                print(f"Deleting legacy folder: {item}")
                try:
                    shutil.rmtree(path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
            else:
                # print(f"Keeping: {item}")
                pass

    print(f"\nCleanup complete. Deleted {deleted_count} folders.")

if __name__ == "__main__":
    # Safety check: Ask user confirmation if running interactively,
    # but since we run this via agent, we assume the user approved the action if they run this script.
    # To be safe, I'll print what would be deleted first?
    # No, the agent takes actions.
    main()
