import sqlite3
from contextlib import contextmanager

DB_FILE = "users.db"


@contextmanager
def get_connection():
    """Open the database, save changes if all goes well, always close it."""
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create the users table if it does not exist yet"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash BLOB NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_user(username, password_hash):
    """Insert a new user. Returns False if the username is already taken."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username):
    """Return (username, password_hash, failed_attempts, locked) or None."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT username, password_hash, failed_attempts, locked "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def record_failed_attempt(username, max_attempts=5):
    """Add one failed attempt and lock the account once the limit is reached."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET failed_attempts = failed_attempts + 1 "
            "WHERE username = ?",
            (username,),
        )
        conn.execute(
            "UPDATE users SET locked = 1"
            "WHERE username = ? AND failed_attempts >= ?",
            (username, max_attempts),
        )


def reset_failed_attempts(username):
    """Clear the failed-attempt counter after a successful login."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET failed_attempts = 0 WHERE username = ?",
            (username,),
        )