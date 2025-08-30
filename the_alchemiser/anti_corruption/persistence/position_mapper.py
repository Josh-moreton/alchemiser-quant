"""Business Unit: utilities | Status: current

Anti-corruption layer for position persistence mapping.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.portfolio.domain.entities.position import Position
from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


class PositionMapper:
    """Maps between Position domain entities and DynamoDB items."""
    
    def position_to_dynamodb_item(self, position: Position) -> dict[str, Any]:
        """Convert Position entity to DynamoDB item.
        
        Args:
            position: Position domain entity
            
        Returns:
            DynamoDB item dictionary
        """
        return {
            "symbol": position.symbol.value,
            "quantity": str(position.quantity),
            "average_cost_amount": str(position.average_cost.amount),
            "average_cost_currency": position.average_cost.currency,
            "current_value_amount": str(position.current_value.amount),
            "current_value_currency": position.current_value.currency,
            "unrealized_pnl_amount": str(position.unrealized_pnl.amount),
            "unrealized_pnl_currency": position.unrealized_pnl.currency,
            "market_price_amount": str(position.market_price.amount),
            "market_price_currency": position.market_price.currency,
            "last_updated": position.last_updated.isoformat(),
            "version": getattr(position, 'version', 1)
        }
    
    def dynamodb_item_to_position(self, item: dict[str, Any]) -> Position:
        """Convert DynamoDB item to Position entity.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            Position domain entity
            
        Raises:
            ValueError: Invalid item data
        """
        try:
            position = Position(
                symbol=Symbol(item["symbol"]),
                quantity=Decimal(item["quantity"]),
                average_cost=Money(
                    Decimal(item["average_cost_amount"]),
                    item["average_cost_currency"]
                ),
                current_value=Money(
                    Decimal(item["current_value_amount"]),
                    item["current_value_currency"]
                ),
                unrealized_pnl=Money(
                    Decimal(item["unrealized_pnl_amount"]),
                    item["unrealized_pnl_currency"]
                ),
                market_price=Money(
                    Decimal(item["market_price_amount"]),
                    item["market_price_currency"]
                ),
                last_updated=datetime.fromisoformat(item["last_updated"])
            )
            
            # Add version for optimistic locking if present
            if "version" in item:
                setattr(position, 'version', item["version"])
            
            return position
            
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid DynamoDB item for position: {e}") from e