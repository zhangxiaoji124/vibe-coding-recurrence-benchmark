import os
import unittest
import tempfile
import shutil
from storage import FileStorageService

class TestFileStorageFunctionality(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.service = FileStorageService(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_round0_save_and_list(self):
        saved = self.service.save_file("sample.txt", b"Hello, world!")
        self.assertTrue(os.path.exists(saved))
        files = self.service.list_files()
        self.assertIn("sample.txt", files)

    def test_round1_download_feature(self):
        # Round 1 requires read_file(filename) -> bytes
        if hasattr(self.service, "read_file"):
            self.service.save_file("read_test.txt", b"Downloadable content")
            content = self.service.read_file("read_test.txt")
            self.assertEqual(content, b"Downloadable content")

    def test_round2_delete_feature(self):
        # Round 2 requires delete_file(filename) -> bool
        if hasattr(self.service, "delete_file"):
            self.service.save_file("delete_test.txt", b"To be deleted")
            res = self.service.delete_file("delete_test.txt")
            self.assertTrue(res)
            self.assertNotIn("delete_test.txt", self.service.list_files())

    def test_round3_move_feature(self):
        # Round 3 requires move_file(src, dst) -> bool
        if hasattr(self.service, "move_file"):
            self.service.save_file("source.txt", b"Move me")
            res = self.service.move_file("source.txt", "target.txt")
            self.assertTrue(res)
            self.assertNotIn("source.txt", self.service.list_files())
            self.assertIn("target.txt", self.service.list_files())

    def test_round4_preview_feature(self):
        # Round 4 requires preview_file(filename, max_bytes) -> bytes
        if hasattr(self.service, "preview_file"):
            self.service.save_file("long_text.txt", b"1234567890abcdefghij")
            preview = self.service.preview_file("long_text.txt", 10)
            self.assertEqual(preview, b"1234567890")

if __name__ == "__main__":
    unittest.main()
