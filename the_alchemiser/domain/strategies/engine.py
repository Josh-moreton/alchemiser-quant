"""Typed Strategy Engine Base Class.

Abstract base class for trading strategy implementations with full type safety,
validation helpers, and error handling integration. This replaces pandas coupling
with clean typed contracts.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from the_alchemiser.domain.market_data.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.services.errors.exceptions import ValidationError
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler


class StrategyEngine(ABC):
    """Abstract base class for typed strategy engines.

    Provides a clean contract for strategy implementations with validation,
    error handling, and typed market data access using constructor injection.
    """

    def __init__(self, strategy_name: str, market_data_port: MarketDataPort) -> None:
        """Initialize strategy engine with required dependencies.

        Args:
            strategy_name: Human-readable name for this strategy
            market_data_port: Market data access interface

        """
        self.strategy_name = strategy_name
        self.market_data_port = market_data_port
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
        self.error_handler = TradingSystemErrorHandler()

    @abstractmethod
    def generate_signals(self, now: datetime) -> list[StrategySignal]:
        """Generate trading signals based on current market data.

        Args:
            now: Current timestamp for signal generation

        Returns:
            List of strategy signals with validated structure

        Raises:
            StrategyExecutionError: If signal generation fails
            ValidationError: If generated signals are invalid

        """
        ...

    def validate_signals(self, signals: list[StrategySignal]) -> bool:
        """Validate generated signals for correctness.

        Args:
            signals: List of signals to validate

        Returns:
            True if all signals are valid

        Raises:
            ValidationError: If any signal is invalid

        """
        if not signals:
            self.logger.warning(f"{self.strategy_name}: No signals generated")
            return True

        for i, signal in enumerate(signals):
            try:
                self._validate_single_signal(signal)
            except Exception as e:
                error_msg = f"{self.strategy_name}: Invalid signal at index {i}: {e}"
                self.error_handler.handle_error(
                    error=e,
                    context="signal_validation",
                    component=f"{self.strategy_name}.validate_signals",
                    additional_data={
                        "signal_index": i,
                        "signal_symbol": getattr(signal, "symbol", "unknown"),
                        "total_signals": len(signals),
                    },
                )
                raise ValidationError(error_msg) from e

        self.logger.info(f"{self.strategy_name}: Validated {len(signals)} signals successfully")
        return True

    def _validate_single_signal(self, signal: StrategySignal) -> None:
        """Validate a single strategy signal.

        Args:
            signal: Signal to validate

        Raises:
            ValidationError: If signal is invalid

        """
        # Check if it's actually a StrategySignal instance or has the right interface
        if (
            not hasattr(signal, "action")
            or not hasattr(signal, "confidence")
            or not hasattr(signal, "target_allocation")
        ):
            raise ValidationError(f"Expected StrategySignal-like object, got {type(signal)}")

        # For proper StrategySignal instances, check the type
        if (
            hasattr(signal, "__class__")
            and signal.__class__.__name__ != "StrategySignal"
            and not isinstance(signal, StrategySignal)
        ):
            raise ValidationError(f"Expected StrategySignal, got {type(signal)}")

        # Validate action
        if signal.action not in ("BUY", "SELL", "HOLD"):
            raise ValidationError(f"Invalid action: {signal.action}")

        # Validate confidence is in range [0, 1]
        confidence_value = signal.confidence.value
        if confidence_value < 0 or confidence_value > 1:
            raise ValidationError(f"Confidence must be between 0 and 1, got {confidence_value}")

        # Validate target allocation is non-negative
        allocation_value = signal.target_allocation.value
        if allocation_value < 0:
            raise ValidationError(f"Target allocation cannot be negative, got {allocation_value}")

    def safe_generate_signals(self, now: datetime) -> list[StrategySignal]:
        """Safely generate signals with error handling.

        Args:
            now: Current timestamp for signal generation

        Returns:
            List of validated signals, or empty list if generation fails

        """
        try:
            signals = self.generate_signals(now)
            self.validate_signals(signals)
            return signals
        except Exception as e:
            self.error_handler.handle_error(
                error=e,
                context="signal_generation",
                component=f"{self.strategy_name}.safe_generate_signals",
                additional_data={"timestamp": now.isoformat(), "strategy": self.strategy_name},
            )
            self.logger.error(f"{self.strategy_name}: Signal generation failed: {e}")
            return []

    def get_required_symbols(self) -> list[str]:
        """Get list of symbols required by this strategy.

        Override this method to specify which symbols the strategy needs.
        Default implementation returns empty list.

        Returns:
            List of symbol strings required for this strategy

        """
        return []

    def validate_market_data_availability(self, symbols: list[str] | None = None) -> bool:
        """Validate that required market data is available.

        Args:
            symbols: Optional list of symbols to check, defaults to required_symbols

        Returns:
            True if all required data is available

        Raises:
            ValidationError: If required data is unavailable

        """
        if symbols is None:
            symbols = self.get_required_symbols()

        if not symbols:
            return True

        unavailable_symbols = []
        for symbol in symbols:
            try:
                from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol

                symbol_obj = Symbol(symbol)
                price = self.market_data_port.get_mid_price(symbol_obj)
                if price is None:
                    unavailable_symbols.append(symbol)
            except Exception as e:
                self.logger.warning(f"Failed to check {symbol}: {e}")
                unavailable_symbols.append(symbol)

        if unavailable_symbols:
            error_msg = f"{self.strategy_name}: Required market data unavailable for symbols: {unavailable_symbols}"
            raise ValidationError(error_msg)

        return True

    def log_strategy_state(self, additional_info: dict[str, Any] | None = None) -> None:
        """Log current strategy state for debugging.

        Args:
            additional_info: Optional additional information to log

        """
        info = {
            "strategy_name": self.strategy_name,
            "required_symbols": self.get_required_symbols(),
            "error_count": len(self.error_handler.errors),
        }

        if additional_info:
            info.update(additional_info)

        self.logger.info(f"{self.strategy_name} state: {info}")
