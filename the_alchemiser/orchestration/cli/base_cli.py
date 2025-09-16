"""Business Unit: shared | Status: current.

Base CLI functionality shared across CLI modules.

Provides common display and formatting functionality to avoid code duplication
between trading executor and other CLI modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.cli.cli_formatter import (
    render_comprehensive_trading_results,
    render_strategy_summary,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO


class BaseCLI:
    """Base class for CLI modules with shared display functionality."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        """Initialize base CLI functionality.

        Args:
            settings: Application settings
            container: Application container for dependency injection

        """
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

    def _display_comprehensive_results(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
        account_info: dict[str, Any] | None = None,
        current_positions: dict[str, Any] | None = None,
        allocation_comparison: AllocationComparisonDTO | None = None,
        open_orders: list[dict[str, Any]] | None = None,
    ) -> None:
        """Display comprehensive analysis results including account info and strategy summary.

        This method consolidates the display logic for trading results.

        Args:
            strategy_signals: Strategy signal results
            consolidated_portfolio: Consolidated portfolio allocation
            account_info: Optional account information
            current_positions: Optional current positions data
            allocation_comparison: Optional AllocationComparisonDTO for allocation comparison
            open_orders: Optional open orders data

        """
        # Display comprehensive trading/signal results
        render_comprehensive_trading_results(
            strategy_signals,
            consolidated_portfolio,
            account_info,
            current_positions,
            allocation_comparison,
            open_orders,
        )

        # Display strategy summary
        allocations = self.settings.strategy.default_strategy_allocations
        render_strategy_summary(strategy_signals, consolidated_portfolio, allocations)

    def _display_strategy_tracking(self, *, paper_trading: bool | None = None) -> None:
        """Display strategy tracking information from StrategyOrderTracker.

        This method consolidates the strategy tracking display logic
        across TradingExecutor and the main CLI status command.

        Args:
            paper_trading: Whether to use paper trading mode. If None, uses container config.

        """
        from the_alchemiser.orchestration.cli.strategy_tracking_utils import display_strategy_tracking

        # Determine paper trading mode
        if paper_trading is None:
            paper_trading = self.container.config.paper_trading()

        display_strategy_tracking(paper_trading=paper_trading)

    def _display_detailed_strategy_positions(self, *, paper_trading: bool | None = None) -> None:
        """Display detailed strategy positions and P&L summary.

        This method shows individual positions and aggregated P&L data,
        complementing the basic strategy tracking display.

        Args:
            paper_trading: Whether to use paper trading mode. If None, uses container config.

        """
        from the_alchemiser.orchestration.cli.strategy_tracking_utils import (
            display_detailed_strategy_positions,
        )

        # Determine paper trading mode
        if paper_trading is None:
            paper_trading = self.container.config.paper_trading()

        display_detailed_strategy_positions(paper_trading=paper_trading)
