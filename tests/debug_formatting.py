
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shared import safe_html_to_markdown, clean_html

test_inputs = [
    "biri <strong><u>değildir?</u></strong>",
    "biri <strong>değildir?</strong>",
    "biri <u>değildir?</u>",
    "biri&nbsp;<strong>değildir?</strong>",
    "<p>biri <strong>değildir?</strong></p>",
    "biri\n<strong>değildir?</strong>"
]

print("--- Debugging Formatting ---")
for inp in test_inputs:
    cleaned = clean_html(inp)
    markdown = safe_html_to_markdown(cleaned)
    print(f"Input:    '{inp}'")
    print(f"Cleaned:  '{cleaned}'")
    print(f"Markdown: '{markdown}'")
    print("-" * 20)
