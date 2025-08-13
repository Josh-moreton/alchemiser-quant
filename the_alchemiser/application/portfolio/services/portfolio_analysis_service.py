"""Portfolio analysis service - provides comprehensive portfolio analysis."""

from decimal import Decimal
from typing import Any

from the_alchemiser.domain.portfolio.analysis.position_analyzer import PositionAnalyzer
from the_alchemiser.domain.portfolio.attribution.strategy_attribution_engine import StrategyAttributionEngine
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class PortfolioAnalysisService:
    """
    Service for comprehensive portfolio analysis and reporting.
    
    Provides detailed analysis of portfolio composition, performance,
    and strategic allocation across different investment strategies.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        position_analyzer: PositionAnalyzer | None = None,
        attribution_engine: StrategyAttributionEngine | None = None
    ):
        """
        Initialize the portfolio analysis service.
        
        Args:
            trading_manager: Service for trading operations and market data
            position_analyzer: Analyzer for position analysis (optional)
            attribution_engine: Engine for strategy attribution (optional)
        """
        self.trading_manager = trading_manager
        self.position_analyzer = position_analyzer or PositionAnalyzer()
        self.attribution_engine = attribution_engine or StrategyAttributionEngine()

    def get_comprehensive_portfolio_analysis(self) -> dict[str, Any]:
        """
        Get comprehensive analysis of the current portfolio.
        
        Returns:
            Complete portfolio analysis including composition, strategy allocation,
            and performance metrics
        """
        # Get current portfolio data
        positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()
        
        if portfolio_value == 0:
            return self._get_empty_portfolio_analysis()

        # Calculate strategy exposures
        strategy_exposures = self.attribution_engine.get_strategy_exposures(positions, portfolio_value)
        strategy_allocations = self.attribution_engine.calculate_strategy_allocations(positions, portfolio_value)

        # Get position analysis
        largest_positions = self._get_largest_positions(positions, portfolio_value)
        concentration_metrics = self._calculate_concentration_metrics(positions, portfolio_value)

        # Get account information
        account_info = self._get_account_information()

        return {
            "portfolio_summary": {
                "total_value": portfolio_value,
                "num_positions": len(positions),
                "cash_balance": account_info.get("cash", Decimal("0")),
                "buying_power": account_info.get("buying_power", Decimal("0"))
            },
            "strategy_analysis": {
                "strategy_exposures": strategy_exposures,
                "strategy_allocations": strategy_allocations,
                "strategy_summary": self._create_strategy_summary(strategy_exposures)
            },
            "position_analysis": {
                "largest_positions": largest_positions,
                "concentration_metrics": concentration_metrics,
                "position_details": self._get_position_details(positions, portfolio_value)
            },
            "risk_metrics": {
                "concentration_risk": concentration_metrics.get("top_10_concentration", Decimal("0")),
                "strategy_diversification": len(strategy_exposures),
                "position_count": len(positions)
            }
        }

    def analyze_portfolio_drift(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """
        Analyze how far the current portfolio has drifted from target allocations.
        
        Args:
            target_weights: Target allocation weights by symbol
            
        Returns:
            Drift analysis showing deviations from target
        """
        current_positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()

        if portfolio_value == 0:
            return {"error": "Portfolio value is zero"}

        # Calculate current weights
        current_weights = {
            symbol: value / portfolio_value
            for symbol, value in current_positions.items()
        }

        # Calculate drift for each symbol
        drift_analysis = {}
        total_absolute_drift = Decimal("0")

        for symbol in set(current_weights.keys()) | set(target_weights.keys()):
            current_weight = current_weights.get(symbol, Decimal("0"))
            target_weight = target_weights.get(symbol, Decimal("0"))
            drift = current_weight - target_weight
            
            drift_analysis[symbol] = {
                "current_weight": current_weight,
                "target_weight": target_weight,
                "drift": drift,
                "drift_percentage": drift * 100,
                "requires_rebalancing": abs(drift) > Decimal("0.01")  # 1% threshold
            }
            
            total_absolute_drift += abs(drift)

        # Calculate overall drift metrics
        return {
            "symbol_drift": drift_analysis,
            "overall_metrics": {
                "total_absolute_drift": total_absolute_drift,
                "average_drift": total_absolute_drift / len(drift_analysis) if drift_analysis else Decimal("0"),
                "symbols_needing_rebalance": sum(
                    1 for analysis in drift_analysis.values()
                    if analysis["requires_rebalancing"]
                ),
                "drift_severity": self._categorize_drift_severity(total_absolute_drift)
            }
        }

    def get_strategy_performance_analysis(self) -> dict[str, Any]:
        """
        Analyze performance by investment strategy.
        
        Returns:
            Performance analysis broken down by strategy
        """
        positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()

        if portfolio_value == 0:
            return {"error": "Portfolio value is zero"}

        # Group positions by strategy
        strategy_groups = self.attribution_engine.group_positions_by_strategy(positions)
        strategy_analysis = {}

        for strategy, strategy_positions in strategy_groups.items():
            strategy_value = sum(strategy_positions.values())
            strategy_allocation = strategy_value / portfolio_value
            
            strategy_analysis[strategy] = {
                "total_value": strategy_value,
                "allocation_percentage": strategy_allocation,
                "position_count": len(strategy_positions),
                "positions": strategy_positions,
                "average_position_size": strategy_value / len(strategy_positions) if strategy_positions else Decimal("0"),
                "strategy_description": self.attribution_engine.classifier.get_strategy_description(strategy)
            }

        return {
            "strategy_breakdown": strategy_analysis,
            "summary": {
                "total_strategies": len(strategy_analysis),
                "most_allocated_strategy": max(
                    strategy_analysis.items(),
                    key=lambda x: x[1]["allocation_percentage"]
                )[0] if strategy_analysis else None,
                "least_allocated_strategy": min(
                    strategy_analysis.items(),
                    key=lambda x: x[1]["allocation_percentage"]
                )[0] if strategy_analysis else None
            }
        }

    def compare_target_vs_current_strategy_allocation(
        self,
        target_weights: dict[str, Decimal]
    ) -> dict[str, Any]:
        """
        Compare current vs target strategy allocations.
        
        Args:
            target_weights: Target allocation weights by symbol
            
        Returns:
            Comparison of current vs target strategy allocations
        """
        current_positions = self._get_current_position_values()
        portfolio_value = self._get_portfolio_value()

        # Calculate current strategy allocations
        current_strategy_allocations = self.attribution_engine.calculate_strategy_allocations(
            current_positions, portfolio_value
        )

        # Calculate target strategy allocations
        target_positions = {
            symbol: portfolio_value * weight
            for symbol, weight in target_weights.items()
        }
        target_strategy_allocations = self.attribution_engine.calculate_strategy_allocations(
            target_positions, portfolio_value
        )

        # Compare allocations
        comparison = {}
        all_strategies = set(current_strategy_allocations.keys()) | set(target_strategy_allocations.keys())

        for strategy in all_strategies:
            current_allocation = current_strategy_allocations.get(strategy, Decimal("0"))
            target_allocation = target_strategy_allocations.get(strategy, Decimal("0"))
            difference = current_allocation - target_allocation

            comparison[strategy] = {
                "current_allocation": current_allocation,
                "target_allocation": target_allocation,
                "difference": difference,
                "difference_percentage": difference * 100,
                "needs_adjustment": abs(difference) > Decimal("0.01")
            }

        return {
            "strategy_comparison": comparison,
            "summary": {
                "strategies_needing_adjustment": sum(
                    1 for comp in comparison.values()
                    if comp["needs_adjustment"]
                ),
                "total_strategy_drift": sum(
                    abs(comp["difference"]) for comp in comparison.values()
                )
            }
        }

    def _get_current_position_values(self) -> dict[str, Decimal]:
        """Get current position values from trading manager."""
        positions = self.trading_manager.get_all_positions()
        return {
            pos.symbol: Decimal(str(pos.market_value))
            for pos in positions
            if pos.market_value > 0
        }

    def _get_portfolio_value(self) -> Decimal:
        """Get total portfolio value from trading manager."""
        portfolio_value = self.trading_manager.get_portfolio_value()
        return Decimal(str(portfolio_value))

    def _get_account_information(self) -> dict[str, Any]:
        """Get account information from trading manager."""
        try:
            account = self.trading_manager.get_account()
            return {
                "cash": Decimal(str(account.cash)),
                "buying_power": Decimal(str(account.buying_power)),
                "equity": Decimal(str(account.equity))
            }
        except Exception:
            return {"cash": Decimal("0"), "buying_power": Decimal("0"), "equity": Decimal("0")}

    def _get_largest_positions(self, positions: dict[str, Decimal], portfolio_value: Decimal) -> list[dict[str, Any]]:
        """Get the largest positions by value."""
        sorted_positions = sorted(
            positions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "symbol": symbol,
                "value": value,
                "weight": value / portfolio_value,
                "percentage": (value / portfolio_value) * 100
            }
            for symbol, value in sorted_positions[:10]  # Top 10 positions
        ]

    def _calculate_concentration_metrics(self, positions: dict[str, Decimal], portfolio_value: Decimal) -> dict[str, Any]:
        """Calculate portfolio concentration metrics."""
        if portfolio_value == 0:
            return {}

        sorted_positions = sorted(positions.values(), reverse=True)
        
        # Calculate concentration metrics
        top_1 = sorted_positions[0] / portfolio_value if len(sorted_positions) >= 1 else Decimal("0")
        top_5 = sum(sorted_positions[:5]) / portfolio_value if len(sorted_positions) >= 5 else sum(sorted_positions) / portfolio_value
        top_10 = sum(sorted_positions[:10]) / portfolio_value if len(sorted_positions) >= 10 else sum(sorted_positions) / portfolio_value

        return {
            "top_1_concentration": top_1,
            "top_5_concentration": top_5,
            "top_10_concentration": top_10,
            "herfindahl_index": sum((value / portfolio_value) ** 2 for value in positions.values())
        }

    def _get_position_details(self, positions: dict[str, Decimal], portfolio_value: Decimal) -> list[dict[str, Any]]:
        """Get detailed information for all positions."""
        return [
            {
                "symbol": symbol,
                "value": value,
                "weight": value / portfolio_value,
                "strategy": self.attribution_engine.classify_symbol(symbol)
            }
            for symbol, value in positions.items()
        ]

    def _create_strategy_summary(self, strategy_exposures: dict[str, Any]) -> dict[str, Any]:
        """Create a summary of strategy exposures."""
        if not strategy_exposures:
            return {}

        total_strategies = len(strategy_exposures)
        largest_strategy = max(
            strategy_exposures.items(),
            key=lambda x: x[1]["allocation_percentage"]
        )
        
        return {
            "total_strategies": total_strategies,
            "largest_strategy": {
                "name": largest_strategy[0],
                "allocation": largest_strategy[1]["allocation_percentage"]
            }
        }

    def _categorize_drift_severity(self, total_drift: Decimal) -> str:
        """Categorize the severity of portfolio drift."""
        if total_drift < Decimal("0.05"):
            return "low"
        elif total_drift < Decimal("0.15"):
            return "moderate"
        elif total_drift < Decimal("0.30"):
            return "high"
        else:
            return "severe"

    def _get_empty_portfolio_analysis(self) -> dict[str, Any]:
        """Return analysis structure for empty portfolio."""
        return {
            "portfolio_summary": {
                "total_value": Decimal("0"),
                "num_positions": 0,
                "cash_balance": Decimal("0"),
                "buying_power": Decimal("0")
            },
            "strategy_analysis": {
                "strategy_exposures": {},
                "strategy_allocations": {},
                "strategy_summary": {}
            },
            "position_analysis": {
                "largest_positions": [],
                "concentration_metrics": {},
                "position_details": []
            },
            "risk_metrics": {
                "concentration_risk": Decimal("0"),
                "strategy_diversification": 0,
                "position_count": 0
            }
        }
