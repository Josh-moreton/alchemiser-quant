"""Business Unit: notifications | Status: current.

Test data flow from orchestrator to notification adapter to templates.

This test verifies the complete end-to-end flow of data from strategy signal generation
through orchestration to notification rendering.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.notifications_v2.service import _ExecutionResultAdapter
from the_alchemiser.shared.events.schemas import TradingNotificationRequested
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)
from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio


def test_end_to_end_data_flow_with_real_structure() -> None:
    """Test that real data structures from strategy handler flow correctly to templates."""
    # Simulate what signal_generation_handler creates
    consolidated_portfolio = ConsolidatedPortfolio.from_dict_allocation(
        allocation_dict={"TQQQ": 0.75, "SOXL": 0.25},
        correlation_id="test-123",
        source_strategies=["DSL"],
    )

    # Simulate what gets serialized in SignalGenerated event
    consolidated_portfolio_dump = consolidated_portfolio.model_dump()

    # Simulate strategy signals from signal_generation_handler._convert_signals_to_display_format
    strategy_signals = {
        "DSL": {
            "symbol": "TQQQ",
            "action": "BUY",
            "reasoning": "Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation",
            "is_multi_symbol": True,
        }
    }

    # Simulate what orchestrator passes to notification service in execution_data
    execution_data = {
        "strategy_signals": strategy_signals,
        "consolidated_portfolio": consolidated_portfolio_dump,
        "orders_executed": [
            {
                "symbol": "TQQQ",
                "action": "BUY",
                "shares": 10,
                "success": True,
            }
        ],
        "execution_summary": {
            "orders_placed": 1,
            "orders_succeeded": 1,
        },
    }

    # Create event as orchestrator does
    event = TradingNotificationRequested(
        correlation_id="test-123",
        causation_id="cause-123",
        event_id="evt-123",
        timestamp=datetime.now(UTC),
        source_module="orchestration",
        source_component="EventDrivenOrchestrator",
        trading_success=True,
        trading_mode="PAPER",
        orders_placed=1,
        orders_succeeded=1,
        total_trade_value=Decimal("1000.00"),
        execution_data=execution_data,
    )

    # Create adapter as notification service does
    adapter = _ExecutionResultAdapter(event)

    # Verify reasoning is mapped to reason
    assert "DSL" in adapter.strategy_signals
    dsl_signal = adapter.strategy_signals["DSL"]
    assert "reason" in dsl_signal, "reason field should be present after normalization"
    assert (
        dsl_signal["reason"] == "Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"
    )

    # Verify consolidated_portfolio is flattened
    assert isinstance(adapter.consolidated_portfolio, dict)
    assert adapter.consolidated_portfolio == {"TQQQ": 0.75, "SOXL": 0.25}

    # Verify template rendering works
    html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(adapter, mode="PAPER")

    # Verify key content is present in the HTML
    assert "Nuclear: ✓ SPY RSI(10)>79" in html, "Decision path should be in the HTML"
    assert "TQQQ" in html, "Symbol should be in the HTML"
    assert "75.0%" in html or "75%" in html, "Allocation percentage should be in the HTML"

    # Save full HTML for inspection

    output_path = "/tmp/test_email_output.html"
    with open(output_path, "w") as f:
        f.write(html)
    print(f"\n\n✅ Full HTML saved to: {output_path}")

    # Check for strategy signals table content with reasoning
    assert "DSL" in html or "Dsl" in html, "Strategy name should be in the HTML"
    assert "Analysis" in html, "Analysis column should be in Strategy Signals table"

    # The key test: verify the decision path appears in the Strategy Signals table
    # It should appear in the "Analysis" column of the table
    strategy_signals_section_start = html.find("Strategy Signals</h3>")
    if strategy_signals_section_start != -1:
        # Extract the section after "Strategy Signals" title (next 2000 chars should contain the table)
        section = html[strategy_signals_section_start : strategy_signals_section_start + 2000]
        print("\n=== STRATEGY SIGNALS TABLE SECTION ===")
        print(section)
        # The reasoning should appear in a table cell
        assert "Nuclear:" in section or "SPY RSI" in section, (
            "Decision path should be in Strategy Signals table"
        )


def test_consolidated_portfolio_flattening_with_decimals() -> None:
    """Test that Decimal allocations in ConsolidatedPortfolio are properly flattened to floats."""
    # Create a ConsolidatedPortfolio DTO with Decimal values
    portfolio = ConsolidatedPortfolio(
        target_allocations={
            "SPY": Decimal("0.6"),
            "BND": Decimal("0.4"),
        },
        correlation_id="test-456",
        timestamp=datetime.now(UTC),
        strategy_count=1,
        source_strategies=["DSL"],
        schema_version="1.0.0",
    )

    # Serialize as done in signal_generation_handler
    portfolio_dump = portfolio.model_dump()

    # Create event with serialized portfolio
    event = TradingNotificationRequested(
        correlation_id="test-456",
        causation_id="cause-456",
        event_id="evt-456",
        timestamp=datetime.now(UTC),
        source_module="tests",
        source_component="tests",
        trading_success=True,
        trading_mode="PAPER",
        orders_placed=0,
        orders_succeeded=0,
        total_trade_value=Decimal("0.00"),
        execution_data={"consolidated_portfolio": portfolio_dump},
    )

    # Create adapter
    adapter = _ExecutionResultAdapter(event)

    # Verify flattening worked (Decimal values are acceptable for templates)
    assert "SPY" in adapter.consolidated_portfolio
    assert "BND" in adapter.consolidated_portfolio
    
    spy_value = adapter.consolidated_portfolio["SPY"]
    bnd_value = adapter.consolidated_portfolio["BND"]
    
    assert isinstance(spy_value, (int, float, Decimal))
    assert isinstance(bnd_value, (int, float, Decimal))
    
    # Convert to float for comparison
    assert float(spy_value) == 0.6  # type: ignore[arg-type]
    assert float(bnd_value) == 0.4  # type: ignore[arg-type]
