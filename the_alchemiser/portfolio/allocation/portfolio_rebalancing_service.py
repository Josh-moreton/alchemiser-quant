"""Business Unit: portfolio assessment & management; Status: current.

Portfolio rebalancing service - main application orchestrator.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.application.mapping.portfolio_rebalancing_mapping import (
    rebalance_plans_dict_to_collection_dto,
)
from the_alchemiser.shared.adapters import (
    portfolio_state_to_dto,
    rebalance_plan_to_order_requests,
)
from the_alchemiser.shared.dto import (
    OrderRequestDTO,
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    RebalancePlanDTO,
    StrategySignalDTO,
)
from ..holdings.position_analyzer import PositionAnalyzer
from ..holdings.position_delta import PositionDelta
from .rebalance_calculator import RebalanceCalculator
from .rebalance_plan import RebalancePlan
from ..state.attribution_engine import (
    StrategyAttributionEngine,
)
from the_alchemiser.portfolio.schemas.rebalancing import (
    RebalancePlanCollectionDTO,
    RebalancingImpactDTO,
    RebalancingSummaryDTO,
)
from the_alchemiser.shared.utils.error_handler import TradingSystemErrorHandler
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


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
        try:
            # Use internal domain method
            domain_plans = self._calculate_rebalancing_plan_domain(
                target_weights, current_positions, portfolio_value
            )

            # Convert to DTO
            return rebalance_plans_dict_to_collection_dto(domain_plans)
        except Exception as e:
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

    def _get_current_position_values(self) -> dict[str, Decimal]:
        """Get current position values from trading manager."""
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

    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value from trading manager.

        Returns:
            Decimal: The portfolio value

        Raises:
            ValueError: If portfolio_dto is None or portfolio_dto.value is not a valid Decimal

        """
        try:
            portfolio_dto = self.trading_manager.get_portfolio_value()

            # Defensive validation: ensure we got a valid PortfolioValueDTO
            if portfolio_dto is None:
                error_handler = TradingSystemErrorHandler()
                error = ValueError("Portfolio DTO is None - potential upstream schema drift")
                error_handler.handle_error(
                    error=error,
                    component="PortfolioRebalancingService._get_portfolio_value",
                    context="portfolio value retrieval",
                    additional_data={"portfolio_dto": None},
                )
                raise error

            # Defensive validation: ensure portfolio_dto.value is a valid Decimal
            if not isinstance(portfolio_dto.value, Decimal):
                error_handler = TradingSystemErrorHandler()
                error = ValueError(
                    f"Portfolio value is not a Decimal: {type(portfolio_dto.value)} - "
                    f"potential upstream schema drift"
                )
                error_handler.handle_error(
                    error=error,
                    component="PortfolioRebalancingService._get_portfolio_value",
                    context="portfolio value validation",
                    additional_data={
                        "portfolio_dto_type": str(type(portfolio_dto)),
                        "value_type": str(type(portfolio_dto.value)),
                        "value_repr": repr(portfolio_dto.value),
                    },
                )
                raise error

            return portfolio_dto.value

        except Exception as e:
            # Re-raise if already handled above, otherwise handle and re-raise
            if isinstance(e, ValueError) and "schema drift" in str(e):
                raise

            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
                error=e,
                component="PortfolioRebalancingService._get_portfolio_value",
                context="portfolio value retrieval - unexpected error",
                additional_data={"error_type": str(type(e))},
            )
            raise

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
                'total_value': portfolio_value,
                'portfolio_value': portfolio_value,
                'cash_value': account_summary.get('cash', Decimal('0')),
                'equity_value': account_summary.get('equity', Decimal('0')),
                'buying_power': account_summary.get('buying_power', Decimal('0')),
                'day_pnl': account_summary.get('unrealized_pl', Decimal('0')),
                'day_pnl_percent': account_summary.get('unrealized_plpc', Decimal('0')),
                'account_id': account_summary.get('account_number'),
            }
            
            return portfolio_state_to_dto(
                portfolio_data=portfolio_context,
                positions=positions_data.get('positions', []) if positions_data else [],
                correlation_id=correlation_id,
                portfolio_id="main_portfolio",
            )
            
        except Exception as e:
            # Return minimal portfolio state with error context
            from datetime import datetime, UTC
            import uuid
            
            correlation_id = correlation_id or f"portfolio_error_{uuid.uuid4().hex[:12]}"
            
            return PortfolioStateDTO(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                portfolio_id="main_portfolio",
                positions=[],
                metrics=PortfolioMetricsDTO(
                    total_value=Decimal('0'),
                    cash_value=Decimal('0'),
                    equity_value=Decimal('0'),
                    buying_power=Decimal('0'),
                    day_pnl=Decimal('0'),
                    day_pnl_percent=Decimal('0'),
                    total_pnl=Decimal('0'),
                    total_pnl_percent=Decimal('0'),
                ),
                metadata={'error': str(e)},
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
                if signal.action in ['BUY', 'SELL'] and signal.allocation_weight is not None:
                    # Use allocation weight if provided
                    weight = float(signal.allocation_weight)
                    if signal.action == 'SELL':
                        weight = 0  # Sell means reduce to zero
                    target_weights[signal.symbol] = Decimal(str(weight))
                    
                signal_context.append({
                    'symbol': signal.symbol,
                    'action': signal.action,
                    'confidence': float(signal.confidence),
                    'strategy': signal.strategy_name,
                    'reasoning': signal.reasoning,
                    'correlation_id': signal.correlation_id,
                })
            
            # Calculate rebalancing impact
            if target_weights:
                impact = self.estimate_rebalancing_impact(target_weights)
                needs_rebalancing = len(target_weights) > 0
            else:
                # No actionable signals
                impact = None
                needs_rebalancing = False
            
            return {
                'correlation_id': correlation_id,
                'signals_processed': len(signals),
                'actionable_signals': len(target_weights),
                'target_weights': {k: float(v) for k, v in target_weights.items()},
                'needs_rebalancing': needs_rebalancing,
                'estimated_impact': impact.model_dump() if impact else None,
                'signal_context': signal_context,
                'timestamp': signals[0].timestamp if signals else None,
            }
            
        except Exception as e:
            return {
                'correlation_id': correlation_id,
                'signals_processed': len(signals) if signals else 0,
                'actionable_signals': 0,
                'error': str(e),
                'needs_rebalancing': False,
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
            from datetime import datetime, UTC
            import uuid
            from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanItemDTO
            
            correlation_id = correlation_id or f"rebalance_{uuid.uuid4().hex[:12]}"
            causation_id = causation_id or correlation_id
            plan_id = f"plan_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Convert plans to DTO items
            items = []
            total_portfolio_value = self._get_portfolio_value()
            total_trade_value = Decimal('0')
            
            for symbol, plan in plan_collection.plans.items():
                if hasattr(plan, 'target_value') and hasattr(plan, 'current_value'):
                    trade_amount = plan.target_value - plan.current_value
                    
                    if abs(trade_amount) > self.min_trade_threshold:
                        action = "BUY" if trade_amount > 0 else "SELL"
                        
                        item = RebalancePlanItemDTO(
                            symbol=symbol,
                            current_weight=plan.current_value / total_portfolio_value if total_portfolio_value > 0 else Decimal('0'),
                            target_weight=plan.target_value / total_portfolio_value if total_portfolio_value > 0 else Decimal('0'),
                            weight_diff=(plan.target_value - plan.current_value) / total_portfolio_value if total_portfolio_value > 0 else Decimal('0'),
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
            
        except Exception as e:
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
        return rebalance_plan_to_order_requests(
            rebalance_plan=rebalance_plan,
            portfolio_id="main_portfolio",
            execution_priority=execution_config.get("execution_priority", "BALANCE") if execution_config else "BALANCE",
            time_in_force=execution_config.get("time_in_force", "DAY") if execution_config else "DAY",
        )
