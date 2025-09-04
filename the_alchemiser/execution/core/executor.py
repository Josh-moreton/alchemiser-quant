"""Business Unit: execution | Status: current

Order execution core functionality.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.execution.mappers.alpaca_dto_mapping import (
    alpaca_order_to_execution_result,
    create_error_execution_result,
)
from the_alchemiser.execution.orders.order_request import OrderRequest
from the_alchemiser.execution.orders.order_schemas import OrderExecutionResult

if TYPE_CHECKING:
    from the_alchemiser.execution.brokers.alpaca.adapter import AlpacaManager

logger = logging.getLogger(__name__)


class CanonicalOrderExecutor:
    """Canonical order executor for handling trade execution.

    Provides a unified interface for executing orders through the Alpaca broker.
    Converts domain order requests to broker-specific formats and handles execution.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with Alpaca manager.

        Args:
            alpaca_manager: Alpaca manager instance for order execution

        """
        self.alpaca_manager = alpaca_manager

    def execute(self, order_request: OrderRequest) -> OrderExecutionResult:
        """Execute an order request.

        Converts the domain order request to Alpaca format and executes it,
        returning a standardized execution result.

        Args:
            order_request: Domain order request to execute

        Returns:
            OrderExecutionResult with success/failure status and order details

        """
        try:
            # Convert domain order request to Alpaca format
            alpaca_request = self._convert_to_alpaca_request(order_request)
            
            # Execute the order through AlpacaManager
            raw_envelope = self.alpaca_manager.place_order(alpaca_request)
            
            if raw_envelope.success and raw_envelope.raw_order:
                # Convert successful result to domain format
                return alpaca_order_to_execution_result(raw_envelope.raw_order)
            else:
                # Handle execution failure
                error_msg = raw_envelope.error_message or "Order execution failed"
                return create_error_execution_result(
                    error_msg,
                    order_id="",
                    symbol=order_request.symbol.value,
                )
                
        except Exception as e:
            logger.error(f"Error executing order for {order_request.symbol.value}: {e}")
            return create_error_execution_result(
                f"Order execution exception: {e}",
                order_id="",
                symbol=order_request.symbol.value,
            )

    def _convert_to_alpaca_request(self, order_request: OrderRequest) -> MarketOrderRequest | LimitOrderRequest:
        """Convert domain order request to Alpaca request format.

        Args:
            order_request: Domain order request

        Returns:
            Alpaca order request (MarketOrderRequest or LimitOrderRequest)

        """
        from alpaca.trading.enums import OrderSide, TimeInForce
        
        # Convert domain types to Alpaca types
        alpaca_side = OrderSide.BUY if order_request.side.value == "buy" else OrderSide.SELL
        alpaca_tif = TimeInForce.DAY  # Default to DAY for now
        
        common_params = {
            "symbol": order_request.symbol.value,
            "qty": float(order_request.quantity.value),
            "side": alpaca_side,
            "time_in_force": alpaca_tif,
        }
        
        if order_request.order_type.value == "market":
            return MarketOrderRequest(**common_params)
        elif order_request.order_type.value == "limit":
            if order_request.limit_price is None:
                raise ValueError("Limit price required for limit orders")
            return LimitOrderRequest(
                **common_params,
                limit_price=float(order_request.limit_price.amount),
            )
        else:
            raise ValueError(f"Unsupported order type: {order_request.order_type.value}")

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """Legacy method name compatibility.

        Args:
            order: Order to execute

        Returns:
            Execution result

        """
        return self.execute(order)
