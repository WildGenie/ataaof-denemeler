import re
import markdownify

class HTMLPreservingConverter(markdownify.MarkdownConverter):
    def convert_sup(self, el, text, parent_tags=None):
        return str(el)
    def convert_sub(self, el, text, parent_tags=None):
        return str(el)

converter = HTMLPreservingConverter(autolinks=False)

def safe_convert(text):
    if not text: return ""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)
    converted = converter.convert(text).strip()
    converted = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)
    return converted

text = "&lt;body&gt;"
converted = safe_convert(text)
print(f"Original: {text}")
print(f"Converted: {converted}")

text2 = "<b>Bold</b>"
converted2 = safe_convert(text2)
print(f"Original: {text2}")
text3 = '<a href="http://google.com">http://google.com</a>'
converted3 = safe_convert(text3)
print(f"Original: {text3}")
print(f"Converted: {converted3}")
