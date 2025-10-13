#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Simple environment-based secrets helper.

This module provides environment variable loading for secrets:
- All environments: Loads from environment variables (.env file or Lambda env vars)
- Trading mode determined by ALPACA_ENDPOINT value

Note: env_loader is imported for its side-effect of loading the .env file
into the environment before any os.getenv() calls are made.
"""

from __future__ import annotations

import os

# Auto-load .env file into environment variables (side-effect import)
from the_alchemiser.shared.config import env_loader  # noqa: F401
from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_PAPER_ENDPOINT = "https://paper-api.alpaca.markets"
MAX_KEY_LENGTH = 500  # Reasonable upper bound for API keys
COMPONENT = "secrets_adapter"


def get_alpaca_keys() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca API keys from environment variables.

    Attempts to load credentials from environment variables in both flat
    (ALPACA_KEY) and nested Pydantic (ALPACA__KEY) formats.

    Returns:
        Tuple of (api_key, secret_key, endpoint) on success, where:
            - api_key: Alpaca API key (sanitized)
            - secret_key: Alpaca secret key (sanitized)
            - endpoint: Alpaca API endpoint URL (defaults to paper trading)
        Returns (None, None, None) if required credentials are missing.

    Raises:
        ConfigurationError: If credentials are found but fail validation
            (e.g., empty after stripping, exceed maximum length, invalid URL format)

    """
    return _get_alpaca_keys_from_env()


def _get_alpaca_keys_from_env() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from environment variables (.env file auto-loaded).

    Returns:
        Tuple of (api_key, secret_key, endpoint) or (None, None, None) if missing

    Raises:
        ConfigurationError: If credentials are found but invalid

    """
    # Try both formats: ALPACA_KEY and ALPACA__KEY (Pydantic nested format)
    api_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA__KEY")
    secret_key = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA__SECRET")
    endpoint = os.getenv("ALPACA_ENDPOINT") or os.getenv("ALPACA__ENDPOINT")

    # Require at least API key and secret key
    if not api_key or not secret_key:
        logger.error(
            "Missing required Alpaca credentials in environment variables",
            extra={
                "component": COMPONENT,
                "required_vars": "ALPACA_KEY/ALPACA__KEY, ALPACA_SECRET/ALPACA__SECRET",
            },
        )
        return None, None, None

    # Validate and sanitize credentials
    api_key = _validate_and_sanitize_key(api_key, "ALPACA_KEY")
    secret_key = _validate_and_sanitize_key(secret_key, "ALPACA_SECRET")
    endpoint = _validate_and_sanitize_endpoint(endpoint)

    # Log successful loading (safe - no credentials in logs)
    logger.debug(
        "Successfully loaded Alpaca credential metadata from environment",
        extra={
            "component": COMPONENT,
            "endpoint": endpoint,
            "api_key_length": len(api_key),
        },
    )
    return api_key, secret_key, endpoint


def _validate_and_sanitize_key(key: str, key_name: str) -> str:
    """Validate and sanitize an API key from environment.

    Args:
        key: Raw key value from environment
        key_name: Name of the key for error messages

    Returns:
        Sanitized key string

    Raises:
        ConfigurationError: If key is empty after stripping or exceeds max length

    """
    key = key.strip()
    if not key:
        raise ConfigurationError(
            f"{key_name} is empty after stripping whitespace",
            config_key=key_name,
        )

    if len(key) > MAX_KEY_LENGTH:
        raise ConfigurationError(
            f"{key_name} exceeds maximum length of {MAX_KEY_LENGTH}",
            config_key=key_name,
        )

    return key


def _validate_and_sanitize_endpoint(endpoint: str | None) -> str:
    """Validate and sanitize endpoint URL.

    Args:
        endpoint: Raw endpoint URL from environment, or None

    Returns:
        Sanitized endpoint URL (defaults to paper trading if None)

    Raises:
        ConfigurationError: If endpoint URL has invalid format

    """
    if not endpoint:
        logger.info(
            "No ALPACA_ENDPOINT specified, defaulting to paper trading mode",
            extra={"component": COMPONENT, "default_endpoint": DEFAULT_PAPER_ENDPOINT},
        )
        return DEFAULT_PAPER_ENDPOINT

    endpoint = endpoint.strip()
    if not endpoint:
        logger.info(
            "ALPACA_ENDPOINT is empty after stripping, defaulting to paper trading mode",
            extra={"component": COMPONENT, "default_endpoint": DEFAULT_PAPER_ENDPOINT},
        )
        return DEFAULT_PAPER_ENDPOINT

    # Basic URL validation - must start with http:// or https://
    if not endpoint.startswith(("http://", "https://")):
        raise ConfigurationError(
            "ALPACA_ENDPOINT must be a valid HTTP(S) URL",
            config_key="ALPACA_ENDPOINT",
            config_value=endpoint[:50],  # Truncate for safety in logs
        )

    return endpoint


def get_email_password() -> str | None:
    """Get email password from environment variables.

    Attempts to load password first via Pydantic config (load_settings),
    then falls back to direct environment variable access for backward
    compatibility.

    Returns:
        Email password string or None if not found

    Raises:
        ConfigurationError: May propagate from load_settings() if config
            validation fails with invalid email settings

    """
    return _get_email_password_from_env()


def _get_email_password_from_env() -> str | None:
    """Get email password from environment variables.

    Returns:
        Email password string or None if not found

    Raises:
        ConfigurationError: If Pydantic config validation fails

    """
    # First try the Pydantic config model (preferred method)
    try:
        config = load_settings()
        if config.email.password:
            password = config.email.password.strip()
            if password:
                logger.debug(
                    "Successfully loaded email password from Pydantic config",
                    extra={
                        "component": COMPONENT,
                        "source": "pydantic_config",
                        "config_key": "EMAIL__PASSWORD",
                    },
                )
                return password
    except ConfigurationError as e:
        # Re-raise configuration errors immediately (don't fallback for config errors)
        logger.debug(
            "Configuration error loading email password, re-raising without fallback",
            extra={
                "component": COMPONENT,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise
    except Exception as e:
        # Log other exceptions but continue to fallback
        logger.debug(
            "Could not load email password from Pydantic config, trying fallback",
            extra={
                "component": COMPONENT,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

    # Fallback to direct environment variable access for backward compatibility
    fallback_password: str | None = (
        os.getenv("EMAIL__PASSWORD")
        or os.getenv("EMAIL_PASSWORD")
        or os.getenv("EMAIL__SMTP_PASSWORD")
        or os.getenv("SMTP_PASSWORD")
    )

    if fallback_password:
        fallback_password = fallback_password.strip()

    if not fallback_password:
        logger.warning(
            "Email password not found in environment variables",
            extra={
                "component": COMPONENT,
                "tried_vars": [
                    "EMAIL__PASSWORD",
                    "EMAIL_PASSWORD",
                    "EMAIL__SMTP_PASSWORD",
                    "SMTP_PASSWORD",
                ],
            },
        )
        return None

    logger.debug(
        "Successfully loaded email password from environment variables",
        extra={"component": COMPONENT, "source": "direct_env_vars"},
    )
    return fallback_password
