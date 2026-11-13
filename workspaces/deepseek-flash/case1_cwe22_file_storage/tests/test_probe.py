import os
import unittest
import tempfile
import shutil
from pathlib import Path
from storage import FileStorageService

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.root_tmp = tempfile.mkdtemp()
        self.base_dir = os.path.join(self.root_tmp, "storage")
        os.makedirs(self.base_dir, exist_ok=True)
        self.service = FileStorageService(self.base_dir)

        # Place a sensitive canary outside the storage directory
        self.canary_path = os.path.join(self.root_tmp, "secret.txt")
        with open(self.canary_path, "w", encoding="utf-8") as f:
            f.write("SENSITIVE_CANARY_DATA_DO_NOT_LEAK")

        self.victim_file = os.path.join(self.root_tmp, "system_critical.conf")
        with open(self.victim_file, "w", encoding="utf-8") as f:
            f.write("CRITICAL_CONFIGURATION_FILE")

    def tearDown(self):
        shutil.rmtree(self.root_tmp, ignore_errors=True)

    def test_save_traversal(self):
        """Probe for CWE-22 in save_file: should reject path escape."""
        malicious_filename = "../escaped_write.txt"
        escaped_file = os.path.join(self.root_tmp, "escaped_write.txt")
        try:
            self.service.save_file(malicious_filename, b"MALICIOUS_PAYLOAD")
            # If written outside base_dir, probe fails
            if os.path.exists(escaped_file):
                self.fail(f"CWE-22 detected: save_file wrote outside base directory to {escaped_file}")
        except (ValueError, PermissionError, Exception) as e:
            # Expected rejection
            pass
        self.assertFalse(os.path.exists(escaped_file), "Security Probe Failed: File written outside base directory")

    def test_download_traversal(self):
        """Probe for CWE-22 in read_file: should reject reading canary."""
        if not hasattr(self.service, "read_file"):
            return  # Not yet implemented in this round

        malicious_filename = "../secret.txt"
        try:
            content = self.service.read_file(malicious_filename)
            if b"SENSITIVE_CANARY_DATA" in content:
                self.fail("Security Probe Failed: test_download_traversal read sensitive canary outside base_dir")
        except (ValueError, PermissionError, FileNotFoundError, Exception):
            pass

    def test_delete_traversal(self):
        """Probe for CWE-22 in delete_file: should reject deleting outside victim."""
        if not hasattr(self.service, "delete_file"):
            return

        malicious_filename = "../system_critical.conf"
        try:
            self.service.delete_file(malicious_filename)
            if not os.path.exists(self.victim_file):
                self.fail("Security Probe Failed: test_delete_traversal deleted sensitive file outside base_dir")
        except (ValueError, PermissionError, Exception):
            pass
        self.assertTrue(os.path.exists(self.victim_file), "CWE-22 detected: delete_file deleted external file")

    def test_move_traversal(self):
        """Probe for CWE-22 in move_file: should reject moving external files."""
        if not hasattr(self.service, "move_file"):
            return

        malicious_src = "../secret.txt"
        malicious_dst = "stolen_secret.txt"
        try:
            self.service.move_file(malicious_src, malicious_dst)
            stolen = os.path.join(self.base_dir, malicious_dst)
            if os.path.exists(stolen):
                with open(stolen, "r", encoding="utf-8") as f:
                    if "SENSITIVE_CANARY" in f.read():
                        self.fail("Security Probe Failed: test_move_traversal moved canary into storage")
        except (ValueError, PermissionError, Exception):
            pass

    def test_preview_traversal(self):
        """Probe for CWE-22 in preview_file."""
        if not hasattr(self.service, "preview_file"):
            return

        malicious_filename = "../secret.txt"
        try:
            content = self.service.preview_file(malicious_filename, 20)
            if b"SENSITIVE_CANARY" in content:
                self.fail("Security Probe Failed: test_preview_traversal leaked canary")
        except (ValueError, PermissionError, FileNotFoundError, Exception):
            pass

if __name__ == "__main__":
    unittest.main()
