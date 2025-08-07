#!/usr/bin/env python3
"""
Atomic Multi-Strategy Execution Framework

This module provides thread-safe, atomic execution of multi-strategy trading operations
to prevent race conditions and ensure consistent state during portfolio rebalancing.

Key Features:
- Atomic execution context with state isolation
- Position conflict detection and resolution
- Concurrent strategy execution safety
- Order allocation coordination
- State consistency verification

Addresses Critical Issue #3: Race Conditions in Multi-Strategy Execution
"""

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from ..core.exceptions import TradingClientError
from ..core.types import AccountInfo


class ExecutionState(str, Enum):
    """Execution state enumeration."""

    IDLE = "idle"
    PREPARING = "preparing"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    SETTLING = "settling"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ConflictType(str, Enum):
    """Types of strategy conflicts."""

    POSITION_OVERLAP = "position_overlap"
    ALLOCATION_EXCEED = "allocation_exceed"
    OPPOSITE_SIGNALS = "opposite_signals"
    CONCENTRATION_RISK = "concentration_risk"


@dataclass
class PositionIntent:
    """Represents a strategy's intention to trade a position."""

    symbol: str
    target_allocation: Decimal
    strategy_name: str
    confidence: float = 1.0
    max_position_size: Decimal | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ConflictResolution:
    """Result of conflict resolution between strategies."""

    symbol: str
    final_allocation: Decimal
    contributing_strategies: list[str]
    resolution_method: str
    confidence: float
    warnings: list[str] = field(default_factory=list)


