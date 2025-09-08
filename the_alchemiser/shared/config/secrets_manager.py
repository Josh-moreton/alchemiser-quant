#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Secrets Manager for credential loading.

This module provides simple functions for loading secrets from the appropriate source:
- Local development: Loads from environment variables (typically .env files)
- AWS Lambda: Loads from AWS Secrets Manager

Trading mode is determined by which credentials you choose to store where.
"""

from __future__ import annotations

import logging

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys, get_twelvedata_api_key

logger = logging.getLogger(__name__)


class SecretsManager:
    """Handles retrieving secrets from environment or AWS Secrets Manager."""

    def __init__(self, region_name: str | None = None) -> None:
        """Initialize the Secrets Manager."""
        # region_name is kept for compatibility but not used in the simple approach
        logger.info("Initialized SecretsManager with simple environment detection")

    def get_secret(self, secret_name: str) -> dict[str, str] | None:
        """Retrieve a secret - not implemented in simple approach."""
        logger.warning("get_secret() is not implemented in the simple approach. Use specific methods like get_alpaca_keys().")
        return None

    def get_alpaca_keys(self, paper_trading: bool = True) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys from the appropriate source.
        
        Note: The paper_trading parameter is ignored as trading mode is determined
        by which credentials are stored where (local .env vs AWS Secrets Manager).
        
        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found
        """
        if paper_trading is False:
            logger.info(
                "Live trading mode requested via paper_trading=False. "
                "Trading mode is determined by credential storage location."
            )
        
        result = get_alpaca_keys()
        if result[0] is None:
            return None, None
        # Return only api_key and secret_key for backward compatibility
        return result[0], result[1]

    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from the appropriate source."""
        return get_twelvedata_api_key()


# Global instance for backward compatibility
secrets_manager = SecretsManager()
