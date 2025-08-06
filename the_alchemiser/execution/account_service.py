import logging
from typing import Any, Protocol

from the_alchemiser.core.types import AccountInfo, PositionInfo, PositionsDict
from the_alchemiser.utils.account_utils import extract_comprehensive_account_data


class DataProvider(Protocol):
    """Protocol defining the data provider interface needed by AccountService."""

    def get_positions(self) -> Any:  # TODO: Use proper typing once Alpaca types are available
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

    def __init__(self, data_provider: DataProvider) -> None:
        self._data_provider = data_provider
        # Pre-import the utility function to avoid runtime imports
        self._extract_account_data = extract_comprehensive_account_data

    def get_account_info(
        self,
    ) -> AccountInfo:  # Phase 17: Migrated from dict[str, Any] to AccountInfo
        """
        Return comprehensive account info.

        Combines raw data provider information with processed account metrics.
        """
        return extract_comprehensive_account_data(self._data_provider)

    def get_positions_dict(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, dict[str, Any]] to PositionsDict
        """
        Return current positions keyed by symbol.

        Transforms the raw positions list into a symbol-indexed dictionary
        for easier lookup and manipulation.
        """
        positions = self._data_provider.get_positions()
        position_dict: PositionsDict = {}  # Phase 18: Migrated to PositionsDict

        if not positions:
            return position_dict

        for position in positions:
            symbol = self._extract_symbol(position)
            if symbol:
                # Convert raw position to PositionInfo
                position_info: PositionInfo = {
                    "symbol": symbol,
                    "qty": getattr(position, "qty", 0.0),
                    "side": "long" if float(getattr(position, "qty", 0)) >= 0 else "short",
                    "market_value": getattr(position, "market_value", 0.0),
                    "cost_basis": getattr(position, "cost_basis", 0.0),
                    "unrealized_pl": getattr(position, "unrealized_pl", 0.0),
                    "unrealized_plpc": getattr(position, "unrealized_plpc", 0.0),
                    "current_price": getattr(position, "current_price", 0.0),
                }
                position_dict[symbol] = position_info

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

    def _extract_symbol(self, position: Any) -> str:
        """Extract symbol from position object, handling different formats."""
        if isinstance(position, dict):
            symbol = position.get("symbol")
            return symbol if symbol is not None else ""
        symbol = getattr(position, "symbol", None)
        return symbol if symbol is not None else ""
