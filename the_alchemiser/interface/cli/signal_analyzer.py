"""Signal analysis CLI module.

Handles signal generation and display without trading execution.
"""

from datetime import datetime
from typing import Any

from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger
from the_alchemiser.interface.cli.cli_formatter import (
    render_footer,
    render_header,
    render_portfolio_allocation,
    render_strategy_signals,
)
from the_alchemiser.services.errors.exceptions import DataProviderError, StrategyExecutionError


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
        # Acquire DI container initialized by main entry point
        import the_alchemiser.main as app_main

        container = app_main._di_container
        if container is None:
            raise RuntimeError("DI container not available - ensure system is properly initialized")

        # Use typed adapter for engines (DataFrame compatibility) and typed port for fetching
        market_data_port = container.infrastructure.market_data_service()

        # Create strategy manager with proper allocations
        strategy_allocations = self._get_strategy_allocations()

        # Generate typed signals directly
        from datetime import UTC, datetime

        typed_manager = TypedStrategyManager(market_data_port, strategy_allocations)
        aggregated_signals = typed_manager.generate_all_signals(datetime.now(UTC))

        # Convert typed signals to display format
        strategy_signals = self._convert_typed_signals_to_display_format(
            aggregated_signals, strategy_allocations
        )

        # Build portfolio allocation from signals
        consolidated_portfolio = self._build_portfolio_allocation(
            aggregated_signals, strategy_allocations
        )

        return strategy_signals, consolidated_portfolio

    def _convert_typed_signals_to_display_format(
        self,
        aggregated_signals: Any,  # TypedStrategyManager.AggregatedSignals
        strategy_allocations: dict[StrategyType, float],
    ) -> dict[StrategyType, dict[str, Any]]:
        """Convert typed signals to display format."""
        strategy_signals: dict[StrategyType, dict[str, Any]] = {}

        for strategy_type, signals in aggregated_signals.get_signals_by_strategy().items():
            if signals:
                # Use the strategy's actual allocation percentage
                actual_allocation = strategy_allocations.get(strategy_type, 0.0) * 100

                if len(signals) == 1:
                    # Single signal strategy
                    signal = signals[0]
                    symbol_value = signal.symbol.value
                    symbol_str = "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value

                    strategy_signals[strategy_type] = {
                        "symbol": symbol_str,
                        "action": signal.action,
                        "confidence": float(signal.confidence.value),
                        "reasoning": signal.reasoning,
                        "allocation_percentage": actual_allocation,
                    }
                else:
                    # Multi-signal strategy (like nuclear portfolio)
                    # Create a consolidated display showing all symbols
                    first_signal = signals[0]
                    symbol_names = [s.symbol.value for s in signals]
                    symbol_display = f"NUCLEAR_PORTFOLIO ({', '.join(symbol_names)})"

                    # Combine reasoning with portfolio breakdown
                    base_reasoning = first_signal.reasoning.split(
                        " | Nuclear portfolio constituent"
                    )[0]
                    portfolio_breakdown = "\n\nNuclear Portfolio Breakdown:\n"
                    for signal in signals:
                        # signal.target_allocation.value is the proportion within the strategy
                        # actual_allocation is the strategy's total allocation as percentage
                        individual_weight_pct = (
                            float(signal.target_allocation.value) * actual_allocation
                        )
                        portfolio_breakdown += (
                            f"• {signal.symbol.value}: {individual_weight_pct:.1f}%\n"
                        )

                    combined_reasoning = base_reasoning + portfolio_breakdown.rstrip()

                    strategy_signals[strategy_type] = {
                        "symbol": symbol_display,
                        "action": first_signal.action,
                        "confidence": float(first_signal.confidence.value),
                        "reasoning": combined_reasoning,
                        "allocation_percentage": actual_allocation,
                    }
            else:
                strategy_signals[strategy_type] = {
                    "symbol": "N/A",
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "No signal produced",
                    "allocation_percentage": 0.0,
                }

        return strategy_signals

    def _build_portfolio_allocation(
        self,
        aggregated_signals: Any,  # TypedStrategyManager.AggregatedSignals
        strategy_allocations: dict[StrategyType, float],
    ) -> dict[str, float]:
        """Build portfolio allocation from typed signals."""
        consolidated_portfolio: dict[str, float] = {}

        # Build consolidated portfolio from all signals
        for strategy_type, signals in aggregated_signals.get_signals_by_strategy().items():
            strategy_allocation = strategy_allocations.get(strategy_type, 0.0)

            for signal in signals:
                if signal.action in ["BUY", "LONG"]:
                    symbol_str = signal.symbol.value

                    # Use the actual signal allocation for individual symbols
                    if symbol_str != "PORT":
                        # Calculate individual allocation as signal proportion * strategy allocation
                        individual_allocation = (
                            float(signal.target_allocation.value) * strategy_allocation
                        )
                        consolidated_portfolio[symbol_str] = individual_allocation

        return consolidated_portfolio

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

        # Display strategy tracking information
        self._display_strategy_tracking()

    def _display_strategy_tracking(self) -> None:
        """Display strategy tracking information from StrategyOrderTracker."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            from the_alchemiser.application.tracking.strategy_order_tracker import (
                StrategyOrderTracker,
            )

            console = Console()

            # Use paper trading mode for signal analysis
            tracker = StrategyOrderTracker(paper_trading=True)

            # Get all positions
            positions = tracker.get_positions_summary()

            if not positions:
                console.print(Panel(
                    "[dim yellow]No strategy tracking data available[/dim yellow]",
                    title="Strategy Performance History",
                    border_style="yellow"
                ))
                return

            # Create tracking table
            tracking_table = Table(title="Strategy Performance Tracking", show_lines=True, expand=True)
            tracking_table.add_column("Strategy", style="bold magenta")
            tracking_table.add_column("Positions", justify="center")
            tracking_table.add_column("Total P&L", justify="right")
            tracking_table.add_column("Return %", justify="right")
            tracking_table.add_column("Recent Orders", justify="center")

            # Group positions by strategy
            strategies_with_data = set(pos.strategy for pos in positions)

            for strategy_name in sorted(strategies_with_data):
                try:
                    # Get P&L summary
                    pnl_summary = tracker.get_pnl_summary(strategy_name)

                    # Get recent orders count
                    recent_orders = tracker.get_orders_for_strategy(strategy_name)

                    # Color code P&L
                    total_pnl = float(pnl_summary.total_pnl)
                    pnl_color = "green" if total_pnl >= 0 else "red"
                    pnl_sign = "+" if total_pnl >= 0 else ""

                    return_pct = float(pnl_summary.total_return_pct)
                    return_color = "green" if return_pct >= 0 else "red"
                    return_sign = "+" if return_pct >= 0 else ""

                    tracking_table.add_row(
                        strategy_name,
                        str(pnl_summary.position_count),
                        f"[{pnl_color}]{pnl_sign}${total_pnl:.2f}[/{pnl_color}]",
                        f"[{return_color}]{return_sign}{return_pct:.2f}%[/{return_color}]",
                        f"{len(recent_orders)} orders"
                    )

                except Exception as e:
                    self.logger.warning(f"Error getting tracking data for {strategy_name}: {e}")
                    tracking_table.add_row(
                        strategy_name,
                        "Error",
                        "[red]Error[/red]",
                        "[red]Error[/red]",
                        "Error"
                    )

            console.print()
            console.print(tracking_table)

            # Add summary insight
            total_strategies = len(strategies_with_data)
            profitable_strategies = sum(
                1 for strategy_name in strategies_with_data
                if float(tracker.get_pnl_summary(strategy_name).total_pnl) > 0
            )

            insight = f"📊 {profitable_strategies}/{total_strategies} strategies profitable"
            console.print(Panel(
                insight,
                title="Performance Insight",
                border_style="blue"
            ))

        except Exception as e:
            # Non-fatal - tracking is enhancement, not critical
            self.logger.warning(f"Strategy tracking display unavailable: {e}")

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
            # System now uses fully typed domain model
            try:
                from rich.console import Console

                Console().print("[dim]Using typed StrategySignal domain model[/dim]")
            except Exception:
                self.logger.info("Using typed StrategySignal domain model")

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
