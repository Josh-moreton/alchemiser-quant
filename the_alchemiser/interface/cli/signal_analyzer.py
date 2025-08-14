"""Signal analysis CLI module.

Handles signal generation and display without trading execution.
"""

from datetime import datetime
from typing import Any

from the_alchemiser.domain.strategies.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.infrastructure.data_providers.data_provider import UnifiedDataProvider
from the_alchemiser.infrastructure.logging.logging_utils import get_logger
from the_alchemiser.interface.cli.cli_formatter import (
    render_footer,
    render_header,
    render_portfolio_allocation,
    render_strategy_signals,
)
from the_alchemiser.services.exceptions import DataProviderError, StrategyExecutionError


class SignalAnalyzer:
    """Handles signal analysis and display."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)

    def _get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Extract strategy allocations from configuration."""
        return {
            StrategyType.NUCLEAR: self.settings.strategy.default_strategy_allocations["nuclear"],
            StrategyType.TECL: self.settings.strategy.default_strategy_allocations["tecl"],
            StrategyType.KLM: self.settings.strategy.default_strategy_allocations["klm"],
        }

    def _generate_signals(self) -> tuple[dict[StrategyType, dict[str, Any]], dict[str, float]]:
        """Generate strategy signals."""
        # Create shared data provider
        shared_data_provider = UnifiedDataProvider(paper_trading=True)

        # Create strategy manager with proper allocations
        strategy_allocations = self._get_strategy_allocations()
        manager = MultiStrategyManager(
            shared_data_provider=shared_data_provider,
            config=self.settings,
            strategy_allocations=strategy_allocations,
        )

        # Generate signals
        strategy_signals, consolidated_portfolio, _ = manager.run_all_strategies()
        return strategy_signals, consolidated_portfolio

    def _display_results(
        self,
        strategy_signals: dict[StrategyType, dict[str, Any]],
        consolidated_portfolio: dict[str, float],
    ) -> None:
        """Display signal analysis results."""
        # Display strategy signals
        render_strategy_signals(strategy_signals)

        # Display consolidated portfolio
        if consolidated_portfolio:
            render_portfolio_allocation(consolidated_portfolio)

        # Display strategy summary
        self._display_strategy_summary(strategy_signals, consolidated_portfolio)

    def _display_strategy_summary(
        self,
        strategy_signals: dict[StrategyType, dict[str, Any]],
        consolidated_portfolio: dict[str, float],
    ) -> None:
        """Display strategy allocation summary."""
        try:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()
        except ImportError:
            console = None

        # Get allocation percentages from config
        allocations = self.settings.strategy.default_strategy_allocations
        strategy_lines = []

        # Build summary for each strategy
        for strategy_name, allocation in allocations.items():
            if allocation > 0:
                pct = int(allocation * 100)
                positions = self._count_positions_for_strategy(
                    strategy_name, strategy_signals, consolidated_portfolio
                )
                strategy_lines.append(
                    f"[bold cyan]{strategy_name.upper()}:[/bold cyan] "
                    f"{positions} positions, {pct}% allocation"
                )

        strategy_summary = "\n".join(strategy_lines)

        if console:
            console.print(Panel(strategy_summary, title="Strategy Summary", border_style="blue"))
        else:
            self.logger.info(f"Strategy Summary:\n{strategy_summary}")

    def _count_positions_for_strategy(
        self,
        strategy_name: str,
        strategy_signals: dict[StrategyType, dict[str, Any]],
        consolidated_portfolio: dict[str, float],
    ) -> int:
        """Count positions for a specific strategy."""
        strategy_type = getattr(StrategyType, strategy_name.upper(), None)
        if not strategy_type or strategy_type not in strategy_signals:
            return 0

        signal = strategy_signals[strategy_type]
        symbol = signal.get("symbol")

        if strategy_name.upper() == "NUCLEAR":
            # Nuclear strategy can have multiple positions
            if signal.get("action") == "BUY":
                if symbol == "UVXY_BTAL_PORTFOLIO":
                    return 2  # UVXY and BTAL
                elif symbol == "UVXY":
                    return 1  # Just UVXY
                else:
                    return 3  # Default nuclear portfolio
            return 0
        elif strategy_name.upper() in ["TECL", "KLM"]:
            # Single position strategies
            return 1 if signal.get("action") == "BUY" else 0
        else:
            # Count from consolidated portfolio if possible
            strategy_symbols = self._get_symbols_for_strategy(strategy_name, strategy_signals)
            return len([s for s in strategy_symbols if s in consolidated_portfolio])

    def _get_symbols_for_strategy(
        self, strategy_name: str, strategy_signals: dict[StrategyType, dict[str, Any]]
    ) -> set[str]:
        """Get symbols associated with a strategy."""
        strategy_type = getattr(StrategyType, strategy_name.upper(), None)
        if not strategy_type or strategy_type not in strategy_signals:
            return set()

        signal = strategy_signals[strategy_type]
        symbol: Any = signal.get("symbol")

        if isinstance(symbol, str):
            return {symbol}
        elif isinstance(symbol, dict):
            return set(symbol.keys())

        return set()

    def run(self) -> bool:
        """Run signal analysis."""
        render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now()}")

        try:
            # Generate signals
            strategy_signals, consolidated_portfolio = self._generate_signals()

            if not strategy_signals:
                self.logger.error("Failed to generate strategy signals")
                return False

            # Display results
            self._display_results(strategy_signals, consolidated_portfolio)

            render_footer("Signal analysis completed successfully!")
            return True

        except (DataProviderError, StrategyExecutionError) as e:
            self.logger.error(f"Signal analysis failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in signal analysis: {e}")
            return False
