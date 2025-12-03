import json
import os
import re
import sys

# Set default encoding to utf-8 for output
sys.stdout.reconfigure(encoding='utf-8')

json_path = "output/Anadolu/json/Donem 1/Anadolu - Dönem 1 - Görsel Estetik - Çıkmış Sorular - Raw.json"

if not os.path.exists(json_path):
    print("File not found.")
    exit()

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data.get("questions", [])
print(f"Total questions: {len(questions)}")

exam_counts = {}
for q in questions:
    source = q.get("source", "Unknown")
    exam_counts[source] = exam_counts.get(source, 0) + 1

print("\nDetailed Exam Analysis:")
sorted_exams = sorted(exam_counts.items())
for source, count in sorted_exams:
    print(f"  {source}: {count} questions")

    # Check question numbers for this exam
    exam_questions = [q for q in questions if q.get("source") == source]
    q_nums = []
    for q in exam_questions:
        qn = q.get("exam_question_number")
        if qn is not None:
            try:
                q_nums.append(int(qn))
            except:
                pass
    q_nums.sort()

    if not q_nums:
        print("    ⚠️  No question numbers found.")
        continue

    # Check for duplicates in exam_question_number
    if len(q_nums) != len(set(q_nums)):
        duplicates = [x for x in q_nums if q_nums.count(x) > 1]
        print(f"    ⚠️  Duplicate question numbers found: {set(duplicates)}")

    # Check if 1-20 are present
    present_set = set(q_nums)
    missing_in_20 = [i for i in range(1, 21) if i not in present_set]

    if missing_in_20:
        print(f"    ⚠️  Missing numbers (1-20): {missing_in_20}")
    else:
        print("    ✅  Questions 1-20 present.")

# Check for duplicate global IDs
ids = [q.get("id") for q in questions]
if len(ids) != len(set(ids)):
    print(f"\n⚠️  Duplicate global IDs found! ({len(ids) - len(set(ids))})")
else:
    print("\n✅  No duplicate global IDs.")

print("\nQuality Checks:")
br_count = 0
u_count = 0
negative_words = ["değildir", "olamaz", "yanlıştır", "yoktur", "beklenmez", "söylenemez", "ulaşılamaz"]
missed_negatives = 0
examples_with_br = []
examples_missed_negative = []

for q in questions:
    text = q.get("question", "")
    if "<br>" in text:
        br_count += 1
        if len(examples_with_br) < 3:
            examples_with_br.append(text)

    if "<u>" in text:
        u_count += 1

    # Check for missed negatives
    lower_text = text.lower()
    for word in negative_words:
        # Check if word exists as a whole word but is NOT underlined
        # We look for the word NOT preceded by <u>
        if re.search(rf"(?<!<u>)\b{word}\b", lower_text):
             missed_negatives += 1
             if len(examples_missed_negative) < 3:
                 examples_missed_negative.append(f"Word: {word} -> {text}")
             break # Count question only once

print(f"  Questions with <br>: {br_count} (Should be low if merging worked, unless lists exist)")
print(f"  Questions with <u>: {u_count}")
print(f"  Potential missed negatives: {missed_negatives}")

if examples_with_br:
    print("\nExamples with <br>:")
    for ex in examples_with_br:
        print(f"  - {ex}")

if examples_missed_negative:
    print("\nExamples with missed negatives:")
    for ex in examples_missed_negative:
        print(f"  - {ex}")

# Check options count
option_counts = {}
for q in questions:
    opt_len = len(q.get("options", []))
    option_counts[opt_len] = option_counts.get(opt_len, 0) + 1

print("\nOption counts:")
for length, count in option_counts.items():
    print(f"  {length} options: {count}")
