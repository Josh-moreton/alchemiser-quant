#!/usr/bin/env python3
"""Business Unit: execution | Status: current..

        Args:
            order_id: Order identifier
            executed_price: Actual execution price
            executed_quantity: Actual executed quantity
            execution_timestamp: When execution occurred

        Returns:
            SlippageAnalysis result or None if no intended price recorded

        """
        if order_id not in self._intended_prices:
            self.logger.warning(f"No intended price recorded for order {order_id}")
            return None

        intended_data = self._intended_prices[order_id]
        intended_price = intended_data["intended_price"]
        symbol = intended_data["symbol"]
        side = intended_data["side"]

        # Calculate slippage
        slippage_analysis = self._calculate_slippage(
            order_id=order_id,
            symbol=symbol,
            side=side,
            intended_price=intended_price,
            executed_price=executed_price,
            quantity=executed_quantity,
            execution_timestamp=execution_timestamp,
        )

        # Store the analysis
        self._slippage_results.append(slippage_analysis)

        self.logger.info(
            f"💰 Slippage analysis for {order_id}: {slippage_analysis.slippage_bps:.1f} bps "
            f"({'favorable' if slippage_analysis.is_favorable else 'unfavorable'})"
        )

        return slippage_analysis

    def _calculate_slippage(
        self,
        order_id: str,
        symbol: str,
        side: str,
        intended_price: Decimal,
        executed_price: Decimal,
        quantity: Decimal,
        execution_timestamp: float,
    ) -> SlippageAnalysis:
        """Calculate detailed slippage metrics.

        Args:
            order_id: Order identifier
            symbol: Trading symbol
            side: Order side
            intended_price: Intended execution price
            executed_price: Actual execution price
            quantity: Executed quantity
            execution_timestamp: Execution timestamp

        Returns:
            Complete slippage analysis

        """
        # Calculate raw slippage (positive = unfavorable, negative = favorable)
        if side.upper() == "BUY":
            # For buys: paying more than intended is unfavorable slippage
            raw_slippage = executed_price - intended_price
        else:
            # For sells: receiving less than intended is unfavorable slippage
            raw_slippage = intended_price - executed_price

        # Convert to basis points (bps): 1 bps = 0.01% = 0.0001
        if intended_price > Decimal("0"):
            slippage_bps = (raw_slippage / intended_price) * Decimal("10000")
        else:
            slippage_bps = Decimal("0")

        # Calculate dollar impact
        slippage_dollars = raw_slippage * quantity

        # Determine if slippage was favorable (negative slippage is good)
        is_favorable = raw_slippage < Decimal("0")

        return SlippageAnalysis(
            order_id=order_id,
            symbol=symbol,
            side=side,
            intended_price=intended_price,
            executed_price=executed_price,
            quantity=quantity,
            slippage_bps=slippage_bps,
            slippage_dollars=slippage_dollars,
            is_favorable=is_favorable,
            execution_timestamp=execution_timestamp,
        )

    def get_slippage_summary(self) -> dict[str, Any]:
        """Get summary statistics for all slippage analyses.

        Returns:
            Dictionary containing slippage summary metrics

        """
        if not self._slippage_results:
            return {
                "total_executions": 0,
                "average_slippage_bps": 0.0,
                "favorable_executions": 0,
                "unfavorable_executions": 0,
                "total_slippage_cost": 0.0,
            }

        total_executions = len(self._slippage_results)
        favorable_count = sum(1 for result in self._slippage_results if result.is_favorable)
        unfavorable_count = total_executions - favorable_count

        # Calculate average slippage in bps
        total_slippage_bps = sum(float(result.slippage_bps) for result in self._slippage_results)
        avg_slippage_bps = total_slippage_bps / total_executions

        # Calculate total dollar cost
        total_slippage_cost = sum(
            float(result.slippage_dollars) for result in self._slippage_results
        )

        return {
            "total_executions": total_executions,
            "average_slippage_bps": avg_slippage_bps,
            "favorable_executions": favorable_count,
            "unfavorable_executions": unfavorable_count,
            "favorable_rate": favorable_count / total_executions,
            "total_slippage_cost": total_slippage_cost,
            "average_slippage_cost_per_execution": total_slippage_cost / total_executions,
        }

    def get_slippage_by_symbol(self) -> dict[str, dict[str, Any]]:
        """Get slippage analysis grouped by symbol.

        Returns:
            Dictionary mapping symbols to their slippage statistics

        """
        symbol_data: dict[str, list[SlippageAnalysis]] = {}

        for result in self._slippage_results:
            if result.symbol not in symbol_data:
                symbol_data[result.symbol] = []
            symbol_data[result.symbol].append(result)

        symbol_summaries = {}
        for symbol, results in symbol_data.items():
            total = len(results)
            favorable = sum(1 for r in results if r.is_favorable)
            avg_bps = sum(float(r.slippage_bps) for r in results) / total
            total_cost = sum(float(r.slippage_dollars) for r in results)

            symbol_summaries[symbol] = {
                "executions": total,
                "average_slippage_bps": avg_bps,
                "favorable_rate": favorable / total,
                "total_cost": total_cost,
            }

        return symbol_summaries

    def export_slippage_data(self) -> dict[str, Any]:
        """Export all slippage data for external analysis.

        Returns:
            Complete slippage dataset with metadata

        """
        return {
            "timestamp": int(__import__("time").time()),
            "summary": self.get_slippage_summary(),
            "by_symbol": self.get_slippage_by_symbol(),
            "raw_data": [
                {
                    "order_id": result.order_id,
                    "symbol": result.symbol,
                    "side": result.side,
                    "intended_price": float(result.intended_price),
                    "executed_price": float(result.executed_price),
                    "quantity": float(result.quantity),
                    "slippage_bps": float(result.slippage_bps),
                    "slippage_dollars": float(result.slippage_dollars),
                    "is_favorable": result.is_favorable,
                    "execution_timestamp": result.execution_timestamp,
                }
                for result in self._slippage_results
            ],
        }

    def reset_data(self) -> None:
        """Reset all stored slippage data."""
        self._slippage_results.clear()
        self._intended_prices.clear()
        self.logger.info("Slippage analyzer data reset")


# NOTE: Removed global singleton accessor; prefer dependency injection.


def create_slippage_analyzer() -> SlippageAnalyzer:
    """Create a new slippage analyzer instance.

    Construct once in the application layer and inject where required
    (e.g., observers, execution managers). Avoid module-level singletons
    to maintain testability and domain purity.
    """
    return SlippageAnalyzer()
