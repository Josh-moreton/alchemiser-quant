"""Business Unit: strategy | Status: current.

Per-strategy rebalancer that orchestrates the full independent book flow:
read positions, calculate rebalance plan, persist plan, enqueue trades.

This replaces the aggregation + portfolio planner flow with a direct
strategy-to-execution pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.errors.exceptions import PortfolioError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.portfolio_snapshot import MarginInfo
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.services.rebalance_plan_calculator import (
    RebalancePlanCalculator,
)
from the_alchemiser.shared.services.strategy_position_service import (
    StrategyPositionService,
)
from the_alchemiser.shared.services.trade_enqueue_service import (
    enqueue_rebalance_trades,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)

MODULE_NAME = "strategy.core.strategy_rebalancer"


@dataclass(frozen=True)
class RebalanceResult:
    """Result of a strategy rebalance execution."""

    strategy_id: str
    trade_count: int
    strategy_capital: Decimal
    plan_id: str
    correlation_id: str


class StrategyRebalancer:
    """Orchestrates per-strategy rebalance: positions -> plan -> trades.

    Each strategy operates on its own capital slice and position book.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        trade_ledger_table: str,
        execution_queue_url: str,
        execution_runs_table: str,
        rebalance_plan_table: str | None = None,
    ) -> None:
        """Initialize the strategy rebalancer.

        Args:
            alpaca_manager: Alpaca client for account data and prices.
            trade_ledger_table: DynamoDB table for trade ledger (position queries).
            execution_queue_url: SQS queue URL for trade execution.
            execution_runs_table: DynamoDB table for execution run tracking.
            rebalance_plan_table: DynamoDB table for plan persistence (optional).

        """
        self._alpaca_manager = alpaca_manager
        self._position_service = StrategyPositionService(table_name=trade_ledger_table)
        self._planner = RebalancePlanCalculator()
        self._execution_queue_url = execution_queue_url
        self._execution_runs_table = execution_runs_table
        self._rebalance_plan_table = rebalance_plan_table

    def execute(
        self,
        strategy_id: str,
        dsl_file: str,
        allocation: Decimal,
        target_weights: dict[str, Decimal],
        correlation_id: str,
        data_freshness: dict[str, Any] | None = None,
    ) -> RebalanceResult:
        """Execute the full rebalance flow for a single strategy.

        Args:
            strategy_id: Strategy identifier (e.g., '1-KMLM').
            dsl_file: DSL strategy file name.
            allocation: Strategy's capital allocation fraction (0-1).
            target_weights: Target portfolio weights from DSL evaluation.
            correlation_id: Workflow correlation ID for tracing.
            data_freshness: Market data freshness info.

        Returns:
            RebalanceResult with execution details.

        Raises:
            PortfolioError: If rebalance fails at any step.

        """
        start_time = time.perf_counter()

        logger.info(
            "Starting per-strategy rebalance",
            extra={
                "strategy_id": strategy_id,
                "dsl_file": dsl_file,
                "allocation": str(allocation),
                "correlation_id": correlation_id,
                "target_symbols": sorted(target_weights.keys()),
            },
        )

        try:
            # Step 1: Get account equity from Alpaca
            account = self._alpaca_manager.get_account()
            if not account:
                raise PortfolioError(
                    "Could not retrieve account data from Alpaca",
                    module=MODULE_NAME,
                    operation="execute",
                    correlation_id=correlation_id,
                )

            equity = self._extract_equity(account)
            strategy_capital = equity * allocation

            logger.info(
                "Calculated strategy capital from account equity",
                extra={
                    "strategy_id": strategy_id,
                    "account_equity": str(equity),
                    "allocation": str(allocation),
                    "strategy_capital": str(strategy_capital),
                    "correlation_id": correlation_id,
                    "note": "Equity read is per-worker; concurrent workers may see different equity values if trades settle between reads",
                },
            )

            # Step 2: Get current prices for target symbols
            target_symbols = list(target_weights.keys())
            prices_float = self._alpaca_manager.get_current_prices(target_symbols)
            current_prices = {
                symbol: Decimal(str(price)) for symbol, price in prices_float.items() if price > 0
            }

            # Step 3: Build per-strategy portfolio snapshot
            margin_info = self._build_margin_info(account)
            snapshot = self._position_service.build_portfolio_snapshot(
                strategy_id=strategy_id,
                strategy_capital=strategy_capital,
                current_prices=current_prices,
                margin_info=margin_info,
            )

            # Step 4: Build strategy allocation (weights already sum to ~1.0)
            strategy_allocation = StrategyAllocation(
                target_weights=target_weights,
                portfolio_value=strategy_capital,
                correlation_id=correlation_id,
            )

            # Step 5: Calculate rebalance plan
            strategy_contributions = {strategy_id: target_weights}
            plan = self._planner.build_plan(
                strategy=strategy_allocation,
                snapshot=snapshot,
                correlation_id=correlation_id,
                causation_id=correlation_id,
                strategy_contributions=strategy_contributions,
            )

            # Add strategy attribution to plan metadata
            plan = plan.model_copy(
                update={
                    "metadata": {
                        **(plan.metadata or {}),
                        "strategy_name": strategy_id,
                        "strategy_attribution": {
                            symbol: {strategy_id: 1.0} for symbol in target_weights
                        },
                        "dsl_file": dsl_file,
                        "execution_mode": "independent",
                    }
                }
            )

            # Step 6: Persist rebalance plan (optional)
            self._persist_plan(plan)

            # Step 7: Enqueue trades to SQS
            trade_count = enqueue_rebalance_trades(
                rebalance_plan=plan,
                correlation_id=correlation_id,
                causation_id=correlation_id,
                queue_url=self._execution_queue_url,
                runs_table_name=self._execution_runs_table,
                alpaca_equity=equity,
                data_freshness=data_freshness,
                strategies_evaluated=1,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "Per-strategy rebalance completed",
                extra={
                    "strategy_id": strategy_id,
                    "dsl_file": dsl_file,
                    "trade_count": trade_count,
                    "plan_id": plan.plan_id,
                    "strategy_capital": str(strategy_capital),
                    "correlation_id": correlation_id,
                    "duration_ms": duration_ms,
                },
            )

            return RebalanceResult(
                strategy_id=strategy_id,
                trade_count=trade_count,
                strategy_capital=strategy_capital,
                plan_id=plan.plan_id,
                correlation_id=correlation_id,
            )

        except PortfolioError:
            raise
        except Exception as e:
            logger.error(
                "Per-strategy rebalance failed",
                extra={
                    "strategy_id": strategy_id,
                    "dsl_file": dsl_file,
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise PortfolioError(
                f"Strategy rebalance failed for {strategy_id}: {e}",
                module=MODULE_NAME,
                operation="execute",
                correlation_id=correlation_id,
            ) from e

    def _extract_equity(self, account: dict[str, Any] | object) -> Decimal:
        """Extract equity from account info."""
        if isinstance(account, dict):
            equity_raw = account.get("equity", 0)
        else:
            equity_raw = getattr(account, "equity", 0)

        if hasattr(equity_raw, "value"):
            return Decimal(str(equity_raw.value))
        return Decimal(str(equity_raw))

    def _build_margin_info(self, account: dict[str, Any] | object) -> MarginInfo:
        """Build MarginInfo from account data."""

        def _get(field: str) -> Decimal | None:
            val = account.get(field) if isinstance(account, dict) else getattr(account, field, None)
            if val is None:
                return None
            if hasattr(val, "value"):
                return Decimal(str(val.value))
            return Decimal(str(val))

        def _get_int(field: str) -> int | None:
            val = account.get(field) if isinstance(account, dict) else getattr(account, field, None)
            if val is None:
                return None
            return int(val)

        return MarginInfo(
            buying_power=_get("buying_power"),
            initial_margin=_get("initial_margin"),
            maintenance_margin=_get("maintenance_margin"),
            equity=_get("equity"),
            regt_buying_power=_get("regt_buying_power"),
            daytrading_buying_power=_get("daytrading_buying_power"),
            multiplier=_get_int("multiplier"),
        )

    def _persist_plan(self, plan: RebalancePlan) -> None:
        """Persist rebalance plan to DynamoDB for auditability."""
        if not self._rebalance_plan_table:
            logger.debug("Rebalance plan persistence disabled (no table configured)")
            return

        try:
            from the_alchemiser.shared.config.config import load_settings
            from the_alchemiser.shared.repositories.dynamodb_rebalance_plan_repository import (
                DynamoDBRebalancePlanRepository,
            )

            settings = load_settings()
            ttl_days = settings.rebalance_plan.ttl_days

            repository = DynamoDBRebalancePlanRepository(
                table_name=self._rebalance_plan_table,
                ttl_days=ttl_days,
            )
            repository.save_plan(plan)

            logger.info(
                "Persisted rebalance plan",
                extra={
                    "plan_id": plan.plan_id,
                    "correlation_id": plan.correlation_id,
                    "item_count": len(plan.items),
                },
            )

        except Exception as exc:
            logger.warning(
                f"Failed to persist rebalance plan: {exc}",
                extra={
                    "plan_id": plan.plan_id,
                    "correlation_id": plan.correlation_id,
                },
            )
