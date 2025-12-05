import unittest
import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.genai_files_manager import GenAIFilesManager
from tests.utils.pdf_generator import create_mock_exam_pdf

# Load environment variables
load_dotenv()

class TestRealPDFIntegration(unittest.TestCase):
    def setUp(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.skipTest("GEMINI_API_KEY not found in .env")

        self.manager = GenAIFilesManager(tracker_path="test_real_pdf_tracker.json")
        self.pdf_path = "test_real_exam.pdf"
        self.num_questions = 3

        # Generate PDF
        create_mock_exam_pdf(self.pdf_path, "Integration Test Course", self.num_questions)

    def tearDown(self):
        # Cleanup local file
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)

        # Cleanup tracker
        if os.path.exists("test_real_pdf_tracker.json"):
            os.remove("test_real_pdf_tracker.json")

        # Cleanup GenAI file (optional, but good practice)
        # We need the file object or name to delete it.
        # In a real scenario we might want to keep it or delete it.
        # For now, we rely on the manager's logic or just leave it (it will be garbage collected by GenAI eventually or we can delete it if we track it)
        pass

    def test_pdf_upload_and_content_verification(self):
        print(f"\nTesting with real PDF: {self.pdf_path}")

        # 1. Upload PDF
        print("Uploading to GenAI...")
        uploaded_file = self.manager.upload_file(
            local_path=self.pdf_path,
            material_id="TEST_REAL_PDF_001",
            display_name="Real PDF Integration Test"
        )

        self.assertIsNotNone(uploaded_file)
        print(f"Uploaded: {uploaded_file.uri}")

        # 2. Verify with Gemini
        print("Verifying content with Gemini...")
        client = genai.Client(api_key=self.api_key)

        prompt = "Bu PDF dosyasında kaç tane soru var? Sadece sayıyı yaz."

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(file_uri=uploaded_file.uri, mime_type="application/pdf"),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )

        print(f"Gemini Response: {response.text}")

        # 3. Assertions
        # The response should contain the number of questions (3)
        self.assertIn(str(self.num_questions), response.text)

        # 4. Clean up remote file
        try:
            client.files.delete(name=uploaded_file.name)
            print("Remote file deleted.")
        except Exception as e:
            print(f"Failed to delete remote file: {e}")

if __name__ == "__main__":
    unittest.main()
