"""Business Unit: portfolio assessment & management; Status: current.

Pure position delta calculation logic.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.portfolio.domain.position.position_delta import PositionDelta


class PositionAnalyzer:
    """Pure position delta calculation logic.

    This class contains no side effects and only performs calculations
    to determine how to adjust positions from current to target quantities.
    """

    def calculate_position_delta(
        self, symbol: str, current_qty: Decimal, target_qty: Decimal
    ) -> PositionDelta:
        """Calculate minimal order needed to reach target position.

        Args:
            symbol: The symbol to analyze
            current_qty: Current position quantity
            target_qty: Target position quantity

        Returns:
            PositionDelta object with calculated action and quantity

        """
        delta = target_qty - current_qty

        if abs(delta) < Decimal("0.01"):
            return PositionDelta(
                symbol=symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta=delta,
                action="no_change",
                quantity=Decimal("0"),
                message=f"No rebalancing needed for {symbol}: {current_qty} ≈ {target_qty}",
            )
        if delta < 0:
            sell_qty = abs(delta).quantize(Decimal("0.000001"))
            return PositionDelta(
                symbol=symbol,
                current_qty=current_qty,
                target_qty=target_qty,
                delta=delta,
                action="sell_excess",
                quantity=sell_qty,
                message=f"Rebalancing {symbol}: selling {sell_qty} shares (reducing {current_qty} → {target_qty})",
            )
        buy_qty = delta.quantize(Decimal("0.000001"))
        return PositionDelta(
            symbol=symbol,
            current_qty=current_qty,
            target_qty=target_qty,
            delta=delta,
            action="buy_more",
            quantity=buy_qty,
            message=f"Rebalancing {symbol}: buying {buy_qty} shares (increasing {current_qty} → {target_qty})",
        )

    def calculate_position_deltas(
        self, current_quantities: dict[str, Decimal], target_quantities: dict[str, Decimal]
    ) -> dict[str, PositionDelta]:
        """Calculate position deltas for multiple symbols.

        Args:
            current_quantities: Dictionary mapping symbols to current quantities
            target_quantities: Dictionary mapping symbols to target quantities

        Returns:
            Dictionary mapping symbols to PositionDelta objects

        """
        all_symbols = set(current_quantities.keys()) | set(target_quantities.keys())

        return {
            symbol: self.calculate_position_delta(
                symbol=symbol,
                current_qty=current_quantities.get(symbol, Decimal("0")),
                target_qty=target_quantities.get(symbol, Decimal("0")),
            )
            for symbol in all_symbols
        }

    def filter_actionable_deltas(
        self, position_deltas: dict[str, PositionDelta]
    ) -> dict[str, PositionDelta]:
        """Filter to only position deltas that require action."""
        return {symbol: delta for symbol, delta in position_deltas.items() if delta.needs_action}

    def get_sell_deltas(
        self, position_deltas: dict[str, PositionDelta]
    ) -> dict[str, PositionDelta]:
        """Get position deltas that require selling."""
        return {symbol: delta for symbol, delta in position_deltas.items() if delta.is_sell}

    def get_buy_deltas(self, position_deltas: dict[str, PositionDelta]) -> dict[str, PositionDelta]:
        """Get position deltas that require buying."""
        return {symbol: delta for symbol, delta in position_deltas.items() if delta.is_buy}

    def analyze_all_positions(
        self, current_positions: dict[str, Decimal], target_positions: dict[str, Decimal]
    ) -> dict[str, PositionDelta]:
        """Analyze all positions and return position deltas.

        Args:
            current_positions: Dictionary mapping symbols to current position values
            target_positions: Dictionary mapping symbols to target position values

        Returns:
            Dictionary mapping symbols to PositionDelta objects

        """
        return self.calculate_position_deltas(current_positions, target_positions)

    def calculate_total_adjustments_needed(
        self, position_deltas: dict[str, PositionDelta]
    ) -> tuple[Decimal, Decimal]:
        """Calculate total sell and buy amounts needed.

        Args:
            position_deltas: Dictionary of position deltas

        Returns:
            Tuple of (total_sells, total_buys) as Decimal amounts

        """
        total_sells = sum(
            (delta.quantity_abs for delta in position_deltas.values() if delta.is_sell),
            Decimal("0"),
        )
        total_buys = sum(
            (delta.quantity_abs for delta in position_deltas.values() if delta.is_buy), Decimal("0")
        )

        return total_sells, total_buys

    def calculate_portfolio_turnover(
        self, position_deltas: dict[str, PositionDelta], portfolio_value: Decimal
    ) -> Decimal:
        """Calculate portfolio turnover from position deltas.

        Args:
            position_deltas: Dictionary of position deltas
            portfolio_value: Total portfolio value

        Returns:
            Portfolio turnover as a decimal percentage

        """
        if portfolio_value == 0:
            return Decimal("0")

        total_trade_value = sum(delta.quantity_abs for delta in position_deltas.values())
        return total_trade_value / portfolio_value

    def get_positions_to_sell(self, position_deltas: dict[str, PositionDelta]) -> list[str]:
        """Get list of symbols that need to be sold.

        Args:
            position_deltas: Dictionary of position deltas

        Returns:
            List of symbols requiring sell orders

        """
        return [symbol for symbol, delta in position_deltas.items() if delta.is_sell]

    def get_positions_to_buy(self, position_deltas: dict[str, PositionDelta]) -> list[str]:
        """Get list of symbols that need to be bought.

        Args:
            position_deltas: Dictionary of position deltas

        Returns:
            List of symbols requiring buy orders

        """
        return [symbol for symbol, delta in position_deltas.items() if delta.is_buy]
