import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.shared import clean_html, questions_to_markdown

class TestShared(unittest.TestCase):
    def test_clean_html_basic(self):
        html_input = "<b>Hello</b> World"
        expected = "<b>Hello</b> World" # clean_html preserves bold
        self.assertEqual(clean_html(html_input), expected)

    def test_clean_html_entities(self):
        html_input = "A&nbsp;B"
        expected = "A B"
        self.assertEqual(clean_html(html_input), expected)

    def test_clean_html_newlines(self):
        html_input = "Line1\nLine2"
        # BeautifulSoup converts <br> to <br/>
        expected = "Line1<br/>Line2"
        self.assertEqual(clean_html(html_input), expected)

    def test_clean_html_paragraphs(self):
        html_input = "<p>Para1</p><p>Para2</p>"
        # p tags are converted to br and unwrapped
        # The implementation might leave a trailing br or handle it differently.
        # Let's check the implementation logic:
        # 1. p -> append br, unwrap.
        # 2. strip trailing br.
        self.assertEqual(clean_html(html_input), "Para1<br/>Para2")

    def test_clean_html_attributes(self):
        html_input = '<span style="color:red" class="foo">Text</span>'
        # span keeps style, removes class
        expected = '<span style="color:red">Text</span>'
        self.assertEqual(clean_html(html_input), expected)

    def test_questions_to_markdown(self):
        questions = [{
            'SoruMetni': 'Question <b>1</b>',
            'DogruCevap': 'A',
            'A': 'Option A',
            'B': 'Option B',
            'C': 'Option C',
            'D': 'Option D',
            'E': 'Option E',
            'Aciklama': 'Explanation'
        }]

        md = questions_to_markdown(questions)

        self.assertIn("1. Question **1**", md)
        self.assertIn("- **Cevap A-) Option A**", md)
        self.assertIn("- B-) Option B", md)
        self.assertIn("> **Açıklama:** Explanation", md)

if __name__ == '__main__':
    unittest.main()
