"""Business Unit: orchestration | Status: current.

Signal analysis orchestration workflow.

Coordinates strategy signal generation and analysis without actual trading execution.
Handles the complete workflow from strategy orchestration to signal validation and display.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.strategy_orchestrator import (
    AggregatedSignals,
    MultiStrategyOrchestrator,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.dto.consolidated_portfolio_dto import (
    ConsolidatedPortfolioDTO,
)
from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO
from the_alchemiser.shared.events import EventBus, SignalGenerated
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types import StrategySignal
from the_alchemiser.shared.types.exceptions import DataProviderError
from the_alchemiser.shared.types.strategy_types import StrategyType
from the_alchemiser.shared.utils.strategy_utils import get_strategy_allocations
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy_v2.engines.nuclear import NUCLEAR_SYMBOLS  # type: ignore[import-untyped]

# Nuclear strategy symbol constants
# Moved to strategy_v2.engines.nuclear.constants for shared access


class SignalOrchestrator:
    """Orchestrates signal analysis workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        """Initialize signal orchestrator with settings and dependency container."""
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container for dual-path emission
        self.event_bus: EventBus = container.services.event_bus()

    def generate_signals(self) -> tuple[dict[str, Any], ConsolidatedPortfolioDTO]:
        """Generate strategy signals and consolidated portfolio allocation.

        Returns:
            Tuple of (strategy_signals dict, ConsolidatedPortfolioDTO)

        """
        # Use strategy orchestrator for signal generation
        market_data_port = self.container.infrastructure.market_data_service()
        strategy_allocations = get_strategy_allocations(self.settings)

        # Strategy allocations are already in the correct format (StrategyType -> float)
        typed_allocations = strategy_allocations
        strategy_orch = MultiStrategyOrchestrator(market_data_port, typed_allocations)
        aggregated_signals = strategy_orch.generate_all_signals(datetime.now(UTC))

        # Convert aggregated signals to display format
        strategy_signals = self._convert_signals_to_display_format(aggregated_signals)

        # Create consolidated portfolio from signals with proper scaling
        consolidated_portfolio_dict, contributing_strategies = (
            self._build_consolidated_portfolio(aggregated_signals, typed_allocations)
        )

        # Create ConsolidatedPortfolioDTO
        consolidated_portfolio = ConsolidatedPortfolioDTO.from_dict_allocation(
            allocation_dict=consolidated_portfolio_dict,
            correlation_id=f"signal_orchestrator_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            source_strategies=contributing_strategies,
        )

        return strategy_signals, consolidated_portfolio

    def _convert_signals_to_display_format(
        self, aggregated_signals: AggregatedSignals
    ) -> dict[str, Any]:
        """Convert aggregated signals to display format."""
        strategy_signals = {}
        for (
            strategy_type,
            signals,
        ) in aggregated_signals.get_signals_by_strategy().items():
            if signals:
                # For strategies with multiple signals (like Nuclear portfolio expansion),
                # combine them into a single display entry with all symbols
                if len(signals) > 1:
                    # Multiple signals - present a concise primary symbol; keep full list separately
                    symbols = [
                        signal.symbol.value
                        for signal in signals
                        if signal.action == "BUY"
                    ]
                    primary_signal = signals[0]  # Use first signal for other attributes
                    primary_symbol = primary_signal.symbol.value
                    strategy_signals[str(strategy_type)] = {
                        "symbol": primary_symbol,
                        "symbols": symbols,  # Keep individual symbols for other processing and display
                        "action": primary_signal.action,
                        "confidence": float(primary_signal.confidence.value),
                        "reasoning": primary_signal.reasoning,
                        "is_multi_symbol": True,
                    }
                else:
                    # Single signal - existing behavior
                    signal = signals[0]
                    strategy_signals[str(strategy_type)] = {
                        "symbol": signal.symbol.value,
                        "action": signal.action,
                        "confidence": float(signal.confidence.value),
                        "reasoning": signal.reasoning,
                        "is_multi_symbol": False,
                    }
        return strategy_signals

    def _build_consolidated_portfolio(
        self,
        aggregated_signals: AggregatedSignals,
        typed_allocations: dict[StrategyType, float],
    ) -> tuple[dict[str, float], list[str]]:
        """Build consolidated portfolio from signals with proper scaling."""
        consolidated_portfolio_dict: dict[str, float] = {}
        contributing_strategies = []

        # Process signals by strategy to preserve allocation context
        for (
            strategy_type,
            signals,
        ) in aggregated_signals.get_signals_by_strategy().items():
            strategy_allocation = typed_allocations.get(strategy_type, 0.0)
            for signal in signals:
                if signal.action == "BUY":
                    signal_allocation = self._extract_signal_allocation(signal)
                    portfolio_allocation = signal_allocation * strategy_allocation

                    # Handle potential conflicts - if symbol already exists, sum allocations
                    if signal.symbol.value in consolidated_portfolio_dict:
                        consolidated_portfolio_dict[
                            signal.symbol.value
                        ] += portfolio_allocation
                    else:
                        consolidated_portfolio_dict[signal.symbol.value] = (
                            portfolio_allocation
                        )

        # Get strategy names that contributed
        for strategy_type in aggregated_signals.get_signals_by_strategy():
            contributing_strategies.append(str(strategy_type))

        return consolidated_portfolio_dict, contributing_strategies

    def _extract_signal_allocation(self, signal: StrategySignal) -> float:
        """Extract signal allocation, handling both Percentage objects and raw Decimal values."""
        if signal.target_allocation:
            # Handle both Percentage objects and raw Decimal values
            if hasattr(signal.target_allocation, "value"):
                return float(signal.target_allocation.value)
            return float(signal.target_allocation)
        return 0.1

    def validate_signal_quality(
        self,
        strategy_signals: dict[str, Any],
    ) -> bool:
        """Validate that signal analysis produced meaningful results.

        Returns False if any data fetch failures occurred or if all strategies failed
        to get market data. The system should not operate on partial information.

        Args:
            strategy_signals: Strategy signal results

        Returns:
            True if signals are valid and meaningful, False if it should be considered a failure

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
        failed_strategies, fallback_strategies = self._categorize_strategy_failures(
            strategy_signals
        )

        # If all strategies either failed completely or are using fallback defaults,
        # consider this a system failure
        total_affected = len(failed_strategies) + len(fallback_strategies)
        if total_affected == len(strategy_signals):
            self._log_all_strategies_affected(failed_strategies, fallback_strategies)
            return False

        return True

    def _categorize_strategy_failures(
        self, strategy_signals: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Categorize strategies into failed and fallback groups based on reasoning."""
        failed_strategies = []
        fallback_strategies = []

        for strategy_type, signal in strategy_signals.items():
            reasoning = signal.get("reasoning", "")
            strategy_name = self._extract_strategy_name(strategy_type)

            # Check for explicit failure indicators
            if reasoning and ("no signal produced" in reasoning.lower()):
                failed_strategies.append(strategy_name)
            # Check for fallback/default behavior due to data issues
            elif reasoning and ("no market data available" in reasoning.lower()):
                fallback_strategies.append(strategy_name)

        return failed_strategies, fallback_strategies

    def _extract_strategy_name(self, strategy_type: StrategyType | str) -> str:
        """Extract strategy name from strategy type."""
        if isinstance(strategy_type, str):
            return strategy_type
        return (
            strategy_type.value
            if hasattr(strategy_type, "value")
            else str(strategy_type)
        )

    def _log_all_strategies_affected(
        self, failed_strategies: list[str], fallback_strategies: list[str]
    ) -> None:
        """Log appropriate error message when all strategies are affected."""
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

        except OSError:
            # Cannot resolve hostname - indicates network restrictions
            # This means any data-dependent operations will fail
            self.logger.warning(
                "Network restrictions detected: cannot resolve data.alpaca.markets. "
                "This indicates data fetch operations will fail."
            )
            return True

    def analyze_signals(self) -> tuple[dict[str, Any], dict[str, float]] | None:
        """Run complete signal analysis workflow.

        DUAL-PATH: Emits SignalGenerated event AND returns traditional response.

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
            if not self.validate_signal_quality(strategy_signals):
                self.logger.error(
                    "Signal analysis failed validation - no meaningful data available"
                )
                return None

            # DUAL-PATH: Emit SignalGenerated event for event-driven consumers
            self._emit_signal_generated_event(
                strategy_signals, consolidated_portfolio.to_dict_allocation()
            )

            # Return traditional response for backwards compatibility
            return strategy_signals, consolidated_portfolio.to_dict_allocation()

        except DataProviderError as e:
            self.logger.error(f"Signal analysis failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in signal analysis: {e}")
            return None

    def _emit_signal_generated_event(
        self, strategy_signals: dict[str, Any], consolidated_portfolio: dict[str, float]
    ) -> None:
        """Emit SignalGenerated event for event-driven architecture.

        Converts traditional signal data to event format for new event-driven consumers.
        """
        try:
            # Convert strategy signals to DTO format
            signal_dtos = []
            correlation_id = str(uuid.uuid4())
            causation_id = f"signal-analysis-{datetime.now(UTC).isoformat()}"

            for strategy_type, signal_data in strategy_signals.items():
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )
                # Use short symbol for DTO (max length 10). If multi, pick first from list.
                raw_symbol = signal_data.get("symbol", "UNKNOWN")
                if signal_data.get("is_multi_symbol") and isinstance(
                    signal_data.get("symbols"), list
                ):
                    symbols_list = signal_data.get("symbols") or []
                    if symbols_list:
                        raw_symbol = symbols_list[0]
                # Enforce 10-char max for StrategySignalDTO.symbol
                sanitized_symbol = str(raw_symbol)[:10]
                signal_dto = StrategySignalDTO(
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    timestamp=datetime.now(UTC),
                    symbol=sanitized_symbol,
                    action=signal_data.get("action", "HOLD"),
                    confidence=Decimal(str(signal_data.get("confidence", 0.0))),
                    reasoning=signal_data.get("reasoning", "Signal generated"),
                    strategy_name=strategy_name,
                    allocation_weight=None,  # Will be determined by portfolio module
                )
                signal_dtos.append(signal_dto)

            # Convert strategy allocations to Decimal for event
            strategy_allocations: dict[str, Decimal] = {}
            allocations = get_strategy_allocations(self.settings)
            for strategy_type_enum, allocation in allocations.items():
                # Convert StrategyType enum to string for event schema compatibility
                strategy_name = str(strategy_type_enum)
                strategy_allocations[strategy_name] = Decimal(str(allocation))

            # Convert consolidated portfolio to Decimal for event
            consolidated_decimal = {}
            for symbol, allocation in consolidated_portfolio.items():
                consolidated_decimal[symbol] = Decimal(str(allocation))

            # Create and emit the event
            event = SignalGenerated(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"signal-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="SignalOrchestrator",
                signals=signal_dtos,
                strategy_allocations=strategy_allocations,
                consolidated_portfolio=consolidated_decimal,
            )

            self.event_bus.publish(event)
            self.logger.debug(f"Emitted SignalGenerated event {event.event_id}")

        except Exception as e:
            # Don't let event emission failure break the traditional workflow
            self.logger.warning(f"Failed to emit SignalGenerated event: {e}")

    def count_positions_for_strategy(
        self,
        strategy_name: str,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
    ) -> int:
        """Count positions for a specific strategy."""
        signal = self._find_signal_for_strategy(strategy_name, strategy_signals)
        if not signal:
            return 0

        symbol = signal.get("symbol")

        if strategy_name.upper() == "NUCLEAR":
            if symbol is None:
                return 0
            if isinstance(symbol, str):
                symbol = Symbol(symbol)
            return self._count_nuclear_positions(signal, symbol, consolidated_portfolio)
        if strategy_name.upper() in ["TECL", "KLM"]:
            # Single position strategies
            return 1 if signal.get("action") == "BUY" else 0
        # Count from consolidated portfolio if possible
        strategy_symbols = self._get_symbols_for_strategy(
            strategy_name, strategy_signals
        )
        return len([s for s in strategy_symbols if s in consolidated_portfolio])

    def _find_signal_for_strategy(
        self, strategy_name: str, strategy_signals: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find signal for a specific strategy by name."""
        strategy_key = strategy_name.upper()
        for key, sig in strategy_signals.items():
            key_name = key.value if hasattr(key, "value") else str(key)
            if key_name.upper() == strategy_key:
                return sig  # type: ignore[no-any-return]
        return None

    def _count_nuclear_positions(
        self,
        signal: dict[str, Any],
        symbol: Symbol,
        consolidated_portfolio: dict[str, float],
    ) -> int:
        """Count positions for nuclear strategy based on signal and symbol."""
        if signal.get("action") != "BUY":
            return 0

        if symbol.value == "UVXY_BTAL_PORTFOLIO":
            return 2  # UVXY and BTAL
        if symbol.value == "UVXY":
            return 1  # Just UVXY
        # For NUCLEAR_PORTFOLIO, count actual symbols in consolidated portfolio
        if isinstance(symbol, str) and "NUCLEAR_PORTFOLIO" in symbol:
            return self._count_nuclear_portfolio_symbols(symbol, consolidated_portfolio)
        return 0

    def _count_nuclear_portfolio_symbols(
        self, symbol: str, consolidated_portfolio: dict[str, float]
    ) -> int:
        """Count nuclear symbols from portfolio symbol string."""
        # Extract symbols from format like "NUCLEAR_PORTFOLIO (SMR, BWXT, LEU)"
        # Use regex for robust parsing to handle edge cases
        match = re.search(r"\(([^)]+)\)", symbol)
        if match:
            symbols_part = match.group(1)
            nuclear_symbols = [s.strip() for s in symbols_part.split(",")]
            return len([s for s in nuclear_symbols if s in consolidated_portfolio])
        # Fallback: count nuclear symbols in consolidated portfolio
        return len([s for s in NUCLEAR_SYMBOLS if s in consolidated_portfolio])

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
            key_name = key.value if hasattr(key, "value") else str(key)
            if key_name.upper() == strategy_key:
                signal = sig
                break

        if not signal:
            return set()

        symbol = signal.get("symbol")  # Type inferred from signal context

        if isinstance(symbol, str):
            return {symbol}
        if isinstance(symbol, dict):
            return set(symbol.keys())

        return set()
