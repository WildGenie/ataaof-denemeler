from libs.shared import clean_html

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
    'Line 1\nLine 2',

    # BR handling
    'Text<br type="_moz" />More Text',
    'Text<br type="_moz">More Text'
]

if __name__ == "__main__":
    for t in test_cases:
        print(f"Original: {repr(t)}")
        cleaned = clean_html(t)
        print(f"Cleaned : {repr(cleaned)}")
        print("-" * 20)
