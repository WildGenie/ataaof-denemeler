import os
import json
import argparse
import sys
import difflib

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_lib import DERSLER_FILE

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Map courses to source directories")
    parser.add_argument("--source-dir", help="Source directory to scan (defaults to LOCAL_MATERIALS_ROOT in .env)")
    parser.add_argument("output_file", help="Output JSON mapping file")
    args = parser.parse_args()

    source_dir = args.source_dir or os.getenv("LOCAL_MATERIALS_ROOT")

    if not source_dir:
        print("Error: Source directory must be provided via --source-dir or LOCAL_MATERIALS_ROOT env var.")
        return

    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return

    # Load courses
    with open(DERSLER_FILE, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    print(f"Loaded {len(courses)} courses.")

    # Scan source directory for candidate folders
    print(f"Scanning source directory: {source_dir}...")
    source_folders = {} # name_norm -> full_path

    # We look at top level and one level deep (e.g. "III. Yarıyıl/Ders Adı")
    for root, dirs, files in os.walk(source_dir):
        # Check if current root or any parent in the relative path contains "Yarıyıl"
        rel_path = os.path.relpath(root, source_dir)

        # We want to capture folders inside "X. Yarıyıl"
        # So if we are at source_dir, we look at dirs.
        # If we are at source_dir/X. Yarıyıl, we look at dirs (which are course folders).

        # Filter: Only consider if we are inside a "Yarıyıl" folder or if the folder itself is "Yarıyıl"
        # Actually, we want to map COURSE folders. Course folders are inside Yarıyıl folders.
        # So we should look at dirs when 'root' is a Yarıyıl folder.

        if "Yarıyıl" in rel_path:
            # We are inside a semester folder, so 'dirs' are likely course folders
            for d in dirs:
                if d.startswith("."): continue
                full_path = os.path.join(root, d)
                norm_name = d.lower().replace(" ", "")
                source_folders[norm_name] = full_path
        elif root == source_dir:
            # We are at top level, check if any dirs are Yarıyıl folders to traverse them
            # os.walk does this automatically, but we don't add top level folders to source_folders map
            pass

    print(f"Found {len(source_folders)} candidate folders.")

    mapping = {}

    for course in courses:
        course_name = course.get("CourseName")
        if not course_name: continue

        course_name_norm = course_name.lower().replace(" ", "")

        # Exact match
        if course_name_norm in source_folders:
            full_path = source_folders[course_name_norm]
            rel_path = os.path.relpath(full_path, source_dir)
            mapping[course_name] = rel_path
            print(f"[Match] {course_name} -> {rel_path}")
            continue

        # Fuzzy match
        matches = difflib.get_close_matches(course_name_norm, source_folders.keys(), n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            full_path = source_folders[best_match]
            rel_path = os.path.relpath(full_path, source_dir)
            mapping[course_name] = rel_path
            print(f"[Fuzzy] {course_name} -> {rel_path}")
        else:
            # print(f"[No Match] {course_name}")
            pass

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4, ensure_ascii=False)

    print(f"Mapping saved to {args.output_file}")

if __name__ == "__main__":
    main()
