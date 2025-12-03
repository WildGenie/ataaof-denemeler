import json
import os
from libs.shared import clean_html

filepath = 'output/Anadolu/json/Donem 3/Anadolu - Dönem 3 - Türk Dili I - Sorularla Ogrenelim.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter for Unit 1
unit1 = [q for q in data if q.get("UniteNo") == 1]

# Sort as in fetch.py
unit1.sort(key=lambda x: int(x.get("Index", 0)))

print(f"Total questions in Unit 1: {len(unit1)}")

current_title = None
for i, q in enumerate(unit1):
    title_raw = q.get("Title")
    title_cleaned = clean_html(title_raw)

    print(f"Q{i}: Raw='{title_raw}' | Cleaned='{title_cleaned}' | Match Previous? {title_cleaned == current_title}")

    if title_cleaned != current_title:
        print(f"  -> CHANGE DETECTED: '{current_title}' -> '{title_cleaned}'")
        current_title = title_cleaned
