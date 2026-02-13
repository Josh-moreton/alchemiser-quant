#!/usr/bin/env python3
"""Business Unit: dashboard | Status: current.

Enhanced Streamlit dashboard for The Alchemiser Trading System.

Multi-page dashboard with:
- Portfolio & PnL overview
- Last run analysis (strategies, signals, trades)
- Trade history & attribution
- Per-symbol analytics

Run locally: streamlit run dashboard/app.py
Deploy: Push to GitHub, connect to Streamlit Cloud

Authentication:
- Uses streamlit-authenticator for secure login
- Credentials stored in Streamlit secrets (bcrypt hashed passwords)
- Cookie-based sessions for convenience
"""

from __future__ import annotations

# Suppress noisy structlog output BEFORE any imports
import os

os.environ["ALCHEMISER_LOG_LEVEL"] = "WARNING"

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import _setup_imports  # noqa: F401
import streamlit as st
from components.styles import inject_styles
from dotenv import load_dotenv
from settings import get_active_stage, get_dashboard_settings, set_stage

if TYPE_CHECKING:
    import streamlit_authenticator

# ---------------------------------------------------------------------------
# Bootstrap: configure stdlib logging so dashboard diagnostics appear in the
# Streamlit console (structlog is already silenced via ALCHEMISER_LOG_LEVEL).
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dashboard")

# Load .env file before importing modules that use environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Favicon/PWA icon - read image bytes to work on Streamlit Cloud
favicon_path = Path(__file__).parent.parent / "android-chrome-512x512.png"
if favicon_path.exists():
    from PIL import Image

    favicon = Image.open(favicon_path)
else:
    favicon = None

