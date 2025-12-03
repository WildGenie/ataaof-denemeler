import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.anadolu_pipeline import AnadoluPipeline

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

    @patch('requests.get')
    def test_process_learn_questions(self, mock_get):
        # Mock response for learn questions
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "QuestionAnswer": [
                {"Index": 1, "Question": "Q1", "Answer": "A1", "Title": "T1"}
            ]
        }
        mock_get.return_value = mock_response

        course = {"DersKodu": "CODE", "CourseName": "Test Course", "Donem": 1}

        # Mock file operations to avoid writing to disk
        with patch('builtins.open', unittest.mock.mock_open()), \
             patch('json.dump'), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False):

            self.pipeline.process_learn_questions(course, silent=True)

            # Verify API was called
            # We expect calls for units 1-8 (or configured count), but we break early if empty.
            # Here we mocked success, so it should call for unit 1 at least.
            self.assertTrue(mock_get.called)

    @patch('requests.get')
    def test_download_past_exams(self, mock_get):
        # Mock materials response
        mock_materials_response = MagicMock()
        mock_materials_response.status_code = 200
        # We need to mock reading the materials file, not fetching it (as download_past_exams reads local file)

        course = {"DersKodu": "CODE", "CourseName": "Test Course", "Donem": 1}

        # Mock file operations
        mock_file_content = json.dumps([
            {
                "Type": "PAST_EXAMS",
                "Materials": [
                    {"MaterialId": 101, "Name": "Exam 1", "UpdatedAt": "2023-01-01", "FileExtension": "application/pdf"}
                ]
            }
        ])

        with patch('builtins.open', unittest.mock.mock_open(read_data=mock_file_content)) as mock_file, \
             patch('json.load') as mock_json_load, \
             patch('json.dump'), \
             patch('os.makedirs'), \
             patch('os.path.exists', side_effect=[True, False, False]): # materials exists, dir not, file not

            # Setup json.load to return the data we want when reading materials
            # The first call is for materials, second for tracker
            mock_json_load.side_effect = [json.loads(mock_file_content), {}]

            # Mock download response
            mock_download_response = MagicMock()
            mock_download_response.status_code = 200
            mock_download_response.content = b"PDF CONTENT"
            mock_get.return_value = mock_download_response

            self.pipeline.download_past_exams(course, silent=True)

            # Verify download was attempted
            # URL should contain material ID
            args, _ = mock_get.call_args
            self.assertIn("101", args[0])

if __name__ == '__main__':
    unittest.main()
