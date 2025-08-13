"""Pure position delta calculation logic."""

from decimal import Decimal

from the_alchemiser.domain.portfolio.position.position_delta import PositionDelta


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
        elif delta < 0:
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
        else:
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
