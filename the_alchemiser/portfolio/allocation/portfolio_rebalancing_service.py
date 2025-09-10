"""Business Unit: portfolio assessment & management; Status: current.

Portfolio rebalancing service - main application orchestrator.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.core.trading_services_facade import (
    TradingServicesFacade as TradingServiceManager,
)
from the_alchemiser.portfolio.mappers.portfolio_rebalancing_mapping import (
    rebalance_plans_dict_to_collection_dto,
)
from the_alchemiser.portfolio.schemas.rebalancing import (
    RebalancePlanCollectionDTO,
    RebalancingImpactDTO,
    RebalancingSummaryDTO,
)

# Removed adapter imports - functionality implemented directly in service
from the_alchemiser.shared.dto import (
    OrderRequestDTO,
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    RebalancePlanDTO,
    StrategySignalDTO,
)

from ..holdings.position_analyzer import PositionAnalyzer
from ..holdings.position_delta import PositionDelta
from ..state.attribution_engine import (
    StrategyAttributionEngine,
)
from .rebalance_calculator import RebalanceCalculator
from .rebalance_plan import RebalancePlan

# Module logger for consistent logging
logger = logging.getLogger(__name__)


class PortfolioRebalancingService:
    """Main application service for portfolio rebalancing operations.

    Orchestrates domain objects to provide high-level rebalancing functionality
    while maintaining clean separation from infrastructure concerns.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        rebalance_calculator: RebalanceCalculator | None = None,
        position_analyzer: PositionAnalyzer | None = None,
        attribution_engine: StrategyAttributionEngine | None = None,
        min_trade_threshold: Decimal = Decimal("0.01"),
    ) -> None:
        """Initialize the portfolio rebalancing service.

        Args:
            trading_manager: Service for trading operations and market data
            rebalance_calculator: Calculator for rebalancing plans (optional)
            position_analyzer: Analyzer for position deltas (optional)
            attribution_engine: Engine for strategy attribution (optional)
            min_trade_threshold: Minimum threshold for trade execution

        """
        self.trading_manager = trading_manager
        self.rebalance_calculator = rebalance_calculator or RebalanceCalculator(min_trade_threshold)
        self.position_analyzer = position_analyzer or PositionAnalyzer()
        self.attribution_engine = attribution_engine or StrategyAttributionEngine()

    def _calculate_rebalancing_plan_domain(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, RebalancePlan]:
        """Internal method to calculate rebalancing plan as domain objects.

        Used by methods that need to work with domain objects internally.
        """
        # Fetch current data if not provided
        if current_positions is None:
            current_positions = self._get_current_position_values()

        if portfolio_value is None:
            portfolio_value = self._get_portfolio_value()

        # Calculate rebalancing plan using domain logic
        return self.rebalance_calculator.calculate_rebalance_plan(
            target_weights, current_positions, portfolio_value
        )

    def calculate_rebalancing_plan(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> RebalancePlanCollectionDTO:
        """Calculate a complete rebalancing plan for the portfolio.

        Args:
            target_weights: Target allocation weights by symbol
            current_positions: Current position values (fetched if None)
            portfolio_value: Total portfolio value (calculated if None)

        Returns:
            RebalancePlanCollectionDTO with rebalancing plans for all symbols

        """
        # === REBALANCING SERVICE DATA TRANSFER LOGGING ===
        logger.info("=== PORTFOLIO REBALANCING SERVICE: CALCULATE_REBALANCING_PLAN ===")
        logger.info(f"SERVICE_TYPE: {type(self).__name__}")
        logger.info(f"RECEIVED_TARGET_WEIGHTS_TYPE: {type(target_weights)}")
        logger.info(f"RECEIVED_TARGET_WEIGHTS_COUNT: {len(target_weights) if target_weights else 0}")
        logger.info(f"RECEIVED_CURRENT_POSITIONS: {current_positions is not None}")
        logger.info(f"RECEIVED_PORTFOLIO_VALUE: {portfolio_value}")
        
        # Log exact received data
        if target_weights:
            logger.info("=== RECEIVED TARGET WEIGHTS ===")
            target_total = sum(target_weights.values())
            logger.info(f"TARGET_WEIGHTS_TOTAL: {target_total}")
            for symbol, weight in target_weights.items():
                logger.info(f"RECEIVED_WEIGHT: {symbol} = {weight} (type: {type(weight)})")
        else:
            logger.error("❌ REBALANCING_SERVICE_RECEIVED_EMPTY_TARGET_WEIGHTS")
            return RebalancePlanCollectionDTO(
                success=False,
                plans={},
                total_symbols=0,
                symbols_needing_rebalance=0,
                total_trade_value=Decimal("0"),
                error="Empty target weights received",
            )
        
        try:
            # === DATA FETCHING PHASE ===
            logger.info("=== DATA FETCHING PHASE ===")
            
            # Fetch current data if not provided
            if current_positions is None:
                logger.info("Fetching current position values...")
                current_positions = self._get_current_position_values()
                logger.info(f"FETCHED_POSITIONS_COUNT: {len(current_positions) if current_positions else 0}")
            
            if portfolio_value is None:
                logger.info("Fetching portfolio value...")
                portfolio_value = self._get_portfolio_value()
                logger.info(f"FETCHED_PORTFOLIO_VALUE: {portfolio_value}")
            
            # Log fetched data
            logger.info("=== FETCHED DATA SUMMARY ===")
            logger.info(f"PORTFOLIO_VALUE: {portfolio_value}")
            if current_positions:
                logger.info(f"CURRENT_POSITIONS_COUNT: {len(current_positions)}")
                for symbol, value in current_positions.items():
                    logger.info(f"CURRENT_POSITION: {symbol} = ${value}")
            else:
                logger.info("CURRENT_POSITIONS: Empty")
            
            # === DOMAIN CALCULATION PHASE ===
            logger.info("=== CALLING DOMAIN CALCULATION ===")
            logger.info(f"CALCULATOR_TYPE: {type(self.rebalance_calculator).__name__}")
            logger.info(f"PASSING_TO_CALCULATOR:")
            logger.info(f"  target_weights: {len(target_weights)} symbols")
            logger.info(f"  current_positions: {len(current_positions) if current_positions else 0} positions")
            logger.info(f"  portfolio_value: ${portfolio_value}")
            
            # Use internal domain method
            domain_plans = self._calculate_rebalancing_plan_domain(
                target_weights, current_positions, portfolio_value
            )
            
            # === DOMAIN RESULTS ANALYSIS ===
            logger.info("=== DOMAIN CALCULATION RESULTS ===")
            logger.info(f"DOMAIN_PLANS_TYPE: {type(domain_plans)}")
            logger.info(f"DOMAIN_PLANS_COUNT: {len(domain_plans) if domain_plans else 0}")
            
            if domain_plans:
                logger.info("=== DOMAIN PLANS DETAILS ===")
                for symbol, plan in domain_plans.items():
                    logger.info(f"DOMAIN_PLAN: {symbol}")
                    logger.info(f"  needs_rebalance: {plan.needs_rebalance}")
                    logger.info(f"  trade_amount: {plan.trade_amount}")
                    logger.info(f"  current_weight: {plan.current_weight}")
                    logger.info(f"  target_weight: {plan.target_weight}")
            else:
                logger.error("❌ DOMAIN_CALCULATION_RETURNED_EMPTY")
            
            # === DTO CONVERSION PHASE ===
            logger.info("=== DTO CONVERSION PHASE ===")
            dto_result = rebalance_plans_dict_to_collection_dto(domain_plans)
            
            logger.info(f"DTO_RESULT_TYPE: {type(dto_result)}")
            logger.info(f"DTO_SUCCESS: {dto_result.success if hasattr(dto_result, 'success') else 'unknown'}")
            logger.info(f"DTO_PLANS_COUNT: {len(dto_result.plans) if hasattr(dto_result, 'plans') else 'unknown'}")
            logger.info(f"DTO_SYMBOLS_NEEDING_REBALANCE: {dto_result.symbols_needing_rebalance if hasattr(dto_result, 'symbols_needing_rebalance') else 'unknown'}")
            
            logger.info("=== REBALANCING SERVICE CALCULATION COMPLETE ===")
            return dto_result
            
        except Exception as e:
            logger.error(f"❌ REBALANCING_SERVICE_CALCULATION_FAILED: {e}")
            logger.exception("Full exception details:")
            return RebalancePlanCollectionDTO(
                success=False,
                plans={},
                total_symbols=0,
                symbols_needing_rebalance=0,
                total_trade_value=Decimal("0"),
                error=f"Failed to calculate rebalancing plan: {e}",
            )

    def analyze_position_deltas(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, PositionDelta]:
        """Analyze position deltas between current and target allocations.

        Args:
            target_weights: Target allocation weights by symbol
            current_positions: Current position values (fetched if None)
            portfolio_value: Total portfolio value (calculated if None)

        Returns:
            Dictionary mapping symbols to their position deltas

        """
        # Fetch current data if not provided
        if current_positions is None:
            current_positions = self._get_current_position_values()

        if portfolio_value is None:
            portfolio_value = self._get_portfolio_value()

        # Calculate target position values
        target_positions = {
            symbol: portfolio_value * weight for symbol, weight in target_weights.items()
        }

        # Analyze deltas using domain logic
        return self.position_analyzer.analyze_all_positions(current_positions, target_positions)

    def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> RebalancingSummaryDTO:
        """Get a comprehensive summary of rebalancing requirements.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            RebalancingSummaryDTO with summary analysis

        """
        try:
            current_positions = self._get_current_position_values()
            portfolio_value = self._get_portfolio_value()

            # Calculate rebalancing plan
            rebalance_plan_result = self.calculate_rebalancing_plan(
                target_weights, current_positions, portfolio_value
            )

            if not rebalance_plan_result.success:
                return RebalancingSummaryDTO(
                    success=False,
                    total_portfolio_value=portfolio_value,
                    total_symbols=0,
                    symbols_needing_rebalance=0,
                    total_trade_value=Decimal("0"),
                    largest_trade_symbol=None,
                    largest_trade_value=Decimal("0"),
                    rebalance_threshold_pct=self.rebalance_calculator.min_trade_threshold,
                    execution_feasible=False,
                    estimated_costs=Decimal("0"),
                    error=rebalance_plan_result.error,
                )

            # Extract rebalancing metrics from the plan collection
            plans = rebalance_plan_result.plans
            largest_trade_value = Decimal("0")
            largest_trade_symbol = None

            for symbol, plan in plans.items():
                if plan.trade_amount_abs > largest_trade_value:
                    largest_trade_value = plan.trade_amount_abs
                    largest_trade_symbol = symbol

            # Estimate basic costs (simplified for this phase)
            estimated_costs = rebalance_plan_result.total_trade_value * Decimal(
                "0.005"
            )  # 0.5% cost estimate

            return RebalancingSummaryDTO(
                success=True,
                total_portfolio_value=portfolio_value,
                total_symbols=rebalance_plan_result.total_symbols,
                symbols_needing_rebalance=rebalance_plan_result.symbols_needing_rebalance,
                total_trade_value=rebalance_plan_result.total_trade_value,
                largest_trade_symbol=largest_trade_symbol,
                largest_trade_value=largest_trade_value,
                rebalance_threshold_pct=self.rebalance_calculator.min_trade_threshold,
                execution_feasible=rebalance_plan_result.symbols_needing_rebalance > 0,
                estimated_costs=estimated_costs,
            )
        except Exception as e:
            return RebalancingSummaryDTO(
                success=False,
                total_portfolio_value=Decimal("0"),
                total_symbols=0,
                symbols_needing_rebalance=0,
                total_trade_value=Decimal("0"),
                largest_trade_symbol=None,
                largest_trade_value=Decimal("0"),
                rebalance_threshold_pct=Decimal("0"),
                execution_feasible=False,
                estimated_costs=Decimal("0"),
                error=f"Failed to generate rebalancing summary: {e}",
            )

    def get_symbols_requiring_sells(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get list of symbols that need to be sold for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring sell orders

        """
        rebalance_plan = self._calculate_rebalancing_plan_domain(target_weights)
        sell_plans = self.rebalance_calculator.get_sell_plans(rebalance_plan)
        return list(sell_plans.keys())

    def get_symbols_requiring_buys(self, target_weights: dict[str, Decimal]) -> list[str]:
        """Get list of symbols that need to be bought for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring buy orders

        """
        rebalance_plan = self._calculate_rebalancing_plan_domain(target_weights)
        buy_plans = self.rebalance_calculator.get_buy_plans(rebalance_plan)
        return list(buy_plans.keys())

    def estimate_rebalancing_impact(
        self, target_weights: dict[str, Decimal]
    ) -> RebalancingImpactDTO:
        """Estimate the impact of rebalancing on the portfolio.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            RebalancingImpactDTO with impact analysis

        """
        try:
            current_positions = self._get_current_position_values()
            portfolio_value = self._get_portfolio_value()

            # Calculate position deltas
            position_deltas = self.analyze_position_deltas(
                target_weights, current_positions, portfolio_value
            )

            # Calculate turnover and trade metrics
            portfolio_turnover = self.position_analyzer.calculate_portfolio_turnover(
                position_deltas, portfolio_value
            )
            positions_to_sell = self.position_analyzer.get_positions_to_sell(position_deltas)
            positions_to_buy = self.position_analyzer.get_positions_to_buy(position_deltas)

            # Calculate estimated costs and impact (simplified for this phase)
            total_trade_value = sum(abs(delta.quantity) for delta in position_deltas.values())
            estimated_transaction_costs = total_trade_value * Decimal(
                "0.002"
            )  # 0.2% transaction cost
            estimated_slippage = total_trade_value * Decimal("0.001")  # 0.1% slippage
            total_estimated_costs = estimated_transaction_costs + estimated_slippage

            # Risk analysis (simplified)
            num_trades = len(positions_to_sell) + len(positions_to_buy)
            portfolio_risk_change = Decimal(str(portfolio_turnover)) * Decimal(
                "0.1"
            )  # Simplified risk calculation
            concentration_risk_change = Decimal("0")  # Placeholder

            # Execution analysis
            if num_trades <= 3:
                execution_complexity = "LOW"
                recommended_time = 15
                market_impact_risk = "LOW"
            elif num_trades <= 6:
                execution_complexity = "MEDIUM"
                recommended_time = 30
                market_impact_risk = "MEDIUM"
            else:
                execution_complexity = "HIGH"
                recommended_time = 60
                market_impact_risk = "HIGH"

            # Net benefit calculation (simplified)
            net_benefit_estimate = -total_estimated_costs  # Conservative approach

            # Recommendation logic
            if (
                total_estimated_costs > portfolio_value * Decimal("0.01") or num_trades > 10
            ):  # > 1% of portfolio
                recommendation = "DEFER"
            else:
                recommendation = "EXECUTE"

            return RebalancingImpactDTO(
                success=True,
                portfolio_risk_change=portfolio_risk_change,
                concentration_risk_change=concentration_risk_change,
                estimated_transaction_costs=estimated_transaction_costs,
                estimated_slippage=estimated_slippage,
                total_estimated_costs=total_estimated_costs,
                execution_complexity=execution_complexity,
                recommended_execution_time=recommended_time,
                market_impact_risk=market_impact_risk,
                net_benefit_estimate=net_benefit_estimate,
                recommendation=recommendation,
            )
        except Exception as e:
            return RebalancingImpactDTO(
                success=False,
                portfolio_risk_change=Decimal("0"),
                concentration_risk_change=Decimal("0"),
                estimated_transaction_costs=Decimal("0"),
                estimated_slippage=Decimal("0"),
                total_estimated_costs=Decimal("0"),
                execution_complexity="UNKNOWN",
                recommended_execution_time=0,
                market_impact_risk="UNKNOWN",
                net_benefit_estimate=Decimal("0"),
                recommendation="CANCEL",
                error=f"Failed to estimate rebalancing impact: {e}",
            )

    def _calculate_strategy_changes(
        self, current_exposures: dict[str, Any], target_exposures: dict[str, Any]
    ) -> dict[str, Decimal]:
        """Calculate changes in strategy allocations."""
        changes = {}

        # Get all strategies from both current and target
        all_strategies = set(current_exposures.keys()) | set(target_exposures.keys())

        for strategy in all_strategies:
            current_allocation = current_exposures.get(strategy, {}).get(
                "allocation_percentage", Decimal("0")
            )
            target_allocation = target_exposures.get(strategy, {}).get(
                "allocation_percentage", Decimal("0")
            )
            changes[strategy] = target_allocation - current_allocation

        return changes

    # ==================== NEW DTO-BASED METHODS ====================

    def get_portfolio_state_dto(self, correlation_id: str | None = None) -> PortfolioStateDTO:
        """Get current portfolio state as DTO for inter-module communication.

        Args:
            correlation_id: Optional correlation ID for tracking

        Returns:
            PortfolioStateDTO with current portfolio state

        """
        try:
            # Get current portfolio data
            current_positions = self._get_current_position_values()
            portfolio_value = self._get_portfolio_value()

            # Get account summary for additional metrics
            account_summary = self.trading_manager.get_account_summary()

            # Get positions data
            positions_data = self.trading_manager.get_positions()

            # Create portfolio context
            portfolio_context = {
                "total_value": portfolio_value,
                "portfolio_value": portfolio_value,
                "cash_value": account_summary.get("cash", Decimal("0")),
                "equity_value": account_summary.get("equity", Decimal("0")),
                "buying_power": account_summary.get("buying_power", Decimal("0")),
                "day_pnl": account_summary.get("unrealized_pl", Decimal("0")),
                "day_pnl_percent": account_summary.get("unrealized_plpc", Decimal("0")),
                "account_id": account_summary.get("account_number"),
            }

            # Convert portfolio data to DTO directly using existing DTO structure
            import uuid
            from datetime import UTC, datetime

            from the_alchemiser.shared.dto.portfolio_state_dto import PositionDTO

            correlation_id = correlation_id or f"portfolio_{uuid.uuid4().hex[:12]}"

            # Convert position dictionaries to PositionDTO objects
            positions_list = positions_data.get("positions", []) if positions_data else []
            position_dtos = []

            for position in positions_list:
                position_dto = PositionDTO(
                    symbol=position.get("symbol", ""),
                    quantity=Decimal(str(position.get("qty", position.get("quantity", 0)))),
                    average_cost=Decimal(
                        str(position.get("avg_entry_price", position.get("average_cost", 0)))
                    ),
                    current_price=Decimal(str(position.get("current_price", 0))),
                    market_value=Decimal(str(position.get("market_value", 0))),
                    unrealized_pnl=Decimal(
                        str(position.get("unrealized_pl", position.get("unrealized_pnl", 0)))
                    ),
                    unrealized_pnl_percent=Decimal(
                        str(
                            position.get(
                                "unrealized_plpc", position.get("unrealized_pnl_percent", 0)
                            )
                        )
                    ),
                    last_updated=position.get("last_updated"),
                    side=position.get("side"),
                    cost_basis=Decimal(str(position.get("cost_basis", 0)))
                    if position.get("cost_basis") is not None
                    else None,
                )
                position_dtos.append(position_dto)

            # Create portfolio metrics from the portfolio data
            metrics = PortfolioMetricsDTO(
                total_value=Decimal(
                    str(
                        portfolio_context.get(
                            "total_value", portfolio_context.get("portfolio_value", 0)
                        )
                    )
                ),
                cash_value=Decimal(str(portfolio_context.get("cash_value", 0))),
                equity_value=Decimal(str(portfolio_context.get("equity_value", 0))),
                buying_power=Decimal(str(portfolio_context.get("buying_power", 0))),
                day_pnl=Decimal(str(portfolio_context.get("day_pnl", 0))),
                day_pnl_percent=Decimal(str(portfolio_context.get("day_pnl_percent", 0))),
                total_pnl=Decimal(str(portfolio_context.get("total_pnl", 0))),
                total_pnl_percent=Decimal(str(portfolio_context.get("total_pnl_percent", 0))),
            )

            return PortfolioStateDTO(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                portfolio_id="main_portfolio",
                positions=position_dtos,
                metrics=metrics,
                metadata=portfolio_context.get("metadata", {}),
            )

        except Exception as e:
            # Return minimal portfolio state with error context
            import uuid
            from datetime import UTC, datetime

            correlation_id = correlation_id or f"portfolio_error_{uuid.uuid4().hex[:12]}"

            return PortfolioStateDTO(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                portfolio_id="main_portfolio",
                positions=[],
                metrics=PortfolioMetricsDTO(
                    total_value=Decimal("0"),
                    cash_value=Decimal("0"),
                    equity_value=Decimal("0"),
                    buying_power=Decimal("0"),
                    day_pnl=Decimal("0"),
                    day_pnl_percent=Decimal("0"),
                    total_pnl=Decimal("0"),
                    total_pnl_percent=Decimal("0"),
                ),
                metadata={"error": str(e)},
            )

    def process_strategy_signals_dto(
        self,
        signals: list[StrategySignalDTO],
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Process strategy signals and determine portfolio adjustments.

        Args:
            signals: List of strategy signal DTOs
            correlation_id: Optional correlation ID for tracking

        Returns:
            Dictionary with processing results and recommended actions

        """
        try:
            # Convert signals to target weights
            target_weights = {}
            signal_context = []

            for signal in signals:
                if signal.action in ["BUY", "SELL"] and signal.allocation_weight is not None:
                    # Use allocation weight if provided
                    weight = float(signal.allocation_weight)
                    if signal.action == "SELL":
                        weight = 0  # Sell means reduce to zero
                    target_weights[signal.symbol] = Decimal(str(weight))

                signal_context.append(
                    {
                        "symbol": signal.symbol,
                        "action": signal.action,
                        "confidence": float(signal.confidence),
                        "strategy": signal.strategy_name,
                        "reasoning": signal.reasoning,
                        "correlation_id": signal.correlation_id,
                    }
                )

            # Calculate rebalancing impact
            if target_weights:
                impact = self.estimate_rebalancing_impact(target_weights)
                needs_rebalancing = len(target_weights) > 0
            else:
                # No actionable signals
                impact = None
                needs_rebalancing = False

            return {
                "correlation_id": correlation_id,
                "signals_processed": len(signals),
                "actionable_signals": len(target_weights),
                "target_weights": {k: float(v) for k, v in target_weights.items()},
                "needs_rebalancing": needs_rebalancing,
                "estimated_impact": impact.model_dump() if impact else None,
                "signal_context": signal_context,
                "timestamp": signals[0].timestamp if signals else None,
            }

        except Exception as e:
            return {
                "correlation_id": correlation_id,
                "signals_processed": len(signals) if signals else 0,
                "actionable_signals": 0,
                "error": str(e),
                "needs_rebalancing": False,
            }

    def create_rebalance_plan_dto(
        self,
        target_weights: dict[str, Decimal],
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> RebalancePlanDTO | None:
        """Create a rebalance plan DTO for execution module consumption.

        Args:
            target_weights: Target allocation weights by symbol
            correlation_id: Optional correlation ID for tracking
            causation_id: Optional causation ID for traceability

        Returns:
            RebalancePlanDTO or None if no rebalancing needed

        """
        try:
            # Calculate rebalancing plan using existing method
            plan_collection = self.calculate_rebalancing_plan(target_weights)

            if not plan_collection.success or not plan_collection.plans:
                return None

            # Convert to RebalancePlanDTO
            import uuid
            from datetime import UTC, datetime

            from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanItemDTO

            correlation_id = correlation_id or f"rebalance_{uuid.uuid4().hex[:12]}"
            causation_id = causation_id or correlation_id
            plan_id = f"plan_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Convert plans to DTO items
            items = []
            total_portfolio_value = self._get_portfolio_value()
            total_trade_value = Decimal("0")

            for symbol, plan in plan_collection.plans.items():
                if hasattr(plan, "target_value") and hasattr(plan, "current_value"):
                    trade_amount = plan.target_value - plan.current_value

                    if abs(trade_amount) > self.rebalance_calculator.min_trade_threshold:
                        action = "BUY" if trade_amount > 0 else "SELL"

                        item = RebalancePlanItemDTO(
                            symbol=symbol,
                            current_weight=plan.current_value / total_portfolio_value
                            if total_portfolio_value > 0
                            else Decimal("0"),
                            target_weight=plan.target_value / total_portfolio_value
                            if total_portfolio_value > 0
                            else Decimal("0"),
                            weight_diff=(plan.target_value - plan.current_value)
                            / total_portfolio_value
                            if total_portfolio_value > 0
                            else Decimal("0"),
                            target_value=plan.target_value,
                            current_value=plan.current_value,
                            trade_amount=trade_amount,
                            action=action,
                            priority=1,  # Default priority
                        )
                        items.append(item)
                        total_trade_value += abs(trade_amount)

            if not items:
                return None

            return RebalancePlanDTO(
                correlation_id=correlation_id,
                causation_id=causation_id,
                timestamp=datetime.now(UTC),
                plan_id=plan_id,
                total_portfolio_value=total_portfolio_value,
                total_trade_value=total_trade_value,
                items=items,
            )

        except Exception:
            # Log error but don't raise - return None to indicate no plan
            return None

    def rebalance_plan_to_orders_dto(
        self,
        rebalance_plan: RebalancePlanDTO,
        execution_config: dict[str, Any] | None = None,
    ) -> list[OrderRequestDTO]:
        """Convert rebalance plan to order requests for execution module.

        Args:
            rebalance_plan: RebalancePlanDTO to convert
            execution_config: Optional execution configuration

        Returns:
            List of OrderRequestDTO for execution

        """
        # Convert rebalance plan DTO to list of order request DTOs directly
        order_requests = []

        # Default values for execution configuration
        portfolio_id = "main_portfolio"
        execution_priority = (
            execution_config.get("execution_priority", "BALANCE") if execution_config else "BALANCE"
        )
        time_in_force = execution_config.get("time_in_force", "DAY") if execution_config else "DAY"

        # Generate correlation ID for this rebalance operation
        correlation_id = f"rebalance_{portfolio_id}_{rebalance_plan.correlation_id or 'unknown'}"

        for item in rebalance_plan.items:
            # Skip if no trade needed or action is HOLD
            if item.action == "HOLD" or item.trade_amount == 0:
                continue

            # Determine order side and quantity based on trade amount
            if item.trade_amount > 0:
                side = "buy"
                quantity = item.trade_amount
            else:
                side = "sell"
                quantity = abs(item.trade_amount)

            # Create order request
            order_request = OrderRequestDTO(
                symbol=item.symbol,
                quantity=quantity,
                side=side,
                order_type="market",  # Default to market orders for rebalancing
                time_in_force=time_in_force,
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                execution_priority=execution_priority,
                created_at=rebalance_plan.timestamp,
            )
            order_requests.append(order_request)

    def _get_current_position_values(self) -> dict[str, Decimal]:
        """Get current position values using trading manager."""
        try:
            positions_data = self.trading_manager.get_positions()
            position_values = {}

            # DEBUG: Log what positions we got
            logger.info("DEBUG: _get_current_position_values called")
            logger.info(
                f"DEBUG: positions_data success: {positions_data.get('success') if positions_data else 'None'}"
            )
            logger.info(
                f"DEBUG: positions count: {len(positions_data.get('positions', [])) if positions_data else 0}"
            )

            if positions_data and positions_data.get("success"):
                positions = positions_data.get("positions", [])
                for position in positions:
                    symbol = position.get("symbol")
                    market_value = position.get("market_value", 0)
                    if symbol:
                        position_values[symbol] = Decimal(str(market_value))
                        logger.info(f"DEBUG: Position {symbol}: ${market_value}")

            logger.info(f"DEBUG: Total position values: {position_values}")
            return position_values
        except Exception:
            return {}

    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value using trading manager."""
        try:
            account_summary = self.trading_manager.get_account_summary()
            if account_summary:
                equity = account_summary.get("equity", 0)
                return Decimal(str(equity))
            return Decimal("0")
        except Exception:
            return Decimal("0")
