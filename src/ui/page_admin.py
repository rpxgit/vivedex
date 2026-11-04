"""Administrator Console view: Platform oversight, user directory, moderation, and audit logs.

Strictly guarded by server-side role authorization checks.
"""

from __future__ import annotations

import streamlit as st

from src.admin_service import AdminService
from src.auth import AuthenticatedUser
from src.database import Database
from src.demo_data import load_demo_dataset
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import render_hero_banner

MODERATION_SAFEGUARD = (
    "MANDATORY SCIENTIFIC SAFEGUARD: 'ACCEPTED_FOR_CATALOG' signifies that the observation meets "
    "platform submission guidelines and morphological plausibility. It DOES NOT signify verified "
    "taxonomic confirmation by an authorized botanical or zoological authority."
)


def render_admin_page(db: Database, admin_service: AdminService) -> None:
    """Render the reconstructed administrator control panel."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Strict server-side access check
    if current_user is None or not current_user.is_admin:
        st.error("⛔ **Access Denied:** Administrator credentials are required to view this console.")
        return

    # Banner
    render_hero_banner(
        title="🛡️ Administrator Oversight Console",
        subtitle=f"Platform governance, observation moderation, user directory, and security audit log inspection. Active Admin: @{current_user.username}",
    )

    tab_overview, tab_mod, tab_users, tab_audit, tab_demo = st.tabs(
        [
            "📊 Platform Overview",
            "⚖️ Observation Moderation",
            "👥 User Directory",
            "📜 Audit History",
            "📦 Demo Dataset Management",
        ]
    )

    # TAB 1: Platform Overview & Metrics
    with tab_overview:
        metrics = admin_service.get_dashboard_metrics(current_user)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{metrics.total_users}</div>
                    <div class="metric-label">Registered Naturalists</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{metrics.total_observations}</div>
                    <div class="metric-label">Total Field Sightings</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{metrics.distinct_taxa_count}</div>
                    <div class="metric-label">Distinct Known Taxa</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val" style="color: #A66B48;">{metrics.pending_submissions}</div>
                    <div class="metric-label">Submissions Pending Review</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val" style="color: #137333;">{metrics.accepted_submissions}</div>
                    <div class="metric-label">Catalog Accepted Submissions</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{metrics.recent_activity_count}</div>
                    <div class="metric-label">Logged Audit Events</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.subheader("🎖️ Milestone Badge Distribution")
        badge_rows = [
            {"Milestone Title": name, "Recipients": count}
            for name, count in metrics.badge_distribution.items()
        ]
        st.dataframe(badge_rows, width=640)

    # TAB 2: Observation Moderation Queue
    with tab_mod:
        st.subheader("⚖️ Observation Review & Moderation Queue")
        st.info(f"ℹ️ {MODERATION_SAFEGUARD}")

        mod_status = st.selectbox(
            "Filter Moderation Queue:",
            ["PENDING", "ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED", "ALL"],
            key="admin_mod_filter_select",
        )

        queue = admin_service.get_moderation_queue(current_user, mod_status)
        st.write(f"Displaying **{len(queue)}** observations")

        for obs in queue:
            tag = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
            with st.expander(f"{tag}{obs.candidate_scientific_name} ({obs.observation_id}) &bull; Current State: {obs.moderation_status}"):
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    st.write(f"**Observation ID:** `{obs.observation_id}`")
                    st.write(f"**Candidate Binomial:** *{obs.candidate_scientific_name}*")
                    st.write(f"**Naturalist Owner ID:** `{obs.owner_id}`")
                    st.write(f"**Coarse Locality:** {obs.coarse_location or 'Unspecified'}")
                with c_m2:
                    st.write(f"**Observation Date:** {obs.observation_timestamp}")
                    st.write(f"**Provenance:** `{obs.provenance}`")
                    st.write(f"**Status:** `{obs.moderation_status}`")

                if obs.field_notes:
                    st.markdown(f"**Field Notes:** {obs.field_notes}")

                st.markdown("---")
                with st.form(f"mod_decision_form_{obs.observation_id}"):
                    decision = st.selectbox(
                        "Moderation Decision:",
                        ["ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED", "PENDING"],
                        index=0 if obs.moderation_status == "PENDING" else 1,
                        key=f"dec_select_{obs.observation_id}",
                    )
                    review_note = st.text_input(
                        "Moderator Review Rationale:",
                        placeholder="e.g. Diagnostic plumage markings corroborated by visual evidence.",
                        key=f"mod_note_{obs.observation_id}",
                    )
                    submit_decision = st.form_submit_button("Record Moderation Decision", type="primary")

                    if submit_decision:
                        admin_service.moderate_observation(
                            admin_user=current_user,
                            observation_id=obs.observation_id,
                            new_status=decision,
                            moderation_note=review_note,
                        )
                        st.success(f"Observation updated to {decision}! Action recorded in security audit log.")
                        st.rerun()

    # TAB 3: User Management Directory
    with tab_users:
        st.subheader("👥 Registered Naturalist Directory")
        all_users = admin_service.list_users(current_user)

        user_records = [
            {
                "User ID": u.user_id,
                "Username": u.username,
                "Display Name": u.display_name,
                "Vivédex ID": u.vivedex_id,
                "System Role": u.role.upper(),
                "Account Active": "Yes" if u.is_active else "No",
                "Sightings Logged": u.observation_count,
                "Joined Date": u.created_at[:10],
            }
            for u in all_users
        ]
        st.dataframe(user_records, width="stretch")

    # TAB 4: Audit History
    with tab_audit:
        st.subheader("📜 Security & Workflow Audit Trail")
        logs = admin_service.get_audit_logs(current_user, limit=75)

        log_rows = [
            {
                "Log ID": l.id,
                "Timestamp": l.timestamp[:19],
                "Actor": l.username or "System",
                "Action Code": l.action,
                "Entity Target": l.entity_type,
                "Entity Key": l.entity_id or "",
                "Event Context": l.details or "",
            }
            for l in logs
        ]
        st.dataframe(log_rows, width="stretch")

    # TAB 5: Demo Data Management
    with tab_demo:
        st.subheader("📦 Controlled Demonstration Dataset Management")
        st.markdown(
            """
            Seed or re-load curated demonstration records with explicit **`DEMO DATA`** provenance tags.
            Enables testing multi-species catalogs, taxonomic classifications,
            and moderation workflows without manual image uploads.
            """
        )
        if st.button("📦 Load Controlled Demonstration Dataset", type="primary", key="admin_load_demo_btn"):
            res = load_demo_dataset(db)
            st.success(f"Demonstration records loaded successfully with {res['provenance']} provenance tag!")
            st.rerun()
