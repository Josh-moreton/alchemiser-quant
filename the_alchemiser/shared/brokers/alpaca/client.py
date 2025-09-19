"""Business Unit: shared | Status: current.

Alpaca client management.

Handles authentication, base client initialization, and session management
for Alpaca broker connections.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient

if TYPE_CHECKING:
    from .config import AlpacaConfig

logger = logging.getLogger(__name__)


class AlpacaClient:
    """Central client manager for Alpaca trading and data clients."""

    def __init__(self, config: AlpacaConfig) -> None:
        """Initialize Alpaca clients with configuration.
        
        Args:
            config: AlpacaConfig instance with credentials and settings

        """
        self._config = config
        self._trading_client: TradingClient | None = None
        self._data_client: StockHistoricalDataClient | None = None

    @property
    def config(self) -> AlpacaConfig:
        """Get the configuration."""
        return self._config

    @property
    def trading_client(self) -> TradingClient:
        """Get the trading client, creating it if needed."""
        if self._trading_client is None:
            try:
                self._trading_client = TradingClient(
                    api_key=self._config.api_key,
                    secret_key=self._config.secret_key,
                    paper=self._config.paper,
                )
                logger.debug(f"Trading client initialized - Paper: {self._config.paper}")
            except Exception as e:
                logger.error(f"Failed to initialize trading client: {e}")
                raise
        return self._trading_client

    @property
    def data_client(self) -> StockHistoricalDataClient:
        """Get the data client, creating it if needed."""
        if self._data_client is None:
            try:
                self._data_client = StockHistoricalDataClient(
                    api_key=self._config.api_key,
                    secret_key=self._config.secret_key,
                )
                logger.debug("Data client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize data client: {e}")
                raise
        return self._data_client

    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working.
        
        Returns:
            True if connection is valid, False otherwise

        """
        try:
            # Test connection by getting account info
            account = self.trading_client.get_account()
            if account:
                logger.info("Alpaca connection validated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Alpaca connection validation failed: {e}")
            return False