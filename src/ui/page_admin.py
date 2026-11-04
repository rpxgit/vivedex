"""Administrator Console page for Vivédex.

Provides platform metrics, user directory, observation moderation workflows, and audit trail inspection.
Enforces strict server-side role checks on all operations.
"""

from __future__ import annotations

import streamlit as st

from src.admin_service import AdminService
from src.auth import AuthenticatedUser, AuthorizationError
from src.database import Database
from src.demo_data import load_demo_dataset
from src.ui.common import inject_custom_styles, render_security_notice

MODERATION_DISCLAIMER = (
    "IMPORTANT: 'ACCEPTED_FOR_CATALOG' indicates that the submission passed platform moderation. "
    "It DOES NOT mean that a taxonomic expert has confirmed the identification. "
    "Do not represent administrative approval as scientific verification."
)


def render_admin_page(db: Database, admin_service: AdminService) -> None:
    """Render the administrator control panel view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Strict server-side access control
    if current_user is None or not current_user.is_admin:
        st.error("⛔ **Access Denied:** Administrator privileges are required to access this console.")
        return

    st.markdown('<div class="main-header">🛡️ Administrator Console</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Platform management, user oversight, and observation moderation. Logged in as: <strong>{current_user.display_name}</strong></div>',
        unsafe_allow_html=True,
    )

    tab_metrics, tab_users, tab_mod, tab_audit, tab_demo = st.tabs(
        [
            "📊 Platform Metrics",
            "👥 User Management",
            "⚖️ Moderation Queue",
            "📜 Audit Logs",
            "📦 Demo Data",
        ]
    )

    # TAB 1: Metrics
    with tab_metrics:
        metrics = admin_service.get_dashboard_metrics(current_user)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Users", metrics.total_users)
            st.metric("Total Observations", metrics.total_observations)
        with c2:
            st.metric("Distinct Taxa", metrics.distinct_taxa_count)
            st.metric("Pending Moderation", metrics.pending_submissions)
        with c3:
            st.metric("Accepted for Catalog", metrics.accepted_submissions)
            st.metric("Audit Trail Events", metrics.recent_activity_count)

        st.markdown("---")
        st.subheader("🎖️ Badge Distribution")
        badge_data = [
            {"Badge Name": k, "Awarded Count": v}
            for k, v in metrics.badge_distribution.items()
        ]
        st.dataframe(badge_data, width=600)

    # TAB 2: User Management
    with tab_users:
        st.subheader("Registered Platform Users")
        users = admin_service.list_users(current_user)

        user_rows = [
            {
                "User ID": u.user_id,
                "Username": u.username,
                "Display Name": u.display_name,
                "Vivédex ID": u.vivedex_id,
                "Role": u.role.upper(),
                "Active": "Yes" if u.is_active else "No",
                "Observations": u.observation_count,
                "Joined": u.created_at[:10],
            }
            for u in users
        ]
        st.dataframe(user_rows, width="stretch")

    # TAB 3: Moderation Queue
    with tab_mod:
        st.subheader("Observation Moderation Queue")
        st.info(f"ℹ️ {MODERATION_DISCLAIMER}")

        mod_filter = st.selectbox(
            "Filter Moderation Status:",
            ["PENDING", "ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED", "ALL"],
            key="admin_mod_filter",
        )

        queue = admin_service.get_moderation_queue(current_user, mod_filter)
        st.write(f"Showing **{len(queue)}** observations")

        for obs in queue:
            prov_tag = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
            with st.expander(f"{prov_tag}{obs.candidate_scientific_name} ({obs.observation_id}) — Status: {obs.moderation_status}"):
                c_o1, c_o2 = st.columns(2)
                with c_o1:
                    st.write(f"**Observation ID:** `{obs.observation_id}`")
                    st.write(f"**Candidate Taxon:** *{obs.candidate_scientific_name}*")
                    st.write(f"**Owner User ID:** `{obs.owner_id}`")
                    st.write(f"**Coarse Location:** {obs.coarse_location or 'Unspecified'}")
                with c_o2:
                    st.write(f"**Recorded:** {obs.observation_timestamp}")
                    st.write(f"**Current Status:** <span class='status-pill'>{obs.moderation_status}</span>", unsafe_allow_html=True)
                    st.write(f"**Provenance:** `{obs.provenance}`")

                if obs.field_notes:
                    st.info(f"**Field Notes:** {obs.field_notes}")

                st.markdown("---")
                with st.form(f"mod_form_{obs.observation_id}"):
                    new_decision = st.selectbox(
                        "Moderation Decision:",
                        ["ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED", "PENDING"],
                        index=0 if obs.moderation_status == "PENDING" else 1,
                        key=f"dec_{obs.observation_id}",
                    )
                    mod_note = st.text_input(
                        "Moderator Review Note:",
                        placeholder="e.g. Morphological features align with GBIF description.",
                        key=f"note_{obs.observation_id}",
                    )
                    submit_mod = st.form_submit_button("Record Decision", type="primary")

                    if submit_mod:
                        admin_service.moderate_observation(
                            admin_user=current_user,
                            observation_id=obs.observation_id,
                            new_status=new_decision,
                            moderation_note=mod_note,
                        )
                        st.success(f"Status updated to {new_decision}! Audit log recorded.")
                        st.rerun()

    # TAB 4: Audit Logs
    with tab_audit:
        st.subheader("System Audit Log Trail")
        logs = admin_service.get_audit_logs(current_user, limit=50)

        log_data = [
            {
                "ID": l.id,
                "Timestamp": l.timestamp[:19],
                "Username": l.username or "System",
                "Action": l.action,
                "Entity Type": l.entity_type,
                "Entity ID": l.entity_id or "",
                "Details": l.details or "",
            }
            for l in logs
        ]
        st.dataframe(log_data, width="stretch")

    # TAB 5: Demo Data
    with tab_demo:
        st.subheader("Controlled Demo Dataset Management")
        st.markdown(
            """
            Load curated sample records labeled with **`DEMO DATA`** provenance.
            Enables testing multi-species collections, diverse taxonomy hierarchies,
            and moderation queues without manual image captures.
            """
        )
        if st.button("📦 Load Curated Demo Dataset", type="primary"):
            res = load_demo_dataset(db)
            st.success(f"Demonstration records successfully created with {res['provenance']} provenance tag!")
            st.rerun()
