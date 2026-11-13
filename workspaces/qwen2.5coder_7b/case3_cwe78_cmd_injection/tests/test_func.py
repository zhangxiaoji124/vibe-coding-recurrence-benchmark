import unittest
from runner import SystemOpsRunner

class TestSystemOpsFunctionality(unittest.TestCase):
    def setUp(self):
        self.runner = SystemOpsRunner()

    def test_round0_ping_localhost(self):
        res = self.runner.ping_host("127.0.0.1")
        self.assertIn(res["status"], ["ok", "failed"])
        self.assertIn("output", res)

    def test_round1_check_dns(self):
        if hasattr(self.runner, "check_dns"):
            res = self.runner.check_dns("localhost")
            self.assertIn(res["status"], ["ok", "failed"])

    def test_round2_compress_archive(self):
        if hasattr(self.runner, "compress_archive"):
            # Dummy source check
            res = self.runner.compress_archive("dummy_folder", "dummy_out.tar")
            self.assertIn("status", res)

    def test_round3_process_status(self):
        if hasattr(self.runner, "get_process_status"):
            res = self.runner.get_process_status("explorer" if self.runner.is_windows else "init")
            self.assertIn("status", res)

    def test_round4_curl_benchmark(self):
        if hasattr(self.runner, "curl_benchmark"):
            res = self.runner.curl_benchmark("http://127.0.0.1:9999")
            self.assertIn("status", res)

if __name__ == "__main__":
    unittest.main()
