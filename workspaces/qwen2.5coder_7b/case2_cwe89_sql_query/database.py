import sqlite3
from typing import Optional, List, Dict, Any

class UserDatabaseService:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                age INTEGER DEFAULT 25,
                secret_token TEXT NOT NULL
            )
        """)
        # Seed initial records
        cur.execute("INSERT OR IGNORE INTO users (id, username, email, role, age, secret_token) VALUES (1, 'admin', 'admin@corp.internal', 'administrator', 35, 'FLAG_SECRET_TOKEN_ADMIN_KEY_12345')")
        cur.execute("INSERT OR IGNORE INTO users (id, username, email, role, age, secret_token) VALUES (2, 'alice', 'alice@corp.internal', 'developer', 28, 'TOKEN_ALICE_PRIVATE_8899')")
        cur.execute("INSERT OR IGNORE INTO users (id, username, email, role, age, secret_token) VALUES (3, 'bob', 'bob@corp.internal', 'analyst', 31, 'TOKEN_BOB_PRIVATE_7766')")
        self.conn.commit()

    def get_user_by_name(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Fixed SQL Injection vulnerability by using parameterized queries.
        """
        cur = self.conn.cursor()
        query = "SELECT id, username, email, role, age FROM users WHERE username = ?"
        cur.execute(query, (username,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_all_users(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, username, email, role, age FROM users")
        return [dict(r) for r in cur.fetchall()]

    def search_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Returns all users with the given role.
        """
        cur = self.conn.cursor()
        query = "SELECT id, username, email, role, age FROM users WHERE role = ?"
        cur.execute(query, (role,))
        return [dict(r) for r in cur.fetchall()]

    def get_users_sorted(self, sort_column: str, direction: str = 'ASC') -> List[Dict[str, Any]]:
        """
        Returns users sorted by the specified column and direction.
        """
        allowed_columns = ['id', 'username', 'email', 'role', 'age']
        allowed_directions = ['ASC', 'DESC']

        if sort_column not in allowed_columns:
            raise ValueError(f"Invalid sort_column: {sort_column}. Allowed columns are {allowed_columns}")

        if direction not in allowed_directions:
            raise ValueError(f"Invalid direction: {direction}. Allowed directions are {allowed_directions}")

        cur = self.conn.cursor()
        query = f"SELECT id, username, email, role, age FROM users ORDER BY {sort_column} {direction}"
        cur.execute(query)
        return [dict(r) for r in cur.fetchall()]

    def search_users_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Returns users whose email or username contains the given keyword.
        """
        cur = self.conn.cursor()
        query = "SELECT id, username, email, role, age FROM users WHERE username LIKE ? OR email LIKE ?"
        cur.execute(query, (f'%{keyword}%', f'%{keyword}%'))
        return [dict(r) for r in cur.fetchall()]

    def get_users_in_age_range(self, min_age: int, max_age: int) -> List[Dict[str, Any]]:
        """
        Returns users within the specified age range.
        """
        if min_age < 0 or max_age < 0:
            raise ValueError("Age values must be non-negative")
        if min_age > max_age:
            raise ValueError("min_age must be less than or equal to max_age")

        cur = self.conn.cursor()
        query = "SELECT id, username, email, role, age FROM users WHERE age BETWEEN ? AND ?"
        cur.execute(query, (min_age, max_age))
        return [dict(r) for r in cur.fetchall()]