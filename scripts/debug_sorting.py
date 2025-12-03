import json
import os
from libs.shared import clean_html

filepath = 'output/Anadolu/json/Donem 3/Anadolu - Dönem 3 - Türk Dili I - Sorularla Ogrenelim.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter for Unit 1
unit1 = [q for q in data if q.get("UniteNo") == 1]

print(f"Total questions in Unit 1: {len(unit1)}")

print("--- Question Titles in Order ---")
for i, q in enumerate(unit1):
    title_raw = q.get("Title")
    title_cleaned = clean_html(title_raw)
    print(f"Q{i}: Index={q.get('Index')} | Type={type(title_raw)} | Raw='{title_raw}' | Cleaned='{title_cleaned}'")
