"""Business Unit: reporting | Status: current.

Execution report service for creating PDF reports from trading execution data.

This service generates PDF reports from execution data (not account snapshots)
and is invoked by the notification service to attach reports to trading emails.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events import EventBus, ReportReady
from the_alchemiser.shared.logging import generate_request_id, get_logger

from .renderer import ReportRenderer

logger = get_logger(__name__)

__all__ = ["ExecutionReportService"]


class ExecutionReportService:
    """Service for generating and storing PDF execution reports."""

    def __init__(
        self,
        event_bus: EventBus,
        s3_bucket: str,
        bucket_owner_account_id: str | None = None,
    ) -> None:
        """Initialize execution report service.

        Args:
            event_bus: Event bus for publishing ReportReady events
            s3_bucket: S3 bucket name for storing reports
            bucket_owner_account_id: AWS account ID that owns the S3 bucket (for security)

        """
        self.event_bus = event_bus
        self.s3_bucket = s3_bucket
        self.bucket_owner_account_id = bucket_owner_account_id
        self.renderer = ReportRenderer()
        logger.debug("Execution report service initialized", s3_bucket=s3_bucket)

    def generate_execution_report(
        self,
        execution_data: dict[str, Any],
        trading_mode: str,
        correlation_id: str | None = None,
    ) -> ReportReady:
        """Generate PDF report from execution data and upload to S3.

        Args:
            execution_data: Execution data containing signals, portfolio, orders, summary
            trading_mode: Trading mode (PAPER or LIVE)
            correlation_id: Optional correlation ID for tracing

        Returns:
            ReportReady event with report metadata

        Raises:
            ValueError: If required execution data fields are missing

        """
        if correlation_id is None:
            correlation_id = generate_request_id()

        logger.info(
            "Generating execution report",
            trading_mode=trading_mode,
            correlation_id=correlation_id,
        )

        # Validate execution data
        self._validate_execution_data(execution_data)

        # Generate unique report ID
        report_id = f"report-{uuid.uuid4().hex[:12]}"

        # Build template context from execution data
        context = self._build_execution_context(execution_data, trading_mode, report_id)

        # Render PDF
        pdf_bytes, generation_metadata = self.renderer.render_execution_pdf(context)

        # Extract account_id from execution data (use a sensible default if missing)
        account_id = execution_data.get("account_id", "unknown")
        if not account_id or account_id == "unknown":
            # Try to extract from execution summary
            exec_summary = execution_data.get("execution_summary", {})
            account_id = exec_summary.get("account_id", "unknown")

        # Construct S3 key
        # Format: reports/{account_id}/{YYYY}/{MM}/execution_{YYYYMMDD_HHMMSS}_{report_id}.pdf
        now = datetime.now(UTC)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        s3_key = (
            f"reports/{account_id}/{now.year:04d}/"
            f"{now.month:02d}/execution_{timestamp_str}_{report_id}.pdf"
        )

        # Upload to S3
        self._upload_to_s3(pdf_bytes, s3_key)

        # Build S3 URI
        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"

        # Get timestamp from execution data or use now
        period_end_str = execution_data.get("timestamp", now.isoformat())
        period_start_str = execution_data.get("timestamp", now.isoformat())

        # Create ReportReady event
        report_ready_event = ReportReady(
            event_id=generate_request_id(),
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=now,
            source_module="reporting",
            source_component="ExecutionReportService",
            report_id=report_id,
            account_id=account_id,
            report_type="trading_execution",
            period_start=period_start_str,
            period_end=period_end_str,
            s3_bucket=self.s3_bucket,
            s3_key=s3_key,
            s3_uri=s3_uri,
            file_size_bytes=generation_metadata["file_size_bytes"],
            generation_time_ms=generation_metadata["generation_time_ms"],
            snapshot_id=f"execution-{timestamp_str}",  # Use execution timestamp as snapshot_id
            metadata={
                "report_version": "1.0",
                "trading_mode": trading_mode,
            },
        )

        # Publish event
        self.event_bus.publish(report_ready_event)

        logger.info(
            "Execution report generated and uploaded",
            report_id=report_id,
            s3_uri=s3_uri,
            file_size_bytes=generation_metadata["file_size_bytes"],
            generation_time_ms=generation_metadata["generation_time_ms"],
        )

        return report_ready_event

    def _validate_execution_data(self, execution_data: dict[str, Any]) -> None:
        """Validate that execution data has required fields.

        Args:
            execution_data: Execution data to validate

        Raises:
            ValueError: If required fields are missing

        """
        # These fields should exist but we'll provide defaults if missing
        # This is defensive - we don't want to fail PDF generation unnecessarily
        if not execution_data:
            raise ValueError("execution_data is empty")

        # Log warnings for missing optional fields
        optional_fields = [
            "strategy_signals",
            "consolidated_portfolio",
            "orders_executed",
            "execution_summary",
        ]
        for field in optional_fields:
            if field not in execution_data:
                logger.warning(
                    f"Optional field '{field}' missing from execution_data",
                    extra={"field": field},
                )

    def _build_execution_context(
        self, execution_data: dict[str, Any], trading_mode: str, report_id: str
    ) -> dict[str, Any]:
        """Build template context from execution data.

        Args:
            execution_data: Execution data containing signals, portfolio, orders, summary
            trading_mode: Trading mode (PAPER or LIVE)
            report_id: Unique report identifier

        Returns:
            Dictionary of template context variables

        """
        now = datetime.now(UTC)

        # Extract data sections with defaults
        strategy_signals = execution_data.get("strategy_signals", {})
        consolidated_portfolio = execution_data.get("consolidated_portfolio", {})
        orders_executed = execution_data.get("orders_executed", [])
        execution_summary = execution_data.get("execution_summary", {})

        # Build context
        return {
            "trading_mode": trading_mode,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "correlation_id": execution_data.get("correlation_id", "N/A"),
            "report_id": report_id,
            "success": execution_summary.get("success", True),
            "strategy_signals": self._format_strategy_signals(strategy_signals),
            "portfolio_allocations": self._format_portfolio_allocations(consolidated_portfolio),
            "orders": self._format_orders(orders_executed),
            "execution_summary": self._format_execution_summary(execution_summary),
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    def _format_strategy_signals(self, signals: dict[str, Any]) -> list[dict[str, Any]]:
        """Format strategy signals for template.

        Args:
            signals: Strategy signals dictionary

        Returns:
            List of formatted signal dictionaries

        """
        formatted_signals = []

        for strategy_name, signal_data in signals.items():
            if not isinstance(signal_data, dict):
                continue

            formatted_signal = {
                "strategy_name": strategy_name,
                "signal": signal_data.get("signal", "HOLD"),
                "reasoning": signal_data.get("reasoning", signal_data.get("reason", "N/A")),
                "confidence": signal_data.get("confidence", "N/A"),
            }
            formatted_signals.append(formatted_signal)

        return formatted_signals

    def _format_portfolio_allocations(self, portfolio: dict[str, Any]) -> list[dict[str, Any]]:
        """Format portfolio allocations for template.

        Args:
            portfolio: Consolidated portfolio dictionary

        Returns:
            List of formatted allocation dictionaries

        """
        formatted_allocations = []

        # Handle different portfolio structures
        # Try to extract target_allocations if it's a nested structure
        if isinstance(portfolio, dict):
            allocations = portfolio.get("target_allocations", portfolio)
        else:
            allocations = {}

        for symbol, allocation in allocations.items():
            if isinstance(allocation, (int, float)):
                formatted_allocations.append(
                    {
                        "symbol": symbol,
                        "target_allocation": float(allocation),
                    }
                )

        return formatted_allocations

    def _format_orders(self, orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format orders for template.

        Args:
            orders: List of executed orders

        Returns:
            List of formatted order dictionaries

        """
        formatted_orders = []

        for order in orders:
            if not isinstance(order, dict):
                continue

            formatted_order = {
                "symbol": order.get("symbol", "N/A"),
                "side": order.get("side", "N/A"),
                "quantity": order.get("qty", order.get("quantity", 0)),
                "price": order.get("filled_avg_price", order.get("price", 0)),
                "status": order.get("status", "unknown"),
                "order_id": order.get("order_id", order.get("id", "N/A")),
            }
            formatted_orders.append(formatted_order)

        return formatted_orders

    def _format_execution_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Format execution summary for template.

        Args:
            summary: Execution summary dictionary

        Returns:
            Formatted summary dictionary

        """
        return {
            "total_orders": summary.get("orders_placed", len(summary.get("orders_executed", []))),
            "successful_orders": summary.get("orders_succeeded", 0),
            "failed_orders": summary.get("orders_failed", 0),
            "total_value": summary.get("total_trade_value", 0),
            "execution_time": summary.get("execution_duration_ms", 0),
        }

    def _upload_to_s3(self, pdf_bytes: bytes, s3_key: str) -> None:
        """Upload PDF to S3 bucket.

        Args:
            pdf_bytes: PDF content as bytes
            s3_key: S3 key (path) for the object

        Raises:
            Exception: If S3 upload fails

        """
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        logger.debug("Uploading PDF to S3", s3_key=s3_key, size_bytes=len(pdf_bytes))

        try:
            s3_client = boto3.client("s3")

            # Calculate checksum for data integrity
            checksum = hashlib.sha256(pdf_bytes).hexdigest()

            # Build put_object parameters
            put_params: dict[str, Any] = {
                "Bucket": self.s3_bucket,
                "Key": s3_key,
                "Body": pdf_bytes,
                "ContentType": "application/pdf",
                "Metadata": {
                    "sha256": checksum,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "report_type": "trading_execution",
                },
            }

            # Add ExpectedBucketOwner if configured (security best practice)
            if self.bucket_owner_account_id:
                put_params["ExpectedBucketOwner"] = self.bucket_owner_account_id

            # Upload with metadata
            s3_client.put_object(**put_params)

            logger.info("PDF uploaded to S3", s3_key=s3_key, checksum=checksum)

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to upload PDF to S3", s3_key=s3_key, error=str(e))
            raise
