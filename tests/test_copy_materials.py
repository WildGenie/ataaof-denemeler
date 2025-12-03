import unittest
import os
import sys
import tempfile
import shutil

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions from the script
# Since scripts/copy_local_materials.py is a script, we might need to import it dynamically or assume it's importable
# Let's try importing it as a module by adding scripts to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from copy_local_materials import index_source_files, find_file_in_index, similar

class TestCopyMaterials(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for testing
        self.test_dir = tempfile.mkdtemp()

        # Create some dummy files
        self.files = [
            "ExactMatch.pdf",
            "Partial Match File.pdf",
            "nested/Deep File.pdf",
            "nested/folder/Another File.epub"
        ]

        for f in self.files:
            path = os.path.join(self.test_dir, f)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as fh:
                fh.write("dummy content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_index_source_files(self):
        index = index_source_files(self.test_dir)

        # Check if all files are indexed
        # Keys are normalized: lowercase, no spaces
        self.assertIn("exactmatch.pdf", index)
        self.assertIn("partialmatchfile.pdf", index)
        self.assertIn("deepfile.pdf", index)
        self.assertIn("anotherfile.epub", index)

        # Check paths
        self.assertTrue(index["exactmatch.pdf"][0].endswith("ExactMatch.pdf"))

    def test_find_file_in_index_exact(self):
        index = index_source_files(self.test_dir)

        path, score = find_file_in_index(index, "ExactMatch.pdf")
        self.assertEqual(score, 1.0)
        self.assertTrue(path.endswith("ExactMatch.pdf"))

    def test_find_file_in_index_fuzzy(self):
        index = index_source_files(self.test_dir)

        # "Partial Match File.pdf" vs "Partial Match.pdf"
        # Normalized: partialmatchfile.pdf vs partialmatch.pdf
        path, score = find_file_in_index(index, "Partial Match.pdf", threshold=0.6)

        # Should match "Partial Match File.pdf"
        self.assertTrue(path.endswith("Partial Match File.pdf"))
        self.assertGreater(score, 0.8) # High similarity expected

    def test_find_file_in_index_no_match(self):
        index = index_source_files(self.test_dir)

        path, score = find_file_in_index(index, "Completely Different.pdf")
        self.assertIsNone(path)
        self.assertEqual(score, 0)

if __name__ == '__main__':
    unittest.main()
