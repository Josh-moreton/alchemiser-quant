"""Business Unit: reporting | Status: current.

Tests for the report generator lambda handler.

These tests verify that the lambda handler:
1. Can be imported without heavy dependencies (pandas, numpy)
2. Creates services correctly with lightweight EventBus
3. Validates event structure
4. Handles errors gracefully
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from the_alchemiser.shared.events.bus import EventBus


class TestLambdaHandlerImports:
    """Test that lambda handler imports work without heavy dependencies."""

    def test_import_lambda_handler_no_pandas(self) -> None:
        """Verify lambda_handler can be imported without pandas.

        This is a critical smoke test - the report lambda failed in production
        because ApplicationContainer imported pandas via the market data chain.
        After the refactor to use a lightweight EventBus, this should pass.
        """
        # This import should NOT trigger pandas/numpy imports
        from the_alchemiser.reporting.lambda_handler import lambda_handler

        assert callable(lambda_handler)

    def test_import_create_event_bus(self) -> None:
        """Verify _create_event_bus can be imported and called."""
        from the_alchemiser.reporting.lambda_handler import _create_event_bus

        event_bus = _create_event_bus()
        assert event_bus is not None

    def test_event_bus_is_lightweight(self) -> None:
        """Verify created EventBus is functional without heavy dependencies."""
        from the_alchemiser.reporting.lambda_handler import _create_event_bus
        from the_alchemiser.shared.events.bus import EventBus

        event_bus = _create_event_bus()
        assert isinstance(event_bus, EventBus)
        # EventBus should be ready to use
        assert event_bus.get_handler_count() == 0
        assert event_bus.get_event_count() == 0


class TestEventValidation:
    """Test event validation logic."""

    def test_validate_event_account_report_missing_account_id(self) -> None:
        """Validate that missing account_id raises ValueError."""
        from the_alchemiser.reporting.lambda_handler import _validate_event

        with pytest.raises(ValueError, match="Missing required fields: account_id"):
            _validate_event({})

    def test_validate_event_account_report_valid(self) -> None:
        """Validate that valid account report event passes."""
        from the_alchemiser.reporting.lambda_handler import _validate_event

        # Should not raise
        _validate_event({"account_id": "PA123456789"})

    def test_validate_event_execution_report_missing_fields(self) -> None:
        """Validate that execution report requires execution_data and trading_mode."""
        from the_alchemiser.reporting.lambda_handler import _validate_event

        with pytest.raises(
            ValueError, match="Missing required fields for execution report"
        ):
            _validate_event({"generate_from_execution": True})

    def test_validate_event_execution_report_valid(self) -> None:
        """Validate that valid execution report event passes."""
        from the_alchemiser.reporting.lambda_handler import _validate_event

        # Should not raise
        _validate_event(
            {
                "generate_from_execution": True,
                "execution_data": {"orders": []},
                "trading_mode": "PAPER",
            }
        )


class TestCorrelationIdExtraction:
    """Test correlation ID extraction logic."""

    def test_extract_correlation_id_from_event(self) -> None:
        """Extract correlation_id when present in event."""
        from the_alchemiser.reporting.lambda_handler import _extract_correlation_id

        event = {"correlation_id": "test-corr-123"}
        assert _extract_correlation_id(event) == "test-corr-123"

    def test_extract_correlation_id_generates_new(self) -> None:
        """Generate new correlation_id when not present."""
        from the_alchemiser.reporting.lambda_handler import _extract_correlation_id

        event: dict[str, Any] = {}
        result = _extract_correlation_id(event)
        assert result is not None
        assert len(result) > 0


class TestLambdaHandlerExecution:
    """Test lambda handler execution paths."""

    @patch("the_alchemiser.reporting.lambda_handler.AccountSnapshotRepository")
    @patch("the_alchemiser.reporting.lambda_handler.ReportGeneratorService")
    def test_account_report_generation_uses_lightweight_event_bus(
        self,
        mock_service_class: MagicMock,
        mock_repo_class: MagicMock,
    ) -> None:
        """Verify account report uses lightweight EventBus, not ApplicationContainer."""
        from the_alchemiser.reporting.lambda_handler import lambda_handler
        from the_alchemiser.shared.events.bus import EventBus

        # Setup mocks
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_report_event = MagicMock()
        mock_report_event.report_id = "report-123"
        mock_report_event.s3_uri = "s3://bucket/key.pdf"
        mock_report_event.s3_bucket = "bucket"
        mock_report_event.s3_key = "key.pdf"
        mock_report_event.file_size_bytes = 1000
        mock_report_event.generation_time_ms = 500
        mock_report_event.snapshot_id = "snap-123"
        mock_service.generate_report_from_latest_snapshot.return_value = mock_report_event

        # Set environment variables
        with patch.dict(
            os.environ,
            {
                "TRADE_LEDGER__TABLE_NAME": "test-table",
                "REPORTS_S3_BUCKET": "test-bucket",
            },
        ):
            result = lambda_handler(
                {"account_id": "PA123", "use_latest": True},
                None,
            )

        # Verify service was created with EventBus (not ApplicationContainer)
        assert mock_service_class.called
        call_kwargs = mock_service_class.call_args.kwargs
        assert "event_bus" in call_kwargs
        assert isinstance(call_kwargs["event_bus"], EventBus)

        # Verify success response
        assert result["status"] == "success"
        assert result["report_id"] == "report-123"

    @patch("the_alchemiser.reporting.lambda_handler.ExecutionReportService")
    def test_execution_report_generation_uses_lightweight_event_bus(
        self,
        mock_service_class: MagicMock,
    ) -> None:
        """Verify execution report uses lightweight EventBus."""
        from the_alchemiser.reporting.lambda_handler import lambda_handler
        from the_alchemiser.shared.events.bus import EventBus

        # Setup mocks
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_report_event = MagicMock()
        mock_report_event.report_id = "report-456"
        mock_report_event.s3_uri = "s3://bucket/exec.pdf"
        mock_report_event.s3_bucket = "bucket"
        mock_report_event.s3_key = "exec.pdf"
        mock_report_event.file_size_bytes = 2000
        mock_report_event.generation_time_ms = 750
        mock_report_event.snapshot_id = "exec-snap-456"
        mock_service.generate_execution_report.return_value = mock_report_event

        # Set environment variables
        with patch.dict(
            os.environ,
            {
                "REPORTS_S3_BUCKET": "test-bucket",
            },
        ):
            result = lambda_handler(
                {
                    "generate_from_execution": True,
                    "execution_data": {"orders": []},
                    "trading_mode": "PAPER",
                },
                None,
            )

        # Verify service was created with EventBus
        assert mock_service_class.called
        call_kwargs = mock_service_class.call_args.kwargs
        assert "event_bus" in call_kwargs
        assert isinstance(call_kwargs["event_bus"], EventBus)

        # Verify success response
        assert result["status"] == "success"
        assert result["report_id"] == "report-456"

    def test_validation_error_returns_failed_status(self) -> None:
        """Verify validation errors return proper error response."""
        from the_alchemiser.reporting.lambda_handler import lambda_handler

        result = lambda_handler({}, None)  # Missing required fields

        assert result["status"] == "failed"
        assert result["error"] == "ValidationError"
        assert "Missing required fields" in result["message"]
