"""Business Unit: scripts | Status: current.

Octarine Capital Dashboard Styles.

This module provides:
- Light theme color constants
- CSS injection for custom styling
"""

from __future__ import annotations

from dataclasses import dataclass
import streamlit as st

# ============================================================================
# Theme Color Palettes
# ============================================================================


@dataclass(frozen=True)
class ThemeColors:
    """Color palette for a theme."""

    primary: str  # Octarine turquoise accent
    text_primary: str  # Main text
    text_secondary: str  # Muted text
    background: str  # Main background
    background_card: str  # Card/elevated background
    positive: str  # Profits, BUY, success
    negative: str  # Losses, SELL, errors
    warning: str  # Warnings, alerts
    border: str  # Subtle borders


THEME_COLORS = ThemeColors(
    primary="#7CF5D4",
    text_primary="#111111",
    text_secondary="#555555",
    background="#ffffff",
    background_card="#F8FAFA",
    positive="#10B981",
    negative="#EF4444",
    warning="#F59E0B",
    border="#E5E7EB",
)


def get_colors() -> ThemeColors:
    """Get the color palette."""
    return THEME_COLORS


# ============================================================================
# CSS Generation
# ============================================================================


def _generate_css(colors: ThemeColors) -> str:
    """Generate CSS for the given color palette."""
    return f"""
    <style>
    /* ===== ROOT VARIABLES ===== */
    :root {{
        --octarine-primary: {colors.primary};
        --octarine-text: {colors.text_primary};
        --octarine-text-muted: {colors.text_secondary};
        --octarine-bg: {colors.background};
        --octarine-bg-card: {colors.background_card};
        --octarine-positive: {colors.positive};
        --octarine-negative: {colors.negative};
        --octarine-warning: {colors.warning};
        --octarine-border: {colors.border};
    }}



    /* ===== HERO METRIC CARD ===== */
    .hero-metric {{
        background: linear-gradient(135deg, {colors.background_card} 0%, {colors.background} 100%);
        border-left: 4px solid {colors.primary};
        border-radius: 0 12px 12px 0;
        padding: 1.5rem 2rem;
        margin-bottom: 1rem;
    }}

    .hero-metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {colors.text_primary};
        font-family: Georgia, serif;
        letter-spacing: -0.02em;
    }}

    .hero-metric-label {{
        font-size: 0.875rem;
        color: {colors.text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.25rem;
    }}

    .hero-metric-subtitle {{
        font-size: 0.875rem;
        color: {colors.text_secondary};
        margin-top: 0.25rem;
    }}

    /* ===== METRIC CARD ===== */
    .metric-card {{
        background: {colors.background_card};
        border: 1px solid {colors.border};
        border-radius: 8px;
        padding: 1rem 1.25rem;
        height: 100%;
    }}

    .metric-card-accent {{
        border-left: 3px solid {colors.primary};
        border-radius: 0 8px 8px 0;
    }}

    .metric-value {{
        font-size: 1.5rem;
        font-weight: 600;
        color: {colors.text_primary};
    }}

    .metric-label {{
        font-size: 0.75rem;
        color: {colors.text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }}

    .metric-delta {{
        font-size: 0.875rem;
        font-weight: 500;
    }}

    .metric-delta-positive {{
        color: {colors.positive};
    }}

    .metric-delta-negative {{
        color: {colors.negative};
    }}

    /* ===== SECTION HEADER ===== */
    .section-header {{
        font-family: Georgia, serif;
        font-size: 0.875rem;
        font-weight: 600;
        color: {colors.text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.15em;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {colors.primary};
        margin-bottom: 1rem;
        margin-top: 1.5rem;
    }}

    /* ===== STATUS BADGES ===== */
    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .status-ok {{
        background: {colors.positive}20;
        color: {colors.positive};
    }}

    .status-warning {{
        background: {colors.warning}20;
        color: {colors.warning};
    }}

    .status-critical {{
        background: {colors.negative}20;
        color: {colors.negative};
    }}

    .status-neutral {{
        background: {colors.border};
        color: {colors.text_secondary};
    }}

    /* ===== DATA TABLES ===== */
    .styled-table {{
        width: 100%;
        border-collapse: collapse;
    }}

    .styled-table th {{
        background: {colors.background_card};
        color: {colors.text_secondary};
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 2px solid {colors.border};
    }}

    .styled-table td {{
        padding: 0.75rem 1rem;
        border-bottom: 1px solid {colors.border};
        color: {colors.text_primary};
    }}

    .styled-table tr:hover {{
        background: {colors.background_card};
    }}

    /* ===== PIPELINE STATUS ===== */
    .pipeline-step {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: {colors.background_card};
        border-radius: 8px;
        margin-right: 0.5rem;
    }}

    .pipeline-step-complete {{
        border: 1px solid {colors.positive};
    }}

    .pipeline-step-error {{
        border: 1px solid {colors.negative};
    }}

    .pipeline-step-pending {{
        border: 1px solid {colors.border};
    }}

    .pipeline-arrow {{
        color: {colors.text_secondary};
        margin: 0 0.25rem;
    }}

    /* ===== PROGRESS BAR ===== */
    .progress-container {{
        background: {colors.border};
        border-radius: 9999px;
        height: 8px;
        overflow: hidden;
    }}

    .progress-bar {{
        height: 100%;
        background: {colors.primary};
        border-radius: 9999px;
        transition: width 0.3s ease;
    }}

    .progress-bar-warning {{
        background: {colors.warning};
    }}

    .progress-bar-danger {{
        background: {colors.negative};
    }}

    /* ===== TABS STYLING ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        border-bottom: 1px solid {colors.border};
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 0.75rem 1.5rem;
        font-size: 0.875rem;
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        border-bottom: 2px solid {colors.primary} !important;
    }}

    /* ===== EXPANDER STYLING ===== */
    .stExpander {{
        border: 1px solid {colors.border};
        border-radius: 8px;
        overflow: hidden;
    }}

    .stExpander [data-testid="stExpanderToggleIcon"] {{
        color: {colors.primary};
    }}

    /* ===== FILTER BAR ===== */
    .filter-bar {{
        background: {colors.background_card};
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
        align-items: end;
    }}

    /* ===== ALERT BOX ===== */
    .alert-box {{
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}

    .alert-warning {{
        background: {colors.warning}15;
        border-left: 4px solid {colors.warning};
    }}

    .alert-error {{
        background: {colors.negative}15;
        border-left: 4px solid {colors.negative};
    }}

    .alert-success {{
        background: {colors.positive}15;
        border-left: 4px solid {colors.positive};
    }}

    .alert-info {{
        background: {colors.primary}15;
        border-left: 4px solid {colors.primary};
    }}

    /* ===== SIDEBAR IMPROVEMENTS ===== */
    [data-testid="stSidebar"] hr {{
        border-color: {colors.border};
        margin: 1rem 0;
    }}

    /* Sidebar navigation links - style buttons as links */
    .nav-link button {{
        background: transparent !important;
        border: none !important;
        color: {colors.text_primary} !important;
        text-align: left !important;
        padding: 0.4rem 0 !important;
        width: 100% !important;
        font-size: 0.95rem !important;
        cursor: pointer !important;
        box-shadow: none !important;
    }}

    .nav-link button:hover {{
        color: {colors.primary} !important;
        background: transparent !important;
    }}

    .nav-link-active button {{
        background: transparent !important;
        border: none !important;
        color: {colors.primary} !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 0.4rem 0 !important;
        width: 100% !important;
        font-size: 0.95rem !important;
        box-shadow: none !important;
    }}

    /* Navigation items */
    [data-testid="stSidebar"] .stSelectbox {{
        margin-top: 0.5rem;
    }}

    /* ===== GENERAL POLISH ===== */
    .stDivider {{
        border-color: {colors.border} !important;
    }}

    /* Remove default Streamlit metric styling issues */
    [data-testid="stMetricDelta"] svg {{
        display: none;
    }}

    /* Better link colors */
    a {{
        color: {colors.primary};
    }}

    a:hover {{
        color: {colors.primary};
        opacity: 0.8;
    }}
    </style>
    """


def inject_styles() -> None:
    """Inject custom CSS styles based on current theme.

    Call this at the top of each page's show() function.
    """
    colors = get_colors()
    st.markdown(_generate_css(colors), unsafe_allow_html=True)


# ============================================================================
# Style Helper Functions
# ============================================================================


def positive_negative_color(value: float) -> str:
    """Return color based on positive/negative value."""
    colors = get_colors()
    if value > 0:
        return colors.positive
    elif value < 0:
        return colors.negative
    return colors.text_secondary


def status_color(status: str) -> str:
    """Return color for status string."""
    colors = get_colors()
    status_lower = status.lower()
    if status_lower in ("ok", "success", "complete", "completed", "active"):
        return colors.positive
    elif status_lower in ("warning", "due", "pending"):
        return colors.warning
    elif status_lower in ("error", "critical", "failed", "overdue"):
        return colors.negative
    return colors.text_secondary


def format_currency(value: float, include_sign: bool = False) -> str:
    """Format a value as currency."""
    if include_sign:
        return f"${value:+,.2f}"
    return f"${value:,.2f}"


def format_percent(value: float, include_sign: bool = False) -> str:
    """Format a value as percentage."""
    if include_sign:
        return f"{value:+.2f}%"
    return f"{value:.2f}%"
