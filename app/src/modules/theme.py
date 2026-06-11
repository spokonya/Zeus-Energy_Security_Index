"""Global Zeus typography, color palette, and theme overrides."""

import streamlit as st

_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700"
    "&family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;0,9..144,800;1,9..144,600"
    "&display=swap"
)

# Streamlit renders chevrons and UI icons via Material Symbols; custom fonts must
# not override those glyphs or ligature names show as overlapping text.
_ICON_FONT_STACK = (
    '"Material Symbols Rounded", "Material Icons", "Material Icons Outlined", '
    '"Material Symbols Outlined", sans-serif'
)

_ZEUS_CSS = """
    :root {
        --zeus-navy: #0C1B2E;
        --zeus-slate: #1E3A52;
        --zeus-amber: #C4841D;
        --zeus-amber-bright: #E8A838;
        --zeus-amber-soft: #F5E6C8;
        --zeus-cream: #F7F5F0;
        --zeus-cream-dark: #EDE9E0;
        --zeus-surface: #FFFFFF;
        --zeus-text: #152535;
        --zeus-text-muted: #5C6B7A;
        --zeus-border: #D8D2C8;
        --zeus-shadow: rgba(12, 27, 46, 0.08);
        --zeus-radius: 12px;
        --zeus-radius-sm: 8px;
    }

    html, body, .stApp {
        font-family: "DM Sans", sans-serif;
        color: var(--zeus-text);
        background-color: var(--zeus-cream);
    }

    /* Subtle warm ambient wash behind main content */
    .stApp {
        background:
            radial-gradient(ellipse 80% 50% at 100% 0%, rgba(232, 168, 56, 0.07), transparent 55%),
            radial-gradient(ellipse 60% 40% at 0% 100%, rgba(30, 58, 82, 0.05), transparent 50%),
            var(--zeus-cream);
    }

    [data-testid="stAppViewContainer"] > section.main {
        background: transparent;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 245, 240, 0.85);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid var(--zeus-border);
    }

    /* ── Typography ─────────────────────────────────────────── */

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        font-family: "Fraunces", Georgia, serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
        color: var(--zeus-navy);
        text-wrap: balance;
    }

    h1, [data-testid="stMarkdownContainer"] h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em;
        padding-bottom: 0.35rem;
        border-bottom: 2px solid var(--zeus-amber-soft);
        margin-bottom: 0.75rem !important;
    }

    p, li, label, input, textarea, select, button, a {
        font-family: "DM Sans", sans-serif;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--zeus-text-muted) !important;
    }

    /* ── Sidebar ────────────────────────────────────────────── */

    [data-testid="stSidebar"] {
        font-family: "DM Sans", sans-serif;
        background: linear-gradient(175deg, var(--zeus-navy) 0%, #132940 55%, #0F2235 100%) !important;
        border-right: 1px solid rgba(232, 168, 56, 0.18);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
        color: #E8ECF0 !important;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        font-size: 0.72rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
        border-radius: var(--zeus-radius-sm);
        margin-bottom: 2px;
        transition: background 0.2s ease, color 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
        background: rgba(232, 168, 56, 0.12) !important;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p,
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span {
        color: #C8D4E0 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p,
    [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover span {
        color: #F5F0E8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(232, 168, 56, 0.2) !important;
        margin: 0.75rem 0 !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #E8A838 !important;
        border: 1px solid rgba(232, 168, 56, 0.45) !important;
        border-radius: var(--zeus-radius-sm) !important;
        font-weight: 600 !important;
        transition: background 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(232, 168, 56, 0.14) !important;
        border-color: var(--zeus-amber-bright) !important;
        color: #F5E6C8 !important;
    }

    /* ── Metrics ────────────────────────────────────────────── */

    [data-testid="stMetric"] {
        background: var(--zeus-surface);
        border: 1px solid var(--zeus-border);
        border-radius: var(--zeus-radius);
        padding: 1rem 1.15rem 0.9rem;
        box-shadow: 0 2px 8px var(--zeus-shadow);
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--zeus-amber-soft);
        box-shadow: 0 4px 14px rgba(12, 27, 46, 0.1);
    }

    [data-testid="stMetricValue"] {
        font-family: "DM Sans", sans-serif !important;
        font-weight: 700 !important;
        font-variant-numeric: tabular-nums;
        color: var(--zeus-navy) !important;
        letter-spacing: -0.02em;
    }

    [data-testid="stMetricLabel"] {
        font-family: "DM Sans", sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.72rem !important;
        color: var(--zeus-text-muted) !important;
    }

    /* Let metric label/value/delta text wrap fully instead of being
       clipped with an ellipsis when it doesn't fit the box width. */
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }

    [data-testid="stMetricLabel"] {
        max-width: 100% !important;
        line-height: 1.25 !important;
    }

    [data-testid="stMetricDelta"] {
        font-variant-numeric: tabular-nums;
        font-weight: 600 !important;
    }

    /* ── Buttons ────────────────────────────────────────────── */

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--zeus-amber) 0%, #A86F15 100%) !important;
        color: #FFFAF0 !important;
        border: none !important;
        border-radius: var(--zeus-radius-sm) !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em;
        box-shadow: 0 2px 6px rgba(196, 132, 29, 0.3);
        transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        filter: brightness(1.06);
        box-shadow: 0 4px 12px rgba(196, 132, 29, 0.35);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"]:active,
    .stButton > button[data-testid="stBaseButton-primary"]:active {
        transform: translateY(0);
    }

    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        border-radius: var(--zeus-radius-sm) !important;
        border-color: var(--zeus-border) !important;
        color: var(--zeus-slate) !important;
        font-weight: 600 !important;
        transition: border-color 0.2s ease, background 0.2s ease;
    }

    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--zeus-amber) !important;
        background: var(--zeus-amber-soft) !important;
    }

    /* ── Inputs & selects ───────────────────────────────────── */

    [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border-radius: var(--zeus-radius-sm) !important;
        border-color: var(--zeus-border) !important;
        background: var(--zeus-surface) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    [data-baseweb="select"]:hover > div,
    [data-testid="stSelectbox"] div[data-baseweb="select"]:hover > div {
        border-color: var(--zeus-amber) !important;
    }

    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        border-radius: var(--zeus-radius-sm) !important;
        border-color: var(--zeus-border) !important;
    }

    /* ── Dividers & expanders ───────────────────────────────── */

    hr, [data-testid="stDivider"] {
        border-color: var(--zeus-border) !important;
        opacity: 0.9;
    }

    [data-testid="stExpander"] {
        background: var(--zeus-surface);
        border: 1px solid var(--zeus-border) !important;
        border-radius: var(--zeus-radius) !important;
        box-shadow: 0 1px 4px var(--zeus-shadow);
    }

    [data-testid="stExpander"] summary {
        font-weight: 600;
        color: var(--zeus-navy);
    }

    /* ── Alerts ─────────────────────────────────────────────── */

    [data-testid="stAlert"] {
        border-radius: var(--zeus-radius-sm) !important;
        border-width: 1px !important;
    }

    /* ── Dataframes & tables ────────────────────────────────── */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--zeus-border);
        border-radius: var(--zeus-radius);
        overflow: hidden;
        box-shadow: 0 1px 4px var(--zeus-shadow);
    }

    /* ── Charts ─────────────────────────────────────────────── */

    [data-testid="stPlotlyChart"] {
        border: 1px solid var(--zeus-border);
        border-radius: var(--zeus-radius);
        background: var(--zeus-surface);
        box-shadow: 0 2px 8px var(--zeus-shadow);
        overflow: visible !important;
        padding: 0 !important;
        box-sizing: border-box;
    }

    [data-testid="stPlotlyChart"] > div,
    [data-testid="stPlotlyChart"] .stPlotlyChart,
    [data-testid="stPlotlyChart"] [data-testid="stElementContainer"] {
        overflow: visible !important;
        max-height: none !important;
    }

    [data-testid="stPlotlyChart"] iframe {
        display: block;
        width: 100% !important;
        border: none;
    }

    /* ── Icons (preserve Material Symbols) ──────────────────── */

    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] span,
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined {
        font-family: ICON_FONT_STACK_PLACEHOLDER !important;
        font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
    }
"""


def zeus_plotly_layout(fig, *, height: int = 400, **kwargs) -> None:
    """Size charts to fit their card without clipping axes or legends."""
    layout = {
        "height": height,
        "autosize": True,
        "margin": {"l": 56, "r": 32, "t": 48, "b": 56},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }
    layout.update(kwargs)
    fig.update_layout(**layout)


def apply_zeus_theme() -> None:
    """Inject Zeus palette, typography, and component styling."""
    css = _ZEUS_CSS.replace("ICON_FONT_STACK_PLACEHOLDER", _ICON_FONT_STACK)
    st.markdown(
        f"""
        <style>
            @import url('{_FONTS_URL}');
            {css}
        </style>
        """,
        unsafe_allow_html=True,
    )
