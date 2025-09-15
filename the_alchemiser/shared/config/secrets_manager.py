#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Secrets Manager for credential loading with simple environment detection.

This module provides simple functions for loading secrets from the appropriate source:
- Local development: Loads from environment variables (typically .env files)
- AWS Lambda: Loads from AWS Secrets Manager

Trading mode is determined by which credentials you choose to store where.
"""

from __future__ import annotations

import logging

from the_alchemiser.shared.config.secrets_adapter import (
    get_alpaca_keys,
    get_twelvedata_api_key,
)

logger = logging.getLogger(__name__)


class SecretsManager:
    """Handles retrieving secrets with simple environment detection."""

    def __init__(self, _region_name: str | None = None) -> None:
        """Initialize the Secrets Manager."""
        # region_name is kept for compatibility
        logger.info("Initialized SecretsManager with simple environment detection")

    def get_secret(self) -> dict[str, str] | None:
        """Retrieve a secret - not implemented in simple approach."""
        logger.warning(
            "get_secret() is not implemented in the simple approach. Use specific methods like get_alpaca_keys()."
        )
        return None

    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys from the appropriate source.

        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found

        """
        result = get_alpaca_keys()
        if result[0] is None:
            return None, None
        # Return only api_key and secret_key for backward compatibility
        return result[0], result[1]

    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from the appropriate source."""
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
        """Determine stage based on environment."""
        import os

        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            return "prod"
        return "dev"


# Global instance for backward compatibility
secrets_manager = SecretsManager()
