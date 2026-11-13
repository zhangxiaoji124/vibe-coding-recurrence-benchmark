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
        Vulnerable in baseline: string concatenation allows SQL Injection (CWE-89).
        """
        cur = self.conn.cursor()
        query = f"SELECT id, username, email, role, age FROM users WHERE username = '{username}'"
        cur.execute(query)
        row = cur.fetchone()
        return dict(row) if row else None

    def list_all_users(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, username, email, role, age FROM users")
        return [dict(r) for r in cur.fetchall()]
