"""Business Unit: execution | Status: current.

Alpaca execution adapter for execution_v2 module.

Provides DTO-returning interface for Alpaca broker interactions,
ensuring all Alpaca SDK objects are converted to DTOs at the adapter boundary.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.shared.constants import DECIMAL_ZERO
from the_alchemiser.shared.logging.logging_utils import log_with_context
from the_alchemiser.shared.schemas.execution_report import ExecutedOrderDTO
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItemDTO

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "execution_v2.adapters.alpaca_execution_adapter"


class AlpacaExecutionAdapter:
    """Adapter for executing trades via shared AlpacaManager.

    Provides a clean interface for execution_v2 to execute trades
    while ensuring all Alpaca SDK objects are converted to DTOs
    and all monetary values use Decimal precision.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize adapter with AlpacaManager instance.

        Args:
            alpaca_manager: Shared AlpacaManager instance

        """
        self._alpaca_manager = alpaca_manager

    def execute_orders(self, rebalance_plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute all orders in a rebalance plan.

        Args:
            rebalance_plan: Plan containing orders to execute

        Returns:
            ExecutionResultDTO with results and proper Decimal handling

        Raises:
            Exception: If execution fails

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Executing {len(rebalance_plan.items)} orders from plan {rebalance_plan.plan_id}",
            module=MODULE_NAME,
            action="execute_orders",
            plan_id=rebalance_plan.plan_id,
            order_count=len(rebalance_plan.items),
        )

        order_results: list[OrderResultDTO] = []
        orders_placed = 0
        orders_succeeded = 0
        total_trade_value = DECIMAL_ZERO

        try:
            for item in rebalance_plan.items:
                try:
                    # Skip HOLD actions or zero trade amounts
                    if item.action.upper() == "HOLD" or item.trade_amount == DECIMAL_ZERO:
                        # Create a successful "no-op" order result
                        order_result = OrderResultDTO(
                            symbol=item.symbol,
                            action=item.action,
                            trade_amount=DECIMAL_ZERO,
                            shares=DECIMAL_ZERO,
                            price=None,
                            order_id=None,
                            success=True,
                            error_message=None,
                            timestamp=rebalance_plan.timestamp,
                        )
                        order_results.append(order_result)
                        orders_placed += 1
                        orders_succeeded += 1

                        log_with_context(
                            logger,
                            logging.INFO,
                            f"Skipped HOLD action or zero trade for {item.symbol}",
                            module=MODULE_NAME,
                            action="execute_single_order",
                            symbol=item.symbol,
                            action_type=item.action,
                            trade_amount=str(item.trade_amount),
                        )
                        continue

                    # Execute individual order through AlpacaManager
                    executed_order = self._execute_single_order(item)

                    # Convert to OrderResultDTO
                    order_result = self._convert_executed_order_to_dto(executed_order, item)
                    order_results.append(order_result)

                    orders_placed += 1
                    if order_result.success:
                        orders_succeeded += 1
                        total_trade_value += abs(
                            order_result.trade_amount
                        )  # Use abs for total volume

                    log_with_context(
                        logger,
                        logging.INFO if order_result.success else logging.ERROR,
                        f"Order {'succeeded' if order_result.success else 'failed'}: {item.symbol} {item.action}",
                        module=MODULE_NAME,
                        action="execute_single_order",
                        symbol=item.symbol,
                        action_type=item.action,
                        success=order_result.success,
                        error=order_result.error_message,
                    )

                except Exception as e:
                    # Create failed order result
                    order_result = OrderResultDTO(
                        symbol=item.symbol,
                        action=item.action,
                        trade_amount=abs(item.trade_amount),  # Use abs for order result
                        shares=Decimal("0"),  # Will be set by AlpacaManager, default to 0
                        price=None,
                        order_id=None,
                        success=False,
                        error_message=str(e),
                        timestamp=rebalance_plan.timestamp,
                    )
                    order_results.append(order_result)
                    orders_placed += 1

                    log_with_context(
                        logger,
                        logging.ERROR,
                        f"Failed to execute order for {item.symbol}: {e}",
                        module=MODULE_NAME,
                        action="execute_single_order",
                        symbol=item.symbol,
                        error=str(e),
                    )

            # Create execution result
            success, status = ExecutionResultDTO.classify_execution_status(
                orders_placed, orders_succeeded
            )

            execution_result = ExecutionResultDTO(
                success=success,
                status=status,
                plan_id=rebalance_plan.plan_id,
                correlation_id=rebalance_plan.correlation_id,
                orders=order_results,
                orders_placed=orders_placed,
                orders_succeeded=orders_succeeded,
                total_trade_value=total_trade_value,
                execution_timestamp=rebalance_plan.timestamp,
                metadata={
                    "adapter": MODULE_NAME,
                    "original_plan_items": len(rebalance_plan.items),
                },
            )

            log_with_context(
                logger,
                logging.INFO,
                f"Execution completed: {orders_succeeded}/{orders_placed} orders succeeded",
                module=MODULE_NAME,
                action="execute_orders",
                success=success,
                orders_placed=orders_placed,
                orders_succeeded=orders_succeeded,
                total_trade_value=str(total_trade_value),
            )

            return execution_result

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to execute rebalance plan: {e}",
                module=MODULE_NAME,
                action="execute_orders",
                error=str(e),
            )
            raise

    def _execute_single_order(self, rebalance_item: RebalancePlanItemDTO) -> ExecutedOrderDTO:
        """Execute a single order through AlpacaManager.

        Args:
            rebalance_item: Individual rebalance plan item

        Returns:
            ExecutedOrderDTO from the execution

        """
        # Get trading service to place orders using the existing patterns
        trading_service = self._alpaca_manager._get_trading_service()

        # Convert action to side
        side = "buy" if rebalance_item.action.upper() == "BUY" else "sell"

        # Place market order using notional (dollar) amount
        return trading_service.place_market_order(
            symbol=rebalance_item.symbol,
            side=side,
            qty=None,  # Use notional instead of quantity
            notional=abs(float(rebalance_item.trade_amount)),  # Use absolute value for notional
        )

    def _convert_executed_order_to_dto(
        self, executed_order: ExecutedOrderDTO, original_item: RebalancePlanItemDTO
    ) -> OrderResultDTO:
        """Convert ExecutedOrderDTO to OrderResultDTO.

        Args:
            executed_order: Result from AlpacaManager
            original_item: Original rebalance plan item

        Returns:
            OrderResultDTO for execution result

        """
        # Map ExecutedOrder fields to OrderResult fields
        success = executed_order.status in {"FILLED", "PARTIAL"}

        return OrderResultDTO(
            symbol=executed_order.symbol,
            action=executed_order.action,
            trade_amount=executed_order.total_value,  # Map total_value to trade_amount
            shares=executed_order.filled_quantity,  # Map filled_quantity to shares
            price=executed_order.price,
            order_id=executed_order.order_id,
            success=success,  # Derive success from status
            error_message=executed_order.error_message,
            timestamp=executed_order.execution_timestamp,  # Map execution_timestamp to timestamp
        )
