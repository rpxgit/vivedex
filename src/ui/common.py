"""Shared layout components, navigation breadcrumbs, and authentication drawer for Vivédex.

Integrates centralized design tokens and provides seamless account access.
Enforces session timeout, strict HTML escaping, and environment-aware demonstration controls.
"""

from __future__ import annotations

import time
import streamlit as st

from src.auth import AuthenticatedUser, AuthenticationError, AuthService
from src.database import Database
from src.demo_data import is_demo_mode, load_demo_dataset
from src.ui.theme import (
    escape_text,
    get_naturalist_rank,
    inject_theme_styles,
    render_security_badge,
)

SESSION_IDLE_TIMEOUT_SECONDS = 30 * 60  # 30-minute idle session timeout (SEC-07)


def inject_custom_styles() -> None:
    """Wrapper calling the centralized theme style injector."""
    inject_theme_styles()


def render_security_notice() -> None:
    """Render the standard security notice."""
    render_security_badge()


def check_session_timeout(timeout_seconds: int = SESSION_IDLE_TIMEOUT_SECONDS) -> bool:
    """Enforce idle session expiration (SEC-07).

    Returns True if session was expired and cleared.
    """
    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    if current_user is None:
        return False

    now = time.time()
    last_act = st.session_state.get("last_activity_timestamp")
    if last_act is not None and (now - last_act) > timeout_seconds:
        st.session_state["current_user"] = None
        st.session_state["active_user_id"] = None
        st.session_state["last_activity_timestamp"] = None
        st.session_state["session_expired_message"] = (
            "Session expired after 30 minutes of inactivity. Please log in again."
        )
        return True

    st.session_state["last_activity_timestamp"] = now
    return False


def render_breadcrumbs(crumbs: list[tuple[str, str | None]]) -> None:
    """Render clean, museum-grade breadcrumbs with strict HTML escaping (SEC-01).

    Each crumb is a tuple of (label, optional_url_target).
    """
    html_parts = []
    for label, target in crumbs:
        safe_label = escape_text(label)
        if target:
            html_parts.append(
                f'<span style="color: #718568; font-weight: 500;">{safe_label}</span>'
            )
        else:
            html_parts.append(
                f'<span style="color: #183B32; font-weight: 700;">{safe_label}</span>'
            )
    crumbs_html = " &nbsp;›&nbsp; ".join(html_parts)
    st.markdown(
        f'<div style="font-size: 0.85rem; margin-bottom: 1.1rem; padding: 6px 0; border-bottom: 1px solid #e8e3d8;">{crumbs_html}</div>',
        unsafe_allow_html=True,
    )


def render_auth_controls(auth_service: AuthService, db: Database) -> None:
    """Render the authentication and researcher profile panel in the sidebar."""
    # Check session expiration before rendering
    if check_session_timeout():
        st.rerun()

    if st.session_state.get("session_expired_message"):
        st.sidebar.warning(st.session_state.pop("session_expired_message"))

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    demo_active = is_demo_mode()
    env_badge = (
        '<span style="font-size: 0.72rem; background: #FEF7E0; color: #B06000; padding: 2px 6px; border-radius: 4px; font-weight: 700;">DEV / DEMO</span>'
        if demo_active
        else '<span style="font-size: 0.72rem; background: #E6F4EA; color: #137333; padding: 2px 6px; border-radius: 4px; font-weight: 700;">PRODUCTION</span>'
    )

    st.sidebar.markdown(
        f"""
        <div style="padding-bottom: 12px; border-bottom: 1px solid #e3ddd0; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-family: 'Cinzel', serif; font-size: 1.5rem; font-weight: 700; color: #183B32;">🌿 Vivédex</div>
                <div>{env_badge}</div>
            </div>
            <div style="font-size: 0.78rem; color: #777E73; text-transform: uppercase; letter-spacing: 0.04em;">Biodiversity Discovery Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if current_user is not None:
        from src.achievements import AchievementService

        ach_service = AchievementService(db)
        stats = ach_service.get_user_gamification_stats(current_user.id)
        rank_title = get_naturalist_rank(stats.level)

        safe_display_name = escape_text(current_user.display_name)
        safe_vivedex_id = escape_text(current_user.vivedex_id)
        safe_role = escape_text(current_user.role.upper())

        st.sidebar.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #ded6c5; border-radius: 8px; padding: 12px; margin-bottom: 14px;">
                <div style="font-size: 0.75rem; text-transform: uppercase; color: #777E73; font-weight: 700;">Field Naturalist</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #183B32;">{safe_display_name}</div>
                <div style="font-size: 0.8rem; color: #A66B48; font-weight: 600;">Level {stats.level} {escape_text(rank_title)} ({stats.total_xp} XP)</div>
                <div style="font-size: 0.75rem; color: #666; font-family: monospace; margin-top: 4px;">ID: {safe_vivedex_id} &bull; {safe_role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("🚪 Log Out", width="stretch", key="auth_logout_btn"):
            st.session_state["current_user"] = None
            st.session_state["active_user_id"] = None
            st.session_state["last_activity_timestamp"] = None
            st.session_state["selected_taxon_id"] = None
            st.sidebar.success("Logged out successfully.")
            st.rerun()
    else:
        st.sidebar.markdown("#### Naturalist Access")
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
                        st.session_state["last_activity_timestamp"] = time.time()
                        st.success(f"Welcome, {escape_text(user.display_name)}!")
                        st.rerun()
                    except AuthenticationError as e:
                        st.error(str(e))

        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("Username", key="reg_username")
                reg_name = st.text_input("Display Name", key="reg_name")
                reg_pwd = st.text_input(
                    "Password (min 8 chars)", type="password", key="reg_pwd"
                )
                reg_submit = st.form_submit_button("Create Account", width="stretch")

                if reg_submit:
                    try:
                        user = auth_service.register_user(
                            username=reg_user,
                            password=reg_pwd,
                            display_name=reg_name,
                        )
                        st.session_state["current_user"] = user
                        st.session_state["active_user_id"] = user.id
                        st.session_state["last_activity_timestamp"] = time.time()
                        st.success("Account registered as standard field naturalist!")
                        st.rerun()
                    except AuthenticationError as e:
                        st.error(str(e))

    # Quick Demo Account Switch (Accessible exclusively in demonstration mode - SEC-02)
    if demo_active:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, role FROM users WHERE username IN ('demo_admin', 'demo_naturalist') ORDER BY role ASC;"
            )
            demo_accounts = cursor.fetchall()

        if demo_accounts:
            st.sidebar.markdown("---")
            st.sidebar.markdown(
                '<div style="font-size: 0.75rem; text-transform: uppercase; color: #777E73; font-weight: 700; margin-bottom: 6px;">⚡ Quick Demo Accounts</div>',
                unsafe_allow_html=True,
            )
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
                        st.session_state["last_activity_timestamp"] = time.time()
                        st.rerun()

        # Fresh database demonstration dataset loader
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]

        if user_count == 0:
            st.sidebar.info(
                "Database is fresh. Load sample demo records to start exploring."
            )
            if st.sidebar.button(
                "📦 Load Sample Demo Data", width="stretch", key="init_demo_btn"
            ):
                load_demo_dataset(db)
                st.sidebar.success("Demo dataset loaded!")
                st.rerun()
