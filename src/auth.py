"""Authentication, role-based access control, and password hashing for Vivédex.

This module uses PBKDF2-HMAC-SHA256 with secure per-user salts.
It enforces role-based access control with server-side checks.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from typing import Any

from src.database import Database, utc_now_iso

LOCAL_AUTH_WARNING = (
    "LOCAL PROTOTYPE — AUTHENTICATION IS NOT PRODUCTION-HARDENED."
)
HASH_ITERATIONS = 100_000


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents an authenticated platform user."""

    id: int
    username: str
    role: str
    display_name: str
    vivedex_id: str
    is_active: bool

    @property
    def is_admin(self) -> bool:
        """Return True if user has the administrator role."""
        return self.role == "admin"


class AuthenticationError(Exception):
    """Raised when authentication credentials fail validation."""


class AuthorizationError(Exception):
    """Raised when an operation is prohibited by role permissions."""


def generate_salt() -> str:
    """Generate a cryptographically secure 16-byte random hex salt."""
    return secrets.token_hex(16)


def hash_password(password: str, salt_hex: str) -> str:
    """Hash a plaintext password with PBKDF2-HMAC-SHA256."""
    salt_bytes = bytes.fromhex(salt_hex)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        HASH_ITERATIONS,
    )
    return derived.hex()


def verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    """Verify a password against stored salt and expected hash using constant-time check."""
    computed_hash = hash_password(password, salt_hex)
    return hmac.compare_digest(computed_hash, expected_hash)


def generate_vivedex_id() -> str:
    """Generate a unique random Vivédex ID."""
    token = secrets.token_hex(3).upper()
    return f"VDX-{token}"


class AuthService:
    """Handles user registration, authentication, and role checks."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def register_user(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> AuthenticatedUser:
        """Register a new user.

        The first registered user is automatically granted the 'admin' role.
        Subsequent users always receive the 'user' role.
        """
        clean_username = username.strip()
        if not clean_username:
            raise AuthenticationError("Username cannot be empty.")

        if not re.match(r"^[a-zA-Z0-9_-]{3,32}$", clean_username):
            raise AuthenticationError(
                "Username must be 3-32 characters long and contain only letters, numbers, underscores, or hyphens."
            )

        if len(password) < 8:
            raise AuthenticationError("Password must be at least 8 characters long.")

        clean_display_name = (display_name or clean_username).strip()
        if not clean_display_name:
            clean_display_name = clean_username

        salt = generate_salt()
        pwd_hash = hash_password(password, salt)
        created_at = utc_now_iso()

        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Check if this is the first user (bootstrap administrator)
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            assigned_role = "admin" if user_count == 0 else "user"

            # Check unique username
            cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE;", (clean_username,))
            if cursor.fetchone() is not None:
                raise AuthenticationError(f"Username '{clean_username}' is already taken.")

            # Insert user
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?);
                """,
                (clean_username, pwd_hash, salt, assigned_role, created_at),
            )
            user_id = cursor.lastrowid

            # Insert user profile
            vivedex_id = generate_vivedex_id()
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, vivedex_id, display_name, bio, external_orcid_url, created_at, updated_at)
                VALUES (?, ?, ?, '', '', ?, ?);
                """,
                (user_id, vivedex_id, clean_display_name, created_at, created_at),
            )

            # Record audit log
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'USER_REGISTERED', 'USER', ?, ?, ?);
                """,
                (user_id, str(user_id), f"Role assigned: {assigned_role}", created_at),
            )

            return AuthenticatedUser(
                id=user_id,
                username=clean_username,
                role=assigned_role,
                display_name=clean_display_name,
                vivedex_id=vivedex_id,
                is_active=True,
            )

    def authenticate_user(self, username: str, password: str) -> AuthenticatedUser:
        """Authenticate user with username and password."""
        clean_username = username.strip()
        if not clean_username or not password:
            raise AuthenticationError("Username and password are required.")

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.password_hash, u.salt, u.role, u.is_active,
                       p.display_name, p.vivedex_id
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.username = ? COLLATE NOCASE;
                """,
                (clean_username,),
            )
            row = cursor.fetchone()
            if row is None:
                raise AuthenticationError("Invalid username or password.")

            user_id, uname, pwd_hash, salt, role, is_active, display_name, vivedex_id = row

            if not is_active:
                raise AuthenticationError("User account is deactivated.")

            if not verify_password(password, salt, pwd_hash):
                raise AuthenticationError("Invalid username or password.")

            # Record login audit
            now = utc_now_iso()
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'USER_LOGIN', 'USER', ?, 'Successful authentication', ?);
                """,
                (user_id, str(user_id), now),
            )

            return AuthenticatedUser(
                id=user_id,
                username=uname,
                role=role,
                display_name=display_name or uname,
                vivedex_id=vivedex_id or f"VDX-{user_id}",
                is_active=bool(is_active),
            )

    def get_user_by_id(self, user_id: int) -> AuthenticatedUser | None:
        """Fetch user by primary ID."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.role, u.is_active, p.display_name, p.vivedex_id
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = ?;
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return AuthenticatedUser(
                id=row["id"],
                username=row["username"],
                role=row["role"],
                display_name=row["display_name"] or row["username"],
                vivedex_id=row["vivedex_id"] or f"VDX-{row['id']}",
                is_active=bool(row["is_active"]),
            )

    @staticmethod
    def require_role(user: AuthenticatedUser | None, required_role: str) -> None:
        """Enforce role permissions on an operation. Raises AuthorizationError if unauthorized."""
        if user is None:
            raise AuthorizationError("Authentication required.")
        if user.role != required_role:
            raise AuthorizationError(
                f"Operation requires '{required_role}' role. Current role is '{user.role}'."
            )

    @staticmethod
    def require_admin(user: AuthenticatedUser | None) -> None:
        """Enforce administrator permissions."""
        AuthService.require_role(user, "admin")

