#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Account DTOs for The Alchemiser Trading System.

This module contains DTOs for account data, buying power checks, risk metrics,
and account-related operations.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for account management operations
- Schema versioning for backward compatibility
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.schemas.base import Result

__all__ = [
    # Backward compatibility aliases
    "AccountMetrics",
    "AccountMetricsDTO",
    "AccountSummary",
    "AccountSummaryDTO",
    "BuyingPowerDTO",
    "BuyingPowerResult",
    "EnrichedAccountSummaryDTO",
    "EnrichedAccountSummaryView",
    "PortfolioAllocationDTO",
    "PortfolioAllocationResult",
    "RiskMetrics",
    "RiskMetricsDTO",
    "RiskMetricsResult",
    "TradeEligibilityDTO",
    "TradeEligibilityResult",
]


class AccountMetrics(BaseModel):
    """DTO for calculated account metrics.

    Provides derived financial ratios and exposure metrics calculated from
    raw account data.

    Attributes:
        cash_ratio: Cash as percentage of equity (0-1 range).
        market_exposure: Market value as percentage of equity (0-1 range).
        leverage_ratio: Leverage ratio if applicable, None for cash accounts.
        available_buying_power_ratio: Available buying power as percentage of equity.
        schema_version: Schema version for backward compatibility tracking.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    cash_ratio: Decimal = Field(..., ge=0, le=1, description="Cash as percentage of equity (0-1)")
    market_exposure: Decimal = Field(..., ge=0, description="Market value as percentage of equity")
    leverage_ratio: Decimal | None = Field(
        None,
        ge=0,
        description="Leverage ratio (None for cash accounts or when not applicable)",
    )
    available_buying_power_ratio: Decimal = Field(
        ..., ge=0, description="Available buying power as percentage of equity"
    )
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class AccountSummary(BaseModel):
    """DTO for comprehensive account summary.

    Used when returning account data from TradingServiceManager methods.
    Includes both raw account fields from broker and calculated metrics.

    Attributes:
        account_id: Unique Alpaca account identifier.
        equity: Current total account equity (cash + market_value).
        cash: Available cash balance.
        market_value: Current market value of all positions.
        buying_power: Available buying power for trading.
        last_equity: Account equity from previous trading day.
        day_trade_count: Number of day trades in last 5 business days (0-unlimited).
        pattern_day_trader: Whether account is flagged as pattern day trader.
        trading_blocked: Whether trading is currently blocked.
        transfers_blocked: Whether transfers are currently blocked.
        account_blocked: Whether account is completely blocked.
        calculated_metrics: Derived financial metrics and ratios.
        schema_version: Schema version for backward compatibility tracking.

    Example:
        >>> summary = AccountSummary(
        ...     account_id="abc123-def456",
        ...     equity=Decimal("10000.00"),
        ...     cash=Decimal("5000.00"),
        ...     market_value=Decimal("5000.00"),
        ...     buying_power=Decimal("10000.00"),
        ...     last_equity=Decimal("9500.00"),
        ...     day_trade_count=2,
        ...     pattern_day_trader=False,
        ...     trading_blocked=False,
        ...     transfers_blocked=False,
        ...     account_blocked=False,
        ...     calculated_metrics=metrics,
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account_id: str = Field(..., min_length=1, description="Alpaca account identifier")
    equity: Decimal = Field(..., ge=0, description="Current account equity")
    cash: Decimal = Field(..., ge=0, description="Available cash balance")
    market_value: Decimal = Field(..., ge=0, description="Market value of positions")
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")
    last_equity: Decimal = Field(..., ge=0, description="Previous day equity")
    day_trade_count: int = Field(..., ge=0, description="Day trades in last 5 business days")
    pattern_day_trader: bool = Field(..., description="Pattern day trader flag status")
    trading_blocked: bool = Field(..., description="Trading block status")
    transfers_blocked: bool = Field(..., description="Transfer block status")
    account_blocked: bool = Field(..., description="Complete account block status")
    calculated_metrics: AccountMetrics = Field(
        ..., description="Calculated financial metrics and ratios"
    )
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class BuyingPowerResult(Result):
    """DTO for buying power check results.

    Validates whether sufficient buying power exists for a trade.

    Attributes:
        success: Whether the operation succeeded.
        error: Error message if operation failed.
        available_buying_power: Current available buying power.
        required_amount: Amount required for the trade.
        sufficient_funds: Whether sufficient funds are available.
        schema_version: Schema version for backward compatibility tracking.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    available_buying_power: Decimal | None = Field(
        None, ge=0, description="Current available buying power"
    )
    required_amount: Decimal | None = Field(None, ge=0, description="Amount required for trade")
    sufficient_funds: bool | None = Field(
        None, description="Whether sufficient funds are available"
    )
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class RiskMetrics(BaseModel):
    """Typed risk metrics data.

    Contains specific risk management metrics and limits.

    Attributes:
        max_position_size: Maximum allowed position size.
        concentration_limit: Maximum concentration per position (0-1).
        total_exposure: Total market exposure as percentage.
        risk_score: Calculated risk score for the account.
        schema_version: Schema version for backward compatibility tracking.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    max_position_size: Decimal = Field(..., ge=0, description="Maximum position size")
    concentration_limit: Decimal = Field(
        ..., ge=0, le=1, description="Maximum concentration per position (0-1)"
    )
    total_exposure: Decimal = Field(..., ge=0, description="Total market exposure percentage")
    risk_score: Decimal = Field(..., ge=0, description="Calculated risk score")
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class RiskMetricsResult(Result):
    """DTO for comprehensive risk metrics.

    Returns calculated risk metrics for account risk management.

    Attributes:
        success: Whether the operation succeeded.
        error: Error message if operation failed.
        risk_metrics: Typed risk metrics data.
        schema_version: Schema version for backward compatibility tracking.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    risk_metrics: RiskMetrics | None = Field(None, description="Calculated risk metrics")
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class TradeEligibilityResult(BaseModel):
    """DTO for trade eligibility validation results.

    Validates whether a trade is eligible to execute based on account
    status, risk limits, and regulatory constraints.

    Attributes:
        eligible: Whether the trade is eligible to execute.
        reason: Reason if trade is not eligible.
        details: Additional validation details.
        symbol: Trading symbol being validated.
        quantity: Trade quantity.
        side: Trade side (BUY or SELL).
        estimated_cost: Estimated cost of the trade.
        schema_version: Schema version for backward compatibility tracking.

    Example:
        >>> result = TradeEligibilityResult(
        ...     eligible=True,
        ...     symbol="AAPL",
        ...     quantity=Decimal("10"),
        ...     side="BUY",
        ...     estimated_cost=Decimal("1500.00"),
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    eligible: bool = Field(..., description="Whether trade is eligible")
    reason: str | None = Field(None, description="Reason if not eligible")
    details: dict[str, Any] | None = Field(None, description="Additional validation details")
    symbol: str | None = Field(None, min_length=1, max_length=10, description="Trading symbol")
    quantity: Decimal | None = Field(None, gt=0, description="Trade quantity")
    side: Literal["BUY", "SELL"] | None = Field(None, description="Trade side")
    estimated_cost: Decimal | None = Field(None, ge=0, description="Estimated trade cost")
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class PortfolioAllocationResult(Result):
    """DTO for portfolio allocation and diversification metrics.

    Returns portfolio allocation data and diversification analysis.

    Attributes:
        success: Whether the operation succeeded.
        error: Error message if operation failed.
        allocation_data: Portfolio allocation details by symbol/sector.
        schema_version: Schema version for backward compatibility tracking.

    Note:
        allocation_data uses dict[str, Any] to maintain flexibility for
        varying allocation structures. Consider defining typed models
        for specific allocation use cases.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    allocation_data: dict[str, Any] | None = Field(None, description="Portfolio allocation details")
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


class EnrichedAccountSummaryView(BaseModel):
    """DTO for enriched account summary with typed domain objects.

    Combines raw broker API response with parsed and validated AccountSummary.
    Useful for debugging and audit trails.

    Attributes:
        raw: Raw account data from broker API (untyped for flexibility).
        summary: Parsed and validated account summary.
        schema_version: Schema version for backward compatibility tracking.

    Note:
        The raw field maintains dict[str, Any] to preserve original broker
        response structure without transformation.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any] = Field(..., description="Raw broker API response")
    summary: AccountSummary = Field(..., description="Parsed account summary")
    schema_version: str = Field(
        default="1.0", description="Schema version for backward compatibility"
    )


# Backward compatibility aliases - will be removed in future version
AccountSummaryDTO = AccountSummary
AccountMetricsDTO = AccountMetrics
BuyingPowerDTO = BuyingPowerResult
RiskMetricsDTO = RiskMetricsResult
TradeEligibilityDTO = TradeEligibilityResult
PortfolioAllocationDTO = PortfolioAllocationResult
EnrichedAccountSummaryDTO = EnrichedAccountSummaryView
