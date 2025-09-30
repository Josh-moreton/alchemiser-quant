#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Secrets Manager for credential loading from environment variables.

This module provides simple functions for loading secrets from environment variables:
- All environments: Loads from environment variables (.env file or Lambda env vars)
- Trading mode is determined by ALPACA_ENDPOINT value
"""

from __future__ import annotations

import logging
import os

from the_alchemiser.shared.config.secrets_adapter import (
    get_alpaca_keys,
    get_twelvedata_api_key,
)

logger = logging.getLogger(__name__)


class SecretsManager:
    """Handles retrieving secrets from environment variables."""

    def __init__(self, _region_name: str | None = None) -> None:
        """Initialize the Secrets Manager.

        Args:
            _region_name: Deprecated parameter, kept for backward compatibility

        """
        logger.info("Initialized SecretsManager with environment variable loading")

    def get_secret(self) -> dict[str, str] | None:
        """Retrieve a secret - not implemented.

        Use specific methods like get_alpaca_keys() instead.
        """
        logger.warning(
            "get_secret() is not implemented. Use specific methods like get_alpaca_keys()."
        )
        return None

    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys from environment variables.

        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found

        """
        result = get_alpaca_keys()
        if result[0] is None:
            return None, None
        # Return only api_key and secret_key for backward compatibility
        return result[0], result[1]

    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from environment variables."""
        return get_twelvedata_api_key()

    @property
    def is_paper_trading(self) -> bool:
        """Determine if paper trading based on endpoint URL."""
        result = get_alpaca_keys()
        if result[2] is None:
            return True  # Default to paper trading if no endpoint
        return "paper" in result[2].lower()

    @property
    def stage(self) -> str:
        """Determine stage based on environment.

        Returns 'prod' if AWS_LAMBDA_FUNCTION_NAME is set, otherwise 'dev'.
        """
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            return "prod"
        return "dev"


# Global instance for backward compatibility
secrets_manager = SecretsManager()
