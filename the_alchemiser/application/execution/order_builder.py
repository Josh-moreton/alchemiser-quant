"""Decimal-safe order builder with normalized construction logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Any, Dict

from the_alchemiser.application.execution.error_taxonomy import (
    OrderError,
    OrderErrorCode,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO


@dataclass(frozen=True)
class OrderBuildingRules:
    """Rules for order construction and normalization."""

    # Quantity rounding
    min_quantity_increment: Decimal = Decimal("0.000001")  # 6 decimal places
    fractional_rounding: str = "ROUND_DOWN"  # Conservative rounding for quantities
    
    # Price rounding
    min_price_increment: Decimal = Decimal("0.01")  # 2 decimal places (cents)
    price_rounding: str = "ROUND_HALF_UP"  # Standard rounding for prices
    
    # Notional rounding
    min_notional_increment: Decimal = Decimal("0.01")  # 2 decimal places
    notional_rounding: str = "ROUND_HALF_UP"
    
    # Safety margins
    buying_power_safety_margin: Decimal = Decimal("0.01")  # 1% safety margin
    quantity_safety_factor: Decimal = Decimal("0.99")  # 99% of calculated quantity
    
    # Validation thresholds
    min_notional_value: Decimal = Decimal("1.00")  # $1 minimum
    max_fractional_precision: int = 6  # Maximum decimal places for quantities


@dataclass(frozen=True)
class NormalizedOrderParams:
    """Normalized and validated order parameters."""

    symbol: Symbol
    side: str
    quantity: Quantity
    order_type: str
    time_in_force: str
    limit_price: Money | None = None
    estimated_notional: Money | None = None
    client_order_id: str | None = None
    
    # Derived values
    is_fractional: bool = False
    original_quantity: Quantity | None = None
    safety_adjusted: bool = False


class DecimalSafeOrderBuilder:
    """Builder for creating normalized, decimal-safe orders."""

    def __init__(self, rules: OrderBuildingRules | None = None) -> None:
        """Initialize the order builder."""
        self.rules = rules or OrderBuildingRules()
        self.logger = logging.getLogger(__name__)

    def build_market_order(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity | None = None,
        notional: Money | None = None,
        current_price: Money | None = None,
        client_order_id: str | None = None,
    ) -> tuple[NormalizedOrderParams | None, OrderError | None]:
        """Build a normalized market order."""
        if quantity is None and notional is None:
            return None, OrderError.create(
                OrderErrorCode.MISSING_REQUIRED_FIELD,
                "Either quantity or notional must be specified for market order",
                {"symbol": str(symbol.value), "side": side},
            )

        # Convert notional to quantity if needed
        if quantity is None and notional is not None:
            if current_price is None or current_price.amount <= 0:
                return None, OrderError.create(
                    OrderErrorCode.INVALID_PRICE,
                    "Current price required to convert notional to quantity",
                    {"symbol": str(symbol.value), "notional": str(notional.amount)},
                )
            
            # Calculate quantity with safety margin
            raw_quantity = notional.amount / current_price.amount
            safe_quantity = raw_quantity * self.rules.quantity_safety_factor
            quantity = self._normalize_quantity(safe_quantity)
            
            if quantity.value <= 0:
                return None, OrderError.create(
                    OrderErrorCode.INVALID_QUANTITY,
                    "Calculated quantity too small after normalization",
                    {
                        "symbol": str(symbol.value),
                        "notional": str(notional.amount),
                        "price": str(current_price.amount),
                        "calculated_quantity": str(safe_quantity),
                    },
                )

        # Normalize quantity
        if quantity is not None:
            normalized_quantity = self._normalize_quantity(quantity.value)
            is_fractional = self._is_fractional_quantity(normalized_quantity.value)
        
        # Estimate notional if not provided
        estimated_notional = notional
        if estimated_notional is None and current_price is not None:
            estimated_notional = Money(normalized_quantity.value * current_price.amount, "USD")

        # Validate minimum notional
        if estimated_notional and estimated_notional.amount < self.rules.min_notional_value:
            return None, OrderError.create(
                OrderErrorCode.INVALID_QUANTITY,
                f"Order value ${estimated_notional.amount} below minimum ${self.rules.min_notional_value}",
                {
                    "symbol": str(symbol.value),
                    "estimated_notional": str(estimated_notional.amount),
                    "minimum": str(self.rules.min_notional_value),
                },
            )

        return NormalizedOrderParams(
            symbol=symbol,
            side=side.upper(),
            quantity=normalized_quantity,
            order_type="market",
            time_in_force="day",
            limit_price=None,
            estimated_notional=estimated_notional,
            client_order_id=client_order_id,
            is_fractional=is_fractional,
            original_quantity=quantity if quantity != normalized_quantity else None,
            safety_adjusted=quantity != normalized_quantity,
        ), None

    def build_limit_order(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity,
        limit_price: Money,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> tuple[NormalizedOrderParams | None, OrderError | None]:
        """Build a normalized limit order."""
        # Normalize inputs
        normalized_quantity = self._normalize_quantity(quantity.value)
        normalized_price = self._normalize_price(limit_price.amount)
        
        if normalized_quantity.value <= 0:
            return None, OrderError.create(
                OrderErrorCode.INVALID_QUANTITY,
                "Quantity must be positive after normalization",
                {
                    "symbol": str(symbol.value),
                    "original_quantity": str(quantity.value),
                    "normalized_quantity": str(normalized_quantity.value),
                },
            )

        if normalized_price.amount <= 0:
            return None, OrderError.create(
                OrderErrorCode.INVALID_PRICE,
                "Limit price must be positive after normalization",
                {
                    "symbol": str(symbol.value),
                    "original_price": str(limit_price.amount),
                    "normalized_price": str(normalized_price.amount),
                },
            )

        # Calculate estimated notional
        estimated_notional = Money(normalized_quantity.value * normalized_price.amount, "USD")
        
        # Validate minimum notional
        if estimated_notional.amount < self.rules.min_notional_value:
            return None, OrderError.create(
                OrderErrorCode.INVALID_QUANTITY,
                f"Order value ${estimated_notional.amount} below minimum ${self.rules.min_notional_value}",
                {
                    "symbol": str(symbol.value),
                    "quantity": str(normalized_quantity.value),
                    "price": str(normalized_price.amount),
                    "estimated_notional": str(estimated_notional.amount),
                    "minimum": str(self.rules.min_notional_value),
                },
            )

        is_fractional = self._is_fractional_quantity(normalized_quantity.value)

        return NormalizedOrderParams(
            symbol=symbol,
            side=side.upper(),
            quantity=normalized_quantity,
            order_type="limit",
            time_in_force=time_in_force.lower(),
            limit_price=normalized_price,
            estimated_notional=estimated_notional,
            client_order_id=client_order_id,
            is_fractional=is_fractional,
            original_quantity=quantity if quantity.value != normalized_quantity.value else None,
            safety_adjusted=False,
        ), None

    def build_aggressive_limit_order(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity,
        bid: Money,
        ask: Money,
        aggression_cents: Decimal = Decimal("0.01"),
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> tuple[NormalizedOrderParams | None, OrderError | None]:
        """Build an aggressive marketable limit order."""
        # Calculate aggressive price
        if side.upper() == "BUY":
            # Buy at ask + aggression
            aggressive_price = ask.amount + aggression_cents
        else:
            # Sell at bid - aggression
            aggressive_price = bid.amount - aggression_cents
            
        # Ensure price doesn't go negative
        if aggressive_price <= 0:
            aggressive_price = self.rules.min_price_increment

        limit_price = Money(aggressive_price, "USD")
        
        return self.build_limit_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=limit_price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
        )

    def build_pegged_order(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity,
        reference_price: Money,
        offset_cents: Decimal,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> tuple[NormalizedOrderParams | None, OrderError | None]:
        """Build a pegged order with price offset."""
        pegged_price = Money(reference_price.amount + offset_cents, "USD")
        
        # Ensure price is positive
        if pegged_price.amount <= 0:
            pegged_price = Money(self.rules.min_price_increment, "USD")

        return self.build_limit_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=pegged_price,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
        )

    def convert_to_dto(self, params: NormalizedOrderParams) -> OrderRequestDTO:
        """Convert normalized parameters to OrderRequestDTO."""
        return OrderRequestDTO(
            symbol=str(params.symbol.value),
            side=params.side.lower(),  # type: ignore[arg-type]
            quantity=params.quantity.value,
            order_type=params.order_type,  # type: ignore[arg-type]
            time_in_force=params.time_in_force,  # type: ignore[arg-type]
            limit_price=params.limit_price.amount if params.limit_price else None,
            client_order_id=params.client_order_id,
        )

    def apply_quantity_reduction(
        self,
        params: NormalizedOrderParams,
        reduction_factor: Decimal,
    ) -> NormalizedOrderParams:
        """Apply a reduction factor to the order quantity."""
        if reduction_factor <= 0 or reduction_factor > 1:
            raise ValueError("Reduction factor must be between 0 and 1")

        new_quantity = self._normalize_quantity(params.quantity.value * reduction_factor)
        
        # Recalculate estimated notional
        new_estimated_notional = None
        if params.limit_price:
            new_estimated_notional = Money(new_quantity.value * params.limit_price.amount, "USD")
        elif params.estimated_notional:
            # Proportional reduction
            new_estimated_notional = Money(params.estimated_notional.amount * reduction_factor, "USD")

        return NormalizedOrderParams(
            symbol=params.symbol,
            side=params.side,
            quantity=new_quantity,
            order_type=params.order_type,
            time_in_force=params.time_in_force,
            limit_price=params.limit_price,
            estimated_notional=new_estimated_notional,
            client_order_id=params.client_order_id,
            is_fractional=self._is_fractional_quantity(new_quantity.value),
            original_quantity=params.original_quantity or params.quantity,
            safety_adjusted=True,
        )

    def _normalize_quantity(self, quantity: Decimal) -> Quantity:
        """Normalize quantity with proper rounding."""
        rounding = getattr(Decimal, self.rules.fractional_rounding, ROUND_DOWN)
        normalized = quantity.quantize(self.rules.min_quantity_increment, rounding=rounding)
        return Quantity(max(Decimal("0"), normalized))

    def _normalize_price(self, price: Decimal) -> Money:
        """Normalize price with proper rounding."""
        rounding = getattr(Decimal, self.rules.price_rounding, ROUND_HALF_UP)
        normalized = price.quantize(self.rules.min_price_increment, rounding=rounding)
        return Money(max(Decimal("0"), normalized), "USD")

    def _is_fractional_quantity(self, quantity: Decimal) -> bool:
        """Check if quantity is fractional (not a whole number)."""
        return quantity % 1 != 0

    def calculate_price_improvement(
        self,
        side: str,
        current_bid: Money,
        current_ask: Money,
        improvement_levels: int = 1,
        tick_size: Decimal = Decimal("0.01"),
    ) -> Money:
        """Calculate improved price for better execution probability."""
        if side.upper() == "BUY":
            # Improve by stepping into the spread
            improvement = tick_size * improvement_levels
            improved_price = current_ask.amount + improvement
        else:
            # Improve by stepping into the spread
            improvement = tick_size * improvement_levels
            improved_price = current_bid.amount - improvement
            
        # Ensure price doesn't go negative
        if improved_price <= 0:
            improved_price = tick_size

        return self._normalize_price(improved_price)

    def log_building_details(
        self,
        original_params: Dict[str, Any],
        normalized_params: NormalizedOrderParams,
    ) -> None:
        """Log detailed order building information."""
        self.logger.info(
            "order_built",
            extra={
                "symbol": str(normalized_params.symbol.value),
                "side": normalized_params.side,
                "order_type": normalized_params.order_type,
                "quantity": str(normalized_params.quantity.value),
                "limit_price": str(normalized_params.limit_price.amount) if normalized_params.limit_price else None,
                "estimated_notional": str(normalized_params.estimated_notional.amount) if normalized_params.estimated_notional else None,
                "is_fractional": normalized_params.is_fractional,
                "safety_adjusted": normalized_params.safety_adjusted,
                "original_params": original_params,
            },
        )