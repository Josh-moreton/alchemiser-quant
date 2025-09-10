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
        """Calculate rebalancing plan as domain objects.

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
        logger.info(
            f"RECEIVED_TARGET_WEIGHTS_COUNT: {len(target_weights) if target_weights else 0}"
        )
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
                logger.info(
                    f"FETCHED_POSITIONS_COUNT: {len(current_positions) if current_positions else 0}"
                )

            if portfolio_value is None:
                logger.info("Fetching portfolio value...")
                portfolio_value = self._get_portfolio_value()
                logger.info(f"FETCHED_PORTFOLIO_VALUE: {portfolio_value}")

            # === CRITICAL DATA VALIDATION ===
            logger.info("=== CRITICAL DATA VALIDATION ===")

            # Validate portfolio value
            if portfolio_value <= 0:
                error_msg = (
                    f"CRITICAL: Portfolio value is ${portfolio_value} - cannot calculate trades"
                )
                logger.error(f"❌ {error_msg}")
                logger.error("🚨 This is the ROOT CAUSE of the 'no trades generated' issue!")
                logger.error("🚨 ANALYSIS:")
                logger.error("  - API calls to get portfolio value are failing (network/auth issues)")
                logger.error("  - Account may be new with zero equity")
                logger.error("  - Trading mode (paper vs live) may be incorrect")
                logger.error("🚨 POTENTIAL_SOLUTIONS:")
                logger.error("  1. Verify account has funds and positions")
                logger.error("  2. Check API credentials and permissions")
                logger.error("  3. Ensure correct trading environment (paper vs live)")
                logger.error("  4. Check if account is restricted or blocked")
                logger.error("  5. For new accounts, deposit funds before trading")
                logger.error("  6. For testing, use paper trading with simulated funds")

                # Enhanced debugging for portfolio value failure
                logger.error("=== PORTFOLIO VALUE FAILURE DEBUGGING ===")
                logger.error(f"TRADING_MANAGER_TYPE: {type(self.trading_manager)}")
                try:
                    # Test portfolio DTO again for detailed error info
                    test_dto = self.trading_manager.get_portfolio_value()
                    logger.error(f"TEST_PORTFOLIO_DTO: {test_dto}")
                    if test_dto and hasattr(test_dto, 'value'):
                        logger.error(f"TEST_DTO_VALUE: {test_dto.value} (type: {type(test_dto.value)})")
                except Exception as test_e:
                    logger.error(f"TEST_DTO_EXCEPTION: {test_e}")
                    
                try:
                    # Test account summary for detailed error info
                    test_summary = self.trading_manager.get_account_summary()
                    logger.error(f"TEST_ACCOUNT_SUMMARY: {test_summary}")
                    if test_summary:
                        portfolio_val = test_summary.get("portfolio_value")
                        equity_val = test_summary.get("equity")
                        logger.error(f"TEST_SUMMARY_PORTFOLIO_VALUE: {portfolio_val}")
                        logger.error(f"TEST_SUMMARY_EQUITY: {equity_val}")
                except Exception as test_e:
                    logger.error(f"TEST_SUMMARY_EXCEPTION: {test_e}")

                # === PAPER TRADING ZERO VALUE RECOVERY ===
                # Attempt to recover for paper trading scenarios
                logger.warning("=== ATTEMPTING PAPER TRADING RECOVERY ===")
                paper_trading_detected = False
                
                # Check if trading manager indicates paper trading
                if hasattr(self.trading_manager, 'is_paper_trading'):
                    is_paper = getattr(self.trading_manager, 'is_paper_trading', False)
                    if is_paper:
                        paper_trading_detected = True
                        logger.warning("✅ PAPER_TRADING_DETECTED_VIA_MANAGER")
                
                # Check if we can access the alpaca manager through trading manager
                if hasattr(self.trading_manager, 'alpaca_manager') or hasattr(self.trading_manager, '_alpaca_manager'):
                    alpaca_mgr = getattr(self.trading_manager, 'alpaca_manager', None) or getattr(self.trading_manager, '_alpaca_manager', None)
                    if alpaca_mgr and hasattr(alpaca_mgr, 'is_paper_trading'):
                        is_paper = getattr(alpaca_mgr, 'is_paper_trading', False)
                        if is_paper:
                            paper_trading_detected = True
                            logger.warning("✅ PAPER_TRADING_DETECTED_VIA_ALPACA_MANAGER")
                
                # Check endpoint for paper trading indicators
                try:
                    from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
                    _, _, endpoint = get_alpaca_keys()
                    if endpoint and "paper" in endpoint.lower():
                        paper_trading_detected = True
                        logger.warning("✅ PAPER_TRADING_DETECTED_VIA_ENDPOINT")
                        logger.warning(f"PAPER_ENDPOINT: {endpoint}")
                except Exception as endpoint_e:
                    logger.error(f"ENDPOINT_CHECK_FAILED: {endpoint_e}")
                
                # Check if account ID contains paper indicators
                try:
                    test_summary = self.trading_manager.get_account_summary()
                    if test_summary:
                        account_id = test_summary.get("account_id", "")
                        if "paper" in str(account_id).lower():
                            paper_trading_detected = True
                            logger.warning("✅ PAPER_TRADING_DETECTED_VIA_ACCOUNT_ID")
                except Exception:
                    pass
                
                if paper_trading_detected:
                    logger.warning("🚨 PAPER TRADING MODE: Applying default portfolio value for testing")
                    default_portfolio_value = Decimal("100000.00")  # $100k default for paper trading
                    logger.warning(f"🚨 USING_DEFAULT_PORTFOLIO_VALUE: ${default_portfolio_value}")
                    logger.warning("🚨 This enables strategy testing with empty paper accounts")
                    
                    # Update portfolio_value for the calculation
                    portfolio_value = default_portfolio_value
                    logger.warning(f"🚨 RECOVERY_SUCCESSFUL: Proceeding with portfolio_value=${portfolio_value}")
                else:
                    logger.error("❌ NOT_PAPER_TRADING: Cannot use default portfolio value for live trading")
                    return RebalancePlanCollectionDTO(
                        success=False,
                        plans={},
                        total_symbols=0,
                        symbols_needing_rebalance=0,
                        total_trade_value=Decimal("0"),
                        error=f"Invalid portfolio value: ${portfolio_value}. {error_msg}",
                    )

            # Validate target weights
            total_target_weight = sum(target_weights.values())
            logger.info(
                f"TOTAL_TARGET_WEIGHT: {total_target_weight} ({total_target_weight * 100:.1f}%)"
            )

            if total_target_weight <= 0:
                error_msg = "Target weights sum to zero or negative"
                logger.error(f"❌ {error_msg}")
                return RebalancePlanCollectionDTO(
                    success=False,
                    plans={},
                    total_symbols=0,
                    symbols_needing_rebalance=0,
                    total_trade_value=Decimal("0"),
                    error=error_msg,
                )

            # Warn if target weights don't sum to 1.0 (100%)
            if abs(total_target_weight - Decimal("1.0")) > Decimal("0.01"):  # Allow 1% tolerance
                logger.warning(
                    f"⚠️ TARGET_WEIGHTS_SUM_UNUSUAL: {total_target_weight:.3f} (expected ~1.0)"
                )

            # Log current position values summary
            current_total_value = (
                sum(current_positions.values()) if current_positions else Decimal("0")
            )
            logger.info(f"CURRENT_POSITIONS_TOTAL_VALUE: ${current_total_value}")

            if current_total_value > portfolio_value * Decimal("1.1"):  # 10% tolerance
                logger.warning(
                    f"⚠️ POSITION_VALUES_EXCEED_PORTFOLIO: ${current_total_value} > ${portfolio_value}"
                )
                logger.warning("⚠️ This might indicate stale data or calculation errors")

            logger.info("✅ DATA VALIDATION PASSED")

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
            logger.info("PASSING_TO_CALCULATOR:")
            logger.info(f"  target_weights: {len(target_weights)} symbols")
            logger.info(
                f"  current_positions: {len(current_positions) if current_positions else 0} positions"
            )
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
            logger.info(
                f"DTO_SUCCESS: {dto_result.success if hasattr(dto_result, 'success') else 'unknown'}"
            )
            logger.info(
                f"DTO_PLANS_COUNT: {len(dto_result.plans) if hasattr(dto_result, 'plans') else 'unknown'}"
            )
            logger.info(
                f"DTO_SYMBOLS_NEEDING_REBALANCE: {dto_result.symbols_needing_rebalance if hasattr(dto_result, 'symbols_needing_rebalance') else 'unknown'}"
            )

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
            _ = self._get_current_position_values()  # Fetch for side effects
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
            # === ENHANCED POSITION VALUES FETCHING ===
            logger.info("=== FETCHING CURRENT POSITION VALUES ===")
            logger.info(f"TRADING_MANAGER_TYPE: {type(self.trading_manager).__name__}")

            positions_data = self.trading_manager.get_positions()
            position_values = {}

            # DEBUG: Log what positions we got
            logger.info("=== POSITIONS DATA ANALYSIS ===")
            logger.info(f"POSITIONS_DATA_TYPE: {type(positions_data)}")
            logger.info(
                f"POSITIONS_DATA_SUCCESS: {positions_data.get('success') if positions_data else 'None'}"
            )
            logger.info(
                f"POSITIONS_DATA_COUNT: {len(positions_data.get('positions', [])) if positions_data else 0}"
            )
            logger.info(f"POSITIONS_DATA_CONTENT: {positions_data}")

            if positions_data and positions_data.get("success"):
                positions = positions_data.get("positions", [])
                logger.info(f"PROCESSING {len(positions)} POSITIONS")

                for i, position in enumerate(positions):
                    logger.info(f"=== POSITION {i + 1} ===")
                    logger.info(f"POSITION_RAW_DATA: {position}")

                    symbol = position.get("symbol")
                    market_value = position.get("market_value", 0)
                    qty = position.get("qty", 0)

                    logger.info(f"POSITION_SYMBOL: {symbol}")
                    logger.info(
                        f"POSITION_MARKET_VALUE: {market_value} (type: {type(market_value)})"
                    )
                    logger.info(f"POSITION_QTY: {qty}")

                    if symbol:
                        try:
                            decimal_value = Decimal(str(market_value))
                            position_values[symbol] = decimal_value
                            logger.info(f"CONVERTED_POSITION: {symbol} = ${decimal_value}")
                        except Exception as e:
                            logger.error(
                                f"❌ FAILED_TO_CONVERT_MARKET_VALUE: {symbol} = {market_value} - {e}"
                            )
                    else:
                        logger.warning(f"⚠️ MISSING_SYMBOL_IN_POSITION: {position}")
            else:
                logger.error("❌ POSITIONS_DATA_FAILED_OR_EMPTY")
                logger.error("🚨 ANALYSIS: This could mean:")
                logger.error("  1. API call to get_positions() failed (network/auth issue)")
                logger.error("  2. Account has no positions (new/empty account)")
                logger.error("  3. API returned success=False")
                logger.error("🚨 DECISION: Proceeding with empty positions - rebalancing will create new positions")

            logger.info("=== FINAL POSITION VALUES ===")
            logger.info(f"TOTAL_POSITIONS_FETCHED: {len(position_values)}")
            if position_values:
                total_value = sum(position_values.values())
                logger.info(f"TOTAL_POSITION_VALUE: ${total_value}")
                for symbol, value in position_values.items():
                    logger.info(f"FINAL_POSITION: {symbol} = ${value}")
            else:
                logger.warning("❌ NO_POSITION_VALUES_EXTRACTED")
                logger.warning("🚨 PROCEEDING WITH EMPTY POSITIONS: All target allocations will be BUY orders")

            return position_values
        except Exception as e:
            logger.error(f"❌ EXCEPTION_IN_GET_CURRENT_POSITION_VALUES: {e}")
            logger.exception("Full exception details:")
            return {}

    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value using trading manager.

        Uses the same method as PortfolioUtilities for consistency.
        """
        try:
            # === ENHANCED PORTFOLIO VALUE FETCHING ===
            logger.info("=== FETCHING PORTFOLIO VALUE ===")
            logger.info(f"TRADING_MANAGER_TYPE: {type(self.trading_manager).__name__}")

            portfolio_dto = self.trading_manager.get_portfolio_value()
            logger.info(f"PORTFOLIO_DTO_TYPE: {type(portfolio_dto)}")
            logger.info(f"PORTFOLIO_DTO_CONTENT: {portfolio_dto}")
            logger.info(
                f"PORTFOLIO_DTO_HAS_VALUE: {hasattr(portfolio_dto, 'value') if portfolio_dto else 'None'}"
            )

            if portfolio_dto and hasattr(portfolio_dto, "value"):
                portfolio_value = portfolio_dto.value
                logger.info(
                    f"PORTFOLIO_VALUE_FROM_DTO: ${portfolio_value} (type: {type(portfolio_value)})"
                )

                # === CRITICAL DATA VALIDATION ===
                if portfolio_value <= 0:
                    logger.error(f"❌ INVALID_PORTFOLIO_VALUE_FROM_DTO: ${portfolio_value}")
                    logger.error(
                        "🚨 This will cause ALL trades to be skipped! Attempting fallback..."
                    )
                    # Continue to fallback method
                else:
                    logger.info(f"✅ VALID_PORTFOLIO_VALUE: ${portfolio_value}")
                    return portfolio_value
            else:
                logger.warning("❌ PORTFOLIO_DTO_MISSING_VALUE_ATTRIBUTE")

            # Fallback method
            logger.info("=== TRYING FALLBACK METHOD ===")
            account_summary = self.trading_manager.get_account_summary()
            logger.info(f"ACCOUNT_SUMMARY_TYPE: {type(account_summary)}")
            logger.info(f"ACCOUNT_SUMMARY_CONTENT: {account_summary}")

            if account_summary:
                # Try portfolio_value first, then equity as fallback (aligned with CLI display logic)
                portfolio_value_raw = account_summary.get("portfolio_value")
                equity_raw = account_summary.get("equity")

                logger.info(f"ACCOUNT_PORTFOLIO_VALUE: {portfolio_value_raw}")
                logger.info(f"ACCOUNT_EQUITY: {equity_raw}")

                final_value = portfolio_value_raw if portfolio_value_raw is not None else equity_raw
                if final_value is not None:
                    portfolio_value = Decimal(str(final_value))
                    logger.info(f"PORTFOLIO_VALUE_FROM_ACCOUNT_SUMMARY: ${portfolio_value}")

                    # === CRITICAL DATA VALIDATION ===
                    if portfolio_value <= 0:
                        logger.error(f"❌ INVALID_PORTFOLIO_VALUE_FROM_ACCOUNT: ${portfolio_value}")
                        logger.error("🚨 This will cause ALL trades to be skipped!")
                        logger.error("🚨 POTENTIAL_FIXES:")
                        logger.error("  1. Check if account has sufficient funds")
                        logger.error("  2. Verify API credentials and permissions")
                        logger.error(
                            "  3. Check if account is in correct trading mode (paper vs live)"
                        )
                        logger.error(
                            "🚨 Returning actual invalid portfolio value for proper error handling"
                        )
                        return portfolio_value
                    logger.info(f"✅ VALID_PORTFOLIO_VALUE_FROM_ACCOUNT: ${portfolio_value}")
                    return portfolio_value
                logger.error("❌ BOTH_PORTFOLIO_VALUE_AND_EQUITY_ARE_NONE")
            else:
                logger.error("❌ ACCOUNT_SUMMARY_IS_NONE")

            logger.error("❌ ALL_PORTFOLIO_VALUE_METHODS_FAILED")
            logger.error("🚨 CRITICAL: Cannot proceed with rebalancing without portfolio value")
            logger.error("🚨 This explains why no trades are being generated!")
            
            # === PAPER TRADING FALLBACK ===
            # For paper trading accounts, provide a default portfolio value to enable testing
            paper_trading_detected = False
            
            # Check multiple ways to detect paper trading
            if hasattr(self.trading_manager, 'is_paper_trading') and getattr(self.trading_manager, 'is_paper_trading', False):
                paper_trading_detected = True
                logger.warning("✅ PAPER_TRADING_DETECTED_VIA_MANAGER")
            
            # Check alpaca manager
            if not paper_trading_detected:
                if hasattr(self.trading_manager, 'alpaca_manager') or hasattr(self.trading_manager, '_alpaca_manager'):
                    alpaca_mgr = getattr(self.trading_manager, 'alpaca_manager', None) or getattr(self.trading_manager, '_alpaca_manager', None)
                    if alpaca_mgr and hasattr(alpaca_mgr, 'is_paper_trading'):
                        is_paper = getattr(alpaca_mgr, 'is_paper_trading', False)
                        if is_paper:
                            paper_trading_detected = True
                            logger.warning("✅ PAPER_TRADING_DETECTED_VIA_ALPACA_MANAGER")
            
            # Check endpoint
            if not paper_trading_detected:
                try:
                    from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
                    _, _, endpoint = get_alpaca_keys()
                    if endpoint and "paper" in endpoint.lower():
                        paper_trading_detected = True
                        logger.warning(f"✅ PAPER_TRADING_DETECTED_VIA_ENDPOINT: {endpoint}")
                except Exception:
                    pass
            
            if paper_trading_detected:
                logger.warning("=== PAPER TRADING FALLBACK ACTIVATED ===")
                logger.warning("🚨 Account has zero equity but this is paper trading mode")
                logger.warning("🚨 Using default portfolio value for testing purposes")
                default_value = Decimal("100000.00")  # $100k default for paper trading
                logger.warning(f"🚨 FALLBACK_PORTFOLIO_VALUE: ${default_value}")
                logger.warning("🚨 This allows strategy testing even with empty paper account")
                return default_value
            
            logger.error("🚨 Returning zero portfolio value for proper error handling")
            return Decimal("0")

        except Exception as e:
            # Fallback to account summary method if DTO method fails
            logger.error(f"❌ EXCEPTION_IN_GET_PORTFOLIO_VALUE: {e}")
            logger.exception("Full exception details:")
            try:
                logger.info("=== TRYING EMERGENCY FALLBACK ===")
                account_summary = self.trading_manager.get_account_summary()
                if account_summary:
                    # Try portfolio_value first, then equity as fallback (aligned with CLI display logic)
                    portfolio_value = account_summary.get(
                        "portfolio_value", account_summary.get("equity", 0)
                    )
                    result = Decimal(str(portfolio_value))
                    logger.info(f"EMERGENCY_FALLBACK_VALUE: ${result}")

                    if result <= 0:
                        logger.error("❌ EMERGENCY_FALLBACK_ALSO_RETURNED_ZERO")
                        
                        # === PAPER TRADING EMERGENCY FALLBACK ===
                        if hasattr(self.trading_manager, 'is_paper_trading') and getattr(self.trading_manager, 'is_paper_trading', False):
                            logger.warning("=== EMERGENCY PAPER TRADING FALLBACK ===")
                            default_value = Decimal("100000.00")
                            logger.warning(f"🚨 EMERGENCY_PAPER_FALLBACK: ${default_value}")
                            return default_value
                        
                        logger.error(
                            "🚨 Returning actual invalid portfolio value for proper error handling"
                        )
                        return result

                    return result
                logger.error("❌ EMERGENCY_FALLBACK_FAILED")
                return Decimal("0")
            except Exception as fallback_e:
                logger.error(f"❌ EMERGENCY_FALLBACK_EXCEPTION: {fallback_e}")
                return Decimal("0")
