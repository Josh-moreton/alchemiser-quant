"""Contract tests for the Reporting FastAPI surface.

These tests verify the API contract for report generation endpoints,
ensuring proper request validation, event emission, and error handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from the_alchemiser.shared.events import EventBus, ReportReady
from the_alchemiser.reporting.api import create_app


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_endpoint_returns_healthy(self) -> None:
        """Health check endpoint returns healthy status."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "reporting"}


class TestContractsEndpoint:
    """Tests for the /contracts endpoint."""

    def test_contracts_endpoint_reports_versions(self) -> None:
        """Contract probe should surface supported events."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/contracts")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "reporting"
        assert body["supported_events"]["ReportReady"] == ReportReady.__event_version__


class TestAccountReportEndpoint:
    """Tests for the /reports/account endpoint."""

    def test_account_report_missing_required_fields(self) -> None:
        """Missing required fields returns 422."""
        app = create_app()
        client = TestClient(app)

        # Missing account_id
        invalid_payload = {"report_type": "account_summary"}

        response = client.post("/reports/account", json=invalid_payload)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_account_report_uses_header_correlation_id(self) -> None:
        """Middleware should supply correlation/causation IDs from headers."""
        app = create_app()
        client = TestClient(app)

        payload = {
            "account_id": "test-account-123",
            "report_type": "account_summary",
        }

        headers = {
            "X-Correlation-ID": "corr-from-header",
            "X-Causation-ID": "cause-header",
        }

        # Patch at the source modules where imports happen
        with patch(
            "the_alchemiser.shared.repositories.account_snapshot_repository.AccountSnapshotRepository"
        ) as mock_repo_class, patch(
            "the_alchemiser.reporting.service.ReportGeneratorService"
        ) as mock_service_class:
            # Setup mocks
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_report_event = Mock(spec=ReportReady)
            mock_report_event.report_id = "report-123"
            mock_report_event.to_dict.return_value = {
                "event_type": "ReportReady",
                "report_id": "report-123",
                "correlation_id": "corr-from-header",
            }
            mock_service.generate_report_from_latest_snapshot.return_value = mock_report_event
            mock_service_class.return_value = mock_service

            response = client.post("/reports/account", json=payload, headers=headers)

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "published"
            assert body["event"]["correlation_id"] == "corr-from-header"

    def test_account_report_success(self) -> None:
        """Successful account report generation returns event."""
        event_bus = EventBus()
        app = create_app(event_bus=event_bus)
        client = TestClient(app)

        with patch(
            "the_alchemiser.shared.repositories.account_snapshot_repository.AccountSnapshotRepository"
        ) as mock_repo_class, patch(
            "the_alchemiser.reporting.service.ReportGeneratorService"
        ) as mock_service_class:
            # Setup mocks
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_report_event = Mock(spec=ReportReady)
            mock_report_event.report_id = "report-456"
            mock_report_event.to_dict.return_value = {
                "event_type": "ReportReady",
                "report_id": "report-456",
                "account_id": "test-account",
                "s3_uri": "s3://bucket/key.pdf",
            }
            mock_service.generate_report_from_latest_snapshot.return_value = mock_report_event
            mock_service_class.return_value = mock_service

            payload = {
                "correlation_id": "corr-test",
                "causation_id": "cause-test",
                "account_id": "test-account",
                "report_type": "account_summary",
                "use_latest": True,
            }

            response = client.post("/reports/account", json=payload)

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "published"
            assert body["event"]["report_id"] == "report-456"

    def test_account_report_service_failure(self) -> None:
        """Service failure returns 500."""
        app = create_app()
        client = TestClient(app)

        with patch(
            "the_alchemiser.shared.repositories.account_snapshot_repository.AccountSnapshotRepository"
        ) as mock_repo_class, patch(
            "the_alchemiser.reporting.service.ReportGeneratorService"
        ) as mock_service_class:
            # Setup mocks
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_service = Mock()
            mock_service.generate_report_from_latest_snapshot.side_effect = RuntimeError(
                "S3 connection failed"
            )
            mock_service_class.return_value = mock_service

            payload = {
                "correlation_id": "corr-test",
                "account_id": "test-account",
            }

            response = client.post("/reports/account", json=payload)

            assert response.status_code == 500
            assert "Report generation failed" in response.json()["detail"]


class TestExecutionReportEndpoint:
    """Tests for the /reports/execution endpoint."""

    def test_execution_report_missing_required_fields(self) -> None:
        """Missing required fields returns 422."""
        app = create_app()
        client = TestClient(app)

        # Missing execution_data and trading_mode
        invalid_payload = {"report_type": "trading_execution"}

        response = client.post("/reports/execution", json=invalid_payload)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_execution_report_success(self) -> None:
        """Successful execution report generation returns event."""
        event_bus = EventBus()
        app = create_app(event_bus=event_bus)
        client = TestClient(app)

        with patch(
            "the_alchemiser.reporting.execution_report_service.ExecutionReportService"
        ) as mock_service_class:
            # Setup mock
            mock_service = Mock()
            mock_report_event = Mock(spec=ReportReady)
            mock_report_event.report_id = "exec-report-789"
            mock_report_event.to_dict.return_value = {
                "event_type": "ReportReady",
                "report_id": "exec-report-789",
                "s3_uri": "s3://bucket/exec-key.pdf",
            }
            mock_service.generate_execution_report.return_value = mock_report_event
            mock_service_class.return_value = mock_service

            payload = {
                "correlation_id": "corr-exec",
                "causation_id": "cause-exec",
                "execution_data": {"orders": [], "success": True},
                "trading_mode": "PAPER",
                "report_type": "trading_execution",
            }

            response = client.post("/reports/execution", json=payload)

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "published"
            assert body["event"]["report_id"] == "exec-report-789"

    def test_execution_report_service_failure(self) -> None:
        """Service failure returns 500."""
        app = create_app()
        client = TestClient(app)

        with patch(
            "the_alchemiser.reporting.execution_report_service.ExecutionReportService"
        ) as mock_service_class:
            # Setup mock
            mock_service = Mock()
            mock_service.generate_execution_report.side_effect = RuntimeError(
                "PDF generation failed"
            )
            mock_service_class.return_value = mock_service

            payload = {
                "correlation_id": "corr-exec",
                "execution_data": {"orders": []},
                "trading_mode": "PAPER",
            }

            response = client.post("/reports/execution", json=payload)

            assert response.status_code == 500
            assert "Report generation failed" in response.json()["detail"]

    def test_execution_report_uses_header_correlation_id(self) -> None:
        """Middleware should supply correlation/causation IDs from headers."""
        app = create_app()
        client = TestClient(app)

        with patch(
            "the_alchemiser.reporting.execution_report_service.ExecutionReportService"
        ) as mock_service_class:
            # Setup mock
            mock_service = Mock()
            mock_report_event = Mock(spec=ReportReady)
            mock_report_event.report_id = "exec-report-header"
            mock_report_event.to_dict.return_value = {
                "event_type": "ReportReady",
                "report_id": "exec-report-header",
                "correlation_id": "header-corr-id",
            }
            mock_service.generate_execution_report.return_value = mock_report_event
            mock_service_class.return_value = mock_service

            payload = {
                "execution_data": {"orders": []},
                "trading_mode": "LIVE",
            }

            headers = {
                "X-Correlation-ID": "header-corr-id",
                "X-Causation-ID": "header-cause-id",
            }

            response = client.post("/reports/execution", json=payload, headers=headers)

            assert response.status_code == 200
            body = response.json()
            assert body["event"]["correlation_id"] == "header-corr-id"


class TestModuleEntrypoint:
    """Tests for the reporting module standalone bootstrap."""

    def test_main_returns_lightweight_context(self) -> None:
        """Main should return a LightweightReportingContext."""
        from the_alchemiser.reporting.__main__ import (
            LightweightReportingContext,
            main,
        )

        context = main(env="testing")

        assert isinstance(context, LightweightReportingContext)
        assert context.environment == "testing"
        assert context.transports is not None
        assert context.transports.event_bus is not None

    def test_main_accepts_custom_transports(self) -> None:
        """Main should accept injected transports."""
        from the_alchemiser.reporting.__main__ import main
        from the_alchemiser.reporting.adapters.transports import ReportingTransports
        from the_alchemiser.shared.events.bus import EventBus

        custom_bus = EventBus()
        custom_transports = ReportingTransports(event_bus=custom_bus)

        context = main(env="testing", transports=custom_transports)

        assert context.transports.event_bus is custom_bus
