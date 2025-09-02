#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Configuration Service.

Handles loading and managing configuration for the trading system.
Provides a clean interface for accessing configuration settings.
"""

from __future__ import annotations

from the_alchemiser.shared.config.config import Settings, load_settings


class ConfigService:
    """Service for loading and managing configuration."""

    def __init__(self, config: Settings | None = None) -> None:
        """Initialize configuration service.

        Args:
            config: Optional configuration object. If None, loads from global config.

        """
        if config is None:
            config = load_settings()
        self._config = config

    @property
    def config(self) -> Settings:
        """Get the configuration object."""
        return self._config

    @property
    def cache_duration(self) -> int:
        """Get cache duration in seconds."""
        return self._config.data.cache_duration or 3600

    @property
    def paper_endpoint(self) -> str:
        """Get Alpaca paper trading endpoint."""
        return self._config.alpaca.paper_endpoint

    @property
    def live_endpoint(self) -> str:
        """Get Alpaca live trading endpoint."""
        return self._config.alpaca.endpoint

    def get_endpoint(self, paper_trading: bool) -> str:
        """Get the appropriate endpoint for the trading mode.

        Args:
            paper_trading: Whether using paper trading

        Returns:
            Appropriate endpoint URL

        """
        return self.paper_endpoint if paper_trading else self.live_endpoint
