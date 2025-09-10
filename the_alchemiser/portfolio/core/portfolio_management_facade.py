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
        min_trade_threshold: Decimal = Decimal("0.001"),
    ) -> None:
        """Initialize the portfolio management facade.

        Args:
            trading_manager: Service for trading operations and market data
            min_trade_threshold: Minimum threshold for trade execution (default: 0.1%)

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

        # === COMPREHENSIVE DATA TRANSFER LOGGING ===
        logger = logging.getLogger(__name__)
        logger.info("=== PORTFOLIO MANAGEMENT FACADE: DATA TRANSFER CHECKPOINT ===")
        logger.info(f"FACADE_RECEIVED_RAW_DATA_TYPE: {type(target_portfolio)}")
        logger.info(
            f"FACADE_RECEIVED_RAW_DATA_COUNT: {len(target_portfolio) if target_portfolio else 0}"
        )
        logger.info(f"FACADE_RECEIVED_PHASE: '{phase}' (normalized: '{phase_normalized}')")

        # Log the exact raw data received
        logger.info("=== RAW DATA RECEIVED BY FACADE ===")
        if target_portfolio:
            total_raw = sum(target_portfolio.values())
            logger.info(f"RAW_DATA_TOTAL: {total_raw}")
            for symbol, weight in target_portfolio.items():
                logger.info(f"RAW_INPUT: {symbol} = {weight} (type: {type(weight)})")
        else:
            logger.error("❌ FACADE_RECEIVED_EMPTY_PORTFOLIO")
            return []

        # Convert to Decimal for internal processing
        target_weights_decimal = {
            symbol: Decimal(str(weight)) for symbol, weight in target_portfolio.items()
        }

        # Log the converted data
        logger.info("=== DATA AFTER DECIMAL CONVERSION ===")
        total_decimal = sum(target_weights_decimal.values())
        logger.info(f"DECIMAL_DATA_TOTAL: {total_decimal}")
        for symbol, weight in target_weights_decimal.items():
            logger.info(f"DECIMAL_CONVERTED: {symbol} = {weight} (type: {type(weight)})")

        # Validate conversion integrity
        original_total = sum(target_portfolio.values())
        converted_total = float(sum(target_weights_decimal.values()))
        if abs(original_total - converted_total) > 0.0001:
            logger.error(
                f"❌ DATA_CONVERSION_ERROR: original={original_total}, converted={converted_total}"
            )
        else:
            logger.info(f"✅ DATA_CONVERSION_VALID: {original_total} -> {converted_total}")

        # Create data integrity checksum for tracking through the system
        data_checksum = f"{len(target_weights_decimal)}:{hash(frozenset(target_weights_decimal.items()))}:{total_decimal:.6f}"
        logger.info(f"DATA_INTEGRITY_CHECKSUM: {data_checksum}")

        # Calculate and filter plan to the requested phase
        full_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights_decimal)

        # === REBALANCING SERVICE RESPONSE LOGGING ===
        logger.info("=== REBALANCING SERVICE RESPONSE ===")
        logger.info(f"REBALANCING_SERVICE_TYPE: {type(self.rebalancing_service).__name__}")
        logger.info(f"FULL_PLAN_TYPE: {type(full_plan)}")
        logger.info(
            f"FULL_PLAN_CONTAINS: {len(full_plan.plans) if hasattr(full_plan, 'plans') else 'unknown'} plans"
        )

        if hasattr(full_plan, "plans"):
            logger.info(
                f"REBALANCE_SYMBOLS_NEEDING_REBALANCE: {getattr(full_plan, 'symbols_needing_rebalance', 'unknown')}"
            )
            logger.info("=== FULL PLAN DETAILS ===")
            for symbol, plan in full_plan.plans.items():
                logger.info(f"PLAN_DETAIL: {symbol}")
                logger.info(f"  needs_rebalance={getattr(plan, 'needs_rebalance', 'unknown')}")
                logger.info(
                    f"  trade_amount={getattr(plan, 'trade_amount', 'unknown')} (type: {type(getattr(plan, 'trade_amount', None))})"
                )
                logger.info(f"  current_weight={getattr(plan, 'current_weight', 'unknown')}")
                logger.info(f"  target_weight={getattr(plan, 'target_weight', 'unknown')}")
        else:
            logger.error(
                f"❌ UNEXPECTED_PLAN_TYPE: {type(full_plan)} does not have 'plans' attribute"
            )
            logger.error(f"❌ PLAN_CONTENT: {full_plan}")
            return []

        # Add logging for debugging trade instruction flow
        logger = logging.getLogger(__name__)
        logger.info(f"=== PORTFOLIO PHASE FILTERING: {phase_normalized.upper()} ===")
        logger.info(f"FACADE_TYPE: {type(self).__name__}")
        logger.info(f"RECEIVED_TARGET_PORTFOLIO: {target_portfolio}")
        logger.info(f"Full plan contains {len(full_plan.plans)} symbols")
        logger.info(f"Symbols needing rebalance: {full_plan.symbols_needing_rebalance}")

        # Log current portfolio state at this exact moment
        current_positions = self.get_current_positions()
        current_portfolio_value = self.get_current_portfolio_value()
        logger.info(f"Current portfolio value: ${current_portfolio_value}")
        logger.info(f"Current positions: {dict(current_positions)}")

        # Log target weights being used
        logger.info("Target weights being used:")
        for symbol, weight in target_weights_decimal.items():
            logger.info(f"  {symbol}: {weight} ({float(weight) * 100:.1f}%)")

        # Log all symbols in the plan for transparency
        for symbol, plan in full_plan.plans.items():
            logger.info(
                f"Symbol {symbol}: needs_rebalance={plan.needs_rebalance}, trade_amount=${plan.trade_amount:.2f}"
            )
            if plan.needs_rebalance:
                action = "SELL" if plan.trade_amount < 0 else "BUY"
                logger.info(f"  → {symbol} would {action} ${abs(plan.trade_amount):.2f}")

        # Add detailed filtering debug logging before filtering
        logger.info(f"=== DETAILED FILTERING DEBUG FOR {phase_normalized.upper()} PHASE ===")
        symbols_that_should_match = []
        for symbol, plan in full_plan.plans.items():
            needs_rebal = plan.needs_rebalance
            trade_amt = plan.trade_amount
            logger.info(
                f"  {symbol}: needs_rebalance={needs_rebal}, trade_amount={trade_amt} (type: {type(trade_amt)})"
            )

            if needs_rebal:
                if phase_normalized == "sell" and trade_amt < 0:
                    symbols_that_should_match.append(f"{symbol} (SELL ${abs(trade_amt):.2f})")
                    logger.info(
                        f"    ✅ {symbol} SHOULD match SELL criteria (trade_amount={trade_amt} < 0)"
                    )
                elif phase_normalized == "buy" and trade_amt > 0:
                    symbols_that_should_match.append(f"{symbol} (BUY ${trade_amt:.2f})")
                    logger.info(
                        f"    ✅ {symbol} SHOULD match BUY criteria (trade_amount={trade_amt} > 0)"
                    )
                else:
                    logger.info(
                        f"    ❌ {symbol} does NOT match {phase_normalized} criteria (trade_amount={trade_amt})"
                    )
            else:
                logger.info(f"    ❌ {symbol} needs_rebalance=False, skipping")

        logger.info(
            f"Expected symbols to match {phase_normalized} phase: {symbols_that_should_match}"
        )

        filtered_plan: dict[str, RebalancePlanDTO] = {}
        
        # Enhanced filtering with explicit type checking and comparison validation
        for symbol, plan in full_plan.plans.items():
            logger.debug(f"Filtering {symbol}: needs_rebalance={plan.needs_rebalance}, trade_amount={plan.trade_amount} (type: {type(plan.trade_amount)})")
            
            # Ensure we have valid data
            if not hasattr(plan, 'needs_rebalance') or not hasattr(plan, 'trade_amount'):
                logger.error(f"❌ Plan for {symbol} missing required attributes")
                continue
                
            needs_rebal = plan.needs_rebalance
            trade_amt = plan.trade_amount
            
            # Explicit type conversion to ensure consistent comparison
            if isinstance(trade_amt, str):
                try:
                    trade_amt = float(trade_amt)
                except (ValueError, TypeError):
                    logger.error(f"❌ Cannot convert trade_amount to number for {symbol}: {trade_amt}")
                    continue
            elif hasattr(trade_amt, '__float__'):  # Handles Decimal and other numeric types
                trade_amt = float(trade_amt)
            
            # Apply filtering logic with explicit conditions
            should_include = False
            if needs_rebal and phase_normalized == "sell" and trade_amt < 0:
                should_include = True
                logger.debug(f"✅ Including {symbol} in SELL phase: trade_amount={trade_amt}")
            elif needs_rebal and phase_normalized == "buy" and trade_amt > 0:
                should_include = True
                logger.debug(f"✅ Including {symbol} in BUY phase: trade_amount={trade_amt}")
            else:
                logger.debug(f"❌ Excluding {symbol}: needs_rebalance={needs_rebal}, phase={phase_normalized}, trade_amount={trade_amt}")
            
            if should_include:
                filtered_plan[symbol] = plan

        logger.info(f"Phase '{phase_normalized}' filtering logic:")
        logger.info("  - Looking for symbols with needs_rebalance=True")
        if phase_normalized == "sell":
            logger.info("  - AND trade_amount < 0 (SELL orders)")
        else:
            logger.info("  - AND trade_amount > 0 (BUY orders)")

        logger.info(f"After filtering: {len(filtered_plan)} symbols match criteria")

        # Log the comparison between expected vs actual
        actual_symbols = list(filtered_plan.keys()) if filtered_plan else []
        logger.info("Expected vs Actual:")
        logger.info(f"  Expected: {symbols_that_should_match}")
        logger.info(f"  Actual:   {actual_symbols}")

        if filtered_plan:
            logger.info(f"Symbols to execute in {phase_normalized} phase: {actual_symbols}")
        else:
            logger.warning(
                f"NO SYMBOLS MATCH {phase_normalized.upper()} PHASE CRITERIA - no trades will be executed"
            )
            logger.warning(
                f"*** POTENTIAL BUG: Expected {len(symbols_that_should_match)} symbols but got 0 ***"
            )

        if logger.isEnabledFor(logging.DEBUG):
            for symbol, plan in full_plan.plans.items():
                logger.debug(
                    f"Symbol {symbol}: needs_rebalance={plan.needs_rebalance}, "
                    f"trade_amount={plan.trade_amount}, phase={phase_normalized}"
                )
            for symbol in filtered_plan:
                logger.debug(f"Filtered symbol for execution: {symbol}")

        if not filtered_plan:
            return []

        # Convert filtered DTO plans to domain objects before execution
        domain_filtered_plan = dto_plans_to_domain(filtered_plan)

        # Log before execution
        logger.info(f"=== EXECUTING {phase_normalized.upper()} PHASE ===")
        logger.info(f"Sending {len(domain_filtered_plan)} symbols to execution service")

        # Execute only the filtered plan; execution service caps buys to BP
        execution_results = self.execution_service.execute_rebalancing_plan(
            domain_filtered_plan, dry_run=False
        )

        # === ENHANCED EXECUTION RESULTS DEBUGGING ===
        logger.info(f"=== POST-EXECUTION ANALYSIS ===")
        logger.info(f"EXECUTION_SERVICE_RETURNED_TYPE: {type(execution_results)}")
        logger.info(f"EXECUTION_SERVICE_RETURNED_CONTENT: {execution_results}")
        
        if isinstance(execution_results, dict):
            orders_placed = execution_results.get("orders_placed", {})
            logger.info(f"ORDERS_PLACED_TYPE: {type(orders_placed)}")
            logger.info(f"ORDERS_PLACED_COUNT: {len(orders_placed) if orders_placed else 0}")
            logger.info(f"ORDERS_PLACED_CONTENT: {orders_placed}")
            
            exec_summary = execution_results.get("execution_summary", {})
            logger.info(f"EXECUTION_SUMMARY_TYPE: {type(exec_summary)}")
            logger.info(f"EXECUTION_SUMMARY_CONTENT: {exec_summary}")
        else:
            logger.error(f"❌ UNEXPECTED_EXECUTION_RESULTS_TYPE: {type(execution_results)}")
        
        logger.info(f"=== DETAILED DOMAIN_FILTERED_PLAN PASSED TO EXECUTION ===")
        logger.info(f"DOMAIN_PLAN_TYPE: {type(domain_filtered_plan)}")
        logger.info(f"DOMAIN_PLAN_COUNT: {len(domain_filtered_plan) if domain_filtered_plan else 0}")
        
        if domain_filtered_plan:
            for symbol, plan in domain_filtered_plan.items():
                logger.info(f"DOMAIN_PLAN_{symbol}:")
                logger.info(f"  Type: {type(plan)}")
                logger.info(f"  needs_rebalance: {getattr(plan, 'needs_rebalance', 'MISSING')}")
                logger.info(f"  trade_amount: {getattr(plan, 'trade_amount', 'MISSING')}")
                logger.info(f"  symbol: {getattr(plan, 'symbol', 'MISSING')}")
        else:
            logger.error(f"❌ DOMAIN_FILTERED_PLAN_IS_EMPTY")

        # Log execution results
        logger.info(f"Execution service returned: {execution_results}")
        logger.info(f"Result type: {type(execution_results)}")

        # Map to OrderDetails
        orders_list: list[OrderDetails] = []
        orders_placed = (
            execution_results.get("orders_placed", {})
            if isinstance(execution_results, dict)
            else {}
        )

        logger.info(f"Orders placed from execution: {orders_placed}")
        logger.info(f"Number of orders returned: {len(orders_placed) if orders_placed else 0}")
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
            qty_float = float(qty_value) if qty_value is not None else 0.0
            # Normalize status to allowed literal values
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

        # Log final results
        logger.info(f"=== {phase_normalized.upper()} PHASE COMPLETE ===")
        logger.info(f"Final orders list: {len(orders_list)} orders created")
        for i, order in enumerate(orders_list):
            logger.info(
                f"Order {i + 1}: {order['side']} {order['qty']} {order['symbol']} (ID: {order['id']})"
            )

        if not orders_list:
            logger.warning(
                f"NO ORDERS CREATED in {phase_normalized} phase - trades may be lost here"
            )

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
