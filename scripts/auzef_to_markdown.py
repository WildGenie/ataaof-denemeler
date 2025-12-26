#!/usr/bin/env python3
import os
import json
import sys
import re
from markdownify import MarkdownConverter

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUZEF_JSON_DIR = os.path.join(PROJECT_ROOT, "output", "Auzef", "json")
AUZEF_MD_DIR = os.path.join(PROJECT_ROOT, "output", "Auzef")

class HTMLPreservingConverter(MarkdownConverter):
    def convert_sup(self, el, text, **kwargs):
        return f'<sup>{text}</sup>'

    def convert_sub(self, el, text, **kwargs):
        return f'<sub>{text}</sub>'

    def convert_u(self, el, text, **kwargs):
        return f'<u>{text}</u>'

    def convert_b(self, el, text, **kwargs):
        return f'<b>{text}</b>'

    def convert_i(self, el, text, **kwargs):
        return f'<i>{text}</i>'

    def convert_strong(self, el, text, **kwargs):
        return f'<b>{text}</b>'

    def convert_em(self, el, text, **kwargs):
        return f'<i>{text}</i>'

    def convert_ins(self, el, text, **kwargs):
        return f'<ins>{text}</ins>'

def safe_convert(text):
    if not text: return ""
    converter = HTMLPreservingConverter(autolinks=False)
    # Replace <br> with temporary token to keep them later
    text = re.sub(r'<br\b[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)
    converted = converter.convert(text).strip()
    # Escape dots after numbers at the start of a line
    converted = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)
    # Escape < except for allowed HTML tags
    allowed_tags = r'sup|sub|u|b|i|strong|em|ins'
    converted = re.sub(r'<(?!/?(' + allowed_tags + r')\b)', '&lt;', converted)
    return converted

def questions_to_markdown(questions):
    md = ""
    for i, q in enumerate(questions, 1):
        q_text = safe_convert(q.get('question', '')).replace('\n', '<br />')

        occ = q.get('occurrence_count', 1)
        badge = f" *({occ} kez soruldu)*" if occ > 1 else ""

        md += f"1. {q_text}{badge}\n"

        options = q.get('options', [])
        correct = q.get('correctIndex', -1)
        for idx, opt in enumerate(options):
            letter = chr(65 + idx)
            prefix = "**Cevap " if idx == correct else ""
            suffix = "**" if idx == correct else ""

            cleaned_opt = safe_convert(opt).replace('\n', ' ').strip()
            md += f"    - {prefix}{letter}-) {cleaned_opt}{suffix}\n"

        if q.get('explanation'):
            exp = safe_convert(q['explanation']).replace('\n', '<br />')
            md += f"\n    > **Açıklama:** {exp}\n\n"

        md += "    <hr />\n"
    return md

def natural_sort_key(s):
    """Natural sort key for strings with numbers (e.g., '6.3' before '6.10')."""
    if s is None:
        return []
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]

def main():
    print("Updating Auzef Markdown files...")

    # 1. Clear old folders if they contain Period 1 (already done manually, but for safety in code)
    # Actually just process what exists in AUZEF_JSON_DIR

    json_files = []
    for root, dirs, files in os.walk(AUZEF_JSON_DIR):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    for json_path in json_files:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        questions = data.get("questions", [])
        meta = data.get("meta", {})
        course_name = meta.get("course_name")
        term = meta.get("term", "")

        if not course_name: continue

        # Determine donem number for path
        match = re.search(r'(\d+)', term)
        term_num = match.group(1) if match else "Other"

        target_dir = os.path.join(AUZEF_MD_DIR, f"Donem {term_num}", course_name)
        os.makedirs(target_dir, exist_ok=True)

        md_path = os.path.join(target_dir, "Sorular.md")
        print(f"  Generating: {md_path}")

        # Filter is_duplicate (we already filtered them in converter, but good to check)
        valid_qs = [q for q in questions if not q.get("is_duplicate")]

        # Group by Unit
        by_unit = {}
        for q in valid_qs:
            u = q.get("unit", "Diğer")
            if u not in by_unit: by_unit[u] = []
            by_unit[u].append(q)

        # Natural sort for units
        sorted_units = sorted(by_unit.keys(), key=natural_sort_key)

        content = f"# {course_name} - Çıkmış Sorular\n\n"

        for unit in sorted_units:
            u_title = unit if "Ünite" in str(unit) else f"Ünite {unit}"
            content += f"## {u_title}\n\n"

            # Group by Topic
            by_topic = {}
            for q in by_unit[unit]:
                t = q.get("topic", "")
                if t not in by_topic: by_topic[t] = []
                by_topic[t].append(q)

            # Natural sort for topics
            sorted_topics = sorted(by_topic.keys(), key=natural_sort_key)
            for topic in sorted_topics:
                if topic:
                    content += f"### {topic}\n\n"
                content += questions_to_markdown(by_topic[topic])
                content += "\n"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    print("Auzef Markdown update complete.")

if __name__ == "__main__":
    main()
