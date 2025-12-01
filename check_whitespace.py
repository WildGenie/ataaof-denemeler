
import sys
import os
from libs.shared import clean_html

# Add project root to sys.path
sys.path.append(os.getcwd())

text_with_nbsp = "Test&nbsp;Text"
text_with_unicode_nbsp = "Test\xa0Text"

print(f"Original (Entity): {repr(text_with_nbsp)}")
cleaned_entity = clean_html(text_with_nbsp)
print(f"Cleaned (Entity):  {repr(cleaned_entity)}")

print(f"\nOriginal (Unicode): {repr(text_with_unicode_nbsp)}")
cleaned_unicode = clean_html(text_with_unicode_nbsp)
print(f"Cleaned (Unicode):  {repr(cleaned_unicode)}")

if '\xa0' in cleaned_entity or '\xa0' in cleaned_unicode:
    print("\nRESULT: Special whitespace (\\xa0) is PRESERVED.")
else:
    print("\nRESULT: Special whitespace is REPLACED.")
