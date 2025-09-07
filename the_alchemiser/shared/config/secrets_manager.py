#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Legacy Secrets Manager - DEPRECATED
This module is maintained for backward compatibility but delegates to the new SecretsAdapter.

The new SecretsAdapter provides:
- Environment-aware credential loading (local .env vs AWS Secrets Manager)
- Stage-based secret isolation (dev/prod)
- Runtime guardrails for paper vs live trading

New code should use SecretsAdapter directly.
"""

from __future__ import annotations

import logging
import warnings

# Issue deprecation warning
warnings.warn(
    "secrets_manager module is deprecated. Use secrets_adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class SecretsManager:
    """Handles retrieving secrets - DEPRECATED.
    
    This class is maintained for backward compatibility but delegates to SecretsAdapter.
    New code should use SecretsAdapter directly.
    """

    def __init__(self, region_name: str | None = None) -> None:
        """Initialize the Secrets Manager - delegates to SecretsAdapter."""
        from the_alchemiser.shared.config.secrets_adapter import secrets_adapter
        
        self._adapter = secrets_adapter
        logger.warning("SecretsManager is deprecated. Use SecretsAdapter instead.")

    def get_secret(self, secret_name: str) -> dict[str, str] | None:
        """Retrieve a secret - DEPRECATED method."""
        logger.warning("get_secret() is deprecated. Use SecretsAdapter methods directly.")
        # Return None to maintain compatibility but don't actually fetch
        return None

    def get_alpaca_keys(self, paper_trading: bool = True) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys - delegates to SecretsAdapter.
        
        Note: The paper_trading parameter is ignored as the new system determines
        trading mode based on environment stage.
        """
        if paper_trading is False:
            logger.warning(
                "Live trading mode requested via paper_trading=False is ignored. "
                "Trading mode is now determined by deployment stage."
            )
        
        return self._adapter.get_alpaca_keys()

    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key - delegates to SecretsAdapter."""
        return self._adapter.get_twelvedata_api_key()


# Global instance for backward compatibility
# New code should use SecretsAdapter directly
from the_alchemiser.shared.config.secrets_adapter import secrets_adapter

secrets_manager = SecretsManager()
