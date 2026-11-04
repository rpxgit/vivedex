"""Command-line administrative interface for Vivédex.

Provides secure, operator-gated administrator provisioning.
Enforces that administrator accounts cannot be bootstrapped via public HTTP registration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.auth import AuthService, AuthenticationError
from src.database import DEFAULT_DB_PATH, Database


def main() -> None:
    """Entry point for the Vivédex administrative CLI."""
    parser = argparse.ArgumentParser(
        description="Vivédex Administrative Command-Line Tool"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-admin subcommand
    create_parser = subparsers.add_parser(
        "create-admin",
        help="Explicitly provision an administrator account",
    )
    create_parser.add_argument(
        "--username",
        required=True,
        help="Administrator username (3-32 alphanumeric characters, - or _)",
    )
    create_parser.add_argument(
        "--password",
        required=True,
        help="Administrator password (minimum 8 characters)",
    )
    create_parser.add_argument(
        "--display-name",
        default=None,
        help="Optional public display name for the administrator",
    )
    create_parser.add_argument(
        "--db-path",
        default=None,
        help="Optional path to the SQLite database file",
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow provisioning even if an administrator account already exists",
    )

    # check-admin subcommand
    check_parser = subparsers.add_parser(
        "check-admin",
        help="Check whether active administrator accounts exist in the database",
    )
    check_parser.add_argument(
        "--db-path",
        default=None,
        help="Optional path to the SQLite database file",
    )

    args = parser.parse_args()
    db_path = Path(args.db_path) if args.db_path else DEFAULT_DB_PATH
    db = Database(db_path)
    db.initialize_schema()
    auth_service = AuthService(db)

    if args.command == "create-admin":
        try:
            admin = auth_service.provision_admin_user(
                username=args.username,
                password=args.password,
                display_name=args.display_name,
                allow_reprovision=args.force,
            )
            print(
                f"[SUCCESS] Administrator '{admin.username}' provisioned successfully "
                f"(ID: {admin.id}, Vivédex ID: {admin.vivedex_id})."
            )
            sys.exit(0)
        except (AuthenticationError, ValueError, PermissionError) as e:
            print(f"[ERROR] Failed to provision administrator: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "check-admin":
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, is_active FROM users WHERE role = 'admin';"
            )
            admins = cursor.fetchall()
            if admins:
                print(f"[INFO] {len(admins)} administrator account(s) found.")
                for row in admins:
                    status = "active" if row["is_active"] else "inactive"
                    print(
                        f"  - User ID: {row['id']}, Username: '{row['username']}', Status: {status}"
                    )
            else:
                print("[NOTICE] Zero administrator accounts exist in the database.")
            sys.exit(0)


if __name__ == "__main__":
    main()
