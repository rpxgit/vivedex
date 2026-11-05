"""Central design tokens, theme stylesheets, and component builders for Vivédex.

Provides a museum-grade botanical editorial aesthetic inspired by botanical atlases,
Restor.eco ecological context, Pokédex organism discovery, Habitica progression,
and ORCID persistent researcher attribution.
"""

from __future__ import annotations

import html
from urllib.parse import urlparse
import streamlit as st

# Authoritative color palette tokens matching RUN 011B design specification
COLOR_TOKENS = {
    "forest": "#183B32",       # Deep evergreen - primary brand (8.6:1 on ivory)
    "deep_forest": "#102A25",  # Contrast dark forest (12.1:1 on ivory)
    "moss": "#718568",         # Botanical accent
    "sage": "#A9B99A",         # Soft botanical sage
    "ivory": "#F5F2E9",        # Canvas background
    "paper": "#FCFAF4",        # Container/card fill
    "earth": "#A66B48",        # Warm terracotta accent
    "gold": "#C6A66B",         # Milestone gold accent
    "ink": "#252C27",          # Primary reading ink (10.9:1 on ivory)
    "muted": "#59645D",        # Secondary reading text (5.2:1 on ivory)
    "white": "#FFFFFF",        # High-contrast white
    "border": "#D8D1C2",       # Card container border
    "border_strong": "#B8AE9C",# Secondary divider
}

NATURALIST_RANKS = {
    1: "Observer",
    2: "Explorer",
    3: "Naturalist",
    4: "Field Researcher",
    5: "Specialist",
    6: "Biodiversity Steward",
}


def get_naturalist_rank(level: int) -> str:
    """Return an immersive naturalist rank title for a given player level."""
    if level in NATURALIST_RANKS:
        return NATURALIST_RANKS[level]
    return NATURALIST_RANKS[6] if level >= 6 else "Observer"


