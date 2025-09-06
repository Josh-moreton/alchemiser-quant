"""Business Unit: execution | Status: current.

Order execution service handling order placement, cancellation, and status operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.execution.mappers.order_mapping import (
    alpaca_order_to_domain,
    summarize_order,
)
from the_alchemiser.execution.mappers.trading_service_dto_mapping import (
    list_to_open_orders_dto,
)
from the_alchemiser.execution.orders.order_schemas import (
    OrderExecutionResultDTO,
)
from the_alchemiser.execution.orders.service import OrderService
from the_alchemiser.shared.schemas.enriched_data import (
    OpenOrdersDTO,
)
from the_alchemiser.shared.schemas.operations import (
    OrderCancellationDTO,
    OrderStatusDTO,
)
from the_alchemiser.shared.utils.decorators import translate_trading_errors


class OrderExecutionService:
    """Service responsible for order execution operations.

    Handles order placement, cancellation, status queries, and order management.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize the order execution service.

        Args:
            alpaca_manager: The Alpaca manager for broker operations

        """
        self.logger = logging.getLogger(__name__)
        self.alpaca_manager = alpaca_manager
        self.orders = OrderService(alpaca_manager)

    def place_stop_loss_order(
        self, symbol: str, quantity: float, stop_price: float, validate: bool = True
    ) -> OrderExecutionResultDTO:
        """Place a stop-loss order using liquidation (not directly supported)."""
        return OrderExecutionResultDTO(
            success=False,
            error="Stop-loss orders not directly supported. Use liquidate_position for position closure.",
            order_id="",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=None,
        )

    def cancel_order(self, order_id: str) -> OrderCancellationDTO:
        """Cancel an order with enhanced feedback."""
        try:
            success = self.orders.cancel_order(order_id)
            return OrderCancellationDTO(success=success, order_id=order_id)
        except Exception as e:
            return OrderCancellationDTO(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> OrderStatusDTO:
        """Get order status (not directly available - use AlpacaManager directly)."""
        return OrderStatusDTO(
            success=False,
            error="Order status queries not available in enhanced services. Use AlpacaManager directly.",
        )

    @translate_trading_errors(
        default_return=OpenOrdersDTO(
            success=False,
            orders=[],
            symbol_filter=None,
            error="open orders unavailable",
        )
    )
    def get_open_orders(self, symbol: str | None = None) -> OpenOrdersDTO:
        """Get open orders.

        Legacy path returns raw-ish dicts derived from Alpaca objects.
        When the type system flag is enabled, returns a richer dict with
        a 'domain' key containing the mapped domain Order and a 'summary'.
        """
        try:
            orders = self.alpaca_manager.get_orders(status="open")
            # Optional symbol filter for safety (Alpaca filter applied earlier best-effort)
            if symbol:
                orders = [
                    o
                    for o in orders
                    if getattr(o, "symbol", None) == symbol
                    or (isinstance(o, dict) and o.get("symbol") == symbol)
                ]

            # Always use enriched typed path (using typed domain)
            enriched: list[dict[str, Any]] = []
            for o in orders:
                dom = alpaca_order_to_domain(o)
                enriched.append(
                    {
                        "raw": o,
                        "domain": dom,
                        "summary": summarize_order(dom),
                    }
                )

            return list_to_open_orders_dto(enriched, symbol)
        except Exception as e:
            return OpenOrdersDTO(success=False, orders=[], symbol_filter=symbol, error=str(e))
