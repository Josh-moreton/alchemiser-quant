"""Business Unit: shared | Status: current.

Alpaca broker adapter (moved from execution module for architectural compliance).

This module consolidates scattered Alpaca client usage into a single, well-managed class.
It provides a clean interface that:
1. Reduces scattered imports
2. Adds consistent error handling
3. Uses Pydantic models directly
4. Provides clean domain interfaces

Phase 2 Update: Now implements domain interfaces for type safety and future migration.
Phase 3 Update: Moved to shared module to resolve architectural boundary violations.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, Literal

# Type checking imports to avoid circular dependencies
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Order, Position, TradeAccount
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
)

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO
from the_alchemiser.shared.dto.broker_dto import (
    OrderExecutionResult,
    WebSocketResult,
)
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO
from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.shared.services.alpaca_account_service import AlpacaAccountService
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService

# Import Alpaca exceptions for proper error handling with type safety
_RetryExcImported: type[Exception]
try:
    from alpaca.common.exceptions import RetryException as _RetryExcImported
except ImportError:  # pragma: no cover - environment-dependent import
    # Fallback if the import path changes or package missing
    class _RetryExcImported(Exception):  # type: ignore[no-redef]
        """Fallback RetryException compatible with Alpaca SDK signature."""


RetryException = _RetryExcImported

# Import requests exceptions for HTTP error handling with type safety
_HTTPErrorImported: type[Exception]
_RequestExcImported: type[Exception]
try:
    from requests.exceptions import (
        HTTPError as _HTTPErrorImported,
    )
    from requests.exceptions import (
        RequestException as _RequestExcImported,
    )
except ImportError:  # pragma: no cover - environment-dependent import

    class _HTTPErrorImported(Exception):  # type: ignore[no-redef]
        """Fallback HTTPError when requests is unavailable."""

    class _RequestExcImported(Exception):  # type: ignore[no-redef]
        """Fallback RequestException when requests is unavailable."""


HTTPError = _HTTPErrorImported
RequestException = _RequestExcImported

if TYPE_CHECKING:
    from the_alchemiser.shared.services.websocket_manager import (
        WebSocketConnectionManager,
    )

logger = logging.getLogger(__name__)


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Centralized Alpaca client management implementing domain interfaces.

    This class consolidates all Alpaca API interactions into a single, well-managed interface.
    It provides consistent error handling, logging, and implements the domain layer interfaces
    for type safety and future architectural improvements.

    Implements:
    - TradingRepository: For order placement and position management
    - MarketDataRepository: For market data and quotes
    - AccountRepository: For account information and portfolio data

    Uses singleton behavior per credentials to prevent multiple WebSocket connections.
    """

    _instances: ClassVar[dict[str, AlpacaManager]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cleanup_in_progress: ClassVar[bool] = False
    _initialized: bool

    def __new__(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> AlpacaManager:
        """Create or return existing instance for the given credentials."""
        credentials_key = f"{api_key}:{secret_key}:{paper}:{base_url}"

        with cls._lock:
            # Wait for any cleanup to complete
            while cls._cleanup_in_progress:
                time.sleep(0.001)  # Brief wait for cleanup to finish

            if credentials_key not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[credentials_key] = instance
                instance._initialized = False
            return cls._instances[credentials_key]

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize Alpaca clients (only once per credentials).

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True for safety)
            base_url: Optional custom base URL

        """
        # Skip initialization if already initialized (singleton pattern)
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = base_url

        # Initialize clients
        try:
            # Note: TradingClient type stubs may not accept base_url as kwarg; avoid passing extras for mypy
            self._trading_client = TradingClient(
                api_key=api_key, secret_key=secret_key, paper=paper
            )

            self._data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

            logger.info(f"AlpacaManager initialized - Paper: {paper}")

        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise

        # Order tracking for WebSocket updates
        self._order_events: dict[str, threading.Event] = {}
        self._order_status: dict[str, str] = {}
        self._order_avg_price: dict[str, Decimal | None] = {}

        # WebSocket connection manager (for centralized WebSocket management)
        self._websocket_manager: WebSocketConnectionManager | None = None
        self._trading_service_active: bool = False

        # Initialize account service for account-related operations
        self._account_service = AlpacaAccountService(self._trading_client)

        # Initialize trading service with lazy WebSocket manager
        self._trading_service: AlpacaTradingService | None = None

        # Asset metadata cache with TTL
        self._asset_cache: dict[str, AssetInfoDTO] = {}
        self._asset_cache_timestamps: dict[str, float] = {}
        self._asset_cache_ttl = 300.0  # 5 minutes TTL
        self._asset_cache_lock = threading.Lock()

        # Mark as initialized to prevent re-initialization
        self._initialized = True

        # Initialize MarketDataService for delegation
        from the_alchemiser.shared.services.market_data_service import MarketDataService

        self._market_data_service = MarketDataService(self)

    @property
    def is_paper_trading(self) -> bool:
        """Return True if using paper trading."""
        return self._paper

    # Public, read-only accessors for credentials and mode (for factories/streams)
    @property
    def api_key(self) -> str:
        """Return the API key (read-only)."""
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Return the secret key (read-only)."""
        return self._secret_key

    @property
    def paper(self) -> bool:
        """Return whether paper/live mode is enabled."""
        return self._paper

    @property
    def trading_client(self) -> TradingClient:
        """Return underlying trading client for backward compatibility."""
        return self._trading_client

    def _get_trading_service(self) -> AlpacaTradingService:
        """Get or create the trading service with WebSocket manager."""
        if self._trading_service is None:
            # Ensure WebSocket manager is available
            if self._websocket_manager is None:
                from the_alchemiser.shared.services.websocket_manager import (
                    WebSocketConnectionManager,
                )

                self._websocket_manager = WebSocketConnectionManager(
                    self._api_key, self._secret_key, paper_trading=self._paper
                )

            # Create trading service with WebSocket manager
            self._trading_service = AlpacaTradingService(
                self._trading_client,
                self._websocket_manager,
                paper_trading=self._paper,
            )

        return self._trading_service

    # Helper methods for DTO mapping
    def _alpaca_order_to_execution_result(self, order: Order) -> OrderExecutionResult:
        """Convert Alpaca order object to OrderExecutionResult.

        Simple implementation that avoids circular imports.
        """
        try:
            # Extract basic fields from order object
            order_id_raw = getattr(order, "id", None)
            order_id = str(order_id_raw) if order_id_raw is not None else "unknown"
            status = getattr(order, "status", "unknown")
            filled_qty = Decimal(str(getattr(order, "filled_qty", 0)))
            avg_fill_price = getattr(order, "avg_fill_price", None)
            if avg_fill_price is not None:
                avg_fill_price = Decimal(str(avg_fill_price))

            # Simple timestamp handling
            submitted_at = getattr(order, "submitted_at", None) or datetime.now(UTC)
            if isinstance(submitted_at, str):
                # Handle ISO format strings
                submitted_at = datetime.fromisoformat(
                    submitted_at.replace("Z", UTC_TIMEZONE_SUFFIX)
                )

            completed_at = getattr(order, "updated_at", None)
            if completed_at and isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(
                    completed_at.replace("Z", UTC_TIMEZONE_SUFFIX)
                )

                # Map status to our expected values - using explicit typing to ensure Literal compliance
            status_mapping: dict[
                str,
                Literal["accepted", "filled", "partially_filled", "rejected", "canceled"],
            ] = {
                "new": "accepted",
                "accepted": "accepted",
                "pending_new": "accepted",
                "filled": "filled",
                "partially_filled": "partially_filled",
                "rejected": "rejected",
                "canceled": "canceled",
                "cancelled": "canceled",
                "expired": "rejected",
            }
            mapped_status: Literal[
                "accepted", "filled", "partially_filled", "rejected", "canceled"
            ] = status_mapping.get(status, "accepted")

            success = mapped_status not in ["rejected", "canceled"]

            return OrderExecutionResult(
                success=success,
                order_id=order_id,
                status=mapped_status,
                filled_qty=filled_qty,
                avg_fill_price=avg_fill_price,
                submitted_at=submitted_at,
                completed_at=completed_at,
                error=None if success else f"Order {status}",
            )
        except Exception as e:
            logger.error(f"Failed to convert order to execution result: {e}")
            return self._create_error_execution_result(e, "Order conversion")

    def _create_error_execution_result(
        self, error: Exception, context: str = "Operation", order_id: str = "unknown"
    ) -> OrderExecutionResult:
        """Create an error OrderExecutionResult."""
        status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = (
            "rejected"
        )
        return OrderExecutionResult(
            success=False,
            order_id=order_id,
            status=status,
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error=f"{context} failed: {error!s}",
        )

    # Trading Operations
    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dict (protocol compliance)."""
        return self._account_service.get_account_info()

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object."""
        return self._account_service.get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as a plain dictionary for convenience."""
        return self._account_service.get_account_dict()

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects (AccountRepository interface)."""
        return self._account_service.get_positions()

    def get_all_positions(self) -> list[Any]:
        """Alias for `get_positions()` to mirror Alpaca SDK naming."""
        return self._account_service.get_all_positions()

    def get_positions_dict(self) -> dict[str, float]:
        """Get all positions as dict mapping symbol to quantity."""
        return self._account_service.get_positions_dict()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        return self._account_service.get_position(symbol)

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        return self._get_trading_service().place_order(order_request)

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result DTO.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResult reflecting the latest known state.

        """
        return self._get_trading_service().get_order_execution_result(order_id)

    def _validate_market_order_params(
        self, symbol: str, side: str, qty: float | None, notional: float | None
    ) -> tuple[str, str]:
        """Validate market order parameters.

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Quantity to trade
            notional: Dollar amount to trade

        Returns:
            Tuple of (normalized_symbol, normalized_side)

        Raises:
            ValueError: If validation fails

        """
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        if qty is None and notional is None:
            raise ValueError("Either qty or notional must be specified")

        if qty is not None and notional is not None:
            raise ValueError("Cannot specify both qty and notional")

        if qty is not None and qty <= 0:
            raise ValueError("Quantity must be positive")

        if notional is not None and notional <= 0:
            raise ValueError("Notional amount must be positive")

        side_normalized = side.lower().strip()
        if side_normalized not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")

        return symbol.upper(), side_normalized

    def _adjust_quantity_for_complete_exit(
        self, symbol: str, side: str, qty: float | None, *, is_complete_exit: bool
    ) -> float | None:
        """Adjust quantity for complete exit if needed.

        Args:
            symbol: Stock symbol
            side: Order side
            qty: Original quantity
            is_complete_exit: Whether this is a complete exit

        Returns:
            Adjusted quantity or original quantity

        """
        if not (is_complete_exit and side == "sell" and qty is not None):
            return qty

        try:
            position = self.get_position(symbol)
            if not position:
                return qty
            # Use qty_available if available, fallback to qty
            available_qty = getattr(position, "qty_available", None)
            if available_qty is not None:
                final_qty = float(available_qty)
                logger.info(
                    f"Complete exit detected for {symbol}: using Alpaca's available quantity "
                    f"{final_qty} instead of calculated {qty}"
                )
                return final_qty

            # Fallback to total qty if qty_available not available
            total_qty = getattr(position, "qty", None)
            if total_qty is not None:
                final_qty = float(total_qty)
                logger.info(
                    f"Complete exit detected for {symbol}: using total quantity "
                    f"{final_qty} instead of calculated {qty}"
                )
                return final_qty
        except Exception as e:
            logger.warning(f"Failed to get position for complete exit of {symbol}: {e}")

        return qty

    def _create_error_dto(
        self,
        order_id: str,
        symbol: str,
        side: str,
        qty: float | None,
        error_message: str,
    ) -> ExecutedOrderDTO:
        """Create error ExecutedOrderDTO for failed orders.

        Args:
            order_id: Error order ID
            symbol: Stock symbol
            side: Order side
            qty: Order quantity
            error_message: Error description

        Returns:
            ExecutedOrderDTO with error details

        """
        return ExecutedOrderDTO(
            order_id=order_id,
            symbol=symbol.upper() if symbol else "UNKNOWN",
            action=side.upper() if side and side.upper() in ["BUY", "SELL"] else "BUY",
            quantity=Decimal(str(qty)) if qty and qty > 0 else Decimal("0.01"),
            filled_quantity=Decimal("0"),
            price=Decimal("0.01"),
            total_value=Decimal("0.01"),  # Must be > 0
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=error_message,
        )

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrderDTO:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use actual available quantity

        Returns:
            ExecutedOrderDTO with execution details

        """
        try:
            # Validation
            normalized_symbol, side_normalized = self._validate_market_order_params(
                symbol, side, qty, notional
            )

            # Adjust quantity for complete exits
            final_qty = self._adjust_quantity_for_complete_exit(
                normalized_symbol,
                side_normalized,
                qty,
                is_complete_exit=is_complete_exit,
            )

            # Use trading service to place the order
            return self._get_trading_service().place_market_order(
                normalized_symbol,
                side_normalized,
                final_qty,
                notional,
                is_complete_exit=is_complete_exit,
            )

        except ValueError as e:
            logger.error(f"Invalid order parameters: {e}")
            return self._create_error_dto("INVALID", symbol, side, qty, str(e))
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return self._create_error_dto("FAILED", symbol, side, qty, str(e))

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> OrderExecutionResult:
        """Place a limit order with validation and DTO conversion.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')

        Returns:
            OrderExecutionResult with execution details

        """
        return self._get_trading_service().place_limit_order(
            symbol, side, quantity, limit_price, time_in_force
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        return self._get_trading_service().cancel_order(order_id)

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status."""
        return self._get_trading_service().get_orders(status)

    # Market Data Operations
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.

        TODO: Consider migrating callers to use structured pricing types:
        - RealTimePricingService.get_quote_data() for bid/ask spreads with market depth
        - RealTimePricingService.get_price_data() for volume and enhanced trade data
        - Enhanced price discovery with QuoteModel and PriceDataModel
        """
        return self._market_data_service.get_current_price(symbol)

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        """
        return self._market_data_service.get_current_prices(symbols)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices, or None if not available.

        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                bid = float(getattr(quote, "bid_price", 0))
                ask = float(getattr(quote, "ask_price", 0))

                # Allow quotes where we have at least a valid bid or ask
                # This handles cases like LEU where bid exists but ask is 0
                if bid > 0 or ask > 0:
                    # If only one side is available, use it for both bid and ask
                    # This allows trading while acknowledging the spread uncertainty
                    if bid > 0 and ask <= 0:
                        logger.info(
                            f"Using bid price for both bid/ask for {symbol} (ask unavailable)"
                        )
                        return (bid, bid)
                    if ask > 0 and bid <= 0:
                        logger.info(
                            f"Using ask price for both bid/ask for {symbol} (bid unavailable)"
                        )
                        return (ask, ask)
                    # Both bid and ask are available and positive
                    return (bid, ask)

            logger.warning(f"No valid quote data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol (MarketDataRepository interface).

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed

        """
        return self._market_data_service.get_quote(symbol)

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)

        Returns:
            List of dictionaries with bar data using Pydantic model field names

        """
        return self._market_data_service.get_historical_bars(
            symbol, start_date, end_date, timeframe
        )

    # Utility Methods
    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working."""
        return self._account_service.validate_connection()

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        return self._account_service.get_buying_power()

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        return self._account_service.get_portfolio_value()

    # Additional methods to match interface contracts

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol

        Returns:
            True if successful, False otherwise.

        """
        try:
            if symbol:
                # Get orders for specific symbol and cancel them
                orders = self.get_orders(status="open")
                symbol_orders = [
                    order for order in orders if getattr(order, "symbol", None) == symbol
                ]
                for order in symbol_orders:
                    order_id = getattr(order, "id", None)
                    if order_id:
                        self.cancel_order(str(order_id))
            else:
                # Cancel all open orders
                self._trading_client.cancel_orders()

            logger.info("Successfully cancelled orders" + (f" for {symbol}" if symbol else ""))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False

    def cancel_stale_orders(self, timeout_minutes: int = 30) -> dict[str, Any]:
        """Cancel orders older than the specified timeout.

        Args:
            timeout_minutes: Orders older than this many minutes will be cancelled

        Returns:
            Dictionary containing:
            - cancelled_count: Number of orders cancelled
            - errors: List of any errors encountered
            - cancelled_orders: List of order IDs that were cancelled

        """
        try:
            cutoff_time = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
            open_orders = self.get_orders(status="open")

            logger.info(
                f"🔍 Checking {len(open_orders)} open orders for staleness (>{timeout_minutes} minutes)"
            )

            cancelled_orders, errors = self._process_stale_orders(open_orders, cutoff_time)
            result = self._build_stale_orders_result(cancelled_orders, errors)
            self._log_stale_orders_result(cancelled_orders)

            return result

        except Exception as e:
            error_msg = f"Failed to cancel stale orders: {e}"
            logger.error(error_msg)
            return {
                "cancelled_count": 0,
                "errors": [error_msg],
                "cancelled_orders": [],
            }

    def _process_stale_orders(
        self, open_orders: list[Any], cutoff_time: datetime
    ) -> tuple[list[str], list[str]]:
        """Process open orders and cancel stale ones.

        Args:
            open_orders: List of open orders to check
            cutoff_time: Cutoff time for staleness

        Returns:
            Tuple of (cancelled_orders, errors) lists

        """
        cancelled_orders = []
        errors = []
        current_time = datetime.now(UTC)

        for order in open_orders:
            try:
                if self._should_cancel_stale_order(order, cutoff_time, current_time):
                    order_id = str(getattr(order, "id", "unknown"))
                    if self.cancel_order(order_id):
                        cancelled_orders.append(order_id)
                    else:
                        errors.append(f"Failed to cancel order {order_id}")

            except Exception as e:
                order_id = str(getattr(order, "id", "unknown"))
                error_msg = f"Error processing order {order_id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return cancelled_orders, errors

    def _should_cancel_stale_order(
        self,
        order: Order | dict[str, Any],
        cutoff_time: datetime,
        current_time: datetime,
    ) -> bool:
        """Check if an order should be cancelled for being stale.

        Args:
            order: Order object to check
            cutoff_time: Cutoff time for staleness
            current_time: Current time for age calculation

        Returns:
            True if order should be cancelled

        """
        submitted_at = getattr(order, "submitted_at", None)
        if not submitted_at:
            return False

        # Handle string timestamps
        if isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at.replace("Z", UTC_TIMEZONE_SUFFIX))

        # Check if order is stale
        if submitted_at < cutoff_time:
            order_id = str(getattr(order, "id", "unknown"))
            symbol = getattr(order, "symbol", "unknown")
            age_minutes = (current_time - submitted_at).total_seconds() / 60

            logger.info(
                f"🗑️ Cancelling stale order {order_id} for {symbol} (age: {age_minutes:.1f} minutes)"
            )
            return True

        return False

    def _build_stale_orders_result(
        self, cancelled_orders: list[str], errors: list[str]
    ) -> dict[str, Any]:
        """Build result dictionary for stale orders operation."""
        return {
            "cancelled_count": len(cancelled_orders),
            "errors": errors,
            "cancelled_orders": cancelled_orders,
        }

    def _log_stale_orders_result(self, cancelled_orders: list[str]) -> None:
        """Log the result of stale orders cancellation."""
        if cancelled_orders:
            logger.info(f"✅ Cancelled {len(cancelled_orders)} stale orders: {cancelled_orders}")
        else:
            logger.info("✅ No stale orders found to cancel")

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed.

        """
        try:
            order = self._trading_client.close_position(symbol)
            order_id = str(getattr(order, "id", "unknown"))
            logger.info(f"Successfully liquidated position for {symbol}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Failed to liquidate position for {symbol}: {e}")
            return None

    def get_asset_info(self, symbol: str) -> AssetInfoDTO | None:
        """Get asset information with caching.

        Args:
            symbol: Stock symbol

        Returns:
            AssetInfoDTO with asset metadata, or None if not found.

        """
        symbol_upper = symbol.upper()
        current_time = time.time()

        # Check cache first
        with self._asset_cache_lock:
            if symbol_upper in self._asset_cache:
                cache_time = self._asset_cache_timestamps.get(symbol_upper, 0)
                if current_time - cache_time < self._asset_cache_ttl:
                    logger.debug(f"📋 Asset cache hit for {symbol_upper}")
                    return self._asset_cache[symbol_upper]
                # Cache expired, remove
                self._asset_cache.pop(symbol_upper, None)
                self._asset_cache_timestamps.pop(symbol_upper, None)
                logger.debug(f"🗑️ Asset cache expired for {symbol_upper}")

        try:
            asset = self._trading_client.get_asset(symbol_upper)

            # Convert SDK object to DTO at adapter boundary
            asset_dto = AssetInfoDTO(
                symbol=getattr(asset, "symbol", symbol_upper),
                name=getattr(asset, "name", None),
                exchange=getattr(asset, "exchange", None),
                asset_class=getattr(asset, "asset_class", None),
                tradable=getattr(asset, "tradable", True),
                fractionable=getattr(asset, "fractionable", True),
                marginable=getattr(asset, "marginable", None),
                shortable=getattr(asset, "shortable", None),
            )

            # Cache the result
            with self._asset_cache_lock:
                self._asset_cache[symbol_upper] = asset_dto
                self._asset_cache_timestamps[symbol_upper] = current_time

            logger.debug(
                f"📡 Fetched asset info for {symbol_upper}: fractionable={asset_dto.fractionable}"
            )
            return asset_dto

        except Exception as e:
            logger.error(f"Failed to get asset info for {symbol_upper}: {e}")
            return None

    def is_fractionable(self, symbol: str) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Stock symbol to check

        Returns:
            True if asset supports fractional shares, False otherwise.
            Defaults to True if asset info cannot be retrieved.

        """
        asset_info = self.get_asset_info(symbol)
        if asset_info is None:
            logger.warning(f"Could not determine fractionability for {symbol}, defaulting to True")
            return True
        return asset_info.fractionable

    def is_market_open(self) -> bool:
        """Check if the market is currently open.

        Returns:
            True if market is open, False otherwise.

        """
        try:
            clock = self._trading_client.get_clock()
            return getattr(clock, "is_open", False)
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return False

    def get_market_calendar(self, _start_date: str, _end_date: str) -> list[dict[str, Any]]:
        """Get market calendar information.

        Args:
            _start_date: Start date (ISO format) - currently unused
            _end_date: End date (ISO format) - currently unused

        Returns:
            List of market calendar entries.

        """
        try:
            # Some stubs may not accept start/end; fetch without filters
            calendar = self._trading_client.get_calendar()
            # Convert to list of dictionaries
            return [
                {
                    "date": str(getattr(day, "date", "")),
                    "open": str(getattr(day, "open", "")),
                    "close": str(getattr(day, "close", "")),
                }
                for day in calendar
            ]
        except Exception as e:
            logger.error(f"Failed to get market calendar: {e}")
            return []

    def get_portfolio_history(
        self,
        _start_date: str | None = None,
        _end_date: str | None = None,
        timeframe: str = "1Day",
    ) -> dict[str, Any] | None:
        """Get portfolio performance history."""
        return self._account_service.get_portfolio_history(_start_date, _end_date, timeframe)

    def get_activities(
        self,
        activity_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get account activities (trades, dividends, etc.)."""
        return self._account_service.get_activities(activity_type, start_date, end_date)

    # OrderExecutor protocol implementation methods

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using execution manager.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed

        """
        return self._get_trading_service().place_smart_sell_order(symbol, qty)

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity.

        This is an alias for get_positions_dict() to satisfy OrderExecutor protocol.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        return self.get_positions_dict()

    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state.

        Args:
            order_id: The order ID to check

        Returns:
            Order status if completed, None if still pending or error occurred

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            order_status = getattr(order, "status", "").upper()

            # Check if order is in a final state
            if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                return order_status
            return None
        except Exception as e:
            logger.warning(f"Failed to check order {order_id} status: {e}")
            return None

    def _process_pending_orders(self, order_ids: list[str], completed_orders: list[str]) -> None:
        """Process pending orders and update completed_orders list.

        Args:
            order_ids: All order IDs to monitor
            completed_orders: List of completed order IDs (modified in place)

        """
        for order_id in order_ids:
            if order_id not in completed_orders:
                final_status = self._check_order_completion_status(order_id)
                if final_status:
                    completed_orders.append(order_id)
                    logger.info(f"Order {order_id} completed with status: {final_status}")

    def _should_continue_waiting(
        self,
        completed_orders: list[str],
        order_ids: list[str],
        start_time: float,
        max_wait_seconds: int,
    ) -> bool:
        """Check if we should continue waiting for order completion.

        Args:
            completed_orders: List of completed order IDs
            order_ids: All order IDs being monitored
            start_time: When monitoring started
            max_wait_seconds: Maximum wait time

        Returns:
            True if should continue waiting, False otherwise

        """
        return (
            len(completed_orders) < len(order_ids) and (time.time() - start_time) < max_wait_seconds
        )

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using TradingStream (with polling fallback).

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResult with completion status and completed order IDs

        """
        return self._get_trading_service().wait_for_order_completion(order_ids, max_wait_seconds)

    # ---- TradingStream helpers ----
    def _ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running via WebSocketConnectionManager."""
        if self._trading_service_active:
            return

        try:
            # Import here to avoid circular dependency
            from the_alchemiser.shared.services.websocket_manager import (
                WebSocketConnectionManager,
            )

            # Get or create the shared WebSocket manager
            if self._websocket_manager is None:
                self._websocket_manager = WebSocketConnectionManager(
                    self._api_key, self._secret_key, paper_trading=self._paper
                )

            # Request trading service from the manager
            if self._websocket_manager.get_trading_service(self._on_order_update):
                self._trading_service_active = True
                logger.info("✅ TradingStream service activated via WebSocketConnectionManager")
            else:
                logger.error("❌ Failed to activate TradingStream service")

        except Exception as exc:
            logger.error(f"Failed to ensure TradingStream via WebSocketConnectionManager: {exc}")
            self._trading_service_active = False

    def _extract_event_and_order(
        self, data: dict[str, Any] | object
    ) -> tuple[str, dict[str, Any] | object | None]:
        """Extract event type and order from data (SDK model or dict).

        Args:
            data: Stream data from TradingStream callback

        Returns:
            Tuple of (event_type, order) where order may be None

        """
        if hasattr(data, "event"):
            event_type = str(getattr(data, "event", "")).lower()
            order = getattr(data, "order", None)
        else:
            event_type = str(data.get("event", "")).lower() if isinstance(data, dict) else ""
            order = data.get("order") if isinstance(data, dict) else None
        return event_type, order

    def _extract_order_info(
        self, order: dict[str, Any] | object | None
    ) -> tuple[str | None, str | None, Decimal | None]:
        """Extract order ID, status, and average price from order object.

        Args:
            order: Order object (SDK model or dict, may be None)

        Returns:
            Tuple of (order_id, status, avg_price) where any may be None

        """
        if order is None:
            return None, None, None

        order_id = str(
            getattr(order, "id", "") or (order.get("id") if isinstance(order, dict) else "")
        )
        status = str(
            getattr(order, "status", "") or (order.get("status") if isinstance(order, dict) else "")
        ).lower()

        avg_price = self._convert_avg_price(order)

        return order_id if order_id else None, status if status else None, avg_price

    def _convert_avg_price(self, order: dict[str, Any] | object) -> Decimal | None:
        """Convert average price from order to Decimal.

        Args:
            order: Order object (SDK model or dict)

        Returns:
            Average price as Decimal or None if conversion fails

        """
        avg_raw = (
            getattr(order, "filled_avg_price", None)
            if not isinstance(order, dict)
            else order.get("filled_avg_price")
        )

        if avg_raw is not None:
            try:
                return Decimal(str(avg_raw))
            except Exception:
                return None
        return None

    def _is_terminal_event(self, event_type: str, status: str | None) -> bool:
        """Check if the event/status indicates a terminal order state.

        Args:
            event_type: The event type from the stream
            status: The order status (may be None)

        Returns:
            True if this is a terminal event requiring event signaling

        """
        final_events = {"fill", "canceled", "rejected", "expired"}
        final_statuses = {"filled", "canceled", "rejected", "expired"}

        return (
            event_type in final_events
            or (status is not None and status in final_events)
            or (status is not None and status in final_statuses)
        )

    async def _on_order_update(self, data: dict[str, Any] | object) -> None:
        """Order update callback for TradingStream (async).

        Handles both SDK models and dict payloads. Must be async for TradingStream.
        """
        try:
            event_type, order = self._extract_event_and_order(data)
            order_id, status, avg_price = self._extract_order_info(order)

            if not order_id:
                return

            # Update order tracking
            self._order_status[order_id] = status or event_type or ""
            self._order_avg_price[order_id] = avg_price

            # Handle terminal events
            if self._is_terminal_event(event_type, status):
                evt = self._order_events.get(order_id)
                if evt:
                    # Safe to set from event loop thread; non-blocking
                    evt.set()
        except Exception as exc:
            logger.error(f"Error in TradingStream order update: {exc}")

    def _wait_for_orders_via_ws(self, order_ids: list[str], timeout: float) -> list[str]:
        """Use TradingStream updates to wait for orders to complete within timeout."""
        self._ensure_trading_stream()

        # Ensure events exist for ids
        events: dict[str, threading.Event] = {}
        for oid in order_ids:
            evt = self._order_events.get(oid)
            if not evt:
                evt = threading.Event()
                self._order_events[oid] = evt
            events[oid] = evt

        start = time.time()
        completed: list[str] = []

        # Check cached statuses first
        for oid in order_ids:
            status = (self._order_status.get(oid, "") or "").lower()
            if status in {"filled", "canceled", "rejected", "expired"}:
                completed.append(oid)

        # Wait for the rest
        for oid in order_ids:
            if oid in completed:
                continue
            time_left = timeout - (time.time() - start)
            if time_left <= 0:
                break
            evt = events.get(oid)
            if evt and evt.wait(timeout=time_left):
                completed.append(oid)

        return completed

    # Note: MarketDataPort implementation removed to avoid protocol compliance issues
    # AlpacaManager provides market data functionality through direct methods
    # without implementing the full MarketDataPort protocol

    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all AlpacaManager instances and their WebSocket connections."""
        with cls._lock:
            cls._cleanup_in_progress = True
            try:
                # Create a copy of instances to avoid dictionary modification during iteration
                instances_to_cleanup = list(cls._instances.values())

                for instance in instances_to_cleanup:
                    try:
                        # Clean up trading service
                        if hasattr(instance, "_trading_service") and instance._trading_service:
                            instance._trading_service.cleanup()
                            instance._trading_service = None

                        # Release trading service from WebSocketConnectionManager
                        if hasattr(instance, "_websocket_manager") and instance._websocket_manager:
                            logger.info(
                                "Releasing TradingStream service from WebSocketConnectionManager"
                            )
                            instance._websocket_manager.release_trading_service()
                            instance._trading_service_active = False
                    except Exception as e:
                        logger.error(f"Error cleaning up AlpacaManager instance: {e}")

                cls._instances.clear()
                logger.info("All AlpacaManager instances cleaned up")
            finally:
                cls._cleanup_in_progress = False

    @classmethod
    def get_connection_health(cls) -> dict[str, Any]:
        """Get health status of all AlpacaManager instances."""
        with cls._lock:
            health_info: dict[str, Any] = {
                "total_instances": len(cls._instances),
                "cleanup_in_progress": cls._cleanup_in_progress,
                "instances": {},
            }

            for key, instance in cls._instances.items():
                try:
                    health_info["instances"][key] = {
                        "paper_trading": instance._paper,
                        "trading_service_active": getattr(
                            instance, "_trading_service_active", False
                        ),
                        "initialized": getattr(instance, "_initialized", False),
                        "websocket_manager_available": getattr(instance, "_websocket_manager", None)
                        is not None,
                    }
                except Exception as e:
                    health_info["instances"][key] = {"status": "error", "error": str(e)}

            return health_info

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AlpacaManager(paper={self._paper})"


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, *, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """Create an AlpacaManager instance.

    This function provides a clean way to create AlpacaManager instances
    and can be easily extended with additional configuration options.
    """
    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url)
