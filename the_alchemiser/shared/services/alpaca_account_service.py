"""Business Unit: shared | Status: current.

Alpaca account service for account-related operations.

This service extracts account management functionality from AlpacaManager
following the Single Responsibility Principle. It provides:
- Account information retrieval
- Financial metrics (buying power, portfolio value)
- Position management
- Account validation
- Portfolio history and activities
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

# Import Position for runtime use in isinstance checks
from alpaca.trading.models import Position

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.models import TradeAccount

logger = logging.getLogger(__name__)


class AlpacaAccountService:
    """Service for account-related operations using Alpaca API.
    
    This service encapsulates all account-related functionality previously
    scattered within AlpacaManager, providing a focused interface for:
    - Account information and validation
    - Position management and querying
    - Financial metrics and history
    - Account activities
    """

    def __init__(self, trading_client: TradingClient) -> None:
        """Initialize account service with Alpaca trading client.
        
        Args:
            trading_client: Alpaca TradingClient instance

        """
        self._trading_client = trading_client

    def get_account_info(self) -> dict[str, Any] | None:
        """Get account information as dict (protocol compliance)."""
        return self.get_account_dict()

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object."""
        return self._get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as a plain dictionary for convenience."""
        account_obj = self._get_account_object()
        if not account_obj:
            return None
        try:
            # Some SDK objects expose __dict__ with serializable fields
            data = account_obj.__dict__ if hasattr(account_obj, "__dict__") else None
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.debug(f"Falling back to manual account dict conversion: {exc}")
        # Fallback: build dict from known attributes
        return {
            "id": getattr(account_obj, "id", None),
            "account_number": getattr(account_obj, "account_number", None),
            "status": getattr(account_obj, "status", None),
            "currency": getattr(account_obj, "currency", None),
            "buying_power": getattr(account_obj, "buying_power", None),
            "cash": getattr(account_obj, "cash", None),
            "equity": getattr(account_obj, "equity", None),
            "portfolio_value": getattr(account_obj, "portfolio_value", None),
        }

    def _get_account_object(self) -> TradeAccount | None:
        """Get account object for internal use."""
        try:
            account = self._trading_client.get_account()
            logger.debug("Successfully retrieved account information")
            return account if isinstance(account, TradeAccount) else None
        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        try:
            account = self._get_account_object()
            if account and hasattr(account, "buying_power") and account.buying_power is not None:
                return float(account.buying_power)
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            raise

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        try:
            account = self._get_account_object()
            if (
                account
                and hasattr(account, "portfolio_value")
                and account.portfolio_value is not None
            ):
                return float(account.portfolio_value)
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            raise

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            # Ensure consistent return type
            return list(positions)
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_all_positions(self) -> list[Any]:
        """Alias for `get_positions()` to mirror Alpaca SDK naming.

        Note:
        - Prefer using `get_positions()` throughout the codebase for consistency.
        - This alias exists to reduce confusion for contributors familiar with the SDK.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        return self.get_positions()

    def get_positions_dict(self) -> dict[str, float]:
        """Get all positions as dict mapping symbol to quantity.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        result: dict[str, float] = {}
        try:
            for pos in self.get_positions():
                position_entry = self._extract_position_entry(pos)
                if position_entry:
                    symbol, quantity = position_entry
                    result[symbol] = quantity
        except (KeyError, AttributeError, TypeError):
            # Best-effort mapping; return what we have
            pass
        return result

    def get_position(self, symbol: str) -> Position | None:
        """Get position for specific symbol.
        
        Args:
            symbol: Trading symbol to get position for
            
        Returns:
            Position object if found, None otherwise

        """
        try:
            position = self._trading_client.get_open_position(symbol)
            logger.debug(f"Successfully retrieved position for {symbol}")
            return position if isinstance(position, Position) else None
        except Exception as e:
            if "position does not exist" in str(e).lower():
                logger.debug(f"No position found for {symbol}")
                return None
            logger.error(f"Failed to get position for {symbol}: {e}")
            raise

    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working."""
        try:
            account = self._get_account_object()
            if account:
                logger.info("Alpaca connection validated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Alpaca connection validation failed: {e}")
            return False

    def get_portfolio_history(
        self,
        _start_date: str | None = None,
        _end_date: str | None = None,
        timeframe: str = "1Day",
    ) -> dict[str, Any] | None:
        """Get portfolio performance history.

        Args:
            _start_date: Start date (ISO format), defaults to 1 month ago - currently unused
            _end_date: End date (ISO format), defaults to today - currently unused
            timeframe: Timeframe for data points

        Returns:
            Portfolio history data, or None if failed.

        """
        try:
            # Fetch without kwargs to satisfy type stubs
            history = self._trading_client.get_portfolio_history()
            # Convert to dictionary
            return {
                "timestamp": getattr(history, "timestamp", []),
                "equity": getattr(history, "equity", []),
                "profit_loss": getattr(history, "profit_loss", []),
                "profit_loss_pct": getattr(history, "profit_loss_pct", []),
                "base_value": getattr(history, "base_value", None),
                "timeframe": timeframe,
            }
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return None

    def get_activities(
        self,
        activity_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get account activities (trades, dividends, etc.).

        Args:
            activity_type: Filter by activity type (optional)
            start_date: Start date (ISO format), defaults to 1 week ago
            end_date: End date (ISO format), defaults to today

        Returns:
            List of activity records.

        """
        try:
            # get_activities may not be present in stubs; guard via getattr
            get_activities = getattr(self._trading_client, "get_activities", None)
            if not callable(get_activities):
                return []
            activities = get_activities(
                activity_type=activity_type, date=start_date, until=end_date
            )
            # Convert to list of dictionaries
            return [
                {
                    "id": str(getattr(activity, "id", "")),
                    "activity_type": str(getattr(activity, "activity_type", "")),
                    "date": str(getattr(activity, "date", "")),
                    "symbol": getattr(activity, "symbol", None),
                    "side": getattr(activity, "side", None),
                    "qty": getattr(activity, "qty", None),
                    "price": getattr(activity, "price", None),
                }
                for activity in activities
            ]
        except Exception as e:
            logger.error(f"Failed to get activities: {e}")
            return []

    def _extract_position_entry(self, pos: Position | dict[str, Any]) -> tuple[str, float] | None:
        """Extract symbol and quantity from a position object.

        Args:
            pos: Position object (SDK model or dict)

        Returns:
            Tuple of (symbol, quantity) if valid, None otherwise

        """
        symbol = self._extract_position_symbol(pos)
        if not symbol:
            return None

        qty_raw = self._extract_position_quantity(pos)
        if qty_raw is None:
            return None

        try:
            return str(symbol), float(qty_raw)
        except (ValueError, TypeError):
            return None

    def _extract_position_symbol(self, pos: Position | dict[str, Any]) -> str | None:
        """Extract symbol from position object."""
        return getattr(pos, "symbol", None) or (
            pos.get("symbol") if isinstance(pos, dict) else None
        )

    def _extract_position_quantity(self, pos: Position | dict[str, Any]) -> float | None:
        """Extract quantity from position object, preferring qty_available."""
        # Use qty_available if available, fallback to qty for compatibility
        qty_available = (
            getattr(pos, "qty_available", None)
            if not isinstance(pos, dict)
            else pos.get("qty_available")
        )
        if qty_available is not None:
            try:
                return float(qty_available)
            except (ValueError, TypeError):
                pass

        # Fallback to total qty if qty_available is not available
        qty = getattr(pos, "qty", None) if not isinstance(pos, dict) else pos.get("qty")
        if qty is not None:
            try:
                return float(qty)
            except (ValueError, TypeError):
                pass
        return None