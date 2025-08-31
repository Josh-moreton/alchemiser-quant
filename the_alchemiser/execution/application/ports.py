"""Business Unit: order execution/placement | Status: current

Port protocols for Execution context external dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    PlannedOrderV1,
    RebalancePlanContractV1,
)
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True)
class OrderAckVO:
    """Value object for order submission acknowledgment."""

    order_id: UUID
    accepted: bool
    broker_order_id: str | None
    message: str
    timestamp: datetime


@dataclass(frozen=True)
class CancelAckVO:
    """Value object for order cancellation acknowledgment."""

    order_id: UUID
    cancelled: bool
    message: str
    timestamp: datetime


@dataclass(frozen=True)
class OrderStatusVO:
    """Value object for order status information."""

    order_id: UUID
    status: str
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_fill_price: Decimal | None
    last_update: datetime


@dataclass(frozen=True)
class BidAskSpreadVO:
    """Value object for bid/ask spread information."""

    symbol: Symbol
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    spread: Decimal
    timestamp: datetime


class OrderRouterPort(Protocol):
    """Port for submitting orders to external broker/exchange.

    Responsibilities:
    - Submit orders to broker API
    - Handle order cancellations
    - Provide order status acknowledgments
    - Map to broker-specific formats

    NOT responsible for:
    - Order validation (belongs in domain)
    - Position sizing (Portfolio responsibility)
    - Fill processing (separate concern)
    - Risk checks (belongs in domain)

    Error expectations:
    - Raises OrderExecutionError for broker failures
    - Raises ValidationError for invalid orders

    Idempotency: Submitting same order twice should be detected and handled
    """

    def submit_order(self, order: PlannedOrderV1) -> OrderAckVO:
        """Submit order to broker for execution.

        Args:
            order: Validated planned order ready for submission

        Returns:
            OrderAckVO with broker response and tracking info

        Raises:
            OrderExecutionError: Broker submission failure
            ValidationError: Invalid order parameters
            InsufficientFundsError: Account lacks required funds/shares

        """
        ...

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
        ...

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
        ...


class PlanSubscriberPort(Protocol):
    """Port for receiving rebalance plans from Portfolio context.

    Responsibilities:
    - Receive RebalancePlanContractV1 messages
    - Trigger order execution workflows
    - Handle message deduplication

    NOT responsible for:
    - Plan validation (Portfolio responsibility)
    - Order modification (belongs in domain)
    - Broker communication (OrderRouter responsibility)

    Error expectations:
    - Raises ProcessingError for handler failures

    Idempotency: Processing same message_id twice has no additional effect
    """

    def handle_rebalance_plan(self, plan: RebalancePlanContractV1) -> None:
        """Process incoming rebalance plan and initiate execution.

        Args:
            plan: Complete rebalance plan with orders to execute

        Raises:
            ProcessingError: Plan processing failure
            ValidationError: Invalid plan contract

        """
        ...


class ExecutionReportPublisherPort(Protocol):
    """Port for publishing execution results back to Portfolio context.

    Responsibilities:
    - Publish ExecutionReportContractV1 to Portfolio
    - Preserve correlation/causation metadata
    - Handle delivery confirmations

    NOT responsible for:
    - Report generation (belongs in application)
    - Fill aggregation (belongs in domain)
    - Portfolio updates (Portfolio responsibility)

    Error expectations:
    - Raises PublishError for delivery failures

    Idempotency: Publishing same message_id twice has no additional effect
    """

    def publish(self, report: ExecutionReportContractV1) -> None:
        """Publish execution report to Portfolio.

        Args:
            report: Complete execution report with fills and summary

        Raises:
            PublishError: Message delivery failure
            ValidationError: Invalid report contract

        """
        ...


class ExecutionMarketDataPort(Protocol):
    """Port for execution-specific market data (optional).

    Responsibilities:
    - Provide real-time prices for execution decisions
    - Handle pre-trade risk checks
    - Support smart execution algorithms

    NOT responsible for:
    - Historical analysis (Strategy responsibility)
    - Signal generation (Strategy responsibility)
    - Position valuation (Portfolio responsibility)

    Error expectations:
    - Raises DataAccessError for connectivity issues

    Idempotency: get_* methods are idempotent for same parameters
    """

    def get_current_price(self, symbol: Symbol) -> Decimal:
        """Get current market price for execution timing.

        Args:
            symbol: Symbol to price

        Returns:
            Current market price as Decimal

        Raises:
            DataAccessError: Market data failure
            SymbolNotFoundError: Invalid symbol

        """
        ...

    def get_bid_ask_spread(self, symbol: Symbol) -> BidAskSpreadVO:
        """Get current bid/ask for spread analysis.

        Args:
            symbol: Symbol to analyze

        Returns:
            BidAskSpreadVO with current market depth

        Raises:
            DataAccessError: Market data failure
            SymbolNotFoundError: Invalid symbol

        """
        ...


# Export list for explicit re-exports
__all__ = [
    "BidAskSpreadVO",
    "CancelAckVO",
    "ExecutionMarketDataPort",
    "ExecutionReportPublisherPort",
    "OrderAckVO",
    "OrderRouterPort",
    "OrderStatusVO",
    "PlanSubscriberPort",
]
