
import os

def verify_locations():
    expected_reports = ["file_match_report.json", "source_structure.json"]
    expected_scripts = ["find_usage.py", "list_json_files.py"]

    print("Checking reports/...")
    if os.path.exists("reports"):
        reports = os.listdir("reports")
        for f in expected_reports:
            if f in reports:
                print(f" - {f} found in reports/")
            else:
                print(f" - {f} NOT found in reports/")

    print("\nChecking scripts/analysis/...")
    if os.path.exists("scripts/analysis"):
        scripts = os.listdir("scripts/analysis")
        for f in expected_scripts:
            if f in scripts:
                print(f" - {f} found in scripts/analysis/")
            else:
                print(f" - {f} NOT found in scripts/analysis/")

    print("\nChecking root for leftovers...")
    for f in expected_reports + expected_scripts + ["course_mapping.json"]:
        if os.path.exists(f):
            print(f" - {f} still in root!")

if __name__ == "__main__":
    verify_locations()
