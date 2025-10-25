"""Tests for PDF report renderer."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from the_alchemiser.reporting.renderer import ReportRenderer
from the_alchemiser.shared.schemas.account_snapshot import (
    AccountSnapshot,
    AlpacaAccountData,
    AlpacaOrderData,
    AlpacaPositionData,
)


@pytest.fixture
def sample_snapshot() -> AccountSnapshot:
    """Create a sample account snapshot for testing."""
    alpaca_account = AlpacaAccountData(
        account_id="test-account-123",
        account_number="PA123456789",
        status="ACTIVE",
        crypto_status="ACTIVE",
        currency="USD",
        buying_power=Decimal("50000.00"),
        cash=Decimal("10000.00"),
        portfolio_value=Decimal("100000.00"),
        equity=Decimal("100000.00"),
        last_equity=Decimal("98000.00"),
        long_market_value=Decimal("90000.00"),
        short_market_value=Decimal("0"),
        initial_margin=Decimal("0"),
        maintenance_margin=Decimal("0"),
        daytrade_count=0,
        pattern_day_trader=False,
        trading_blocked=False,
        transfers_blocked=False,
        account_blocked=False,
        created_at=datetime.now(UTC),
        shorting_enabled=True,
        multiplier=Decimal("2"),
        last_maintenance_margin=Decimal("0"),
    )

    positions = [
        AlpacaPositionData(
            asset_id="test-asset-1",
            symbol="SPY",
            exchange="NASDAQ",
            asset_class="us_equity",
            avg_entry_price=Decimal("450.00"),
            qty=Decimal("100"),
            qty_available=Decimal("100"),
            side="long",
            market_value=Decimal("45000.00"),
            cost_basis=Decimal("45000.00"),
            unrealized_pl=Decimal("0.00"),
            unrealized_plpc=Decimal("0.00"),
            unrealized_intraday_pl=Decimal("0.00"),
            unrealized_intraday_plpc=Decimal("0.00"),
            current_price=Decimal("450.00"),
        )
    ]

    orders = [
        AlpacaOrderData(
            order_id="order-123",
            symbol="SPY",
            side="buy",
            order_type="market",
            qty=Decimal("100"),
            filled_qty=Decimal("100"),
            status="filled",
            time_in_force="day",
            submitted_at=datetime.now(UTC),
        )
    ]

    return AccountSnapshot(
        snapshot_id="snap-123",
        snapshot_version="1.0",
        account_id="test-account-123",
        period_start=datetime.now(UTC),
        period_end=datetime.now(UTC),
        correlation_id="corr-123",
        created_at=datetime.now(UTC),
        alpaca_account=alpaca_account,
        alpaca_positions=positions,
        alpaca_orders=orders,
        checksum="abc123",
    )


class TestReportRenderer:
    """Test report renderer."""

    def test_renderer_initialization(self) -> None:
        """Test renderer initialization."""
        renderer = ReportRenderer()
        assert renderer.jinja_env is not None

    def test_render_html(self, sample_snapshot: AccountSnapshot) -> None:
        """Test HTML rendering from snapshot."""
        renderer = ReportRenderer()
        html = renderer.render_html(sample_snapshot)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "The Alchemiser" in html
        assert "Account Performance Report" in html
        assert sample_snapshot.account_id in html

    def test_render_html_with_metadata(self, sample_snapshot: AccountSnapshot) -> None:
        """Test HTML rendering with custom metadata."""
        renderer = ReportRenderer()
        metadata = {"report_version": "2.0"}
        html = renderer.render_html(sample_snapshot, metadata)

        assert "2.0" in html

    def test_prepare_template_context(self, sample_snapshot: AccountSnapshot) -> None:
        """Test template context preparation."""
        renderer = ReportRenderer()
        context = renderer._prepare_template_context(sample_snapshot, {})

        assert "account_id" in context
        assert "snapshot_id" in context
        assert "metrics" in context
        assert "positions" in context
        assert "recent_orders" in context

        # Check positions are formatted correctly
        assert len(context["positions"]) == 1
        assert context["positions"][0]["symbol"] == "SPY"
        assert isinstance(context["positions"][0]["qty"], float)

        # Check orders are formatted correctly
        assert len(context["recent_orders"]) == 1
        assert context["recent_orders"][0]["symbol"] == "SPY"

    @patch("the_alchemiser.reporting.renderer.ReportRenderer._html_to_pdf_with_playwright")
    def test_render_pdf_mock(
        self, mock_pdf_gen: MagicMock, sample_snapshot: AccountSnapshot
    ) -> None:
        """Test PDF rendering with mocked Playwright."""
        mock_pdf_bytes = b"fake-pdf-content"
        mock_pdf_gen.return_value = mock_pdf_bytes

        renderer = ReportRenderer()
        pdf_bytes, metadata = renderer.render_pdf(sample_snapshot)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert "generation_time_ms" in metadata
        assert "file_size_bytes" in metadata
        assert metadata["snapshot_id"] == sample_snapshot.snapshot_id

    @patch("the_alchemiser.reporting.renderer.ReportRenderer._html_to_pdf_with_playwright")
    def test_render_pdf_with_output_path(
        self, mock_pdf_gen: MagicMock, sample_snapshot: AccountSnapshot, tmp_path: Path
    ) -> None:
        """Test PDF rendering with output file path."""
        mock_pdf_bytes = b"fake-pdf-content"
        mock_pdf_gen.return_value = mock_pdf_bytes

        renderer = ReportRenderer()
        output_path = tmp_path / "test_report.pdf"
        pdf_bytes, metadata = renderer.render_pdf(sample_snapshot, output_path=output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == mock_pdf_bytes
