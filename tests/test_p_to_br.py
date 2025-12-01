from bs4 import BeautifulSoup

def clean_p_tags(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Logic: Replace <p> with content + <br>
    # But avoid double <br> if one already exists?

    # Strategy:
    # For each p tag, append a <br> to it, then unwrap.
    # But we want to avoid adding <br> to the very last p tag if it's at the end of the document?
    # Or just add to all and let strip() handle trailing whitespace,
    # but <br> is not whitespace.

    # Let's try inserting <br> after the p tag, then unwrapping.
    p_tags = soup.find_all('p')
    for i, p in enumerate(p_tags):
        # Don't add br after the last p tag?
        # Or maybe we do want it if there's text after?

        # Simple approach: Insert <br> after every p tag
        # p.insert_after(soup.new_tag('br'))
        # p.unwrap()

        # Better approach:
        # If p tag has content, append <br> to the content (inside), then unwrap.
        # This keeps the <br> associated with the paragraph text.

        br = soup.new_tag('br')
        p.append(br)
        p.unwrap()

    return str(soup)

examples = [
    "<p>Line 1</p><p>Line 2</p>",
    "<p>Single Line</p>",
    "Text <p>Para</p> Text",
    "<p>Para 1</p>\n<p>Para 2</p>"
]

for ex in examples:
    print(f"Original: {ex}")
    print(f"Cleaned:  {clean_p_tags(ex)}")
    print("-" * 20)
