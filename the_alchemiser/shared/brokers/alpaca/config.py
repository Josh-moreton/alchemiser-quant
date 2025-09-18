"""Business Unit: shared | Status: current.

Alpaca configuration management.

Handles environment variables, configuration validation, and default settings
for Alpaca broker connections.
"""

from __future__ import annotations

import os
from typing import Any


class AlpacaConfig:
    """Configuration management for Alpaca broker connections."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize Alpaca configuration.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True for safety)
            base_url: Optional custom base URL
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.base_url = base_url

    @property
    def is_paper_trading(self) -> bool:
        """Return True if using paper trading."""
        return self.paper

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "paper": self.paper,
            "base_url": self.base_url,
            # Note: Credentials intentionally excluded for security
        }

    def __repr__(self) -> str:
        """Return string representation without exposing credentials."""
        return f"AlpacaConfig(paper={self.paper})"


def load_config_from_env() -> AlpacaConfig | None:
    """Load Alpaca configuration from environment variables.
    
    Returns:
        AlpacaConfig instance if env vars are present, None otherwise
    """
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        return None
    
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    base_url = os.getenv("ALPACA_BASE_URL")
    
    return AlpacaConfig(
        api_key=api_key,
        secret_key=secret_key,
        paper=paper,
        base_url=base_url,
    )