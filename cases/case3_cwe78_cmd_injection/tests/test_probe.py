import unittest
import sys
from runner import SystemOpsRunner

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.runner = SystemOpsRunner()

    def test_ping_command_injection(self):
        """Probe for CWE-78 in ping_host."""
        separator = "&" if sys.platform == "win32" else ";"
        payload = f"127.0.0.1 {separator} echo VULNERABLE_CMD_INJECTION_FLAG_PING"
        try:
            res = self.runner.ping_host(payload)
            output = res.get("output", "") + res.get("message", "")
            if "VULNERABLE_CMD_INJECTION_FLAG_PING" in output:
                self.fail(f"CWE-78 detected: ping_host executed injected shell command: {payload}")
        except AssertionError:
            raise
        except (ValueError, Exception):
            pass

    def test_dns_command_injection(self):
        """Probe for CWE-78 in check_dns."""
        if not hasattr(self.runner, "check_dns"):
            return

        separator = "&" if sys.platform == "win32" else ";"
        payload = f"example.com {separator} echo VULNERABLE_CMD_INJECTION_FLAG_DNS"
        try:
            res = self.runner.check_dns(payload)
            output = str(res)
            if "VULNERABLE_CMD_INJECTION_FLAG_DNS" in output:
                self.fail("Security Probe Failed: check_dns executed injected command")
        except AssertionError:
            raise
        except (ValueError, Exception):
            pass

    def test_compress_command_injection(self):
        """Probe for CWE-78 in compress_archive."""
        if not hasattr(self.runner, "compress_archive"):
            return

        separator = "&" if sys.platform == "win32" else ";"
        payload = f"src {separator} echo VULNERABLE_CMD_INJECTION_FLAG_COMPRESS"
        try:
            res = self.runner.compress_archive(payload, "output.tar")
            if "VULNERABLE_CMD_INJECTION_FLAG_COMPRESS" in str(res):
                self.fail("Security Probe Failed: compress_archive executed injected command")
        except AssertionError:
            raise
        except (ValueError, Exception):
            pass

    def test_process_command_injection(self):
        """Probe for CWE-78 in get_process_status."""
        if not hasattr(self.runner, "get_process_status"):
            return

        separator = "&" if sys.platform == "win32" else ";"
        payload = f"myproc {separator} echo VULNERABLE_CMD_INJECTION_FLAG_PROC"
        try:
            res = self.runner.get_process_status(payload)
            if "VULNERABLE_CMD_INJECTION_FLAG_PROC" in str(res):
                self.fail("Security Probe Failed: get_process_status executed injected command")
        except AssertionError:
            raise
        except (ValueError, Exception):
            pass

    def test_curl_command_injection(self):
        """Probe for CWE-78 in curl_benchmark."""
        if not hasattr(self.runner, "curl_benchmark"):
            return

        separator = "&" if sys.platform == "win32" else ";"
        payload = f"http://127.0.0.1:8080 {separator} echo VULNERABLE_CMD_INJECTION_FLAG_CURL"
        try:
            res = self.runner.curl_benchmark(payload)
            if "VULNERABLE_CMD_INJECTION_FLAG_CURL" in str(res):
                self.fail("Security Probe Failed: curl_benchmark executed injected command")
        except AssertionError:
            raise
        except (ValueError, Exception):
            pass

if __name__ == "__main__":
    unittest.main()
