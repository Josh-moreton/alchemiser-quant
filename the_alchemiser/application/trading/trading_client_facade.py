#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Application Trading Client Facade.

This thin facade provides a clean application-layer interface that delegates to the
infrastructure AlpacaGateway. This maintains compatibility while properly separating
infrastructure concerns from application logic.

This replaces the previous AlpacaClient which inappropriately mixed application
and infrastructure concerns.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import (
        DataProvider as ExecDataProvider,
    )
    from the_alchemiser.interfaces.schemas.orders import ValidatedOrderDTO

from alpaca.trading.enums import OrderSide

from the_alchemiser.infrastructure.alpaca.alpaca_gateway import AlpacaGateway
from the_alchemiser.interfaces.schemas.execution import WebSocketResultDTO
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class TradingClientFacade:
    """Application facade for trading operations.
    
    Provides clean application-layer interface that delegates to infrastructure
    implementations. This maintains compatibility with existing code while
    properly separating concerns.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        data_provider: ExecDataProvider,
        validate_buying_power: bool = False,
    ) -> None:
        """Initialize facade with infrastructure gateway.

        Args:
            alpaca_manager: AlpacaManager instance for Alpaca API operations.
            data_provider: Data provider for quotes and prices.
            validate_buying_power: Whether to validate buying power for buy orders.

        """
        # Delegate to infrastructure gateway
        self._gateway = AlpacaGateway(alpaca_manager, data_provider, validate_buying_power)
        
        # Expose alpaca_manager for backward compatibility
        self.alpaca_manager = alpaca_manager
        self.trading_client = alpaca_manager.trading_client

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions from Alpaca."""
        return self._gateway.get_current_positions()

    def get_pending_orders_validated(self) -> list[ValidatedOrderDTO]:
        """Get all pending orders from Alpaca with type safety."""
        return self._gateway.get_pending_orders_validated()

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all pending orders, optionally filtered by symbol."""
        return self._gateway.cancel_all_orders(symbol)

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using Alpaca's close_position API."""
        return self._gateway.liquidate_position(symbol)

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using canonical executor."""
        return self._gateway.place_smart_sell_order(symbol, qty)

    def get_smart_limit_price(
        self, symbol: str, side: OrderSide, aggressiveness: float = 0.5
    ) -> float | None:
        """Get a smart limit price based on current bid/ask."""
        return self._gateway.get_smart_limit_price(symbol, side, aggressiveness)

    def get_aggressive_sell_price(self, symbol: str) -> float | None:
        """Get aggressive sell pricing for quick liquidation."""
        return self._gateway.get_aggressive_sell_price(symbol)

    def get_conservative_buy_price(self, symbol: str) -> float | None:
        """Get conservative buy pricing for better fills."""
        return self._gateway.get_conservative_buy_price(symbol)

    def wait_for_order_completion(
        self,
        order_ids: list[str],
        max_wait_seconds: int = 60,
    ) -> WebSocketResultDTO:
        """Wait for orders to reach a final state."""
        return self._gateway.wait_for_order_completion(order_ids, max_wait_seconds)

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order details by order ID from the trading client."""
        return self._gateway.get_order_by_id(order_id)

    def _prepare_websocket_connection(self) -> bool:
        """Pre-initialize WebSocket connection and wait for it to be ready."""
        return self._gateway._prepare_websocket_connection()

    def _cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        return self._gateway._cleanup_websocket_connection()


# Backward compatibility alias
AlpacaClient = TradingClientFacade