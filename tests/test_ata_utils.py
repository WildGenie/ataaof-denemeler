import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pdfminer.high_level before importing ata.utils.process_short_summary
sys.modules['pdfminer'] = MagicMock()
sys.modules['pdfminer.high_level'] = MagicMock()

from ata.utils.fetch_books import fetch_booklet
from ata.utils.fetch_units import download_pdf as download_unit_pdf
from ata.utils.fetch_short_summary import download_pdf as download_summary_pdf
from ata.utils.process_short_summary import download_short_summary, pdf_to_text, text_to_markdown

class TestAtaUtils(unittest.TestCase):

    @patch('ata.utils.fetch_books.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_fetch_booklet_success(self, mock_exists, mock_file, mock_get):
        mock_exists.return_value = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.content = b'PDF_CONTENT'
        mock_get.return_value = mock_response

        course = {"DersId": "123", "CourseName": "Test Course", "Donem": 1}
        fetch_booklet(course)

        mock_get.assert_called_once()
        mock_file.assert_called_once()
        handle = mock_file()
        handle.write.assert_called_with(b'PDF_CONTENT')

    @patch('ata.utils.fetch_units.urlopen')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_unit_pdf_success(self, mock_file, mock_urlopen):
        mock_response = MagicMock()
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.read.return_value = b'UNIT_PDF_CONTENT'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        success = download_unit_pdf("123", 1, "output.pdf")

        self.assertTrue(success)
        mock_file.assert_called_with("output.pdf", "wb")
        handle = mock_file()
        handle.write.assert_called_with(b'UNIT_PDF_CONTENT')

    @patch('ata.utils.fetch_short_summary.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_summary_pdf_success(self, mock_file, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.content = b'SUMMARY_PDF_CONTENT'
        mock_get.return_value = mock_response

        download_summary_pdf("Test Course", "123")

        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called_with(b'SUMMARY_PDF_CONTENT')

    def test_pdf_to_text(self):
        # Since we mocked the module at the top level, we can just verify the mock is called
        # But pdf_to_text calls extract_text.
        # We need to ensure our mock returns something.
        sys.modules['pdfminer.high_level'].extract_text.return_value = "Extracted Text"

        text = pdf_to_text(b'PDF_BYTES')
        self.assertEqual(text, "Extracted Text")

    def test_text_to_markdown(self):
        text = "LINE 1\n\nLINE 2"
        md = text_to_markdown("Course", text)
        self.assertIn("# Course — Kısa Özet", md)
        self.assertIn("LINE 1", md)

    @patch('ata.utils.process_short_summary.requests.get')
    @patch('ata.utils.process_short_summary.pdf_to_text')
    @patch('builtins.open', new_callable=mock_open)
    def test_process_short_summary_download(self, mock_file, mock_pdf_to_text, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.content = b'PDF'
        mock_get.return_value = mock_response

        mock_pdf_to_text.return_value = "Markdown Content"

        download_short_summary("Test Course", "123")

        mock_file.assert_called() # Should write MD file
        handle = mock_file()
        handle.write.assert_called()
        args, _ = handle.write.call_args
        self.assertIn("Markdown Content", args[0])

if __name__ == '__main__':
    unittest.main()
