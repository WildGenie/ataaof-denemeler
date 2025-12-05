import unittest
import os
import json
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.genai_files_manager import GenAIFilesManager

class IntegrationTestGenAIFilesManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a dummy PDF file (minimal valid PDF structure)
        cls.test_pdf_path = "test_integration_dummy.pdf"
        pdf_content = (
            b"%PDF-1.0\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000111 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        )
        with open(cls.test_pdf_path, "wb") as f:
            f.write(pdf_content)

        # Temporary tracker path
        cls.test_tracker_path = "test_integration_tracker.json"
        if os.path.exists(cls.test_tracker_path):
            os.remove(cls.test_tracker_path)

    @classmethod
    def tearDownClass(cls):
        # Clean up local files
        if os.path.exists(cls.test_pdf_path):
            os.remove(cls.test_pdf_path)
        if os.path.exists(cls.test_tracker_path):
            os.remove(cls.test_tracker_path)

        # Note: We are NOT deleting the file from GenAI automatically here
        # to avoid accidental deletion of important stuff if logic is wrong.
        # But for a true integration test, we should clean up.
        # Let's try to clean up in the test method itself.

    def test_upload_flow(self):
        print("\n--- Starting Integration Test ---")

        # Initialize manager with test tracker
        manager = GenAIFilesManager(tracker_path=self.test_tracker_path)

        # 1. Upload File
        print("1. Uploading file...")
        uploaded_file = manager.upload_file(self.test_pdf_path, material_id="TEST_MAT_001")

        self.assertIsNotNone(uploaded_file.uri)
        self.assertEqual(uploaded_file.display_name, self.test_pdf_path)
        print(f"   Uploaded URI: {uploaded_file.uri}")

        # 2. Verify Tracker Update
        print("2. Verifying tracker...")
        with open(self.test_tracker_path, 'r') as f:
            tracker_data = json.load(f)

        self.assertIn("TEST_MAT_001", tracker_data)
        self.assertEqual(tracker_data["TEST_MAT_001"]["genai_name"], uploaded_file.name)
        print("   Tracker updated successfully.")

        # 3. Test Caching (Upload again)
        print("3. Testing caching (uploading again)...")
        cached_file = manager.upload_file(self.test_pdf_path, material_id="TEST_MAT_001")

        self.assertEqual(cached_file.uri, uploaded_file.uri)
        self.assertEqual(cached_file.name, uploaded_file.name)
        print("   Cache hit confirmed.")

        # 4. Clean up (Delete from GenAI)
        print("4. Cleaning up remote file...")
        try:
            manager.client.files.delete(name=uploaded_file.name)
            print("   Remote file deleted.")
        except Exception as e:
            print(f"   Failed to delete remote file: {e}")

if __name__ == '__main__':
    unittest.main()
