"""Business Unit: portfolio | Status: current..15,
        max_order_size_pct: float = 0.10,
    ) -> PolicyOrchestrator:
        """Create a PolicyOrchestrator with all standard policies.

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
        """Create a minimal PolicyOrchestrator with only fractionability policy.

        Useful for testing or scenarios where only fractionability validation is needed.

        Returns:
            PolicyOrchestrator with only fractionability policy

        """
        from the_alchemiser.execution.orders.order_request import OrderRequest
        from the_alchemiser.execution.types.policy_result import (
            PolicyResult,
            create_approved_result,
        )

        fractionability_policy = FractionabilityPolicyImpl()

        # Create minimal implementations for other policies (no-op)
        class NoOpPositionPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpPositionPolicy"

            def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
                return create_approved_result(order_request=order_request)

        class NoOpBuyingPowerPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpBuyingPowerPolicy"

            def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
                return create_approved_result(order_request=order_request)

        class NoOpRiskPolicy:
            @property
            def policy_name(self) -> str:
                return "NoOpRiskPolicy"

            def validate_and_adjust(self, order_request: OrderRequest) -> PolicyResult:
                return create_approved_result(order_request=order_request)

        return PolicyOrchestrator(
            fractionability_policy=fractionability_policy,
            position_policy=NoOpPositionPolicy(),  # type: ignore
            buying_power_policy=NoOpBuyingPowerPolicy(),  # type: ignore
            risk_policy=NoOpRiskPolicy(),  # type: ignore
        )
