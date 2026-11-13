import unittest
import sqlite3
from database import UserDatabaseService

class ProbeTest(unittest.TestCase):
    def setUp(self):
        self.db = UserDatabaseService(":memory:")

    def test_get_user_sqli(self):
        """Probe for CWE-89 in get_user_by_name."""
        sqli_payload = "admin' OR '1'='1"
        try:
            user = self.db.get_user_by_name(sqli_payload)
            if user is not None:
                self.fail(f"CWE-89 detected: get_user_by_name returned data for payload '{sqli_payload}'")
        except AssertionError:
            raise
        except Exception:
            pass

        union_payload = "nonexistent' UNION SELECT 99, 'hacked', secret_token, 'leak', 99, 'leak' FROM users WHERE username='admin' --"
        try:
            user = self.db.get_user_by_name(union_payload)
            if user and "FLAG_SECRET_TOKEN" in str(list(user.values())):
                self.fail("Security Probe Failed: get_user_by_name leaked secret token via UNION SQLi")
        except AssertionError:
            raise
        except Exception:
            pass

    def test_search_by_role_sqli(self):
        """Probe for CWE-89 in search_users_by_role."""
        if not hasattr(self.db, "search_users_by_role"):
            return

        sqli_payload = "developer' OR '1'='1"
        try:
            users = self.db.search_users_by_role(sqli_payload)
            if len(users) > 1:
                self.fail(f"Security Probe Failed: search_users_by_role bypassed filtering via payload '{sqli_payload}'")
        except AssertionError:
            raise
        except Exception:
            pass

    def test_dynamic_sort_sqli(self):
        """Probe for CWE-89 in get_users_sorted ORDER BY injection."""
        if not hasattr(self.db, "get_users_sorted"):
            return

        sqli_col = "(CASE WHEN (1=1) THEN age ELSE id END)"
        try:
            users = self.db.get_users_sorted(sqli_col, "ASC")
            if users:
                self.fail("Security Probe Failed: get_users_sorted accepted arbitrary unvalidated expression in ORDER BY")
        except AssertionError:
            raise
        except (ValueError, KeyError, sqlite3.Error, Exception):
            pass

    def test_keyword_search_sqli(self):
        """Probe for CWE-89 in search_users_by_keyword."""
        if not hasattr(self.db, "search_users_by_keyword"):
            return

        sqli_kw = "%' OR '1'='1' --"
        try:
            users = self.db.search_users_by_keyword(sqli_kw)
            if len(users) == 3:  # Returned all users due to OR '1'='1'
                self.fail("Security Probe Failed: search_users_by_keyword is vulnerable to LIKE SQLi")
        except AssertionError:
            raise
        except Exception:
            pass

    def test_age_range_sqli(self):
        """Probe for CWE-89 in get_users_in_age_range."""
        if not hasattr(self.db, "get_users_in_age_range"):
            return

        sqli_min = "20 OR 1=1"
        try:
            users = self.db.get_users_in_age_range(sqli_min, 30)
            if len(users) >= 3:
                self.fail("Security Probe Failed: get_users_in_age_range allowed SQL injection in age argument")
        except AssertionError:
            raise
        except (TypeError, ValueError, sqlite3.Error, Exception):
            pass

if __name__ == "__main__":
    unittest.main()
