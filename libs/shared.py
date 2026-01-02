import re
import html
try:
    import markdownify
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

def clean_html(text):
    if not text:
        return ""

    # Decode entities
    text = html.unescape(text)

    if not HAS_BEAUTIFULSOUP:
        # Fallback: Just return unescaped text without stripping tags
        return text.strip()

    # Normalize line endings and standardized types of BR tags
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Standardize noisy br tags (like <br type="_moz">)
    text = re.sub(r'<br\b[^>]*>', '<br/>', text, flags=re.I)

    # Pre-process newlines to <br> to preserve them
    text = text.replace('\n', '<br/>')

    # Collapse multiple consecutive line breaks early on
    text = re.sub(r'(<br/>\s*)+', '<br/>', text)

    # Fix specific encoding artifacts found in Anadolu content
    # \x1e and \x1f appear to be corrupted 'i' characters
    text = text.replace('\x1e', 'i').replace('\x1f', 'i')

    # Replace non-breaking spaces with normal spaces
    text = text.replace('\xa0', ' ')

    # Remove invisible zero-width characters (U+200B, U+200C, U+200D, U+FEFF)
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

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

    # 4. Strip attributes from strict tags (preserving formatting)
    strict_tags = ['strong', 'b', 'i', 'em', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'ul', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'sup', 'sub', 'ins']
    for tag_name in strict_tags:
        for tag in soup.find_all(tag_name):
            tag.attrs = {}

    # 5. Smart strip for ol, p, u, span, ins
    allowed_attrs = {
        'ol': ['type', 'start', 'style'],
        'p': ['style'],
        'u': ['style'],
        'ins': ['style'],
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

    # 7. Unwrap p and div tags (they often cause line breaks)
    for tag in soup.find_all(['p', 'div']):
        # If the tag has content, ensure it has a newline after it
        if tag.get_text(strip=True):
            tag.insert_after(soup.new_string("\n"))
        tag.unwrap()

    # Get string
    cleaned_text = soup.decode_contents().strip()

    # Collapse multiple spaces and remove isPasted markers
    cleaned_text = cleaned_text.replace('id="isPasted"', '')
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)

    # Remove empty tags again after unwrapping (often leaves <b></b> etc)
    cleaned_text = re.sub(r'<([a-z0-9]+)[^>]*>\s*</\1>', '', cleaned_text, flags=re.IGNORECASE)

    # Collapse multiple newlines/br tags
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
    cleaned_text = re.sub(r'(<br\b[^>]*>\s*)+', '<br/>', cleaned_text, flags=re.IGNORECASE)

    # Remove leading/trailing line breaks and whitespace
    # Only if there's other content to preserve. If it's JUST <br/> and whitespace, leave it.
    if re.sub(r'<br\b[^>]*>|&lt;br\s*/?&gt;|\s|\n', '', cleaned_text, flags=re.I):
        cleaned_text = re.sub(r'^(<br\b[^>]*>|\s|\n)+', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'(<br\b[^>]*>|\s|\n)+$', '', cleaned_text, flags=re.IGNORECASE)

    return cleaned_text.strip()

if HAS_MARKDOWNIFY:
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
        def convert_ins(self, el, text, parent_tags=None):
            return str(el)
else:
    class HTMLPreservingConverter:
        def convert(self, text):
            # Fallback: Return original text with minor cleanups
            return text

def safe_html_to_markdown(text):
    if not text: return ""

    # Pre-process text to replace <br> with newlines before markdownify
    # Strip spaces around br tags to avoid " ? <br />" artifacts
    text = re.sub(r'\s*<br\b[^>]*>\s*', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '', text, flags=re.IGNORECASE)

    # Protect &lt; and &gt; from markdownify's unescaping
    text = text.replace('&lt;', '[[LT]]').replace('&gt;', '[[GT]]')
    text = text.replace('&LT;', '[[LT]]').replace('&GT;', '[[GT]]')

    if HAS_MARKDOWNIFY:
        converter = HTMLPreservingConverter(autolinks=False)
    else:
        converter = HTMLPreservingConverter()

    converted = converter.convert(text).strip()

    # Restore protected entities
    converted = converted.replace('[[LT]]', '&lt;').replace('[[GT]]', '&gt;')

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

    # Strip trailing spaces from each line to prevent " <br />" artifacts later
    converted = re.sub(r' +$', '', converted, flags=re.MULTILINE)

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
                # Aggressively remove any remaining literal <br> tags (already handled by clean_html usually)
                opt_text_formatted = re.sub(r'<br\b[^>]*>', ' ', opt_text_formatted, flags=re.IGNORECASE)
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
