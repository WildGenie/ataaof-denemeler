
import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shared import safe_html_to_markdown, clean_html

test_inputs = [
    ("Joined", "biri<strong>değildir?</strong>"),
    ("Joined with ID", "biri<strong id=\"isPasted\">değildir?</strong>"),
    ("Joined U", "biri<u>değildir?</u>"),
    ("Already spaced", "biri <strong>değildir?</strong>"),
    ("Div Joined", "<div>biri</div><div><strong>değildir</strong></div>"),
    ("Paragraph Joined", "<p>biri</p><p><strong>değildir</strong></p>"),
    ("Raw from JSON", "<p>Aşağıdakilerden hangisi tik bozukluklarına sık eşlik eden psikiyatrik bozukluklardan biri<strong id=\"isPasted\"><u>değildir?</u></strong></p>")
]

print("--- Debugging Formatting V2 ---")
for name, inp in test_inputs:
    cleaned = clean_html(inp)
    markdown = safe_html_to_markdown(cleaned)
    print(f"Case: {name}")
    print(f"Input:    '{inp}'")
    print(f"Cleaned:  '{cleaned}'")
    print(f"Markdown: '{markdown}'")
    print("-" * 20)
