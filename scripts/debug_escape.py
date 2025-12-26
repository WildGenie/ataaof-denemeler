import re
from markdownify import MarkdownConverter

class HTMLPreservingConverter(MarkdownConverter):
    def convert_sup(self, el, text, **kwargs): return f'<sup>{text}</sup>'
    def convert_sub(self, el, text, **kwargs): return f'<sub>{text}</sub>'
    def convert_u(self, el, text, **kwargs): return f'<u>{text}</u>'
    def convert_b(self, el, text, **kwargs): return f'<b>{text}</b>'
    def convert_i(self, el, text, **kwargs): return f'<i>{text}</i>'
    def convert_strong(self, el, text, **kwargs): return f'<b>{text}</b>'
    def convert_em(self, el, text, **kwargs): return f'<i>{text}</i>'
    def convert_ins(self, el, text, **kwargs): return f'<ins>{text}</ins>'

def safe_convert(text):
    if not text: return ""
    converter = HTMLPreservingConverter(autolinks=False)
    text = re.sub(r'<br\b[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)
    converted = converter.convert(text).strip()
    return converted

test_text = "Konuyla ilgili bilimsel çalışmalar yaşam boyunca ortaya çıkan bütün psikiyatrik bozuklukların <u>_________</u> ilk olarak çocukluk çağında ortaya çıktığını göstermektedir."
print(f"Original: {test_text}")
print(f"Converted: {safe_convert(test_text)}")
