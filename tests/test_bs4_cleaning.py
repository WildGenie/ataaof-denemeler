from bs4 import BeautifulSoup, NavigableString, Tag
import re
import html

def clean_html_bs4(text):
    if not text:
        return ""

    # Decode entities first
    text = html.unescape(text)

    # Pre-process newlines to <br> to preserve them?
    # Or let BS4 handle it?
    # User wanted \n -> <br>.
    text = text.replace('\n', '<br>')

    soup = BeautifulSoup(text, 'html.parser')

    # 1. Handle o:p and other specific tags
    # Replace <o:p> with space (block-like)
    # Use strict regex to avoid matching 'strong', 'body', etc.
    for tag in soup.find_all(re.compile(r'^o(:p)?$', re.I)):
        # Replace with space + content
        # We can insert a space string before unwrapping
        tag.insert_before(" ")
        tag.unwrap()

    # 2. Unwrap noisy block tags with space
    # div, article, body, html, head
    for tag_name in ['div', 'article', 'body', 'html', 'head']:
        for tag in soup.find_all(tag_name):
            tag.insert_before(" ")
            tag.unwrap()

    # 3. Unwrap noisy inline tags (no space)
    # font
    for tag in soup.find_all('font'):
        tag.unwrap()

    # 4. Strip attributes from strict tags
    strict_tags = ['strong', 'b', 'i', 'em', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'ul', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre']
    # DEBUG
    print(f"Before strict strip: {soup}")
    for tag_name in strict_tags:
        for tag in soup.find_all(tag_name):
            print(f"Stripping attrs from {tag.name}")
            tag.attrs = {}
    # DEBUG
    print(f"After strict strip: {soup}")

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
    # Repeat a few times for nested empty tags?
    # Or recursive function.
    # Simple pass:
    for tag in soup.find_all():
        if tag.name not in ['img', 'br', 'a'] and not tag.get_text(strip=True):
            # Check if it has no children tags (like <img>)
            if not tag.find(['img', 'br', 'a']):
                tag.decompose()

    # 7. Remove wrapping <p> if it's the ONLY top-level element
    # Get top-level elements ignoring whitespace strings
    contents = [c for c in soup.contents if not (isinstance(c, NavigableString) and not c.strip())]

    if len(contents) == 1 and isinstance(contents[0], Tag) and contents[0].name == 'p':
        contents[0].unwrap()

    # 8. Escape < that are not tags
    # BS4 handles output escaping, but we need to be careful.
    # str(soup) will produce valid HTML.
    # But we want to ensure < in text is &lt;
    # BS4 usually does this automatically for text nodes.

    return str(soup).strip()

test_cases = [
    # User's problem case (multi-paragraph)
    '<p>I. Dadaist bir sanatçıdır</p> <p>II. Kavramsal ve Fluxus gibi 1960 sonrası akımların esin kaynağı olmuştur</p> <p>III. Tabure ve bisiklet tekerleği isimli çalışmayı yapan sanatçıdır</p> <p>Yukarıdakilerden hangisi ya da hangileri Marcel Duchamp\' a aittir?</p>',

    # Wrapping p case (should be removed)
    '<p>Otizm spektrum bozukluğu</p>',

    # Merged words case
    'Bas konuş<o:p>kartları</o:p>',
    'Bas konuş<o>kartları</o>',
    'Bas konuş<div>kartları</div>',

    # Attributes case
    '<span style="text-decoration: underline;">Test</span>',
    '<p style="text-align: center;">Centered</p>',
    '<strong class="bold">Bold</strong>',

    # Nested empty tags
    '<p><strong> </strong></p>',

    # Strong tag check
    '<strong>Bold</strong>',
    'Text <strong>Bold</strong> Text',

    # Less than symbol checks
    'a < b',
    'a <b',
    '1 < 2',
    'başlıyacak (< başla-y-acak)',

    # Newlines
    'Line 1\nLine 2'
]

for t in test_cases:
    print(f"Original: {t}")
    cleaned = clean_html_bs4(t)
    print(f"Cleaned : {cleaned}")
    print("-" * 20)
