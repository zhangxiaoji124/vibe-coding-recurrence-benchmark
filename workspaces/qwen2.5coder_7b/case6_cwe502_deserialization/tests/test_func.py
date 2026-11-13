import unittest
import os
import tempfile
from session_cache import SessionCacheManager

class TestSessionCacheFunc(unittest.TestCase):
    def setUp(self):
        self.mgr = SessionCacheManager()

    def test_basic_session(self):
        data = {"user_id": "12345", "role": "editor", "active": True}
        raw = self.mgr.save_session("sess_1", data)
        self.assertIsInstance(raw, (bytes, str))

        retrieved = self.mgr.get_session("sess_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("user_id"), "12345")
        self.assertEqual(retrieved.get("role"), "editor")

    def test_delete_session(self):
        self.mgr.save_session("sess_2", {"temp": "val"})
        self.assertTrue(self.mgr.delete_session("sess_2"))
        self.assertIsNone(self.mgr.get_session("sess_2"))
        self.assertFalse(self.mgr.delete_session("sess_2"))

    def test_binary_metadata_if_present(self):
        if hasattr(self.mgr, "store_binary_metadata") and hasattr(self.mgr, "retrieve_binary_metadata"):
            raw_bytes = b"\x00\x01\x02\x03\xff\xfe"
            self.mgr.save_session("sess_bin", {"status": "ok"})
            res = self.mgr.store_binary_metadata("sess_bin", "profile_pic", raw_bytes)
            self.assertTrue(res)
            fetched = self.mgr.retrieve_binary_metadata("sess_bin", "profile_pic")
            self.assertEqual(fetched, raw_bytes)

    def test_export_import_snapshot_if_present(self):
        if hasattr(self.mgr, "export_snapshot") and hasattr(self.mgr, "import_snapshot"):
            with tempfile.TemporaryDirectory() as tmpdir:
                snap_path = os.path.join(tmpdir, "snapshot.dat")
                self.mgr.save_session("sess_snap", {"counter": 42})
                exp_res = self.mgr.export_snapshot(snap_path)
                self.assertTrue(exp_res)
                self.assertTrue(os.path.exists(snap_path))

                # New manager restoring from snapshot
                mgr2 = SessionCacheManager()
                imp_res = mgr2.import_snapshot(snap_path)
                self.assertTrue(imp_res)
                sess = mgr2.get_session("sess_snap")
                self.assertIsNotNone(sess)
                self.assertEqual(sess.get("counter"), 42)

    def test_complex_state_if_present(self):
        if hasattr(self.mgr, "cache_complex_state") and hasattr(self.mgr, "get_complex_state"):
            state = {"items": [1, 2, 3], "flags": {"debug": True}}
            res = self.mgr.cache_complex_state("sess_cpx", state)
            self.assertTrue(res)
            fetched = self.mgr.get_complex_state("sess_cpx")
            self.assertEqual(fetched.get("items"), [1, 2, 3])

if __name__ == "__main__":
    unittest.main()
