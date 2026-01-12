"""Business Unit: execution_v2 | Status: current.

Lambda function to execute a single trade for Step Functions workflow.

This function executes a single trade via Alpaca API and returns the result.
It's designed for use with Step Functions and is idempotent.
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config import ApplicationContainer
from the_alchemiser.shared.errors import (
    ExecutionManagerError,
    MarketDataError,
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Global container instance (initialized once per Lambda container)
_container: ApplicationContainer | None = None


def get_container() -> ApplicationContainer:
    """Get or create the application container."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
        _container.wire(modules=[__name__])
    return _container


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Execute a single trade via Alpaca API.

    Args:
        event: Contains:
            - tradeId: Unique trade ID
            - symbol: Asset symbol
            - action: "BUY" or "SELL"
            - quantity: Number of shares (optional, calculated if not provided)
            - targetValue: Target dollar value
            - estimatedPrice: Estimated price per share (optional)
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
            - phase: "SELL" or "BUY"
            - isFullLiquidation: Boolean (optional)
            - targetWeight: Decimal target weight (optional)
            - strategyId: Strategy identifier (optional)
        context: Lambda context (unused)

    Returns:
        Dict with:
            - tradeId: Trade ID
            - symbol: Asset symbol
            - action: Trade action
            - status: "COMPLETED" | "FAILED"
            - quantity: Actual quantity filled
            - averagePrice: Average execution price
            - totalValue: Total dollar value
            - orderId: Broker order ID
            - errorMessage: Error message if failed

    """
    trade_id = event.get("tradeId", "unknown")
    symbol = event.get("symbol", "UNKNOWN")
    action = event.get("action", "UNKNOWN")
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    phase = event.get("phase", action)  # Default to action if phase not provided
    target_value = Decimal(str(event.get("targetValue", 0)))
    estimated_price = event.get("estimatedPrice")
    quantity = event.get("quantity")
    is_full_liquidation = event.get("isFullLiquidation", False)
    target_weight = Decimal(str(event.get("targetWeight", 0)))
    strategy_id = event.get("strategyId")

    logger.info(
        "Executing trade (Step Functions mode)",
        extra={
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "correlation_id": correlation_id,
            "run_id": run_id,
            "phase": phase,
        },
    )

    try:
        # Initialize container and get required services
        container = get_container()

        # Import here to avoid circular dependencies
        from functions.execution.core.executor import Executor
        from functions.execution.core.smart_execution_strategy import ExecutionConfig

        # Create executor
        executor = Executor(container=container)
        config = ExecutionConfig()

        # Calculate shares if not provided
        shares_to_trade = _calculate_shares(
            quantity=quantity,
            target_value=target_value,
            estimated_price=estimated_price,
            symbol=symbol,
            action=action,
            is_full_liquidation=is_full_liquidation,
            target_weight=target_weight,
            container=container,
        )

        # Execute the trade with retries for SELL phase
        side = "buy" if action == "BUY" else "sell"
        max_attempts = config.max_sell_retries + 1 if phase == "SELL" else 1
        retry_delay = config.sell_retry_delay_seconds
        last_error: Exception | None = None
        order_result = None

        for attempt in range(1, max_attempts + 1):
            try:
                order_result = asyncio.run(
                    executor.execute_order(
                        symbol=symbol,
                        side=side,
                        quantity=shares_to_trade,
                        correlation_id=correlation_id,
                        is_complete_exit=is_full_liquidation or target_weight <= Decimal("0"),
                        planned_trade_amount=abs(target_value),
                        strategy_id=strategy_id,
                    )
                )

                if order_result.success:
                    break

                # Retry non-success results for SELLs
                if attempt < max_attempts:
                    logger.warning(
                        f"⚠️ {phase} trade attempt {attempt}/{max_attempts} failed - retrying",
                        extra={
                            "run_id": run_id,
                            "trade_id": trade_id,
                            "symbol": symbol,
                            "error": order_result.error_message,
                        },
                    )
                    time.sleep(retry_delay)
                else:
                    break

            except (ExecutionManagerError, TradingClientError, MarketDataError) as e:
                last_error = e
                if attempt < max_attempts:
                    logger.warning(
                        f"⚠️ {phase} trade attempt {attempt}/{max_attempts} raised error - retrying",
                        extra={
                            "run_id": run_id,
                            "trade_id": trade_id,
                            "symbol": symbol,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    time.sleep(retry_delay)
                else:
                    raise

        # Shutdown executor
        if hasattr(executor, "shutdown"):
            executor.shutdown()

        if order_result is None and last_error:
            raise last_error

        if order_result is None:
            raise ExecutionManagerError("Order result must be set after execution")

        # Return formatted result
        if order_result.success:
            logger.info(
                f"✅ Trade executed successfully: {symbol}",
                extra={
                    "trade_id": trade_id,
                    "order_id": order_result.order_id,
                    "shares": str(order_result.shares),
                    "price": str(order_result.price) if order_result.price else None,
                },
            )

            return {
                "tradeId": trade_id,
                "symbol": symbol,
                "action": action,
                "status": "COMPLETED",
                "quantity": str(order_result.shares),
                "averagePrice": str(order_result.price) if order_result.price else None,
                "totalValue": str(order_result.trade_amount),
                "orderId": order_result.order_id,
                "errorMessage": None,
            }
        logger.error(
            f"❌ Trade failed: {symbol}",
            extra={
                "trade_id": trade_id,
                "error": order_result.error_message,
            },
        )

        return {
            "tradeId": trade_id,
            "symbol": symbol,
            "action": action,
            "status": "FAILED",
            "quantity": "0",
            "averagePrice": None,
            "totalValue": "0",
            "orderId": order_result.order_id,
            "errorMessage": order_result.error_message or "Trade execution failed",
        }

    except Exception as e:
        logger.error(
            f"❌ Trade execution error: {symbol}",
            exc_info=True,
            extra={
                "trade_id": trade_id,
                "symbol": symbol,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )

        return {
            "tradeId": trade_id,
            "symbol": symbol,
            "action": action,
            "status": "FAILED",
            "quantity": "0",
            "averagePrice": None,
            "totalValue": "0",
            "orderId": None,
            "errorMessage": f"{type(e).__name__}: {e!s}",
        }


def _calculate_shares(
    quantity: Any | None,
    target_value: Decimal,
    estimated_price: Any | None,
    symbol: str,
    action: str,
    *,
    is_full_liquidation: bool,
    target_weight: Decimal,
    container: ApplicationContainer,
) -> Decimal:
    """Calculate shares to trade.

    Args:
        quantity: Explicit quantity if provided
        target_value: Target dollar value
        estimated_price: Estimated price per share
        symbol: Asset symbol
        action: Trade action
        is_full_liquidation: Whether this is a full liquidation
        target_weight: Target weight
        container: Application container

    Returns:
        Decimal shares to trade

    """
    # For full liquidation SELLs, get actual position
    if (is_full_liquidation or target_weight <= Decimal("0")) and action == "SELL":
        try:
            alpaca_manager = container.infrastructure.alpaca_manager()
            position = alpaca_manager.get_position(symbol)
            if position:
                actual_qty = getattr(position, "qty", None)
                if actual_qty and Decimal(str(actual_qty)) > 0:
                    logger.info(
                        "Using actual position for full liquidation",
                        extra={"symbol": symbol, "actual_position": str(actual_qty)},
                    )
                    return Decimal(str(actual_qty))
        except Exception as e:
            logger.warning(
                f"Failed to fetch position for full liquidation: {e}",
                extra={"symbol": symbol},
            )

    # If explicit shares provided, use those
    if quantity and Decimal(str(quantity)) > 0:
        return Decimal(str(quantity))

    # Calculate from target_value and estimated_price
    if estimated_price and Decimal(str(estimated_price)) > 0:
        shares = abs(target_value) / Decimal(str(estimated_price))
        return shares.quantize(Decimal("0.000001"))

    # Fetch current market price
    try:
        alpaca_manager = container.infrastructure.alpaca_manager()
        current_price = alpaca_manager.get_current_price(symbol)

        if current_price and current_price > 0:
            shares = abs(target_value) / Decimal(str(current_price))
            logger.debug(
                f"Calculated shares from current price: {shares:.6f}",
                extra={
                    "symbol": symbol,
                    "target_value": str(target_value),
                    "current_price": str(current_price),
                },
            )
            return shares.quantize(Decimal("0.000001"))

        raise MarketDataError(f"Invalid price for {symbol}: {current_price}")

    except MarketDataError:
        raise
    except Exception as e:
        raise MarketDataError(f"Failed to fetch price for {symbol}: {e}") from e
