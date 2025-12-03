
import json

def check():
    try:
        # Load unmatched targets
        with open("report_unmatched_targets.json", 'r', encoding='utf-8') as f:
            unmatched_data = json.load(f)

        unmatched_targets = {item['TargetFile'] for item in unmatched_data}
        print(f"Loaded {len(unmatched_targets)} unmatched targets.")

        # Load potential matches
        with open("potential_matches_report.json", 'r', encoding='utf-8') as f:
            potential_data = json.load(f)

        print(f"Loaded {len(potential_data)} potential matches.")

        # Check for overlaps
        found_matches = []
        for item in potential_data:
            target = item.get("PotentialTarget")
            if target in unmatched_targets:
                found_matches.append(item)

        print(f"\nFound {len(found_matches)} potential matches for unmatched targets:")
        for match in found_matches:
            print(f"Target: {match.get('PotentialTarget')}")
            print(f"  Source: {match.get('SourceFile')}")
            print(f"  Reason: {match.get('Reason')}")
            print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