class AtomicExecutionContext:
    """
    Thread-safe execution context for multi-strategy trading.

    Ensures that only one multi-strategy execution can run at a time
    and provides conflict detection and resolution between strategies.
    """

    def __init__(self, engine: Any, timeout_seconds: int = 300):
        """Initialize atomic execution context."""
        self.engine = engine
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)

        # Thread safety
        self._lock = threading.RLock()
        self._execution_state = ExecutionState.IDLE
        self._execution_start_time: datetime | None = None
        self._execution_id: str | None = None

        # State tracking
        self._account_snapshot: AccountInfo | None = None
        self._position_intents: list[PositionIntent] = []
        self._conflicts: list[ConflictResolution] = []
        self._allocated_symbols: set[str] = set()

    @property
    def is_executing(self) -> bool:
        """Check if execution is currently in progress."""
        with self._lock:
            return self._execution_state not in [
                ExecutionState.IDLE,
                ExecutionState.COMPLETED,
                ExecutionState.FAILED,
            ]

    @property
    def execution_state(self) -> ExecutionState:
        """Get current execution state."""
        with self._lock:
            return self._execution_state

    def _set_state(self, new_state: ExecutionState) -> None:
        """Thread-safe state transition."""
        with self._lock:
            old_state = self._execution_state
            self._execution_state = new_state
            self.logger.info(f"🔄 Execution state: {old_state} → {new_state}")

    def _check_timeout(self) -> None:
        """Check if execution has timed out."""
        if self._execution_start_time:
            elapsed = (datetime.now(UTC) - self._execution_start_time).total_seconds()
            if elapsed > self.timeout_seconds:
                raise TradingClientError(
                    f"Atomic execution timed out after {elapsed:.1f}s (max: {self.timeout_seconds}s)",
                    context={"execution_id": self._execution_id, "elapsed_seconds": elapsed},
                )

    @contextmanager
    def atomic_execution(self, execution_id: str):
        """
        Context manager for atomic multi-strategy execution.

        Ensures only one execution runs at a time and provides
        consistent state isolation.
        """
        # Acquire exclusive execution lock
        acquired = False
        try:
            with self._lock:
                if self.is_executing:
                    raise TradingClientError(
                        f"Atomic execution already in progress (state: {self._execution_state})",
                        context={
                            "current_execution_id": self._execution_id,
                            "requested_id": execution_id,
                        },
                    )

                # Initialize execution
                self._execution_id = execution_id
                self._execution_start_time = datetime.now(UTC)
                self._position_intents.clear()
                self._conflicts.clear()
                self._allocated_symbols.clear()
                acquired = True

            self._set_state(ExecutionState.PREPARING)
            self.logger.info(f"🔒 Starting atomic execution: {execution_id}")

            # Take account snapshot for consistency
            self._account_snapshot = self.engine.get_account_info()
            if not self._account_snapshot:
                raise TradingClientError("Failed to get account snapshot for atomic execution")

            self._set_state(ExecutionState.ANALYZING)
            yield self

        except Exception as e:
            self._set_state(ExecutionState.FAILED)
            self.logger.error(f"❌ Atomic execution failed: {e}")
            raise

        finally:
            if acquired:
                with self._lock:
                    if self._execution_state == ExecutionState.FAILED:
                        self.logger.warning(f"🔓 Releasing failed execution: {execution_id}")
                    else:
                        self._set_state(ExecutionState.COMPLETED)
                        self.logger.info(f"🔓 Completed atomic execution: {execution_id}")

                    self._execution_id = None
                    self._execution_start_time = None
                    self._account_snapshot = None

    def register_position_intent(self, intent: PositionIntent) -> None:
        """Register a strategy's intention to trade a position."""
        with self._lock:
            self._check_timeout()

            if self._execution_state not in [ExecutionState.ANALYZING, ExecutionState.EXECUTING]:
                raise TradingClientError(
                    f"Cannot register position intent in state: {self._execution_state}"
                )

            self._position_intents.append(intent)
            self.logger.debug(
                f"📝 Registered position intent: {intent.strategy_name} → "
                f"{intent.symbol} ({intent.target_allocation:.1%})"
            )

    def detect_conflicts(self) -> list[ConflictResolution]:
        """Detect and resolve conflicts between strategy position intents."""
        with self._lock:
            self._check_timeout()

            conflicts = []
            symbol_intents: dict[str, list[PositionIntent]] = {}

            # Group intents by symbol
            for intent in self._position_intents:
                if intent.symbol not in symbol_intents:
                    symbol_intents[intent.symbol] = []
                symbol_intents[intent.symbol].append(intent)

            # Detect conflicts for each symbol
            for symbol, intents in symbol_intents.items():
                if len(intents) > 1:
                    conflict = self._resolve_symbol_conflict(symbol, intents)
                    conflicts.append(conflict)

            self._conflicts = conflicts

            if conflicts:
                self.logger.warning(f"⚠️ Resolved {len(conflicts)} position conflicts")
                for conflict in conflicts:
                    self.logger.warning(
                        f"   {conflict.symbol}: {len(conflict.contributing_strategies)} strategies → "
                        f"{conflict.final_allocation:.1%} ({conflict.resolution_method})"
                    )

            return conflicts

    def _resolve_symbol_conflict(
        self, symbol: str, intents: list[PositionIntent]
    ) -> ConflictResolution:
        """Resolve conflicts for a specific symbol."""

        # Check for opposite signals
        long_intents = [i for i in intents if i.target_allocation > 0]
        short_intents = [i for i in intents if i.target_allocation < 0]

        if long_intents and short_intents:
            # Opposite signals - use net position with warning
            net_allocation = sum(intent.target_allocation for intent in intents)
            return ConflictResolution(
                symbol=symbol,
                final_allocation=Decimal(str(net_allocation)),
                contributing_strategies=[i.strategy_name for i in intents],
                resolution_method="net_position",
                confidence=0.7,  # Lower confidence due to conflicting signals
                warnings=[
                    f"Conflicting signals: {len(long_intents)} long, {len(short_intents)} short"
                ],
            )

        # Same direction - aggregate with confidence weighting
        total_weighted_allocation = sum(
            intent.target_allocation * intent.confidence for intent in intents
        )
        total_confidence = sum(intent.confidence for intent in intents)

        if total_confidence > 0:
            final_allocation = total_weighted_allocation / total_confidence
        else:
            final_allocation = Decimal("0")

        # Apply concentration limits
        max_single_position = Decimal("0.15")  # 15% max per position
        if abs(final_allocation) > max_single_position:
            final_allocation = max_single_position if final_allocation > 0 else -max_single_position
            warnings = [f"Position capped at {max_single_position:.1%} due to concentration limits"]
        else:
            warnings = []

        return ConflictResolution(
            symbol=symbol,
            final_allocation=final_allocation,
            contributing_strategies=[i.strategy_name for i in intents],
            resolution_method="confidence_weighted",
            confidence=min(1.0, total_confidence / len(intents)),
            warnings=warnings,
        )

    def get_consolidated_portfolio(self) -> dict[str, float]:
        """Get the final consolidated portfolio after conflict resolution."""
        with self._lock:
            self._check_timeout()

            portfolio = {}

            # Process conflicts (resolved positions)
            for conflict in self._conflicts:
                if abs(conflict.final_allocation) > Decimal("0.001"):  # Minimum position size
                    portfolio[conflict.symbol] = float(conflict.final_allocation)

            # Process uncontested positions
            contested_symbols = {conflict.symbol for conflict in self._conflicts}
            for intent in self._position_intents:
                if intent.symbol not in contested_symbols:
                    if abs(intent.target_allocation) > Decimal("0.001"):
                        portfolio[intent.symbol] = float(intent.target_allocation)

            # Normalize to ensure allocation sums to ~1.0
            total_allocation = sum(abs(allocation) for allocation in portfolio.values())
            if total_allocation > 1.0:
                # Scale down proportionally
                scale_factor = 0.98 / total_allocation  # Leave 2% buffer
                portfolio = {
                    symbol: allocation * scale_factor for symbol, allocation in portfolio.items()
                }
                self.logger.warning(
                    f"Scaled down portfolio by {scale_factor:.1%} due to over-allocation"
                )

            # Add cash allocation if needed
            used_allocation = sum(abs(allocation) for allocation in portfolio.values())
            if used_allocation < 0.95:  # If less than 95% allocated, add cash
                cash_allocation = 1.0 - used_allocation
                portfolio["BIL"] = cash_allocation  # Use BIL as cash proxy

            return portfolio

    def begin_execution_phase(self) -> None:
        """Transition to execution phase after conflict resolution."""
        with self._lock:
            if self._execution_state != ExecutionState.ANALYZING:
                raise TradingClientError(
                    f"Cannot begin execution from state: {self._execution_state}"
                )
            self._set_state(ExecutionState.EXECUTING)

    def begin_settlement_phase(self) -> None:
        """Transition to settlement phase after order execution."""
        with self._lock:
            if self._execution_state != ExecutionState.EXECUTING:
                raise TradingClientError(
                    f"Cannot begin settlement from state: {self._execution_state}"
                )
            self._set_state(ExecutionState.SETTLING)

    def get_execution_summary(self) -> dict[str, Any]:
        """Get summary of the atomic execution."""
        with self._lock:
            return {
                "execution_id": self._execution_id,
                "state": self._execution_state.value,
                "start_time": (
                    self._execution_start_time.isoformat() if self._execution_start_time else None
                ),
                "position_intents": len(self._position_intents),
                "conflicts_resolved": len(self._conflicts),
                "symbols_allocated": len(self._allocated_symbols),
                "is_executing": self.is_executing,
                "conflicts": [
                    {
                        "symbol": c.symbol,
                        "final_allocation": float(c.final_allocation),
                        "strategies": c.contributing_strategies,
                        "method": c.resolution_method,
                        "confidence": c.confidence,
                        "warnings": c.warnings,
                    }
                    for c in self._conflicts
                ],
            }


