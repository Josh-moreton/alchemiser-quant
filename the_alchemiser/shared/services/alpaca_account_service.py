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

from the_alchemiser.shared.errors.exceptions import (
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.alpaca_error_handler import (
    HTTPError,
    RequestException,
    RetryException,
    alpaca_retry_context,
)

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

        Returns all account fields from the Alpaca GET /v2/account endpoint:
        https://docs.alpaca.markets/reference/getaccount-1

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

            # Helper to safely extract string value from account attribute
            def _safe_str(attr_name: str) -> str | None:
                val = getattr(account_obj, attr_name, None)
                return str(val) if val is not None else None

            # Build dict from all known attributes per Alpaca API
            # See: https://docs.alpaca.markets/reference/getaccount-1
            return {
                # Identity fields
                "id": getattr(account_obj, "id", None),
                "account_number": getattr(account_obj, "account_number", None),
                "status": getattr(account_obj, "status", None),
                "currency": getattr(account_obj, "currency", None),
                # Core financial values (as strings for precision)
                "buying_power": _safe_str("buying_power"),
                "cash": _safe_str("cash"),
                "equity": _safe_str("equity"),
                "portfolio_value": _safe_str("portfolio_value"),
                "last_equity": _safe_str("last_equity"),
                "long_market_value": _safe_str("long_market_value"),
                "short_market_value": _safe_str("short_market_value"),
                # Margin fields - critical for leverage safety
                "initial_margin": _safe_str("initial_margin"),
                "maintenance_margin": _safe_str("maintenance_margin"),
                "last_maintenance_margin": _safe_str("last_maintenance_margin"),
                "sma": _safe_str("sma"),  # Special Memorandum Account
                # Buying power variants
                "regt_buying_power": _safe_str("regt_buying_power"),  # Reg T overnight
                "daytrading_buying_power": _safe_str("daytrading_buying_power"),  # PDT 4x
                # Account type indicator: 1=cash, 2=margin, 4=PDT
                "multiplier": _safe_str("multiplier"),
                # Day trading status
                "daytrade_count": getattr(account_obj, "daytrade_count", None),
                "pattern_day_trader": getattr(account_obj, "pattern_day_trader", None),
                # Account status flags
                "trading_blocked": getattr(account_obj, "trading_blocked", None),
                "transfers_blocked": getattr(account_obj, "transfers_blocked", None),
                "account_blocked": getattr(account_obj, "account_blocked", None),
                "shorting_enabled": getattr(account_obj, "shorting_enabled", None),
            }
        except TradingClientError:
            # Already logged in _get_account_object
            raise
        except (ValueError, TypeError, AttributeError) as exc:
            # Data conversion errors - wrap in TradingClientError
            logger.error(
                "Failed to convert account to dictionary due to data conversion error",
                error=str(exc),
                error_type=type(exc).__name__,
                module="alpaca_account_service",
            )
            raise TradingClientError("Account data conversion failed") from exc
        except Exception as exc:
            # Unexpected errors during conversion
            logger.error(
                "Failed to convert account to dictionary due to unexpected error",
                error=str(exc),
                error_type=type(exc).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (HTTPError, RetryException, RequestException) as e:
            # Alpaca API errors - wrap in TradingClientError
            logger.error(
                "Failed to get account information due to API error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            raise TradingClientError(
                "Failed to retrieve account information from Alpaca API"
            ) from e
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Failed to get account information due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (ValueError, TypeError, ArithmeticError) as e:
            # Decimal conversion errors - wrap in TradingClientError
            logger.error(
                "Failed to convert buying power to Decimal due to conversion error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            raise TradingClientError("Invalid buying power value") from e
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Failed to convert buying power to Decimal due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (ValueError, TypeError, ArithmeticError) as e:
            # Decimal conversion errors - wrap in TradingClientError
            logger.error(
                "Failed to convert portfolio value to Decimal due to conversion error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            raise TradingClientError("Invalid portfolio value") from e
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Failed to convert portfolio value to Decimal due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (HTTPError, RetryException, RequestException) as e:
            # Alpaca API errors - wrap in TradingClientError
            logger.error(
                "Failed to get positions due to API error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            raise TradingClientError("Failed to retrieve positions from Alpaca API") from e
        except Exception as e:
            # Unexpected errors
            logger.error(
                "Failed to get positions due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (ValueError, TypeError, AttributeError) as e:
            # Data extraction/conversion errors - log but return partial results
            logger.error(
                "Failed to build positions dictionary due to data error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            # Return partial results rather than failing completely for graceful degradation
        except Exception as e:
            # Unexpected errors - log but return partial results
            logger.error(
                "Failed to build positions dictionary due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            # Return partial results rather than failing completely for graceful degradation
        return result

    def get_position(self, symbol: str) -> Position | None:
        """Get position for specific symbol.

        Args:
            symbol: Trading symbol to get position for

        Returns:
            Position object if found, None otherwise

        Raises:
            TradingClientError: If position retrieval fails (except when position doesn't exist)

        Note:
            This method does NOT use retry logic for 404 errors (position does not exist).
            A 404 is expected behavior for BUY orders on symbols with no existing position.
            Retries are only used for transient network errors.

        """
        try:
            # Direct API call without retry context for expected 404s
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
            # Check for "position does not exist" - this is expected, not an error
            # Alpaca returns error code 40410000 for non-existent positions
            error_str = str(e).lower()
            is_position_not_found = (
                "position does not exist" in error_str
                or "40410000" in str(e)
                or "not found" in error_str
            )

            if is_position_not_found:
                # Expected case: no position exists (e.g., for BUY orders on new symbols)
                logger.debug(
                    "No position found for symbol",
                    symbol=symbol,
                    module="alpaca_account_service",
                )
                return None

            # Actual error - could be transient, use retry logic
            try:
                with alpaca_retry_context(
                    max_retries=3, operation_name=f"Get position for {symbol}"
                ):
                    position = self._trading_client.get_open_position(symbol)
                    logger.debug(
                        "Successfully retrieved position after retry",
                        symbol=symbol,
                        module="alpaca_account_service",
                    )
                    if position is not None:
                        return position  # type: ignore[return-value]
                    return None
            except Exception as retry_error:
                logger.error(
                    "Failed to get position",
                    symbol=symbol,
                    error=str(retry_error),
                    module="alpaca_account_service",
                )
                raise TradingClientError(
                    f"Failed to retrieve position for {symbol}"
                ) from retry_error

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
        except (HTTPError, RetryException, RequestException) as e:
            # Alpaca API errors - log and return None
            logger.error(
                "Failed to get portfolio history due to API error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            return None
        except (ValueError, TypeError, AttributeError) as e:
            # Data conversion/access errors - log and return None
            logger.error(
                "Failed to get portfolio history due to data error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            return None
        except Exception as e:
            # Unexpected errors - log and return None
            logger.error(
                "Failed to get portfolio history due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
        except (HTTPError, RetryException, RequestException) as e:
            # Alpaca API errors - log and return empty list
            logger.error(
                "Failed to get activities due to API error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            return []
        except (ValueError, TypeError, AttributeError) as e:
            # Data conversion/access errors - log and return empty list
            logger.error(
                "Failed to get activities due to data error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
            )
            return []
        except Exception as e:
            # Unexpected errors - log and return empty list
            logger.error(
                "Failed to get activities due to unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                module="alpaca_account_service",
                exc_info=True,
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
