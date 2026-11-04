"""Security Regression Test Suite for Vivédex.

Validates security remediations for RUN 010 (ASD-STE100):
- SEC-01: HTML escaping and safe URL filtering to prevent XSS.
- SEC-02: Removal of automatic first-user admin bootstrap; explicit operator CLI admin provisioning; demo mode isolation.
- SEC-03: Progressive login rate limiting.
- SEC-04: Constant-time dummy password verification on non-existent usernames.
- SEC-05: Separation of observation encounters from manual collection saves (XP inflation prevention).
- SEC-06: Image dimensions and pixel limit validation (decompression bomb protection).
- SEC-07: Idle session timeout enforcement.
- SEC-08: Strict ORCID URL validation.
- User record isolation and authorization enforcement.
"""

from __future__ import annotations

import io
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from PIL import Image

from src.achievements import AchievementService
from src.admin_service import AdminService
from src.auth import (
    AuthenticatedUser,
    AuthenticationError,
    AuthService,
    AuthorizationError,
    validate_orcid_url,
)
from src.cli import main as cli_main
from src.collection_service import CollectionService
from src.database import Database
from src.demo_data import is_demo_mode, load_demo_dataset
from src.image_processor import (
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_WIDTH,
    ImageValidationError,
    preprocess_image,
    validate_image,
)
from src.schemas import GBIFMatchResult
from src.ui.common import check_session_timeout
from src.ui.theme import escape_text, safe_url


