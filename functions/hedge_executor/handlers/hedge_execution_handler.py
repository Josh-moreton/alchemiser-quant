"""Business Unit: hedge_executor | Status: current.

Event handler for hedge execution.

Processes HedgeEvaluationCompleted events and executes hedge orders.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from botocore.exceptions import BotoCoreError, ClientError
from core.option_selector import OptionSelector, SelectedOption
from core.options_execution_service import ExecutionResult, OptionsExecutionService

from the_alchemiser.shared.events.schemas import (
    AllHedgesCompleted,
    HedgeEvaluationCompleted,
    HedgeExecuted,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import (
    AlpacaOptionsAdapter,
    HedgePositionsRepository,
)
from the_alchemiser.shared.options.constants import MAX_SINGLE_POSITION_PCT
from the_alchemiser.shared.options.schemas.hedge_position import (
    HedgePosition,
    HedgePositionState,
    RollState,
)
from the_alchemiser.shared.options.utils import get_underlying_price

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import EventBus

logger = get_logger(__name__)


class HedgeExecutionHandler:
    """Handler for hedge execution events.

    Processes HedgeEvaluationCompleted events and executes protective
    options orders via the Alpaca Options API.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize handler.

        Args:
            container: Application DI container
            event_bus: Optional event bus for publishing

        """
        self._container = container

        # Initialize Alpaca options adapter (standard env var pattern)
        api_key = os.environ.get("ALPACA__KEY", "")
        secret_key = os.environ.get("ALPACA__SECRET", "")
        endpoint = os.environ.get("ALPACA__ENDPOINT", "")
        paper = self._is_paper_from_endpoint(endpoint)

        self._options_adapter = AlpacaOptionsAdapter(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

        self._option_selector = OptionSelector(self._options_adapter)
        self._execution_service = OptionsExecutionService(self._options_adapter)

        # Initialize DynamoDB repository for hedge positions
        table_name = os.environ.get("HEDGE_POSITIONS_TABLE_NAME", "")
        self._positions_repo = HedgePositionsRepository(table_name) if table_name else None

        # Create event bus if not provided
        if event_bus is None:
            from the_alchemiser.shared.events import EventBus as EventBusClass

            self._event_bus = EventBusClass()
        else:
            self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus for subscribing to events."""
        return self._event_bus

    def handle_event(self, event: HedgeEvaluationCompleted) -> None:
        """Handle HedgeEvaluationCompleted event.

        Executes hedge orders based on recommendations.

        Args:
            event: HedgeEvaluationCompleted from hedge evaluator

        """
        correlation_id = event.correlation_id
        plan_id = event.plan_id

        logger.info(
            "Processing HedgeEvaluationCompleted for execution",
            correlation_id=correlation_id,
            plan_id=plan_id,
            recommendations_count=len(event.recommendations),
        )

        # Check if hedging was skipped
        if event.skip_reason:
            logger.info(
                "Hedge evaluation was skipped",
                correlation_id=correlation_id,
                skip_reason=event.skip_reason,
            )
            self._publish_all_hedges_completed(
                event=event,
                results=[],
                _skipped=True,
            )
            return

        # Execute each hedge recommendation
        results: list[HedgeExecuted] = []

        for recommendation in event.recommendations:
            try:
                result = self._execute_recommendation(
                    recommendation=recommendation,
                    correlation_id=correlation_id,
                    plan_id=plan_id,
                    portfolio_nav=event.portfolio_nav,
                )
                if result:
                    results.append(result)
                    self._event_bus.publish(result)
            except Exception as e:
                logger.error(
                    "Failed to execute hedge recommendation",
                    correlation_id=correlation_id,
                    underlying=recommendation.get("underlying_symbol"),
                    error=str(e),
                    exc_info=True,
                )

        # Publish aggregated completion event
        self._publish_all_hedges_completed(event, results)

        logger.info(
            "Hedge execution completed",
            correlation_id=correlation_id,
            total_recommendations=len(event.recommendations),
            successful_hedges=sum(1 for r in results if r.success),
        )

    def _execute_recommendation(
        self,
        recommendation: dict[str, Any],
        correlation_id: str,
        plan_id: str,
        portfolio_nav: Decimal,
    ) -> HedgeExecuted | None:
        """Execute a single hedge recommendation.

        Args:
            recommendation: Hedge recommendation dict
            correlation_id: Correlation ID for tracing
            plan_id: Source plan ID
            portfolio_nav: Portfolio NAV for percentage calculation

        Returns:
            HedgeExecuted event if executed, None on failure

        """
        underlying = recommendation.get("underlying_symbol", "QQQ")
        target_delta = Decimal(recommendation.get("target_delta", "0.15"))
        target_dte = recommendation.get("target_dte", 90)
        premium_budget = Decimal(recommendation.get("premium_budget", "0"))

        # Validate position concentration limit (defensive check)
        # This should already be enforced in HedgeSizer, but double-check here
        max_premium = portfolio_nav * MAX_SINGLE_POSITION_PCT
        if premium_budget > max_premium:
            logger.warning(
                "Premium budget exceeds max concentration at execution time",
                premium_budget=str(premium_budget),
                max_premium=str(max_premium),
                max_concentration_pct=str(MAX_SINGLE_POSITION_PCT),
                nav=str(portfolio_nav),
                underlying=underlying,
            )
            return HedgeExecuted(
                correlation_id=correlation_id,
                causation_id=plan_id,
                event_id=f"hedge-exec-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="hedge_executor",
                source_component="HedgeExecutionHandler",
                hedge_id=f"hedge-{uuid.uuid4()}",
                plan_id=plan_id,
                order_id="",
                option_symbol="",
                underlying_symbol=underlying,
                quantity=0,
                filled_price=Decimal("0"),
                total_premium=Decimal("0"),
                nav_percentage=Decimal("0"),
                success=False,
                error_message=f"Position would exceed max concentration (${float(premium_budget):.2f} > ${float(max_premium):.2f} = {float(MAX_SINGLE_POSITION_PCT):.1%} NAV)",
            )

        # Get underlying price
        underlying_price = get_underlying_price(self._container, underlying)

        # Select optimal contract
        selected = self._option_selector.select_hedge_contract(
            underlying_symbol=underlying,
            target_delta=target_delta,
            target_dte=target_dte,
            premium_budget=premium_budget,
            underlying_price=underlying_price,
            nav=portfolio_nav,
        )

        if selected is None:
            logger.warning(
                "No suitable contract found",
                underlying=underlying,
            )
            return HedgeExecuted(
                correlation_id=correlation_id,
                causation_id=plan_id,
                event_id=f"hedge-exec-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="hedge_executor",
                source_component="HedgeExecutionHandler",
                hedge_id=f"hedge-{uuid.uuid4()}",
                plan_id=plan_id,
                order_id="",
                option_symbol="",
                underlying_symbol=underlying,
                quantity=0,
                filled_price=Decimal("0"),
                total_premium=Decimal("0"),
                nav_percentage=Decimal("0"),
                success=False,
                error_message="No suitable contract found",
            )

        # Execute order
        hedge_id = f"hedge-{uuid.uuid4()}"
        result = self._execution_service.execute_hedge_order(
            selected_option=selected,
            underlying_symbol=underlying,
            client_order_id=hedge_id,
        )

        # Calculate NAV percentage
        nav_pct = Decimal("0")
        if portfolio_nav > 0 and result.total_premium > 0:
            nav_pct = result.total_premium / portfolio_nav

        # Persist position to DynamoDB if execution succeeded
        if result.success and self._positions_repo:
            try:
                # Extract template and spread info from recommendation
                hedge_template = recommendation.get("hedge_template", "tail_first")
                is_spread = recommendation.get("is_spread", False)
                short_leg_symbol = recommendation.get("short_leg_symbol")
                short_leg_strike = (
                    Decimal(recommendation["short_leg_strike"])
                    if recommendation.get("short_leg_strike")
                    else None
                )
                short_leg_entry_price = (
                    Decimal(recommendation["short_leg_entry_price"])
                    if recommendation.get("short_leg_entry_price")
                    else None
                )
                short_leg_current_delta = (
                    Decimal(recommendation["short_leg_current_delta"])
                    if recommendation.get("short_leg_current_delta")
                    else None
                )

                self._persist_hedge_position(
                    hedge_id=hedge_id,
                    selected=selected,
                    result=result,
                    correlation_id=correlation_id,
                    portfolio_nav=portfolio_nav,
                    nav_pct=nav_pct,
                    hedge_template=hedge_template,
                    is_spread=is_spread,
                    short_leg_symbol=short_leg_symbol,
                    short_leg_strike=short_leg_strike,
                    short_leg_entry_price=short_leg_entry_price,
                    short_leg_current_delta=short_leg_current_delta,
                )
            except (BotoCoreError, ClientError) as e:
                logger.error(
                    "Failed to persist hedge position to DynamoDB",
                    hedge_id=hedge_id,
                    error=str(e),
                    exc_info=True,
                )

        return HedgeExecuted(
            correlation_id=correlation_id,
            causation_id=plan_id,
            event_id=f"hedge-exec-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_executor",
            source_component="HedgeExecutionHandler",
            hedge_id=hedge_id,
            plan_id=plan_id,
            order_id=result.order_id or "",
            option_symbol=result.option_symbol,
            underlying_symbol=underlying,
            quantity=result.filled_quantity,
            filled_price=result.filled_price or Decimal("0"),
            total_premium=result.total_premium,
            nav_percentage=nav_pct,
            success=result.success,
            error_message=result.error_message,
        )

    def _publish_all_hedges_completed(
        self,
        event: HedgeEvaluationCompleted,
        results: list[HedgeExecuted],
        *,
        _skipped: bool = False,
    ) -> None:
        """Publish AllHedgesCompleted aggregation event.

        Args:
            event: Source evaluation event
            results: List of execution results
            _skipped: Whether hedging was skipped (reserved for future use)

        """
        succeeded = sum(1 for r in results if r.success)
        failed = len(results) - succeeded

        total_premium = sum((r.total_premium for r in results), Decimal("0"))
        total_nav_pct = sum((r.nav_percentage for r in results), Decimal("0"))

        hedge_positions = [
            {
                "hedge_id": r.hedge_id,
                "option_symbol": r.option_symbol,
                "underlying": r.underlying_symbol,
                "quantity": r.quantity,
                "premium": str(r.total_premium),
            }
            for r in results
            if r.success
        ]

        failed_symbols = [r.underlying_symbol for r in results if not r.success]

        completed_event = AllHedgesCompleted(
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"all-hedges-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_executor",
            source_component="HedgeExecutionHandler",
            plan_id=event.plan_id,
            total_hedges=len(results),
            succeeded_hedges=succeeded,
            failed_hedges=failed,
            total_premium_spent=total_premium,
            total_nav_pct=total_nav_pct,
            hedge_positions=hedge_positions,
            failed_symbols=failed_symbols,
        )

        self._event_bus.publish(completed_event)

    def _persist_hedge_position(
        self,
        hedge_id: str,
        selected: SelectedOption,
        result: ExecutionResult,
        correlation_id: str,
        portfolio_nav: Decimal,
        nav_pct: Decimal,
        *,
        hedge_template: str = "tail_first",
        is_spread: bool = False,
        short_leg_symbol: str | None = None,
        short_leg_strike: Decimal | None = None,
        short_leg_entry_price: Decimal | None = None,
        short_leg_current_delta: Decimal | None = None,
    ) -> None:
        """Persist hedge position to DynamoDB.

        Args:
            hedge_id: Unique hedge identifier
            selected: Selected option with contract details
            result: Execution result with fill details
            correlation_id: Correlation ID for tracing
            portfolio_nav: Portfolio NAV at entry
            nav_pct: Premium as percentage of NAV
            hedge_template: Template used (tail_first or smoothing)
            is_spread: Whether this is a spread position
            short_leg_symbol: OCC symbol for short leg (spreads only)
            short_leg_strike: Strike price of short leg (spreads only)
            short_leg_entry_price: Entry price of short leg (spreads only)
            short_leg_current_delta: Current delta of short leg (spreads only)

        Raises:
            botocore.exceptions.BotoCoreError: If DynamoDB operation fails
            botocore.exceptions.ClientError: If DynamoDB request fails

        """
        if not self._positions_repo:
            return

        contract = selected.contract
        now = datetime.now(UTC)

        position = HedgePosition(
            hedge_id=hedge_id,
            correlation_id=correlation_id,
            option_symbol=contract.symbol,
            underlying_symbol=contract.underlying_symbol,
            option_type=contract.option_type,
            strike_price=contract.strike_price,
            expiration_date=contract.expiration_date,
            contracts=result.filled_quantity,
            entry_price=result.filled_price or Decimal("0"),
            entry_date=now,
            entry_delta=contract.delta or Decimal("0.15"),  # Fallback to target delta
            total_premium_paid=result.total_premium,
            state=HedgePositionState.ACTIVE,
            roll_state=RollState.HOLDING,
            last_updated=now,
            hedge_template=hedge_template,
            nav_at_entry=portfolio_nav,
            nav_percentage=nav_pct,
            is_spread=is_spread,
            short_leg_symbol=short_leg_symbol,
            short_leg_strike=short_leg_strike,
            short_leg_entry_price=short_leg_entry_price,
            short_leg_current_delta=short_leg_current_delta,
        )

        self._positions_repo.put_position(position)

        logger.info(
            "Hedge position persisted to DynamoDB",
            hedge_id=hedge_id,
            option_symbol=contract.symbol,
            expiration_date=contract.expiration_date.isoformat(),
        )

    @staticmethod
    def _is_paper_from_endpoint(ep: str | None) -> bool:
        """Determine if endpoint is for paper trading.

        Args:
            ep: Endpoint URL string or None.

        Returns:
            True if endpoint is for paper trading, False for live trading.

        """
        if not ep:
            return True
        ep_norm = ep.strip().rstrip("/").lower()
        if ep_norm.endswith("/v2"):
            ep_norm = ep_norm[:-3]
        # Explicit paper host
        if "paper-api.alpaca.markets" in ep_norm:
            return True
        # Explicit live host
        return not ("api.alpaca.markets" in ep_norm and "paper" not in ep_norm)
