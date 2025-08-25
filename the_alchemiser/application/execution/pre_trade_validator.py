"""Pre-trade validation and risk checks for order execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Protocol

from the_alchemiser.application.execution.error_taxonomy import (
    OrderError,
    OrderErrorCode,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


@dataclass(frozen=True)
class PreTradeValidationResult:
    """Result of pre-trade validation checks."""

    is_valid: bool
    errors: List[OrderError]
    warnings: List[str]
    approved_quantity: Quantity | None = None
    approved_notional: Money | None = None
    risk_score: Decimal = Decimal("0")


@dataclass(frozen=True)
class RiskLimits:
    """Risk limits configuration for pre-trade validation."""

    max_position_concentration: Decimal = Decimal("0.25")  # 25% max
    max_notional_per_order: Money = Money(Decimal("100000"), "USD")  # $100K max
    max_orders_per_day: int = 100
    min_buying_power_reserve: Decimal = Decimal("0.05")  # 5% reserve
    max_slippage_bps: Decimal = Decimal("50")  # 50 basis points
    max_spread_bps: Decimal = Decimal("100")  # 100 basis points


class TradingDataProvider(Protocol):
    """Protocol for trading data access."""

    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information."""
        ...

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        ...

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for symbol."""
        ...

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote."""
        ...


