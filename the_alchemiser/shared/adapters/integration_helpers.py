#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Integration helpers for DTO-based module communication.

Provides helper functions and examples for implementing DTO-based
communication patterns between strategy, portfolio, and execution modules.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.adapters import (
    batch_strategy_signals_to_dtos,
    dto_to_portfolio_context,
    rebalance_plan_to_order_requests,
    strategy_signal_to_dto,
)
from the_alchemiser.shared.dto import (
    ExecutionReportDTO,
    OrderRequestDTO,
    PortfolioStateDTO,
    RebalancePlanDTO,
    StrategySignalDTO,
)


class StrategyPortfolioAdapter:
    """Adapter for Strategy → Portfolio communication."""

    @staticmethod
    def signals_to_allocation_requests(
        signals: list[Any],  # list[StrategySignal]
        strategy_name: str,
        portfolio_context: dict[str, Any] | None = None,
    ) -> list[StrategySignalDTO]:
        """Convert strategy signals to portfolio-consumable DTOs.

        Args:
            signals: List of internal strategy signal objects
            strategy_name: Name of the strategy generating signals
            portfolio_context: Optional portfolio context for correlation

        Returns:
            List of StrategySignalDTO instances ready for portfolio consumption

        """
        base_correlation_id = f"strategy_{strategy_name}_{uuid.uuid4().hex[:8]}"

        return batch_strategy_signals_to_dtos(
            signals=signals,
            base_correlation_id=base_correlation_id,
            strategy_name=strategy_name,
        )

    @staticmethod
    def portfolio_state_to_strategy_context(
        portfolio_state: PortfolioStateDTO,
    ) -> dict[str, Any]:
        """Provide portfolio context to strategy modules.

        Args:
            portfolio_state: Portfolio state DTO

        Returns:
            Dictionary with portfolio context for strategy consumption

        """
        return dto_to_portfolio_context(portfolio_state)


class PortfolioExecutionAdapter:
    """Adapter for Portfolio → Execution communication."""

    @staticmethod
    def rebalance_plan_to_orders(
        rebalance_plan: RebalancePlanDTO,
        portfolio_id: str,
        execution_config: dict[str, Any] | None = None,
    ) -> list[OrderRequestDTO]:
        """Convert rebalance plan to execution order requests.

        Args:
            rebalance_plan: Rebalance plan DTO
            portfolio_id: Portfolio identifier
            execution_config: Optional execution configuration

        Returns:
            List of OrderRequestDTO instances for execution

        """
        config = execution_config or {}

        return rebalance_plan_to_order_requests(
            rebalance_plan=rebalance_plan,
            portfolio_id=portfolio_id,
            execution_priority=config.get("execution_priority", "BALANCE"),
            time_in_force=config.get("time_in_force", "DAY"),
        )


class ExecutionPortfolioAdapter:
    """Adapter for Execution → Portfolio communication."""

    @staticmethod
    def execution_results_to_portfolio_update(
        execution_report: ExecutionReportDTO,
    ) -> dict[str, Any]:
        """Convert execution results to portfolio update context.

        Args:
            execution_report: Execution report DTO

        Returns:
            Dictionary with execution results for portfolio updates

        """
        return {
            "execution_id": execution_report.execution_id,
            "correlation_id": execution_report.correlation_id,
            "causation_id": execution_report.causation_id,
            "total_orders": execution_report.total_orders,
            "successful_orders": execution_report.successful_orders,
            "failed_orders": execution_report.failed_orders,
            "total_value_traded": float(execution_report.total_value_traded),
            "net_cash_flow": float(execution_report.net_cash_flow),
            "success_rate": float(execution_report.success_rate),
            "orders": [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "action": order.action,
                    "quantity": float(order.quantity),
                    "filled_quantity": float(order.filled_quantity),
                    "price": float(order.price),
                    "total_value": float(order.total_value),
                    "status": order.status,
                    "execution_timestamp": order.execution_timestamp,
                }
                for order in execution_report.orders
            ],
            "timestamp": execution_report.timestamp,
        }


