"""Business Unit: order execution/placement | Status: current.

Position analysis use case for execution context.

Provides position monitoring and analysis operations for execution decision-making.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from the_alchemiser.domain.interfaces import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.services.errors.decorators import translate_trading_errors
from the_alchemiser.domain.shared_kernel.tooling.num import floats_equal

logger = logging.getLogger(__name__)


@dataclass
class PositionInfo:
    """Detailed position information with analysis."""

    symbol: str
    quantity: float
    market_value: float | None
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    cost_basis: float | None
    current_price: float | None
    weight_percent: float | None  # Position weight in portfolio


@dataclass
class PortfolioSummary:
    """Portfolio-level position summary."""

    total_positions: int
    total_market_value: float
    largest_position_value: float
    largest_position_symbol: str | None
    concentration_risk: float  # Largest position as % of portfolio
    long_positions: int
    short_positions: int
    unrealized_pnl_total: float


class PositionAnalysis:
    """Position analysis use case for execution context.

    Provides position monitoring and analysis operations for execution decision-making.
    """

    def __init__(
        self,
        trading_repo: TradingRepository,
        account_repo: AccountRepository,
        market_data_repo: MarketDataRepository,
    ) -> None:
        """Initialize position analysis use case.

        Args:
            trading_repo: Repository for trading operations
            account_repo: Repository for account operations
            market_data_repo: Repository for market data operations

        """
        self.trading_repo = trading_repo
        self.account_repo = account_repo
        self.market_data_repo = market_data_repo
        self.logger = logging.getLogger(__name__)

    @translate_trading_errors
    def get_position_details(self, symbol: str) -> PositionInfo | None:
        """Get detailed information for a specific position.

        Args:
            symbol: Symbol to get position details for

        Returns:
            PositionInfo object or None if no position exists

        """
        try:
            positions = self.trading_repo.get_positions()

            # Find the position for the symbol
            target_position = None
            for position in positions:
                if getattr(position, "symbol", "") == symbol:
                    target_position = position
                    break

            if not target_position:
                return None

            # Get current price for analysis
            current_price = None
            try:
                current_price = self.market_data_repo.get_current_price(symbol)
            except Exception:
                self.logger.warning(f"Could not get current price for {symbol}")

            # Get portfolio value for weight calculation
            portfolio_value = 0.0
            try:
                account = self.account_repo.get_account()
                portfolio_value = float(getattr(account, "portfolio_value", 0))
            except Exception:
                self.logger.warning("Could not get portfolio value for weight calculation")

            # Extract position data
            quantity = float(getattr(target_position, "qty", 0))
            market_value = getattr(target_position, "market_value", None)
            unrealized_pnl = getattr(target_position, "unrealized_pl", None)
            unrealized_pnl_percent = getattr(target_position, "unrealized_plpc", None)
            cost_basis = getattr(target_position, "avg_entry_price", None)

            # Calculate weight percentage
            weight_percent = None
            if market_value and portfolio_value > 0:
                weight_percent = (abs(float(market_value)) / portfolio_value) * 100

            return PositionInfo(
                symbol=symbol,
                quantity=quantity,
                market_value=float(market_value) if market_value else None,
                unrealized_pnl=float(unrealized_pnl) if unrealized_pnl else None,
                unrealized_pnl_percent=float(unrealized_pnl_percent)
                if unrealized_pnl_percent
                else None,
                cost_basis=float(cost_basis) if cost_basis else None,
                current_price=current_price,
                weight_percent=weight_percent,
            )

        except Exception as e:
            self.logger.error(f"Failed to get position details for {symbol}: {e}")
            raise

    @translate_trading_errors
    def get_all_positions(self) -> list[PositionInfo]:
        """Get detailed information for all positions.

        Returns:
            List of PositionInfo objects

        """
        try:
            positions = self.trading_repo.get_positions()
            position_details = []

            # Get portfolio value for weight calculations
            portfolio_value = 0.0
            try:
                account = self.account_repo.get_account()
                portfolio_value = float(getattr(account, "portfolio_value", 0))
            except Exception:
                self.logger.warning("Could not get portfolio value for weight calculation")

            for position in positions:
                symbol = getattr(position, "symbol", "")
                if not symbol:
                    continue

                quantity = float(getattr(position, "qty", 0))

                # Skip positions with zero quantity
                if floats_equal(quantity, 0.0):
                    continue

                # Get current price
                current_price = None
                try:
                    current_price = self.market_data_repo.get_current_price(symbol)
                except Exception:
                    self.logger.warning(f"Could not get current price for {symbol}")

                # Extract position data
                market_value = getattr(position, "market_value", None)
                unrealized_pnl = getattr(position, "unrealized_pl", None)
                unrealized_pnl_percent = getattr(position, "unrealized_plpc", None)
                cost_basis = getattr(position, "avg_entry_price", None)

                # Calculate weight percentage
                weight_percent = None
                if market_value and portfolio_value > 0:
                    weight_percent = (abs(float(market_value)) / portfolio_value) * 100

                position_info = PositionInfo(
                    symbol=symbol,
                    quantity=quantity,
                    market_value=float(market_value) if market_value else None,
                    unrealized_pnl=float(unrealized_pnl) if unrealized_pnl else None,
                    unrealized_pnl_percent=float(unrealized_pnl_percent)
                    if unrealized_pnl_percent
                    else None,
                    cost_basis=float(cost_basis) if cost_basis else None,
                    current_price=current_price,
                    weight_percent=weight_percent,
                )
                position_details.append(position_info)

            return position_details

        except Exception as e:
            self.logger.error(f"Failed to get all positions: {e}")
            raise

    @translate_trading_errors
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio-level position summary.

        Returns:
            PortfolioSummary object

        """
        try:
            positions = self.get_all_positions()

            if not positions:
                return PortfolioSummary(
                    total_positions=0,
                    total_market_value=0.0,
                    largest_position_value=0.0,
                    largest_position_symbol=None,
                    concentration_risk=0.0,
                    long_positions=0,
                    short_positions=0,
                    unrealized_pnl_total=0.0,
                )

            # Calculate summary statistics
            total_market_value = sum(abs(pos.market_value) for pos in positions if pos.market_value)

            unrealized_pnl_total = sum(
                pos.unrealized_pnl for pos in positions if pos.unrealized_pnl
            )

            long_positions = len([pos for pos in positions if pos.quantity > 0])
            short_positions = len([pos for pos in positions if pos.quantity < 0])

            # Find largest position
            largest_position = max(
                positions,
                key=lambda p: abs(p.market_value) if p.market_value else 0,
                default=None,
            )

            largest_position_value = 0.0
            largest_position_symbol = None
            concentration_risk = 0.0

            if largest_position and largest_position.market_value:
                largest_position_value = abs(largest_position.market_value)
                largest_position_symbol = largest_position.symbol
                if total_market_value > 0:
                    concentration_risk = (largest_position_value / total_market_value) * 100

            return PortfolioSummary(
                total_positions=len(positions),
                total_market_value=total_market_value,
                largest_position_value=largest_position_value,
                largest_position_symbol=largest_position_symbol,
                concentration_risk=concentration_risk,
                long_positions=long_positions,
                short_positions=short_positions,
                unrealized_pnl_total=unrealized_pnl_total,
            )

        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {e}")
            raise

    def validate_position_for_order(self, symbol: str, quantity: float, side: str) -> bool:
        """Validate if an order can be placed based on current position.

        Args:
            symbol: Symbol to validate
            quantity: Order quantity
            side: Order side ('buy' or 'sell')

        Returns:
            True if order is valid based on position

        """
        try:
            position_info = self.get_position_details(symbol)

            if side.lower() == "sell":
                if not position_info:
                    self.logger.warning(f"Cannot sell {symbol}: no position exists")
                    return False

                current_quantity = position_info.quantity
                if current_quantity <= 0:
                    self.logger.warning(f"Cannot sell {symbol}: no long position")
                    return False

                if abs(quantity) > current_quantity:
                    self.logger.warning(
                        f"Cannot sell {abs(quantity)} shares of {symbol}: "
                        f"only {current_quantity} shares available"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate position for order {symbol}: {e}")
            return False

    def calculate_position_risk_metrics(self, symbol: str) -> dict[str, float]:
        """Calculate risk metrics for a specific position.

        Args:
            symbol: Symbol to calculate risk for

        Returns:
            Dictionary with risk metrics

        """
        try:
            position_info = self.get_position_details(symbol)
            if not position_info:
                return {"error": "Position not found"}

            portfolio_summary = self.get_portfolio_summary()

            metrics = {
                "position_value": abs(position_info.market_value)
                if position_info.market_value
                else 0,
                "portfolio_weight": position_info.weight_percent or 0,
                "unrealized_pnl": position_info.unrealized_pnl or 0,
                "unrealized_pnl_percent": position_info.unrealized_pnl_percent or 0,
                "portfolio_concentration_risk": portfolio_summary.concentration_risk,
            }

            # Add current price vs cost basis analysis
            if position_info.current_price and position_info.cost_basis:
                price_change_percent = (
                    (position_info.current_price - position_info.cost_basis)
                    / position_info.cost_basis
                ) * 100
                metrics["price_change_percent"] = price_change_percent

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics for {symbol}: {e}")
            return {"error": str(e)}
