#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""

    count: int
    errors: list[ErrorDetailInfo]


class ErrorReportSummary(TypedDict):
    """Comprehensive error report summary."""

    critical: ErrorSummaryData | None
    trading: ErrorSummaryData | None
    data: ErrorSummaryData | None
    strategy: ErrorSummaryData | None
    configuration: ErrorSummaryData | None
    notification: ErrorSummaryData | None
    warning: ErrorSummaryData | None


# Error Notification Types
class ErrorNotificationData(TypedDict):
    """Data for error notifications."""

    severity: str
    priority: str
    title: str
    error_report: str
    html_content: str


class ErrorContextData(TypedDict):
    """Context information for error tracking."""

    operation: str
    component: str
    function_name: str | None
    request_id: str | None
    user_id: str | None
    session_id: str | None
    additional_data: dict[str, Any]
    timestamp: str
