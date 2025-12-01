import unittest
import sys
import os
import json
import shutil
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.pipeline import QuestionPipeline

class TestPipelineImplementation(QuestionPipeline):
    def fetch_raw_questions(self, course, unit):
        return [{"SoruID": 1, "SoruMetni": "Raw Question"}]

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/temp_output"
        self.raw_dir = os.path.join(self.test_dir, "raw")
        self.json_dir = os.path.join(self.test_dir, "json")
        self.full_dir = os.path.join(self.test_dir, "full")
        self.md_dir = os.path.join(self.test_dir, "md")

        self.pipeline = TestPipelineImplementation(
            self.raw_dir, self.json_dir, self.full_dir, self.md_dir
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_setup_directories(self):
        self.assertTrue(os.path.exists(self.raw_dir))
        self.assertTrue(os.path.exists(self.json_dir))

    def test_process_unit(self):
        course = {"CourseName": "Test Course", "Donem": 1, "DersiVeren": "TEST"}
        unit = 1

        questions = self.pipeline.process_unit(course, unit)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["SoruID"], 1)

        # Verify files created
        raw_file = os.path.join(self.raw_dir, "TEST - Dönem 1 - Test Course - Unite 01 - Raw.json")
        json_file = os.path.join(self.json_dir, "TEST - Dönem 1 - Test Course - Unite 01.json")

        self.assertTrue(os.path.exists(raw_file))
        self.assertTrue(os.path.exists(json_file))

    def test_get_or_fetch_raw_cache(self):
        course = {"CourseName": "Test Course", "Donem": 1, "DersiVeren": "TEST"}
        unit = 1

        # Create cache file manually
        raw_file = os.path.join(self.raw_dir, "TEST - Dönem 1 - Test Course - Unite 01 - Raw.json")
        with open(raw_file, 'w') as f:
            json.dump([{"SoruID": 99, "SoruMetni": "Cached"}], f)

        # Should load from cache, not fetch (fetch returns ID 1)
        questions = self.pipeline.get_or_fetch_raw(course, unit)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["SoruID"], 99)

if __name__ == '__main__':
    unittest.main()
