import unittest
import json
from libs.shared import questions_to_markdown
from libs.anadolu_lib import map_to_old_format

class TestAnadoluQuestion(unittest.TestCase):
    def test_specific_question_formatting(self):
        # Mock raw question data instead of reading from missing file
        # Based on assertions, we reconstruct the necessary parts
        raw_question = {
            "QuestionId": 3863644,
            "Text": "Test Question Text",
            "AnswerExplanation": "1. Öğrencilerin genel ihtiyaçlarını<br>2. Toplumun ihtiyaçlarını<br>3. Konu alanı ve felsefi temelleri<br>...<br>7. Program sonunda<br>8. Öğretimsel amaçları<br>...<br>14. Öğretimi değerlendir",
            "Title": "Test Title",
            "CorrectAnswer": "A",
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D",
            "E": "Option E"
        }

        # Use the actual system function to transform the question
        # map_to_old_format(api_question, course_name, unit_or_type, donem)
        processed_question = map_to_old_format(
            raw_question,
            course_name="Öğretim Tasarımı",
            unit_or_type=3,
            donem=7
        )



        # 3. Generate Markdown
        md = questions_to_markdown([processed_question])



        # Assertions to verify content presence
        # Check for list items 1-6
        self.assertIn("Öğrencilerin genel ihtiyaçlarını", md, "Item 1 missing")
        self.assertIn("Toplumun ihtiyaçlarını", md, "Item 2 missing")
        self.assertIn("felsefi temelleri", md.replace('­', ''), "Item 3 missing") # Handle soft hyphen if needed

        # Check for item 7
        self.assertIn("Program sonunda", md, "Item 7 missing")

        # Check for items 8-14
        self.assertIn("Öğretimsel amaçları", md, "Item 8 missing")
        self.assertIn("Öğretimi değerlendir", md, "Item 14 missing")

        # Assert backslash escaping for list items is present
        # We expect "1\. " because we re-enabled escaping
        self.assertIn(r"1\.", md, "List item 1 SHOULD be escaped")
        self.assertIn(r"7\.", md, "List item 7 SHOULD be escaped")

        # Assert presence of <br /> tags
        self.assertIn("<br />", md, "Should contain <br /> tags")
        # Assert NO double <br /> tags
        self.assertNotIn("<br /><br />", md, "Should NOT contain double <br /> tags")

    def test_moz_br_handling(self):
        # Construct a fake question with moz br tags
        fake_question = {
            "SoruMetni": "Line 1<br type=\"_moz\" />Line 2<br type=\"_moz\">Line 3",
            "Aciklama": "Exp 1<br type=\"_moz\" />Exp 2",
            "DogruCevap": "A",
            "A": "Opt A",
            "B": "Opt B",
            "C": "Opt C",
            "D": "Opt D",
            "E": "Opt E"
        }

        md = questions_to_markdown([fake_question])

        # Assertions
        self.assertIn("Line 1<br />Line 2<br />Line 3", md)
        self.assertIn("Exp 1<br />Exp 2", md)
        self.assertNotIn('type="_moz"', md)

    def test_ata_moz_br(self):
        # Specific ATA question provided by user
        ata_question = {
            "SoruID": 314509,
            "SoruMetni": "<strong>Aşağıdakilerden hangisi Dada&rsquo;nın ortaya &ccedil;ıktığı d&ouml;nemin sosyopolitik &ouml;zelliklerinden biridir?</strong><br type=\"_moz\" />\r\n",
            "A": "I. D&uuml;nya Savaşı&rsquo;nın yıkıcı etkisi ",
            "B": "Sanayi Devrimi&rsquo;nin etkisi ",
            "C": "Ekim Devrimi&rsquo;nin etkisi ",
            "D": "B&uuml;y&uuml;k Buhran&rsquo;ın etkisi ",
            "E": "Fransız İhtilali&rsquo;nin etkisi ",
            "DogruCevap": "A",
            "DersAd": "Grafik Tasarım Tarihi",
            "Somestre": 0,
            "DogruCevapSirasi": 1,
            "Unite": 7,
            "OlusturmaTarihi": "2025-07-28T08:49:01.01+03:00",
            "GelYer": 2,
            "DersId": 479,
            "OBSDersId": 82517,
            "CevapSira": 1
        }

        # We need to simulate the pipeline transform first because that's where clean_html is called
        # But questions_to_markdown calls safe_convert which also does some cleaning.
        # However, pipeline.transform_question calls clean_html explicitly.

        from libs.shared import clean_html

        # Simulate pipeline transform
        transformed_q = ata_question.copy()
        transformed_q['SoruMetni'] = clean_html(transformed_q['SoruMetni'])
        transformed_q['A'] = clean_html(transformed_q['A'])
        # ... other options ...

        md = questions_to_markdown([transformed_q])



        # Assertions
        # The <br type="_moz" /> should be removed or converted to <br /> if it was significant,
        # but here it is at the end of the line, so it might be stripped by "Remove trailing <br> tags" logic in clean_html
        self.assertNotIn('type="_moz"', md)
        self.assertNotIn('<br type="_moz" />', md)

        # Check that the text is clean
        self.assertIn("**Aşağıdakilerden hangisi Dada’nın ortaya çıktığı dönemin sosyopolitik özelliklerinden biridir?**", md)

        # Ensure no trailing <br /> if it was at the end
        # The regex `re.sub(r'\s*<br\b[^>]*>\s*$', '', cleaned_text, flags=re.IGNORECASE)` in clean_html should remove it.
        self.assertFalse(md.strip().endswith("<br />"))

    def test_messy_br_in_options(self):
        # Specific ATA question with messy BRs in options
        ata_question = {
            "SoruID": 267085,
            "SoruMetni": "<strong>Hristiyan Ortodoks Kilisesi’nde ibadete mahsus...</strong>",
            "A": "İkona",
            "B": "Minyatür",
            "C": "Fresko",
            "D": "Mozaik<br/> <br/><br> <br/></br>",
            "E": "Diptikon",
            "DogruCevap": "A",
            "DersAd": "Genel Sanat Tarihi",
            "Somestre": 1,
            "DogruCevapSirasi": 1,
            "Unite": 5,
            "OlusturmaTarihi": "2025-10-28T08:54:39.313",
            "GelYer": 2,
            "DersId": 454,
            "OBSDersId": 82515,
            "CevapSira": 1
        }

        md = questions_to_markdown([ata_question])



        # Assertions
        # Option D should be clean "Mozaik"
        # We expect the BRs to be replaced by spaces and then collapsed/trimmed
        self.assertIn("- D-) Mozaik", md)
        self.assertNotIn("Mozaik<br", md)
        self.assertNotIn("Mozaik <br", md)

if __name__ == '__main__':
    unittest.main()
