"""Signal analysis CLI module.

Handles signal generation and display without trading execution.
Uses the typed strategy system (TypedStrategyManager) for end-to-end type safety.
"""

from datetime import datetime, UTC
from typing import Any

from the_alchemiser.domain.registry.strategy_registry import StrategyType
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
        """Generate strategy signals using TypedStrategyManager."""
        # Acquire DI container initialized by main entry point
        import the_alchemiser.main as app_main

        container = app_main._di_container
        if container is None:
            raise RuntimeError("DI container not available - ensure system is properly initialized")

        # Use market data port for typed strategy manager
        market_data_port = container.infrastructure.market_data_service()

        # Create typed strategy manager with proper allocations
        strategy_allocations = self._get_strategy_allocations()
        manager = TypedStrategyManager(
            market_data_port=market_data_port,
            strategy_allocations=strategy_allocations,
        )

        # Generate signals using typed strategy manager
        aggregated_signals = manager.generate_all_signals(datetime.now(UTC))
        
        # Convert typed signals to legacy format for display compatibility
        # TODO: Update display functions to use typed signals directly
        legacy_format_signals = self._convert_to_legacy_format(aggregated_signals)
        consolidated_portfolio = self._create_consolidated_portfolio(aggregated_signals)
        
        return legacy_format_signals, consolidated_portfolio

    def _convert_to_legacy_format(self, aggregated_signals) -> dict[StrategyType, dict[str, Any]]:
        """Convert AggregatedSignals to legacy format for display compatibility.
        
        TODO: Remove this once display functions are updated to use typed signals.
        """
        legacy_signals = {}
        
        for strategy_type, signals in aggregated_signals.get_signals_by_strategy().items():
            if signals:
                # Take the first signal as the primary signal for this strategy
                signal = signals[0]
                legacy_signals[strategy_type] = {
                    "action": signal.action,
                    "symbol": signal.symbol.value,
                    "reasoning": signal.reasoning,
                    "confidence": float(signal.confidence.value),
                    "target_allocation": float(signal.target_allocation.value),
                    "timestamp": signal.timestamp,
                }
            else:
                # No signals for this strategy
                legacy_signals[strategy_type] = {
                    "action": "HOLD",
                    "symbol": "N/A",
                    "reasoning": "No signals generated",
                    "confidence": 0.0,
                    "target_allocation": 0.0,
                    "timestamp": datetime.now(UTC),
                }
        
        return legacy_signals

    def _create_consolidated_portfolio(self, aggregated_signals) -> dict[str, float]:
        """Create consolidated portfolio allocation from typed signals.
        
        TODO: Remove this once display functions are updated to use typed signals.
        """
        portfolio = {}
        
        # Get all signals and aggregate by symbol
        all_signals = aggregated_signals.get_all_signals()
        for signal in all_signals:
            symbol = signal.symbol.value
            allocation = float(signal.target_allocation.value)
            
            if symbol in portfolio:
                portfolio[symbol] += allocation
            else:
                portfolio[symbol] = allocation
        
        return portfolio

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
            # Indicate typed mode in console if enabled
            if type_system_v2_enabled():
                try:
                    from rich.console import Console

                    Console().print(
                        "[dim]TYPES_V2_ENABLED: typed StrategySignal path is ACTIVE[/dim]"
                    )
                except Exception:
                    self.logger.info("TYPES_V2_ENABLED: typed StrategySignal path is ACTIVE")

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
