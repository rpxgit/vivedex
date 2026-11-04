"""Shared layout components, navigation helpers, and authentication controls for Vivédex.

Applies a cohesive nature-inspired theme and displays security prototype notices.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser, AuthenticationError, AuthService
from src.database import Database
from src.demo_data import load_demo_dataset

LOCAL_PROTOTYPE_NOTICE = (
    "LOCAL PROTOTYPE — AUTHENTICATION IS NOT PRODUCTION-HARDENED."
)


def inject_custom_styles() -> None:
    """Inject nature-inspired styling consistent across all platform pages."""
    st.markdown(
        """
        <style>
        /* Nature-inspired palette */
        :root {
            --primary-green: #2d6a4f;
            --soft-green: #d8f3dc;
            --forest-dark: #1b4332;
            --earth-slate: #2b2d42;
            --accent-gold: #e9c46a;
        }
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1b4332;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #555555;
            margin-bottom: 1.2rem;
        }
        .security-badge {
            background-color: #fff3cd;
            color: #856404;
            padding: 0.35rem 0.75rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            border-left: 4px solid #ffeeba;
            margin-bottom: 1rem;
        }
        .card-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }
        .taxon-rank-pill {
            display: inline-block;
            background-color: #d8f3dc;
            color: #1b4332;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
        }
        .status-pill {
            display: inline-block;
            background-color: #e2eafc;
            color: #1d3557;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
        }
        .provenance-tag {
            font-size: 0.72rem;
            color: #6c757d;
            font-family: monospace;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_security_notice() -> None:
    """Render the mandatory local prototype security banner."""
    st.markdown(
        f'<div class="security-badge">⚠️ {LOCAL_PROTOTYPE_NOTICE}</div>',
        unsafe_allow_html=True,
    )


def render_auth_controls(auth_service: AuthService, db: Database) -> None:
    """Render authentication and user account controls in the Streamlit sidebar."""
    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.sidebar.markdown("### 🌿 Vivédex")
    st.sidebar.caption("Biodiversity Discovery & Collection")

    if current_user is not None:
        st.sidebar.markdown(f"**Researcher:** {current_user.display_name}")
        st.sidebar.caption(f"ID: `{current_user.vivedex_id}` | Role: `{current_user.role.upper()}`")

        if st.sidebar.button("🚪 Log Out", width="stretch"):
            st.session_state["current_user"] = None
            st.sidebar.success("Logged out successfully.")
            st.rerun()
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### Account Access")
        tab_login, tab_register = st.sidebar.tabs(["Log In", "Register"])

        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username", key="login_username")
                login_pwd = st.text_input("Password", type="password", key="login_pwd")
                login_submit = st.form_submit_button("Log In", width="stretch")

                if login_submit:
                    try:
                        user = auth_service.authenticate_user(login_user, login_pwd)
                        st.session_state["current_user"] = user
                        st.session_state["active_user_id"] = user.id
                        st.success(f"Welcome back, {user.display_name}!")
                        st.rerun()
                    except AuthenticationError as e:
                        st.error(str(e))

        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("New Username", key="reg_username")
                reg_name = st.text_input("Display Name", key="reg_name")
                reg_pwd = st.text_input("Password (min 8 chars)", type="password", key="reg_pwd")
                reg_submit = st.form_submit_button("Register", width="stretch")

                if reg_submit:
                    try:
                        user = auth_service.register_user(
                            username=reg_user,
                            password=reg_pwd,
                            display_name=reg_name,
                        )
                        st.session_state["current_user"] = user
                        st.session_state["active_user_id"] = user.id
                        st.success(f"Account created! Role: {user.role.upper()}")
                        st.rerun()
                    except AuthenticationError as e:
                        st.error(str(e))

        # Quick Demo Account login if demo accounts exist
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users WHERE username IN ('demo_admin', 'demo_naturalist') ORDER BY role ASC;")
            demo_accounts = cursor.fetchall()

        if demo_accounts:
            st.sidebar.markdown("---")
            st.sidebar.markdown("#### ⚡ Quick Demo Switch")
            for d_user in demo_accounts:
                role_label = "Admin" if d_user["role"] == "admin" else "Naturalist"
                if st.sidebar.button(
                    f"👤 {d_user['username']} ({role_label})",
                    width="stretch",
                    key=f"quick_login_{d_user['id']}",
                ):
                    u = auth_service.get_user_by_id(d_user["id"])
                    if u:
                        st.session_state["current_user"] = u
                        st.session_state["active_user_id"] = u.id
                        st.rerun()

        # Check if database has users; if empty, offer one-click demo data load
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users;")
            count = cursor.fetchone()[0]

        if count == 0:
            st.sidebar.info("Database is empty. Register first user (Admin) or load sample data.")
            if st.sidebar.button("📦 Load Sample Demo Data", width="stretch"):
                res = load_demo_dataset(db)
                st.sidebar.success("Demo data loaded. Admin & Naturalist ready.")
                st.rerun()

