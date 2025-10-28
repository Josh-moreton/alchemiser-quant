"""Tests for ExecutionReportService."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from the_alchemiser.reporting.execution_report_service import ExecutionReportService
from the_alchemiser.shared.events import ReportReady


@pytest.fixture
def mock_event_bus() -> Mock:
    """Create a mock event bus."""
    return Mock()


@pytest.fixture
def sample_execution_data() -> dict[str, object]:
    """Create sample execution data."""
    return {
        "account_id": "test-account-123",
        "correlation_id": "corr-123",
        "timestamp": datetime.now(UTC).isoformat(),
        "strategy_signals": {
            "nuclear_strategy": {
                "signal": "BUY",
                "reasoning": "Market conditions favorable",
                "confidence": "HIGH",
            },
            "tecl_strategy": {
                "signal": "HOLD",
                "reasoning": "Waiting for better entry",
                "confidence": "MEDIUM",
            },
        },
        "consolidated_portfolio": {
            "target_allocations": {
                "TQQQ": 0.4,
                "TECL": 0.3,
                "SOXL": 0.3,
            }
        },
        "orders_executed": [
            {
                "symbol": "TQQQ",
                "side": "buy",
                "qty": 100,
                "filled_avg_price": 45.50,
                "status": "filled",
                "order_id": "order-123",
            },
            {
                "symbol": "TECL",
                "side": "buy",
                "qty": 50,
                "filled_avg_price": 32.25,
                "status": "filled",
                "order_id": "order-456",
            },
        ],
        "execution_summary": {
            "success": True,
            "orders_placed": 2,
            "orders_succeeded": 2,
            "orders_failed": 0,
            "total_trade_value": 6162.50,
            "execution_duration_ms": 1250,
        },
    }


class TestExecutionReportService:
    """Test execution report service."""

    def test_service_initialization(self, mock_event_bus: Mock) -> None:
        """Test service initializes correctly."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        assert service.event_bus is mock_event_bus
        assert service.s3_bucket == "test-bucket"
        assert service.renderer is not None

    @patch("the_alchemiser.reporting.execution_report_service.ExecutionReportService._upload_to_s3")
    @patch("the_alchemiser.reporting.execution_report_service.ReportRenderer.render_execution_pdf")
    def test_generate_execution_report(
        self,
        mock_render: MagicMock,
        mock_upload: MagicMock,
        mock_event_bus: Mock,
        sample_execution_data: dict[str, object],
    ) -> None:
        """Test execution report generation."""
        # Setup mocks
        mock_pdf_bytes = b"fake-pdf-content"
        mock_metadata = {
            "file_size_bytes": len(mock_pdf_bytes),
            "generation_time_ms": 1500,
        }
        mock_render.return_value = (mock_pdf_bytes, mock_metadata)

        # Create service
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        # Generate report
        report_event = service.generate_execution_report(
            execution_data=sample_execution_data,
            trading_mode="PAPER",
            correlation_id="corr-123",
        )

        # Verify report event
        assert isinstance(report_event, ReportReady)
        assert report_event.report_type == "trading_execution"
        assert report_event.s3_bucket == "test-bucket"
        assert "execution_" in report_event.s3_key
        assert report_event.file_size_bytes == len(mock_pdf_bytes)
        assert report_event.generation_time_ms == 1500
        assert report_event.correlation_id == "corr-123"

        # Verify renderer was called
        mock_render.assert_called_once()
        context = mock_render.call_args[0][0]
        assert context["trading_mode"] == "PAPER"
        assert context["success"] is True
        assert len(context["strategy_signals"]) == 2
        assert len(context["orders"]) == 2

        # Verify S3 upload was called
        mock_upload.assert_called_once()

        # Verify event was published
        mock_event_bus.publish.assert_called_once()

    def test_validate_execution_data_empty(self, mock_event_bus: Mock) -> None:
        """Test validation fails for empty execution data."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        with pytest.raises(ValueError, match="execution_data is empty"):
            service._validate_execution_data({})

    def test_format_strategy_signals(self, mock_event_bus: Mock) -> None:
        """Test strategy signals formatting."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        signals = {
            "strategy1": {
                "signal": "BUY",
                "reasoning": "Test reason",
                "confidence": "HIGH",
            },
            "strategy2": {
                "signal": "SELL",
                "reason": "Alternative reason field",  # Test 'reason' fallback
            },
        }

        formatted = service._format_strategy_signals(signals)

        assert len(formatted) == 2
        assert formatted[0]["strategy_name"] == "strategy1"
        assert formatted[0]["signal"] == "BUY"
        assert formatted[0]["reasoning"] == "Test reason"
        assert formatted[1]["strategy_name"] == "strategy2"
        assert formatted[1]["reasoning"] == "Alternative reason field"

    def test_format_portfolio_allocations(self, mock_event_bus: Mock) -> None:
        """Test portfolio allocations formatting."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        # Test nested structure
        portfolio = {
            "target_allocations": {
                "SPY": 0.5,
                "QQQ": 0.3,
                "IWM": 0.2,
            }
        }

        formatted = service._format_portfolio_allocations(portfolio)

        assert len(formatted) == 3
        assert formatted[0]["symbol"] == "SPY"
        assert formatted[0]["target_allocation"] == 0.5

        # Test flat structure
        flat_portfolio = {
            "AAPL": 0.6,
            "MSFT": 0.4,
        }

        formatted_flat = service._format_portfolio_allocations(flat_portfolio)
        assert len(formatted_flat) == 2

    def test_format_orders(self, mock_event_bus: Mock) -> None:
        """Test orders formatting."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        orders = [
            {
                "symbol": "AAPL",
                "side": "buy",
                "qty": 100,
                "filled_avg_price": 150.50,
                "status": "filled",
                "order_id": "order-123",
            },
            {
                "symbol": "MSFT",
                "side": "sell",
                "quantity": 50,  # Alternative field name
                "price": 300.25,  # Alternative field name
                "status": "failed",
                "id": "order-456",  # Alternative field name
            },
        ]

        formatted = service._format_orders(orders)

        assert len(formatted) == 2
        assert formatted[0]["symbol"] == "AAPL"
        assert formatted[0]["quantity"] == 100
        assert formatted[0]["price"] == 150.50
        assert formatted[1]["symbol"] == "MSFT"
        assert formatted[1]["quantity"] == 50
        assert formatted[1]["price"] == 300.25

    def test_format_execution_summary(self, mock_event_bus: Mock) -> None:
        """Test execution summary formatting."""
        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        summary = {
            "orders_placed": 5,
            "orders_succeeded": 4,
            "orders_failed": 1,
            "total_trade_value": 10000.50,
            "execution_duration_ms": 2500,
        }

        formatted = service._format_execution_summary(summary)

        assert formatted["total_orders"] == 5
        assert formatted["successful_orders"] == 4
        assert formatted["failed_orders"] == 1
        assert formatted["total_value"] == 10000.50
        assert formatted["execution_time"] == 2500

    @patch("boto3.client")
    def test_upload_to_s3(
        self,
        mock_boto_client: MagicMock,
        mock_event_bus: Mock,
    ) -> None:
        """Test S3 upload with ExpectedBucketOwner."""
        mock_s3_client = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        def client_factory(service_name: str) -> Mock:
            if service_name == "s3":
                return mock_s3_client
            if service_name == "sts":
                return mock_sts_client
            return Mock()

        mock_boto_client.side_effect = client_factory

        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        pdf_bytes = b"test-pdf-content"
        s3_key = "reports/test/2024/10/execution_test.pdf"

        service._upload_to_s3(pdf_bytes, s3_key)

        # Verify STS client was called to get account ID
        mock_sts_client.get_caller_identity.assert_called_once()

        # Verify S3 client was called with ExpectedBucketOwner
        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == s3_key
        assert call_kwargs["Body"] == pdf_bytes
        assert call_kwargs["ContentType"] == "application/pdf"
        assert call_kwargs["ExpectedBucketOwner"] == "123456789012"
        assert "Metadata" in call_kwargs
        assert "sha256" in call_kwargs["Metadata"]

    @patch("boto3.client")
    def test_upload_to_s3_caches_account_id(
        self,
        mock_boto_client: MagicMock,
        mock_event_bus: Mock,
    ) -> None:
        """Test that AWS account ID is cached and STS is only called once."""
        mock_s3_client = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        def client_factory(service_name: str) -> Mock:
            if service_name == "s3":
                return mock_s3_client
            if service_name == "sts":
                return mock_sts_client
            return Mock()

        mock_boto_client.side_effect = client_factory

        service = ExecutionReportService(
            event_bus=mock_event_bus,
            s3_bucket="test-bucket",
        )

        pdf_bytes = b"test-pdf-content"
        s3_key_1 = "reports/test/2024/10/execution_test1.pdf"
        s3_key_2 = "reports/test/2024/10/execution_test2.pdf"

        # Upload twice
        service._upload_to_s3(pdf_bytes, s3_key_1)
        service._upload_to_s3(pdf_bytes, s3_key_2)

        # Verify STS client was only called once (caching works)
        mock_sts_client.get_caller_identity.assert_called_once()

        # Verify S3 client was called twice with same account ID
        assert mock_s3_client.put_object.call_count == 2
        for call in mock_s3_client.put_object.call_args_list:
            call_kwargs = call[1]
            assert call_kwargs["ExpectedBucketOwner"] == "123456789012"
