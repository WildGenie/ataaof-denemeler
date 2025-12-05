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
        self.pipeline = MagicMock()

    def test_process_course_wrapper_success(self):
        # Create mock args
        args = MagicMock()
        args.unit = None
        args.pdf = False
        args.chapters = False
        args.materials = False
        args.download_exams = False
        args.infographics = False
        args.summaries = False
        args.learn_questions = False
        args.questions = True

        course = {"DersKodu": "TEST101", "CourseName": "Test Course", "Donem": 1}

        success, result = process_course_wrapper(self.pipeline, course, args)

        self.assertTrue(success)
        self.assertEqual(result, "Test Course")
        self.pipeline.process_course.assert_called_once()

    def test_process_course_wrapper_with_pdf(self):
        args = MagicMock()
        args.unit = None
        args.pdf = True
        args.chapters = False
        args.materials = False
        args.download_exams = False
        args.infographics = False
        args.summaries = False
        args.learn_questions = False
        args.questions = False

        course = {"DersKodu": "TEST101", "CourseName": "Test Course", "Donem": 1}

        # Mock unit_count
        self.pipeline.unit_count = 8

        success, result = process_course_wrapper(self.pipeline, course, args)

        self.assertTrue(success)
        self.assertEqual(result, "Test Course")
        # Should call fetch_pdf 8 times
        self.assertEqual(self.pipeline.fetch_pdf.call_count, 8)

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
