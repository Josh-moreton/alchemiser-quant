"""Business Unit: order execution/placement | Status: current

Alpaca order router adapter implementing OrderRouterPort.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict
from uuid import UUID

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError

from the_alchemiser.anti_corruption.brokers.alpaca_order_mapper import AlpacaOrderMapper
from the_alchemiser.execution.application.ports import (
    CancelAckVO,
    OrderAckVO,
    OrderRouterPort,
    OrderStatusVO,
)
from the_alchemiser.execution.domain.exceptions import (
    InsufficientFundsError,
    OrderExecutionError,
    OrderNotFoundError,
)
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import PlannedOrderV1
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError

logger = logging.getLogger(__name__)

class AlpacaOrderRouterAdapter(OrderRouterPort):
    """Alpaca broker adapter for order submission and management."""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str) -> None:
        """Initialize Alpaca trading client.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key  
            base_url: Base URL (paper/live trading)
        """
        self._api = tradeapi.REST(api_key, secret_key, base_url)
        self._mapper = AlpacaOrderMapper()
        self._logger = logger.bind(
            component="AlpacaOrderRouterAdapter",
            base_url=base_url
        )
        # Track internal order ID to broker order ID mapping
        self._order_id_map: Dict[UUID, str] = {}
    
    def submit_order(self, order: PlannedOrderV1) -> OrderAckVO:
        """Submit order to Alpaca for execution.
        
        Args:
            order: Validated planned order
            
        Returns:
            OrderAckVO with broker response
            
        Raises:
            OrderExecutionError: Broker submission failure
            ValidationError: Invalid order parameters
            InsufficientFundsError: Account lacks funds/shares
        """
        try:
            # Convert to Alpaca order format via anti-corruption layer
            alpaca_request = self._mapper.planned_order_to_alpaca_request(order)
            
            self._logger.info(
                "Submitting order to Alpaca",
                order_id=str(order.order_id),
                symbol=order.symbol.value,
                side=order.side.value,
                quantity=str(order.quantity)
            )
            
            # Submit to Alpaca
            alpaca_order = self._api.submit_order(**alpaca_request)
            
            # Store mapping for future lookups
            self._order_id_map[order.order_id] = alpaca_order.id
            
            # Convert response to domain object
            order_ack = OrderAckVO(
                order_id=order.order_id,
                accepted=True,
                broker_order_id=alpaca_order.id,
                message=f"Order accepted by Alpaca: {alpaca_order.status}",
                timestamp=datetime.utcnow()
            )
            
            self._logger.debug(
                "Order submitted successfully",
                order_id=str(order.order_id),
                alpaca_order_id=alpaca_order.id,
                status=alpaca_order.status
            )
            
            return order_ack
            
        except APIError as e:
            error_code = getattr(e, 'code', None)
            
            # Map specific Alpaca errors to domain exceptions
            if error_code == 40310000:  # Insufficient funds
                self._logger.warning(
                    "Insufficient funds for order",
                    order_id=str(order.order_id),
                    error=str(e)
                )
                raise InsufficientFundsError(
                    f"Insufficient funds for order {order.order_id}: {e}"
                ) from e
            elif error_code in [40010001, 42210000]:  # Invalid symbols/parameters
                self._logger.warning(
                    "Invalid order parameters",
                    order_id=str(order.order_id),
                    error=str(e)
                )
                raise ValidationError(
                    f"Invalid order parameters: {e}"
                ) from e
            else:
                self._logger.error(
                    "Alpaca order submission failed",
                    order_id=str(order.order_id),
                    error=str(e),
                    error_code=error_code
                )
                raise OrderExecutionError(
                    f"Alpaca order submission failed: {e}"
                ) from e
                
        except Exception as e:
            self._logger.error(
                "Unexpected error submitting order",
                order_id=str(order.order_id),
                error=str(e)
            )
            raise OrderExecutionError(
                f"Unexpected error submitting order: {e}"
            ) from e
    
    def cancel_order(self, order_id: UUID) -> CancelAckVO:
        """Cancel existing order by ID.
        
        Args:
            order_id: Order identifier to cancel
            
        Returns:
            CancelAckVO with cancellation status
            
        Raises:
            OrderExecutionError: Broker cancellation failure
            OrderNotFoundError: Order ID not found
        """
        try:
            # Find the broker order ID first
            broker_order_id = self._find_broker_order_id(order_id)
            
            self._logger.info(
                "Cancelling order with Alpaca",
                order_id=str(order_id),
                broker_order_id=broker_order_id
            )
            
            # Cancel with Alpaca
            alpaca_order = self._api.cancel_order(broker_order_id)
            
            cancel_ack = CancelAckVO(
                order_id=order_id,
                cancelled=alpaca_order.status in ["canceled", "cancelled"],
                message=f"Alpaca cancel response: {alpaca_order.status}",
                timestamp=datetime.utcnow()
            )
            
            self._logger.debug(
                "Order cancellation processed",
                order_id=str(order_id),
                cancelled=cancel_ack.cancelled,
                status=alpaca_order.status
            )
            
            return cancel_ack
            
        except APIError as e:
            if "order not found" in str(e).lower():
                raise OrderNotFoundError(
                    f"Order {order_id} not found at broker"
                ) from e
            else:
                self._logger.error(
                    "Alpaca order cancellation failed",
                    order_id=str(order_id),
                    error=str(e)
                )
                raise OrderExecutionError(
                    f"Alpaca order cancellation failed: {e}"
                ) from e
        except OrderNotFoundError:
            raise  # Re-raise domain exception as-is
        except Exception as e:
            self._logger.error(
                "Unexpected error cancelling order",
                order_id=str(order_id),
                error=str(e)
            )
            raise OrderExecutionError(
                f"Unexpected error cancelling order: {e}"
            ) from e
    
    def get_order_status(self, order_id: UUID) -> OrderStatusVO:
        """Get current status of submitted order.
        
        Args:
            order_id: Order identifier to check
            
        Returns:
            OrderStatusVO with current state and fills
            
        Raises:
            OrderExecutionError: Broker query failure
            OrderNotFoundError: Order ID not found
        """
        try:
            # Find the broker order ID first
            broker_order_id = self._find_broker_order_id(order_id)
            
            self._logger.debug(
                "Getting order status from Alpaca",
                order_id=str(order_id),
                broker_order_id=broker_order_id
            )
            
            # Get status from Alpaca
            alpaca_order = self._api.get_order(broker_order_id)
            
            # Convert to domain value object
            filled_qty = Decimal(alpaca_order.filled_qty or 0)
            total_qty = Decimal(alpaca_order.qty)
            remaining_qty = total_qty - filled_qty
            
            avg_fill_price = None
            if alpaca_order.filled_avg_price:
                avg_fill_price = Decimal(alpaca_order.filled_avg_price)
            
            status_vo = OrderStatusVO(
                order_id=order_id,
                status=alpaca_order.status,
                filled_quantity=filled_qty,
                remaining_quantity=remaining_qty,
                average_fill_price=avg_fill_price,
                last_update=alpaca_order.updated_at or datetime.utcnow()
            )
            
            self._logger.debug(
                "Retrieved order status",
                order_id=str(order_id),
                status=status_vo.status,
                filled_qty=str(filled_qty)
            )
            
            return status_vo
            
        except APIError as e:
            if "order not found" in str(e).lower():
                raise OrderNotFoundError(
                    f"Order {order_id} not found at broker"
                ) from e
            else:
                self._logger.error(
                    "Alpaca order status query failed",
                    order_id=str(order_id),
                    error=str(e)
                )
                raise OrderExecutionError(
                    f"Alpaca order status query failed: {e}"
                ) from e
        except OrderNotFoundError:
            raise  # Re-raise domain exception as-is
        except Exception as e:
            self._logger.error(
                "Unexpected error getting order status",
                order_id=str(order_id),
                error=str(e)
            )
            raise OrderExecutionError(
                f"Unexpected error getting order status: {e}"
            ) from e
    
    def _find_broker_order_id(self, order_id: UUID) -> str:
        """Find broker order ID for internal order ID.
        
        Args:
            order_id: Internal order identifier
            
        Returns:
            Broker order ID
            
        Raises:
            OrderNotFoundError: Order ID not found
        """
        if order_id in self._order_id_map:
            return self._order_id_map[order_id]
        
        # Fallback: search Alpaca orders by client_order_id
        try:
            orders = self._api.list_orders(
                status="all",
                limit=100
            )
            
            for alpaca_order in orders:
                if alpaca_order.client_order_id == str(order_id):
                    # Cache the mapping for future use
                    self._order_id_map[order_id] = alpaca_order.id
                    return alpaca_order.id
            
            raise OrderNotFoundError(f"Order {order_id} not found")
            
        except APIError as e:
            raise OrderExecutionError(
                f"Failed to lookup order {order_id}: {e}"
            ) from e