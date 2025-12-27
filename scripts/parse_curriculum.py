import re
import json

def parse_curriculum(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for headers: <h4> ... <strong> ... 1 . Sınıf - Güz ... </strong> ... </h4>
    # We can split by headers or regex find iteratively.

    # Let's find all headers first
    # Regex to capture "X . Sınıf - Güz/Bahar"
    # Matches: 1 . Sınıf -\nGüz

    # Clean up whitespace for easier matching
    cleaned_content = re.sub(r'\s+', ' ', content)

    # Mapping
    term_map = {
        '1 . Sınıf - Güz': 1,
        '1 . Sınıf - Bahar': 2,
        '2 . Sınıf - Güz': 3,
        '2 . Sınıf - Bahar': 4,
        '3 . Sınıf - Güz': 5,
        '3 . Sınıf - Bahar': 6,
        '4 . Sınıf - Güz': 7,
        '4 . Sınıf - Bahar': 8
    }

    courses = []

    # Find tables corresponding to headers.
    # Since HTML is messy, let's use a simpler approach:
    # Find "X . Sınıf - Y" then find the table following it.

    # We can use regex to find the block between headers?
    # Or just `cleaned_content.split('<h4>')`?

    parts = cleaned_content.split('<h4>')

    current_term = None

    for part in parts:
        # Check if this part contains the term header
        # Part starts with the content inside h4 because we split by <h4> but wait, split consumes separator.
        # Actually split gives: [pre, content_after_h4_1, content_after_h4_2...]
        # The term info is AT THE BEGINNING of 'part' (inside strong tags usually).

        # Example part start: " <strong> 1 . Sınıf - Güz </strong> </h4> ... table ..."

        # Try to match the term string
        found_term = None
        for key, val in term_map.items():
            # Normalize key spaces
            normalized_key = " ".join(key.split())
            if normalized_key in part:
                 found_term = val
                 break

        if found_term:
            current_term = found_term

            # Find all rows <tr>...</tr>
            # Be careful with nested tables if any, but structure looks simple.
            # Regex to find TRs that contain course info

            # Pattern: <tr> ... <td...hidden...>CODE</td> ... <td...col-md-7...> ... <a>NAME</a> ... </tr>
            # Let's extract all TR content first

            rows = re.findall(r'<tr>(.*?)</tr>', part, re.DOTALL | re.IGNORECASE)

            for row in rows:
                if 'hidden-sm hidden-xs' not in row: continue # Skip header row keys

                # Extract Code
                # <td class="col-md-1 hidden-sm hidden-xs">ACCG1001</td>
                code_match = re.search(r'<td[^>]*class="[^"]*hidden-xs[^"]*"[^>]*>\s*(.*?)\s*</td>', row, re.IGNORECASE)
                if not code_match: continue
                course_code = code_match.group(1).strip()

                # Extract Name and Link
                # <td class="col-md-7"><a href="..."> ... </a></td>
                name_match = re.search(r'<td[^>]*class="col-md-7"[^>]*>\s*<a[^>]*href="(.*?)"[^>]*>(.*?)</a>', row, re.IGNORECASE | re.DOTALL)
                if not name_match: continue

                href = name_match.group(1).strip()
                raw_name = name_match.group(2).strip()

                # Extract ID from href
                id_match = re.search(r'[?&]id=(\d+)', href)
                curriculum_id = id_match.group(1) if id_match else None

                # Title Case
                clean_name = raw_name
                words = clean_name.split()
                title_cased_words = []

                for i, word in enumerate(words):
                    subwords = word.split('-')
                    sub_cased = []
                    for sub in subwords:
                        if not sub: continue
                        if sub in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']:
                            sub_cased.append(sub)
                            continue
                        w_lower = sub.replace('İ', 'i').replace('I', 'ı').lower()
                        first_char = sub[0]
                        if first_char == 'İ': w_title = 'İ' + w_lower[1:]
                        elif first_char == 'I': w_title = 'I' + w_lower[1:]
                        else:
                            first_lower = w_lower[0]
                            if first_lower == 'i': upper = 'İ'
                            elif first_lower == 'ı': upper = 'I'
                            else: upper = first_lower.upper()
                            w_title = upper + w_lower[1:]
                        sub_cased.append(w_title)
                    w_final = "-".join(sub_cased)
                    if i > 0 and w_final.lower().replace('ı', 'i') in ['ve', 'ile', 'veya', 'de', 'da', 'icin', 'için']:
                         w_final = w_final.lower().replace('I', 'ı').replace('İ', 'i')
                         if w_final.lower().startswith('ve'): w_final = 've'
                         if w_final.lower().startswith('ile'): w_final = 'ile'
                         if w_final.lower().startswith('veya'): w_final = 'veya'
                         if w_final.lower().startswith('için'): w_final = 'için'
                    title_cased_words.append(w_final)

                final_name = " ".join(title_cased_words)

                courses.append({
                    "term": current_term,
                    "code": course_code,
                    "id": curriculum_id,
                    "name": final_name
                })

    return courses

courses = parse_curriculum('curriculum_input.html')
print(json.dumps(courses, indent=2, ensure_ascii=False))

# Save to canonical file
with open('auzef/curriculum_courses.json', 'w', encoding='utf-8') as f:
    json.dump(courses, f, indent=2, ensure_ascii=False)
