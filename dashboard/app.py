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

# Suppress debug logs BEFORE any imports (structlog respects this env var)
import os

os.environ["ALCHEMISER_LOG_LEVEL"] = "WARNING"

import logging
from pathlib import Path

import _setup_imports  # noqa: F401
import streamlit as st
from dotenv import load_dotenv

from components.styles import inject_styles

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


def show_dashboard() -> None:
    """Show the main dashboard content."""
    # Inject custom styles based on theme
    inject_styles()

    # Initialize current page in session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Portfolio Overview"

    # Navigation links
    pages = [
        ("Portfolio Overview", "Portfolio Overview"),
        ("Forward Projection", "Forward Projection"),
        ("Last Run Analysis", "Last Run Analysis"),
        ("Trade History", "Trade History"),
        ("Strategy Performance", "Strategy Performance"),
        ("Execution Quality", "Execution Quality"),
        ("Symbol Analytics", "Symbol Analytics"),
        ("Options Hedging", "Options Hedging"),
    ]

    # Render navigation links
    for label, page_key in pages:
        is_active = st.session_state.current_page == page_key
        css_class = "nav-link-active" if is_active else "nav-link"
        st.sidebar.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        if st.sidebar.button(label, key=f"nav_{page_key}", use_container_width=True):
            st.session_state.current_page = page_key
            st.rerun()
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.caption("Real-time trading system dashboard")

    # Route to pages
    page_key = st.session_state.current_page

    if page_key == "Portfolio Overview":
        from pages import portfolio_overview

        portfolio_overview.show()
    elif page_key == "Forward Projection":
        from pages import forward_projection

        forward_projection.show()
    elif page_key == "Last Run Analysis":
        from pages import last_run_analysis

        last_run_analysis.show()
    elif page_key == "Trade History":
        from pages import trade_history

        trade_history.show()
    elif page_key == "Strategy Performance":
        from pages import strategy_performance

        strategy_performance.show()
    elif page_key == "Execution Quality":
        from pages import execution_quality

        execution_quality.show()
    elif page_key == "Symbol Analytics":
        from pages import symbol_analytics

        symbol_analytics.show()
    elif page_key == "Options Hedging":
        from pages import options_hedging

        options_hedging.show()


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
