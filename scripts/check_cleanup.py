
import re
from bs4 import BeautifulSoup

def cleanup_logic(text):
    # Simulate clean_html steps

    # 1. Collapse multiple spaces (excluding tags? No, on the string)
    # But we need to be careful not to merge attributes if we do it on HTML string.
    # Doing it on the final string from soup is safer.

    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = str(soup).strip()

    # Collapse multiple spaces (visual spaces)
    # We use [ \t]+ to match spaces and tabs, but not newlines (though newlines should be <br> by now)
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

    # Collapse multiple <br> tags to single <br/>
    cleaned_text = re.sub(r'(<br\s*/?>\s*)+', '<br/>', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text

input_text = "Text  with   spaces.<br><br> <br />New line."
print(f"Input: {repr(input_text)}")
output_text = cleanup_logic(input_text)
print(f"Output: {repr(output_text)}")

if "  " not in output_text and "<br/><br/>" not in output_text and "<br/>" in output_text:
    print("SUCCESS: Collapsed spaces and brs.")
else:
    print("FAILURE: Did not collapse correctly.")
