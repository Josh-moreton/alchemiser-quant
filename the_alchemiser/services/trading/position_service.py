"""Enhanced Position Service.

This service provides type-safe position monitoring and management operations.
It builds on top of the TradingRepository and MarketDataRepository interfaces, adding:
- Position analysis and reporting
- Risk calculations and validation
- Portfolio-level position management
- Enhanced error handling and logging
- Type safety throughout

This represents the service layer from our eventual architecture vision,
providing business logic while depending on domain interfaces.
"""

import logging
from dataclasses import dataclass

from the_alchemiser.domain.interfaces import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)
from the_alchemiser.services.errors.decorators import translate_trading_errors

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

    total_market_value: float
    total_positions: int
    largest_position_value: float
    largest_position_percent: float
    cash_balance: float | None
    total_equity: float | None


class PositionValidationError(Exception):
    """Exception raised when position validation fails."""


class PositionService:
    """Enhanced position service with analysis and portfolio management.

    This service provides a higher-level interface for position operations,
    adding analysis, risk calculations, and portfolio management on top of
    the basic repository operations.
    """

    def __init__(
        self,
        trading_repo: TradingRepository,
        market_data_repo: MarketDataRepository | None = None,
        account_repo: AccountRepository | None = None,
        max_position_weight: float = 0.10,  # 10% max position weight
    ) -> None:
        """Initialize the position service.

        Args:
            trading_repo: Trading repository for position operations
            market_data_repo: Optional market data repository for price data
            account_repo: Optional account repository for balance data
            max_position_weight: Maximum allowed position weight (0.10 = 10%)

        """
        self._trading = trading_repo
        self._market_data = market_data_repo
        self._account = account_repo
        self._max_position_weight = max_position_weight

    @translate_trading_errors()
    def get_positions_with_analysis(self) -> dict[str, PositionInfo]:
        """Get all positions with detailed analysis.

        Returns:
            Dictionary mapping symbols to detailed position information

        Raises:
            Exception: If position data cannot be retrieved

        """
        logger.info("Retrieving positions with analysis")

        # Get basic positions
        positions = self._trading.get_positions_dict()

        if not positions:
            logger.info("No positions found")
            return {}

        # Get portfolio total for weight calculations
        portfolio_total = self._calculate_portfolio_total(positions)

        # Enhance each position with analysis
        enhanced_positions = {}

        for symbol, quantity in positions.items():
            if quantity == 0:
                continue  # Skip zero positions

            try:
                position_info = self._create_position_info(symbol, quantity, portfolio_total)
                enhanced_positions[symbol] = position_info

            except Exception as e:
                logger.error(f"Failed to analyze position {symbol}: {e}")
                # Create minimal position info
                enhanced_positions[symbol] = PositionInfo(
                    symbol=symbol,
                    quantity=quantity,
                    market_value=None,
                    unrealized_pnl=None,
                    unrealized_pnl_percent=None,
                    cost_basis=None,
                    current_price=None,
                    weight_percent=None,
                )

        logger.info(f"✅ Retrieved {len(enhanced_positions)} positions with analysis")
        return enhanced_positions

    @translate_trading_errors()
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio-level summary and analysis.

        Returns:
            Portfolio summary with key metrics

        Raises:
            Exception: If portfolio data cannot be retrieved

        """
        logger.info("Calculating portfolio summary")

        positions = self.get_positions_with_analysis()

        if not positions:
            return PortfolioSummary(
                total_market_value=0.0,
                total_positions=0,
                largest_position_value=0.0,
                largest_position_percent=0.0,
                cash_balance=self._get_cash_balance(),
                total_equity=None,
            )

        # Calculate summary metrics
        total_market_value = 0.0
        largest_position_value = 0.0
        largest_position_percent = 0.0

        for position in positions.values():
            if position.market_value:
                total_market_value += position.market_value

                if position.market_value > largest_position_value:
                    largest_position_value = position.market_value

            if position.weight_percent:
                if position.weight_percent > largest_position_percent:
                    largest_position_percent = position.weight_percent

        cash_balance = self._get_cash_balance()
        total_equity = total_market_value + (cash_balance or 0.0)

        summary = PortfolioSummary(
            total_market_value=total_market_value,
            total_positions=len(positions),
            largest_position_value=largest_position_value,
            largest_position_percent=largest_position_percent,
            cash_balance=cash_balance,
            total_equity=total_equity,
        )

        logger.info(
            f"✅ Portfolio summary: {summary.total_positions} positions, "
            f"${summary.total_market_value:.2f} market value"
        )
        return summary

    def check_position_limits(self, symbol: str, proposed_quantity: float) -> bool:
        """Check if a proposed position would violate position limits.

        Args:
            symbol: Symbol to check
            proposed_quantity: Proposed total position size

        Returns:
            True if position is within limits

        Raises:
            PositionValidationError: If position violates limits

        """
        if proposed_quantity <= 0:
            return True  # No position, no limit violation

        try:
            # Get current portfolio total
            positions = self._trading.get_positions_dict()
            portfolio_total = self._calculate_portfolio_total(positions)

            if portfolio_total <= 0:
                return True  # No portfolio value to check against

            # Calculate proposed position value
            if self._market_data:
                current_price = self._market_data.get_current_price(symbol)
                if current_price:
                    proposed_value = proposed_quantity * current_price
                    proposed_weight = proposed_value / portfolio_total

                    if proposed_weight > self._max_position_weight:
                        raise PositionValidationError(
                            f"Position weight {proposed_weight:.1%} exceeds limit "
                            f"{self._max_position_weight:.1%} for {symbol}"
                        )

            logger.info(f"✅ Position limits check passed for {symbol}")
            return True

        except PositionValidationError:
            raise
        except Exception as e:
            logger.warning(f"Could not validate position limits for {symbol}: {e}")
            return True  # Allow if we can't validate

    @translate_trading_errors()
    def get_position_risk_metrics(self, symbol: str) -> dict[str, float | None]:
        """Get risk metrics for a specific position.

        Args:
            symbol: Symbol to analyze

        Returns:
            Dictionary with risk metrics

        Raises:
            Exception: If position data cannot be retrieved

        """
        positions = self._trading.get_positions_dict()
        quantity = positions.get(symbol, 0.0)

        if quantity == 0:
            return {
                "position_value": 0.0,
                "portfolio_weight": 0.0,
                "unrealized_pnl": 0.0,
                "unrealized_pnl_percent": 0.0,
            }

        position_info = self.get_positions_with_analysis().get(symbol)

        if not position_info:
            return {
                "position_value": None,
                "portfolio_weight": None,
                "unrealized_pnl": None,
                "unrealized_pnl_percent": None,
            }

        return {
            "position_value": position_info.market_value,
            "portfolio_weight": position_info.weight_percent,
            "unrealized_pnl": position_info.unrealized_pnl,
            "unrealized_pnl_percent": position_info.unrealized_pnl_percent,
        }

    @translate_trading_errors()
    def get_largest_positions(self, limit: int = 5) -> list[PositionInfo]:
        """Get the largest positions by market value.

        Args:
            limit: Number of positions to return

        Returns:
            List of largest positions sorted by market value

        Raises:
            Exception: If position data cannot be retrieved

        """
        positions = self.get_positions_with_analysis()

        # Filter positions with market value and sort
        valued_positions = [
            pos
            for pos in positions.values()
            if pos.market_value is not None and pos.market_value > 0
        ]

        valued_positions.sort(key=lambda p: p.market_value or 0, reverse=True)

        return valued_positions[:limit]

    @translate_trading_errors(default_return=0.0)
    def calculate_diversification_score(self) -> float:
        """Calculate a simple diversification score (0-1, higher is more diversified).

        Returns:
            Diversification score between 0 and 1

        Raises:
            Exception: If position data cannot be retrieved

        """
        positions = self.get_positions_with_analysis()

        if len(positions) <= 1:
            return 0.0  # No diversification with 0-1 positions

        # Calculate concentration (sum of squared weights)
        total_squared_weights = 0.0
        valid_weights = 0

        for position in positions.values():
            if position.weight_percent is not None:
                weight = position.weight_percent / 100.0  # Convert to decimal
                total_squared_weights += weight**2
                valid_weights += 1

        if valid_weights == 0:
            return 0.0

        # Herfindahl index (concentration measure)
        herfindahl = total_squared_weights

        # Convert to diversification score (1 - concentration)
        # Perfect diversification (equal weights) would give score closer to 1
        max_herfindahl = 1.0  # Maximum concentration (one position = 100%)
        diversification_score = 1.0 - (herfindahl / max_herfindahl)

        return min(1.0, max(0.0, diversification_score))

    # Private helper methods

    def _create_position_info(
        self, symbol: str, quantity: float, portfolio_total: float
    ) -> PositionInfo:
        """Create detailed position information."""
        current_price = None
        market_value = None
        weight_percent = None

        # Get current price and calculate market value
        if self._market_data:
            try:
                current_price = self._market_data.get_current_price(symbol)
                if current_price:
                    market_value = quantity * current_price

                    # Calculate portfolio weight
                    if portfolio_total > 0 and market_value:
                        weight_percent = (market_value / portfolio_total) * 100

            except Exception as e:
                logger.warning(f"Could not get market data for {symbol}: {e}")

        # Get cost basis and PnL (if available through account repository)
        cost_basis = None
        unrealized_pnl = None
        unrealized_pnl_percent = None

        if self._account:
            try:
                account_positions = self._account.get_positions()
                position_data = None

                # Find the position data for the symbol
                for position in account_positions:
                    if (hasattr(position, "symbol") and position.symbol == symbol) or (
                        isinstance(position, dict) and position.get("symbol") == symbol
                    ):
                        position_data = position
                        break

                if position_data:
                    if hasattr(position_data, "cost_basis"):
                        cost_basis = position_data.cost_basis
                        unrealized_pnl = getattr(position_data, "unrealized_pl", None)
                    elif isinstance(position_data, dict):
                        cost_basis = position_data.get("cost_basis")
                        unrealized_pnl = position_data.get("unrealized_pnl")

                    # Calculate PnL percentage
                    if unrealized_pnl is not None and cost_basis and cost_basis != 0:
                        unrealized_pnl_percent = (
                            float(unrealized_pnl) / abs(float(cost_basis))
                        ) * 100

            except Exception as e:
                logger.warning(f"Could not get account data for {symbol}: {e}")

        return PositionInfo(
            symbol=symbol,
            quantity=quantity,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            cost_basis=cost_basis,
            current_price=current_price,
            weight_percent=weight_percent,
        )

    def _calculate_portfolio_total(self, positions: dict[str, float]) -> float:
        """Calculate total portfolio market value."""
        if not self._market_data:
            return 0.0

        total = 0.0

        for symbol, quantity in positions.items():
            if quantity != 0:
                try:
                    price = self._market_data.get_current_price(symbol)
                    if price:
                        total += abs(quantity) * price
                except Exception as e:
                    logger.warning(f"Could not get price for {symbol}: {e}")

        return total

    def _get_cash_balance(self) -> float | None:
        """Get cash balance if available."""
        if not self._account:
            return None

        try:
            account_info = self._account.get_account()
            if account_info:
                if hasattr(account_info, "cash"):
                    return float(account_info.cash)
                if isinstance(account_info, dict):
                    cash = account_info.get("cash") or account_info.get("cash_balance")
                    return float(cash) if cash is not None else None
            return None
        except Exception as e:
            logger.warning(f"Could not get cash balance: {e}")
            return None
