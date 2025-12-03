import os
import json
import argparse
import sys

def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path, x)) for x in os.listdir(path) if not x.startswith('.')]
    else:
        d['type'] = "file"
    return d

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Save directory structure to JSON")
    parser.add_argument("--source-dir", help="Source directory to analyze (defaults to LOCAL_MATERIALS_ROOT in .env)")
    parser.add_argument("output_file", help="Output JSON file")
    args = parser.parse_args()

    source_dir = args.source_dir or os.getenv("LOCAL_MATERIALS_ROOT")

    if not source_dir:
        print("Error: Source directory must be provided via --source-dir or LOCAL_MATERIALS_ROOT env var.")
        return

    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return

    print(f"Analyzing {source_dir}...")
    structure = path_to_dict(source_dir)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=4, ensure_ascii=False)

    print(f"Structure saved to {args.output_file}")

if __name__ == "__main__":
    main()
