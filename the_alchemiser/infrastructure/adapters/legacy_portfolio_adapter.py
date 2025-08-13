"""Legacy adapter for gradual migration from old portfolio rebalancer."""

from decimal import Decimal
from typing import Any

from the_alchemiser.application.portfolio.services.portfolio_management_facade import PortfolioManagementFacade
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class LegacyPortfolioRebalancerAdapter:
    """
    Adapter to bridge between the new portfolio management system 
    and the existing portfolio rebalancer interface.
    
    This allows gradual migration from the monolithic portfolio_rebalancer.py
    to the new modular system with feature flags for safe deployment.
    """

    def __init__(
        self,
        trading_manager: TradingServiceManager,
        use_new_system: bool = False,
        min_trade_threshold: Decimal = Decimal("0.01")
    ):
        """
        Initialize the legacy adapter.
        
        Args:
            trading_manager: Service for trading operations
            use_new_system: Feature flag to enable new system
            min_trade_threshold: Minimum threshold for trades
        """
        self.trading_manager = trading_manager
        self.use_new_system = use_new_system
        
        # Initialize new system components
        if use_new_system:
            self.portfolio_facade = PortfolioManagementFacade(trading_manager, min_trade_threshold)
        else:
            self.portfolio_facade = None

    def calculate_rebalance_amounts(
        self,
        target_weights: dict[str, float],
        current_values: dict[str, float],
        portfolio_value: float,
        threshold: float = 0.01
    ) -> dict[str, dict[str, Any]]:
        """
        Legacy interface for calculating rebalance amounts.
        
        Maintains compatibility with existing portfolio_rebalancer.py interface
        while optionally using the new system under the hood.
        """
        if not self.use_new_system or self.portfolio_facade is None:
            # Fall back to original trading_math calculation
            from the_alchemiser.utils.trading_math import calculate_rebalance_amounts
            return calculate_rebalance_amounts(target_weights, current_values, portfolio_value, threshold)

        # Use new system with conversion between old and new interfaces
        target_weights_decimal = {symbol: Decimal(str(weight)) for symbol, weight in target_weights.items()}
        current_values_decimal = {symbol: Decimal(str(value)) for symbol, value in current_values.items()}
        portfolio_value_decimal = Decimal(str(portfolio_value))

        # Calculate using new system
        rebalance_plan = self.portfolio_facade.calculate_rebalancing_plan(
            target_weights_decimal, current_values_decimal, portfolio_value_decimal
        )

        # Convert back to legacy format
        legacy_format = {}
        for symbol, plan in rebalance_plan.items():
            legacy_format[symbol] = {
                "current_weight": float(plan.current_weight),
                "target_weight": float(plan.target_weight),
                "weight_diff": float(plan.weight_diff),
                "target_value": float(plan.target_value),
                "current_value": float(plan.current_value),
                "trade_amount": float(plan.trade_amount),
                "needs_rebalance": plan.needs_rebalance
            }

        return legacy_format

    def get_portfolio_analysis(self) -> dict[str, Any]:
        """Get comprehensive portfolio analysis using new or old system."""
        if not self.use_new_system or self.portfolio_facade is None:
            # Provide basic analysis using existing methods
            positions = self.trading_manager.get_all_positions()
            portfolio_value = self.trading_manager.get_portfolio_value()
            
            return {
                "portfolio_value": portfolio_value,
                "num_positions": len(positions),
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "value": pos.market_value,
                        "qty": pos.qty
                    }
                    for pos in positions
                ]
            }

        # Use new system for rich analysis
        return self.portfolio_facade.get_portfolio_analysis()

    def execute_rebalancing(
        self,
        target_weights: dict[str, float],
        dry_run: bool = True
    ) -> dict[str, Any]:
        """Execute portfolio rebalancing using new or old system."""
        if not self.use_new_system or self.portfolio_facade is None:
            # Use legacy execution approach
            return self._legacy_execute_rebalancing(target_weights, dry_run)

        # Use new system
        target_weights_decimal = {symbol: Decimal(str(weight)) for symbol, weight in target_weights.items()}
        return self.portfolio_facade.execute_rebalancing(target_weights_decimal, dry_run)

    def get_symbols_needing_rebalance(self, target_weights: dict[str, float]) -> list[str]:
        """Get symbols that need rebalancing."""
        if not self.use_new_system or self.portfolio_facade is None:
            # Use legacy calculation
            current_values = {
                pos.symbol: pos.market_value
                for pos in self.trading_manager.get_all_positions()
            }
            portfolio_value = self.trading_manager.get_portfolio_value()
            
            rebalance_data = self.calculate_rebalance_amounts(
                target_weights, current_values, portfolio_value
            )
            
            return [
                symbol for symbol, data in rebalance_data.items()
                if data.get("needs_rebalance", False)
            ]

        # Use new system
        target_weights_decimal = {symbol: Decimal(str(weight)) for symbol, weight in target_weights.items()}
        rebalance_plan = self.portfolio_facade.calculate_rebalancing_plan(target_weights_decimal)
        
        return [
            symbol for symbol, plan in rebalance_plan.items()
            if plan.needs_rebalance
        ]

    def get_rebalancing_summary(self, target_weights: dict[str, float]) -> dict[str, Any]:
        """Get comprehensive rebalancing summary."""
        if not self.use_new_system or self.portfolio_facade is None:
            # Provide basic summary using legacy methods
            symbols_needing_rebalance = self.get_symbols_needing_rebalance(target_weights)
            return {
                "symbols_needing_rebalance": symbols_needing_rebalance,
                "num_symbols_to_rebalance": len(symbols_needing_rebalance),
                "analysis_method": "legacy"
            }

        # Use new system for comprehensive summary
        target_weights_decimal = {symbol: Decimal(str(weight)) for symbol, weight in target_weights.items()}
        return self.portfolio_facade.get_rebalancing_summary(target_weights_decimal)

    def _legacy_execute_rebalancing(self, target_weights: dict[str, float], dry_run: bool) -> dict[str, Any]:
        """Legacy rebalancing execution using basic order placement."""
        try:
            # Get current positions and calculate what needs to be done
            current_values = {
                pos.symbol: pos.market_value
                for pos in self.trading_manager.get_all_positions()
            }
            portfolio_value = self.trading_manager.get_portfolio_value()
            
            rebalance_data = self.calculate_rebalance_amounts(
                target_weights, current_values, portfolio_value
            )

            orders_placed = {}
            
            for symbol, data in rebalance_data.items():
                if not data.get("needs_rebalance", False):
                    continue
                
                trade_amount = data["trade_amount"]
                
                if dry_run:
                    orders_placed[symbol] = {
                        "status": "simulated",
                        "trade_amount": trade_amount,
                        "message": f"Would trade ${trade_amount} of {symbol}"
                    }
                else:
                    # Place actual orders using trading manager
                    try:
                        if trade_amount > 0:
                            # Buy order
                            result = self.trading_manager.place_market_order(symbol, "buy", abs(trade_amount))
                            orders_placed[symbol] = {
                                "status": "placed",
                                "side": "buy",
                                "amount": trade_amount,
                                "order_id": result.get("order_id")
                            }
                        else:
                            # Sell order
                            result = self.trading_manager.place_market_order(symbol, "sell", abs(trade_amount))
                            orders_placed[symbol] = {
                                "status": "placed",
                                "side": "sell",
                                "amount": abs(trade_amount),
                                "order_id": result.get("order_id")
                            }
                    except Exception as e:
                        orders_placed[symbol] = {
                            "status": "failed",
                            "error": str(e),
                            "trade_amount": trade_amount
                        }

            return {
                "status": "completed",
                "execution_method": "legacy",
                "orders_placed": orders_placed,
                "total_orders": len(orders_placed)
            }

        except Exception as e:
            return {
                "status": "failed",
                "execution_method": "legacy",
                "error": str(e),
                "orders_placed": {}
            }

    def is_using_new_system(self) -> bool:
        """Check if the adapter is using the new system."""
        return self.use_new_system and self.portfolio_facade is not None

    def switch_to_new_system(self) -> None:
        """Switch to using the new system."""
        if self.portfolio_facade is None:
            self.portfolio_facade = PortfolioManagementFacade(self.trading_manager)
        self.use_new_system = True

    def switch_to_legacy_system(self) -> None:
        """Switch back to using the legacy system."""
        self.use_new_system = False

    def compare_systems(self, target_weights: dict[str, float]) -> dict[str, Any]:
        """Compare results between legacy and new systems for validation."""
        # Calculate using legacy system
        current_values = {
            pos.symbol: pos.market_value
            for pos in self.trading_manager.get_all_positions()
        }
        portfolio_value = self.trading_manager.get_portfolio_value()
        
        legacy_results = self.calculate_rebalance_amounts(
            target_weights, current_values, portfolio_value
        )

        # Calculate using new system (temporarily)
        original_flag = self.use_new_system
        self.use_new_system = True
        if self.portfolio_facade is None:
            self.portfolio_facade = PortfolioManagementFacade(self.trading_manager)
        
        new_results = {}
        try:
            target_weights_decimal = {symbol: Decimal(str(weight)) for symbol, weight in target_weights.items()}
            rebalance_plan = self.portfolio_facade.calculate_rebalancing_plan(target_weights_decimal)
            
            # Convert to comparable format
            new_results = {
                symbol: {
                    "current_weight": float(plan.current_weight),
                    "target_weight": float(plan.target_weight),
                    "weight_diff": float(plan.weight_diff),
                    "target_value": float(plan.target_value),
                    "current_value": float(plan.current_value),
                    "trade_amount": float(plan.trade_amount),
                    "needs_rebalance": plan.needs_rebalance
                }
                for symbol, plan in rebalance_plan.items()
            }
        finally:
            # Restore original flag
            self.use_new_system = original_flag

        # Compare results
        differences = {}
        all_symbols = set(legacy_results.keys()) | set(new_results.keys())
        
        for symbol in all_symbols:
            legacy_data = legacy_results.get(symbol, {})
            new_data = new_results.get(symbol, {})
            
            if legacy_data and new_data:
                differences[symbol] = {
                    "trade_amount_diff": abs(legacy_data.get("trade_amount", 0) - new_data.get("trade_amount", 0)),
                    "weight_diff_match": abs(legacy_data.get("weight_diff", 0) - new_data.get("weight_diff", 0)) < 0.001,
                    "needs_rebalance_match": legacy_data.get("needs_rebalance") == new_data.get("needs_rebalance")
                }

        return {
            "legacy_results": legacy_results,
            "new_results": new_results,
            "differences": differences,
            "systems_match": all(
                diff["weight_diff_match"] and diff["needs_rebalance_match"] 
                for diff in differences.values()
            )
        }
