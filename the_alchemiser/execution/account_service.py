import logging
from typing import Any, Protocol

from the_alchemiser.utils.account_utils import extract_comprehensive_account_data


class DataProvider(Protocol):
    """Protocol defining the data provider interface needed by AccountService."""

    def get_positions(self) -> list[Any]:
        """Get all positions."""
        ...

    def get_current_price(self, symbol: str) -> float | int | None:
        """Get current price for a symbol."""
        ...


class AccountService:
    """
    Service class for account and position management.

    Uses composition and dependency injection instead of thin proxy methods.
    Provides higher-level account operations by combining data provider
    capabilities with business logic.
    """

    def __init__(self, data_provider: DataProvider):
        self._data_provider = data_provider
        # Pre-import the utility function to avoid runtime imports
        self._extract_account_data = extract_comprehensive_account_data

    def get_account_info(self) -> dict[str, Any]:
        """
        Return comprehensive account info.

        Combines raw data provider information with processed account metrics.
        """
        return self._extract_account_data(self._data_provider)

    def get_positions_dict(self) -> dict[str, dict[str, Any]]:
        """
        Return current positions keyed by symbol.

        Transforms the raw positions list into a symbol-indexed dictionary
        for easier lookup and manipulation.
        """
        positions = self._data_provider.get_positions()
        position_dict: dict[str, dict[str, Any]] = {}

        if not positions:
            return position_dict

        for position in positions:
            symbol = self._extract_symbol(position)
            if symbol:
                position_dict[symbol] = position

        return position_dict

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Provides type-safe wrapper around data provider with sensible defaults.
        """
        price = self._data_provider.get_current_price(symbol)
        return float(price) if price is not None else 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """
        Return current market values for multiple symbols.

        Efficiently batches price requests and handles errors gracefully.
        Returns only valid prices to prevent calculation errors downstream.
        """
        prices = {}

        for symbol in symbols:
            try:
                price = self.get_current_price(symbol)
                if price > 0:
                    prices[symbol] = price
            except Exception as e:
                logging.warning(f"Failed to get current price for {symbol}: {e}")

        return prices

    def _extract_symbol(self, position) -> str:
        """Extract symbol from position object, handling different formats."""
        if isinstance(position, dict):
            symbol = position.get("symbol")
            return symbol if symbol is not None else ""
        symbol = getattr(position, "symbol", None)
        return symbol if symbol is not None else ""
