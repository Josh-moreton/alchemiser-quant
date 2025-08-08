"""
Account Service

Unified service for account information, positions and portfolio history.
Merges functionality from core.services.account_service and execution.account_service.
Separates account operations from market data responsibilities.
"""

import logging
from typing import Any, Protocol

from the_alchemiser.domain.models.account import AccountModel
from the_alchemiser.domain.types import AccountInfo, PositionInfo, PositionsDict
from the_alchemiser.services.account_utils import extract_comprehensive_account_data
from the_alchemiser.services.trading_client_service import TradingClientService


class DataProvider(Protocol):
    """Protocol defining the data provider interface needed by AccountService."""

    def get_positions(self) -> Any:
        """Get all positions."""
        ...

    def get_current_price(self, symbol: str) -> float | int | None:
        """Get current price for a symbol."""
        ...


class AccountService:
    """Unified service for account and position management operations."""

    def __init__(
        self,
        trading_client_service: TradingClientService,
        api_key: str,
        secret_key: str,
        api_endpoint: str,
        data_provider: DataProvider | None = None,
    ) -> None:
        """
        Initialize account service.

        Args:
            trading_client_service: Trading client service
            api_key: API key for direct API calls
            secret_key: Secret key for direct API calls
            api_endpoint: API endpoint for direct calls
            data_provider: Optional data provider for legacy compatibility
        """
        self._trading_client_service = trading_client_service
        self._api_key = api_key
        self._secret_key = secret_key
        self._api_endpoint = api_endpoint
        self._data_provider = data_provider

        # Pre-import the utility function to avoid runtime imports
        if data_provider:
            self._extract_account_data = extract_comprehensive_account_data

    # New API methods using TradingClientService
    def get_account_info(self) -> AccountModel | None:
        """
        Get account information as a typed model.

        Returns:
            AccountModel or None if error
        """
        try:
            account_data = self._trading_client_service.get_account_info()
            if account_data:
                return AccountModel.from_dict(account_data)
            return None
        except Exception as e:
            logging.error(f"Error getting account info: {e}")
            return None

    def get_account_info_dict(self) -> dict[str, Any] | None:
        """
        Get account information as dictionary (backward compatibility).

        Returns:
            Account information as dict or None if error
        """
        return self._trading_client_service.get_account_info()

    # Legacy API methods using DataProvider for backward compatibility
    def get_account_info_legacy(self) -> AccountInfo:
        """
        Return comprehensive account info using legacy data provider.

        Combines raw data provider information with processed account metrics.
        """
        if not self._data_provider:
            raise ValueError("Data provider not configured for legacy methods")
        return extract_comprehensive_account_data(self._data_provider)

    def get_positions_dict(self) -> PositionsDict:
        """
        Return current positions keyed by symbol using legacy data provider.

        Transforms the raw positions list into a symbol-indexed dictionary
        for easier lookup and manipulation.
        """
        if not self._data_provider:
            raise ValueError("Data provider not configured for legacy methods")

        positions = self._data_provider.get_positions()
        position_dict: PositionsDict = {}

        if not positions:
            return position_dict

        for position in positions:
            symbol = self._extract_symbol(position)
            if symbol:
                # Handle both dict and object types for position data
                def safe_get_pos(obj: Any, key: str, default: Any = 0.0) -> Any:
                    if isinstance(obj, dict):
                        return obj.get(key, default)
                    else:
                        return getattr(obj, key, default)

                # Convert raw position to PositionInfo
                qty_raw = safe_get_pos(position, "qty", 0.0)
                qty = float(qty_raw) if qty_raw is not None else 0.0

                position_info: PositionInfo = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": "long" if qty >= 0 else "short",
                    "market_value": float(safe_get_pos(position, "market_value", 0.0) or 0.0),
                    "cost_basis": float(safe_get_pos(position, "cost_basis", 0.0) or 0.0),
                    "unrealized_pl": float(safe_get_pos(position, "unrealized_pl", 0.0) or 0.0),
                    "unrealized_plpc": float(safe_get_pos(position, "unrealized_plpc", 0.0) or 0.0),
                    "current_price": float(safe_get_pos(position, "current_price", 0.0) or 0.0),
                }
                position_dict[symbol] = position_info

        return position_dict

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol using legacy data provider.

        Provides type-safe wrapper around data provider with sensible defaults.
        """
        if not self._data_provider:
            raise ValueError("Data provider not configured for legacy methods")

        price = self._data_provider.get_current_price(symbol)
        return float(price) if price is not None else 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """
        Return current market values for multiple symbols using legacy data provider.

        Efficiently batches price requests and handles errors gracefully.
        Returns only valid prices to prevent calculation errors downstream.
        """
        if not self._data_provider:
            raise ValueError("Data provider not configured for legacy methods")

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
