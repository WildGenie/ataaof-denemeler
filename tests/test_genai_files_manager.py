import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import json
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to patch its globals
import libs.genai_files_manager as gfm
from libs.genai_files_manager import GenAIFilesManager

class TestGenAIFilesManager(unittest.TestCase):

    def setUp(self):
        # Patch the global GEMINI_API_KEY in the module to ensure it has a value by default
        self.api_key_patcher = patch('libs.genai_files_manager.GEMINI_API_KEY', 'fake_key')
        self.api_key_patcher.start()

        # Mock genai.Client
        self.client_patcher = patch('libs.genai_files_manager.genai.Client')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = self.mock_client_class.return_value

        # Mock Tracker Path with a directory component
        self.tracker_patcher = patch('libs.genai_files_manager.TRACKER_PATH', '/tmp/fake_tracker.json')
        self.tracker_patcher.start()

    def tearDown(self):
        self.api_key_patcher.stop()
        self.client_patcher.stop()
        self.tracker_patcher.stop()

    def test_init_no_api_key(self):
        # Patch the global variable to None to simulate missing key
        with patch('libs.genai_files_manager.GEMINI_API_KEY', None):
            with self.assertRaises(ValueError):
                GenAIFilesManager()

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('os.path.exists', return_value=True)
    def test_init_loads_tracker(self, mock_exists, mock_file):
        manager = GenAIFilesManager()
        self.assertEqual(manager.tracker, {})
        mock_file.assert_called_with('/tmp/fake_tracker.json', 'r', encoding='utf-8')

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('os.path.exists', return_value=True) # Tracker exists
    @patch('libs.genai_files_manager.os.path.exists', return_value=True) # Local file exists
    @patch('os.makedirs') # Mock makedirs
    def test_upload_new_file(self, mock_makedirs, mock_local_exists, mock_tracker_exists, mock_file):
        manager = GenAIFilesManager()

        # Mock upload response
        mock_upload_file = MagicMock()
        mock_upload_file.name = "files/123"
        mock_upload_file.uri = "https://fake.uri"
        mock_upload_file.state = "ACTIVE" # Directly active for simplicity
        mock_upload_file.size_bytes = 1024
        mock_upload_file.display_name = "Test File.pdf"
        mock_upload_file.create_time = "2023-01-01T00:00:00Z"

        self.mock_client.files.upload.return_value = mock_upload_file
        self.mock_client.files.get.return_value = mock_upload_file # For the wait loop check

        # Call upload
        result = manager.upload_file("path/to/Test File - 12345.pdf")

        # Assertions
        self.mock_client.files.upload.assert_called_once()
        self.assertEqual(result.uri, "https://fake.uri")

        # Check tracker update
        self.assertIn("12345", manager.tracker)
        self.assertEqual(manager.tracker["12345"]["genai_name"], "files/123")

    @patch('builtins.open', new_callable=mock_open, read_data='{"12345": {"genai_name": "files/existing", "genai_uri": "https://existing.uri"}}')
    @patch('os.path.exists', return_value=True)
    @patch('libs.genai_files_manager.os.path.exists', return_value=True)
    def test_upload_cached_active(self, mock_local_exists, mock_tracker_exists, mock_file):
        manager = GenAIFilesManager()

        # Mock get response for existing file
        mock_existing_file = MagicMock()
        mock_existing_file.state = "ACTIVE"
        mock_existing_file.uri = "https://existing.uri"
        self.mock_client.files.get.return_value = mock_existing_file

        # Call upload
        result = manager.upload_file("path/to/Test File - 12345.pdf")

        # Assertions
        self.mock_client.files.upload.assert_not_called() # Should NOT upload
        self.mock_client.files.get.assert_called_with(name="files/existing")
        self.assertEqual(result.uri, "https://existing.uri")

    @patch('builtins.open', new_callable=mock_open, read_data='{"12345": {"genai_name": "files/missing"}}')
    @patch('os.path.exists', return_value=True)
    @patch('libs.genai_files_manager.os.path.exists', return_value=True)
    @patch('os.makedirs')
    def test_upload_cached_but_missing_on_server(self, mock_makedirs, mock_local_exists, mock_tracker_exists, mock_file):
        manager = GenAIFilesManager()

        # Mock get raising exception (file not found on server)
        # Then return a valid file object
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.state = "ACTIVE"
        mock_uploaded_file.name = "files/new"
        mock_uploaded_file.uri = "https://new.uri"
        mock_uploaded_file.size_bytes = 100
        mock_uploaded_file.display_name = "Test"
        mock_uploaded_file.create_time = "now"

        self.mock_client.files.get.side_effect = [Exception("Not found"), mock_uploaded_file]

        # Mock upload response
        # The upload method returns the file object (or a job that resolves to it)
        # In our code we call files.upload(...), then files.get(...)
        # So files.upload should return something that has a .name
        mock_upload_op = MagicMock()
        mock_upload_op.name = "files/new"
        self.mock_client.files.upload.return_value = mock_upload_op

        # Call upload
        result = manager.upload_file("path/to/Test File - 12345.pdf")

        # Assertions
        self.mock_client.files.upload.assert_called_once()
        self.assertEqual(result.uri, "https://new.uri")

        # Tracker should be updated with new file
        self.assertEqual(manager.tracker["12345"]["genai_name"], "files/new")

if __name__ == '__main__':
    unittest.main()
