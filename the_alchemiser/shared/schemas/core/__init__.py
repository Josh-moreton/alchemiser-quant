"""Core schemas module."""

from .base import Result
from .common import AllocationComparison, MultiStrategyExecutionResult, MultiStrategySummary
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)

__all__ = [
    "AllocationComparison",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "Result",
]