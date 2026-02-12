"""Business Unit: shared | Status: current.

Per-strategy position service for the per-strategy books architecture.

Queries the trade ledger for a strategy's open lots and builds a
per-strategy portfolio snapshot for rebalance calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import boto3

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.portfolio_snapshot import (
    MarginInfo,
    PortfolioSnapshot,
)
from the_alchemiser.shared.schemas.strategy_lot import StrategyLot

logger = get_logger(__name__)

MODULE_NAME = "shared.services.strategy_position_service"


@dataclass(frozen=True)
class StrategyPosition:
    """A strategy's aggregated position in a single symbol."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal


class StrategyPositionService:
    """Service for querying per-strategy positions from the trade ledger.

    Uses GSI5 (StrategyLotsIndex) to query open lots per strategy,
    then aggregates into per-symbol positions.
    """

    def __init__(self, table_name: str) -> None:
        """Initialize with the trade ledger DynamoDB table name.

        Args:
            table_name: DynamoDB table name for the trade ledger.

        """
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def get_open_positions(self, strategy_id: str) -> dict[str, StrategyPosition]:
        """Query open lots for a strategy and aggregate into positions.

        Args:
            strategy_id: Strategy identifier (e.g., '1-KMLM').

        Returns:
            Dictionary mapping symbol to aggregated StrategyPosition.

        """
        try:
            # Query GSI5 for all open lots belonging to this strategy
            # GSI5PK = STRATEGY_LOTS#{strategy_name}, GSI5SK begins_with OPEN#
            response = self._table.query(
                IndexName="GSI5-StrategyLotsIndex",
                KeyConditionExpression="GSI5PK = :pk AND begins_with(GSI5SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"STRATEGY_LOTS#{strategy_id}",
                    ":sk_prefix": "OPEN#",
                },
                ScanIndexForward=True,
            )

            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self._table.query(
                    IndexName="GSI5-StrategyLotsIndex",
                    KeyConditionExpression="GSI5PK = :pk AND begins_with(GSI5SK, :sk_prefix)",
                    ExpressionAttributeValues={
                        ":pk": f"STRATEGY_LOTS#{strategy_id}",
                        ":sk_prefix": "OPEN#",
                    },
                    ScanIndexForward=True,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            # Aggregate lots into per-symbol positions
            positions: dict[str, StrategyPosition] = {}
            symbol_qty: dict[str, Decimal] = {}
            symbol_cost: dict[str, Decimal] = {}

            for item in items:
                try:
                    lot = StrategyLot.from_dynamodb_item(item)
                    if lot.remaining_qty <= Decimal("0"):
                        continue

                    symbol = lot.symbol.upper()
                    if symbol not in symbol_qty:
                        symbol_qty[symbol] = Decimal("0")
                        symbol_cost[symbol] = Decimal("0")

                    symbol_qty[symbol] += lot.remaining_qty
                    symbol_cost[symbol] += lot.remaining_qty * lot.entry_price

                except Exception as e:
                    logger.warning(
                        f"Failed to parse lot item: {e}",
                        extra={
                            "strategy_id": strategy_id,
                            "item_pk": item.get("PK", "unknown"),
                        },
                    )

            for symbol in symbol_qty:
                qty = symbol_qty[symbol]
                avg_cost = symbol_cost[symbol] / qty if qty > Decimal("0") else Decimal("0")
                positions[symbol] = StrategyPosition(
                    symbol=symbol,
                    quantity=qty,
                    avg_cost=avg_cost,
                )

            logger.info(
                "Retrieved strategy positions",
                extra={
                    "strategy_id": strategy_id,
                    "lot_count": len(items),
                    "position_count": len(positions),
                    "symbols": sorted(positions.keys()),
                },
            )

            return positions

        except Exception as e:
            logger.error(
                "Failed to query strategy positions - failing closed",
                extra={
                    "strategy_id": strategy_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            # Fail closed: propagate error so strategy does not trade
            # with incorrect position state (could double exposure)
            from the_alchemiser.shared.errors.exceptions import PortfolioError

            raise PortfolioError(
                f"Cannot read positions for strategy '{strategy_id}': {e}",
                module="strategy_position_service",
                operation="get_strategy_positions",
                correlation_id=strategy_id,
            ) from e

    def build_portfolio_snapshot(
        self,
        strategy_id: str,
        strategy_capital: Decimal,
        current_prices: dict[str, Decimal],
        margin_info: MarginInfo | None = None,
    ) -> PortfolioSnapshot:
        """Build a portfolio snapshot for a strategy's book.

        Args:
            strategy_id: Strategy identifier.
            strategy_capital: Total capital allocated to this strategy.
            current_prices: Current market prices for relevant symbols.
            margin_info: Optional margin info from the account.

        Returns:
            PortfolioSnapshot for this strategy's positions.

        """
        open_positions = self.get_open_positions(strategy_id)

        # Build position quantities and prices dicts for the snapshot
        positions: dict[str, Decimal] = {}
        prices: dict[str, Decimal] = {}
        total_position_value = Decimal("0")

        for symbol, pos in open_positions.items():
            if pos.quantity <= Decimal("0"):
                continue

            price = current_prices.get(symbol)
            if price is None or price <= Decimal("0"):
                logger.warning(
                    f"No current price for {symbol}, using avg_cost as fallback",
                    extra={
                        "strategy_id": strategy_id,
                        "symbol": symbol,
                        "quantity": str(pos.quantity),
                        "avg_cost": str(pos.avg_cost),
                    },
                )
                price = pos.avg_cost

            positions[symbol] = pos.quantity
            prices[symbol] = price
            total_position_value += pos.quantity * price

        # Also include prices for symbols we don't hold (for snapshot validation)
        for symbol, price in current_prices.items():
            if symbol not in prices and price > Decimal("0"):
                prices[symbol] = price

        cash = strategy_capital - total_position_value

        # Defensive guard: warn if cash goes negative (position value exceeds allocated capital)
        if cash < Decimal("0"):
            logger.warning(
                "Negative implied cash for strategy - positions exceed allocated capital",
                extra={
                    "strategy_id": strategy_id,
                    "cash": str(cash),
                    "strategy_capital": str(strategy_capital),
                    "total_position_value": str(total_position_value),
                    "excess_value": str(abs(cash)),
                },
            )

        total_value = strategy_capital

        logger.info(
            "Built strategy portfolio snapshot",
            extra={
                "strategy_id": strategy_id,
                "strategy_capital": str(strategy_capital),
                "total_position_value": str(total_position_value),
                "cash": str(cash),
                "position_count": len(positions),
            },
        )

        return PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
            margin=margin_info if margin_info else MarginInfo(),
        )
