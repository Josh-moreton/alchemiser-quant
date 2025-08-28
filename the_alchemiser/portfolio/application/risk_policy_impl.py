"""Business Unit: portfolio assessment & management; Status: current.

Risk Policy Implementation

Concrete implementation of RiskPolicy that handles risk assessment and limits.
Now uses pure domain objects and typed protocols.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.domain.policies.policy_result import (
    PolicyResult,
    PolicyWarning,
    create_approved_result,
    create_rejected_result,
)
from the_alchemiser.domain.policies.protocols import DataProviderProtocol, TradingClientProtocol
from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.infrastructure.logging.logging_utils import log_with_context

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RiskPolicyImpl:
    """Concrete implementation of risk policy.

    Provides basic risk assessment functionality with configurable thresholds.
    Can be extended with more sophisticated risk models in the future.
    Uses typed protocols for external dependencies.
    """

    def __init__(
        self,
        trading_client: TradingClientProtocol | None = None,
        data_provider: DataProviderProtocol | None = None,
        max_risk_score: Decimal = Decimal("100"),
        max_position_concentration: float = 0.15,  # 15% of portfolio
        max_order_size_pct: float = 0.10,  # 10% of portfolio per order
    ) -> None:
        """Initialize the risk policy.

        Args:
            trading_client: Trading client for portfolio data
            data_provider: Data provider for price information
            max_risk_score: Maximum acceptable risk score
            max_position_concentration: Maximum position concentration (as fraction of portfolio)
            max_order_size_pct: Maximum order size as percentage of portfolio

        """
        self.trading_client = trading_client
        self.data_provider = data_provider
        self._policy_name = "RiskPolicy"
        self._max_risk_score = max_risk_score
        self.max_position_concentration = max_position_concentration
        self.max_order_size_pct = max_order_size_pct

    def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
        """Assess risk and validate order against risk limits.

        Args:
            order_request: The domain order request to validate

        Returns:
            PolicyResult with risk assessment and any adjustments

        """
        log_with_context(
            logger,
            logging.INFO,
            f"Assessing risk for {order_request.symbol.value}",
            policy=self.policy_name,
            symbol=order_request.symbol.value,
            side=order_request.side.value,
            quantity=str(order_request.quantity.value),
        )

        warnings: list[PolicyWarning] = []
        risk_score = Decimal("0")

        try:
            # Calculate risk score for the order
            risk_score = self.calculate_risk_score(
                order_request.symbol.value,
                float(order_request.quantity.value),
                order_request.order_type.value,
            )

            # Check if risk score exceeds maximum
            if risk_score > self.max_risk_score:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Order rejected: risk score {risk_score} exceeds maximum {self.max_risk_score}",
                    policy=self.policy_name,
                    action="reject",
                    symbol=order_request.symbol.value,
                    risk_score=str(risk_score),
                    max_risk_score=str(self.max_risk_score),
                )

                result = create_rejected_result(
                    order_request=order_request,
                    rejection_reason=f"Risk score {risk_score} exceeds maximum {self.max_risk_score}",
                )
                return result.with_risk_score(risk_score)

            # Add warning if risk score is high but acceptable
            if risk_score > self.max_risk_score * Decimal("0.8"):  # 80% of max
                warning = PolicyWarning(
                    policy_name=self.policy_name,
                    action="allow",
                    message=f"High risk score: {risk_score}",
                    original_value=str(order_request.quantity.value),
                    adjusted_value=str(order_request.quantity.value),
                    risk_level="high",
                )
                warnings.append(warning)

            # Assess position concentration for buy orders
            if order_request.side.value.lower() == "buy" and self.trading_client:
                is_acceptable, concentration_warning = self.assess_position_concentration(
                    order_request.symbol.value, float(order_request.quantity.value)
                )

                if not is_acceptable:
                    log_with_context(
                        logger,
                        logging.WARNING,
                        "Order rejected: excessive position concentration",
                        policy=self.policy_name,
                        action="reject",
                        symbol=order_request.symbol.value,
                        reason=concentration_warning,
                    )

                    result = create_rejected_result(
                        order_request=order_request,
                        rejection_reason=concentration_warning
                        or "Excessive position concentration",
                    )
                    return result.with_risk_score(risk_score)

                if concentration_warning:
                    warning = PolicyWarning(
                        policy_name=self.policy_name,
                        action="allow",
                        message=concentration_warning,
                        original_value=str(order_request.quantity.value),
                        adjusted_value=str(order_request.quantity.value),
                        risk_level="medium",
                    )
                    warnings.append(warning)

        except Exception as e:
            # Log error but allow order to proceed with warning
            warning_msg = f"Risk assessment failed but allowing order: {e}"

            warning = PolicyWarning(
                policy_name=self.policy_name,
                action="allow",
                message=warning_msg,
                original_value=str(order_request.quantity.value),
                adjusted_value=str(order_request.quantity.value),
                risk_level="medium",
            )
            warnings.append(warning)

            log_with_context(
                logger,
                logging.WARNING,
                "Risk assessment failed but allowing order to proceed",
                policy=self.policy_name,
                action="allow",
                symbol=order_request.symbol.value,
                error=str(e),
                error_type=type(e).__name__,
            )

        # Approve the order
        log_with_context(
            logger,
            logging.INFO,
            "Risk assessment passed",
            policy=self.policy_name,
            action="allow",
            symbol=order_request.symbol.value,
            risk_score=str(risk_score),
        )

        result = create_approved_result(order_request=order_request)

        # Add warnings and metadata
        if warnings:
            result = result.with_warnings(tuple(warnings))

        metadata = {"risk_score": str(risk_score)}
        result = result.with_metadata(metadata)
        result = result.with_risk_score(risk_score)

        return result

    def calculate_risk_score(
        self, symbol: str, quantity: float, order_type: str = "market"
    ) -> Decimal:
        """Calculate a risk score for an order.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            order_type: Type of order

        Returns:
            Risk score (higher values indicate higher risk)

        """
        try:
            base_score = Decimal("10")  # Base risk score

            # Add risk based on order type
            if order_type == "market":
                base_score += Decimal("5")  # Market orders have execution risk

            # Add risk based on quantity (larger orders = higher risk)
            quantity_risk = min(Decimal(str(quantity)) * Decimal("0.1"), Decimal("20"))
            base_score += quantity_risk

            # Add symbol-specific risk (placeholder - could be enhanced with volatility data)
            # For now, just add a small amount for all symbols
            base_score += Decimal("5")

            return base_score

        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Error calculating risk score for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return Decimal("50")  # Conservative default risk score

    def assess_position_concentration(
        self, symbol: str, additional_quantity: float
    ) -> tuple[bool, str | None]:
        """Assess if adding quantity would create excessive concentration.

        Args:
            symbol: Stock symbol
            additional_quantity: Additional quantity being added

        Returns:
            Tuple of (is_acceptable, warning_message)

        """
        try:
            if not self.trading_client or not self.data_provider:
                return True, None  # Skip check if dependencies not available

            # Get current portfolio value (simplified calculation)
            account = self.trading_client.get_account()
            portfolio_value = float(getattr(account, "portfolio_value", 0) or 0)

            if portfolio_value <= 0:
                return True, "Unable to assess concentration - unknown portfolio value"

            # Get current price to estimate order value
            current_price = self.data_provider.get_current_price(symbol)
            if not current_price or current_price <= 0:
                return True, f"Unable to assess concentration for {symbol} - no price data"

            # Calculate order value
            order_value = additional_quantity * float(current_price)
            concentration_pct = order_value / portfolio_value

            if concentration_pct > self.max_position_concentration:
                return (
                    False,
                    f"Order would create {concentration_pct:.1%} position concentration (max: {self.max_position_concentration:.1%})",
                )

            if concentration_pct > self.max_position_concentration * 0.8:  # 80% of limit
                return True, f"High concentration warning: {concentration_pct:.1%} of portfolio"

            return True, None

        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Error assessing position concentration for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return True, f"Concentration assessment failed: {e}"

    def validate_order_size(
        self, symbol: str, quantity: float, portfolio_value: float
    ) -> tuple[bool, str | None]:
        """Validate order size against portfolio limits.

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            portfolio_value: Current portfolio value

        Returns:
            Tuple of (is_acceptable, warning_message)

        """
        try:
            if not self.data_provider:
                return True, None  # Skip check if no data provider

            current_price = self.data_provider.get_current_price(symbol)
            if not current_price or current_price <= 0:
                return True, f"Unable to validate order size for {symbol} - no price data"

            order_value = quantity * float(current_price)
            order_size_pct = order_value / portfolio_value

            if order_size_pct > self.max_order_size_pct:
                return (
                    False,
                    f"Order size {order_size_pct:.1%} exceeds limit {self.max_order_size_pct:.1%}",
                )

            return True, None

        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Error validating order size for {symbol}: {e}",
                policy=self.policy_name,
                symbol=symbol,
                error=str(e),
            )
            return True, f"Order size validation failed: {e}"

    @property
    def max_risk_score(self) -> Decimal:
        """Get the maximum acceptable risk score."""
        return self._max_risk_score

    @property
    def policy_name(self) -> str:
        """Get the name of this policy for logging and identification."""
        return self._policy_name
