from __future__ import annotations

"""Business Unit: execution | Status: current..
"""

#!/usr/bin/env python3
"""Business Unit: execution | Status: current..

    Contains order execution results plus validation and account impact data.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_execution: OrderExecutionResultDTO | None = None
    pre_trade_validation: TradeEligibilityDTO | None = None
    order_validation: OrderValidationMetadataDTO | None = None
    account_impact: AccountSummaryDTO | None = None
    reason: str | None = None
    error: str | None = None

    validation_details: dict[str, Any] | None = None


class TradingDashboardDTO(ResultDTO):
    """DTO for comprehensive trading dashboard data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account: AccountSummaryDTO
    risk_metrics: dict[str, Any]
    portfolio_allocation: dict[str, Any]
    position_summary: dict[str, Any]
    open_orders: list[dict[str, Any]]
    market_status: dict[str, Any]
    timestamp: datetime
    error: str | None = None