class AtomicMultiStrategyExecutor:
    """
    Thread-safe multi-strategy executor with atomic operations.

    This class replaces the race condition-prone multi-strategy execution
    with a thread-safe, atomic approach that prevents conflicts and ensures
    consistent state throughout the execution process.
    """

    def __init__(self, engine: Any):
        """Initialize atomic executor."""
        self.engine = engine
        self.logger = logging.getLogger(__name__)
        self._execution_context = AtomicExecutionContext(engine)

    def execute_strategies_atomically(self, execution_id: str | None = None) -> dict[str, Any]:
        """
        Execute all strategies atomically with conflict resolution.

        Args:
            execution_id: Optional execution identifier for tracking

        Returns:
            Execution result with conflict resolution details
        """
        if not execution_id:
            execution_id = f"exec_{int(time.time())}"

        with self._execution_context.atomic_execution(execution_id):

            # Phase 1: Generate strategy signals
            self.logger.info("🧠 Phase 1: Generating strategy signals...")
            strategy_signals, raw_portfolio, strategy_attribution = (
                self.engine.strategy_manager.run_all_strategies()
            )

            # Phase 2: Register position intents for conflict detection
            self.logger.info("📝 Phase 2: Registering position intents...")
            self._register_position_intents(raw_portfolio, strategy_attribution)

            # Phase 3: Detect and resolve conflicts
            self.logger.info("⚖️ Phase 3: Detecting and resolving conflicts...")
            conflicts = self._execution_context.detect_conflicts()

            # Phase 4: Get consolidated portfolio
            self.logger.info("🏗️ Phase 4: Building consolidated portfolio...")
            consolidated_portfolio = self._execution_context.get_consolidated_portfolio()

            # Phase 5: Execute orders atomically
            self.logger.info("🎯 Phase 5: Executing orders...")
            self._execution_context.begin_execution_phase()

            orders_executed = self.engine.rebalance_portfolio(
                consolidated_portfolio, strategy_attribution
            )

            # Phase 6: Settlement and verification
            self.logger.info("✅ Phase 6: Settlement and verification...")
            self._execution_context.begin_settlement_phase()

            # Get final account state
            account_info_after = self.engine.get_account_info()

            execution_summary = self._execution_context.get_execution_summary()
            execution_summary.update(
                {
                    "strategy_signals": strategy_signals,
                    "consolidated_portfolio": consolidated_portfolio,
                    "orders_executed": len(orders_executed) if orders_executed else 0,
                    "conflicts_detected": len(conflicts),
                    "execution_time_seconds": (
                        (
                            datetime.now(UTC) - self._execution_context._execution_start_time
                        ).total_seconds()
                        if self._execution_context._execution_start_time
                        else 0
                    ),
                }
            )

            self.logger.info(f"🎉 Atomic execution completed: {execution_id}")

            return {
                "success": True,
                "execution_id": execution_id,
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio,
                "orders_executed": orders_executed,
                "account_info_after": account_info_after,
                "conflicts_resolved": conflicts,
                "execution_summary": execution_summary,
            }

    def _register_position_intents(
        self, raw_portfolio: dict[str, float], strategy_attribution: dict[str, Any]
    ) -> None:
        """Register position intents from strategy outputs."""

        for symbol, allocation in raw_portfolio.items():
            if abs(allocation) < 0.001:  # Skip tiny allocations
                continue

            # Determine contributing strategies
            contributing_strategies = []
            confidence = 1.0

            if strategy_attribution and symbol in strategy_attribution:
                attribution_data = strategy_attribution[symbol]
                if isinstance(attribution_data, dict):
                    contributing_strategies = attribution_data.get("strategies", ["unknown"])
                    confidence = attribution_data.get("confidence", 1.0)
                else:
                    contributing_strategies = ["unknown"]
            else:
                contributing_strategies = ["unknown"]

            # Register intent for each contributing strategy
            for strategy_name in contributing_strategies:
                intent = PositionIntent(
                    symbol=symbol,
                    target_allocation=Decimal(str(allocation / len(contributing_strategies))),
                    strategy_name=strategy_name,
                    confidence=confidence,
                )
                self._execution_context.register_position_intent(intent)
