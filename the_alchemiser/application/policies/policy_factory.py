"""
Policy Factory

Factory for creating policy orchestrator with all required dependencies.
Provides convenient methods for setting up the policy layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from the_alchemiser.application.policies.buying_power_policy_impl import BuyingPowerPolicyImpl
from the_alchemiser.application.policies.fractionability_policy_impl import (
    FractionabilityPolicyImpl,
)
from the_alchemiser.application.policies.policy_orchestrator import PolicyOrchestrator
from the_alchemiser.application.policies.position_policy_impl import PositionPolicyImpl
from the_alchemiser.application.policies.risk_policy_impl import RiskPolicyImpl

if TYPE_CHECKING:
    from decimal import Decimal

    from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO, OrderRequestDTO


class PolicyFactory:
    """
    Factory for creating policy orchestrator instances.

    Provides convenient methods for setting up the unified policy layer
    with appropriate dependencies and configuration.
    """

    @staticmethod
    def create_orchestrator(
        trading_client: Any,
        data_provider: Any,
        max_risk_score: Decimal | None = None,
        max_position_concentration: float = 0.15,
        max_order_size_pct: float = 0.10,
    ) -> PolicyOrchestrator:
        """
        Create a PolicyOrchestrator with all standard policies.

        Args:
            trading_client: Trading client for account and position data
            data_provider: Data provider for price information
            max_risk_score: Maximum acceptable risk score (default: 100)
            max_position_concentration: Maximum position concentration (default: 15%)
            max_order_size_pct: Maximum order size as percentage of portfolio (default: 10%)

        Returns:
            PolicyOrchestrator configured with all standard policies
        """
        from decimal import Decimal

        if max_risk_score is None:
            max_risk_score = Decimal("100")

        # Create policy implementations
        fractionability_policy = FractionabilityPolicyImpl()

        position_policy = PositionPolicyImpl(trading_client)

        buying_power_policy = BuyingPowerPolicyImpl(trading_client, data_provider)

        risk_policy = RiskPolicyImpl(
            trading_client=trading_client,
            data_provider=data_provider,
            max_risk_score=max_risk_score,
            max_position_concentration=max_position_concentration,
            max_order_size_pct=max_order_size_pct,
        )

        # Create orchestrator
        return PolicyOrchestrator(
            fractionability_policy=fractionability_policy,
            position_policy=position_policy,
            buying_power_policy=buying_power_policy,
            risk_policy=risk_policy,
        )

    @staticmethod
    def create_fractionability_only_orchestrator() -> PolicyOrchestrator:
        """
        Create a minimal PolicyOrchestrator with only fractionability policy.

        Useful for testing or scenarios where only fractionability validation is needed.

        Returns:
            PolicyOrchestrator with only fractionability policy
        """
        from decimal import Decimal

        fractionability_policy = FractionabilityPolicyImpl()

        # Create minimal implementations for other policies (no-op)
        class NoOpPositionPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpPositionPolicy"

            def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
                from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO
                return AdjustedOrderRequestDTO(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    order_type=order_request.order_type,
                    time_in_force=order_request.time_in_force,
                    limit_price=order_request.limit_price,
                    client_order_id=order_request.client_order_id,
                    is_approved=True,
                    total_risk_score=Decimal("0"),
                )

        class NoOpBuyingPowerPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpBuyingPowerPolicy"

            def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
                from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO
                return AdjustedOrderRequestDTO(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    order_type=order_request.order_type,
                    time_in_force=order_request.time_in_force,
                    limit_price=order_request.limit_price,
                    client_order_id=order_request.client_order_id,
                    is_approved=True,
                    total_risk_score=Decimal("0"),
                )

        class NoOpRiskPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpRiskPolicy"

            def validate_and_adjust(self, order_request: OrderRequestDTO) -> AdjustedOrderRequestDTO:
                from the_alchemiser.interfaces.schemas.orders import AdjustedOrderRequestDTO
                return AdjustedOrderRequestDTO(
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    order_type=order_request.order_type,
                    time_in_force=order_request.time_in_force,
                    limit_price=order_request.limit_price,
                    client_order_id=order_request.client_order_id,
                    is_approved=True,
                    total_risk_score=Decimal("0"),
                )

        return PolicyOrchestrator(
            fractionability_policy=fractionability_policy,
            position_policy=NoOpPositionPolicy(),  # type: ignore
            buying_power_policy=NoOpBuyingPowerPolicy(),  # type: ignore
            risk_policy=NoOpRiskPolicy(),  # type: ignore
        )
