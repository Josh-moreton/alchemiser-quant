"""Business Unit: portfolio assessment & management; Status: current.

Portfolio management facade - unified interface for all portfolio operations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.core.trading_services_facade import (
    TradingServicesFacade as TradingServiceManager,
)
from the_alchemiser.execution.mappers.order_domain_mappers import normalize_order_status
from the_alchemiser.portfolio.allocation.rebalance_calculator import (
    RebalanceCalculator,
)
from the_alchemiser.portfolio.holdings.position_analyzer import PositionAnalyzer
from the_alchemiser.portfolio.mappers.portfolio_rebalancing_mapping import (
    dto_plans_to_domain,
    dto_to_domain_rebalance_plan,
)
from the_alchemiser.portfolio.schemas.rebalancing import RebalancePlanDTO
from the_alchemiser.portfolio.state.attribution_engine import (
    StrategyAttributionEngine,
)
from the_alchemiser.shared.math.num import floats_equal
from the_alchemiser.shared.utils.serialization import ensure_serialized_dict
from the_alchemiser.shared.value_objects.core_types import OrderDetails
from the_alchemiser.strategy.registry.strategy_registry import StrategyType

from ..allocation.portfolio_rebalancing_service import (
    PortfolioRebalancingService,
)
from ..allocation.rebalance_execution_service import (
    RebalanceExecutionService,
)
from .portfolio_analysis_service import (
    PortfolioAnalysisService,
)


class PortfolioManagementFacade:
    """Unified facade for all portfolio management operations.

    Provides a single entry point for portfolio rebalancing, analysis,
    and execution while maintaining clean separation of concerns.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        min_trade_threshold: Decimal = Decimal("0.01"),
    ) -> None:
        """Initialize the portfolio management facade.

        Args:
            trading_manager: Service for trading operations and market data
            min_trade_threshold: Minimum threshold for trade execution

        """
        self.trading_manager = trading_manager

        # Initialize domain objects
        self.rebalance_calculator = RebalanceCalculator(min_trade_threshold)
        self.position_analyzer = PositionAnalyzer()
        self.attribution_engine = StrategyAttributionEngine()

        # Initialize application services
        self.rebalancing_service = PortfolioRebalancingService(
            trading_manager,
            self.rebalance_calculator,
            self.position_analyzer,
            self.attribution_engine,
        )
        self.analysis_service = PortfolioAnalysisService(
            trading_manager, self.position_analyzer, self.attribution_engine
        )
        self.execution_service = RebalanceExecutionService(trading_manager)

    # Portfolio Analysis Operations
    def get_portfolio_analysis(self) -> dict[str, Any]:
        """Get comprehensive portfolio analysis."""
        return self.analysis_service.get_comprehensive_portfolio_analysis()

    def analyze_portfolio_drift(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Analyze portfolio drift from target allocations."""
        return self.analysis_service.analyze_portfolio_drift(target_weights)

    def get_strategy_performance(self) -> dict[str, Any]:
        """Get strategy performance analysis."""
        return self.analysis_service.get_strategy_performance_analysis()

    def compare_strategy_allocations(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Compare current vs target strategy allocations."""
        return self.analysis_service.compare_target_vs_current_strategy_allocation(target_weights)

    # Portfolio Rebalancing Operations
    def calculate_rebalancing_plan(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, Any]:
        """Calculate complete rebalancing plan.

        Returns:
            Serialized dictionary containing rebalancing plan data.

        """
        plan_dto = self.rebalancing_service.calculate_rebalancing_plan(
            target_weights, current_positions, portfolio_value
        )
        return plan_dto.model_dump()

    def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Get comprehensive rebalancing summary.

        Returns:
            Serialized dictionary containing rebalancing summary data.

        """
        summary_dto = self.rebalancing_service.get_rebalancing_summary(target_weights)
        return summary_dto.model_dump()

    def estimate_rebalancing_impact(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Estimate the impact of rebalancing.

        Returns:
            Serialized dictionary containing rebalancing impact analysis.

        """
        impact_dto = self.rebalancing_service.estimate_rebalancing_impact(target_weights)
        return impact_dto.model_dump()

    def get_symbols_to_sell(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get symbols requiring sell orders."""
        return self.rebalancing_service.get_symbols_requiring_sells(target_weights)

    def get_symbols_to_buy(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get symbols requiring buy orders."""
        return self.rebalancing_service.get_symbols_requiring_buys(target_weights)

    # Portfolio Execution Operations
    def validate_rebalancing_plan(self, rebalance_plan: dict[str, Any]) -> dict[str, Any]:
        """Validate a rebalancing plan before execution."""
        return self.execution_service.validate_rebalancing_plan(rebalance_plan)

    def execute_rebalancing(
        self, target_weights: dict[str, Decimal], dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute complete portfolio rebalancing."""
        logging.debug(
            "PortfolioManagementFacade.execute_rebalancing called: target_weights=%s dry_run=%s",
            target_weights,
            dry_run,
        )
        # Calculate rebalancing plan (DTO collection)
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)

        logging.debug(
            "Rebalancing plan computed for symbols=%s",
            list(rebalance_plan.plans.keys()),
        )

        # Convert DTO plans once for validation & potential execution
        domain_plans = dto_plans_to_domain(rebalance_plan.plans)

        # Validate plan (uses domain objects)
        validation = self.execution_service.validate_rebalancing_plan(domain_plans)
        logging.debug("Validation results: %s", validation)
        if not validation["is_valid"]:
            logging.warning(
                "Rebalancing validation failed. Issues: %s | Symbols to trade: %s",
                validation.get("issues", []),
                validation.get("symbols_to_trade", []),
            )
            return {
                "status": "validation_failed",
                "validation_results": validation,
                "execution_results": None,
            }

        # Execute plan with already converted domain plans
        execution_results = self.execution_service.execute_rebalancing_plan(domain_plans, dry_run)

        logging.debug("Execution results: %s", execution_results)
        try:
            summary = execution_results.get("execution_summary", {})
            logging.info(
                "Rebalancing execution summary: total=%s success=%s failed=%s",
                summary.get("total_orders", 0),
                summary.get("successful_orders", 0),
                summary.get("failed_orders", 0),
            )
        except Exception:
            pass

        result_dict = {
            "status": "completed",
            "validation_results": validation,
            "execution_results": execution_results,
            "rebalance_plan": rebalance_plan,
        }
        return ensure_serialized_dict(result_dict)

    def execute_single_symbol_rebalance(
        self, symbol: str, target_weight: Decimal, dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute rebalancing for a single symbol."""
        # Calculate plan for single symbol
        target_weights = {symbol: target_weight}
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)

        if symbol not in rebalance_plan.plans:
            return {
                "status": "error",
                "message": f"No rebalancing plan generated for {symbol}",
            }

        # Execute single symbol rebalance
        return self.execution_service.execute_single_rebalance(
            symbol, dto_to_domain_rebalance_plan(rebalance_plan.plans[symbol]), dry_run
        )

    # Comprehensive Operations
    def get_complete_portfolio_overview(
        self, target_weights: dict[str, Decimal] | None = None
    ) -> dict[str, Any]:
        """Get complete portfolio overview with analysis and rebalancing info.

        Returns:
            Serialized dictionary containing comprehensive portfolio overview.

        """
        overview = {
            "portfolio_analysis": self.get_portfolio_analysis(),
            "strategy_performance": self.get_strategy_performance(),
        }

        if target_weights:
            overview.update(
                {
                    "drift_analysis": self.analyze_portfolio_drift(target_weights),
                    "rebalancing_summary": self.get_rebalancing_summary(target_weights),
                    "rebalancing_impact": self.estimate_rebalancing_impact(target_weights),
                    "strategy_comparison": self.compare_strategy_allocations(target_weights),
                }
            )

        return overview

    def perform_portfolio_rebalancing_workflow(
        self,
        target_weights: dict[str, Decimal],
        dry_run: bool = True,
        include_analysis: bool = True,
    ) -> dict[str, Any]:
        """Complete portfolio rebalancing workflow with analysis."""
        workflow_results: dict[str, Any] = {}

        # Step 1: Pre-rebalancing analysis
        if include_analysis:
            workflow_results["pre_rebalancing_analysis"] = {
                "portfolio_analysis": self.get_portfolio_analysis(),
                "drift_analysis": self.analyze_portfolio_drift(target_weights),
                "impact_estimate": self.estimate_rebalancing_impact(target_weights),
            }

        # Step 2: Calculate and validate rebalancing plan
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)
        domain_plans = dto_plans_to_domain(rebalance_plan.plans)
        validation = self.execution_service.validate_rebalancing_plan(domain_plans)
        workflow_results["rebalancing_plan"] = ensure_serialized_dict(
            {
                "plan": rebalance_plan,
                "validation": validation,
                "summary": self.rebalancing_service.get_rebalancing_summary(target_weights),
            }
        )

        # Step 3: Execute if validation passes
        if validation["is_valid"]:
            execution_results = self.execution_service.execute_rebalancing_plan(
                domain_plans, dry_run
            )
            workflow_results["execution"] = execution_results
        else:
            workflow_results["execution"] = {
                "status": "skipped",
                "reason": "Validation failed",
                "issues": validation.get("issues", []),
            }

        # Step 4: Post-rebalancing analysis (if executed)
        if include_analysis and validation["is_valid"] and not dry_run:
            workflow_results["post_rebalancing_analysis"] = {
                "portfolio_analysis": self.get_portfolio_analysis(),
                "remaining_drift": self.analyze_portfolio_drift(target_weights),
            }

        return workflow_results

    # RebalancingService Protocol Implementation
    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        _strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Main rebalancing interface compatible with RebalancingService protocol.

        Args:
            target_portfolio: Target allocation weights by symbol
            strategy_attribution: Optional strategy attribution mapping

        Returns:
            List of order details from execution

        """
        # Convert to Decimal for internal processing
        target_weights_decimal = {
            symbol: Decimal(str(weight)) for symbol, weight in target_portfolio.items()
        }

        # Execute rebalancing and get results
        execution_result = self.execute_rebalancing(target_weights_decimal, dry_run=False)

        # Extract orders from execution results
        orders_list: list[OrderDetails] = []

        if execution_result.get("status") == "completed":
            execution_results = execution_result.get("execution_results", {})
            orders_placed = execution_results.get("orders_placed", {})

            # Convert to OrderDetails format
            for symbol, order_data in orders_placed.items():
                if not isinstance(order_data, dict):
                    continue

                # Determine side and quantity from order data
                side = order_data.get("side", "buy")
                qty_value = (
                    order_data.get("shares")
                    or order_data.get("quantity")
                    or order_data.get("amount")
                    or 0
                )
                qty_float = float(qty_value) if qty_value is not None else 0.0

                # Normalize status to allowed literal values for DTO
                status_norm = normalize_order_status(str(order_data.get("status", "new")))

                order_details: OrderDetails = {
                    "id": order_data.get("order_id", "unknown"),
                    "symbol": symbol,
                    "qty": qty_float,
                    "side": side,
                    "order_type": "market",
                    "time_in_force": "day",
                    "status": status_norm,
                    "filled_qty": 0.0,
                    "filled_avg_price": None,
                    "created_at": "",
                    "updated_at": "",
                }
                orders_list.append(order_details)

        else:
            # Surface validation failure via a log entry; return empty list per protocol
            logging.warning(
                "Rebalancing workflow did not complete (status=%s). No orders mapped.",
                execution_result.get("status"),
            )

        return orders_list

    def rebalance_portfolio_phase(
        self,
        target_portfolio: dict[str, float],
        phase: str,  # "sell" or "buy"
    ) -> list[OrderDetails]:
        """Execute only one phase of the rebalancing: sells or buys.

        This enables true sequential execution: execute sells first, wait for BP refresh,
        then execute buys sized to current buying power.
        """
        phase_normalized = phase.lower().strip()
        if phase_normalized not in {"sell", "buy"}:
            phase_normalized = "buy"

        # Convert to Decimal for internal processing
        target_weights_decimal = {
            symbol: Decimal(str(weight)) for symbol, weight in target_portfolio.items()
        }

        # Calculate and filter plan to the requested phase
        full_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights_decimal)
        
        # Add logging for debugging trade instruction flow
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Rebalance phase '{phase_normalized}': Full plan contains {len(full_plan.plans)} symbols")
        logger.info(f"Symbols needing rebalance: {full_plan.symbols_needing_rebalance}")
        
        filtered_plan: dict[str, RebalancePlanDTO] = {
            symbol: plan
            for symbol, plan in full_plan.plans.items()
            if plan.needs_rebalance
            and (
                (phase_normalized == "sell" and plan.trade_amount < 0)
                or (phase_normalized == "buy" and plan.trade_amount > 0)
            )
        }
        
        logger.info(f"Phase '{phase_normalized}' filtered plan contains {len(filtered_plan)} symbols")
        
        if logger.isEnabledFor(logging.DEBUG):
            for symbol, plan in full_plan.plans.items():
                logger.debug(f"Symbol {symbol}: needs_rebalance={plan.needs_rebalance}, "
                           f"trade_amount={plan.trade_amount}, phase={phase_normalized}")
            for symbol in filtered_plan:
                logger.debug(f"Filtered symbol for execution: {symbol}")

        if not filtered_plan:
            return []

        # Convert filtered DTO plans to domain objects before execution
        domain_filtered_plan = dto_plans_to_domain(filtered_plan)
        # Execute only the filtered plan; execution service caps buys to BP
        execution_results = self.execution_service.execute_rebalancing_plan(
            domain_filtered_plan, dry_run=False
        )

        # Map to OrderDetails
        orders_list: list[OrderDetails] = []
        orders_placed = (
            execution_results.get("orders_placed", {})
            if isinstance(execution_results, dict)
            else {}
        )
        for symbol, order_data in orders_placed.items():
            if not isinstance(order_data, dict):
                continue
            side = order_data.get("side", "buy")
            qty_value = (
                order_data.get("shares")
                or order_data.get("quantity")
                or order_data.get("amount")
                or 0
            )
            order_status = normalize_order_status(order_data.get("status", "unknown"))
            order_id = order_data.get("id") or order_data.get("order_id")

            # Build OrderDetails dict
            order_details = OrderDetails(
                {
                    "symbol": symbol,
                    "qty": qty_value,
                    "side": side,
                    "status": order_status,
                    "id": order_id,
                    "order_type": order_data.get("order_type", "market"),
                    "time_in_force": order_data.get("time_in_force", "day"),
                    "submitted_at": order_data.get("submitted_at"),
                    "filled_at": order_data.get("filled_at"),
                    "avg_fill_price": order_data.get("avg_fill_price"),
                }
            )
            orders_list.append(order_details)

        return orders_list

    def execute_rebalance_phase_with_plan(
        self,
        rebalance_plan: Any,  # RebalancePlanCollectionDTO
        phase: str,  # "sell" or "buy"
    ) -> list[OrderDetails]:
        """Execute only one phase of the rebalancing using a pre-calculated plan.

        This method prevents trade instruction loss by using a pre-calculated plan
        instead of recalculating, which could show different results after portfolio
        state changes from sell orders.

        Args:
            rebalance_plan: Pre-calculated RebalancePlanCollectionDTO
            phase: "sell" or "buy"

        Returns:
            List of executed orders as OrderDetails
        """
        phase_normalized = phase.lower().strip()
        if phase_normalized not in {"sell", "buy"}:
            phase_normalized = "buy"

        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔒 Executing phase '{phase_normalized}' with PRE-CALCULATED plan to preserve trade instructions")
        logger.info(f"Pre-calculated plan contains {len(rebalance_plan.plans)} symbols")
        logger.info(f"Symbols needing rebalance: {rebalance_plan.symbols_needing_rebalance}")

        # Filter the pre-calculated plan to the requested phase
        filtered_plan: dict[str, RebalancePlanDTO] = {
            symbol: plan
            for symbol, plan in rebalance_plan.plans.items()
            if plan.needs_rebalance
            and (
                (phase_normalized == "sell" and plan.trade_amount < 0)
                or (phase_normalized == "buy" and plan.trade_amount > 0)
            )
        }
        
        logger.info(f"Phase '{phase_normalized}' with pre-calculated plan contains {len(filtered_plan)} symbols")
        
        if logger.isEnabledFor(logging.DEBUG):
            for symbol, plan in rebalance_plan.plans.items():
                logger.debug(f"Pre-calculated symbol {symbol}: needs_rebalance={plan.needs_rebalance}, "
                           f"trade_amount={plan.trade_amount}, phase={phase_normalized}")
            for symbol in filtered_plan:
                logger.debug(f"Pre-calculated filtered symbol for execution: {symbol}")

        if not filtered_plan:
            logger.info(f"No {phase_normalized} trades needed from pre-calculated plan")
            return []

        # Convert filtered DTO plans to domain objects before execution
        domain_filtered_plan = dto_plans_to_domain(filtered_plan)
        # Execute only the filtered plan; execution service caps buys to BP
        execution_results = self.execution_service.execute_rebalancing_plan(
            domain_filtered_plan, dry_run=False
        )

        # Map to OrderDetails
        orders_list: list[OrderDetails] = []
        orders_placed = (
            execution_results.get("orders_placed", {})
            if isinstance(execution_results, dict)
            else {}
        )
        for symbol, order_data in orders_placed.items():
            if not isinstance(order_data, dict):
                continue
            side = order_data.get("side", "buy")
            qty_value = (
                order_data.get("shares")
                or order_data.get("quantity")
                or order_data.get("amount")
                or 0
            )
            order_status = normalize_order_status(order_data.get("status", "unknown"))
            order_id = order_data.get("id") or order_data.get("order_id")

            # Build OrderDetails dict
            order_details = OrderDetails(
                {
                    "symbol": symbol,
                    "qty": qty_value,
                    "side": side,
                    "status": order_status,
                    "id": order_id,
                    "order_type": order_data.get("order_type", "market"),
                    "time_in_force": order_data.get("time_in_force", "day"),
                    "submitted_at": order_data.get("submitted_at"),
                    "filled_at": order_data.get("filled_at"),
                    "avg_fill_price": order_data.get("avg_fill_price"),
                }
            )
            orders_list.append(order_details)

        logger.info(f"✅ Executed {len(orders_list)} {phase_normalized} orders from pre-calculated plan")
        return orders_list

    # Utility methods
    def get_current_portfolio_value(self) -> Decimal:
        """Get current total portfolio value."""
        portfolio_dto = self.trading_manager.get_portfolio_value()
        return portfolio_dto.value

    def get_current_positions(self) -> dict[str, Decimal]:
        """Get current position values."""
        positions = self.trading_manager.get_all_positions()
        values: dict[str, Decimal] = {}
        for pos in positions:
            try:
                mv = Decimal(str(getattr(pos, "market_value", 0) or 0))
            except Exception:
                mv = Decimal("0")
            if mv > Decimal("0"):
                values[getattr(pos, "symbol", "")] = mv
        return values

    def get_current_weights(self) -> dict[str, Decimal]:
        """Get current portfolio weights."""
        positions = self.get_current_positions()
        portfolio_value = self.get_current_portfolio_value()

        if floats_equal(portfolio_value, 0.0):
            return {}

        return {symbol: value / portfolio_value for symbol, value in positions.items()}
