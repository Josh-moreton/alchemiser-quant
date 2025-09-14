"""Business Unit: shared | Status: current.

Signal analysis CLI module.

Thin CLI wrapper that delegates to orchestration layer for signal analysis workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator
from the_alchemiser.shared.cli.base_cli import BaseCLI
from the_alchemiser.shared.cli.cli_formatter import (
    render_footer,
    render_header,
)
from the_alchemiser.shared.config.config import Settings


class SignalAnalyzer(BaseCLI):
    """Event-driven CLI wrapper for signal analysis workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        super().__init__(settings, container)

        # Use event-driven trading orchestrator for signal analysis with account info
        self.trading_orchestrator = TradingOrchestrator(settings, container, ignore_market_hours=True)



    def run(self, show_tracking: bool = False) -> bool:
        """Run signal analysis with enhanced account information display via event-driven workflow.

        Args:
            show_tracking: When True, include strategy performance tracking table (opt-in to keep
                default output closer to original minimal signal view).

        """
        render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now(UTC)}")

        # Use event-driven trading orchestrator for comprehensive signal analysis with account info
        result = self.trading_orchestrator.execute_strategy_signals()

        if result is None:
            self.logger.error("Signal analysis failed")
            return False

        # Extract comprehensive result data from event-driven workflow
        strategy_signals = result.get("signals", {})
        consolidated_portfolio = result.get("consolidated_portfolio", {})
        portfolio_analysis = result.get("portfolio_analysis", {})
        account_info = portfolio_analysis.get("account_data", {}).get("account_info")
        current_positions = portfolio_analysis.get("account_data", {}).get("current_positions")
        allocation_comparison = portfolio_analysis.get("allocation_comparison")
        open_orders = portfolio_analysis.get("account_data", {}).get("open_orders", [])

        # Display results with enhanced account information
        self._display_comprehensive_results(
            strategy_signals,
            consolidated_portfolio,
            account_info,
            current_positions,
            allocation_comparison,
            open_orders,
        )

        # Display tracking if requested
        if show_tracking:
            self._display_strategy_tracking(paper_trading=True)

        render_footer("Signal analysis completed successfully!")
        return True
