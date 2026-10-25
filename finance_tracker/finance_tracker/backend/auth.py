"""Authentication: registration and login with salted PBKDF2 password hashes.
Passwords are never stored in plain text."""
import hashlib
import hmac
import os
import re
import sqlite3

from .database import Database

ITERATIONS = 200_000
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
MIN_PASSWORD = 6


class AuthError(Exception):
    """Raised for login / registration problems; the message is safe to show."""


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def register(self, username, password, confirm):
        username = (username or "").strip()
        if not USERNAME_RE.match(username):
            raise AuthError("Username must be 3-20 characters: letters, numbers or _ only.")
        if len(password or "") < MIN_PASSWORD:
            raise AuthError(f"Password must be at least {MIN_PASSWORD} characters.")
        if password != confirm:
            raise AuthError("Passwords do not match.")
        try:
            user_id = self.db.create_user(username, hash_password(password))
        except sqlite3.IntegrityError:
            raise AuthError("That username is already taken.")
        return {"id": user_id, "username": username}

    def login(self, username, password):
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Enter your username and password.")
        user = self.db.get_user(username)
        if user is None or not verify_password(password, user["password_hash"]):
            raise AuthError("Incorrect username or password.")
        return {"id": user["id"], "username": user["username"]}
