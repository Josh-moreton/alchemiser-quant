"""Business Unit: shared | Status: current.

Alpaca broker adapter facade (preserves backward compatibility).

This module provides a facade over the new modular Alpaca package structure
while maintaining the original API for existing consumers. The implementation
has been decomposed into focused modules for better maintainability.

DEPRECATION NOTICE: This facade will be deprecated in a future release.
New code should use the modular alpaca package directly:
- from the_alchemiser.shared.brokers.alpaca import config, client, accounts, etc.

Legacy compatibility is maintained for:
1. All existing method signatures
2. Import paths and class names  
3. Protocol implementations (TradingRepository, MarketDataRepository, AccountRepository)
4. Error handling behavior
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, Any

from alpaca.trading.models import Order, Position, TradeAccount
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

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

# Import the new modular components
from .alpaca.accounts import AccountManager
from .alpaca.client import AlpacaClient
from .alpaca.config import AlpacaConfig
from .alpaca.market_data import MarketDataManager
from .alpaca.orders import OrderManager
from .alpaca.positions import PositionManager
from .alpaca.streaming import StreamingManager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Facade for modular Alpaca broker functionality.

    This class maintains backward compatibility while delegating to the new
    modular implementation. It provides the same interface as the original
    monolithic implementation but with better separation of concerns.

    DEPRECATION WARNING: This facade pattern is maintained for backward
    compatibility. New code should use the modular components directly.

    Implements:
    - TradingRepository: For order placement and position management
    - MarketDataRepository: For market data and quotes  
    - AccountRepository: For account information and portfolio data
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize Alpaca facade with modular components.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True for safety)
            base_url: Optional custom base URL
        """
        # Show deprecation warning for direct usage
        warnings.warn(
            "AlpacaManager facade will be deprecated. "
            "Consider using the modular alpaca package directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        # Initialize configuration and core client
        self._config = AlpacaConfig(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
            base_url=base_url,
        )
        self._client = AlpacaClient(self._config)
        
        # Initialize modular managers
        self._accounts = AccountManager(self._client)
        self._positions = PositionManager(self._client)
        self._orders = OrderManager(self._client)
        self._market_data = MarketDataManager(self._client)
        self._streaming = StreamingManager(self._config)
        
        logger.info(f"AlpacaManager facade initialized - Paper: {paper}")

    # Properties for backward compatibility
    @property
    def is_paper_trading(self) -> bool:
        """Return True if using paper trading."""
        return self._config.is_paper_trading

    @property
    def api_key(self) -> str:
        """Return the API key (read-only)."""
        return self._config.api_key

    @property
    def secret_key(self) -> str:
        """Return the secret key (read-only)."""
        return self._config.secret_key

    @property
    def paper(self) -> bool:
        """Return whether paper/live mode is enabled."""
        return self._config.paper

    @property
    def trading_client(self) -> Any:
        """Return underlying trading client for backward compatibility."""
        return self._client.trading_client

    # Account operations - delegate to AccountManager
    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dict (protocol compliance)."""
        return self._accounts.get_account()

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object."""
        return self._accounts.get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as a plain dictionary for convenience."""
        return self._accounts.get_account_dict()

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        return self._accounts.get_buying_power()

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        return self._accounts.get_portfolio_value()

    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working."""
        return self._accounts.validate_connection()

    # Position operations - delegate to PositionManager  
    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects."""
        return self._positions.get_positions()

    def get_all_positions(self) -> list[Any]:
        """Alias for get_positions() to mirror Alpaca SDK naming."""
        return self._positions.get_all_positions()

    def get_positions_dict(self) -> dict[str, float]:
        """Get all positions as dict mapping symbol to quantity."""
        return self._positions.get_positions_dict()

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity."""
        return self._positions.get_current_positions()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        return self._positions.get_position(symbol)

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API."""
        return self._positions.liquidate_position(symbol)

    def get_asset_info(self, symbol: str) -> dict[str, Any] | None:
        """Get asset information."""
        return self._positions.get_asset_info(symbol)

    # Order operations - delegate to OrderManager
    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        return self._orders.place_order(order_request)

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result DTO."""
        return self._orders.get_order_execution_result(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        return self._orders.cancel_order(order_id)

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol."""
        return self._orders.cancel_all_orders(symbol)

    def cancel_stale_orders(self, timeout_minutes: int = 30) -> dict[str, Any]:
        """Cancel orders older than the specified timeout."""
        return self._orders.cancel_stale_orders(timeout_minutes)

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status."""
        return self._orders.get_orders(status)

    # Market data operations - delegate to MarketDataManager
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        return self._market_data.get_current_price(symbol)

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols."""
        return self._market_data.get_current_prices(symbols)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol."""
        return self._market_data.get_latest_quote(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol."""
        return self._market_data.get_quote(symbol)

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol."""
        return self._market_data.get_historical_bars(symbol, start_date, end_date, timeframe)

    # Streaming operations - delegate to StreamingManager
    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using WebSocket updates."""
        return self._streaming.wait_for_order_completion(order_ids, max_wait_seconds)

    # Additional legacy methods for complete backward compatibility
    def place_market_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = "day"
    ) -> ExecutedOrderDTO:
        """Place a market order (legacy wrapper)."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest
        
        # Map string parameters to enums
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        tif = TimeInForce.DAY if time_in_force.upper() == "DAY" else TimeInForce.GTC
        
        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=tif,
        )
        return self.place_order(request)

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = "day"
    ) -> ExecutedOrderDTO:
        """Place a limit order (legacy wrapper)."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest
        
        # Map string parameters to enums
        order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        tif = TimeInForce.DAY if time_in_force.upper() == "DAY" else TimeInForce.GTC
        
        request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            limit_price=limit_price,
            time_in_force=tif,
        )
        return self.place_order(request)

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order (legacy method)."""
        try:
            result = self.place_market_order(symbol, qty, "SELL")
            return result.order_id if result.status != "REJECTED" else None
        except Exception as e:
            logger.error(f"Smart sell order failed for {symbol}: {e}")
            return None

    def is_market_open(self) -> bool:
        """Check if market is currently open (legacy method)."""
        try:
            clock = self._client.trading_client.get_clock()
            return getattr(clock, "is_open", False)
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return False

    def get_market_calendar(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get market calendar information (legacy method)."""
        try:
            calendar = self._client.trading_client.get_calendar()
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
        start_date: str | None = None,
        end_date: str | None = None,
        timeframe: str = "1Day",
    ) -> dict[str, Any] | None:
        """Get portfolio history (legacy method)."""
        try:
            # This is a complex method that would need portfolio client
            # For now, return None to maintain interface compatibility
            logger.warning("get_portfolio_history not implemented in facade")
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return None

    def get_activities(
        self,
        activity_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get account activities (legacy method)."""
        try:
            # This is a complex method that would need account activities client
            # For now, return empty list to maintain interface compatibility
            logger.warning("get_activities not implemented in facade")
            return []
        except Exception as e:
            logger.error(f"Failed to get activities: {e}")
            return []

    # Private helper methods for internal compatibility
    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state (legacy method)."""
        return self._orders.check_order_completion_status(order_id)

    def _ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running (legacy method)."""
        self._streaming.ensure_trading_stream()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AlpacaManager(paper={self._config.paper})"


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, *, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """Create an AlpacaManager instance.

    This function provides a clean way to create AlpacaManager instances
    and can be easily extended with additional configuration options.
    
    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading (default: True for safety)
        base_url: Optional custom base URL
        
    Returns:
        AlpacaManager facade instance
    """
    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url)