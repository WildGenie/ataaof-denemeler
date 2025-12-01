import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from concurrent.futures import ThreadPoolExecutor

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anadolu.fetch import AnadoluPipeline, process_course_wrapper

class TestParallelProcessing(unittest.TestCase):
    def setUp(self):
        self.pipeline = AnadoluPipeline("raw", "json", "full", "md")

    @patch('anadolu.fetch.requests.get')
    def test_process_course_wrapper_success(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Questions": []}
        mock_get.return_value = mock_response

        # Create mock args
        args = MagicMock()
        args.unit = None
        args.pdf = False
        args.chapters = False

        course = {"DersKodu": "TEST101", "CourseName": "Test Course", "Donem": 1}

        success, result = process_course_wrapper(self.pipeline, course, args)

        self.assertTrue(success)
        self.assertEqual(result, "Test Course")

    @patch('anadolu.fetch.requests.get')
    def test_process_course_wrapper_with_pdf(self, mock_get):
        # Mock RandPart response
        mock_rand_response = MagicMock()
        mock_rand_response.status_code = 200
        mock_rand_response.json.return_value = {"RandPart": "RANDOM", "Questions": []}

        # Mock PDF download response
        mock_pdf_response = MagicMock()
        mock_pdf_response.status_code = 200
        mock_pdf_response.content = b'PDF_CONTENT'

        mock_get.side_effect = [mock_rand_response] + [mock_pdf_response] * 28  # 14 units * 2 PDFs

        args = MagicMock()
        args.unit = None
        args.pdf = True
        args.chapters = False

        course = {"DersKodu": "TEST101", "CourseName": "Test Course", "Donem": 1}

        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=False):
                success, result = process_course_wrapper(self.pipeline, course, args)

        self.assertTrue(success)
        self.assertEqual(result, "Test Course")

    def test_process_course_wrapper_error(self):
        # Test error handling
        args = MagicMock()
        args.unit = None
        args.pdf = False
        args.chapters = False

        # Course with missing DersKodu to trigger error
        course = {"CourseName": "Test Course", "Donem": 1}

        # This should handle the error gracefully
        success, result = process_course_wrapper(self.pipeline, course, args)

        # Should still succeed even with missing data
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
