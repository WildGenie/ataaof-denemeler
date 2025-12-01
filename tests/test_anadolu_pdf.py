import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anadolu.fetch import AnadoluPipeline

class TestAnadoluPDF(unittest.TestCase):
    def setUp(self):
        self.pipeline = AnadoluPipeline("raw", "json", "full", "md")

    @patch('anadolu.fetch.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_fetch_pdf_success(self, mock_exists, mock_file, mock_get):
        mock_exists.return_value = False

        # Mock RandPart response
        mock_rand_response = MagicMock()
        mock_rand_response.status_code = 200
        mock_rand_response.json.return_value = {"RandPart": "RANDOM_PART"}

        # Mock PDF download response
        mock_pdf_response = MagicMock()
        mock_pdf_response.status_code = 200
        mock_pdf_response.content = b'PDF_CONTENT'

        # Configure side_effect for multiple calls
        mock_get.side_effect = [mock_rand_response, mock_pdf_response, mock_pdf_response]

        course = {"DersKodu": "CODE", "CourseName": "Course", "Donem": 1}
        self.pipeline.fetch_pdf(course, 1)

        # Check calls
        self.assertEqual(mock_get.call_count, 3) # 1 for RandPart, 2 for PDFs (Exam + Solution)

        # Check file writes
        self.assertEqual(mock_file.call_count, 2)
        handle = mock_file()
        handle.write.assert_called_with(b'PDF_CONTENT')

    @patch('anadolu.fetch.requests.get')
    def test_fetch_pdf_no_randpart(self, mock_get):
        # Mock response without RandPart
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {} # Empty
        mock_get.return_value = mock_response

        course = {"DersKodu": "CODE", "CourseName": "Course", "Donem": 1}
        self.pipeline.fetch_pdf(course, 1)

        # Should stop after first call
        self.assertEqual(mock_get.call_count, 1)

    @patch('anadolu.fetch.requests.get')
    def test_fetch_chapters_success(self, mock_get):
        # Mock successful chapters response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "CourseCode": "GIT301U",
            "CourseName": "Git ve Versiyon Kontrol",
            "Chapters": [
                {"ChapterId": 1, "Title": "Giriş", "Order": 1},
                {"ChapterId": 2, "Title": "Temel Kavramlar", "Order": 2}
            ]
        }
        mock_get.return_value = mock_response

        result = self.pipeline.fetch_chapters("GIT301U")

        # Verify the call was made
        self.assertEqual(mock_get.call_count, 1)
        # Verify result contains chapters
        self.assertIsNotNone(result)
        self.assertEqual(len(result.get('Chapters', [])), 2)
        self.assertEqual(result['CourseCode'], 'GIT301U')

    @patch('anadolu.fetch.requests.get')
    def test_fetch_chapters_error(self, mock_get):
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.pipeline.fetch_chapters("INVALID")

        # Should return None on error
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
