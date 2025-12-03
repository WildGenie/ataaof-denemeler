
import unicodedata
import re

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

def extract_year_and_type(filename):
    """Extract year range and exam type from filename."""
    # Normalize Unicode first!
    filename_normalized = unicodedata.normalize('NFC', filename)
    # Convert Turkish chars to ASCII
    filename_ascii = turkish_to_ascii(filename_normalized)
    # Remove spaces and lowercase
    filename_clean = filename_ascii.lower().replace(" ", "")

    print(f"Original: {filename}")
    print(f"Normalized: {filename_normalized}")
    print(f"ASCII: {filename_ascii}")
    print(f"Clean: {filename_clean}")

    # Extract year range
    year_match = re.search(r'20\d{2}-20\d{2}', filename_clean)
    year_range = year_match.group(0) if year_match else None

    # Extract single year (for Yaz Okulu)
    single_year_match = re.search(r'20\d{2}(?!-)', filename_clean)
    single_year = single_year_match.group(0) if single_year_match else None

    # Determine exam type - check space-less patterns
    exam_type = None
    if 'donemsonu' in filename_clean or 'final' in filename_clean:
        exam_type = 'Dönem Sonu'
    elif 'arasinav' in filename_clean or 'vize' in filename_clean or 'baharara' in filename_clean or 'guzara' in filename_clean:
        exam_type = 'Ara Sınav'
    elif 'yazokulu' in filename_clean:
        exam_type = 'Yaz Okulu'
    elif 'tekders' in filename_clean:
        exam_type = 'Tek Ders'
    elif 'ucders' in filename_clean:
        exam_type = 'Üç Ders'

    return year_range, single_year, exam_type

# Test cases from report
filenames = [
    "DÖNEM SONU 2019-2020 Çıkmış Sınav Soruları.pdf",
    "ARA SINAV 2018-2019 Çıkmış Sınav Soruları.pdf",
    "YAZ OKULU 2023-2024 Çıkmış Sınav Soruları.pdf",
    "2024-2025 BAHAR ARA - A.pdf",
    "2023-2024 BAHAR ARA - A.pdf"
]

for f in filenames:
    print(f"\nTesting: {f}")
    print(extract_year_and_type(f))