# Page config (must be first Streamlit call)
st.set_page_config(
    page_title="Octarine Capital - Trading Dashboard",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Page imports (deferred so heavy deps load only when needed)
# ---------------------------------------------------------------------------
def _page_portfolio_overview() -> None:
    from pages import portfolio_overview

    portfolio_overview.show()


def _page_forward_projection() -> None:
    from pages import forward_projection

    forward_projection.show()


def _page_last_run_analysis() -> None:
    from pages import last_run_analysis

    last_run_analysis.show()


def _page_trade_history() -> None:
    from pages import trade_history

    trade_history.show()


def _page_strategy_performance() -> None:
    from pages import strategy_performance

    strategy_performance.show()


def _page_execution_quality() -> None:
    from pages import execution_quality

    execution_quality.show()


def _page_symbol_analytics() -> None:
    from pages import symbol_analytics

    symbol_analytics.show()


def _page_options_hedging() -> None:
    from pages import options_hedging

    options_hedging.show()


def _page_pnl_table() -> None:
    from pages import pnl_table

    pnl_table.show()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def get_authenticator() -> streamlit_authenticator.Authenticate | None:
    """Create authenticator from Streamlit secrets or environment.

    Returns None if authentication is disabled (local dev without secrets).
    """
    try:
        import streamlit_authenticator as stauth
    except ImportError:
        st.warning("streamlit-authenticator not installed. Run: poetry install")
        return None

    # Check environment variable to skip auth (local dev)
    if os.environ.get("SKIP_AUTH", "").lower() in ("true", "1", "yes"):
        return None

    # Check if credentials are configured in secrets
    try:
        if hasattr(st, "secrets") and "credentials" in st.secrets:
            # Production: use Streamlit Cloud secrets
            credentials = st.secrets["credentials"].to_dict()
            cookie_config = st.secrets.get("cookie", {})

            return stauth.Authenticate(
                credentials={"usernames": credentials.get("usernames", {})},
                cookie_name=cookie_config.get("name", "alchemiser_dashboard"),
                cookie_key=cookie_config.get("key", "default_key_change_me"),
                cookie_expiry_days=cookie_config.get("expiry_days", 30),
            )
    except Exception:
        # Secrets file doesn't exist or is malformed - skip auth for local dev
        pass

    # No secrets configured - check if we're in Streamlit Cloud
    # (Streamlit Cloud sets specific env vars)
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        st.error(
            "Authentication not configured.\n\n"
            "Add credentials to Streamlit Cloud secrets. See dashboard/docs/README.md for setup."
        )
        st.stop()

    # Local development without secrets - skip auth with warning
    return None


def show_login_page(authenticator: streamlit_authenticator.Authenticate) -> bool:
    """Show login form and return True if authenticated."""
    # Show logo on login page
    logo_path = Path(__file__).parent.parent / "octarine_capital_stacked.svg"

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_path.exists():
            st.image(str(logo_path), width="stretch")
        else:
            st.title("Octarine Capital")

        st.markdown("---")

    # Render login widget
    authenticator.login(location="main")

    if st.session_state.get("authentication_status"):
        return True
    if st.session_state.get("authentication_status") is False:
        st.error("Username or password is incorrect")
        return False
    st.info("Please enter your credentials")
    return False


# ---------------------------------------------------------------------------
# Sidebar controls: environment switcher + connection status
# ---------------------------------------------------------------------------

_STAGE_OPTIONS = ("dev", "staging", "prod")


def _render_sidebar_controls() -> None:
    """Render the environment switcher and connection status in the sidebar."""
    current_stage = get_active_stage()
    stage_index = _STAGE_OPTIONS.index(current_stage) if current_stage in _STAGE_OPTIONS else 0

    selected_stage = st.sidebar.selectbox(
        "Environment",
        _STAGE_OPTIONS,
        index=stage_index,
        key="env_selector",
    )

    # If the user changed the environment, rebuild settings + clear caches
    if selected_stage != current_stage:
        logger.info("Environment switched from %s to %s", current_stage, selected_stage)
        set_stage(selected_stage)
        st.rerun()

    # Connection status indicator
    settings = get_dashboard_settings()
    if not settings.has_aws_credentials():
        st.sidebar.warning("AWS credentials not configured (using default chain)")
    else:
        st.sidebar.caption(f"Connected: {settings.account_data_table}")

    st.sidebar.markdown("---")


# ---------------------------------------------------------------------------
# Dashboard rendering via st.navigation()
# ---------------------------------------------------------------------------


def show_dashboard() -> None:
    """Show the main dashboard content using Streamlit's st.navigation API."""
    # Inject custom styles based on theme
    inject_styles()

    # Sidebar: environment switcher + status
    _render_sidebar_controls()

    # Define pages using st.navigation
    nav_pages = [
        st.Page(_page_portfolio_overview, title="Portfolio Overview", default=True),
        st.Page(_page_forward_projection, title="Forward Projection"),
        st.Page(_page_pnl_table, title="Daily PnL Table"),
        st.Page(_page_last_run_analysis, title="Last Run Analysis"),
        st.Page(_page_trade_history, title="Trade History"),
        st.Page(_page_strategy_performance, title="Strategy Performance"),
        st.Page(_page_execution_quality, title="Execution Quality"),
        st.Page(_page_symbol_analytics, title="Symbol Analytics"),
        st.Page(_page_options_hedging, title="Options Hedging"),
    ]

    selected_page = st.navigation(nav_pages)
    selected_page.run()


def main() -> None:
    """Main entry point with authentication."""
    authenticator = get_authenticator()

    if authenticator is None:
        # Auth disabled (local dev) - show dashboard directly
        show_dashboard()
        return

    # Check authentication status
    if show_login_page(authenticator):
        # Authenticated - show logout in sidebar and dashboard
        with st.sidebar:
            st.write(f"Welcome, **{st.session_state.get('name', 'User')}**")
            authenticator.logout("Logout", "sidebar")

        show_dashboard()


if __name__ == "__main__":
    main()
else:
    # When imported by Streamlit, run main
    main()
