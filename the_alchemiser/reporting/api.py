"""Business Unit: reporting | Status: current.

FastAPI surface for report generation.

Architecture Note:
    This module avoids importing ApplicationContainer to keep dependencies minimal.
    The ApplicationContainer pulls in heavy dependencies (pandas, numpy) via its
    import chain that are not needed for PDF report generation. Instead, we create
    a lightweight EventBus directly.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, ReportReady
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.middleware import CorrelationIdMiddleware, resolve_trace_context
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)


class AccountReportRequest(BaseModel):
    """Request schema for generating an account report."""

    correlation_id: str | None = Field(
        default=None, description="Workflow correlation identifier (header or body)"
    )
    causation_id: str | None = Field(
        default=None, description="Causation identifier for traceability (header or body)"
    )
    event_id: str | None = Field(default=None, description="Optional event identifier override")
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp for the event; defaults to now if omitted",
    )
    source_module: str = Field(default="reporting", description="Event source module")
    source_component: str | None = Field(
        default="api",
        description="Specific component emitting the event",
    )
    account_id: str = Field(..., description="Account ID to generate report for")
    snapshot_id: str | None = Field(
        default=None, description="Specific snapshot ID (uses latest if omitted)"
    )
    report_type: str = Field(default="account_summary", description="Type of report to generate")
    use_latest: bool = Field(
        default=True, description="Use latest snapshot if snapshot_id not provided"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded with the event",
    )


class ExecutionReportRequest(BaseModel):
    """Request schema for generating an execution report."""

    correlation_id: str | None = Field(
        default=None, description="Workflow correlation identifier (header or body)"
    )
    causation_id: str | None = Field(
        default=None, description="Causation identifier for traceability (header or body)"
    )
    event_id: str | None = Field(default=None, description="Optional event identifier override")
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp for the event; defaults to now if omitted",
    )
    source_module: str = Field(default="reporting", description="Event source module")
    source_component: str | None = Field(
        default="api",
        description="Specific component emitting the event",
    )
    execution_data: dict[str, Any] = Field(..., description="Execution data payload")
    trading_mode: str = Field(..., description="Trading mode: PAPER or LIVE")
    report_type: str = Field(default="trading_execution", description="Type of report to generate")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded with the event",
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def _create_lightweight_event_bus() -> EventBus:
    """Create a lightweight EventBus instance without heavy dependencies.

    This avoids importing ApplicationContainer which pulls in pandas/numpy.
    """
    return EventBus()


def create_app(event_bus: EventBus | None = None) -> FastAPI:
    """Create a FastAPI app for report generation.

    Args:
        event_bus: Optional EventBus to use. Creates lightweight one if not provided.

    Returns:
        FastAPI application instance.

    """
    bus = event_bus or _create_lightweight_event_bus()
    app = FastAPI(title="Reporting API", version="0.1.0")
    app.add_middleware(CorrelationIdMiddleware)
    app.state.event_bus = bus

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "healthy", "service": "reporting"}

    @app.get("/contracts")
    def contracts() -> dict[str, Any]:
        """Report contract versions supported by the service."""
        return {
            "service": "reporting",
            "supported_events": {"ReportReady": ReportReady.__event_version__},
        }

    @app.post("/reports/account")
    def generate_account_report(payload: AccountReportRequest, request: Request) -> dict[str, Any]:
        """Generate an account report from snapshot data.

        This endpoint triggers report generation and emits a ReportReady event
        upon successful completion.
        """
        try:
            correlation_id, causation_id = resolve_trace_context(
                payload.correlation_id, payload.causation_id, request
            )

            # Import services here to avoid import-time heavy dependencies
            from the_alchemiser.shared.repositories.account_snapshot_repository import (
                AccountSnapshotRepository,
            )

            from .service import ReportGeneratorService

            # Get configuration from environment
            table_name = os.environ.get("TRADE_LEDGER__TABLE_NAME", "alchemiser-trade-ledger-dev")
            s3_bucket = os.environ.get("REPORTS_S3_BUCKET", "the-alchemiser-reports")
            bucket_owner_account_id = os.environ.get("AWS_ACCOUNT_ID")

            logger.info(
                "Generating account report via API",
                account_id=payload.account_id,
                snapshot_id=payload.snapshot_id,
                report_type=payload.report_type,
                correlation_id=correlation_id,
            )

            # Initialize services with lightweight EventBus
            snapshot_repository = AccountSnapshotRepository(table_name=table_name)
            report_service = ReportGeneratorService(
                snapshot_repository=snapshot_repository,
                event_bus=bus,
                s3_bucket=s3_bucket,
                bucket_owner_account_id=bucket_owner_account_id,
            )

            # Generate report
            if payload.use_latest or payload.snapshot_id is None:
                report_ready_event = report_service.generate_report_from_latest_snapshot(
                    account_id=payload.account_id,
                    report_type=payload.report_type,
                    correlation_id=correlation_id,
                )
            else:
                report_ready_event = report_service.generate_report_from_snapshot_id(
                    account_id=payload.account_id,
                    snapshot_id=payload.snapshot_id,
                    report_type=payload.report_type,
                    correlation_id=correlation_id,
                )

            logger.info(
                "Account report generated successfully",
                report_id=report_ready_event.report_id,
                correlation_id=correlation_id,
            )

            return {"status": "published", "event": report_ready_event.to_dict()}

        except ValueError as e:
            logger.error(
                "Validation error in account report generation",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=422, detail=f"Validation error: {e}") from e
        except Exception as e:
            logger.error(
                "Failed to generate account report",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Report generation failed: {e}") from e

    @app.post("/reports/execution")
    def generate_execution_report(
        payload: ExecutionReportRequest, request: Request
    ) -> dict[str, Any]:
        """Generate an execution report from trading data.

        This endpoint triggers execution report generation and emits a ReportReady
        event upon successful completion.
        """
        try:
            correlation_id, causation_id = resolve_trace_context(
                payload.correlation_id, payload.causation_id, request
            )

            # Import services here to avoid import-time heavy dependencies
            from .execution_report_service import ExecutionReportService

            # Get S3 bucket from environment
            s3_bucket = os.environ.get("REPORTS_S3_BUCKET", "the-alchemiser-reports")
            bucket_owner_account_id = os.environ.get("AWS_ACCOUNT_ID")

            logger.info(
                "Generating execution report via API",
                trading_mode=payload.trading_mode,
                report_type=payload.report_type,
                correlation_id=correlation_id,
            )

            # Initialize services with lightweight EventBus
            execution_report_service = ExecutionReportService(
                event_bus=bus,
                s3_bucket=s3_bucket,
                bucket_owner_account_id=bucket_owner_account_id,
            )

            # Generate execution report
            report_ready_event = execution_report_service.generate_execution_report(
                execution_data=payload.execution_data,
                trading_mode=payload.trading_mode,
                correlation_id=correlation_id,
            )

            logger.info(
                "Execution report generated successfully",
                report_id=report_ready_event.report_id,
                correlation_id=correlation_id,
            )

            return {"status": "published", "event": report_ready_event.to_dict()}

        except ValueError as e:
            logger.error(
                "Validation error in execution report generation",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=422, detail=f"Validation error: {e}") from e
        except Exception as e:
            logger.error(
                "Failed to generate execution report",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Report generation failed: {e}") from e

    return app


__all__ = ["AccountReportRequest", "ExecutionReportRequest", "create_app"]