class PreTradeValidator:
    """Comprehensive pre-trade validation and risk management."""

    def __init__(
        self,
        data_provider: TradingDataProvider,
        risk_limits: RiskLimits | None = None,
    ) -> None:
        """Initialize the pre-trade validator."""
        self.data_provider = data_provider
        self.risk_limits = risk_limits or RiskLimits()
        self.logger = logging.getLogger(__name__)

    def validate_order(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity | None = None,
        notional: Money | None = None,
        limit_price: Money | None = None,
        strategy: str | None = None,
    ) -> PreTradeValidationResult:
        """Comprehensive pre-trade validation for an order."""
        errors: List[OrderError] = []
        warnings: List[str] = []
        risk_score = Decimal("0")

        # Basic validation
        basic_errors = self._validate_basic_parameters(symbol, side, quantity, notional)
        errors.extend(basic_errors)

        if errors:
            return PreTradeValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                risk_score=risk_score,
            )

        # Get account information
        try:
            account_info = self.data_provider.get_account_info()
        except Exception as e:
            errors.append(
                OrderError.create(
                    OrderErrorCode.SYSTEM_UNAVAILABLE,
                    f"Unable to retrieve account information: {e}",
                    {"symbol": str(symbol.value), "side": side},
                )
            )
            return PreTradeValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                risk_score=risk_score,
            )

        # Calculate effective quantity and notional
        if quantity is None and notional is not None:
            # Convert notional to quantity
            current_price = self.data_provider.get_current_price(str(symbol.value))
            if current_price is None or current_price <= 0:
                errors.append(
                    OrderError.create(
                        OrderErrorCode.INVALID_PRICE,
                        f"Unable to get valid price for {symbol.value}",
                        {"symbol": str(symbol.value)},
                        "Check market data connectivity or symbol validity",
                    )
                )
                return PreTradeValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    risk_score=risk_score,
                )
            
            calculated_quantity = notional.amount / Decimal(str(current_price))
            quantity = Quantity(calculated_quantity * Decimal("0.99"))  # 99% for safety
            
        elif notional is None and quantity is not None:
            # Calculate notional from quantity
            current_price = self.data_provider.get_current_price(str(symbol.value))
            if current_price is None or current_price <= 0:
                errors.append(
                    OrderError.create(
                        OrderErrorCode.INVALID_PRICE,
                        f"Unable to get valid price for {symbol.value}",
                        {"symbol": str(symbol.value)},
                    )
                )
                return PreTradeValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    risk_score=risk_score,
                )
            
            notional = Money(quantity.value * Decimal(str(current_price)), "USD")

        # Buying power validation
        buying_power_errors, bp_risk = self._validate_buying_power(
            account_info, notional, side
        )
        errors.extend(buying_power_errors)
        risk_score += bp_risk

        # Position concentration validation
        concentration_errors, conc_risk = self._validate_position_concentration(
            symbol, notional, side
        )
        errors.extend(concentration_errors)
        risk_score += conc_risk

        # Notional limits validation
        notional_errors, notional_risk = self._validate_notional_limits(notional)
        errors.extend(notional_errors)
        risk_score += notional_risk

        # Market conditions validation
        market_errors, market_warnings, market_risk = self._validate_market_conditions(
            symbol, limit_price
        )
        errors.extend(market_errors)
        warnings.extend(market_warnings)
        risk_score += market_risk

        # Price validation if limit order
        if limit_price is not None:
            price_errors, price_warnings = self._validate_limit_price(symbol, side, limit_price)
            errors.extend(price_errors)
            warnings.extend(price_warnings)

        is_valid = len(errors) == 0
        
        return PreTradeValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            approved_quantity=quantity if is_valid else None,
            approved_notional=notional if is_valid else None,
            risk_score=risk_score,
        )

    def _validate_basic_parameters(
        self,
        symbol: Symbol,
        side: str,
        quantity: Quantity | None,
        notional: Money | None,
    ) -> List[OrderError]:
        """Validate basic order parameters."""
        errors: List[OrderError] = []

        # Symbol validation
        if not symbol.value or len(symbol.value) > 10:
            errors.append(
                OrderError.create(
                    OrderErrorCode.INVALID_SYMBOL,
                    f"Invalid symbol: {symbol.value}",
                    {"symbol": str(symbol.value)},
                )
            )

        # Side validation
        if side.upper() not in ["BUY", "SELL"]:
            errors.append(
                OrderError.create(
                    OrderErrorCode.INVALID_QUANTITY,
                    f"Invalid side: {side}",
                    {"side": side},
                )
            )

        # Quantity/notional validation
        if quantity is None and notional is None:
            errors.append(
                OrderError.create(
                    OrderErrorCode.MISSING_REQUIRED_FIELD,
                    "Either quantity or notional must be specified",
                    {"quantity": quantity, "notional": notional},
                )
            )
        elif quantity is not None and quantity.value <= 0:
            errors.append(
                OrderError.create(
                    OrderErrorCode.INVALID_QUANTITY,
                    f"Quantity must be positive: {quantity.value}",
                    {"quantity": str(quantity.value)},
                )
            )
        elif notional is not None and notional.amount <= 0:
            errors.append(
                OrderError.create(
                    OrderErrorCode.INVALID_QUANTITY,
                    f"Notional must be positive: {notional.amount}",
                    {"notional": str(notional.amount)},
                )
            )

        return errors

    def _validate_buying_power(
        self, account_info: Dict[str, Any], notional: Money | None, side: str
    ) -> tuple[List[OrderError], Decimal]:
        """Validate buying power sufficiency."""
        errors: List[OrderError] = []
        risk_score = Decimal("0")

        if side.upper() != "BUY" or notional is None:
            return errors, risk_score

        buying_power = Decimal(str(account_info.get("buying_power", 0)))
        required_reserve = buying_power * self.risk_limits.min_buying_power_reserve
        available_power = buying_power - required_reserve

        if notional.amount > available_power:
            errors.append(
                OrderError.create(
                    OrderErrorCode.INSUFFICIENT_BUYING_POWER,
                    f"Insufficient buying power: need {notional.amount}, have {available_power}",
                    {
                        "required": str(notional.amount),
                        "available": str(available_power),
                        "total_buying_power": str(buying_power),
                        "reserve": str(required_reserve),
                    },
                    "Reduce order size or increase account balance",
                )
            )
        elif notional.amount > available_power * Decimal("0.8"):
            # High utilization warning
            risk_score += Decimal("20")

        return errors, risk_score

    def _validate_position_concentration(
        self, symbol: Symbol, notional: Money | None, side: str
    ) -> tuple[List[OrderError], Decimal]:
        """Validate position concentration limits."""
        errors: List[OrderError] = []
        risk_score = Decimal("0")

        if notional is None:
            return errors, risk_score

        try:
            account_info = self.data_provider.get_account_info()
            portfolio_value = Decimal(str(account_info.get("portfolio_value", 0)))
            
            if portfolio_value <= 0:
                return errors, risk_score

            # Get current position in this symbol
            positions = self.data_provider.get_positions()
            current_position_value = Decimal("0")
            
            for position in positions:
                if position.get("symbol") == symbol.value:
                    market_value = Decimal(str(position.get("market_value", 0)))
                    current_position_value += abs(market_value)

            # Calculate new position value after order
            if side.upper() == "BUY":
                new_position_value = current_position_value + notional.amount
            else:
                new_position_value = max(Decimal("0"), current_position_value - notional.amount)

            # Check concentration limit
            concentration = new_position_value / portfolio_value
            max_concentration = self.risk_limits.max_position_concentration

            if concentration > max_concentration:
                errors.append(
                    OrderError.create(
                        OrderErrorCode.CONCENTRATION_LIMIT_EXCEEDED,
                        f"Position concentration {concentration:.1%} exceeds limit {max_concentration:.1%}",
                        {
                            "symbol": str(symbol.value),
                            "concentration": str(concentration),
                            "limit": str(max_concentration),
                            "new_position_value": str(new_position_value),
                            "portfolio_value": str(portfolio_value),
                        },
                        f"Reduce allocation to stay under {max_concentration:.1%} limit",
                    )
                )
            elif concentration > max_concentration * Decimal("0.8"):
                # High concentration warning
                risk_score += Decimal("15")

        except Exception as e:
            self.logger.warning(f"Unable to validate position concentration: {e}")
            risk_score += Decimal("10")

        return errors, risk_score

    def _validate_notional_limits(self, notional: Money | None) -> tuple[List[OrderError], Decimal]:
        """Validate notional amount limits."""
        errors: List[OrderError] = []
        risk_score = Decimal("0")

        if notional is None:
            return errors, risk_score

        if notional.amount > self.risk_limits.max_notional_per_order.amount:
            errors.append(
                OrderError.create(
                    OrderErrorCode.NOTIONAL_LIMIT_EXCEEDED,
                    f"Order size {notional.amount} exceeds limit {self.risk_limits.max_notional_per_order.amount}",
                    {
                        "notional": str(notional.amount),
                        "limit": str(self.risk_limits.max_notional_per_order.amount),
                    },
                    f"Reduce order size to under {self.risk_limits.max_notional_per_order.amount}",
                )
            )
        elif notional.amount > self.risk_limits.max_notional_per_order.amount * Decimal("0.8"):
            # Large order warning
            risk_score += Decimal("10")

        return errors, risk_score

    def _validate_market_conditions(
        self, symbol: Symbol, limit_price: Money | None
    ) -> tuple[List[OrderError], List[str], Decimal]:
        """Validate current market conditions."""
        errors: List[OrderError] = []
        warnings: List[str] = []
        risk_score = Decimal("0")

        try:
            quote = self.data_provider.get_latest_quote(str(symbol.value))
            if quote is None:
                warnings.append(f"No quote data available for {symbol.value}")
                risk_score += Decimal("5")
                return errors, warnings, risk_score

            bid, ask = quote
            if bid <= 0 or ask <= 0:
                warnings.append(f"Invalid quote data for {symbol.value}")
                risk_score += Decimal("5")
                return errors, warnings, risk_score

            # Calculate spread
            spread = ask - bid
            mid_price = (bid + ask) / 2
            spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0

            # Check spread limits
            if spread_bps > float(self.risk_limits.max_spread_bps):
                errors.append(
                    OrderError.create(
                        OrderErrorCode.WIDE_SPREAD,
                        f"Spread {spread_bps:.1f} bps exceeds limit {self.risk_limits.max_spread_bps} bps",
                        {
                            "symbol": str(symbol.value),
                            "spread_bps": str(spread_bps),
                            "limit_bps": str(self.risk_limits.max_spread_bps),
                            "bid": str(bid),
                            "ask": str(ask),
                        },
                        "Wait for spread to narrow or use market order",
                    )
                )
            elif spread_bps > float(self.risk_limits.max_spread_bps) * 0.8:
                warnings.append(f"Wide spread detected: {spread_bps:.1f} bps")
                risk_score += Decimal("8")

        except Exception as e:
            self.logger.warning(f"Unable to validate market conditions for {symbol.value}: {e}")
            risk_score += Decimal("5")

        return errors, warnings, risk_score

    def _validate_limit_price(
        self, symbol: Symbol, side: str, limit_price: Money
    ) -> tuple[List[OrderError], List[str]]:
        """Validate limit price against current market."""
        errors: List[OrderError] = []
        warnings: List[str] = []

        try:
            quote = self.data_provider.get_latest_quote(str(symbol.value))
            if quote is None:
                warnings.append(f"Cannot validate limit price - no quote data for {symbol.value}")
                return errors, warnings

            bid, ask = quote
            mid_price = (bid + ask) / 2

            # Check if price is too far from market
            price_diff_pct = abs(float(limit_price.amount) - mid_price) / mid_price * 100
            
            if price_diff_pct > 10:  # More than 10% away
                if side.upper() == "BUY" and float(limit_price.amount) > ask * 1.1:
                    errors.append(
                        OrderError.create(
                            OrderErrorCode.PRICE_TOO_FAR_FROM_MARKET,
                            f"Buy limit price {limit_price.amount} too far above ask {ask}",
                            {
                                "symbol": str(symbol.value),
                                "limit_price": str(limit_price.amount),
                                "ask": str(ask),
                                "diff_pct": str(price_diff_pct),
                            },
                        )
                    )
                elif side.upper() == "SELL" and float(limit_price.amount) < bid * 0.9:
                    errors.append(
                        OrderError.create(
                            OrderErrorCode.PRICE_TOO_FAR_FROM_MARKET,
                            f"Sell limit price {limit_price.amount} too far below bid {bid}",
                            {
                                "symbol": str(symbol.value),
                                "limit_price": str(limit_price.amount),
                                "bid": str(bid),
                                "diff_pct": str(price_diff_pct),
                            },
                        )
                    )
            elif price_diff_pct > 5:  # 5-10% away - warning
                warnings.append(f"Limit price {price_diff_pct:.1f}% away from market")

        except Exception as e:
            self.logger.warning(f"Unable to validate limit price for {symbol.value}: {e}")

        return errors, warnings