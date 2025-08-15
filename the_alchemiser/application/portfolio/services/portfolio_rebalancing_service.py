"""Portfolio rebalancing service - main application orchestrator."""

from decimal import Decimal
from typing import Any

from the_alchemiser.domain.portfolio.position.position_analyzer import PositionAnalyzer
from the_alchemiser.domain.portfolio.position.position_delta import PositionDelta
from the_alchemiser.domain.portfolio.rebalancing.rebalance_calculator import RebalanceCalculator
from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan
from the_alchemiser.domain.portfolio.strategy_attribution.attribution_engine import (
    StrategyAttributionEngine,
)
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


class PortfolioRebalancingService:
    """
    Main application service for portfolio rebalancing operations.

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
    ):
        """
        Initialize the portfolio rebalancing service.

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

    def calculate_rebalancing_plan(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, RebalancePlan]:
        """
        Calculate a complete rebalancing plan for the portfolio.

        Args:
            target_weights: Target allocation weights by symbol
            current_positions: Current position values (fetched if None)
            portfolio_value: Total portfolio value (calculated if None)

        Returns:
            Dictionary mapping symbols to their rebalance plans
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

    def analyze_position_deltas(
        self,
        target_weights: dict[str, Decimal],
        current_positions: dict[str, Decimal] | None = None,
        portfolio_value: Decimal | None = None,
    ) -> dict[str, PositionDelta]:
        """
        Analyze position deltas between current and target allocations.

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

    def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """
        Get a comprehensive summary of rebalancing requirements.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            Summary containing plans, deltas, and analysis
        """
        current_positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()

        # Calculate rebalancing plan
        rebalance_plan = self.calculate_rebalancing_plan(
            target_weights, current_positions, portfolio_value
        )

        # Calculate position deltas
        position_deltas = self.analyze_position_deltas(
            target_weights, current_positions, portfolio_value
        )

        # Get symbols needing rebalancing
        symbols_needing_rebalance = self.rebalance_calculator.get_symbols_needing_rebalance(
            rebalance_plan
        )
        sell_plans = self.rebalance_calculator.get_sell_plans(rebalance_plan)
        buy_plans = self.rebalance_calculator.get_buy_plans(rebalance_plan)

        # Calculate totals
        total_trade_value = self.rebalance_calculator.calculate_total_trade_value(rebalance_plan)
        total_sells, total_buys = self.position_analyzer.calculate_total_adjustments_needed(
            position_deltas
        )
        portfolio_turnover = self.position_analyzer.calculate_portfolio_turnover(
            position_deltas, portfolio_value
        )

        # Get strategy attribution
        strategy_exposures = self.attribution_engine.get_strategy_exposures(
            current_positions, portfolio_value
        )

        return {
            "rebalance_plan": rebalance_plan,
            "position_deltas": position_deltas,
            "symbols_needing_rebalance": symbols_needing_rebalance,
            "sell_plans": sell_plans,
            "buy_plans": buy_plans,
            "total_trade_value": total_trade_value,
            "total_sells": total_sells,
            "total_buys": total_buys,
            "portfolio_turnover": portfolio_turnover,
            "strategy_exposures": strategy_exposures,
            "portfolio_value": portfolio_value,
        }

    def get_symbols_requiring_sells(self, target_weights: dict[str, Decimal]) -> list[str]:
        """
        Get list of symbols that need to be sold for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring sell orders
        """
        rebalance_plan = self.calculate_rebalancing_plan(target_weights)
        sell_plans = self.rebalance_calculator.get_sell_plans(rebalance_plan)
        return list(sell_plans.keys())

    def get_symbols_requiring_buys(self, target_weights: dict[str, Decimal]) -> list[str]:
        """
        Get list of symbols that need to be bought for rebalancing.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            List of symbols requiring buy orders
        """
        rebalance_plan = self.calculate_rebalancing_plan(target_weights)
        buy_plans = self.rebalance_calculator.get_buy_plans(rebalance_plan)
        return list(buy_plans.keys())

    def estimate_rebalancing_impact(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """
        Estimate the impact of rebalancing on the portfolio.

        Args:
            target_weights: Target allocation weights by symbol

        Returns:
            Impact analysis including turnover, trade counts, and strategy shifts
        """
        current_positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()

        # Calculate position deltas
        position_deltas = self.analyze_position_deltas(
            target_weights, current_positions, portfolio_value
        )

        # Calculate current and target strategy exposures
        current_strategy_exposures = self.attribution_engine.get_strategy_exposures(
            current_positions, portfolio_value
        )

        target_positions = {
            symbol: portfolio_value * weight for symbol, weight in target_weights.items()
        }
        target_strategy_exposures = self.attribution_engine.get_strategy_exposures(
            target_positions, portfolio_value
        )

        # Calculate turnover and trade metrics
        portfolio_turnover = self.position_analyzer.calculate_portfolio_turnover(
            position_deltas, portfolio_value
        )
        positions_to_sell = self.position_analyzer.get_positions_to_sell(position_deltas)
        positions_to_buy = self.position_analyzer.get_positions_to_buy(position_deltas)

        return {
            "portfolio_turnover": portfolio_turnover,
            "num_sells_required": len(positions_to_sell),
            "num_buys_required": len(positions_to_buy),
            "current_strategy_exposures": current_strategy_exposures,
            "target_strategy_exposures": target_strategy_exposures,
            "strategy_allocation_changes": self._calculate_strategy_changes(
                current_strategy_exposures, target_strategy_exposures
            ),
        }

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
        """Get total portfolio value from trading manager."""
        raw = self.trading_manager.get_portfolio_value()
        # Support typed path returning {"value": float, "money": Money}
        if isinstance(raw, dict) and "value" in raw:
            raw_value = raw.get("value", 0)
        else:
            raw_value = raw
        try:
            return Decimal(str(raw_value))
        except Exception:
            return Decimal("0")

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
