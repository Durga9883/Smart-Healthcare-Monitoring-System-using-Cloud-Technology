"""
models/user.py – User account CRUD
Handles admin / doctor / patient login accounts.
Passwords are stored as bcrypt hashes – never plain-text.
"""

import bcrypt
from models import get_db


# ── Helpers ────────────────────────────────────────────────────────────────────

def hash_password(plain_text: str) -> str:
    """Return a bcrypt hash string for the given plain-text password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_text.encode(), salt).decode()


def check_password(plain_text: str, hashed: str) -> bool:
    """Return True if plain_text matches the bcrypt hash."""
    return bcrypt.checkpw(plain_text.encode(), hashed.encode())


# ── Queries ────────────────────────────────────────────────────────────────────

def find_by_username(username: str) -> dict | None:
    """Fetch a user row by username; returns None if not found."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = %s LIMIT 1",
                (username,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def find_by_id(user_id: int) -> dict | None:
    """Fetch a user row by primary key."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, role, email, full_name, created_at "
                "FROM users WHERE id = %s LIMIT 1",
                (user_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def create_user(username: str, password: str, role: str,
                email: str = "", full_name: str = "") -> int:
    """
    Insert a new user and return the new user id.
    Raises an exception if username already exists.
    """
    pw_hash = hash_password(password)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (username, password_hash, role, email, full_name)
                   VALUES (%s, %s, %s, %s, %s)""",
                (username, pw_hash, role, email, full_name)
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_doctors() -> list:
    """Return all users whose role is 'doctor'."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email FROM users WHERE role = 'doctor'"
            )
            return cur.fetchall()
    finally:
        conn.close()
