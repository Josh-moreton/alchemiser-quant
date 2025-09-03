#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    available_buying_power: Decimal | None = None
    required_amount: Decimal | None = None
    sufficient_funds: bool | None = None


class RiskMetricsResult(Result):
    """DTO for comprehensive risk metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    risk_metrics: dict[str, Any] | None = None


class TradeEligibilityResult(BaseModel):
    """DTO for trade eligibility validation results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    eligible: bool
    reason: str | None = None
    details: dict[str, Any] | None = None
    symbol: str | None = None
    quantity: int | None = None
    side: str | None = None
    estimated_cost: Decimal | None = None


class PortfolioAllocationResult(Result):
    """DTO for portfolio allocation and diversification metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    allocation_data: dict[str, Any] | None = None


class EnrichedAccountSummaryView(BaseModel):
    """DTO for enriched account summary with typed domain objects."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    summary: AccountSummary


# Backward compatibility aliases - will be removed in future version
AccountSummaryDTO = AccountSummary
AccountMetricsDTO = AccountMetrics
BuyingPowerDTO = BuyingPowerResult
RiskMetricsDTO = RiskMetricsResult
TradeEligibilityDTO = TradeEligibilityResult
PortfolioAllocationDTO = PortfolioAllocationResult
EnrichedAccountSummaryDTO = EnrichedAccountSummaryView
