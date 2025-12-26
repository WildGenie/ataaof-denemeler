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
    text = text.replace('\n', '<br/>')

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
    strict_tags = ['strong', 'b', 'i', 'em', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'ul', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'sup', 'sub', 'br']
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
    cleaned_text = re.sub(r'(<br\b[^>]*>\s*)+', '<br/>', cleaned_text, flags=re.IGNORECASE)

    # 8. Remove trailing <br> tags
    cleaned_text = re.sub(r'\s*<br\b[^>]*>\s*$', '', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text

class HTMLPreservingConverter(markdownify.MarkdownConverter):
    def convert_sup(self, el, text, parent_tags=None):
        return str(el)
    def convert_sub(self, el, text, parent_tags=None):
        return str(el)
    def convert_u(self, el, text, parent_tags=None):
        return str(el)
    def convert_b(self, el, text, parent_tags=None):
        return str(el)
    def convert_i(self, el, text, parent_tags=None):
        return str(el)
    def convert_em(self, el, text, parent_tags=None):
        return str(el)
    def convert_strong(self, el, text, parent_tags=None):
        return str(el)

def safe_html_to_markdown(text):
    if not text: return ""

    # Pre-process text to replace <br> with newlines before markdownify
    text = re.sub(r'<br\b[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)

    converter = HTMLPreservingConverter(autolinks=False)
    converted = converter.convert(text).strip()

    # Escape dots after numbers at the start of a line to prevent markdown list parsing
    converted = re.sub(r'^(\d+)\.', r'\1\.', converted, flags=re.MULTILINE)

    # Convert escaped markdown characters back to markdown
    # Markdownify escapes * to \*, but we might want them as * if they were in the text or converted from b/strong
    # Wait, if we preserve b/strong as HTML, then * shouldn't be here from them.
    # But if the text itself contained *, markdownify escapes it.
    # However, user likely wants literal * if they typed it, OR markdown bolding if they typed it?
    # The issue is "\*\*sadece\*\*" appearing. This means original text had "**" or converter added it and escaped it?
    # Actually, Markdownify converts <b> to ** by default.
    # BUT we overrode convert_b to return plain HTML.
    # So if we see \*\*, it means the input text had ** and markdownify escaped it.
    # OR input had <b>, we returned <b>, and nothing added **.
    # The user says: "\*\*sadece\*\*".
    # This implies markdownify is escaping these characters.
    # Let's unescape common markdown syntax that we might want to be valid?
    # Or simply unescape the backslashes for specific chars.

    converted = converted.replace(r'\*\*', '**').replace(r'\*', '*')
    converted = converted.replace(r'\_', '_')
    converted = converted.replace(r'\.', '.')

    return converted

def questions_to_markdown(questions):
    md = ""
    # safe_convert was here, now using safe_html_to_markdown globally

    for i, q in enumerate(questions, 1):
        # Use custom converter to preserve HTML content like sup/sub
        q_text_content = q.get('SoruMetni') or q.get('question') or ""
        q_text_raw = safe_html_to_markdown(q_text_content)
        # Replace newlines with <br /> for questions, but ensure no double <br />
        q_text_formatted = q_text_raw.replace('\n', '<br />')
        # Collapse multiple <br /> and remove surrounding spaces
        q_text_formatted = re.sub(r'\s*(<br\b[^>]*>\s*)+', '<br />', q_text_formatted)

        # Get index number if provided in question object, else use enumeration
        q_idx = i

        md += f"{q_idx}. {q_text_formatted}\n"

        options = ['A', 'B', 'C', 'D', 'E']
        for opt in options:
            # Handle correct answer check
            is_correct = False
            correct_answer = q.get('DogruCevap') or q.get('correctAnswer') # Fallback if specific convention used

            # Sometimes correct answer is index?
            if 'correctIndex' in q and q['correctIndex'] is not None:
                # Assuming options list matches A,B,C... order
                # but here we iterate options A,B,C..
                # This logic is tricky if data formats mix.
                # Let's stick to DogruCevap matching 'A','B' etc.
                pass

            if correct_answer and str(correct_answer).strip().upper() == opt:
                is_correct = True

            prefix = "**Cevap " if is_correct else ""
            suffix = "**" if is_correct else ""

            # Construct the list item prefix: "    - A-) "
            list_item_prefix = f"    - {prefix}{opt}-) "

            opt_content = q.get(opt, "")
            if opt_content:
                opt_text_raw = safe_html_to_markdown(opt_content)
                # Replace newlines with space in options
                opt_text_formatted = opt_text_raw.replace('\n', ' ')
                # Aggressively remove any remaining <br> tags
                opt_text_formatted = re.sub(r'<br\b[^>]*>|&lt;br\s*/?&gt;', ' ', opt_text_formatted, flags=re.IGNORECASE)
                # Collapse multiple spaces
                opt_text_formatted = re.sub(r'\s+', ' ', opt_text_formatted).strip()
            else:
                opt_text_formatted = ""

            md += f"{list_item_prefix}{opt_text_formatted}{suffix}\n"

        if q.get('Aciklama'):
            explanation = safe_html_to_markdown(q['Aciklama'])
            # Replace newlines with <br /> to match question formatting
            explanation = explanation.replace('\n', '<br />')
            # Collapse multiple <br /> tags
            explanation = re.sub(r'(<br\b[^>]*>\s*)+', '<br />', explanation)
            md += f"\n    > **Açıklama:** {explanation}\n\n"

        md += "    <hr />\n"
    return md
