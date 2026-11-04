"""Vivédex — Multi-Page Biodiversity Platform Entry Point.

Combines organism identification with personal collections, gamified naturalist milestones,
persistent field journals, researcher credentials, knowledge graph exploration, and admin oversight.
"""

from __future__ import annotations

import os
from pathlib import Path
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.achievements import AchievementService
from src.admin_service import AdminService
from src.auth import AuthService
from src.backend import VivedexBackend
from src.collection_service import CollectionService
from src.database import DEFAULT_DB_PATH, Database
from src.knowledge_graph import KnowledgeGraphService
from src.ui.common import inject_custom_styles, render_auth_controls
from src.ui.page_achievements import render_achievements_page
from src.ui.page_admin import render_admin_page
from src.ui.page_collection import render_collection_page
from src.ui.page_explore import render_explore_page
from src.ui.page_home import render_home_page
from src.ui.page_identify import render_identify_page
from src.ui.page_journal import render_journal_page
from src.ui.page_knowledge import render_knowledge_page
from src.ui.page_profile import render_profile_page

# Configure Streamlit page settings
st.set_page_config(
    page_title="Vivédex — Biodiversity Discovery & Collection Platform",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Database singleton in session state
if "db" not in st.session_state:
    db = Database(DEFAULT_DB_PATH)
    db.initialize_schema()
    st.session_state["db"] = db
else:
    db = st.session_state["db"]

# Initialize domain services
if "auth_service" not in st.session_state:
    st.session_state["auth_service"] = AuthService(db)
if "collection_service" not in st.session_state:
    st.session_state["collection_service"] = CollectionService(db)
if "achievement_service" not in st.session_state:
    st.session_state["achievement_service"] = AchievementService(db)
if "admin_service" not in st.session_state:
    st.session_state["admin_service"] = AdminService(db)
if "kg_service" not in st.session_state:
    st.session_state["kg_service"] = KnowledgeGraphService(db)
if "backend" not in st.session_state:
    st.session_state["backend"] = VivedexBackend()

auth_service: AuthService = st.session_state["auth_service"]
collection_service: CollectionService = st.session_state["collection_service"]
achievement_service: AchievementService = st.session_state["achievement_service"]
admin_service: AdminService = st.session_state["admin_service"]
kg_service: KnowledgeGraphService = st.session_state["kg_service"]
backend: VivedexBackend = st.session_state["backend"]

# Apply styling and render authentication sidebar
inject_custom_styles()
render_auth_controls(auth_service, db)

current_user = st.session_state.get("current_user")

# Define distinct named page views to ensure unique URL paths
def view_home() -> None:
    render_home_page(db, collection_service, achievement_service)

def view_explore() -> None:
    render_explore_page(collection_service)

def view_identify() -> None:
    render_identify_page(backend, collection_service)

def view_collection() -> None:
    render_collection_page(collection_service)

def view_journal() -> None:
    render_journal_page(collection_service)

def view_achievements() -> None:
    render_achievements_page(achievement_service)

def view_profile() -> None:
    render_profile_page(collection_service, achievement_service)

def view_knowledge() -> None:
    render_knowledge_page(db, kg_service)

def view_admin() -> None:
    render_admin_page(db, admin_service)

p_home = st.Page(view_home, title="Home", icon="🏠", url_path="home", default=True)
p_explore = st.Page(view_explore, title="Explore Dex", icon="🔍", url_path="explore")
p_identify = st.Page(view_identify, title="Identify", icon="🌿", url_path="identify")
p_collection = st.Page(view_collection, title="My Collection", icon="📚", url_path="collection")
p_journal = st.Page(view_journal, title="Field Journal", icon="📓", url_path="journal")
p_achievements = st.Page(view_achievements, title="Achievements", icon="🏆", url_path="achievements")
p_profile = st.Page(view_profile, title="Researcher Profile", icon="👤", url_path="profile")
p_knowledge = st.Page(view_knowledge, title="Knowledge Explorer", icon="🕸️", url_path="knowledge")

pages = [
    p_home,
    p_explore,
    p_identify,
    p_collection,
    p_journal,
    p_achievements,
    p_profile,
    p_knowledge,
]

# Only include Admin Console if the logged in user has administrator role
if current_user is not None and current_user.is_admin:
    p_admin = st.Page(view_admin, title="Admin Console", icon="🛡️", url_path="admin")
    pages.append(p_admin)

nav = st.navigation(pages)
nav.run()

