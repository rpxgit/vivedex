"""Authentication, role-based access control, and password hashing for Vivédex.

This module uses PBKDF2-HMAC-SHA256 with secure per-user salts.
It enforces role-based access control with server-side checks.
Includes login rate limiting, constant-time dummy verification, and operator-gated admin provisioning.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

from src.database import Database, utc_now_iso

LOCAL_AUTH_WARNING = (
    "LOCAL PROTOTYPE — AUTHENTICATION IS NOT PRODUCTION-HARDENED."
)
HASH_ITERATIONS = 100_000
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN_SECONDS = 60  # Initial 1-minute cooldown for 5 failed attempts
DUMMY_SALT = "00" * 16
DUMMY_HASH = hashlib.pbkdf2_hmac(
    "sha256",
    b"dummy_constant_hash_string_timing_mitigation",
    bytes.fromhex(DUMMY_SALT),
    HASH_ITERATIONS,
).hex()

ORCID_PATH_REGEX = re.compile(r"^/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


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


def validate_orcid_url(url: str | None) -> str:
    """Validate external ORCID URL.

    Accepts only HTTPS URLs on orcid.org or www.orcid.org with valid 16-digit structure.
    Rejects javascript:, data:, http:, embedded credentials, queries, and fragments.
    Returns normalized canonical URL (https://orcid.org/XXXX-XXXX-XXXX-XXXX) or empty string.
    Raises ValueError on invalid input.
    """
    if not url or not str(url).strip():
        return ""
    clean = str(url).strip()
    parsed = urllib.parse.urlsplit(clean)
    if parsed.scheme.lower() != "https":
        raise ValueError("ORCID URL must use secure HTTPS protocol.")
    if parsed.username or parsed.password:
        raise ValueError("Embedded credentials in ORCID URL are prohibited.")
    hostname = (parsed.netloc or "").split(":")[0].lower()
    if hostname not in ("orcid.org", "www.orcid.org"):
        raise ValueError("ORCID URL must be hosted on orcid.org or www.orcid.org.")
    path = parsed.path.rstrip("/")
    if not ORCID_PATH_REGEX.match(path):
        raise ValueError(
            "Invalid ORCID profile format. Expected: https://orcid.org/0000-0000-0000-0000"
        )
    if parsed.query or parsed.fragment:
        raise ValueError(
            "Query parameters and fragment identifiers are not permitted in ORCID profile URLs."
        )
    return f"https://orcid.org{path}"


class AuthService:
    """Handles user registration, authentication, rate limiting, and role checks."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._failed_logins: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _check_login_rate_limit(self, username: str) -> None:
        """Enforce rate limiting on failed login attempts.

        Progressive cooldown:
        - 5 failed attempts locks for 60 seconds.
        - Additional failed attempts increment cooldown up to 900 seconds (15 minutes).
        """
        now = time.monotonic()
        key = username.lower().strip()
        with self._lock:
            attempts = self._failed_logins.get(key, [])
            # Prune attempts older than 15 minutes (900 seconds)
            attempts = [t for t in attempts if now - t < 900]
            self._failed_logins[key] = attempts
            if len(attempts) >= MAX_FAILED_LOGIN_ATTEMPTS:
                latest_attempt = max(attempts)
                cooldown = min(
                    900,
                    LOGIN_COOLDOWN_SECONDS
                    * (1 + len(attempts) - MAX_FAILED_LOGIN_ATTEMPTS),
                )
                remaining = cooldown - (now - latest_attempt)
                if remaining > 0:
                    raise AuthenticationError(
                        f"Too many failed login attempts. Please wait {int(remaining) + 1} seconds before trying again."
                    )

    def _record_failed_login(self, username: str) -> None:
        """Record a failed login attempt for rate limiting."""
        now = time.monotonic()
        key = username.lower().strip()
        with self._lock:
            if key not in self._failed_logins:
                self._failed_logins[key] = []
            self._failed_logins[key].append(now)

    def _clear_failed_logins(self, username: str) -> None:
        """Clear failed login records after successful authentication."""
        key = username.lower().strip()
        with self._lock:
            self._failed_logins.pop(key, None)

    def register_user(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> AuthenticatedUser:
        """Register a new standard user account.

        All ordinary registrations unconditionally receive the 'user' role.
        Automatic administrator promotion is prohibited (SEC-02).
        Administrator accounts can only be provisioned via the explicit CLI command.
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
        assigned_role = "user"  # SEC-02: Public registrations are ALWAYS standard users

        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Check unique username
            cursor.execute(
                "SELECT id FROM users WHERE username = ? COLLATE NOCASE;",
                (clean_username,),
            )
            if cursor.fetchone() is not None:
                raise AuthenticationError(
                    f"Username '{clean_username}' is already taken."
                )

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

    def provision_admin_user(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
        allow_reprovision: bool = False,
    ) -> AuthenticatedUser:
        """Explicitly provision an administrator account.

        Operator-gated CLI use only (SEC-02).
        Requires explicit confirmation if an administrator already exists unless allow_reprovision is True.
        Executes within an atomic transaction and logs an administrative audit event.
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

            # Check if active admin exists
            cursor.execute("SELECT id, username FROM users WHERE role = 'admin' AND is_active = 1;")
            existing_admin = cursor.fetchone()
            if existing_admin and not allow_reprovision:
                raise PermissionError(
                    f"An active administrator account already exists ('{existing_admin['username']}'). "
                    f"Use --force to provision an additional administrator."
                )

            # Check unique username
            cursor.execute(
                "SELECT id FROM users WHERE username = ? COLLATE NOCASE;",
                (clean_username,),
            )
            if cursor.fetchone() is not None:
                raise AuthenticationError(
                    f"Username '{clean_username}' is already taken."
                )

            # Insert administrator
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, is_active, created_at)
                VALUES (?, ?, ?, 'admin', 1, ?);
                """,
                (clean_username, pwd_hash, salt, created_at),
            )
            user_id = cursor.lastrowid

            # Insert user profile
            vivedex_id = generate_vivedex_id()
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, vivedex_id, display_name, bio, external_orcid_url, created_at, updated_at)
                VALUES (?, ?, ?, 'Platform Administrator', '', ?, ?);
                """,
                (user_id, vivedex_id, clean_display_name, created_at, created_at),
            )

            # Record audit log
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'ADMIN_PROVISIONED_VIA_CLI', 'USER', ?, 'Administrator provisioned via operator CLI', ?);
                """,
                (user_id, str(user_id), created_at),
            )

            return AuthenticatedUser(
                id=user_id,
                username=clean_username,
                role="admin",
                display_name=clean_display_name,
                vivedex_id=vivedex_id,
                is_active=True,
            )

    def authenticate_user(self, username: str, password: str) -> AuthenticatedUser:
        """Authenticate user with username and password.

        Defends against timing side-channels via constant-time dummy verification (SEC-04).
        Defends against brute-force attacks via progressive rate limiting (SEC-03).
        """
        clean_username = username.strip()
        if not clean_username or not password:
            raise AuthenticationError("Username and password are required.")

        # 1. Check rate limit
        self._check_login_rate_limit(clean_username)

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

        # 2. Timing attack mitigation (SEC-04):
        # If user does not exist, compute dummy password verification with equal work factor
        if row is None:
            verify_password(password, DUMMY_SALT, DUMMY_HASH)
            self._record_failed_login(clean_username)
            raise AuthenticationError("Invalid username or password.")

        user_id, uname, pwd_hash, salt, role, is_active, display_name, vivedex_id = row

        if not is_active:
            self._record_failed_login(clean_username)
            raise AuthenticationError("User account is deactivated.")

        if not verify_password(password, salt, pwd_hash):
            self._record_failed_login(clean_username)
            raise AuthenticationError("Invalid username or password.")

        # 3. Successful authentication: clear failed attempt counters
        self._clear_failed_logins(clean_username)

        # Record login audit
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
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
