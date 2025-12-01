import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anadolu.fetch import AnadoluPipeline

class TestAnadoluPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = AnadoluPipeline("raw", "json", "full", "md")

    @patch('requests.get')
    def test_fetch_raw_questions_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Questions": [{"QuestionId": 1, "Text": "Test"}]
        }
        mock_get.return_value = mock_response

        course = {"DersKodu": "CODE"}
        questions = self.pipeline.fetch_raw_questions(course, 1)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["QuestionId"], 1)

    def test_transform_question(self):
        # Test that it calls map_to_old_format (indirectly via result structure)
        raw_q = {
            "QuestionId": 123,
            "Text": "Desc",
            "CorrectAnswer": "A",
            "A": "OptA",
            "B": "OptB",
            "C": "OptC",
            "D": "OptD",
            "E": "OptE"
        }
        course = {"CourseName": "Course", "Donem": 1}

        transformed = self.pipeline.transform_question(raw_q, course, 1)

        self.assertEqual(transformed["SoruID"], 123)
        self.assertEqual(transformed["DersAd"], "Course")

if __name__ == '__main__':
    unittest.main()
