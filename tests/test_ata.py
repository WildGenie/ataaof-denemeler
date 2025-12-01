import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ata.fetch import AtaPipeline

class TestAtaPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = AtaPipeline("raw", "json", "full", "md")

    @patch('requests.get')
    def test_fetch_raw_questions_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"SoruID": 1, "SoruMetni": "Test Q"}
        ]
        mock_get.return_value = mock_response

        course = {"DersId": "123"}
        questions = self.pipeline.fetch_raw_questions(course, 1)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["SoruID"], 1)

    @patch('requests.get')
    def test_fetch_raw_questions_failure(self, mock_get):
        # Mock failure
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        course = {"DersId": "123"}
        questions = self.pipeline.fetch_raw_questions(course, 1)

        # Should return empty list after retries
        self.assertEqual(len(questions), 0)

if __name__ == '__main__':
    unittest.main()
