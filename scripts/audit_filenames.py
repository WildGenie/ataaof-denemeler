import os
import re

# Directory to scan
TARGET_DIR = '/Users/wildgenie/Projects/ataaof-denemeler/output/Auzef/json'
conjunctions = ['ve', 'ile', 'veya', 'de', 'da', 'ki', 'mi', 'mı']

def is_title_case_correct(name):
    """
    Checks if a filename follows the Title Case rule:
    - Words should start with Uppercase.
    - Conjunctions should be lowercase (unless they are the first word, which usually isn't the case here).
    - Returns None if correct, or the suggested correct name if wrong.
    """

    # Remove extension
    base, ext = os.path.splitext(name)

    words = base.split()
    new_words = []
    has_change = False

    for i, w in enumerate(words):
        original_word = w

        # Split by hyphens to check sub-parts (like Sosyal-Duygusal)
        sub_parts = w.split('-')
        new_sub_parts = []

        for j, part in enumerate(sub_parts):
            if not part:
                new_sub_parts.append(part)
                continue

            is_conjunction = part.lower() in conjunctions
            is_start_of_filename = (i == 0 and j == 0)

            if is_conjunction and not is_start_of_filename:
                # Must be lowercase
                fixed_part = part.lower()
            else:
                # Must be Title Case
                # SPECIAL HANDLING:
                # 1. Roman Numerals / Acronyms: Keep them if they are already UPPER
                if part.isupper() and len(part) > 1:
                    fixed_part = part
                    # Edge case: "VE" is upper but should be lower.
                    if part.lower() in conjunctions:
                         fixed_part = part.lower()

                # 2. Mixed case (e.g. mRNA)? Keep it?
                # 3. Standard words: 'Anatomi', 'Gelişimsel'
                else:
                    # Generic title casing handling Turkish chars loosely
                    # Just ensure first letter is Upper.
                    # Be careful with I/i.

                    if part[0].islower():
                         # e.g. "duygusal" -> "Duygusal"
                         # Handle i -> İ, ı -> I
                         if part.startswith('i'):
                             fixed_part = 'İ' + part[1:]
                         elif part.startswith('ı'):
                             fixed_part = 'I' + part[1:]
                         else:
                             fixed_part = part[0].upper() + part[1:]
                    else:
                        fixed_part = part

            new_sub_parts.append(fixed_part)

        new_word = "-".join(new_sub_parts)
        if new_word != original_word:
            has_change = True

        new_words.append(new_word)

    if has_change:
        return " ".join(new_words) + ext
    return None

issues_found = []

print("Scanning for casing issues...")

for root, dirs, files in os.walk(TARGET_DIR):
    for f in files:
        if not f.endswith('.json'): continue

        suggestion = is_title_case_correct(f)
        if suggestion:
            full_path = os.path.join(root, f)
            print(f"[ISSUE] {f}")
            print(f"     -> Suggested: {suggestion}")
            issues_found.append(f)

if not issues_found:
    print("No obvious casing issues found based on the rules!")
else:
    print(f"Found {len(issues_found)} files with potential issues.")