def escape_text(val: object | None) -> str:
    """Safely escape arbitrary values for HTML interpolation (SEC-01)."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def safe_url(url: str | None) -> str:
    """Validate and escape URL to prevent javascript: or data: XSS injections (SEC-01, SEC-08)."""
    if not url:
        return ""
    stripped = url.strip()
    parsed = urlparse(stripped)
    if parsed.scheme.lower() in ("http", "https"):
        return html.escape(stripped, quote=True)
    return ""


def inject_theme_styles() -> None:
    """Inject typography, custom CSS design tokens, and botanical layout rules.

    Eliminates wildcard font overrides to preserve Streamlit component rendering,
    enforces strict contrast ratios, styles sidebar navigation, and refines the file uploader.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Playfair+Display:ital,wght@0,500;0,700;1,500;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        :root {
            --forest: #183B32;
            --deep-forest: #102A25;
            --moss: #718568;
            --sage: #A9B99A;
            --ivory: #F5F2E9;
            --paper: #FCFAF4;
            --earth: #A66B48;
            --gold: #C6A66B;
            --ink: #252C27;
            --muted: #59645D;
            --white: #FFFFFF;
            --border: #D8D1C2;
            --border-strong: #B8AE9C;
        }

        /* App container & base canvas */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: var(--ivory) !important;
            color: var(--ink) !important;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }

        /* Main content constraint */
        .main .block-container {
            max-width: 1200px;
            padding-top: 1.8rem;
            padding-bottom: 3.5rem;
        }

        /* Headings: Playfair Display for editorial elegance */
        h1, h2 {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: var(--deep-forest);
            font-weight: 700 !important;
            letter-spacing: -0.01em;
        }

        h3, h4 {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: var(--forest);
            font-weight: 600 !important;
        }

        /* Hero Banner - Explicit High-Contrast Styling */
        .hero-banner {
            background: linear-gradient(135deg, #102A25 0%, #183B32 75%, #244C42 100%) !important;
            border-radius: 12px !important;
            padding: 2.2rem 2.6rem !important;
            margin-bottom: 1.8rem !important;
            border: 1px solid #2B574C !important;
            box-shadow: 0 4px 18px rgba(16, 42, 37, 0.14) !important;
            color: #FFFFFF !important;
        }

        .hero-banner h1,
        .hero-banner h2,
        .hero-banner [data-testid="stMarkdownContainer"] h1,
        .hero-banner [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] .hero-banner h1,
        [data-testid="stMarkdownContainer"] .hero-banner h2 {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: #FFFFFF !important;
            font-size: 2.3rem !important;
            margin: 0 0 0.5rem 0 !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em !important;
            line-height: 1.2 !important;
        }

        .hero-banner p,
        .hero-banner [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] .hero-banner p {
            color: #F5F2E9 !important;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
            font-size: 1.05rem !important;
            margin: 0 !important;
            font-weight: 400 !important;
            line-height: 1.5 !important;
            max-width: 860px !important;
            opacity: 0.95 !important;
        }

        /* High-contrast Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #EDE8DC !important;
            border-right: 1px solid #D6CEBE !important;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
            color: var(--ink) !important;
            font-weight: 500 !important;
        }

        [data-testid="stSidebarNav"] span {
            color: var(--forest) !important;
            font-weight: 600 !important;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 6px !important;
            margin-bottom: 2px !important;
            transition: background-color 0.15s ease !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: #DBD4C1 !important;
            border-left: 4px solid var(--forest) !important;
            font-weight: 700 !important;
        }

        [data-testid="stSidebarNav"] a:hover {
            background-color: #E2DBD0 !important;
        }

        /* Custom File Uploader Drag-and-Drop Area */
        [data-testid="stFileUploader"] {
            background: transparent !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background-color: var(--paper) !important;
            border: 2px dashed var(--sage) !important;
            border-radius: 12px !important;
            padding: 2rem 1.6rem !important;
            transition: border-color 0.2s ease, background-color 0.2s ease !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--forest) !important;
            background-color: #F8F5EC !important;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] {
            color: var(--ink) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: var(--muted) !important;
        }

        [data-testid="stFileUploaderDropzone"] button {
            background-color: var(--forest) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--deep-forest) !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            padding: 0.45rem 1.2rem !important;
            transition: background-color 0.15s ease !important;
        }

        [data-testid="stFileUploaderDropzone"] button:hover {
            background-color: var(--deep-forest) !important;
        }

        /* Primary Action Buttons */
        .stButton > button {
            background-color: var(--forest) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--deep-forest) !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            transition: background-color 0.15s ease, transform 0.1s ease !important;
        }

        .stButton > button:hover {
            background-color: var(--deep-forest) !important;
            border-color: #081714 !important;
            transform: translateY(-1px);
        }

        /* Form Inputs */
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox > div > div {
            background-color: #FFFFFF !important;
            color: var(--ink) !important;
            border-color: var(--border) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        .stTextInput > div > div > input::placeholder,
        .stTextArea textarea::placeholder {
            color: var(--muted) !important;
            opacity: 0.8;
        }

        /* Specimen & Botanical Cards */
        .specimen-card {
            background: var(--paper) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px;
            padding: 1.4rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(37, 44, 39, 0.04);
            transition: box-shadow 0.15s ease, border-color 0.15s ease;
        }

        .specimen-card:hover {
            box-shadow: 0 6px 16px rgba(24, 59, 50, 0.09);
            border-color: var(--border-strong) !important;
        }

        /* Latin Binomial Styling */
        .latin-binomial {
            font-family: 'Playfair Display', Georgia, serif;
            font-style: italic;
            font-weight: 600;
            color: var(--forest);
        }

        /* Prototype Security Notice */
        .security-badge {
            background-color: #FDF9EE;
            color: #7A5313;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            border: 1px solid #F2DC9E;
            border-left: 4px solid var(--gold);
            margin-bottom: 1.3rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Naturalist Privacy Safeguard */
        .privacy-badge {
            background-color: #F5F8F4;
            color: var(--deep-forest);
            padding: 0.6rem 1rem;
            border-radius: 6px;
            font-size: 0.82rem;
            line-height: 1.5;
            border: 1px solid #C4D6BD;
            border-left: 4px solid var(--moss);
            margin-bottom: 1.2rem;
        }

        /* Botanical Metrics Grid */
        .naturalist-metric {
            background: #FFFFFF !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 1.2rem 1rem;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
        }

        .naturalist-metric .metric-val {
            font-family: 'Cinzel', serif !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: var(--forest) !important;
            line-height: 1.1;
        }

        .naturalist-metric .metric-label {
            font-size: 0.82rem !important;
            color: var(--muted) !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 6px;
        }

        /* Botanical Badges & Tags */
        .rank-pill {
            display: inline-block;
            background-color: #E2ECDD;
            color: var(--forest);
            font-size: 0.74rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid #C4D6BD;
        }

        .status-pill-accepted {
            display: inline-block;
            background-color: #E6F4EA;
            color: #137333;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid #CEEAD6;
        }

        .status-pill-pending {
            display: inline-block;
            background-color: #FEF7E0;
            color: #8C5400;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid #FEEFC3;
        }

        .status-pill-review {
            display: inline-block;
            background-color: #FCE8E6;
            color: #B31D19;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid #FAD2CF;
        }

        /* Quest Card */
        .quest-box {
            background: #FFFFFF !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
            border-left: 5px solid var(--gold) !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.03);
        }

        .quest-habit {
            border-left-color: var(--forest) !important;
        }

        .quest-recurring {
            border-left-color: var(--earth) !important;
        }

        .quest-milestone {
            border-left-color: var(--gold) !important;
        }

        /* Provenance State Badges */
        .prov-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .prov-self {
            background-color: #F0EDE4;
            color: #5A544A;
            border: 1px solid #D6D0C2;
        }
        .prov-linked {
            background-color: #E6F1F8;
            color: #17537D;
            border: 1px solid #C8DEF0;
        }
        .prov-reviewed {
            background-color: #E8F5E9;
            color: #1E6B24;
            border: 1px solid #C4E4C7;
        }
        .prov-verified {
            background-color: #EDE7F6;
            color: #4A148C;
            border: 1px solid #D1C4E9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_banner(title: str, subtitle: str) -> None:
    """Render a museum-grade editorial hero banner with guaranteed contrast."""
    escaped_title = escape_text(title)
    escaped_subtitle = escape_text(subtitle)
    st.markdown(
        f"""
        <div class="hero-banner" style="background: linear-gradient(135deg, #102A25 0%, #183B32 75%, #244C42 100%) !important; color: #FFFFFF !important; border-radius: 12px; padding: 2.2rem 2.6rem; margin-bottom: 1.8rem; border: 1px solid #2B574C; box-shadow: 0 4px 18px rgba(16, 42, 37, 0.14);">
            <h1 style="color: #FFFFFF !important; font-family: 'Playfair Display', Georgia, serif !important; font-size: 2.3rem !important; margin: 0 0 0.5rem 0 !important; font-weight: 700 !important; letter-spacing: -0.01em !important; line-height: 1.2 !important;">{escaped_title}</h1>
            <p style="color: #F5F2E9 !important; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important; font-size: 1.05rem !important; margin: 0 !important; font-weight: 400 !important; line-height: 1.5 !important; max-width: 860px !important; opacity: 0.95 !important;">{escaped_subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_security_badge() -> None:
    """Render the standard local prototype warning badge."""
    st.markdown(
        """
        <div class="security-badge">
            <span>⚠️</span>
            <span><strong>LOCAL PROTOTYPE</strong> — AUTHENTICATION IS NOT PRODUCTION-HARDENED.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_privacy_notice() -> None:
    """Render the privacy safeguard badge."""
    st.markdown(
        """
        <div class="privacy-badge">
            🔒 <strong>Naturalist Privacy Safeguard:</strong> Specimen photographs are processed strictly in volatile memory.
            EXIF metadata, device serials, and precise GPS coordinates are stripped before analysis. Images are never written to permanent storage.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_provenance_badge(state: str) -> str:
    """Generate HTML pill for an output or observation provenance state."""
    safe_state = escape_text(state)
    cls_map = {
        "SELF_REPORTED": "prov-self",
        "SOURCE_LINKED": "prov-linked",
        "PLATFORM_REVIEWED": "prov-reviewed",
        "EXTERNALLY_VERIFIED": "prov-verified",
    }
    css_class = cls_map.get(state, "prov-self")
    label_map = {
        "SELF_REPORTED": "Self-Reported",
        "SOURCE_LINKED": "Source-Linked",
        "PLATFORM_REVIEWED": "Platform-Reviewed",
        "EXTERNALLY_VERIFIED": "Externally Verified",
    }
    label = label_map.get(state, safe_state)
    return f'<span class="prov-badge {css_class}">{escape_text(label)}</span>'
