"""Enhanced execution result DTOs with comprehensive order tracking."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field, validator

from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.types import AccountInfo, StrategySignal
from the_alchemiser.interfaces.schemas.execution_summary import (
    ExecutionSummaryDTO,
    PortfolioStateDTO,
)


class OrderExecutionStatus(BaseModel):
    """Comprehensive order execution status with lifecycle tracking."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Required order identification (never None)
    order_id: str = Field(..., min_length=1, description="Order ID (never None/empty)")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    
    # Order details
    side: str = Field(..., regex="^(buy|sell)$", description="Order side")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    order_type: str = Field(..., description="Order type (market/limit)")
    
    # Execution status
    status: str = Field(..., description="Current order status")
    filled_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="Filled quantity")
    average_fill_price: Decimal | None = Field(None, ge=0, description="Average fill price")
    
    # Lifecycle tracking
    submitted_at: str | None = Field(None, description="Submission timestamp")
    completed_at: str | None = Field(None, description="Completion timestamp")
    
    # Execution attempts and re-pegging
    attempt_count: int = Field(default=1, ge=1, description="Number of execution attempts")
    repeg_count: int = Field(default=0, ge=0, description="Number of re-peg attempts")
    
    # Error tracking
    error_code: str | None = Field(None, description="Error code if failed")
    error_message: str | None = Field(None, description="Error message if failed")
    suggested_action: str | None = Field(None, description="Suggested action for errors")
    
    # Market data context
    limit_price: Decimal | None = Field(None, ge=0, description="Limit price if applicable")
    market_price_at_submission: Decimal | None = Field(None, ge=0, description="Market price when submitted")
    
    @validator("order_id")
    def validate_order_id_not_empty(cls, v: str) -> str:
        """Ensure order_id is never None or empty."""
        if not v or v.strip() == "":
            raise ValueError("order_id cannot be None or empty")
        return v.strip()

    @validator("filled_quantity", "quantity")
    def validate_fill_not_exceeds_quantity(cls, v: Decimal, values: Dict[str, any]) -> Decimal:
        """Ensure filled quantity doesn't exceed order quantity."""
        if "quantity" in values and v > values["quantity"]:
            raise ValueError("filled_quantity cannot exceed order quantity")
        return v

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status.lower() in ["filled", "completely_filled"]

    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.filled_quantity > 0 and not self.is_filled

    @property
    def fill_percentage(self) -> Decimal:
        """Calculate fill percentage."""
        if self.quantity == 0:
            return Decimal("0")
        return (self.filled_quantity / self.quantity) * Decimal("100")

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining unfilled quantity."""
        return self.quantity - self.filled_quantity

    @property
    def total_fill_value(self) -> Decimal | None:
        """Calculate total value of filled portion."""
        if self.average_fill_price is None or self.filled_quantity == 0:
            return None
        return self.filled_quantity * self.average_fill_price

    @property
    def has_error(self) -> bool:
        """Check if order has error."""
        return self.error_code is not None or self.error_message is not None


class ExecutionFailureReport(BaseModel):
    """Report for failed execution phases."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    phase: str = Field(..., description="Execution phase that failed (sell/buy/settlement)")
    error_category: str = Field(..., description="Error category")
    error_count: int = Field(..., ge=0, description="Number of errors in this phase")
    failed_orders: List[OrderExecutionStatus] = Field(default_factory=list, description="Orders that failed")
    critical_failures: List[str] = Field(default_factory=list, description="Critical failure descriptions")
    recovery_attempted: bool = Field(default=False, description="Whether recovery was attempted")
    recovery_successful: bool = Field(default=False, description="Whether recovery succeeded")


