import json
import os

filepath = 'output/Anadolu/json/Donem 3/Anadolu - Dönem 3 - Sanatta Eleştirel Düşünce - Alıştırma Soruları.json'

if not os.path.exists(filepath):
    print(f"File not found: {filepath}")
    exit(1)

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    counts = {}
    for q in data:
        u = q.get('Unite', 'Unknown')
        counts[u] = counts.get(u, 0) + 1

    print(f"Total Questions: {len(data)}")
    print("-" * 20)
    for u in sorted(counts.keys(), key=lambda x: int(x) if isinstance(x, int) else 999):
        print(f"Unit {u}: {counts[u]} questions")

except Exception as e:
    print(f"Error: {e}")
