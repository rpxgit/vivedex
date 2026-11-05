"""Account Settings and AI Provider Configuration for Vivédex.

Features Bring Your Own Key (BYOK) credential management for Meta Model API (Muse Spark),
session-isolated memory storage, connection verification, and naturalist account information.
"""

from __future__ import annotations

import os
import streamlit as st

from src.auth import AuthenticatedUser, AuthService
from src.database import Database
from src.meta_adapter import MetaAPIAdapter
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_settings_page(
    db: Database,
    auth_service: AuthService,
    meta_adapter: MetaAPIAdapter,
) -> None:
    """Render the user Account Settings and BYOK Meta API configuration interface."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Hero Banner
    render_hero_banner(
        title="Account & AI Provider Settings",
        subtitle="Manage your naturalist credentials, configure personal Meta Model API access, and review privacy safeguards.",
    )

    if current_user is None:
        st.warning(
            "🔒 **Authentication Required:** You must be signed in to manage account settings and connect personal API keys. "
            "Please use the sign-in form in the sidebar or return to the Expedition Hub."
        )
        return

    # Tabs for Settings Sections
    tab_ai, tab_account, tab_security, tab_privacy = st.tabs(
        [
            "🤖 AI Provider Settings",
            "👤 Account Information",
            "🔒 Security",
            "🛡️ Privacy Safeguards",
        ]
    )

    # -------------------------------------------------------------------------
    # TAB 1: AI PROVIDER SETTINGS (CONNECT META MODEL API)
    # -------------------------------------------------------------------------
    with tab_ai:
        st.markdown("## Connect Meta Model API")
        st.markdown(
            "Connect your own Meta Model API account to power live biodiversity identification with **Meta Muse Spark** (`muse-spark-1.3`). "
            "Vivédex operates on a **Bring Your Own Key (BYOK)** model for independent naturalist research."
        )

        # Session-Only Credential Isolation Notice
        st.info(
            "🔒 **Session-Only Memory Storage:** Your API key stays in server memory for this session only. "
            "Vivédex does NOT save it to your account or database. You may need to enter it again in a new session."
        )

        user_key: str | None = st.session_state.get("user_meta_api_key")
        conn_status: str = st.session_state.get("user_meta_connection_status", "NOT_CONNECTED")
        conn_msg: str = st.session_state.get("user_meta_connection_msg", "")

        # ---------------------------------------------------------------------
        # Step 1: Obtain an API Key
        # ---------------------------------------------------------------------
        with st.expander("📖 Step 1 — Obtain an API key from Meta", expanded=not bool(user_key)):
            st.markdown(
                """
                1. Open the [Meta Model API Dashboard](https://dev.meta.ai/) (opens in new window).
                2. Sign in to your Meta developer account.
                3. Open the **API Keys** section.
                4. Select **Create API Key**.
                5. Enter a descriptive label (e.g. `Vivedex-Naturalist-Client`).
                6. Copy the generated key string.
                
                For setup documentation, read the [Meta Model API Quickstart Guide](https://dev.meta.ai/docs/quickstart).
                """
            )
            col_link1, col_link2 = st.columns(2)
            with col_link1:
                st.link_button("🔗 Open Meta Developer Dashboard", "https://dev.meta.ai/", use_container_width=True)
            with col_link2:
                st.link_button("📖 Read API Quickstart Docs", "https://dev.meta.ai/docs/quickstart", use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # Step 2 & 3 & 4: Enter Key, Test, and Connection Status
        # ---------------------------------------------------------------------
        if user_key:
            # Active Key Presentation (Masked)
            masked_hint = f"••••••••••••••••••••...{user_key[-4:]}" if len(user_key) >= 8 else "••••••••••••••••••••"

            st.markdown("### Active Connection Status")

            # Status Badge Rendering
            if conn_status == "CONNECTED":
                st.success(f"🟢 **CONNECTED:** Meta Muse Spark is connected. Live identification is available. (Model: `{MetaAPIAdapter.MODEL_ID}`)")
            elif conn_status == "INVALID_KEY":
                st.error(f"🔴 **INVALID KEY:** {conn_msg or 'Authentication failed. The key was rejected by the Meta API endpoint.'}")
            elif conn_status == "RATE_LIMITED":
                st.warning(f"🟡 **RATE LIMITED:** {conn_msg or 'Meta Model API rate limits exceeded. Please retry shortly.'}")
            elif conn_status == "CONNECTION_FAILED":
                st.error(f"🟠 **CONNECTION FAILED:** {conn_msg or 'Could not communicate with Meta Model API endpoint.'}")
            else:
                st.info("ℹ️ **KEY ENTERED — NOT VERIFIED:** Click 'Test Connection' below to verify this key with Meta Muse Spark.")

            col_info1, col_info2 = st.columns([2, 1])
            with col_info1:
                st.markdown(f"**Connected Model:** `{MetaAPIAdapter.MODEL_ID}`")
                st.markdown(f"**Credential Source:** `My Meta API Key`")
                st.markdown(f"**Session Key:** `{masked_hint}`")
            with col_info2:
                st.caption("Active in server-side session memory.")

            # Controls: Test Connection, Replace Key, Disconnect
            st.markdown("#### Key Controls")
            col_test, col_replace, col_disc = st.columns([1, 1, 1], gap="small")

            with col_test:
                if st.button("🧪 Test Connection", type="primary", use_container_width=True, key="settings_test_btn"):
                    with st.spinner("Testing connection to Meta Model API (muse-spark-1.3)..."):
                        status_name, display_msg, _ = meta_adapter.test_connection(user_key)
                        st.session_state["user_meta_connection_status"] = status_name
                        st.session_state["user_meta_connection_msg"] = display_msg
                        st.rerun()

            with col_replace:
                if st.button("🔄 Replace API Key", use_container_width=True, key="settings_replace_btn"):
                    st.session_state["settings_show_replace_form"] = True
                    st.rerun()

            with col_disc:
                if st.button("🚪 Disconnect", use_container_width=True, key="settings_disconnect_btn"):
                    st.session_state.pop("user_meta_api_key", None)
                    st.session_state.pop("user_meta_connection_status", None)
                    st.session_state.pop("user_meta_connection_msg", None)
                    st.session_state.pop("settings_show_replace_form", None)
                    st.success("API key removed from session memory. Vivédex is now disconnected.")
                    st.rerun()

            # Form to replace existing key
            if st.session_state.get("settings_show_replace_form"):
                st.markdown("---")
                st.markdown("#### Enter New Meta Model API Key")
                with st.form("replace_meta_key_form"):
                    new_key_raw = st.text_input(
                        "New Meta Model API Key",
                        type="password",
                        placeholder="Paste new Meta Model API key",
                        help="Enter your new key. Accidental leading or trailing spaces are trimmed automatically.",
                    )
                    col_sub1, col_sub2 = st.columns([1, 1])
                    with col_sub1:
                        replace_submit = st.form_submit_button("Verify & Save to Session", type="primary", use_container_width=True)
                    with col_sub2:
                        cancel_replace = st.form_submit_button("Cancel", use_container_width=True)

                    if cancel_replace:
                        st.session_state["settings_show_replace_form"] = False
                        st.rerun()

                    if replace_submit:
                        cleaned = new_key_raw.strip()
                        if not cleaned:
                            st.error("API key cannot be empty. Please enter your Meta Model API key.")
                        else:
                            st.session_state["user_meta_api_key"] = cleaned
                            st.session_state["settings_show_replace_form"] = False
                            with st.spinner("Verifying new key with Meta Muse Spark..."):
                                status_name, display_msg, _ = meta_adapter.test_connection(cleaned)
                                st.session_state["user_meta_connection_status"] = status_name
                                st.session_state["user_meta_connection_msg"] = display_msg
                            st.rerun()

        else:
            # No Key Connected State
            st.markdown("### Step 2 — Enter your key")
            st.markdown(
                '<span class="rank-pill" style="background:#F0EDE4; color:#5A544A;">NOT CONNECTED</span>',
                unsafe_allow_html=True,
            )

            col_input, col_show = st.columns([4, 1])
            with col_show:
                show_key = st.checkbox("Show key", key="settings_show_key_toggle")
            with col_input:
                key_input = st.text_input(
                    "Meta Model API Key",
                    type="default" if show_key else "password",
                    placeholder="Paste your Meta Model API key",
                    help="Your key is kept in volatile server memory for this session and never written to permanent storage.",
                    key="settings_key_input",
                )

            connect_clicked = st.button("Connect Meta Model API", type="primary", use_container_width=True, key="settings_connect_btn")
            if connect_clicked:
                cleaned_input = key_input.strip()
                if not cleaned_input:
                    st.error("API key cannot be empty. Please paste a valid Meta Model API key.")
                else:
                    st.session_state["user_meta_api_key"] = cleaned_input
                    with st.spinner("Verifying connection to Meta Model API (muse-spark-1.3)..."):
                        status_name, display_msg, _ = meta_adapter.test_connection(cleaned_input)
                        st.session_state["user_meta_connection_status"] = status_name
                        st.session_state["user_meta_connection_msg"] = display_msg
                    st.rerun()

        # Operator Fallback Status Info
        st.markdown("---")
        st.markdown("### Credential Precedence & Availability")
        has_env_key = bool(os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY"))
        if has_env_key:
            st.info(
                "ℹ️ **Application-Provided Key Available:** An operator key is configured in the environment. "
                "Whenever your personal key is connected, Vivédex prioritizes **My Meta API Key** for all your observations."
            )
        else:
            st.caption("No application-wide environment key is configured. Individual user keys or Demo Fixture Mode are required for observations.")

    # -------------------------------------------------------------------------
    # TAB 2: ACCOUNT INFORMATION
    # -------------------------------------------------------------------------
    with tab_account:
        st.markdown("## Account Information")
        st.markdown("Your persistent naturalist profile and system attribution.")

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.write(f"**Username:** `{escape_text(current_user.username)}`")
            st.write(f"**Naturalist Display Name:** {escape_text(current_user.display_name)}")
            st.write(f"**Contributor ID:** `{escape_text(current_user.vivedex_id)}`")
        with col_a2:
            st.write(f"**Naturalist Role:** `{escape_text(current_user.role.upper())}`")
            st.write(f"**Account Created:** {escape_text(current_user.created_at[:10])}")
            st.write(f"**Administrator Privileges:** {'Yes' if current_user.is_admin else 'Standard User'}")

        st.caption("To update your biography, institution, or ORCID identifier, visit your [Researcher Passport](/passport).")

    # -------------------------------------------------------------------------
    # TAB 3: SECURITY
    # -------------------------------------------------------------------------
    with tab_security:
        st.markdown("## Security & Session Controls")
        st.markdown(
            "Vivédex applies cryptographic password hashing using **PBKDF2-HMAC-SHA256** with 600,000 iterations. "
            "Sensitive credentials are never stored in plaintext."
        )

        st.markdown("### Password Management")
        with st.form("settings_password_form"):
            curr_pass = st.text_input("Current Password", type="password", key="settings_curr_pass")
            new_pass = st.text_input("New Password (min 8 characters)", type="password", key="settings_new_pass")
            conf_pass = st.text_input("Confirm New Password", type="password", key="settings_conf_pass")
            pass_submit = st.form_submit_button("Update Password", use_container_width=True)

            if pass_submit:
                if not curr_pass or not new_pass:
                    st.error("All password fields are required.")
                elif len(new_pass) < 8:
                    st.error("New password must be at least 8 characters long.")
                elif new_pass != conf_pass:
                    st.error("New password and confirmation do not match.")
                else:
                    try:
                        # Verify current password
                        auth_service.authenticate_user(current_user.username, curr_pass)
                        # Hash and update in DB
                        auth_service.update_password(current_user.id, new_pass)
                        st.success("✅ Password updated successfully!")
                    except Exception as e:
                        st.error(f"Failed to update password: {str(e)}")

        st.markdown("### Active Session")
        st.write(f"**Authenticated As:** `{escape_text(current_user.username)}` ({escape_text(current_user.vivedex_id)})")
        if st.button("🚪 Log Out of Vivédex", key="settings_logout_btn"):
            st.session_state["current_user"] = None
            st.session_state["active_user_id"] = None
            st.session_state.pop("user_meta_api_key", None)
            st.session_state.pop("user_meta_connection_status", None)
            st.session_state.pop("user_meta_connection_msg", None)
            st.success("Logged out successfully.")
            st.rerun()

    # -------------------------------------------------------------------------
    # TAB 4: PRIVACY SAFEGUARDS
    # -------------------------------------------------------------------------
    with tab_privacy:
        st.markdown("## Naturalist Privacy Safeguards")
        st.markdown(
            """
            Vivédex is engineered according to strict naturalist data minimization principles:
            
            1. **Volatile Memory Credential Isolation:**
               Personal Meta Model API keys reside exclusively in temporary server session memory. 
               Keys are never written to SQLite, user profile rows, observations, export files, or persistent disk.
               
            2. **In-Memory EXIF Metadata Stripping:**
               When you upload a specimen photograph for identification, embedded EXIF metadata—including 
               precise GPS coordinates, camera serial numbers, and device timestamps—is stripped in volatile memory 
               before analysis.
               
            3. **Zero Permanent Image Retention:**
               Specimen photographs are analyzed in memory and immediately discarded. Vivédex never stores 
               raw photographs in permanent databases or public cloud buckets.
               
            4. **Transparent Taxonomic Provenance:**
               All species matches are reconciled against the global GBIF Backbone Taxonomy and clearly 
               attributed with CC BY 4.0 licensing and confidence scores.
            """
        )
