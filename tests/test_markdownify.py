import markdownify
from markdownify import MarkdownConverter

text = "1m<sup>2</sup> test <sub>sub</sub>"

class RobustCustomConverter(MarkdownConverter):
    def convert_sup(self, el, text, parent_tags=None):
        return str(el)
    def convert_sub(self, el, text, parent_tags=None):
        return str(el)

try:
    md2 = RobustCustomConverter().convert(text)
    print(f"RobustCustomConverter: {md2}")
except Exception as e:
    print(f"Error: {e}")
