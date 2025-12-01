
import sys
import os
import re
from bs4 import BeautifulSoup

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.shared import clean_html

explanation_raw = """<p class=\"p1\">Çıktı (Output), girdinin bir süreç tarafından değiştirilerek ürün hâline getirilmesidir. Örnek olarak kağıdın işlenip kitap haline gelmesi verilebilir. </p> <p class=\"p1\">Doğru cevap \"Çıktı\" seçeneğidir.</p>"""
title_raw = """<p class=\"p1\">Çıktı (Output), girdinin bir süreç tarafından değiştirilerek ürün hâline getirilmesidir. Örnek olarak kağıdın işlenip kitap haline gelmesi verilebilir. </p>\n<p class=\"p1\">Doğru cevap \"Çıktı\" seçeneğidir.</p>"""

print("--- Raw Inputs ---")
print(f"Explanation: {repr(explanation_raw)}")
print(f"Title:       {repr(title_raw)}")

cleaned_exp = clean_html(explanation_raw)
cleaned_title = clean_html(title_raw)

print("\n--- Cleaned Outputs ---")
print(f"Explanation: {repr(cleaned_exp)}")
print(f"Title:       {repr(cleaned_title)}")

# Current normalization logic
t_norm = cleaned_title.lower().strip()
e_norm = cleaned_exp.lower().strip()

print("\n--- Comparison ---")
print(f"Title in Explanation? {t_norm in e_norm}")
print(f"Explanation in Title? {e_norm in t_norm}")

# Proposed fix: Strip tags for comparison
def get_text_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

text_title = get_text_content(cleaned_title).lower().strip()
text_exp = get_text_content(cleaned_exp).lower().strip()

# Normalize whitespace
text_title = re.sub(r'\s+', ' ', text_title)
text_exp = re.sub(r'\s+', ' ', text_exp)

print("\n--- Text-Only Comparison ---")
print(f"Title Text: {repr(text_title)}")
print(f"Exp Text:   {repr(text_exp)}")
print(f"Title Text in Exp Text? {text_title in text_exp}")
print(f"Exp Text in Title Text? {text_exp in text_title}")