class EnhancedMultiStrategyExecutionResultDTO(BaseModel):
    """Enhanced DTO for multi-strategy execution results with comprehensive order tracking."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution status
    success: bool = Field(..., description="Overall execution success")
    execution_phase: str = Field(default="completed", description="Current/final execution phase")

    # Strategy data
    strategy_signals: Dict[StrategyType, StrategySignal] = Field(..., description="Strategy signals")
    consolidated_portfolio: Dict[str, float] = Field(..., description="Target portfolio allocation")

    # Enhanced order execution results
    orders_executed: List[OrderExecutionStatus] = Field(..., description="All order execution results")
    
    # Phase-specific order groups
    sell_orders: List[OrderExecutionStatus] = Field(default_factory=list, description="SELL phase orders")
    buy_orders: List[OrderExecutionStatus] = Field(default_factory=list, description="BUY phase orders")

    # Account state tracking
    account_info_before: AccountInfo = Field(..., description="Account state before execution")
    account_info_after: AccountInfo = Field(..., description="Account state after execution")

    # Execution summary and portfolio state
    execution_summary: ExecutionSummaryDTO = Field(..., description="Execution summary")
    final_portfolio_state: PortfolioStateDTO | None = Field(None, description="Final portfolio state")

    # Failure tracking
    execution_failures: List[ExecutionFailureReport] = Field(
        default_factory=list, description="Execution failure reports"
    )

    # Settlement tracking
    settlement_duration_seconds: float | None = Field(None, ge=0, description="Settlement duration")
    websocket_events_received: int = Field(default=0, ge=0, description="WebSocket events received")
    polling_fallback_used: bool = Field(default=False, description="Whether polling fallback was used")

    # Drift analysis
    allocation_drift_pct: Dict[str, Decimal] = Field(
        default_factory=dict, description="Allocation drift percentage by symbol"
    )
    max_drift_symbol: str | None = Field(None, description="Symbol with maximum drift")
    max_drift_pct: Decimal | None = Field(None, description="Maximum drift percentage")

    @validator("orders_executed")
    def validate_no_empty_order_ids(cls, v: List[OrderExecutionStatus]) -> List[OrderExecutionStatus]:
        """Ensure no orders have empty or None IDs."""
        for order in v:
            if not order.order_id or order.order_id.strip() == "":
                raise ValueError(f"Order with symbol {order.symbol} has empty order_id")
        return v

    @validator("sell_orders", "buy_orders")
    def validate_phase_order_ids(cls, v: List[OrderExecutionStatus]) -> List[OrderExecutionStatus]:
        """Ensure phase-specific orders have valid IDs."""
        for order in v:
            if not order.order_id or order.order_id.strip() == "":
                raise ValueError(f"Phase order with symbol {order.symbol} has empty order_id")
        return v

    @property
    def total_orders(self) -> int:
        """Total number of orders executed."""
        return len(self.orders_executed)

    @property
    def successful_orders(self) -> List[OrderExecutionStatus]:
        """Get successfully executed orders."""
        return [
            order for order in self.orders_executed
            if order.is_filled and not order.has_error
        ]

    @property
    def failed_orders(self) -> List[OrderExecutionStatus]:
        """Get failed orders."""
        return [
            order for order in self.orders_executed
            if order.has_error or order.status.lower() in ["rejected", "cancelled", "expired"]
        ]

    @property
    def partially_filled_orders(self) -> List[OrderExecutionStatus]:
        """Get partially filled orders."""
        return [order for order in self.orders_executed if order.is_partially_filled]

    @property
    def success_rate(self) -> Decimal:
        """Calculate order success rate."""
        if self.total_orders == 0:
            return Decimal("100")
        return (Decimal(str(len(self.successful_orders))) / Decimal(str(self.total_orders))) * Decimal("100")

    @property
    def total_repeg_attempts(self) -> int:
        """Total re-peg attempts across all orders."""
        return sum(order.repeg_count for order in self.orders_executed)

    @property
    def average_execution_attempts(self) -> Decimal:
        """Average execution attempts per order."""
        if self.total_orders == 0:
            return Decimal("0")
        total_attempts = sum(order.attempt_count for order in self.orders_executed)
        return Decimal(str(total_attempts)) / Decimal(str(self.total_orders))

    @property
    def has_critical_failures(self) -> bool:
        """Check if there are any critical failures."""
        return any(report.critical_failures for report in self.execution_failures)

    @property
    def settlement_success_rate(self) -> Decimal:
        """Calculate settlement success rate (non-timeout orders)."""
        non_timeout_orders = [
            order for order in self.orders_executed
            if order.status.lower() != "timeout"
        ]
        if len(non_timeout_orders) == 0:
            return Decimal("100")
        return (Decimal(str(len(non_timeout_orders))) / Decimal(str(self.total_orders))) * Decimal("100")

    def get_orders_by_symbol(self, symbol: str) -> List[OrderExecutionStatus]:
        """Get all orders for a specific symbol."""
        return [order for order in self.orders_executed if order.symbol.upper() == symbol.upper()]

    def get_orders_by_status(self, status: str) -> List[OrderExecutionStatus]:
        """Get all orders with specific status."""
        return [order for order in self.orders_executed if order.status.lower() == status.lower()]