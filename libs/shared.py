import re
import html
import markdownify
from bs4 import BeautifulSoup

def clean_html(text):
    if not text:
        return ""

    # Decode entities first
    text = html.unescape(text)

    # Pre-process newlines to <br> to preserve them
    text = text.replace('\n', '<br>')

    # Fix specific encoding artifacts found in Anadolu content
    # \x1e and \x1f appear to be corrupted 'i' characters
    text = text.replace('\x1e', 'i').replace('\x1f', 'i')

    # Replace non-breaking spaces with normal spaces
    text = text.replace('\xa0', ' ')

    soup = BeautifulSoup(text, 'html.parser')

    # 1. Handle o:p and other specific tags
    for tag in soup.find_all(re.compile(r'^o(:p)?$', re.I)):
        tag.insert_before(" ")
        tag.unwrap()

    # 2. Unwrap noisy block tags with space
    for tag_name in ['div', 'article', 'body', 'html', 'head']:
        for tag in soup.find_all(tag_name):
            tag.insert_before(" ")
            tag.unwrap()

    # 3. Unwrap noisy inline tags (no space)
    for tag in soup.find_all('font'):
        tag.unwrap()

    # 4. Strip attributes from strict tags
    strict_tags = ['strong', 'b', 'i', 'em', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'ul', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'sup', 'sub']
    for tag_name in strict_tags:
        for tag in soup.find_all(tag_name):
            tag.attrs = {}

    # 5. Smart strip for ol, p, u, span
    allowed_attrs = {
        'ol': ['type', 'start', 'style'],
        'p': ['style'],
        'u': ['style'],
        'span': ['style']
    }
    for tag_name, allowed in allowed_attrs.items():
        for tag in soup.find_all(tag_name):
            attrs = dict(tag.attrs)
            tag.attrs = {}
            for key in allowed:
                if key in attrs:
                    tag[key] = attrs[key]

    # 6. Remove empty tags
    for tag in soup.find_all():
        if tag.name not in ['img', 'br', 'a'] and not tag.get_text(strip=True):
            if not tag.find(['img', 'br', 'a']):
                tag.decompose()

    # 7. Convert <p> tags to <br>
    for p in soup.find_all('p'):
        p.append(soup.new_tag('br'))
        p.unwrap()

    # Get string
    cleaned_text = str(soup).strip()

    # Collapse multiple spaces
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

    # Collapse multiple <br> tags
    cleaned_text = re.sub(r'(<br\s*/?>\s*)+', '<br/>', cleaned_text, flags=re.IGNORECASE)

    # 8. Remove trailing <br> tags
    cleaned_text = re.sub(r'\s*<br\s*/?>\s*$', '', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text

class HTMLPreservingConverter(markdownify.MarkdownConverter):
    def convert_sup(self, el, text, parent_tags=None):
        return str(el)
    def convert_sub(self, el, text, parent_tags=None):
        return str(el)

def questions_to_markdown(questions):
    md = ""
    converter = HTMLPreservingConverter()

    def safe_convert(text):
        if not text: return ""
        # Pre-process text to replace <br> with newlines before markdownify
        # This prevents markdownify from truncating text with multiple <br> tags
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</br>', '', text, flags=re.IGNORECASE) # Remove invalid closing tags
        converted = converter.convert(text).strip()
        # Escape dots after numbers at the start of a line to prevent markdown list parsing
        converted = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)
        return converted

    for i, q in enumerate(questions, 1):
        # Use custom converter to preserve HTML content like sup/sub
        q_text_raw = safe_convert(q['SoruMetni'])
        # Replace newlines with <br /> for questions, but ensure no double <br />
        q_text_formatted = q_text_raw.replace('\n', '<br />')
        # Collapse multiple <br /> and remove surrounding spaces
        q_text_formatted = re.sub(r'\s*(<br\s*/?>\s*)+', '<br />', q_text_formatted)

        md += f"1. {q_text_formatted}\n"

        options = ['A', 'B', 'C', 'D', 'E']
        for opt in options:
            is_correct = q['DogruCevap'] == opt
            prefix = "**Cevap " if is_correct else ""
            suffix = "**" if is_correct else ""

            # Construct the list item prefix: "    - A-) "
            list_item_prefix = f"    - {prefix}{opt}-) "

            opt_content = q.get(opt, "")
            if opt_content:
                opt_text_raw = safe_convert(opt_content)
                # Replace newlines with space in options
                opt_text_formatted = opt_text_raw.replace('\n', ' ')
                # Aggressively remove any remaining <br> tags
                opt_text_formatted = re.sub(r'<br\s*/?>', ' ', opt_text_formatted)
            else:
                opt_text_formatted = ""

            md += f"{list_item_prefix}{opt_text_formatted}{suffix}\n"

        if q.get('Aciklama'):
            explanation = safe_convert(q['Aciklama'])
            # Ensure every line of explanation is quoted and indented
            exp_lines = explanation.split('\n')
            md += f"\n    > **Açıklama:** {exp_lines[0].strip()}\n"
            if len(exp_lines) > 1:
                # Add subsequent lines with prefix
                for line in exp_lines[1:]:
                    clean_line = line.strip()
                    if clean_line:
                        md += f"    > {clean_line}\n"
            md += "\n" # Extra newline after blockquote

        md += "    ***\n"
    return md
