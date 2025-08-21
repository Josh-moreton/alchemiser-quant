"""Signal analysis CLI module.

Handles signal generation and display without trading execution.
"""

from datetime import datetime
from typing import Any

from the_alchemiser.application.mapping.strategy_signal_mapping import (
    map_signals_dict as _map_signals_to_typed,
)
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
from the_alchemiser.utils.feature_flags import type_system_v2_enabled


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

        # Build a minimal adapter around TypedStrategyManager for compatibility
        class _Adapter:
            def __init__(self, port: Any, allocs: dict[StrategyType, float]):
                self._typed = TypedStrategyManager(port, allocs)
                self._strategy_allocations = allocs

            def run_all_strategies(
                self,
            ) -> tuple[
                dict[StrategyType, dict[str, Any]], dict[str, float], dict[str, list[StrategyType]]
            ]:
                from datetime import UTC, datetime

                agg = self._typed.generate_all_signals(datetime.now(UTC))
                legacy: dict[StrategyType, dict[str, Any]] = {}
                consolidated_portfolio: dict[str, float] = {}

                # Process signals by strategy for legacy format
                for st, signals in agg.get_signals_by_strategy().items():
                    if signals:
                        # Use the strategy's actual allocation percentage
                        actual_allocation = self._strategy_allocations.get(st, 0.0) * 100

                        if len(signals) == 1:
                            # Single signal strategy
                            s = signals[0]
                            symbol_value = s.symbol.value
                            symbol_str = (
                                "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value
                            )

                            legacy[st] = {
                                "symbol": symbol_str,
                                "action": s.action,
                                "confidence": float(s.confidence.value),
                                "reasoning": s.reasoning,
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
                                # signal.target_allocation.value is the proportion within the strategy (e.g., 0.333 for 33.3%)
                                # actual_allocation is the strategy's total allocation as percentage (e.g., 30.0 for 30%)
                                individual_weight_pct = (
                                    float(signal.target_allocation.value) * actual_allocation
                                )
                                portfolio_breakdown += (
                                    f"• {signal.symbol.value}: {individual_weight_pct:.1f}%\n"
                                )

                            combined_reasoning = base_reasoning + portfolio_breakdown.rstrip()

                            legacy[st] = {
                                "symbol": symbol_display,
                                "action": first_signal.action,
                                "confidence": float(first_signal.confidence.value),
                                "reasoning": combined_reasoning,
                                "allocation_percentage": actual_allocation,
                            }
                    else:
                        legacy[st] = {
                            "symbol": "N/A",
                            "action": "HOLD",
                            "confidence": 0.0,
                            "reasoning": "No signal produced",
                            "allocation_percentage": 0.0,
                        }

                # Build consolidated portfolio from all signals
                for strategy_type, signals in agg.get_signals_by_strategy().items():
                    strategy_allocation = self._strategy_allocations.get(strategy_type, 0.0)

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

                return legacy, consolidated_portfolio, {}

        manager = _Adapter(market_data_port, strategy_allocations)

        # Generate signals
        strategy_signals, consolidated_portfolio, _ = manager.run_all_strategies()
        # Feature-flag: convert to typed StrategySignal for display/reporting
        if type_system_v2_enabled():
            try:
                # Visible indicator in logs when typed path is active
                self.logger.info(
                    "TYPES_V2_ENABLED detected: using typed StrategySignal mapping for display"
                )
                typed_signals = _map_signals_to_typed(strategy_signals)
                # For display we keep the legacy shape when returning from this method
                # but downstream display utilities can accept the TypedDict form as well.
                _ = typed_signals  # keep for potential future use
            except Exception:
                pass
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
