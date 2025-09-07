"""Business Unit: execution | Status: current.

Order execution core functionality.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from the_alchemiser.execution.mappers.broker_integration_mappers import (
    alpaca_order_to_execution_result,
)
from the_alchemiser.execution.orders.schemas import OrderRequest
from the_alchemiser.execution.types.broker_requests import (
    AlpacaRequestConverter,
    BrokerLimitOrderRequest,
    BrokerMarketOrderRequest,
)
from the_alchemiser.shared.dto.broker_dto import OrderExecutionResult
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide, BrokerTimeInForce

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers import AlpacaManager

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

    def _convert_to_alpaca_request(self, order_request: OrderRequest) -> Any:
        """Convert domain order request to Alpaca request format.

        Args:
            order_request: Domain order request

        Returns:
            Alpaca order request (MarketOrderRequest or LimitOrderRequest)

        """
        # Convert domain types to broker abstractions
        broker_side = (
            BrokerOrderSide.BUY if order_request.side.value == "buy" else BrokerOrderSide.SELL
        )
        broker_tif = BrokerTimeInForce.DAY  # Default to DAY for now

        if order_request.order_type.value == "market":
            market_request = BrokerMarketOrderRequest(
                symbol=order_request.symbol.value,
                side=broker_side,
                time_in_force=broker_tif,
                qty=order_request.quantity.value,
            )
            return AlpacaRequestConverter.to_market_order(market_request)
        if order_request.order_type.value == "limit":
            if order_request.limit_price is None:
                raise ValueError("Limit price required for limit orders")
            limit_request = BrokerLimitOrderRequest(
                symbol=order_request.symbol.value,
                side=broker_side,
                time_in_force=broker_tif,
                qty=order_request.quantity.value,
                limit_price=order_request.limit_price.amount,
            )
            return AlpacaRequestConverter.to_limit_order(limit_request)
        raise ValueError(f"Unsupported order type: {order_request.order_type.value}")

    def execute_order(self, order: OrderRequest) -> OrderExecutionResult:
        """Legacy method name compatibility.

        Args:
            order: Order to execute

        Returns:
            Execution result

        """
        return self.execute(order)
