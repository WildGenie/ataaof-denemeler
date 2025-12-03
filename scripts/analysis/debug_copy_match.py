
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

def test_match(target_name, source_name):
    print(f"\nTarget: {target_name}")
    print(f"Source: {source_name}")

    target_year_range, target_single_year, target_exam_type = extract_year_and_type(target_name)
    source_year_range, source_single_year, source_exam_type = extract_year_and_type(source_name)

    print(f"Target Info: {target_year_range}, {target_single_year}, {target_exam_type}")
    print(f"Source Info: {source_year_range}, {source_single_year}, {source_exam_type}")

    if target_exam_type != source_exam_type:
        print("FAIL: Type mismatch")
        return

    year_match = False
    if target_year_range and source_year_range:
        if target_year_range == source_year_range:
            year_match = True
    elif target_single_year and source_year_range:
        if target_single_year in source_year_range:
            year_match = True
    elif target_year_range and source_single_year:
            if source_single_year in target_year_range:
                year_match = True
    elif target_single_year and source_single_year:
        if target_single_year == source_single_year:
            year_match = True

    if year_match:
        print("SUCCESS: Match found")
    else:
        print("FAIL: Year mismatch")

# Test cases
test_match("Ara Sınav 2024-2025 - 634500.pdf", "ARA SINAV 2024-2025 Çıkmış Sınav Soruları.pdf")
test_match("Çıkmış Sınav Soruları AÖF Yaz Okulu - Yaz Okulu 2024-2025.pdf", "YAZ OKULU 2023-2024 Çıkmış Sınav Soruları.pdf")
