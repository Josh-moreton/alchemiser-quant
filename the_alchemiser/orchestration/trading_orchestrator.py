"""Business Unit: orchestration | Status: current.

Minimal TradingOrchestrator for test compatibility and transitional wiring.

This orchestrator coordinates high-level workflow steps for signal analysis,
portfolio analysis, optional rebalancing, and execution. It is intentionally
lightweight and designed to work with mocked dependencies in tests.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from the_alchemiser.shared.errors.exceptions import (
    AlchemiserError,
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger

# Component identifiers for structured logging
_COMPONENT_EXECUTE_SIGNALS: str = "TradingOrchestrator.execute_strategy_signals"
"""Component identifier for execute_strategy_signals method in structured logging."""

_COMPONENT_EXECUTE_SIGNALS_WITH_TRADING: str = (
    "TradingOrchestrator.execute_strategy_signals_with_trading"
)
"""Component identifier for execute_strategy_signals_with_trading method in structured logging."""


@runtime_checkable
class SignalOrchestratorLike(Protocol):
    """Protocol for signal analysis orchestrator."""

    def analyze_signals(
        self,
    ) -> dict[str, object] | None:  # pragma: no cover - protocol
        """Analyze signals and return a result mapping or None on failure."""


@runtime_checkable
class PortfolioOrchestratorLike(Protocol):
    """Protocol for portfolio analysis orchestrator."""

    def get_comprehensive_account_data(
        self,
    ) -> dict[str, object] | None:  # pragma: no cover
        """Return comprehensive account data for decision-making."""

    def analyze_allocation_comparison(
        self, account_data: dict[str, object]
    ) -> dict[str, object] | None:  # pragma: no cover
        """Analyze allocation vs target and return comparison mapping."""

    def create_rebalance_plan(
        self, signals: object, account_data: dict[str, object]
    ) -> object:  # pragma: no cover
        """Create a rebalance plan from signals and account data."""


@runtime_checkable
class ExecutionOrchestratorLike(Protocol):
    """Protocol for execution orchestrator."""

    def execute_rebalance_plan(self, plan: object) -> dict[str, object] | None:  # pragma: no cover
        """Execute a rebalance plan and return an execution summary mapping."""


@runtime_checkable
class NotificationServiceLike(Protocol):
    """Protocol for notification service."""

    def notify(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
        """Send a notification with arbitrary payload."""


@dataclass
class _Deps:
    signal_orchestrator: SignalOrchestratorLike
    portfolio_orchestrator: PortfolioOrchestratorLike
    execution_orchestrator: ExecutionOrchestratorLike
    notification_service: NotificationServiceLike


class TradingOrchestrator:
    """Coordinate trading workflow steps using injected orchestrators/services."""

    def __init__(
        self,
        *,
        signal_orchestrator: SignalOrchestratorLike,
        portfolio_orchestrator: PortfolioOrchestratorLike,
        execution_orchestrator: ExecutionOrchestratorLike,
        notification_service: NotificationServiceLike,
        live_trading: bool,
    ) -> None:
        """Initialize orchestrator with dependencies.

        Args:
            signal_orchestrator: Component that analyzes strategy signals
            portfolio_orchestrator: Component providing account/portfolio analysis
            execution_orchestrator: Component executing rebalance plans
            notification_service: Component used to send notifications
            live_trading: Whether orchestrator runs in live trading mode

        """
        self.deps = _Deps(
            signal_orchestrator=signal_orchestrator,
            portfolio_orchestrator=portfolio_orchestrator,
            execution_orchestrator=execution_orchestrator,
            notification_service=notification_service,
        )
        self.live_trading: bool = live_trading
        self.logger = get_logger(__name__)

        # Workflow state tracking for tests
        self.workflow_state: dict[str, Any] = {
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_step": None,
            "last_correlation_id": None,
        }

    def execute_strategy_signals(self, correlation_id: str | None = None) -> dict[str, Any] | None:
        """Analyze strategy signals and update workflow state.

        Args:
            correlation_id: Optional correlation ID for tracing. Generated if not provided.

        Returns:
            Dict with analysis results if successful; None on failure

        """
        correlation_id = correlation_id or str(uuid.uuid4())
        self.workflow_state["last_correlation_id"] = correlation_id
        self.workflow_state["signal_generation_in_progress"] = True
        try:
            result = self.deps.signal_orchestrator.analyze_signals()
            if not result or not result.get("success"):
                self.logger.warning(
                    "Signal analysis returned no result or unsuccessful",
                    extra={
                        "correlation_id": correlation_id,
                        "component": _COMPONENT_EXECUTE_SIGNALS,
                    },
                )
                return None
            self.workflow_state["last_successful_step"] = "signal_generation"
            return {
                "success": True,
                "correlation_id": correlation_id,
                "strategy_signals": result.get("strategy_signals", []),
                "consolidated_portfolio_dto": result.get("consolidated_portfolio_dto"),
            }
        except (DataProviderError, TradingClientError) as exc:
            self.logger.error(
                "Signal analysis failed with specific error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS,
                },
            )
            return None
        except AlchemiserError as exc:
            self.logger.error(
                "Signal analysis failed with system error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS,
                },
            )
            return None
        except Exception as exc:
            self.logger.error(
                "Signal analysis failed with unexpected error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS,
                },
            )
            return None
        finally:
            self.workflow_state["signal_generation_in_progress"] = False

    def execute_strategy_signals_with_trading(self) -> dict[str, Any] | None:
        """Run full workflow: analyze signals, analyze portfolio, and execute if needed.

        Returns:
            Dict with complete workflow results if successful; None on failure.
            Includes strategy_signals, account_data, rebalance_plan, and execution_result.

        """
        base = self.execute_strategy_signals()
        if not base:
            return None

        correlation_id = base.get("correlation_id", str(uuid.uuid4()))

        try:
            account_data = self.deps.portfolio_orchestrator.get_comprehensive_account_data()
            if not account_data:
                self.logger.warning(
                    "Failed to retrieve account data",
                    extra={
                        "correlation_id": correlation_id,
                        "component": _COMPONENT_EXECUTE_SIGNALS_WITH_TRADING,
                    },
                )
                return None

            comparison = self.deps.portfolio_orchestrator.analyze_allocation_comparison(
                account_data
            )

            # No rebalancing required
            if not comparison or not comparison.get("needs_rebalancing"):
                self.workflow_state["last_successful_step"] = "analysis"
                return {
                    "success": True,
                    "strategy_signals": base.get("strategy_signals", []),
                    "account_data": account_data,
                    "rebalance_plan": None,
                    "execution_result": None,
                }

            # Build rebalance plan
            plan = self.deps.portfolio_orchestrator.create_rebalance_plan(
                base.get("strategy_signals"), account_data
            )
            if not getattr(plan, "items", None):
                self.workflow_state["last_successful_step"] = "planning"
                return {
                    "success": True,
                    "strategy_signals": base.get("strategy_signals", []),
                    "account_data": account_data,
                    "rebalance_plan": plan,
                    "execution_result": None,
                }

            # Execute plan
            self.workflow_state["rebalancing_in_progress"] = True
            exec_result = self.deps.execution_orchestrator.execute_rebalance_plan(plan)
            self.workflow_state["last_successful_step"] = "execution"

            return {
                "success": (
                    bool(exec_result.get("success", True))
                    if isinstance(exec_result, dict)
                    else True
                ),
                "strategy_signals": base.get("strategy_signals", []),
                "account_data": account_data,
                "rebalance_plan": plan,
                "execution_result": exec_result,
            }
        except (DataProviderError, TradingClientError) as exc:
            self.logger.error(
                "Trading workflow failed with specific error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS_WITH_TRADING,
                },
            )
            return None
        except AlchemiserError as exc:
            self.logger.error(
                "Trading workflow failed with system error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS_WITH_TRADING,
                },
            )
            return None
        except Exception as exc:
            self.logger.error(
                "Trading workflow failed with unexpected error",
                exc_info=exc,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "component": _COMPONENT_EXECUTE_SIGNALS_WITH_TRADING,
                },
            )
            return None
        finally:
            self.workflow_state["rebalancing_in_progress"] = False
            self.workflow_state["trading_in_progress"] = False
