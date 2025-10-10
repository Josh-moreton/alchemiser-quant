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

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

# Import Position and TradeAccount for runtime use
from alpaca.trading.models import Position, TradeAccount
from alpaca.trading.requests import GetPortfolioHistoryRequest

from the_alchemiser.shared.errors.exceptions import TradingClientError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.alpaca_error_handler import alpaca_retry_context

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = get_logger(__name__)


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

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object."""
        return self._get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as a plain dictionary for convenience.

        Note: Financial values are returned as strings to preserve precision.
        Convert to Decimal for calculations.

        Returns:
            Dictionary with account data or None if unavailable

        Raises:
            TradingClientError: If account retrieval fails

        """
        try:
            account_obj = self._get_account_object()
            if not account_obj:
                return None

            # Build dict from known attributes with proper type handling
            return {
                "id": getattr(account_obj, "id", None),
                "account_number": getattr(account_obj, "account_number", None),
                "status": getattr(account_obj, "status", None),
                "currency": getattr(account_obj, "currency", None),
                # Return financial values as strings to preserve precision
                "buying_power": str(getattr(account_obj, "buying_power", "0"))
                if getattr(account_obj, "buying_power", None) is not None
                else None,
                "cash": str(getattr(account_obj, "cash", "0"))
                if getattr(account_obj, "cash", None) is not None
                else None,
                "equity": str(getattr(account_obj, "equity", "0"))
                if getattr(account_obj, "equity", None) is not None
                else None,
                "portfolio_value": str(getattr(account_obj, "portfolio_value", "0"))
                if getattr(account_obj, "portfolio_value", None) is not None
                else None,
            }
        except TradingClientError:
            # Already logged in _get_account_object
            raise
        except Exception as exc:
            logger.error(
                "Failed to convert account to dictionary",
                error=str(exc),
                module="alpaca_account_service",
            )
            raise TradingClientError("Account data conversion failed") from exc

    def _get_account_object(self) -> TradeAccount | None:
        """Get account object for internal use.

        Returns:
            TradeAccount object or None if retrieval fails

        Raises:
            TradingClientError: If account retrieval fails after retries

        """
        try:
            with alpaca_retry_context(max_retries=3, operation_name="Get account information"):
                account = self._trading_client.get_account()
                logger.debug("Successfully retrieved account information")
                if account is not None:
                    return account  # type: ignore[return-value]
                return None
        except Exception as e:
            logger.error(
                "Failed to get account information",
                error=str(e),
                module="alpaca_account_service",
            )
            raise TradingClientError(
                "Failed to retrieve account information from Alpaca API"
            ) from e

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power.

        Returns:
            Buying power as Decimal or None if unavailable

        Raises:
            TradingClientError: If account retrieval fails

        """
        try:
            account = self._get_account_object()
            if account and hasattr(account, "buying_power") and account.buying_power is not None:
                return Decimal(str(account.buying_power))
            return None
        except TradingClientError:
            # Already logged in _get_account_object
            raise
        except Exception as e:
            logger.error(
                "Failed to convert buying power to Decimal",
                error=str(e),
                module="alpaca_account_service",
            )
            raise TradingClientError("Invalid buying power value") from e

    def get_portfolio_value(self) -> Decimal | None:
        """Get current portfolio value.

        Returns:
            Portfolio value as Decimal or None if unavailable

        Raises:
            TradingClientError: If account retrieval fails

        """
        try:
            account = self._get_account_object()
            if (
                account
                and hasattr(account, "portfolio_value")
                and account.portfolio_value is not None
            ):
                return Decimal(str(account.portfolio_value))
            return None
        except TradingClientError:
            # Already logged in _get_account_object
            raise
        except Exception as e:
            logger.error(
                "Failed to convert portfolio value to Decimal",
                error=str(e),
                module="alpaca_account_service",
            )
            raise TradingClientError("Invalid portfolio value") from e

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        Raises:
            TradingClientError: If position retrieval fails

        """
        try:
            with alpaca_retry_context(max_retries=3, operation_name="Get all positions"):
                positions = self._trading_client.get_all_positions()
                logger.debug(
                    "Successfully retrieved positions",
                    count=len(positions),
                    module="alpaca_account_service",
                )
                return list(positions)
        except Exception as e:
            logger.error(
                "Failed to get positions",
                error=str(e),
                module="alpaca_account_service",
            )
            raise TradingClientError("Failed to retrieve positions from Alpaca API") from e

    def get_all_positions(self) -> list[Any]:
        """Alias for `get_positions()` to mirror Alpaca SDK naming.

        Note:
        - Prefer using `get_positions()` throughout the codebase for consistency.
        - This alias exists to reduce confusion for contributors familiar with the SDK.

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        return self.get_positions()

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all positions as dict mapping symbol to quantity.

        Returns:
            Dictionary mapping symbol to quantity (as Decimal) owned.
            Only includes non-zero positions.

        Raises:
            TradingClientError: If position retrieval fails

        """
        result: dict[str, Decimal] = {}
        try:
            for pos in self.get_positions():
                position_entry = self._extract_position_entry(pos)
                if position_entry:
                    symbol, quantity = position_entry
                    result[symbol] = quantity
        except TradingClientError:
            # Already logged in get_positions
            raise
        except Exception as e:
            logger.error(
                "Failed to build positions dictionary",
                error=str(e),
                module="alpaca_account_service",
            )
            # Return partial results rather than failing completely
            # This allows graceful degradation
        return result

    def get_position(self, symbol: str) -> Position | None:
        """Get position for specific symbol.

        Args:
            symbol: Trading symbol to get position for

        Returns:
            Position object if found, None otherwise

        Raises:
            TradingClientError: If position retrieval fails (except when position doesn't exist)

        """
        try:
            with alpaca_retry_context(max_retries=3, operation_name=f"Get position for {symbol}"):
                position = self._trading_client.get_open_position(symbol)
                logger.debug(
                    "Successfully retrieved position",
                    symbol=symbol,
                    module="alpaca_account_service",
                )
                if position is not None:
                    return position  # type: ignore[return-value]
                return None
        except Exception as e:
            # Check for "position does not exist" in error message
            # This is not an error condition - just means no position exists
            error_msg = str(e).lower()
            if "position does not exist" in error_msg or "not found" in error_msg:
                logger.debug(
                    "No position found for symbol",
                    symbol=symbol,
                    module="alpaca_account_service",
                )
                return None
            logger.error(
                "Failed to get position",
                symbol=symbol,
                error=str(e),
                module="alpaca_account_service",
            )
            raise TradingClientError(f"Failed to retrieve position for {symbol}") from e

    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working.

        Returns:
            True if connection is valid, False otherwise

        """
        try:
            account = self._get_account_object()
            if account:
                logger.info(
                    "Alpaca connection validated successfully",
                    module="alpaca_account_service",
                )
                return True
            return False
        except TradingClientError as e:
            logger.error(
                "Alpaca connection validation failed",
                error=str(e),
                module="alpaca_account_service",
            )
            return False

    def get_portfolio_history(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        timeframe: str = "1Day",
        period: str | None = None,
    ) -> dict[str, Any] | None:
        """Get portfolio performance history.

        Args:
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)
            timeframe: Timeframe for data points (valid: 1Min, 5Min, 15Min, 1H, 1D)
            period: Period string (1W, 1M, 3M, 1A) - alternative to start/end dates

        Returns:
            Portfolio history data, or None if failed.

        """
        try:
            # Normalize timeframe to Alpaca-accepted values for portfolio history
            # Accept friendly inputs like "1Day"/"1Hour" and map to "1D"/"1H"
            tf_input = (timeframe or "").strip()
            tf_lower = tf_input.lower()
            timeframe_normalized = tf_input
            if tf_lower in ("1day", "1d"):
                timeframe_normalized = "1D"
            elif tf_lower in ("1hour", "1h"):
                timeframe_normalized = "1H"
            elif tf_lower in ("1min", "1m"):
                timeframe_normalized = "1Min"
            elif tf_lower in ("5min", "5m"):
                timeframe_normalized = "5Min"
            elif tf_lower in ("15min", "15m"):
                timeframe_normalized = "15Min"

            # Build request parameters (typed to allow datetime values for start/end)
            request_params: dict[str, Any] = {"timeframe": timeframe_normalized}

            if period:
                request_params["period"] = period
            else:
                if start_date:
                    request_params["start"] = datetime.fromisoformat(start_date)
                if end_date:
                    request_params["end"] = datetime.fromisoformat(end_date)

            # Create request object
            if request_params:
                request = GetPortfolioHistoryRequest(**request_params)
                history = self._trading_client.get_portfolio_history(request)
            else:
                history = self._trading_client.get_portfolio_history()

            # Convert to dictionary
            return {
                "timestamp": getattr(history, "timestamp", []),
                "equity": getattr(history, "equity", []),
                "profit_loss": getattr(history, "profit_loss", []),
                "profit_loss_pct": getattr(history, "profit_loss_pct", []),
                "base_value": getattr(history, "base_value", None),
                "timeframe": timeframe_normalized,
            }
        except Exception as e:
            logger.error(
                "Failed to get portfolio history",
                error=str(e),
                module="alpaca_account_service",
            )
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
            logger.error(
                "Failed to get activities",
                error=str(e),
                module="alpaca_account_service",
            )
            return []

    def _extract_position_entry(self, pos: Position | dict[str, Any]) -> tuple[str, Decimal] | None:
        """Extract symbol and quantity from a position object.

        Args:
            pos: Position object (SDK model or dict)

        Returns:
            Tuple of (symbol, quantity as Decimal) if valid, None otherwise

        """
        symbol = self._extract_position_symbol(pos)
        if not symbol:
            return None

        qty_raw = self._extract_position_quantity(pos)
        if qty_raw is None:
            return None

        try:
            return str(symbol), Decimal(str(qty_raw))
        except (ValueError, TypeError, ArithmeticError):
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
