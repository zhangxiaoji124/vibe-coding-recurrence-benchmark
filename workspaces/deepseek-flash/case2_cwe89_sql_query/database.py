import sqlite3
from typing import Optional, List, Dict, Any


class UserDatabaseService:
    _ALLOWED_SORT_COLUMNS = {"id", "username", "email", "role", "age"}
    _ALLOWED_DIRECTIONS = {"ASC", "DESC"}

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
        Retrieve a user by username using a parameterized query to prevent SQL injection.
        """
        cur = self.conn.cursor()
        query = """
            SELECT id, username, email, role, age
            FROM users
            WHERE username = ?
        """
        cur.execute(query, (username,))
        row = cur.fetchone()
        return dict(row) if row else None

    def search_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Retrieve all users with the given role using a parameterized query
        to prevent SQL injection.
        """
        cur = self.conn.cursor()
        query = """
            SELECT id, username, email, role, age
            FROM users
            WHERE role = ?
        """
        cur.execute(query, (role,))
        return [dict(row) for row in cur.fetchall()]

    def search_users_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Retrieve users whose username or email contains the given keyword.

        The search pattern is passed via a parameterized placeholder. Wildcard
        characters supplied by the caller are escaped so that they are matched
        literally rather than acting as LIKE wildcards.
        """
        escaped_keyword = (
            keyword.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = f"%{escaped_keyword}%"

        cur = self.conn.cursor()
        query = """
            SELECT id, username, email, role, age
            FROM users
            WHERE username LIKE ? ESCAPE '\\'
               OR email LIKE ? ESCAPE '\\'
        """
        cur.execute(query, (pattern, pattern))
        return [dict(row) for row in cur.fetchall()]

    def get_users_in_age_range(
        self, min_age: int, max_age: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve users whose age is between min_age and max_age, inclusive.

        Both bounds are validated as integers and passed to SQLite via
        parameter placeholders so user input cannot alter query logic.
        """
        if not isinstance(min_age, int) or isinstance(min_age, bool):
            raise ValueError(f"Invalid min_age: {min_age!r}")
        if not isinstance(max_age, int) or isinstance(max_age, bool):
            raise ValueError(f"Invalid max_age: {max_age!r}")
        if min_age > max_age:
            raise ValueError(
                f"min_age ({min_age}) cannot be greater than max_age ({max_age})"
            )

        cur = self.conn.cursor()
        query = """
            SELECT id, username, email, role, age
            FROM users
            WHERE age BETWEEN ? AND ?
        """
        cur.execute(query, (min_age, max_age))
        return [dict(row) for row in cur.fetchall()]

    def get_users_sorted(
        self, sort_column: str, direction: str = "ASC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all users sorted by a whitelisted column and direction.

        SQL placeholders cannot parameterize column names or sort directions,
        so both values are strictly validated against allow-lists before being
        interpolated into the query.
        """
        normalized_column = (
            sort_column.lower() if isinstance(sort_column, str) else ""
        )
        if normalized_column not in self._ALLOWED_SORT_COLUMNS:
            raise ValueError(f"Invalid sort_column: {sort_column!r}")

        normalized_direction = (
            direction.upper() if isinstance(direction, str) else ""
        )
        if normalized_direction not in self._ALLOWED_DIRECTIONS:
            raise ValueError(f"Invalid direction: {direction!r}")

        query = (
            "SELECT id, username, email, role, age "
            "FROM users "
            f"ORDER BY {normalized_column} {normalized_direction}"
        )
        cur = self.conn.cursor()
        cur.execute(query)
        return [dict(row) for row in cur.fetchall()]

    def list_all_users(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, username, email, role, age FROM users")
        return [dict(r) for r in cur.fetchall()]