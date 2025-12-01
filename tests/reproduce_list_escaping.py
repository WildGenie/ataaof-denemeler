
import sys
import os
import re
import markdownify

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.shared import HTMLPreservingConverter

def safe_convert(text):
    if not text: return ""
    converter = HTMLPreservingConverter()
    # Pre-process text to replace <br> with newlines before markdownify
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)

    converted = converter.convert(text).strip()
    return converted

raw_text = "<p>1. Düşünsel bir yanının olması</p> <p>2. İkna etme gücünün olması</p>"

print("--- Original Output ---")
converted = safe_convert(raw_text)
print(converted)

print("\n--- Proposed Fix Output ---")
# Escape dots after numbers at the start of a line
fixed = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)
print(fixed)

if "1\\." in fixed:
    print("\nSUCCESS: Dot is escaped.")
else:
    print("\nFAILURE: Dot is NOT escaped.")
