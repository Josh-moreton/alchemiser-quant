"""Business Unit: shared | Status: current.

Signal analysis CLI module.

Thin CLI wrapper that delegates to orchestration layer for signal analysis workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.signal_orchestrator import SignalOrchestrator
from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator
from the_alchemiser.shared.cli.base_cli import BaseCLI
from the_alchemiser.shared.cli.cli_formatter import (
    render_footer,
    render_header,
)
from the_alchemiser.shared.config.config import Settings


class SignalAnalyzer(BaseCLI):
    """Thin CLI wrapper for signal analysis workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        super().__init__(settings, container)

        # Delegate orchestration to dedicated orchestrator
        self.orchestrator = SignalOrchestrator(settings, container)

        # Also create trading orchestrator for enhanced signal analysis with account info
        self.trading_orchestrator = TradingOrchestrator(settings, container, live_trading=False)

    def run(self, show_tracking: bool = False) -> bool:
        """Run signal analysis with enhanced account information display.

        Args:
            show_tracking: When True, include strategy performance tracking table (opt-in to keep
                default output closer to original minimal signal view).

        """
        render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now(UTC)}")

        # Use enhanced trading orchestrator for comprehensive signal analysis with account info
        result = self.trading_orchestrator.execute_strategy_signals()

        if result is None:
            self.logger.error("Signal analysis failed")
            return False

        # Extract comprehensive result data
        strategy_signals = result.get("strategy_signals", {})
        consolidated_portfolio = result.get("consolidated_portfolio", {})
        account_info = result.get("account_info")
        current_positions = result.get("current_positions")
        allocation_comparison = result.get("allocation_comparison")
        open_orders = result.get("open_orders", [])

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
