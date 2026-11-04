"""Central design tokens, theme stylesheets, and component builders for Vivédex.

Provides a museum-grade botanical aesthetic inspired by botanical atlases,
Restor.eco ecological context, and Pokédex organism discovery.
"""

from __future__ import annotations

import streamlit as st

# Color Palette Tokens
COLOR_TOKENS = {
    "forest": "#183B32",
    "deep_forest": "#102A25",
    "moss": "#718568",
    "sage": "#A9B99A",
    "ivory": "#F5F2E9",
    "paper": "#FCFAF4",
    "border": "#E3DDD0",
    "earth": "#A66B48",
    "gold": "#C6A66B",
    "ink": "#252C27",
    "muted": "#777E73",
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


def inject_theme_styles() -> None:
    """Inject Google Fonts, custom CSS design tokens, and botanical layout rules."""
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
            --border: #E3DDD0;
            --earth: #A66B48;
            --gold: #C6A66B;
            --ink: #252C27;
            --muted: #777E73;
        }

        /* Typography */
        h1, h2 {
            font-family: 'Cinzel', 'Playfair Display', Georgia, serif !important;
            color: var(--deep-forest) !important;
            letter-spacing: -0.01em;
        }

        h3, h4 {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: var(--forest) !important;
        }

        body, p, span, div, label {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            color: var(--ink);
        }

        /* Hero Header */
        .hero-banner {
            background: linear-gradient(135deg, #102A25 0%, #183B32 70%, #244C42 100%);
            border-radius: 12px;
            padding: 2.2rem 2.5rem;
            color: #FCFAF4;
            margin-bottom: 1.8rem;
            border: 1px solid #2d5a50;
            box-shadow: 0 4px 18px rgba(16, 42, 37, 0.12);
        }

        .hero-banner h1 {
            color: #FCFAF4 !important;
            font-size: 2.6rem !important;
            margin: 0 0 0.4rem 0 !important;
            font-weight: 700;
        }

        .hero-banner p {
            color: #d1ded6;
            font-size: 1.1rem;
            margin: 0;
            font-weight: 400;
            max-width: 820px;
        }

        /* Security Prototype Banner */
        .security-badge {
            background-color: #fbf7ee;
            color: #8c6827;
            padding: 0.45rem 0.9rem;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            border: 1px solid #fae8c3;
            border-left: 4px solid #C6A66B;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Specimen Cards */
        .specimen-card {
            background: var(--paper);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.4rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(37, 44, 39, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .specimen-card:hover {
            box-shadow: 0 6px 16px rgba(24, 59, 50, 0.08);
            border-color: #c9c0af;
        }

        /* Latin Binomial Styling */
        .latin-binomial {
            font-family: 'Playfair Display', Georgia, serif;
            font-style: italic;
            font-weight: 600;
            color: var(--forest);
        }

        /* Badges & Pills */
        .rank-pill {
            display: inline-block;
            background-color: #e5ede0;
            color: #183B32;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid #c8d8be;
        }

        .status-pill-accepted {
            display: inline-block;
            background-color: #e6f4ea;
            color: #137333;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 14px;
            border: 1px solid #ceead6;
        }

        .status-pill-pending {
            display: inline-block;
            background-color: #fef7e0;
            color: #b06000;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 14px;
            border: 1px solid #feefc3;
        }

        .status-pill-review {
            display: inline-block;
            background-color: #fce8e6;
            color: #c5221f;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 14px;
            border: 1px solid #fad2cf;
        }

        .dex-collected-tag {
            display: inline-block;
            background-color: #fdf5e6;
            color: #94691e;
            font-size: 0.74rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 14px;
            border: 1px solid #edd39f;
        }

        .provenance-tag {
            font-size: 0.74rem;
            color: var(--muted);
            font-family: 'JetBrains Mono', ui-monospace, monospace;
            line-height: 1.4;
        }

        /* Naturalist Metric Box */
        .naturalist-metric {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.1rem;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.03);
        }

        .naturalist-metric .metric-val {
            font-family: 'Cinzel', serif;
            font-size: 1.9rem;
            font-weight: 700;
            color: var(--forest);
            line-height: 1.1;
        }

        .naturalist-metric .metric-label {
            font-size: 0.8rem;
            color: var(--muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 4px;
        }

        /* Quest Card */
        .quest-box {
            background: #ffffff;
            border: 1px solid #ded6c5;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
            border-left: 4px solid var(--gold);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_banner(title: str, subtitle: str) -> None:
    """Render a museum-grade editorial hero banner."""
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{title}</h1>
            <p>{subtitle}</p>
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
