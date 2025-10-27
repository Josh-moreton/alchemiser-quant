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

Architecture Notes:
==================
This module uses a **Singleton Facade Pattern** that requires some imports to be
deferred to runtime (inside __init__) to break circular dependencies. This is an
intentional design trade-off documented in docs/adr/ADR-001-circular-imports.md.

Circular Import Dependencies:
- WebSocketConnectionManager is imported inside __init__ (line ~248)
- MarketDataService is imported inside __init__ (line ~264)

This pattern is SAFE because:
1. Imports occur after module and class definitions are complete
2. __init__ runs once per credential set (singleton behavior)
3. No module-level code dependencies exist
4. Extensively tested for thread-safety and correctness

Import Order Requirements:
- AlpacaManager implements repository protocols (TradingRepository, etc.)
- Services depend on these protocol implementations
- Therefore, services MUST be imported after AlpacaManager is fully defined
- DO NOT move these imports to module level

See docs/adr/ADR-001-circular-imports.md for full architectural rationale.
"""

from __future__ import annotations

import hashlib
import threading
import warnings
from decimal import Decimal
from typing import Any, ClassVar

# Type checking imports to avoid circular dependencies
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Position, TradeAccount
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    ReplaceOrderRequest,
)

from the_alchemiser.shared.brokers.alpaca_utils import (
    create_data_client,
    create_trading_client,
)
from the_alchemiser.shared.errors import SymbolValidationError, ValidationError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.shared.schemas.asset_info import AssetInfo
from the_alchemiser.shared.schemas.broker import (
    OrderExecutionResult,
    WebSocketResult,
)
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.operations import OrderCancellationResult
from the_alchemiser.shared.services.alpaca_account_service import AlpacaAccountService
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService
from the_alchemiser.shared.services.asset_metadata_service import AssetMetadataService
from the_alchemiser.shared.types.market_data import QuoteModel
from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler

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


logger = get_logger(__name__)


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

    Security Note:
        Credentials are stored internally for SDK usage but are hashed (SHA-256)
        when used as dictionary keys. Raw credentials are never logged or exposed
        in debug output.
    """

    _instances: ClassVar[dict[str, AlpacaManager]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _cleanup_event: ClassVar[threading.Event] = threading.Event()
    _cleanup_in_progress: ClassVar[bool] = False
    _initialized: bool

    @staticmethod
    def _hash_credentials(
        api_key: str, secret_key: str, *, paper: bool, base_url: str | None = None
    ) -> str:
        """Create deterministic instance key from credentials.

        Args:
            api_key: API key
            secret_key: Secret key
            paper: Paper trading flag
            base_url: Optional base URL

        Returns:
            SHA-256 hash of credentials for use as dictionary key

        Security Note:
            This is NOT a security measure. This method creates a deterministic
            hash for singleton instance deduplication only. The credentials are
            stored in memory in plain text (self._api_key, self._secret_key) for
            SDK usage.

            Purpose: Enable singleton pattern for connection pooling.
            Threat Model: Does not protect credentials. If an attacker has memory
            access to read this hash, they already have access to read the plain
            text credentials stored in the same process.

            The hash simply prevents credential exposure in:
            - Dictionary key iteration/inspection
            - Debug output of _instances dictionary
            - Accidental logging of _instances keys

        """
        credentials_str = f"{api_key}:{secret_key}:{paper}:{base_url}"
        return hashlib.sha256(credentials_str.encode()).hexdigest()

    def __new__(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> AlpacaManager:
        """Create or return existing instance for the given credentials.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
            base_url: Optional base URL

        Returns:
            Singleton instance for the credential set

        Note:
            Credentials are hashed before being used as dictionary keys
            for security. The cleanup event is used instead of busy-wait
            polling for better performance and responsiveness.

        """
        credentials_key = cls._hash_credentials(api_key, secret_key, paper=paper, base_url=base_url)

        with cls._lock:
            # Wait for cleanup to complete using Event (non-busy wait)
            if cls._cleanup_in_progress:
                cls._cleanup_event.clear()
            # Release lock while waiting
            if cls._cleanup_in_progress:
                cls._lock.release()
                cls._cleanup_event.wait(timeout=5.0)
                cls._lock.acquire()

            if credentials_key not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[credentials_key] = instance
                instance._initialized = False
                instance._credentials_hash = credentials_key
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
            api_key: Alpaca API key (stored internally, not logged)
            secret_key: Alpaca secret key (stored internally, not logged)
            paper: Whether to use paper trading (default: True)
            base_url: Optional base URL for Alpaca API

        Note:
            Credentials are stored for SDK usage but never logged.
            Only credential hashes are used for identification and logging.

        Security Warning:
            Credentials are stored in memory for the lifetime of this instance.
            Ensure proper cleanup using cleanup_all_instances() when shutting down.

        """
        # Skip initialization if already initialized (singleton pattern)
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Store credentials securely (not logged) - hash is set in __new__
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = base_url
        self._credentials_hash: str  # Set in __new__, type annotation for mypy

        # Initialize clients using factory functions from alpaca_utils
        try:
            # Use factory functions for consistent error handling and logging
            self._trading_client = create_trading_client(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper,
            )

            self._data_client = create_data_client(
                api_key=api_key,
                secret_key=secret_key,
            )

            logger.debug(
                "AlpacaManager initialized",
                paper=paper,
                credentials_hash=self._credentials_hash[:16],  # Only log first 16 chars
            )

        except Exception as e:
            logger.error("Failed to initialize Alpaca clients", error=str(e))
            raise

        # Initialize WebSocket manager for centralized WebSocket management
        # NOTE: Imported inside __init__ to break circular dependency
        # See docs/adr/ADR-001-circular-imports.md for architectural rationale
        # DO NOT move this import to module level - it will cause import-time circular dependency
        from the_alchemiser.shared.services.websocket_manager import (
            WebSocketConnectionManager,
        )

        self._websocket_manager = WebSocketConnectionManager(
            self._api_key, self._secret_key, paper_trading=self._paper
        )

        # Initialize extracted services
        self._account_service = AlpacaAccountService(self._trading_client)
        self._trading_service = AlpacaTradingService(
            self._trading_client, self._websocket_manager, paper_trading=self._paper
        )
        self._asset_metadata_service = AssetMetadataService(self._trading_client)

        # Initialize MarketDataService for delegation
        # NOTE: Imported inside __init__ to break circular dependency
        # See docs/adr/ADR-001-circular-imports.md for architectural rationale
        # MarketDataService requires a repository implementing MarketDataRepository (which this class does)
        # DO NOT move this import to module level - it will cause import-time circular dependency
        from the_alchemiser.shared.services.market_data_service import MarketDataService

        self._market_data_service = MarketDataService(self)

        # Mark as initialized to prevent re-initialization
        self._initialized = True

    @property
    def is_paper_trading(self) -> bool:
        """Return True if using paper trading."""
        return self._paper

    # Public, read-only accessors for credentials and mode (for factories/streams)
    @property
    def api_key(self) -> str:
        """Return the API key (read-only).

        Deprecated:
            Direct credential access is discouraged. This property is maintained
            for backward compatibility but will be removed in a future version.
            Use service injection or dependency injection patterns instead.

        Security Warning:
            Accessing credentials directly increases attack surface. Prefer
            using the higher-level service methods that don't require raw credentials.

        Returns:
            API key string

        """
        warnings.warn(
            "Direct access to api_key property is deprecated and will be removed. "
            "Use dependency injection or service patterns instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Return the secret key (read-only).

        Deprecated:
            Direct credential access is discouraged. This property is maintained
            for backward compatibility but will be removed in a future version.
            Use service injection or dependency injection patterns instead.

        Security Warning:
            Accessing credentials directly increases attack surface. Prefer
            using the higher-level service methods that don't require raw credentials.

        Returns:
            Secret key string

        """
        warnings.warn(
            "Direct access to secret_key property is deprecated and will be removed. "
            "Use dependency injection or service patterns instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._secret_key

    @property
    def paper(self) -> bool:
        """Return whether paper/live mode is enabled."""
        return self._paper

    @property
    def trading_client(self) -> TradingClient:
        """Return underlying trading client for backward compatibility."""
        return self._trading_client

    def get_data_client(self) -> StockHistoricalDataClient:
        """Return data client for market data access.

        Returns:
            StockHistoricalDataClient for market data operations

        """
        return self._data_client

    def _get_trading_service(self) -> AlpacaTradingService:
        """Get the trading service."""
        return self._trading_service

    # Trading Operations
    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dict (protocol compliance)."""
        return self._account_service.get_account_dict()

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object."""
        return self._account_service.get_account_object()

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects (AccountRepository interface)."""
        return self._account_service.get_positions()

    def get_all_positions(self) -> list[Any]:
        """Alias for `get_positions()` to mirror Alpaca SDK naming."""
        return self._account_service.get_all_positions()

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all positions as dict mapping symbol to quantity."""
        return self._account_service.get_positions_dict()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        return self._account_service.get_position(symbol)

    def place_order(self, order_request: LimitOrderRequest | MarketOrderRequest) -> ExecutedOrder:
        """Place an order and return execution details."""
        return self._get_trading_service().place_order(order_request)

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result schema.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResult reflecting the latest known state.

        """
        return self._get_trading_service().get_order_execution_result(order_id)

    def _validate_market_order_params(
        self, symbol: str, side: str, qty: float | None, notional: float | None
    ) -> tuple[str, str]:
        """Validate market order parameters."""
        if not symbol or not symbol.strip():
            raise SymbolValidationError(
                "Symbol cannot be empty", symbol=symbol, reason="Empty or whitespace"
            )
        if qty is None and notional is None:
            raise ValidationError(
                "Either qty or notional must be specified", field_name="qty_or_notional"
            )
        if qty is not None and notional is not None:
            raise ValidationError(
                "Cannot specify both qty and notional", field_name="qty_and_notional"
            )
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be positive", field_name="qty", value=qty)
        if notional is not None and notional <= 0:
            raise ValidationError(
                "Notional amount must be positive", field_name="notional", value=notional
            )

        side_normalized = side.lower().strip()
        if side_normalized not in ["buy", "sell"]:
            raise ValidationError("Side must be 'buy' or 'sell'", field_name="side", value=side)

        return symbol.upper(), side_normalized

    def _adjust_quantity_for_complete_exit(
        self, symbol: str, side: str, qty: float | None, *, is_complete_exit: bool
    ) -> float | None:
        """Adjust quantity for complete exit if needed."""
        if not (is_complete_exit and side == "sell" and qty is not None):
            return qty

        try:
            position = self.get_position(symbol)
            if position:
                # Use qty_available if available, fallback to qty
                available_qty = getattr(position, "qty_available", None) or getattr(
                    position, "qty", None
                )
                if available_qty:
                    return float(available_qty)
        except Exception as e:
            logger.warning(
                "Failed to get position for complete exit of",
                symbol=symbol,
                error=str(e),
            )

        return qty

    def _place_market_order_internal(
        self,
        symbol: str,
        side: str,
        qty: Decimal | None,
        notional: Decimal | None,
        *,
        is_complete_exit: bool,
    ) -> ExecutedOrder:
        """Place internal market order with testable logic.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade as Decimal
            notional: Dollar amount to trade as Decimal
            is_complete_exit: If True and side is 'sell', use actual available quantity

        Returns:
            ExecutedOrder with execution details and status

        """
        # Convert Decimal to float for internal processing
        qty_float = float(qty) if qty is not None else None
        notional_float = float(notional) if notional is not None else None

        # Validation
        normalized_symbol, side_normalized = self._validate_market_order_params(
            symbol, side, qty_float, notional_float
        )

        # Adjust quantity for complete exits
        final_qty = self._adjust_quantity_for_complete_exit(
            normalized_symbol,
            side_normalized,
            qty_float,
            is_complete_exit=is_complete_exit,
        )

        # Use trading service to place the order
        return self._get_trading_service().place_market_order(
            normalized_symbol,
            side_normalized,
            final_qty,
            notional_float,
            is_complete_exit=is_complete_exit,
        )

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: Decimal | None = None,
        notional: Decimal | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrder:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade as Decimal (use either qty OR notional)
            notional: Dollar amount to trade as Decimal (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use actual available quantity

        Returns:
            ExecutedOrder with execution details and status.

        """
        return AlpacaErrorHandler.handle_market_order_errors(
            symbol,
            side,
            float(qty) if qty is not None else None,
            lambda: self._place_market_order_internal(
                symbol, side, qty, notional, is_complete_exit=is_complete_exit
            ),
        )

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> OrderExecutionResult:
        """Place a limit order with validation and schema conversion.

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

    def cancel_order(self, order_id: str) -> OrderCancellationResult:
        """Cancel an order by ID.

        Returns:
            OrderCancellationResult with detailed cancellation status

        """
        return self._get_trading_service().cancel_order(order_id)

    def replace_order(
        self, order_id: str, order_data: ReplaceOrderRequest | None = None
    ) -> OrderExecutionResult:
        """Replace an order with new parameters.

        Args:
            order_id: The unique order ID to replace
            order_data: The parameters to update (quantity, limit_price, etc.)

        Returns:
            OrderExecutionResult with the updated order details

        """
        return self._get_trading_service().replace_order(order_id, order_data)

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status."""
        return self._get_trading_service().get_orders(status)

    # Market Data Operations
    def get_current_price(self, symbol: str) -> Decimal | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.

        Note: Migrating callers to the structured pricing services would unlock richer
        market context:
        - RealTimePricingService.get_quote_data() surfaces bid/ask spreads with market depth
        - RealTimePricingService.get_price_data() adds volume and enhanced trade data
        - Enhanced price discovery with QuoteModel and PriceDataModel becomes possible

        Args:
            symbol: Stock symbol

        Returns:
            Current price as Decimal for financial precision, or None if unavailable.

        """
        price = self._market_data_service.get_current_price(symbol)
        if price is None:
            return None

        # Defensive: handle both Decimal and float returns from service layer
        # MarketDataService.get_current_price() currently returns float, but we convert
        # to Decimal here for financial precision and to handle potential future changes
        if isinstance(price, Decimal):
            return price
        return Decimal(str(price))  # Convert via string to avoid float precision issues

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        """
        return self._market_data_service.get_current_prices(symbols)

    def get_latest_quote(self, symbol: str) -> QuoteModel | None:
        """Get latest bid/ask quote for a symbol (delegates to MarketDataService).

        Args:
            symbol: Stock symbol

        Returns:
            Enhanced QuoteModel with bid/ask prices and sizes, or None if not available.

        """
        from the_alchemiser.shared.value_objects.symbol import Symbol

        symbol_obj = Symbol(value=symbol.upper())
        return self._market_data_service.get_latest_quote(symbol_obj)

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

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power."""
        return self._account_service.get_buying_power()

    def get_portfolio_value(self) -> Decimal | None:
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
        return self._get_trading_service().cancel_all_orders(symbol)

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API (delegates to TradingService).

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed.

        """
        return self._get_trading_service().liquidate_position(symbol)

    def close_all_positions(self, *, cancel_orders: bool = True) -> list[dict[str, Any]]:
        """Liquidate all positions for an account (delegates to TradingService).

        Places an order for each open position to liquidate.

        Args:
            cancel_orders: If True, cancel all open orders before liquidating positions

        Returns:
            List of responses from each closed position containing status and order info

        """
        return self._get_trading_service().close_all_positions(cancel_orders=cancel_orders)

    def get_asset_info(self, symbol: str) -> AssetInfo | None:
        """Get asset information with caching.

        Args:
            symbol: Stock symbol

        Returns:
            AssetInfo or None if not found

        Raises:
            ValidationError: If symbol is invalid
            TradingClientError: If API call fails (other than not found)

        """
        return self._asset_metadata_service.get_asset_info(symbol)

    def is_fractionable(self, symbol: str) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Stock symbol

        Returns:
            True if fractionable, False otherwise

        Raises:
            ValidationError: If symbol is invalid
            DataProviderError: If asset not found
            TradingClientError: If API call fails

        """
        return self._asset_metadata_service.is_fractionable(symbol)

    def is_market_open(self) -> bool:
        """Check if the market is currently open.

        Returns:
            True if market is open, False otherwise.

        Raises:
            TradingClientError: If API call fails

        """
        return self._asset_metadata_service.is_market_open()

    def get_market_calendar(self) -> list[dict[str, Any]]:
        """Get market calendar information.

        Returns:
            List of market calendar entries.

        Raises:
            TradingClientError: If API call fails

        """
        return self._asset_metadata_service.get_market_calendar()

    def get_portfolio_history(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        timeframe: str = "1Day",
        period: str | None = None,
    ) -> dict[str, Any] | None:
        """Get portfolio performance history."""
        return self._account_service.get_portfolio_history(
            start_date=start_date, end_date=end_date, timeframe=timeframe, period=period
        )

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

    def get_current_positions(self) -> dict[str, Decimal]:
        """Get all current positions as dict mapping symbol to quantity.

        This is an alias for get_positions_dict() to satisfy OrderExecutor protocol.

        Returns:
            Dictionary mapping symbol to quantity (as Decimal) owned.
            Only includes non-zero positions.

        """
        return self.get_positions_dict()

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

    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state (delegates to TradingService).

        Args:
            order_id: Order ID to check

        Returns:
            Order status if in final state, None otherwise

        Deprecated:
            This method exposes internal implementation details and should not be
            used outside of this class. It is maintained for backward compatibility
            with existing tests but will be removed in a future version.

        """
        warnings.warn(
            "_check_order_completion_status is an internal method and will be removed. "
            "Use public API methods instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._get_trading_service()._check_order_completion_status(order_id)

    def _ensure_trading_stream(self) -> None:
        """Ensure trading stream is active (delegates to TradingService).

        Deprecated:
            This method exposes internal implementation details and should not be
            used outside of this class. It is maintained for backward compatibility
            but will be removed in a future version.

        """
        warnings.warn(
            "_ensure_trading_stream is an internal method and will be removed. "
            "Use public API methods instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._get_trading_service()._ensure_trading_stream()

    # ---- TradingStream helpers ----

    @classmethod
    def cleanup_all_instances(cls) -> None:
        """Clean up all AlpacaManager instances and their WebSocket connections.

        Thread Safety:
            Uses Event-based signaling to prevent race conditions during cleanup.
            Other threads waiting in __new__ will be notified when cleanup completes.

        """
        with cls._lock:
            cls._cleanup_in_progress = True
            cls._cleanup_event.clear()
            try:
                for instance in cls._instances.values():
                    try:
                        if hasattr(instance, "_trading_service") and instance._trading_service:
                            instance._trading_service.cleanup()
                        if hasattr(instance, "_websocket_manager") and instance._websocket_manager:
                            instance._websocket_manager.release_trading_service()
                    except Exception as e:
                        logger.error(
                            "Error cleaning up AlpacaManager instance",
                            error=str(e),
                            credentials_hash=getattr(instance, "_credentials_hash", "unknown")[:16],
                        )
                cls._instances.clear()
                logger.info("All AlpacaManager instances cleaned up")
            finally:
                cls._cleanup_in_progress = False
                cls._cleanup_event.set()  # Signal waiting threads

    @classmethod
    def get_connection_health(cls) -> dict[str, Any]:
        """Get health status of all AlpacaManager instances."""
        with cls._lock:
            return {
                "total_instances": len(cls._instances),
                "cleanup_in_progress": cls._cleanup_in_progress,
                "instances": {
                    key: {
                        "paper_trading": instance._paper,
                        "initialized": getattr(instance, "_initialized", False),
                    }
                    for key, instance in cls._instances.items()
                },
            }

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

    Note: This factory function is maintained for backward compatibility and
    is used by the_alchemiser.shared.services.pnl_service.py. It adds minimal
    overhead and provides a stable public API for dependency injection.

    Usage:
        >>> manager = create_alpaca_manager(api_key="...", secret_key="...", paper=True)
    """
    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url)
