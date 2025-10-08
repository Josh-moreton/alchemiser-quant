#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Lambda event data transfer objects for AWS Lambda event handling.

Provides typed DTOs for Lambda event parsing and cross-module coordination.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LambdaEvent(BaseModel):
    """DTO for AWS Lambda event data.

    Used for parsing Lambda events to determine trading mode and configuration.
    Supports trading, signal-only (bot), and P&L analysis modes.

    Examples:
        Paper trading:
            >>> event = LambdaEvent(mode="trade", trading_mode="paper")
            >>> event.mode
            'trade'

        Live trading:
            >>> event = LambdaEvent(mode="trade", trading_mode="live")
            >>> event.trading_mode
            'live'

        Signal-only mode:
            >>> event = LambdaEvent(mode="bot")
            >>> event.mode
            'bot'

        P&L weekly analysis:
            >>> event = LambdaEvent(action="pnl_analysis", pnl_type="weekly")
            >>> event.action
            'pnl_analysis'

        P&L with custom period:
            >>> event = LambdaEvent(action="pnl_analysis", pnl_period="3M")
            >>> event.pnl_period
            '3M'

    Schema Version: 1.0

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="forbid",  # Reject undocumented fields
    )

    # Schema version for backward compatibility tracking
    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Schema version for backward compatibility tracking"
    )

    # Trading invocation fields
    mode: Literal["trade", "bot"] | None = Field(
        default=None,
        description="Execution mode: 'trade' for trading, 'bot' for signal-only analysis",
    )
    trading_mode: Literal["paper", "live"] | None = Field(
        default=None,
        description="Trading mode: 'paper' for paper trading, 'live' for live trading",
    )
    arguments: list[str] | None = Field(
        default=None, description="Additional command line arguments for CLI invocation"
    )

    # Action invocation fields (optional)
    action: Literal["pnl_analysis"] | None = Field(
        default=None,
        description="Action to perform ('pnl_analysis' only; monthly_summary deprecated, use CLI)",
    )
    month: str | None = Field(
        default=None,
        description="Target month in YYYY-MM format (defaults to previous month)",
        pattern=r"^\d{4}-\d{2}$",
    )
    account_id: str | None = Field(
        default=None, description="Explicit account ID override for summary"
    )

    # P&L analysis fields (optional)
    pnl_type: Literal["weekly", "monthly"] | None = Field(
        default=None, description="P&L analysis type: 'weekly' or 'monthly'"
    )
    pnl_periods: int | None = Field(
        default=None,
        description="Number of periods back to analyze (must be positive)",
        ge=1,
    )
    pnl_period: str | None = Field(
        default=None,
        description="Alpaca period format (e.g., '1W', '1M', '3M', '1A')",
        pattern=r"^\d+[WMA]$",
    )
    pnl_detailed: bool | None = Field(
        default=None, description="Include detailed daily breakdown in P&L analysis"
    )

    # Common optional fields
    to: EmailStr | None = Field(
        default=None, description="Override recipient email address for summary"
    )
    subject: str | None = Field(default=None, description="Override email subject for summary")
    dry_run: bool | None = Field(
        default=None, description="When true, compute summary but do not send email"
    )

    # Event tracing fields (optional)
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for tracing related events across services",
    )
    causation_id: str | None = Field(
        default=None,
        description="Causation ID identifying the event that caused this invocation",
    )

    @model_validator(mode="after")
    def validate_pnl_fields(self) -> LambdaEvent:
        """Validate P&L analysis field combinations.

        Ensures that when action is 'pnl_analysis', either pnl_type or pnl_period
        is specified to define the analysis scope.

        Returns:
            Self with validated fields

        Raises:
            ValueError: If pnl_analysis action lacks required fields

        """
        if self.action == "pnl_analysis" and not self.pnl_type and not self.pnl_period:
            raise ValueError(
                "P&L analysis requires either 'pnl_type' or 'pnl_period' to be specified"
            )
        return self


# Public API exports
__all__ = ["LambdaEvent"]


# Backward compatibility - emit deprecation warning for legacy alias
def __getattr__(name: str) -> type:
    """Emit deprecation warning for legacy alias.

    Args:
        name: Attribute name being accessed

    Returns:
        LambdaEvent class if accessing LambdaEventDTO

    Raises:
        AttributeError: If attribute does not exist

    """
    import warnings

    if name == "LambdaEventDTO":
        warnings.warn(
            "LambdaEventDTO is deprecated; use LambdaEvent instead. "
            "This alias will be removed in version 3.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        return LambdaEvent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
