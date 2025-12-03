#!/usr/bin/env python3
"""
Convert Enriched JSON files to Markdown format.
Groups questions by unit and uses the existing project format.
"""

import os
import json
import sys
import re
from markdownify import MarkdownConverter

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from libs.shared import clean_html

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_BASE_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "json")
MD_BASE_DIR = os.path.join(PROJECT_ROOT, "output", "Anadolu", "md")

class HTMLPreservingConverter(MarkdownConverter):
    """Custom converter that preserves certain HTML tags."""
    def convert_sup(self, el, text, convert_as_inline):
        return f'<sup>{text}</sup>'

    def convert_sub(self, el, text, convert_as_inline):
        return f'<sub>{text}</sub>'

def questions_to_markdown(questions):
    """Convert questions to markdown format (matching existing format)."""
    md = ""
    converter = HTMLPreservingConverter(autolinks=False)

    def safe_convert(text):
        if not text: return ""
        # Pre-process text to replace <br> with newlines
        text = re.sub(r'<br\b[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)
        converted = converter.convert(text).strip()
        # Escape dots after numbers at the start of a line
        converted = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)
        # Escape < characters except for allowed tags
        converted = re.sub(r'<(?!/?(sup|sub)>)', '&lt;', converted)
        return converted

    for i, q in enumerate(questions, 1):
        # Question text
        q_text_raw = safe_convert(q.get('question', ''))
        q_text_formatted = q_text_raw.replace('\n', '<br />')
        q_text_formatted = re.sub(r'\s*(<br\b[^>]*>\s*)+', '<br />', q_text_formatted)

        md += f"1. {q_text_formatted}\n"

        # Options
        options_list = ['A', 'B', 'C', 'D', 'E']
        correct_index = q.get('correctIndex', 0)
        options = q.get('options', [])

        for idx, opt_letter in enumerate(options_list):
            if idx >= len(options):
                break

            is_correct = idx == correct_index
            prefix = "**Cevap " if is_correct else ""
            suffix = "**" if is_correct else ""

            list_item_prefix = f"    - {prefix}{opt_letter}-) "

            opt_content = options[idx]
            if opt_content:
                opt_text_raw = safe_convert(opt_content)
                opt_text_formatted = opt_text_raw.replace('\n', ' ')
                opt_text_formatted = re.sub(r'<br\b[^>]*>|&lt;br\s*/?&gt;', ' ', opt_text_formatted, flags=re.IGNORECASE)
                opt_text_formatted = re.sub(r'\s+', ' ', opt_text_formatted).strip()
            else:
                opt_text_formatted = ""

            md += f"{list_item_prefix}{opt_text_formatted}{suffix}\n"

        # Explanation
        if q.get('explanation'):
            explanation = safe_convert(q['explanation'])
            explanation = explanation.replace('\n', '<br />')
            explanation = re.sub(r'(<br\b[^>]*>\s*)+', '<br />', explanation)
            md += f"\n    > **Açıklama:** {explanation}\n\n"

        md += "    <hr />\n"
    return md

def convert_to_markdown(course_name, donem):
    """Convert JSON to Markdown (Enriched preferred, fallback to Raw)."""

    # Paths
    enriched_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}",
                                       f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Enriched.json")
    raw_json_path = os.path.join(JSON_BASE_DIR, f"Donem {donem}",
                                  f"Anadolu - Dönem {donem} - {course_name} - Çıkmış Sorular - Raw.json")

    data = None
    is_enriched = False

    # Try loading Enriched JSON first
    if os.path.exists(enriched_json_path):
        print(f"Converting (Enriched): {course_name} (Dönem {donem})")
        with open(enriched_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        is_enriched = True
    # Fallback to Raw JSON
    elif os.path.exists(raw_json_path):
        print(f"Converting (Raw): {course_name} (Dönem {donem})")
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        is_enriched = False
    else:
        print(f"No JSON found for: {course_name}")
        return

    questions = data.get("questions", [])

    if not questions:
        print("  No questions found.")
        return

    # Output path
    # New structure: output/Anadolu/Donem X/[Course Name]/Çıkmış Sorular.md
    md_dir = os.path.join(PROJECT_ROOT, "output", "Anadolu", f"Donem {donem}", course_name)
    os.makedirs(md_dir, exist_ok=True)

    md_path = os.path.join(md_dir, "Çıkmış Sorular.md")

    md_content = f"# {course_name} - Çıkmış Sorular\n\n"

    if is_enriched:
        # Group by Unit -> Topic
        questions_by_unit = {}
        for q in questions:
            unit = q.get("UniteNo", "Diğer")
            if unit not in questions_by_unit:
                questions_by_unit[unit] = []
            questions_by_unit[unit].append(q)

        sorted_units = sorted(
            questions_by_unit.keys(),
            key=lambda x: int(x) if isinstance(x, int) or (isinstance(x, str) and str(x).isdigit()) else 999
        )

        for unit in sorted_units:
            md_content += f"## Ünite {unit}\n\n"
            unit_questions = questions_by_unit[unit]

            questions_by_topic = {}
            for q in unit_questions:
                topic = q.get("topic", "Diğer Konular")
                if topic not in questions_by_topic:
                    questions_by_topic[topic] = []
                questions_by_topic[topic].append(q)

            sorted_topics = sorted(questions_by_topic.keys())

            for topic in sorted_topics:
                if topic and topic != "Diğer Konular":
                    md_content += f"### {topic}\n\n"

                topic_questions = questions_by_topic[topic]
                md_content += questions_to_markdown(topic_questions)
                md_content += "\n"

    else:
        # Group by Source (Exam Name)
        questions_by_source = {}
        for q in questions:
            source = q.get("source", "Bilinmeyen Kaynak")
            if source not in questions_by_source:
                questions_by_source[source] = []
            questions_by_source[source].append(q)

        sorted_sources = sorted(questions_by_source.keys())

        for source in sorted_sources:
            md_content += f"## {source}\n\n"
            source_questions = questions_by_source[source]
            md_content += questions_to_markdown(source_questions)
            md_content += "\n"

    # Save Markdown
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"  ✅ Saved: {md_path}")
    print(f"  Generated {len(questions)} questions in Markdown format.\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert Enriched JSON to Markdown.")
    parser.add_argument("--course", required=True, help="Course name")
    parser.add_argument("--donem", type=int, required=True, help="Semester number (1-8)")

    args = parser.parse_args()

    convert_to_markdown(args.course, args.donem)
