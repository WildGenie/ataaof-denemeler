#!/usr/bin/env python3
"""
Sanitize JSON files by removing unusual line terminators (LS/PS).
These characters (\u2028, \u2029) can cause issues in some editors and parsers.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")

def sanitize_file(filepath):
    """Read a file, replace LS/PS characters, and save if changed."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace Line Separator and Paragraph Separator
        # Usually replacing with newline or space is appropriate
        new_content = content.replace('\u2028', '\n').replace('\u2029', '\n')

        if content != new_content:
            print(f"Sanitizing: {os.path.basename(filepath)}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    print(f"Scanning {JSON_DIR} for unusual line terminators...")
    count = 0
    cleaned = 0

    for root, dirs, files in os.walk(JSON_DIR):
        for file in files:
            if file.endswith(".json"):
                count += 1
                filepath = os.path.join(root, file)
                if sanitize_file(filepath):
                    cleaned += 1

    print(f"\nScanned {count} files.")
    print(f"Cleaned {cleaned} files.")

if __name__ == "__main__":
    main()
