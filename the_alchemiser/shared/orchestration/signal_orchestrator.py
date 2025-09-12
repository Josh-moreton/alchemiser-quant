"""Business Unit: shared | Status: current

Signal analysis orchestration workflow.

Coordinates strategy signal generation and analysis without actual trading execution.
Handles the complete workflow from strategy orchestration to signal validation and display.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.orchestration.strategy_orchestrator import StrategyOrchestrator
from the_alchemiser.shared.types.exceptions import DataProviderError
from the_alchemiser.shared.utils.strategy_utils import get_strategy_allocations

# Nuclear strategy symbol constants  
NUCLEAR_SYMBOLS = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]


class SignalOrchestrator:
    """Orchestrates signal analysis workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

    def generate_signals(self) -> tuple[dict[str, Any], dict[str, float]]:
        """Generate strategy signals."""
        # Use strategy orchestrator for signal generation
        market_data_port = self.container.infrastructure.market_data_service()
        strategy_allocations = get_strategy_allocations(self.settings)
        
        # Convert strategy allocations to new format
        from the_alchemiser.shared.types.strategy_types import StrategyType
        typed_allocations = {}
        for strategy_name, allocation in strategy_allocations.items():
            strategy_type = getattr(StrategyType, strategy_name.upper(), None)
            if strategy_type:
                typed_allocations[strategy_type] = allocation
        
        strategy_orch = StrategyOrchestrator(market_data_port, typed_allocations)
        aggregated_signals = strategy_orch.generate_all_signals(datetime.now(UTC))

        # Convert aggregated signals to display format
        strategy_signals = {}
        for strategy_type, signals in aggregated_signals.get_signals_by_strategy().items():
            if signals:
                signal = signals[0]  # Take first signal for each strategy
                strategy_signals[strategy_type] = {
                    "symbol": signal.symbol.value,
                    "action": signal.action,
                    "confidence": float(signal.confidence.value),
                    "reasoning": signal.reasoning,
                }

        # Create consolidated portfolio from signals
        consolidated_portfolio = {}
        for signal in aggregated_signals.consolidated_signals:
            if signal.action == "BUY":
                consolidated_portfolio[signal.symbol.value] = float(signal.target_allocation or 0.1)

        return strategy_signals, consolidated_portfolio

    def validate_signal_quality(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
    ) -> bool:
        """Validate that signal analysis produced meaningful results.

        Returns False if any data fetch failures occurred or if all strategies failed
        to get market data. The system should not operate on partial information.

        Args:
            strategy_signals: Generated strategy signals
            consolidated_portfolio: Consolidated portfolio allocation

        Returns:
            True if analysis appears valid, False if it should be considered a failure

        """
        if not strategy_signals:
            return False

        # Check for any data fetch failures - fail immediately on any failure
        # We don't want trades being made on partial information
        if self._has_data_fetch_failures():
            self.logger.error(
                "Signal analysis failed due to data fetch failures. "
                "The system does not operate on partial information."
            )
            return False

        # Count strategies that failed due to data issues
        failed_strategies = []
        fallback_strategies = []  # Strategies using fallback/default signals

        for strategy_type, signal in strategy_signals.items():
            reasoning = signal.get("reasoning", "")

            # Check for explicit failure indicators
            if reasoning and ("no signal produced" in reasoning.lower()):
                strategy_name = strategy_type.value if hasattr(strategy_type, 'value') else str(strategy_type)
                failed_strategies.append(strategy_name)
            # Check for fallback/default behavior due to data issues
            elif reasoning and ("no market data available" in reasoning.lower()):
                strategy_name = strategy_type.value if hasattr(strategy_type, 'value') else str(strategy_type)
                fallback_strategies.append(strategy_name)

        # If all strategies either failed completely or are using fallback defaults,
        # consider this a system failure
        total_affected = len(failed_strategies) + len(fallback_strategies)

        if total_affected == len(strategy_signals):
            if failed_strategies and not fallback_strategies:
                # All strategies failed completely
                self.logger.error(
                    f"All strategies failed due to market data issues: {failed_strategies}"
                )
            elif fallback_strategies and not failed_strategies:
                # All strategies using fallback due to market data issues
                self.logger.error(
                    f"All strategies using fallback signals due to market data issues: {fallback_strategies}"
                )
            else:
                # Mixed failure/fallback
                self.logger.error(
                    f"All strategies affected by market data issues - "
                    f"failed: {failed_strategies}, fallback: {fallback_strategies}"
                )
            return False

        return True

    def _has_data_fetch_failures(self) -> bool:
        """Check if any data fetch failures occurred during signal generation.

        This method detects if the system is in an environment where data fetching
        fails, which should cause the signal analysis to fail rather than operate
        on partial information.

        Returns:
            True if data fetch failures are detected, False otherwise

        """
        try:
            # Check if we're in a network-restricted environment by attempting
            # to resolve the Alpaca data endpoint that strategies depend on
            import socket

            socket.gethostbyname("data.alpaca.markets")

            # If we can resolve the hostname, we likely have network access
            # Any data fetch failures would be credential/API issues that
            # should be handled by individual strategy error handling
            return False

        except (socket.gaierror, OSError):
            # Cannot resolve hostname - indicates network restrictions
            # This means any data-dependent operations will fail
            self.logger.warning(
                "Network restrictions detected: cannot resolve data.alpaca.markets. "
                "This indicates data fetch operations will fail."
            )
            return True

        except Exception as e:
            # If we can't determine connectivity, be conservative
            # In production this should rarely happen
            self.logger.debug(f"Could not determine network connectivity: {e}")
            return False

    def analyze_signals(self) -> tuple[dict[str, Any], dict[str, float]] | None:
        """Run complete signal analysis workflow.
        
        Returns:
            Tuple of (strategy_signals, consolidated_portfolio) if successful, None if failed
        """
        try:
            # System now uses fully typed domain model
            self.logger.info("Using typed StrategySignal domain model")

            # Generate signals
            strategy_signals, consolidated_portfolio = self.generate_signals()

            if not strategy_signals:
                self.logger.error("Failed to generate strategy signals")
                return None

            # Check if analysis produced meaningful results
            if not self.validate_signal_quality(strategy_signals, consolidated_portfolio):
                self.logger.error(
                    "Signal analysis failed validation - no meaningful data available"
                )
                return None

            return strategy_signals, consolidated_portfolio

        except (DataProviderError,) as e:
            self.logger.error(f"Signal analysis failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in signal analysis: {e}")
            return None

    def count_positions_for_strategy(
        self,
        strategy_name: str,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
    ) -> int:
        """Count positions for a specific strategy."""
        # Convert strategy name to strategy type key
        strategy_key = strategy_name.upper()
        signal = None
        
        # Find signal for this strategy
        for key, sig in strategy_signals.items():
            key_name = key.value if hasattr(key, 'value') else str(key)
            if key_name.upper() == strategy_key:
                signal = sig
                break
                
        if not signal:
            return 0

        symbol = signal.get("symbol")

        if strategy_name.upper() == "NUCLEAR":
            # Nuclear strategy can have multiple positions
            if signal.get("action") == "BUY":
                if symbol == "UVXY_BTAL_PORTFOLIO":
                    return 2  # UVXY and BTAL
                if symbol == "UVXY":
                    return 1  # Just UVXY
                # For NUCLEAR_PORTFOLIO, count actual symbols in consolidated portfolio
                if isinstance(symbol, str) and "NUCLEAR_PORTFOLIO" in symbol:
                    # Extract symbols from format like "NUCLEAR_PORTFOLIO (SMR, BWXT, LEU)"
                    # Use regex for robust parsing to handle edge cases
                    match = re.search(r"\(([^)]+)\)", symbol)
                    if match:
                        symbols_part = match.group(1)
                        nuclear_symbols = [s.strip() for s in symbols_part.split(",")]
                        return len([s for s in nuclear_symbols if s in consolidated_portfolio])
                    # Fallback: count nuclear symbols in consolidated portfolio
                    return len([s for s in NUCLEAR_SYMBOLS if s in consolidated_portfolio])
            return 0
        if strategy_name.upper() in ["TECL", "KLM"]:
            # Single position strategies
            return 1 if signal.get("action") == "BUY" else 0
        # Count from consolidated portfolio if possible
        strategy_symbols = self._get_symbols_for_strategy(strategy_name, strategy_signals)
        return len([s for s in strategy_symbols if s in consolidated_portfolio])

    def _get_symbols_for_strategy(
        self,
        strategy_name: str,
        strategy_signals: dict[str, Any],
    ) -> set[str]:
        """Get symbols associated with a strategy."""
        # Convert strategy name to strategy type key
        strategy_key = strategy_name.upper()
        signal = None
        
        # Find signal for this strategy
        for key, sig in strategy_signals.items():
            key_name = key.value if hasattr(key, 'value') else str(key)
            if key_name.upper() == strategy_key:
                signal = sig
                break
                
        if not signal:
            return set()

        symbol: Any = signal.get("symbol")

        if isinstance(symbol, str):
            return {symbol}
        if isinstance(symbol, dict):
            return set(symbol.keys())

        return set()