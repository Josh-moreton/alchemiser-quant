"""Business Unit: reporting | Status: current.

PDF report renderer using Playwright and Jinja2.

Handles HTML template rendering and PDF generation from account snapshots.
"""

from __future__ import annotations

import contextlib
import tempfile
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.account_snapshot import AccountSnapshot

from .metrics import compute_metrics_from_snapshot

logger = get_logger(__name__)

__all__ = ["ReportRenderer"]


class ReportRenderer:
    """Render PDF reports from account snapshots using Playwright."""

    def __init__(self) -> None:
        """Initialize the report renderer."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        logger.debug("Report renderer initialized", template_dir=str(template_dir))

    def render_html(
        self,
        snapshot: AccountSnapshot,
        report_metadata: dict[str, Any] | None = None,
    ) -> str:
        """Render HTML from snapshot data.

        Args:
            snapshot: Account snapshot data
            report_metadata: Optional metadata for the report

        Returns:
            Rendered HTML string

        """
        logger.info("Rendering HTML report", snapshot_id=snapshot.snapshot_id)

        # Prepare template context
        context = self._prepare_template_context(snapshot, report_metadata or {})

        # Load and render template
        template = self.jinja_env.get_template("account_report.html")
        html_content = str(template.render(**context))

        logger.debug("HTML rendered successfully", html_length=len(html_content))
        return html_content

    def render_pdf(
        self,
        snapshot: AccountSnapshot,
        output_path: str | Path | None = None,
        report_metadata: dict[str, Any] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """Render PDF from snapshot data using Playwright.

        Args:
            snapshot: Account snapshot data
            output_path: Optional path to save PDF (if None, returns bytes only)
            report_metadata: Optional metadata for the report

        Returns:
            Tuple of (PDF bytes, metadata dict with generation info)

        """
        start_time = time.time()
        logger.info("Rendering PDF report", snapshot_id=snapshot.snapshot_id)

        # Render HTML first
        html_content = self.render_html(snapshot, report_metadata)

        # Use Playwright to convert HTML to PDF
        pdf_bytes = self._html_to_pdf_with_playwright(html_content)

        # Calculate generation time and file size
        generation_time_ms = int((time.time() - start_time) * 1000)
        file_size_bytes = len(pdf_bytes)

        metadata = {
            "generation_time_ms": generation_time_ms,
            "file_size_bytes": file_size_bytes,
            "snapshot_id": snapshot.snapshot_id,
            "account_id": snapshot.account_id,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(pdf_bytes)
            logger.info("PDF saved to file", path=str(output_path))

        logger.info(
            "PDF rendered successfully",
            generation_time_ms=generation_time_ms,
            file_size_bytes=file_size_bytes,
        )

        return pdf_bytes, metadata

    def _html_to_pdf_with_playwright(self, html_content: str) -> bytes:
        """Convert HTML to PDF using Playwright.

        Args:
            html_content: HTML string to convert

        Returns:
            PDF bytes

        """
        from playwright.sync_api import sync_playwright

        logger.debug("Converting HTML to PDF with Playwright")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()

            # Write HTML to temp file to avoid inline HTML issues
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(html_content)
                temp_path = temp_file.name

            try:
                # Load HTML from file URL
                page.goto(f"file://{temp_path}")

                # Wait for page to load
                page.wait_for_load_state("networkidle")

                # Generate PDF with A4 format
                pdf_bytes_result = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0.5cm", "right": "0.5cm", "bottom": "0.5cm", "left": "0.5cm"},
                )

                logger.debug("PDF generated", size_bytes=len(pdf_bytes_result))
                return bytes(pdf_bytes_result)

            finally:
                browser.close()
                # Clean up temp file
                with contextlib.suppress(OSError):
                    Path(temp_path).unlink()

    def _prepare_template_context(
        self, snapshot: AccountSnapshot, report_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare context data for template rendering.

        Args:
            snapshot: Account snapshot data
            report_metadata: Report metadata

        Returns:
            Dictionary of template context variables

        """
        # Serialize snapshot data for metrics computation
        snapshot_dict = {
            "alpaca_account": snapshot.alpaca_account.model_dump(),
            "alpaca_positions": [pos.model_dump() for pos in snapshot.alpaca_positions],
            "alpaca_orders": [order.model_dump() for order in snapshot.alpaca_orders],
        }

        # Compute metrics
        metrics = compute_metrics_from_snapshot(snapshot_dict)

        # Convert Decimal to float for template
        metrics_for_template = {
            key: float(value) if isinstance(value, Decimal) else value
            for key, value in metrics.items()
        }

        # Prepare positions data
        positions = []
        for pos in snapshot.alpaca_positions:
            positions.append(
                {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty) if pos.qty else 0,
                    "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0,
                    "current_price": float(pos.current_price) if pos.current_price else 0,
                    "market_value": float(pos.market_value) if pos.market_value else 0,
                    "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                }
            )

        # Prepare recent orders data
        recent_orders = []
        for order in snapshot.alpaca_orders[:10]:  # Only show 10 most recent
            recent_orders.append(
                {
                    "symbol": order.symbol,
                    "side": order.side,
                    "qty": float(order.qty) if order.qty else 0,
                    "type": order.order_type,
                    "status": order.status,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                }
            )

        # Build template context
        return {
            "account_id": snapshot.account_id,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_version": snapshot.snapshot_version,
            "period_start": snapshot.period_start.strftime("%Y-%m-%d"),
            "period_end": snapshot.period_end.strftime("%Y-%m-%d"),
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "metrics": metrics_for_template,
            "positions": positions,
            "recent_orders": recent_orders,
            "report_version": report_metadata.get("report_version", "1.0"),
        }

    def render_execution_pdf(
        self,
        context: dict[str, Any],
        output_path: str | Path | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """Render execution report PDF from context.

        Args:
            context: Execution report context with strategy signals, orders, etc.
            output_path: Optional path to save PDF locally

        Returns:
            Tuple of (pdf_bytes, metadata) where metadata includes:
            - file_size_bytes: Size of PDF
            - generation_time_ms: Time taken to generate

        """
        start_time = time.time()
        logger.info("Rendering execution PDF report")

        # Load execution report template
        template = self.jinja_env.get_template("execution_report.html")
        html_content = str(template.render(**context))

        # Convert to PDF using Playwright
        pdf_bytes = self._html_to_pdf_with_playwright(html_content)

        # Calculate generation time and file size
        generation_time_ms = int((time.time() - start_time) * 1000)
        file_size_bytes = len(pdf_bytes)

        metadata = {
            "generation_time_ms": generation_time_ms,
            "file_size_bytes": file_size_bytes,
        }

        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(pdf_bytes)
            logger.info("Execution PDF saved to file", path=str(output_path))

        logger.info(
            "Execution PDF rendered successfully",
            generation_time_ms=generation_time_ms,
            file_size_bytes=file_size_bytes,
        )

        return pdf_bytes, metadata
