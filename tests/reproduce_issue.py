import re
import html

def clean_html(text):
    if not text:
        return ""

    # NEW: Unescape HTML entities first
    text = html.unescape(text)

    # NEW: Preserve newlines as <br /> before normalizing whitespace
    text = text.replace('\n', '<br />')

    # Replace non-breaking spaces and other unicode spaces with standard space
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')

    # Normalize whitespace (collapse multiple spaces/newlines to single space)
    text = re.sub(r'\s+', ' ', text).strip()

    # Unwrap specific tags (remove tag, keep content)
    # Block tags -> replace with space to prevent word merging
    # Added 'o' here because <o:p> often acts as a separator/paragraph break
    text = re.sub(r'</?(div|article|body|html|head|o)\b[^>]*>', ' ', text, flags=re.IGNORECASE)
    # Inline tags -> remove tag, keep content (no space added)
    text = re.sub(r'</?(font)\b[^>]*>', '', text, flags=re.IGNORECASE)

    # 1. Strip ALL attributes from strict tags
    strict_tags = 'strong|b|i|em|table|tr|td|th|tbody|thead|tfoot|ul|li|blockquote|h[1-6]|code|pre'
    text = re.sub(r'<(' + strict_tags + r')\s+[^>]*>', r'<\1>', text, flags=re.IGNORECASE)

    # 2. Smart strip for ol, p, u, span (preserve specific attributes)
    def clean_attrs(match):
        tag = match.group(1)
        attrs = match.group(2)

        # Define allowed attributes for each tag
        allowed = []
        if tag.lower() == 'ol':
            allowed = ['type', 'start', 'style']
        elif tag.lower() == 'p':
            allowed = ['style']
        elif tag.lower() == 'u':
            allowed = ['style']
        elif tag.lower() == 'span':
            allowed = ['style']

        # Simple regex to find attributes: name="value" or name='value'
        new_attrs = []
        for attr_match in re.finditer(r'([a-zA-Z0-9-]+)\s*=\s*(["\'])(.*?)\2', attrs):
            name = attr_match.group(1).lower()
            value = attr_match.group(3)
            if name in allowed:
                new_attrs.append(f'{name}="{value}"')

        if new_attrs:
            return f'<{tag} {" ".join(new_attrs)}>'
        else:
            return f'<{tag}>'

    # Match tags with attributes: <(ol|p|u|span)\s+([^>]*)>
    text = re.sub(r'<(ol|p|u|span)\s+([^>]*)>', clean_attrs, text, flags=re.IGNORECASE)

    # Remove empty tags
    all_tags = strict_tags + '|ol|p|u|span'
    for _ in range(2):
        text = re.sub(r'<(' + all_tags + r')>\s*</\1>', '', text, flags=re.IGNORECASE)

    # Collapse multiple <br> tags
    text = re.sub(r'\s*(<br\s*/?>\s*)+', '<br />', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*(<br\s*/?>\s*)+$', '', text, flags=re.IGNORECASE)

    # Escape < characters
    allowed_tags_pattern = r'/?(br|p|b|i|strong|em|u|ol|ul|li|table|tr|td|th|tbody|thead|tfoot|caption|colgroup|col|img|a|blockquote|code|pre|h[1-6]|span)\b'
    text = re.sub(r'<(?!' + allowed_tags_pattern + r')', '&lt;', text, flags=re.IGNORECASE)

    return text.strip()

test_cases = [
    'Bas konuş<div>kartları</div>',
    'Bas konuş\nkartları',
    'Bas konuş<br>kartları',
    'Bas konuş<span>kartları</span>',
    'Bas konuş<o>kartları</o>',
    'Bas konuş<o:p>kartları</o:p>',
    'Bas konuş<font>kartları</font>',
    'Bas konuş<p>kartları</p>',
    'Bas konuş kartları'
]

for t in test_cases:
    print(f"Original: {t}")
    print(f"Cleaned : {clean_html(t)}")
    print("-" * 20)
