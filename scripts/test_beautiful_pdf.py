"""Test script to generate beautiful PDF reports with WeasyPrint.

This script creates sample execution and account reports to preview the new design.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from the_alchemiser.reporting.renderer import ReportRenderer


def generate_sample_execution_report() -> None:
    """Generate a sample execution report PDF."""
    renderer = ReportRenderer()

    # Sample execution context
    context = {
        "success": True,
        "trading_mode": "PAPER",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "correlation_id": "abc-123-def-456-ghi-789",
        "report_id": "exec-report-001",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "strategy_signals": [
            {
                "strategy_name": "Momentum Strategy",
                "signal": "BUY",
                "reasoning": "Strong upward momentum detected",
                "confidence": "0.87",
            },
            {
                "strategy_name": "Mean Reversion",
                "signal": "HOLD",
                "reasoning": "Price near historical mean",
                "confidence": "0.65",
            },
            {
                "strategy_name": "Trend Following",
                "signal": "BUY",
                "reasoning": "Clear uptrend established",
                "confidence": "0.92",
            },
        ],
        "portfolio_allocations": [
            {"symbol": "AAPL", "target_allocation": 0.25},
            {"symbol": "MSFT", "target_allocation": 0.20},
            {"symbol": "NVDA", "target_allocation": 0.15},
            {"symbol": "SPY", "target_allocation": 0.40},
        ],
        "orders": [
            {
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 10,
                "price": 185.50,
                "status": "filled",
                "order_id": "order-abc-123-def-456",
            },
            {
                "symbol": "MSFT",
                "side": "buy",
                "quantity": 8,
                "price": 420.75,
                "status": "filled",
                "order_id": "order-def-456-ghi-789",
            },
            {
                "symbol": "NVDA",
                "side": "buy",
                "quantity": 5,
                "price": 920.30,
                "status": "filled",
                "order_id": "order-ghi-789-jkl-012",
            },
        ],
        "execution_summary": {
            "total_orders": 3,
            "successful_orders": 3,
            "failed_orders": 0,
            "total_value": 9466.50,
        },
    }

    # Generate PDF
    output_path = Path("reports") / "sample_execution_report.pdf"
    pdf_bytes, metadata = renderer.render_execution_pdf(context, output_path)

    print(f"✅ Generated execution report: {output_path}")
    print(f"   Size: {metadata['file_size_bytes']:,} bytes")
    print(f"   Generation time: {metadata['generation_time_ms']}ms")


def main() -> None:
    """Run the test script."""
    print("🧪 The Alchemiser - Beautiful PDF Report Generator Test\n")

    # Create reports directory
    Path("reports").mkdir(exist_ok=True)

    # Generate sample reports
    generate_sample_execution_report()

    print("\n✨ All reports generated successfully!")
    print("   Check the 'reports/' directory for output files")


if __name__ == "__main__":
    main()
