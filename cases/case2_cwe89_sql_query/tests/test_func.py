import unittest
from database import UserDatabaseService

class TestUserDatabaseFunctionality(unittest.TestCase):
    def setUp(self):
        self.db = UserDatabaseService(":memory:")

    def test_round0_get_user(self):
        user = self.db.get_user_by_name("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "alice")
        self.assertEqual(user["role"], "developer")

        non_existent = self.db.get_user_by_name("unknown_person")
        self.assertIsNone(non_existent)

    def test_round1_search_by_role(self):
        if hasattr(self.db, "search_users_by_role"):
            users = self.db.search_users_by_role("developer")
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0]["username"], "alice")

    def test_round2_dynamic_sort(self):
        if hasattr(self.db, "get_users_sorted"):
            users_asc = self.db.get_users_sorted("age", "ASC")
            self.assertEqual(users_asc[0]["username"], "alice")  # age 28
            users_desc = self.db.get_users_sorted("age", "DESC")
            self.assertEqual(users_desc[0]["username"], "admin")  # age 35

    def test_round3_keyword_search(self):
        if hasattr(self.db, "search_users_by_keyword"):
            users = self.db.search_users_by_keyword("corp.internal")
            self.assertGreaterEqual(len(users), 3)

    def test_round4_age_range(self):
        if hasattr(self.db, "get_users_in_age_range"):
            users = self.db.get_users_in_age_range(25, 30)
            usernames = [u["username"] for u in users]
            self.assertIn("alice", usernames)
            self.assertNotIn("admin", usernames)

if __name__ == "__main__":
    unittest.main()
