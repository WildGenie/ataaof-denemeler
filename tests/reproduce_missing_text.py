
import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.shared import clean_html, questions_to_markdown

raw_text = """<p>Çekimler sırasında aydınlatma amaçlı kullanılan yapay  ışık kaynakları aşağıdakilerden hangisileridir?</p>\n<p>I-Mum</p>\n<p>II-Gaz lambası</p>\n<p>III-Kamp ateşi</p>\n<p>IV-Şimşek</p>"""

print("--- Original Text ---")
print(repr(raw_text))

cleaned = clean_html(raw_text)
print("\n--- Cleaned Text ---")
print(repr(cleaned))

q = {
    "SoruMetni": cleaned,
    "DogruCevap": "C",
    "A": "I-IV", "B": "II-III", "C": "I-II-III", "D": "IV-III", "E": "I-III-IV"
}

md = questions_to_markdown([q])
print("\n--- Markdown Output ---")
print(md)
