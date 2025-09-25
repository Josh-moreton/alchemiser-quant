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
import re
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from secrets import randbelow
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast

# Type checking imports to avoid circular dependencies
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.models import Order, Position, TradeAccount
from alpaca.trading.requests import (
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.dto.broker_dto import (
    OrderExecutionResult,
    WebSocketResult,
    WebSocketStatus,
)
from the_alchemiser.shared.schemas.execution.reports import ExecutedOrder
from the_alchemiser.shared.protocols.market_data import BarsIterable
from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.shared.schemas.system.assets import AssetInfo

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

        # Asset metadata cache with TTL
        self._asset_cache: dict[str, AssetInfo] = {}
        self._asset_cache_timestamps: dict[str, float] = {}
        self._asset_cache_ttl = 300.0  # 5 minutes TTL
        self._asset_cache_lock = threading.Lock()

        # Mark as initialized to prevent re-initialization
        self._initialized = True

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

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects (AccountRepository interface).

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

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
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

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrder:
        """Place an order and return execution details."""
        try:
            order = self._trading_client.submit_order(order_request)
            return self._create_success_order_dto(order, order_request)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return self._create_failed_order_dto(order_request, e)

    def _create_success_order_dto(
        self,
        order: Order | dict[str, Any],
        order_request: LimitOrderRequest | MarketOrderRequest,
    ) -> ExecutedOrder:
        """Create ExecutedOrder from successful order placement.

        Args:
            order: Successful order from Alpaca API
            order_request: Original order request

        Returns:
            ExecutedOrder with order details

        """
        # Extract basic order attributes
        order_data = self._extract_order_attributes(order)

        logger.info(
            f"Successfully placed order: {order_data['order_id']} for {order_data['symbol']}"
        )

        # Calculate price and total value
        price = self._calculate_order_price(order_data["filled_avg_price"], order_request)
        total_value = self._calculate_total_value(
            order_data["filled_qty_decimal"], order_data["order_qty_decimal"], price
        )

        return ExecutedOrder(
            order_id=order_data["order_id"],
            symbol=order_data["symbol"],
            action=order_data["action_value"],
            quantity=order_data["order_qty_decimal"],
            filled_quantity=order_data["filled_qty_decimal"],
            price=price,
            total_value=total_value,
            status=order_data["status_value"],
            execution_timestamp=datetime.now(UTC),
        )

    def _extract_order_attributes(self, order: Order | dict[str, Any]) -> dict[str, Any]:
        """Extract attributes from order object safely.

        Args:
            order: Order object from Alpaca API

        Returns:
            Dictionary with extracted attributes

        """
        order_id = str(getattr(order, "id", ""))
        order_symbol = str(getattr(order, "symbol", ""))
        order_qty = getattr(order, "qty", "0")
        order_filled_qty = getattr(order, "filled_qty", "0")
        order_filled_avg_price = getattr(order, "filled_avg_price", None)
        order_side = getattr(order, "side", "")
        order_status = getattr(order, "status", "SUBMITTED")

        # Extract enum values properly
        action_value = self._extract_enum_value(order_side)
        status_value = self._extract_enum_value(order_status)

        return {
            "order_id": order_id,
            "symbol": order_symbol,
            "filled_avg_price": order_filled_avg_price,
            "filled_qty_decimal": Decimal(str(order_filled_qty)),
            "order_qty_decimal": Decimal(str(order_qty)),
            "action_value": action_value,
            "status_value": status_value,
        }

    def _extract_enum_value(self, enum_obj: object) -> str:
        """Extract string value from enum object safely."""
        return enum_obj.value.upper() if hasattr(enum_obj, "value") else str(enum_obj).upper()

    def _calculate_order_price(
        self,
        filled_avg_price: float | None,
        order_request: LimitOrderRequest | MarketOrderRequest,
    ) -> Decimal:
        """Calculate order price from filled price or request."""
        # Handle price - use filled_avg_price if available, otherwise estimate
        if filled_avg_price:
            return Decimal(str(filled_avg_price))
        if hasattr(order_request, "limit_price") and order_request.limit_price:
            return Decimal(str(order_request.limit_price))
        return Decimal("0.01")  # Default minimal price

    def _calculate_total_value(
        self, filled_qty_decimal: Decimal, order_qty_decimal: Decimal, price: Decimal
    ) -> Decimal:
        """Calculate total value ensuring positive result for DTO validation."""
        if filled_qty_decimal > 0:
            return filled_qty_decimal * price
        return order_qty_decimal * price

    def _create_failed_order_dto(
        self, order_request: LimitOrderRequest | MarketOrderRequest, error: Exception
    ) -> ExecutedOrder:
        """Create ExecutedOrder for failed order placement.

        Args:
            order_request: Original order request
            error: Exception that occurred

        Returns:
            ExecutedOrder with error details

        """
        symbol = getattr(order_request, "symbol", "UNKNOWN")
        action = self._extract_action_from_request(order_request)

        return ExecutedOrder(
            order_id="FAILED",  # Must be non-empty
            symbol=symbol,
            action=action,
            quantity=Decimal("0.01"),  # Must be > 0
            filled_quantity=Decimal("0"),
            price=Decimal("0.01"),
            total_value=Decimal("0.01"),  # Must be > 0
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=str(error),
        )

    def _extract_action_from_request(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> str:
        """Extract action from order request safely."""
        side = getattr(order_request, "side", None)
        if not side:
            return "BUY"  # Default fallback

        if hasattr(side, "value"):
            return str(side.value).upper()

        side_str = str(side).upper()
        if "SELL" in side_str:
            return "SELL"
        return "BUY"

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result DTO.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResult reflecting the latest known state.

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            if isinstance(order, Order):
                return self._alpaca_order_to_execution_result(order)
            logger.error(f"Unexpected order type: {type(order)}")
            return self._create_error_execution_result(
                Exception("Invalid order type"),
                context="Order type validation",
                order_id=order_id,
            )
        except Exception as e:
            logger.error(f"Failed to refresh order {order_id}: {e}")
            return self._create_error_execution_result(
                e, context="Order refresh", order_id=order_id
            )

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
    ) -> ExecutedOrder:
        """Create error ExecutedOrder for failed orders.

        Args:
            order_id: Error order ID
            symbol: Stock symbol
            side: Order side
            qty: Order quantity
            error_message: Error description

        Returns:
            ExecutedOrder with error details

        """
        return ExecutedOrder(
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
    ) -> ExecutedOrder:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use Alpaca's available quantity

        Returns:
            ExecutedOrder with execution details

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

            # Create order request
            order_request = MarketOrderRequest(
                symbol=normalized_symbol,
                qty=final_qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            # Use the updated place_order method that returns ExecutedOrder
            return self.place_order(order_request)

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
        try:
            # Validation
            if not symbol or not symbol.strip():
                raise ValueError("Symbol cannot be empty")

            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            if limit_price <= 0:
                raise ValueError("Limit price must be positive")

            side_normalized = side.lower().strip()
            if side_normalized not in ["buy", "sell"]:
                raise ValueError("Side must be 'buy' or 'sell'")

            # Create order request
            order_request = LimitOrderRequest(
                symbol=symbol.upper(),
                qty=quantity,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                limit_price=limit_price,
                time_in_force=(
                    TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
                ),
            )

            # Use the updated place_order method that returns ExecutedOrder
            executed_order_dto = self.place_order(order_request)

            # Convert ExecutedOrder to OrderExecutionResult
            # Map ExecutedOrder status to OrderExecutionResult Literal status
            dto_status_to_result_status: dict[
                str,
                Literal["accepted", "filled", "partially_filled", "rejected", "canceled"],
            ] = {
                "FILLED": "filled",
                "PARTIAL": "partially_filled",
                "REJECTED": "rejected",
                "CANCELLED": "canceled",
                "CANCELED": "canceled",
                "PENDING": "accepted",
                "PENDING_NEW": "accepted",
                "FAILED": "rejected",
                "ACCEPTED": "accepted",
            }

            result_status: Literal[
                "accepted", "filled", "partially_filled", "rejected", "canceled"
            ] = dto_status_to_result_status.get(executed_order_dto.status.upper(), "accepted")

            success = result_status not in ["rejected", "canceled"]

            return OrderExecutionResult(
                success=success,
                order_id=executed_order_dto.order_id,
                status=result_status,
                filled_qty=executed_order_dto.filled_quantity,
                avg_fill_price=(
                    executed_order_dto.price if executed_order_dto.filled_quantity > 0 else None
                ),
                submitted_at=executed_order_dto.execution_timestamp,
                completed_at=(executed_order_dto.execution_timestamp if success else None),
                error=executed_order_dto.error_message if not success else None,
            )

        except ValueError as e:
            logger.error(f"Invalid limit order parameters: {e}")
            return self._create_error_execution_result(e, "Limit order validation")
        except Exception as e:
            logger.error(f"Failed to place limit order for {symbol}: {e}")
            return self._create_error_execution_result(e, f"Limit order for {symbol}")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(f"Successfully cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status."""
        try:
            # Use proper request to get more orders (default limit is very low)
            if status and status.lower() == "open":
                # Use the API's built-in open status filter for efficiency
                request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
                orders = self._trading_client.get_orders(request)
            else:
                # Get recent orders with higher limit to catch all relevant orders
                request = GetOrdersRequest(limit=100)  # Increased from default
                orders = self._trading_client.get_orders(request)

            orders_list = list(orders)

            # Apply manual filtering for non-open status requests
            if status and status.lower() != "open":
                status_lower = status.lower()
                # For other statuses, try exact match on the enum name
                orders_list = [
                    o for o in orders_list if str(getattr(o, "status", "")).lower() == status_lower
                ]

            logger.debug(f"Successfully retrieved {len(orders_list)} orders")
            return orders_list
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

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
        from the_alchemiser.shared.utils.price_discovery_utils import (
            get_current_price_from_quote,
        )

        try:
            return get_current_price_from_quote(self, symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        """
        try:
            prices = {}
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
                else:
                    logger.warning(f"Could not get price for {symbol}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get current prices for {symbols}: {e}")
            raise

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
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                # Use Pydantic model_dump() for consistent field names
                quote_dict = quote.model_dump()
                # Ensure we have symbol in the output
                quote_dict["symbol"] = symbol
                return quote_dict
            return None
        except (RetryException, HTTPError) as e:
            # These are specific API failures that should not be silent
            error_msg = f"Alpaca API failure getting quote for {symbol}: {e}"
            if "429" in str(e) or "rate limit" in str(e).lower():
                error_msg = f"Alpaca API rate limit exceeded getting quote for {symbol}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except RequestException as e:
            # Other network/HTTP errors
            error_msg = f"Network error getting quote for {symbol}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

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
        # Retry with exponential backoff and jitter for transient upstream failures
        max_retries = 3
        base_sleep = 0.6  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Resolve timeframe and create request
                resolved_timeframe = self._resolve_timeframe(timeframe)

                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)

                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=resolved_timeframe,
                    start=start_dt,
                    end=end_dt,
                )

                # Make API call and extract bars
                response = self._data_client.get_stock_bars(request)
                bars_obj = self._extract_bars_from_response(response, symbol)

                if not bars_obj:
                    if self._should_raise_missing_data_error(
                        start_date, end_date, timeframe, symbol
                    ):
                        error_msg = f"No historical data returned for {symbol}"
                        # Treat as transient in retry path, many times this is upstream glitch
                        raise RuntimeError(error_msg)
                    return []

                # Convert bars to dictionaries and return
                return self._convert_bars_to_dicts(bars_obj, symbol)

            except (RetryException, HTTPError, RequestException, Exception) as e:
                transient, reason = self._is_transient_error(e)
                last_attempt = attempt == max_retries

                if transient and not last_attempt:
                    jitter = 1.0 + 0.2 * (randbelow(1000) / 1000.0)
                    sleep_s = base_sleep * (2 ** (attempt - 1)) * jitter
                    logger.warning(
                        f"Transient market data error for {symbol} ({reason}); retry {attempt}/{max_retries} in {sleep_s:.2f}s"
                    )
                    time.sleep(sleep_s)
                    continue

                # Non-transient or out of retries: raise sanitized error
                summary = self._sanitize_error_message(e)
                msg = self._format_final_error_message(e, symbol, summary)
                logger.error(msg)
                raise RuntimeError(msg)

        # Defensive fallback for static analysis (should not be reached)
        return []

    # Private helper methods for get_historical_bars
    def _is_transient_error(self, err: Exception) -> tuple[bool, str]:
        """Check if an error is transient and should be retried.

        Args:
            err: Exception to check

        Returns:
            Tuple of (is_transient, reason_description)

        """
        msg = str(err)
        # Normalize common transient markers
        if "502" in msg or "Bad Gateway" in msg:
            return True, "502 Bad Gateway"
        if "503" in msg or "Service Unavailable" in msg:
            return True, "503 Service Unavailable"
        if "504" in msg or "Gateway Timeout" in msg or "timeout" in msg.lower():
            return True, "Gateway Timeout/Timeout"
        # HTML error pages from proxies
        if "<html" in msg.lower():
            # Try to extract status code
            m = re.search(r"\b(5\d{2})\b", msg)
            code = m.group(1) if m else "5xx"
            return True, f"HTTP {code} HTML error"
        return False, ""

    def _sanitize_error_message(self, err: Exception) -> str:
        """Sanitize error message for logging and user display.

        Args:
            err: Exception to sanitize

        Returns:
            Clean error message string

        """
        transient, reason = self._is_transient_error(err)
        if transient:
            return reason
        # Trim long HTML/text blobs
        msg = str(err)
        if "<html" in msg.lower():
            return "Upstream returned HTML error page"
        return msg

    def _resolve_timeframe(self, timeframe: str) -> TimeFrame:
        """Resolve timeframe string to Alpaca TimeFrame object.

        Args:
            timeframe: Timeframe string (case-insensitive)

        Returns:
            Alpaca TimeFrame object

        Raises:
            ValueError: If timeframe is not supported

        """
        timeframe_map = {
            "1min": TimeFrame(1, TimeFrameUnit.Minute),
            "5min": TimeFrame(5, TimeFrameUnit.Minute),
            "15min": TimeFrame(15, TimeFrameUnit.Minute),
            "1hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1day": TimeFrame(1, TimeFrameUnit.Day),
        }

        timeframe_lower = timeframe.lower()
        if timeframe_lower not in timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        return timeframe_map[timeframe_lower]

    def _extract_bars_from_response(self, response: object, symbol: str) -> BarsIterable | None:
        """Extract bars object from various possible response shapes.

        Args:
            response: API response object
            symbol: Stock symbol to extract bars for

        Returns:
            Bars object or None if not found

        """
        bars_obj: BarsIterable | None = None
        try:
            # Preferred: BarsBySymbol has a `.data` dict
            data_attr = getattr(response, "data", None)
            if isinstance(data_attr, dict) and symbol in data_attr:
                bars_obj = cast(BarsIterable, data_attr[symbol])
            # Some SDKs expose attributes per symbol
            elif hasattr(response, symbol):
                bars_obj = cast(BarsIterable, getattr(response, symbol))
            # Fallback: mapping-like access
            elif isinstance(response, dict) and symbol in response:
                bars_obj = cast(BarsIterable, response[symbol])
        except Exception:
            bars_obj = None

        return bars_obj

    def _convert_bars_to_dicts(self, bars_obj: BarsIterable, symbol: str) -> list[dict[str, Any]]:
        """Convert bars object to list of dictionaries using Pydantic model_dump.

        Args:
            bars_obj: Bars object from API response
            symbol: Stock symbol for logging

        Returns:
            List of dictionaries with bar data

        """
        bars = list(bars_obj)
        logger.debug(f"Successfully retrieved {len(bars)} bars for {symbol}")

        result: list[dict[str, Any]] = []
        for bar in bars:
            try:
                bar_dict = bar.model_dump()
                result.append(bar_dict)
            except Exception as e:  # pragma: no cover - conversion resilience
                logger.warning(f"Failed to convert bar for {symbol}: {e}")
                continue
        return result

    def _format_final_error_message(self, err: Exception, symbol: str, summary: str) -> str:
        """Format final error message based on exception type.

        Args:
            err: Original exception
            symbol: Stock symbol for context
            summary: Sanitized error summary

        Returns:
            Formatted error message

        """
        if isinstance(err, (RetryException, HTTPError)):
            return f"Alpaca API failure for {symbol}: {summary}"
        if isinstance(err, RequestException):
            return f"Network error retrieving data for {symbol}: {summary}"
        return f"Failed to get historical data for {symbol}: {summary}"

    def _should_raise_missing_data_error(
        self, start_date: str, end_date: str, timeframe: str, symbol: str
    ) -> bool:
        """Check if missing data should raise an error for retry.

        Args:
            start_date: Start date string
            end_date: End date string
            timeframe: Timeframe string
            symbol: Stock symbol for logging

        Returns:
            True if should raise error (will be retried), False if should return empty list

        """
        start_dt_local = datetime.fromisoformat(start_date)
        end_dt_local = datetime.fromisoformat(end_date)
        days_requested = (end_dt_local - start_dt_local).days

        # For daily data over a reasonable period, we should expect some bars
        if days_requested > 5 and timeframe.lower() == "1day":
            return True

        logger.warning(f"No historical data found for {symbol}")
        return False

    # Utility Methods
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

    def get_asset_info(self, symbol: str) -> AssetInfo | None:
        """Get asset information with caching.

        Args:
            symbol: Stock symbol

        Returns:
            AssetInfo with asset metadata, or None if not found.

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
            asset_dto = AssetInfo(
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

    # OrderExecutor protocol implementation methods

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using execution manager.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed

        """
        try:
            # Use the place_market_order method which now returns ExecutedOrder
            result = self.place_market_order(symbol, "sell", qty=qty)

            # Check if the order was successful and return order_id
            if result.status not in ["REJECTED", "CANCELED"] and result.order_id:
                return result.order_id
            logger.error(f"Smart sell order failed for {symbol}: {result.error_message}")
            return None

        except Exception as e:
            logger.error(f"Smart sell order failed for {symbol}: {e}")
            return None

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
        completed_orders: list[str] = []
        start_time = time.time()

        try:
            # Prefer websocket order updates
            completed_orders = self._wait_for_orders_via_ws(order_ids, max_wait_seconds)

            # Fallback to polling for any remaining orders within remaining time
            remaining = [oid for oid in order_ids if oid not in completed_orders]
            if remaining:
                time_left = max(0.0, max_wait_seconds - (time.time() - start_time))
                local_start = time.time()
                while remaining and (time.time() - local_start) < time_left:
                    self._process_pending_orders(remaining, completed_orders)
                    remaining = [oid for oid in remaining if oid not in completed_orders]
                    if remaining:
                        time.sleep(0.3)

            success = len(completed_orders) == len(order_ids)

            return WebSocketResult(
                status=(WebSocketStatus.COMPLETED if success else WebSocketStatus.TIMEOUT),
                message=f"Completed {len(completed_orders)}/{len(order_ids)} orders",
                completed_order_ids=completed_orders,
                metadata={"total_wait_time": time.time() - start_time},
            )

        except Exception as e:
            logger.error(f"Error monitoring order completion: {e}")
            return WebSocketResult(
                status=WebSocketStatus.ERROR,
                message=f"Error monitoring orders: {e}",
                completed_order_ids=completed_orders,
                metadata={"error": str(e)},
            )

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
