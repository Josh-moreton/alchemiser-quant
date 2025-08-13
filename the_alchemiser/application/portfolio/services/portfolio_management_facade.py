"""Portfolio management facade - unified interface for all portfolio operations."""

from decimal import Decimal
from typing import Any

from the_alchemiser.application.portfolio.services.portfolio_analysis_service import PortfolioAnalysisService
from the_alchemiser.application.portfolio.services.portfolio_rebalancing_service import PortfolioRebalancingService
from the_alchemiser.application.portfolio.services.rebalance_execution_service import RebalanceExecutionService
from the_alchemiser.domain.portfolio.analysis.position_analyzer import PositionAnalyzer
from the_alchemiser.domain.portfolio.attribution.strategy_attribution_engine import StrategyAttributionEngine
from the_alchemiser.domain.portfolio.rebalancing.rebalance_calculator import RebalanceCalculator
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class PortfolioManagementFacade:
    """
    Unified facade for all portfolio management operations.
    
    Provides a single entry point for portfolio rebalancing, analysis,
    and execution while maintaining clean separation of concerns.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        min_trade_threshold: Decimal = Decimal("0.01")
    ):
        """
        Initialize the portfolio management facade.
        
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
            trading_manager, self.rebalance_calculator, self.position_analyzer, self.attribution_engine
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
        portfolio_value: Decimal | None = None
    ) -> dict[str, Any]:
        """Calculate complete rebalancing plan."""
        return self.rebalancing_service.calculate_rebalancing_plan(
            target_weights, current_positions, portfolio_value
        )

    def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Get comprehensive rebalancing summary."""
        return self.rebalancing_service.get_rebalancing_summary(target_weights)

    def estimate_rebalancing_impact(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
        """Estimate the impact of rebalancing."""
        return self.rebalancing_service.estimate_rebalancing_impact(target_weights)

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
        self,
        target_weights: dict[str, Decimal],
        dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute complete portfolio rebalancing."""
        # Calculate rebalancing plan
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)
        
        # Validate plan
        validation = self.execution_service.validate_rebalancing_plan(rebalance_plan)
        if not validation["is_valid"]:
            return {
                "status": "validation_failed",
                "validation_results": validation,
                "execution_results": None
            }
        
        # Execute plan
        execution_results = self.execution_service.execute_rebalancing_plan(rebalance_plan, dry_run)
        
        return {
            "status": "completed",
            "validation_results": validation,
            "execution_results": execution_results,
            "rebalance_plan": rebalance_plan
        }

    def execute_single_symbol_rebalance(
        self,
        symbol: str,
        target_weight: Decimal,
        dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute rebalancing for a single symbol."""
        # Calculate plan for single symbol
        target_weights = {symbol: target_weight}
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)
        
        if symbol not in rebalance_plan:
            return {
                "status": "error",
                "message": f"No rebalancing plan generated for {symbol}"
            }
        
        # Execute single symbol rebalance
        return self.execution_service.execute_single_rebalance(
            symbol, rebalance_plan[symbol], dry_run
        )

    # Comprehensive Operations
    def get_complete_portfolio_overview(self, target_weights: dict[str, Decimal] | None = None) -> dict[str, Any]:
        """Get complete portfolio overview with analysis and rebalancing info."""
        overview = {
            "portfolio_analysis": self.get_portfolio_analysis(),
            "strategy_performance": self.get_strategy_performance()
        }
        
        if target_weights:
            overview.update({
                "drift_analysis": self.analyze_portfolio_drift(target_weights),
                "rebalancing_summary": self.get_rebalancing_summary(target_weights),
                "rebalancing_impact": self.estimate_rebalancing_impact(target_weights),
                "strategy_comparison": self.compare_strategy_allocations(target_weights)
            })
        
        return overview

    def perform_portfolio_rebalancing_workflow(
        self,
        target_weights: dict[str, Decimal],
        dry_run: bool = True,
        include_analysis: bool = True
    ) -> dict[str, Any]:
        """Complete portfolio rebalancing workflow with analysis."""
        workflow_results = {}
        
        # Step 1: Pre-rebalancing analysis
        if include_analysis:
            workflow_results["pre_rebalancing_analysis"] = {
                "portfolio_analysis": self.get_portfolio_analysis(),
                "drift_analysis": self.analyze_portfolio_drift(target_weights),
                "impact_estimate": self.estimate_rebalancing_impact(target_weights)
            }
        
        # Step 2: Calculate and validate rebalancing plan
        rebalance_plan = self.rebalancing_service.calculate_rebalancing_plan(target_weights)
        validation = self.execution_service.validate_rebalancing_plan(rebalance_plan)
        
        workflow_results["rebalancing_plan"] = {
            "plan": rebalance_plan,
            "validation": validation,
            "summary": self.rebalancing_service.get_rebalancing_summary(target_weights)
        }
        
        # Step 3: Execute if validation passes
        if validation["is_valid"]:
            execution_results = self.execution_service.execute_rebalancing_plan(rebalance_plan, dry_run)
            workflow_results["execution"] = execution_results
        else:
            workflow_results["execution"] = {
                "status": "skipped",
                "reason": "Validation failed",
                "issues": validation["issues"]
            }
        
        # Step 4: Post-rebalancing analysis (if executed)
        if include_analysis and validation["is_valid"] and not dry_run:
            workflow_results["post_rebalancing_analysis"] = {
                "portfolio_analysis": self.get_portfolio_analysis(),
                "remaining_drift": self.analyze_portfolio_drift(target_weights)
            }
        
        return workflow_results

    # Utility methods
    def get_current_portfolio_value(self) -> Decimal:
        """Get current total portfolio value."""
        return Decimal(str(self.trading_manager.get_portfolio_value()))

    def get_current_positions(self) -> dict[str, Decimal]:
        """Get current position values."""
        positions = self.trading_manager.get_all_positions()
        return {
            pos.symbol: Decimal(str(pos.market_value))
            for pos in positions
            if pos.market_value > 0
        }

    def get_current_weights(self) -> dict[str, Decimal]:
        """Get current portfolio weights."""
        positions = self.get_current_positions()
        portfolio_value = self.get_current_portfolio_value()
        
        if portfolio_value == 0:
            return {}
        
        return {
            symbol: value / portfolio_value
            for symbol, value in positions.items()
        }
