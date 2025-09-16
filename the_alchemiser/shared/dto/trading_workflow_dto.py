#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Trading workflow data transfer objects for orchestration module.

Provides typed DTOs for trading workflow results that replace dict[str, Any]
usage in trading orchestration business logic methods.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .portfolio_analysis_dto import AccountInfoDTO, OrderDataDTO, PositionDataDTO
from .signal_analysis_dto import SignalAnalysisResultDTO


class TradingWorkflowResultDTO(BaseModel):
    """DTO for trading workflow execution results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    success: bool = Field(..., description="Whether workflow succeeded")
    signal_analysis: SignalAnalysisResultDTO | None = Field(
        default=None, description="Signal analysis results"
    )
    account_info: AccountInfoDTO | None = Field(
        default=None, description="Account information"
    )
    current_positions: dict[str, PositionDataDTO] = Field(
        default_factory=dict, description="Current positions"
    )
    open_orders: list[OrderDataDTO] = Field(
        default_factory=list, description="Open orders"
    )
    execution_results: list["ExecutionResultDTO"] = Field(  # Forward reference to execution DTO
        default_factory=list, description="Execution results"
    )
    total_executed_value: Decimal = Field(
        default=Decimal("0"), ge=0, description="Total value executed"
    )
    trades_executed: int = Field(default=0, ge=0, description="Number of trades executed")
    workflow_duration_seconds: Decimal | None = Field(
        default=None, ge=0, description="Workflow execution time"
    )
    execution_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="When workflow was executed"
    )
    correlation_id: str = Field(..., min_length=1, description="Correlation ID")
    mode: Literal["live", "paper", "analysis"] = Field(
        default="analysis", description="Trading mode"
    )
    error_message: str | None = Field(
        default=None, description="Error message if workflow failed"
    )


class NotificationDataDTO(BaseModel):
    """DTO for trading notification data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    workflow_result: TradingWorkflowResultDTO = Field(
        ..., description="Trading workflow result"
    )
    mode: str = Field(..., min_length=1, description="Trading mode")
    notification_type: Literal["success", "error", "warning"] = Field(
        default="success", description="Type of notification"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(), description="Notification timestamp"
    )