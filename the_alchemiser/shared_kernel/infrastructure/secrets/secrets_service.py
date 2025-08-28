#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Secrets Service.

Handles credential retrieval for the trading system.
Provides a clean interface for accessing API keys and other sensitive data.
"""

from __future__ import annotations

import logging

from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager
from the_alchemiser.shared_kernel.infrastructure.errors.exceptions import ConfigurationError


class SecretsService:
    """Service for credential retrieval and management."""

    def __init__(self) -> None:
        """Initialize the secrets service."""
        self._secrets_manager = SecretsManager()

    def get_alpaca_credentials(self, paper_trading: bool) -> tuple[str, str]:
        """Get Alpaca API credentials.

        Args:
            paper_trading: Whether to get paper trading credentials

        Returns:
            Tuple of (api_key, secret_key)

        Raises:
            ConfigurationError: If credentials are not found or invalid

        """
        api_key, secret_key = self._secrets_manager.get_alpaca_keys(paper_trading=paper_trading)

        if not api_key or not secret_key:
            mode = "paper" if paper_trading else "live"
            error_msg = (
                f"Alpaca API keys not found for {mode} trading. "
                f"Please check that you have either:\n"
                f"1. Valid AWS credentials and the secret exists in AWS Secrets Manager, or\n"
                f"2. Environment variables set: ALPACA_{'PAPER_' if paper_trading else ''}KEY and ALPACA_{'PAPER_' if paper_trading else ''}SECRET"
            )
            raise ConfigurationError(error_msg)

        logging.debug(
            f"Successfully retrieved Alpaca {'paper' if paper_trading else 'live'} trading credentials"
        )

        return api_key, secret_key
