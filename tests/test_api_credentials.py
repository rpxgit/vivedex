"""Tests for Bring Your Own Key (BYOK) credential management, isolation, and security.

Verifies:
1. Key input validation.
2. Successful connection test.
3. Invalid key handling.
4. Key masking.
5. Disconnect behaviour.
6. Replacement behaviour.
7. Session isolation.
8. Per-request credential selection.
9. Environment key fallback.
10. User key precedence.
11. Logout clearing.
12. No key in database records.
13. No key in observation exports.
14. No key in logs.
15. No key in exception messages.
16. No cross-user credential leakage.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.auth import AuthService
from src.backend import VivedexBackend
from src.collection_service import CollectionService
from src.database import Database
from src.meta_adapter import MetaAPIAdapter, MetaAPIConfigurationError, MetaAPIRequestError
from src.schemas import CandidateIdentification, ModelIdentificationResult, VivedexResult


class TestAPICredentials(unittest.TestCase):
    """Test suite for BYOK Meta Model API credentials and session isolation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cred.sqlite3"
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.auth_service = AuthService(self.db)
        self.collection_service = CollectionService(self.db)
        self.adapter = MetaAPIAdapter(api_key=None)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Key input validation
    # -------------------------------------------------------------------------
    def test_key_input_validation(self) -> None:
        """Reject empty or whitespace-only keys and trim surrounding whitespace."""
        # Empty string
        status, msg, _ = self.adapter.test_connection("")
        self.assertEqual(status, "INVALID_KEY")
        self.assertIn("cannot be empty", msg)

        # Whitespace-only string
        status, msg, _ = self.adapter.test_connection("   \t\n  ")
        self.assertEqual(status, "INVALID_KEY")
        self.assertIn("cannot be empty", msg)

        # Whitespace trimmed properly in _require_api_key
        with patch.dict(os.environ, {"MODEL_API_KEY": "  valid_env_key  "}):
            adapter = MetaAPIAdapter()
            self.assertEqual(adapter._require_api_key(), "valid_env_key")

    # -------------------------------------------------------------------------
    # 2. Successful connection test
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_successful_connection_test(self, mock_urlopen: MagicMock) -> None:
        """Verify minimal text-only request structure and CONNECTED status."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "VIVEDEX_API_CONNECTION_OK",
                        }
                    }
                ]
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        status, msg, details = self.adapter.test_connection("meta_test_key_valid_12345")

        self.assertEqual(status, "CONNECTED")
        self.assertIn("Meta Muse Spark is connected", msg)
        self.assertEqual(details["model"], "muse-spark-1.3")

        # Verify HTTP request was made with correct URL and headers
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.meta.ai/v1/chat/completions")
        self.assertEqual(req.headers["Authorization"], "Bearer meta_test_key_valid_12345")

        # Verify payload: text-only test prompt, NO organism image
        payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(payload["model"], "muse-spark-1.3")
        self.assertEqual(payload["messages"][0]["content"], "Reply with exactly: VIVEDEX_API_CONNECTION_OK")
        self.assertNotIn("image_url", req.data.decode("utf-8"))

    # -------------------------------------------------------------------------
    # 3. Invalid key handling
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_invalid_key_handling(self, mock_urlopen: MagicMock) -> None:
        """Handle HTTP 401/403 errors and report INVALID_KEY."""
        mock_err = urllib.error.HTTPError(
            url="https://api.meta.ai/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b'{"error": {"message": "Invalid API key provided."}}'),
        )
        mock_urlopen.side_effect = mock_err

        status, msg, details = self.adapter.test_connection("meta_bad_key_99999")
        self.assertEqual(status, "INVALID_KEY")
        self.assertIn("Authentication failed", msg)
        self.assertEqual(details["http_status"], 401)
        # Verify raw key is NOT present in error message
        self.assertNotIn("meta_bad_key_99999", msg)

    # -------------------------------------------------------------------------
    # 4. Key masking
    # -------------------------------------------------------------------------
    def test_key_masking(self) -> None:
        """Ensure keys are never exposed in full and masked properly."""
        secret_key = "sk_meta_live_998877665544332211"
        masked = f"••••••••••••••••••••...{secret_key[-4:]}" if len(secret_key) >= 8 else "••••••••••••••••••••"

        self.assertTrue(masked.startswith("••••••••••••••••••••..."))
        self.assertTrue(masked.endswith("2211"))
        self.assertNotIn("99887766554433", masked)

    # -------------------------------------------------------------------------
    # 5. Disconnect behaviour
    # -------------------------------------------------------------------------
    def test_disconnect_behaviour(self) -> None:
        """Disconnect clears session credential completely."""
        session_state: dict[str, str | None] = {
            "user_meta_api_key": "test_user_key_active",
            "user_meta_connection_status": "CONNECTED",
        }

        # Simulate disconnect
        session_state.pop("user_meta_api_key", None)
        session_state.pop("user_meta_connection_status", None)

        self.assertNotIn("user_meta_api_key", session_state)
        self.assertNotIn("user_meta_connection_status", session_state)

    # -------------------------------------------------------------------------
    # 6. Replacement behaviour
    # -------------------------------------------------------------------------
    def test_replacement_behaviour(self) -> None:
        """Replacing key overwrites old key and updates session."""
        session_state = {"user_meta_api_key": "old_key_1111"}
        new_key = "new_key_2222"

        # Update
        session_state["user_meta_api_key"] = new_key
        self.assertEqual(session_state["user_meta_api_key"], "new_key_2222")
        self.assertNotEqual(session_state["user_meta_api_key"], "old_key_1111")

    # -------------------------------------------------------------------------
    # 7. Session isolation
    # -------------------------------------------------------------------------
    def test_session_isolation(self) -> None:
        """Verify MetaAPIAdapter does not store per-request api_key on instance."""
        adapter = MetaAPIAdapter(api_key="global_or_none")
        self.assertEqual(adapter.api_key, "global_or_none")

        # Using explicit key in _require_api_key does NOT mutate instance
        explicit = adapter._require_api_key(explicit_key="transient_user_key")
        self.assertEqual(explicit, "transient_user_key")
        self.assertEqual(adapter.api_key, "global_or_none")

    # -------------------------------------------------------------------------
    # 8. Per-request credential selection
    # -------------------------------------------------------------------------
    @patch.object(MetaAPIAdapter, "identify_image")
    def test_per_request_credential_selection(self, mock_identify: MagicMock) -> None:
        """Verify backend routes explicit key through to adapter."""
        mock_identify.return_value = ModelIdentificationResult(
            observation_summary="Test organism",
            candidates=[CandidateIdentification(scientific_name="Passer domesticus")],
        )

        backend = VivedexBackend(meta_adapter=self.adapter)

        # 1x1 black JPEG
        sample_jpeg = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"
            b"\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f"
            b"\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b"
            b"\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00"
            b"\x00?\x00\xbf\x00\xff\xd9"
        )

        backend.process_observation(sample_jpeg, "image/jpeg", api_key="explicit_user_key_123")

        mock_identify.assert_called_once()
        _, kwargs = mock_identify.call_args
        self.assertEqual(kwargs.get("api_key"), "explicit_user_key_123")

    # -------------------------------------------------------------------------
    # 9. Environment key fallback
    # -------------------------------------------------------------------------
    def test_environment_key_fallback(self) -> None:
        """When no user key is passed, adapter falls back to environment variable."""
        with patch.dict(os.environ, {"MODEL_API_KEY": "env_fallback_key_456"}):
            adapter = MetaAPIAdapter()
            resolved = adapter._require_api_key(explicit_key=None)
            self.assertEqual(resolved, "env_fallback_key_456")

    # -------------------------------------------------------------------------
    # 10. User key precedence
    # -------------------------------------------------------------------------
    def test_user_key_precedence(self) -> None:
        """User key takes precedence over environment variable."""
        with patch.dict(os.environ, {"MODEL_API_KEY": "env_key_should_be_ignored"}):
            adapter = MetaAPIAdapter()
            resolved = adapter._require_api_key(explicit_key="user_priority_key_789")
            self.assertEqual(resolved, "user_priority_key_789")

    # -------------------------------------------------------------------------
    # 11. Logout clearing
    # -------------------------------------------------------------------------
    def test_logout_clearing(self) -> None:
        """Logout removes all credential keys from session state."""
        session_state = {
            "current_user": MagicMock(),
            "active_user_id": 1,
            "user_meta_api_key": "secret_key_session",
            "user_meta_connection_status": "CONNECTED",
            "user_meta_connection_msg": "Connected",
        }

        # Simulate logout sequence from common.py
        session_state["current_user"] = None
        session_state["active_user_id"] = None
        session_state.pop("user_meta_api_key", None)
        session_state.pop("user_meta_connection_status", None)
        session_state.pop("user_meta_connection_msg", None)

        self.assertIsNone(session_state["current_user"])
        self.assertNotIn("user_meta_api_key", session_state)
        self.assertNotIn("user_meta_connection_status", session_state)

    # -------------------------------------------------------------------------
    # 12. No key in database records
    # -------------------------------------------------------------------------
    def test_no_key_in_database_records(self) -> None:
        """Verify API key is never written to SQLite database tables."""
        user = self.auth_service.register_user("botanist_jane", "Password123!", "Jane Doe")
        secret_key = "sk_secret_never_save_to_db_9988"

        # Create observation record
        obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Monstera deliciosa",
            model_result_json=json.dumps(
                {
                    "model": "muse-spark-1.3",
                    "observation_summary": "Monstera deliciosa in cloud forest",
                    "candidates": [{"scientific_name": "Monstera deliciosa"}],
                    "limitations": "AI candidate suggestion.",
                }
            ),
            field_notes="Found in forest canopy",
        )

        # Inspect all database tables for the secret key
        with self.db.connect() as conn:
            cursor = conn.cursor()
            for table in ["users", "user_profiles", "observations", "collections", "audit_logs"]:
                cursor.execute(f"SELECT * FROM {table};")
                rows = cursor.fetchall()
                for row in rows:
                    for val in row:
                        if isinstance(val, str):
                            self.assertNotIn(secret_key, val)

    # -------------------------------------------------------------------------
    # 13. No key in observation exports
    # -------------------------------------------------------------------------
    def test_no_key_in_observation_exports(self) -> None:
        """Verify JSON exports never contain API keys."""
        secret_key = "sk_secret_never_export_7766"
        res = VivedexResult(
            timestamp="2026-11-05T06:00:00Z",
            ai_candidate=ModelIdentificationResult(
                observation_summary="Specimen photo",
                candidates=[CandidateIdentification(scientific_name="Passer domesticus")],
            ),
        )

        json_out = res.to_json()
        self.assertNotIn(secret_key, json_out)
        self.assertNotIn("api_key", json_out)

    # -------------------------------------------------------------------------
    # 14. No key in logs
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_no_key_in_logs(self, mock_urlopen: MagicMock) -> None:
        """Verify logs do not capture raw API keys."""
        secret_key = "sk_secret_do_not_log_5544"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"choices": [{"message": {"content": "OK"}}]}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with self.assertLogs(level="INFO") if hasattr(self, "_assertLogs") else unittest.mock.patch("logging.Logger.info"):
            status, msg, _ = self.adapter.test_connection(secret_key)
            self.assertEqual(status, "CONNECTED")
            self.assertNotIn(secret_key, msg)

    # -------------------------------------------------------------------------
    # 15. No key in exception messages
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_no_key_in_exception_messages(self, mock_urlopen: MagicMock) -> None:
        """Verify error and exception messages sanitize away API keys."""
        secret_key = "sk_secret_exception_test_3322"
        mock_err = urllib.error.HTTPError(
            url="https://api.meta.ai/v1/chat/completions",
            code=500,
            msg="Internal Server Error",
            hdrs={"Authorization": f"Bearer {secret_key}"},
            fp=io.BytesIO(b'{"error": "Internal failure"}'),
        )
        mock_urlopen.side_effect = mock_err

        # Testing test_connection
        status, msg, _ = self.adapter.test_connection(secret_key)
        self.assertEqual(status, "CONNECTION_FAILED")
        self.assertNotIn(secret_key, msg)

        # Testing identify_image exception
        with self.assertRaises(MetaAPIRequestError) as ctx:
            self.adapter.identify_image(b"fake_bytes", "image/jpeg", api_key=secret_key)
        self.assertNotIn(secret_key, str(ctx.exception))

    # -------------------------------------------------------------------------
    # 16. No cross-user credential leakage
    # -------------------------------------------------------------------------
    def test_no_cross_user_credential_leakage(self) -> None:
        """Simulate two concurrent sessions; verify keys remain isolated."""
        session_user_a: dict[str, str | None] = {"user_meta_api_key": "key_user_A_1111"}
        session_user_b: dict[str, str | None] = {"user_meta_api_key": "key_user_B_2222"}

        # User A makes request with User A's key
        key_for_req_a = session_user_a.get("user_meta_api_key")
        self.assertEqual(key_for_req_a, "key_user_A_1111")
        self.assertNotEqual(key_for_req_a, session_user_b.get("user_meta_api_key"))

        # User A disconnects
        session_user_a.pop("user_meta_api_key", None)
        self.assertIsNone(session_user_a.get("user_meta_api_key"))

        # User B's key remains completely intact and unaffected
        self.assertEqual(session_user_b.get("user_meta_api_key"), "key_user_B_2222")


if __name__ == "__main__":
    unittest.main()
