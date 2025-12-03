
import unicodedata

def turkish_to_ascii(text):
    """Convert Turkish characters to ASCII equivalents."""
    turkish_map = {
        'ç': 'c', 'Ç': 'c',
        'ğ': 'g', 'Ğ': 'g',
        'ı': 'i', 'I': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o',
        'ş': 's', 'Ş': 's',
        'ü': 'u', 'Ü': 'u'
    }
    for turkish_char, ascii_char in turkish_map.items():
        text = text.replace(turkish_char, ascii_char)
    return text

def normalize_name_current(name):
    """Current implementation of normalize_name."""
    return unicodedata.normalize('NFC', name).lower().replace(" ", "")

def normalize_name_proposed(name):
    """Proposed implementation of normalize_name with turkish_to_ascii."""
    name = unicodedata.normalize('NFC', name)
    name = turkish_to_ascii(name)
    return name.lower().replace(" ", "")

test_cases = [
    ("Ara Sınav.pdf", "Ara Sinav.pdf"),
    ("Dönem Sonu.pdf", "Donem Sonu.pdf"),
    ("GÜZ ARA.pdf", "Guz Ara.pdf"),
    ("İktisat.pdf", "Iktisat.pdf"),
    ("Çağdaş.pdf", "Cagdas.pdf"),
    ("Öğrenme.pdf", "Ogrenme.pdf"),
    ("Şey.pdf", "Sey.pdf"),
    ("Ünite.pdf", "Unite.pdf"),
]

print(f"{'File 1':<20} | {'File 2':<20} | {'Current Match':<13} | {'Proposed Match':<13}")
print("-" * 75)

for f1, f2 in test_cases:
    n1_curr = normalize_name_current(f1)
    n2_curr = normalize_name_current(f2)
    match_curr = n1_curr == n2_curr

    n1_prop = normalize_name_proposed(f1)
    n2_prop = normalize_name_proposed(f2)
    match_prop = n1_prop == n2_prop

    print(f"{f1:<20} | {f2:<20} | {str(match_curr):<13} | {str(match_prop):<13}")
