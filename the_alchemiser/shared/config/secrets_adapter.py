#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Simple environment-based secrets helper.

This module provides environment variable loading for secrets:
- All environments: Loads from environment variables (.env file or Lambda env vars)
- Trading mode determined by ALPACA_ENDPOINT value
"""

from __future__ import annotations

import logging
import os

# Auto-load .env file into environment variables
from the_alchemiser.shared.config import env_loader  # noqa: F401
from the_alchemiser.shared.config.config import load_settings

logger = logging.getLogger(__name__)


def get_alpaca_keys() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca API keys from environment variables.

    Returns:
        Tuple of (api_key, secret_key, endpoint) or (None, None, None) if not found

    """
    return _get_alpaca_keys_from_env()


def _get_alpaca_keys_from_env() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from environment variables (.env file auto-loaded)."""
    # Try both formats: ALPACA_KEY and ALPACA__KEY (Pydantic nested format)
    api_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA__KEY")
    secret_key = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA__SECRET")
    endpoint = os.getenv("ALPACA_ENDPOINT") or os.getenv("ALPACA__ENDPOINT")

    # Require at least API key and secret key
    if not api_key or not secret_key:
        logger.error(
            "Missing required Alpaca credentials in environment variables: "
            "ALPACA_KEY/ALPACA__KEY, ALPACA_SECRET/ALPACA__SECRET"
        )
        return None, None, None

    # If no endpoint specified, default to paper trading
    if not endpoint:
        endpoint = "https://paper-api.alpaca.markets"
        logger.info("No ALPACA_ENDPOINT specified, defaulting to paper trading mode")

    logger.debug("Successfully loaded Alpaca credentials from environment variables")
    return api_key, secret_key, endpoint


def get_twelvedata_api_key() -> str | None:
    """Get TwelveData API key from environment variables."""
    return _get_twelvedata_key_from_env()


def _get_twelvedata_key_from_env() -> str | None:
    """Get TwelveData key from environment variables."""
    api_key = os.getenv("TWELVEDATA_KEY")

    if not api_key:
        logger.warning("TwelveData API key not found in environment variables")
        return None

    logger.debug("Successfully loaded TwelveData API key from environment")
    return api_key


def get_email_password() -> str | None:
    """Get email password from environment variables.

    Returns:
        Email password string or None if not found

    """
    return _get_email_password_from_env()


def _get_email_password_from_env() -> str | None:
    """Get email password from environment variables."""
    # First try the Pydantic config model (preferred method)
    try:
        config = load_settings()
        if config.email.password:
            logger.debug(
                "Successfully loaded email password from Pydantic config (EMAIL__PASSWORD)"
            )
            return config.email.password
    except Exception as e:
        logger.debug(f"Could not load email password from Pydantic config: {e}")

    # Fallback to direct environment variable access for backward compatibility
    password = (
        os.getenv("EMAIL__PASSWORD")
        or os.getenv("EMAIL_PASSWORD")
        or os.getenv("EMAIL__SMTP_PASSWORD")
        or os.getenv("SMTP_PASSWORD")
    )

    if not password:
        logger.warning(
            "Email password not found in environment variables "
            "(tried EMAIL__PASSWORD, EMAIL_PASSWORD, EMAIL__SMTP_PASSWORD, SMTP_PASSWORD)"
        )
        return None

    logger.debug("Successfully loaded email password from environment variables (fallback method)")
    return password