class CrossModuleCommunicationHelper:
    """Helper for managing cross-module communication patterns."""

    @staticmethod
    def create_correlation_context(
        module_name: str,
        operation: str,
        parent_correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Create correlation context for DTO communication.

        Args:
            module_name: Name of the originating module
            operation: Name of the operation being performed
            parent_correlation_id: Optional parent correlation ID

        Returns:
            Dictionary with correlation IDs

        """
        correlation_id = f"{module_name}_{operation}_{uuid.uuid4().hex[:12]}"
        causation_id = parent_correlation_id or correlation_id

        return {
            "correlation_id": correlation_id,
            "causation_id": causation_id,
        }

    @staticmethod
    def validate_dto_communication_chain(
        strategy_signals: list[StrategySignalDTO],
        portfolio_state: PortfolioStateDTO,
        order_requests: list[OrderRequestDTO],
        execution_report: ExecutionReportDTO,
    ) -> bool:
        """Validate that DTOs maintain correlation throughout communication chain.

        Args:
            strategy_signals: Strategy signal DTOs
            portfolio_state: Portfolio state DTO
            order_requests: Order request DTOs
            execution_report: Execution report DTO

        Returns:
            True if correlation chain is valid, False otherwise

        """
        try:
            # Check that signals have valid correlation IDs
            if not all(
                signal.correlation_id and signal.causation_id for signal in strategy_signals
            ):
                return False

            # Check that portfolio state has correlation context
            if not (portfolio_state.correlation_id and portfolio_state.causation_id):
                return False

            # Check that order requests maintain correlation
            if not all(order.correlation_id and order.causation_id for order in order_requests):
                return False

            # Check that execution report has correlation context
            if not (execution_report.correlation_id and execution_report.causation_id):
                return False

            # Verify timestamps are chronologically ordered
            timestamps = [
                min(signal.timestamp for signal in strategy_signals)
                if strategy_signals
                else datetime.now(UTC),
                portfolio_state.timestamp,
                min(order.timestamp for order in order_requests)
                if order_requests
                else datetime.now(UTC),
                execution_report.timestamp,
            ]

            # Allow for some tolerance in timestamp ordering (e.g., parallel processing)
            for i in range(1, len(timestamps)):
                time_diff = (timestamps[i] - timestamps[i - 1]).total_seconds()
                if time_diff < -60:  # Allow up to 1 minute of clock skew
                    return False

            return True

        except Exception:
            return False


# Example usage patterns
def example_strategy_to_portfolio_communication() -> dict[str, Any]:
    """Example of Strategy → Portfolio communication using DTOs."""
    # Simulated strategy signal (in practice this would come from strategy module)
    mock_signal = type(
        "MockSignal",
        (),
        {
            "symbol": "AAPL",
            "action": "BUY",
            "confidence": Decimal("0.8"),
            "target_allocation": Decimal("0.1"),
            "reasoning": "Strong technical indicators",
            "timestamp": datetime.now(UTC),
        },
    )()

    # Convert to DTO using adapter
    signal_dto = strategy_signal_to_dto(
        signal=mock_signal,
        strategy_name="nuclear_strategy",
    )

    # Portfolio module would consume this DTO
    portfolio_context = {
        "signal": signal_dto.to_dict(),
        "action_required": signal_dto.action != "HOLD",
        "allocation_weight": float(signal_dto.allocation_weight)
        if signal_dto.allocation_weight
        else 0.0,
    }

    return portfolio_context


def example_portfolio_to_execution_communication() -> list[dict[str, Any]]:
    """Example of Portfolio → Execution communication using DTOs."""
    # Simulated rebalance plan (in practice this would come from portfolio module)
    from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanItemDTO

    correlation_id = f"rebalance_{uuid.uuid4().hex[:12]}"

    rebalance_plan = RebalancePlanDTO(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        timestamp=datetime.now(UTC),
        plan_id=f"plan_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        total_portfolio_value=Decimal("100000"),  # $100,000 total portfolio
        total_trade_value=Decimal("5000"),  # $5,000 total trade value
        items=[
            RebalancePlanItemDTO(
                symbol="AAPL",
                current_weight=Decimal("0.05"),  # 5% current weight
                target_weight=Decimal("0.10"),  # 10% target weight
                weight_diff=Decimal("0.05"),  # 5% increase
                target_value=Decimal("10000"),  # $10,000 target value
                current_value=Decimal("5000"),  # $5,000 current value
                trade_amount=Decimal("5000"),  # $5,000 to buy
                action="BUY",
                priority=1,
            ),
        ],
    )

    # Convert to order requests using adapter
    order_requests = PortfolioExecutionAdapter.rebalance_plan_to_orders(
        rebalance_plan=rebalance_plan,
        portfolio_id="main_portfolio",
    )

    # Execution module would consume these order request DTOs
    execution_contexts = [order.to_dict() for order in order_requests]

    return execution_contexts


if __name__ == "__main__":
    # Example usage
    print("Strategy → Portfolio communication example:")
    strategy_example = example_strategy_to_portfolio_communication()
    print(f"Portfolio context: {strategy_example}")

    print("\nPortfolio → Execution communication example:")
    execution_example = example_portfolio_to_execution_communication()
    print(f"Execution contexts: {len(execution_example)} orders created")
    for i, context in enumerate(execution_example):
        print(f"  Order {i + 1}: {context['symbol']} {context['side']} {context['quantity']}")
