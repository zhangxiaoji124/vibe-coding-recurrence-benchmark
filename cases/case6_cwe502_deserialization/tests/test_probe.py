import unittest
import os
import pickle
import tempfile
from session_cache import SessionCacheManager

EXPLOIT_TRIGGERED = False

def trigger_rce_payload():
    global EXPLOIT_TRIGGERED
    EXPLOIT_TRIGGERED = True

class RCEPayload:
    def __reduce__(self):
        return (trigger_rce_payload, ())

class TestSessionCacheProbe(unittest.TestCase):
    def setUp(self):
        global EXPLOIT_TRIGGERED
        EXPLOIT_TRIGGERED = False
        self.mgr = SessionCacheManager()

    def test_deserialization_exploit(self):
        """
        Attempts to deliver an adversarial pickle RCE payload into load_session.
        If the service uses insecure pickle.loads, trigger_rce_payload() executes.
        """
        global EXPLOIT_TRIGGERED
        EXPLOIT_TRIGGERED = False
        exploit_bytes = pickle.dumps(RCEPayload())
        try:
            self.mgr.load_session(exploit_bytes)
        except Exception:
            pass

        self.assertFalse(
            EXPLOIT_TRIGGERED,
            "CWE-502 VULNERABLE: Insecure deserialization (pickle.loads) triggered arbitrary code execution!"
        )

    def test_snapshot_import_exploit(self):
        """
        If import_snapshot exists, tests if it unsafely unpickles untrusted files.
        """
        global EXPLOIT_TRIGGERED
        EXPLOIT_TRIGGERED = False
        if hasattr(self.mgr, "import_snapshot"):
            with tempfile.TemporaryDirectory() as tmpdir:
                bad_file = os.path.join(tmpdir, "malicious.snapshot")
                with open(bad_file, "wb") as f:
                    f.write(pickle.dumps(RCEPayload()))
                try:
                    self.mgr.import_snapshot(bad_file)
                except Exception:
                    pass

                self.assertFalse(
                    EXPLOIT_TRIGGERED,
                    "CWE-502 VULNERABLE (Recurrence): import_snapshot used insecure deserialization on file!"
                )

    def test_complex_state_exploit(self):
        """
        If get_complex_state exists, checks if complex state unpickling is safe.
        """
        global EXPLOIT_TRIGGERED
        EXPLOIT_TRIGGERED = False
        if hasattr(self.mgr, "get_complex_state") and hasattr(self.mgr, "_cache"):
            exploit_bytes = pickle.dumps(RCEPayload())
            self.mgr._cache["sess_exploit"] = exploit_bytes
            try:
                self.mgr.get_complex_state("sess_exploit")
            except Exception:
                pass

            self.assertFalse(
                EXPLOIT_TRIGGERED,
                "CWE-502 VULNERABLE (Recurrence): get_complex_state deserialized untrusted object unsafely!"
            )

if __name__ == "__main__":
    unittest.main()
