"""Business Unit: shared | Status: current.

Execution report data schema for decoupled report generation.

Provides a frozen, lightweight Pydantic model for passing execution results
from the main trading lambda to the report generator lambda without requiring
shared module imports or database queries.

All values are pre-serialized at boundaries:
- Decimals converted to strings
- Datetimes converted to ISO 8601 strings
- Financial values explicitly decimal-based for precision
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ExecutionReportData"]


class ExecutionReportData(BaseModel):
    """Immutable execution report data for report generation.

    This model contains all information needed to generate a trading execution
    report, pre-computed and serialized by the main trading lambda. The report
    generator lambda consumes this event and produces a PDF without querying
    databases or importing business logic modules.

    Schema versioning allows future evolution without breaking existing reports.
    All financial values use string representation to preserve Decimal precision.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,  # Immutable
        validate_default=True,
    )

    # Schema metadata
    schema_version: str = Field(
        default="1.0",
        description="Schema version for evolution tracking",
    )

    # Execution context
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    timestamp: str = Field(
        ..., description="Execution timestamp (ISO 8601 UTC)"
    )  # Pre-serialized from main lambda
    trading_mode: str = Field(..., description="Trading mode (PAPER or LIVE)")
    trading_success: bool = Field(..., description="Whether trading was successful")

    # Order execution summary
    orders_placed: int = Field(..., description="Total orders placed")
    orders_succeeded: int = Field(..., description="Orders that succeeded")
    orders_failed: int = Field(default=0, description="Orders that failed")  # Inferred or explicit
    total_trade_value: str = Field(..., description="Total value of trades (Decimal as string)")
    execution_duration_ms: int = Field(
        default=0, description="Total execution duration in milliseconds"
    )

    # Strategy signals (last 20 truncated at boundary)
    strategy_signals: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy signals by strategy name: {name: {signal, reasoning, confidence}}",
    )

    # Portfolio allocations (last 20 truncated at boundary)
    portfolio_allocations: dict[str, str] = Field(
        default_factory=dict,
        description="Target portfolio allocations: {symbol: allocation_percentage_as_string}",
    )

    # Orders executed (last 20 truncated at boundary)
    orders_executed: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of executed orders: [{symbol, side, qty, price, status, order_id, ...}]",
    )

    # Error details (if trading_success=False)
    error_message: str | None = Field(default=None, description="Error message if trading failed")
    error_code: str | None = Field(default=None, description="Error code if trading failed")

    # Additional metadata
    failed_symbols: list[str] = Field(
        default_factory=list, description="Symbols that failed execution"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )

    @classmethod
    def from_trading_notification(
        cls,
        trading_mode: str,
        *,
        trading_success: bool,
        orders_placed: int,
        orders_succeeded: int,
        total_trade_value: str,
        execution_data: dict[str, Any],
        correlation_id: str,
        timestamp: str | None = None,
        error_message: str | None = None,
        error_code: str | None = None,
    ) -> ExecutionReportData:
        """Build ExecutionReportData from TradingNotificationRequested event.

        Convenience factory method to construct report data from orchestrator's
        published notification event.

        Args:
            trading_mode: PAPER or LIVE
            trading_success: Success indicator
            orders_placed: Total orders placed
            orders_succeeded: Successful orders
            total_trade_value: Total trade value (Decimal as string)
            execution_data: Dict with strategy_signals, portfolio_allocations, orders_executed, execution_summary
            correlation_id: Correlation ID for tracing
            timestamp: Execution timestamp (ISO string); defaults to now UTC
            error_message: Error message if failed
            error_code: Error code if failed

        Returns:
            ExecutionReportData instance

        """
        from datetime import UTC

        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        # Extract fields from execution_data, truncate to last 20 items
        strategy_signals = execution_data.get("strategy_signals", {})
        portfolio_allocations = execution_data.get("consolidated_portfolio", {})
        if isinstance(portfolio_allocations, dict):
            # Extract target_allocations if nested
            portfolio_allocations = portfolio_allocations.get(
                "target_allocations", portfolio_allocations
            )

        orders_executed = execution_data.get("orders_executed", [])
        if isinstance(orders_executed, list) and len(orders_executed) > 20:
            orders_executed = orders_executed[-20:]  # Last 20

        execution_summary = execution_data.get("execution_summary", {})

        return cls(
            schema_version="1.0",
            correlation_id=correlation_id,
            timestamp=timestamp,
            trading_mode=trading_mode,
            trading_success=trading_success,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            orders_failed=execution_summary.get("orders_failed", 0),
            total_trade_value=total_trade_value,
            execution_duration_ms=execution_summary.get("execution_duration_ms", 0),
            strategy_signals=strategy_signals,
            portfolio_allocations=portfolio_allocations,
            orders_executed=orders_executed,
            error_message=error_message,
            error_code=error_code,
            failed_symbols=execution_data.get("failed_symbols", []),
            metadata=execution_data.get("metadata", {}),
        )
