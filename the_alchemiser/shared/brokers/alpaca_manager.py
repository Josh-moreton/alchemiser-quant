"""Business Unit: shared | Status: current.

Alpaca broker facade composing focused adapters for backwards compatibility.

This facade delegates to specialized adapters while preserving the existing
public API for gradual migration. The original ~2091 LOC implementation has been
decomposed into focused adapters:

- AlpacaTradingAdapter: Order placement, cancellation, positions
- AlpacaMarketDataAdapter: Price retrieval, quotes, historical data  
- AlpacaAccountAdapter: Account info, buying power, position queries
- AlpacaStreamingManager: WebSocket lifecycle and order events
- AlpacaAssetCache: Asset metadata caching with TTL
- AlpacaMappers: SDK↔DTO conversion utilities

This facade provides backwards compatibility during migration while enabling
focused testing and maintenance of individual responsibilities.
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.brokers.alpaca_account_adapter import AlpacaAccountAdapter
from the_alchemiser.shared.brokers.alpaca_assets import AlpacaAssetCache
from the_alchemiser.shared.brokers.alpaca_market_data_adapter import (
    AlpacaMarketDataAdapter,
)
from the_alchemiser.shared.brokers.alpaca_streaming import AlpacaStreamingManager
from the_alchemiser.shared.brokers.alpaca_trading_adapter import AlpacaTradingAdapter
from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO
from the_alchemiser.shared.dto.broker_dto import WebSocketResult
from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.models import Position, TradeAccount
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

    from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO

logger = logging.getLogger(__name__)


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Facade composing focused Alpaca adapters for backwards compatibility.
    
    This class maintains the same public API as the original monolithic AlpacaManager
    while delegating to specialized adapters. This enables gradual migration of
    callers to use adapters directly while preserving backwards compatibility.
    
    Implements:
    - TradingRepository: Delegated to AlpacaTradingAdapter
    - MarketDataRepository: Delegated to AlpacaMarketDataAdapter  
    - AccountRepository: Delegated to AlpacaAccountAdapter
    
    Additional capabilities:
    - WebSocket streaming: AlpacaStreamingManager
    - Asset caching: AlpacaAssetCache
    - Legacy compatibility methods with deprecation warnings
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize Alpaca manager facade with composed adapters.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True for safety)
            base_url: Optional custom base URL (currently unused)
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = base_url

        # Initialize focused adapters
        self._trading_adapter = AlpacaTradingAdapter(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        self._market_data_adapter = AlpacaMarketDataAdapter(
            api_key=api_key, secret_key=secret_key
        )
        self._account_adapter = AlpacaAccountAdapter(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        self._streaming_manager = AlpacaStreamingManager(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        
        # Initialize asset cache using trading client
        self._asset_cache = AlpacaAssetCache(
            trading_client=self._trading_adapter.trading_client,
            ttl_seconds=300.0  # 5 minutes TTL
        )

        logger.info(f"AlpacaManager facade initialized - Paper: {paper}")

    # Properties for backwards compatibility
    @property
    def is_paper_trading(self) -> bool:
        """Return True if using paper trading."""
        return self._paper

    @property
    def api_key(self) -> str:
        """Return the API key (read-only)."""
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Return the secret key (read-only)."""
        warnings.warn(
            "Direct access to secret_key is deprecated for security",
            DeprecationWarning,
            stacklevel=2
        )
        return self._secret_key

    @property
    def paper(self) -> bool:
        """Return whether paper/live mode is enabled."""
        return self._paper

    @property
    def trading_client(self) -> TradingClient:
        """Return underlying trading client for backward compatibility."""
        warnings.warn(
            "Direct access to trading_client is deprecated. Use adapter methods instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._trading_adapter.trading_client

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AlpacaManager(paper={self._paper})"

    # TradingRepository implementation - delegate to trading adapter
    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity."""
        return self._trading_adapter.get_positions_dict()

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        return self._trading_adapter.get_buying_power()

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        return self._trading_adapter.get_portfolio_value()

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        return self._trading_adapter.place_order(order_request)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrderDTO:
        """Place a market order with validation and execution result return."""
        return self._trading_adapter.place_market_order(
            symbol=symbol,
            side=side,
            qty=qty,
            notional=notional,
            is_complete_exit=is_complete_exit,
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        return self._trading_adapter.cancel_order(order_id)

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol."""
        return self._trading_adapter.cancel_all_orders(symbol)

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API."""
        return self._trading_adapter.liquidate_position(symbol)

    def validate_connection(self) -> bool:
        """Validate connection to trading service."""
        return self._trading_adapter.validate_connection()

    # MarketDataRepository implementation - delegate to market data adapter
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        return self._market_data_adapter.get_current_price(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol."""
        return self._market_data_adapter.get_quote(symbol)

    # AccountRepository implementation - delegate to account adapter
    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dictionary."""
        return self._account_adapter.get_account()

    # Additional methods for backwards compatibility
    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object (deprecated)."""
        warnings.warn(
            "get_account_object is deprecated. Use get_account() for dict representation.",
            DeprecationWarning,
            stacklevel=2
        )
        return self._account_adapter._get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as dictionary (alias for get_account)."""
        warnings.warn(
            "get_account_dict is deprecated. Use get_account() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_account()

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects."""
        return self._account_adapter.get_positions()

    def get_all_positions(self) -> list[Any]:
        """Alias for get_positions() to mirror Alpaca SDK naming."""
        warnings.warn(
            "get_all_positions is deprecated. Use get_positions() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_positions()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol."""
        return self._account_adapter.get_position(symbol)

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions as dict (alias for get_positions_dict)."""
        warnings.warn(
            "get_current_positions is deprecated. Use get_positions_dict() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_positions_dict()

    # Market data convenience methods
    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols."""
        return self._market_data_adapter.get_current_prices(symbols)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol."""
        return self._market_data_adapter.get_latest_quote(symbol)

    # Asset information methods - delegate to asset cache
    def get_asset_info(self, symbol: str) -> AssetInfoDTO | None:
        """Get asset information with caching."""
        return self._asset_cache.get_asset_info(symbol)

    def is_fractionable(self, symbol: str) -> bool:
        """Check if asset is fractionable."""
        return self._asset_cache.is_fractionable(symbol)

    # Streaming methods - delegate to streaming manager
    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to complete via WebSocket events."""
        return self._streaming_manager.wait_for_order_completion(
            order_ids, max_wait_seconds
        )

    def _ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running (for backwards compatibility)."""
        warnings.warn(
            "_ensure_trading_stream is deprecated. Streaming is managed automatically.",
            DeprecationWarning,
            stacklevel=2
        )
        self._streaming_manager.ensure_trading_stream()

    # Cleanup method
    def disconnect(self) -> None:
        """Disconnect and cleanup all resources."""
        try:
            self._streaming_manager.disconnect()
            logger.info("AlpacaManager facade disconnected")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, *, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """Create an AlpacaManager instance.

    This function provides a clean way to create AlpacaManager instances
    and can be easily extended with additional configuration options.
    """
    return AlpacaManager(
        api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url
    )