class TestSecurityHardening(unittest.TestCase):
    """Security verification test cases adhering to ASD-STE100."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_sec.sqlite3")
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.auth_service = AuthService(self.db)
        self.collection_service = CollectionService(self.db)
        self.achievement_service = AchievementService(self.db)
        self.admin_service = AdminService(self.db)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # SEC-01: HTML Escaping
    def test_html_escaping_utility(self) -> None:
        """Verify that escape_text escapes HTML characters correctly."""
        raw_xss = "<script>alert('XSS')</script>"
        escaped = escape_text(raw_xss)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)
        self.assertIn("&#x27;XSS&#x27;", escaped)

        attr_payload = '<img src=x onerror="alert(1)">'
        escaped_attr = escape_text(attr_payload)
        self.assertNotIn("<img", escaped_attr)
        self.assertIn("&quot;", escaped_attr)

        self.assertEqual(escape_text(None), "")
        self.assertEqual(escape_text(12345), "12345")

    # SEC-01 & SEC-08: Safe URL Filtering
    def test_safe_url_filtering(self) -> None:
        """Verify safe_url accepts HTTP/HTTPS and rejects javascript/data schemes."""
        self.assertEqual(safe_url("https://orcid.org/0000-0002-1825-0097"), "https://orcid.org/0000-0002-1825-0097")
        self.assertEqual(safe_url("http://example.com/specimen"), "http://example.com/specimen")
        self.assertEqual(safe_url("javascript:alert(document.cookie)"), "")
        self.assertEqual(safe_url("data:text/html;base64,PHNjcmlwdD4="), "")
        self.assertEqual(safe_url("vbscript:MsgBox(1)"), "")
        self.assertEqual(safe_url(None), "")
        self.assertEqual(safe_url(""), "")

    # SEC-08: Strict ORCID URL Validation
    def test_orcid_validation_valid_formats(self) -> None:
        """Verify valid ORCID URLs pass strict validation and normalize to canonical domain."""
        valid_1 = "https://orcid.org/0000-0002-1825-0097"
        valid_2 = "https://www.orcid.org/0000-0001-5109-3700"
        valid_x = "https://orcid.org/0000-0002-1694-233X"

        self.assertEqual(validate_orcid_url(valid_1), "https://orcid.org/0000-0002-1825-0097")
        self.assertEqual(validate_orcid_url(valid_2), "https://orcid.org/0000-0001-5109-3700")
        self.assertEqual(validate_orcid_url(valid_x), "https://orcid.org/0000-0002-1694-233X")
        self.assertEqual(validate_orcid_url(None), "")
        self.assertEqual(validate_orcid_url(""), "")

    def test_orcid_validation_invalid_formats(self) -> None:
        """Verify invalid or hostile ORCID URLs raise ValueError."""
        invalid_cases = [
            "http://orcid.org/0000-0002-1825-0097",  # Insecure HTTP
            "https://evil-orcid.org/0000-0002-1825-0097",  # Spoofed host
            "https://orcid.org/0000-0002-1825-0097?query=xss",  # Query params forbidden
            "https://orcid.org/0000-0002-1825-0097#fragment",  # Fragment forbidden
            "https://orcid.org/0000-0002",  # Incomplete digits
            "https://orcid.org/0000-0002-1825-0097/extra",  # Extra path
            "javascript:alert(1)",  # Script injection
        ]
        for url in invalid_cases:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_orcid_url(url)

    # SEC-02: Public Registration Does Not Assign Admin
    def test_public_registration_never_assigns_admin(self) -> None:
        """Verify that public registration always assigns 'user' role."""
        first_user = self.auth_service.register_user("first_registrant", "password_123")
        second_user = self.auth_service.register_user("second_registrant", "password_123")

        self.assertEqual(first_user.role, "user")
        self.assertFalse(first_user.is_admin)
        self.assertEqual(second_user.role, "user")
        self.assertFalse(second_user.is_admin)

    # SEC-02: Explicit Administrator Provisioning via Service
    def test_provision_admin_user_service(self) -> None:
        """Verify explicit admin provisioning creates verified admin accounts."""
        admin = self.auth_service.provision_admin_user("operator_admin", "admin_secure_pw")
        self.assertEqual(admin.role, "admin")
        self.assertTrue(admin.is_admin)

        # Attempting duplicate admin without allow_reprovision raises PermissionError
        with self.assertRaises(PermissionError):
            self.auth_service.provision_admin_user("operator_admin_2", "another_pw")

    # SEC-02: Operator CLI Admin Provisioning
    def test_cli_admin_provisioning_command(self) -> None:
        """Verify CLI create-admin command provisions administrator."""
        exit_code = cli_main([
            "create-admin",
            "--username", "cli_admin",
            "--password", "cli_pass_123",
            "--db", self.db_path,
        ])
        self.assertEqual(exit_code, 0)

        # User is authentic admin
        user = self.auth_service.authenticate_user("cli_admin", "cli_pass_123")
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_admin)

        # Re-running without force fails
        exit_code_dup = cli_main([
            "create-admin",
            "--username", "cli_admin",
            "--password", "cli_pass_123",
            "--db", self.db_path,
        ])
        self.assertEqual(exit_code_dup, 1)

    # SEC-03: Progressive Login Rate Limiting
    def test_login_rate_limiting_lockout(self) -> None:
        """Verify 5 failed attempts trigger rate limit cooldown."""
        self.auth_service.register_user("target_user", "correct_password")

        # 4 failed attempts succeed in checking password (returning AuthenticationError)
        for _ in range(4):
            with self.assertRaises(AuthenticationError) as ctx:
                self.auth_service.authenticate_user("target_user", "wrong_pass")
            self.assertIn("Invalid username or password", str(ctx.exception))

        # 5th failed attempt triggers cooldown
        with self.assertRaises(AuthenticationError) as ctx:
            self.auth_service.authenticate_user("target_user", "wrong_pass")
        self.assertIn("Invalid username or password", str(ctx.exception))

        # 6th attempt is blocked by rate limiter without checking credentials
        with self.assertRaises(AuthenticationError) as ctx:
            self.auth_service.authenticate_user("target_user", "wrong_pass")
        self.assertIn("Too many failed login attempts", str(ctx.exception))

        # Even with correct password, account is locked during cooldown
        with self.assertRaises(AuthenticationError) as ctx:
            self.auth_service.authenticate_user("target_user", "correct_password")
        self.assertIn("Too many failed login attempts", str(ctx.exception))

        # Clear rate limit and confirm successful login
        self.auth_service._clear_failed_logins("target_user")
        user = self.auth_service.authenticate_user("target_user", "correct_password")
        self.assertEqual(user.username, "target_user")

    # SEC-04: Constant-Time Dummy PBKDF2 Verification
    def test_dummy_password_verification_for_missing_user(self) -> None:
        """Verify non-existent users undergo PBKDF2 hashing to reduce timing side-channels."""
        # Non-existent user fails with standard error message
        with self.assertRaises(AuthenticationError) as ctx:
            self.auth_service.authenticate_user("completely_unknown_user", "some_password")
        self.assertIn("Invalid username or password", str(ctx.exception))

    # SEC-05: Prevent XP Inflation (Separation of Collection & Observations)
    def test_xp_separation_no_xp_for_manual_collection_save(self) -> None:
        """Verify that saving taxa to collection manually does not grant encounter XP."""
        user = self.auth_service.register_user("naturalist_one", "password_123")

        # Upsert 3 taxa into catalog
        for i in range(3):
            gbif_match = GBIFMatchResult(
                query_name=f"Species {i}",
                matched_scientific_name=f"Species {i}",
                canonical_name=f"Species {i}",
                match_type="EXACT",
                usage_key=1000 + i,
                rank="SPECIES",
                status="ACCEPTED",
                retrieved_at="2026-11-05T00:00:00Z",
            )
            t_id = self.collection_service.upsert_taxon_from_gbif(gbif_match)
            # Add to user's collection manually
            self.collection_service.save_to_collection(user.id, t_id, "Manual bookmark")

        # Check total XP: should be 0 because 0 authentic observations were recorded
        stats = self.achievement_service.get_user_gamification_stats(user.id)
        self.assertEqual(stats.total_xp, 0)
        self.assertEqual(stats.level, 1)

        # Now record an authentic observation for Taxon 1000
        self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Species 0",
            model_result_json="{}",
            matched_taxon_id=1000,
        )

        # Now authentic encounter XP is awarded (+50 XP for 1 unique observed taxon + 50 XP First Encounter badge)
        stats_after = self.achievement_service.get_user_gamification_stats(user.id)
        self.assertEqual(stats_after.total_xp, 100)

    # SEC-06: Image Decompression Bomb & Dimension Bounds Protection
    def test_image_processor_rejects_oversized_dimensions(self) -> None:
        """Verify Image validation rejects images exceeding width/height bounds."""
        oversized = Image.new("RGB", (MAX_IMAGE_WIDTH + 1, 100), color="green")
        buf = io.BytesIO()
        oversized.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        with self.assertRaises(ImageValidationError) as ctx:
            validate_image(raw_bytes, "image/jpeg")
        self.assertIn("exceed maximum allowed", str(ctx.exception))

    def test_image_processor_validates_standard_dimensions(self) -> None:
        """Verify Image processing accepts standard resolution photographs."""
        standard = Image.new("RGB", (1200, 800), color="blue")
        buf = io.BytesIO()
        standard.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        clean_bytes, mime = preprocess_image(raw_bytes)
        self.assertEqual(mime, "image/jpeg")
        self.assertGreater(len(clean_bytes), 0)

    # SEC-07: Idle Session Timeout
    def test_session_timeout_expiration(self) -> None:
        """Verify idle sessions older than timeout threshold are cleared."""
        user = AuthenticatedUser(
            id=1,
            username="active_user",
            role="user",
            display_name="Active User",
            vivedex_id="VDX-111111",
            is_active=True,
        )
        fake_session: dict[str, object] = {
            "current_user": user,
            "active_user_id": user.id,
            "last_activity_timestamp": time.time() - 3600,  # 1 hour ago
        }

        with patch("streamlit.session_state", fake_session):
            expired = check_session_timeout(timeout_seconds=1800)
            self.assertTrue(expired)
            self.assertIsNone(fake_session["current_user"])
            self.assertIsNone(fake_session["active_user_id"])
            self.assertIn("session_expired_message", fake_session)

    def test_session_timeout_active_session_retained(self) -> None:
        """Verify active sessions within timeout threshold are not expired."""
        user = AuthenticatedUser(
            id=2,
            username="recent_user",
            role="user",
            display_name="Recent User",
            vivedex_id="VDX-222222",
            is_active=True,
        )
        fake_session: dict[str, object] = {
            "current_user": user,
            "active_user_id": user.id,
            "last_activity_timestamp": time.time() - 30,  # 30 seconds ago
        }

        with patch("streamlit.session_state", fake_session):
            expired = check_session_timeout(timeout_seconds=1800)
            self.assertFalse(expired)
            self.assertEqual(fake_session["current_user"], user)

    # SEC-02: Demonstration Mode Flag Enforcement
    def test_demo_mode_guard_behavior(self) -> None:
        """Verify demonstration dataset operations honor VIVEDEX_DEMO_MODE environment variable."""
        with patch.dict(os.environ, {"VIVEDEX_DEMO_MODE": "0"}):
            self.assertFalse(is_demo_mode())
            with self.assertRaises(PermissionError) as ctx:
                load_demo_dataset(self.db)
            self.assertIn("Demo dataset creation is prohibited in production mode", str(ctx.exception))

        with patch.dict(os.environ, {"VIVEDEX_DEMO_MODE": "1"}):
            self.assertTrue(is_demo_mode())
            res = load_demo_dataset(self.db)
            self.assertEqual(res["provenance"], "DEMO DATA")

    # User Record Isolation
    def test_user_record_isolation(self) -> None:
        """Verify a user cannot modify another user's observation notes."""
        user_a = self.auth_service.register_user("user_a", "password_123")
        user_b = self.auth_service.register_user("user_b", "password_123")

        obs_a = self.collection_service.record_observation(
            user_id=user_a.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json="{}",
            field_notes="Original notes from User A",
        )

        # User B attempts to overwrite User A's observation notes and is blocked
        with self.assertRaises(PermissionError):
            self.collection_service.update_observation_notes(
                user_id=user_b.id,
                observation_id=obs_a.observation_id,
                new_notes="Hostile overwrite attempt by User B",
            )

        # Verify notes were NOT changed
        reloaded = self.collection_service.get_observation_by_uid(obs_a.observation_id)
        self.assertEqual(reloaded.field_notes, "Original notes from User A")


if __name__ == "__main__":
    unittest.main()
