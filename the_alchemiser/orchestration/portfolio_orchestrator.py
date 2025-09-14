"""Business Unit: orchestration | Status: current

Portfolio rebalancing orchestration workflow.

Coordinates portfolio state analysis and rebalancing plan generation using the
portfolio_v2 module. This orchestrator focuses on portfolio optimization logic
without trading execution.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolioDTO
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO


class PortfolioOrchestrator:
    """Orchestrates portfolio rebalancing workflow."""

    def __init__(self, settings: Settings, container: ApplicationContainer) -> None:
        self.settings = settings
        self.container = container
        self.logger = get_logger(__name__)

    def analyze_portfolio_state(self) -> dict[str, Any] | None:
        """Analyze current portfolio state and generate rebalancing recommendations.

        Returns:
            Portfolio analysis result or None if analysis failed

        """
        try:
            # Use portfolio_v2 for modern portfolio analysis
            from the_alchemiser.portfolio_v2 import PortfolioServiceV2

            # Get portfolio service from container  
            portfolio_service = PortfolioServiceV2(
                alpaca_manager=self.container.infrastructure.alpaca_manager()
            )

            # Get current portfolio snapshot via state reader
            portfolio_snapshot = portfolio_service._state_reader.build_portfolio_snapshot()

            if not portfolio_snapshot:
                self.logger.warning("Could not retrieve portfolio snapshot")
                return None

            self.logger.info(
                f"Portfolio analysis: {len(portfolio_snapshot.positions)} positions, "
                f"${portfolio_snapshot.total_value:.2f} total value"
            )

            return {
                "snapshot": portfolio_snapshot,
                "analysis_timestamp": datetime.now(),
                "position_count": len(portfolio_snapshot.positions),
                "total_value": float(portfolio_snapshot.total_value),
            }

        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            return None

    def generate_rebalancing_plan(
        self, target_allocations: ConsolidatedPortfolioDTO
    ) -> dict[str, Any] | None:
        """Generate rebalancing plan based on target allocations.

        Args:
            target_allocations: Consolidated portfolio allocation DTO

        Returns:
            Rebalancing plan or None if generation failed

        """
        try:
            # Use portfolio_v2 for rebalancing plan calculation

            from the_alchemiser.portfolio_v2 import RebalancePlanCalculator
            from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO

            # Convert ConsolidatedPortfolioDTO to target weights for portfolio_v2
            target_weights = target_allocations.target_allocations

            # Create strategy allocation DTO
            allocation_dto = StrategyAllocationDTO(
                target_weights=target_weights,
                correlation_id=target_allocations.correlation_id,
                as_of=target_allocations.timestamp,
                constraints=target_allocations.constraints,
            )

            # Get data adapter
            data_adapter = self.container.infrastructure.alpaca_manager()

            # Create rebalance plan calculator
            calculator = RebalancePlanCalculator()

            # Get portfolio snapshot
            from the_alchemiser.portfolio_v2.core.state_reader import PortfolioStateReader
            from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import AlpacaDataAdapter
            
            data_adapter_instance = AlpacaDataAdapter(data_adapter)
            state_reader = PortfolioStateReader(data_adapter_instance)
            snapshot = state_reader.build_portfolio_snapshot()

            # Generate rebalancing plan
            correlation_id = f"rebalance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            rebalance_plan = calculator.build_plan(allocation_dto, snapshot, correlation_id)

            if not rebalance_plan:
                self.logger.warning("Could not generate rebalancing plan")
                return None

            self.logger.info(
                f"Generated rebalancing plan: {len(rebalance_plan.items)} trades, "
                f"${rebalance_plan.total_trade_value:.2f} total trade value"
            )

            return {
                "plan": rebalance_plan,
                "trade_count": len(rebalance_plan.items),
                "total_trade_value": float(rebalance_plan.total_trade_value),
                "target_allocations": target_allocations.to_dict_allocation(),
                "plan_timestamp": rebalance_plan.timestamp,
            }

        except Exception as e:
            self.logger.error(f"Rebalancing plan generation failed: {e}")
            return None

    def analyze_allocation_comparison(
        self, consolidated_portfolio: ConsolidatedPortfolioDTO
    ) -> AllocationComparisonDTO | None:
        """Analyze target vs current allocations.

        Args:
            consolidated_portfolio: Consolidated portfolio allocation DTO

        Returns:
            AllocationComparisonDTO or None if analysis failed

        """
        try:
            # Get current account info and positions
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                self.logger.warning("Could not retrieve account information")
                return None

            # Get current positions
            current_positions = alpaca_manager.get_positions()
            positions_dict = {pos.symbol: float(pos.market_value) for pos in current_positions}

            # Use shared utilities for allocation comparison
            from the_alchemiser.shared.utils.portfolio_calculations import (
                build_allocation_comparison,
            )

            # Convert account info to dict format expected by calculation
            account_dict = {
                "equity": account_info.equity,
                "portfolio_value": account_info.portfolio_value,
                "buying_power": account_info.buying_power,
            }

            # Convert ConsolidatedPortfolioDTO to dict for existing utility function
            allocation_comparison_data = build_allocation_comparison(
                consolidated_portfolio.to_dict_allocation(), account_dict, positions_dict
            )

            # Create AllocationComparisonDTO from the calculation result
            allocation_comparison_dto = AllocationComparisonDTO(
                target_values=allocation_comparison_data["target_values"],
                current_values=allocation_comparison_data["current_values"],
                deltas=allocation_comparison_data["deltas"],
            )

            self.logger.info("Generated allocation comparison analysis")

            return allocation_comparison_dto

        except Exception as e:
            self.logger.error(f"Allocation comparison analysis failed: {e}")
            return None

    def get_comprehensive_account_data(self) -> dict[str, Any] | None:
        """Retrieve comprehensive account data including account info, positions, and open orders.

        Returns:
            Dictionary containing account_info, current_positions, and open_orders, or None if failed

        """
        try:
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account info
            account_raw = alpaca_manager.get_account()
            account_info = None
            if account_raw:
                account_info = {
                    "portfolio_value": getattr(account_raw, "portfolio_value", None)
                    or getattr(account_raw, "equity", None),
                    "cash": getattr(account_raw, "cash", 0),
                    "buying_power": getattr(account_raw, "buying_power", 0),
                    "equity": getattr(account_raw, "equity", None)
                    or getattr(account_raw, "portfolio_value", None),
                }
                portfolio_value = account_info.get("portfolio_value", 0)
                # Safely convert to float for logging, handling string values from API
                try:
                    portfolio_value_float = (
                        float(portfolio_value) if portfolio_value is not None else 0.0
                    )
                except (ValueError, TypeError):
                    portfolio_value_float = 0.0
                self.logger.info(
                    f"Retrieved account info: Portfolio value ${portfolio_value_float:,.2f}"
                )

            # Get current positions
            current_positions = {}
            positions_list = alpaca_manager.get_positions()
            if positions_list:
                current_positions = {
                    pos.symbol: {
                        "qty": float(getattr(pos, "qty", 0)),
                        "market_value": float(getattr(pos, "market_value", 0)),
                        "avg_entry_price": float(getattr(pos, "avg_entry_price", 0)),
                        "current_price": float(getattr(pos, "current_price", 0)),
                        "unrealized_pl": float(getattr(pos, "unrealized_pl", 0)),
                        "unrealized_plpc": float(getattr(pos, "unrealized_plpc", 0)),
                    }
                    for pos in positions_list
                }
                self.logger.info(f"Retrieved {len(current_positions)} current positions")

            # Get open orders
            open_orders = []
            try:
                orders_list = alpaca_manager.get_orders(status="open")
                if orders_list:
                    open_orders = [
                        {
                            "id": getattr(order, "id", "unknown"),
                            "symbol": getattr(order, "symbol", "unknown"),
                            "type": str(getattr(order, "order_type", "unknown")).replace(
                                "OrderType.", ""
                            ),
                            "qty": float(getattr(order, "qty", 0)),
                            "limit_price": float(getattr(order, "limit_price", 0))
                            if order.limit_price
                            else None,
                            "status": str(getattr(order, "status", "unknown")).replace(
                                "OrderStatus.", ""
                            ),
                            "created_at": str(getattr(order, "created_at", "unknown")),
                        }
                        for order in orders_list
                    ]
                    self.logger.info(f"Retrieved {len(open_orders)} open orders")
            except Exception as e:
                self.logger.warning(f"Failed to retrieve open orders: {e}")

            return {
                "account_info": account_info,
                "current_positions": current_positions,
                "open_orders": open_orders,
            }

        except Exception as e:
            self.logger.error(f"Failed to retrieve comprehensive account data: {e}")
            return None

    def execute_portfolio_workflow(
        self, target_allocations: dict[str, float]
    ) -> dict[str, Any] | None:
        """Execute complete portfolio analysis workflow.

        Args:
            target_allocations: Target allocation percentages by symbol

        Returns:
            Complete portfolio analysis result or None if failed

        """
        try:
            # Analyze current portfolio state
            portfolio_state = self.analyze_portfolio_state()
            if not portfolio_state:
                return None

            # Create ConsolidatedPortfolioDTO from target allocations dict
            from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolioDTO
            from decimal import Decimal
            
            consolidated_dto = ConsolidatedPortfolioDTO(
                target_allocations={symbol: Decimal(str(weight)) for symbol, weight in target_allocations.items()},
                correlation_id=f"portfolio_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                strategy_count=1,
                source_strategies=["portfolio_workflow"]
            )

            # Generate rebalancing plan
            rebalancing_plan = self.generate_rebalancing_plan(consolidated_dto)
            if not rebalancing_plan:
                return None

            # Analyze allocation comparison
            allocation_analysis = self.analyze_allocation_comparison(consolidated_dto)
            if not allocation_analysis:
                return None

            return {
                "portfolio_state": portfolio_state,
                "rebalancing_plan": rebalancing_plan,
                "allocation_analysis": allocation_analysis,
                "workflow_success": True,
            }

        except Exception as e:
            self.logger.error(f"Portfolio workflow execution failed: {e}")
            return None
