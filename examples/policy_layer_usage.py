"""Business Unit: utilities; Status: legacy.

Unified Policy Layer Usage Example

This example demonstrates how to use the new unified policy layer
for order validation and adjustment.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.application.policies import PolicyFactory
from the_alchemiser.execution.orders.order_schemas import OrderRequestDTO


def example_policy_usage():
    """Example showing how to use the unified policy layer."""
    # Setup (in real application, these would be your actual clients)
    trading_client = get_trading_client()  # Your trading client
    data_provider = get_data_provider()  # Your data provider

    # Create policy orchestrator with all standard policies
    policy_orchestrator = PolicyFactory.create_orchestrator(
        trading_client=trading_client,
        data_provider=data_provider,
        max_risk_score=Decimal("100"),
        max_position_concentration=0.15,  # 15% max concentration
        max_order_size_pct=0.10,  # 10% max order size
    )

    # Create an order request
    order_request = OrderRequestDTO(
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10.5"),
        order_type="market",
        time_in_force="day",
    )

    # Validate and adjust the order through all policies
    adjusted_order = policy_orchestrator.validate_and_adjust_order(order_request)

    # Check if order was approved
    if adjusted_order.is_approved:
        print(f"✅ Order approved for {adjusted_order.symbol}")
        print(f"   Final quantity: {adjusted_order.quantity}")

        # Check for policy adjustments
        if adjusted_order.has_adjustments:
            print(f"   Adjusted from: {adjusted_order.original_quantity}")
            print(f"   Reason: {adjusted_order.adjustment_reason}")

        # Display any warnings
        if adjusted_order.has_warnings:
            print("   Warnings:")
            for warning in adjusted_order.warnings:
                print(f"     - {warning.policy_name}: {warning.message}")

        # Proceed with order execution
        execute_order(adjusted_order)

    else:
        print(f"❌ Order rejected: {adjusted_order.rejection_reason}")
        # Handle rejection (e.g., log, notify user, etc.)


def execute_order(adjusted_order):
    """Execute an approved order (placeholder)."""
    print(f"🚀 Executing order for {adjusted_order.symbol}...")
    # Your order execution logic here


def get_trading_client():
    """Get trading client (placeholder)."""
    # Return your actual trading client


def get_data_provider():
    """Get data provider (placeholder)."""
    # Return your actual data provider


# Policy-specific usage examples


def fractionability_only_example():
    """Example using only fractionability policy."""
    # For scenarios where you only need fractionability validation
    orchestrator = PolicyFactory.create_fractionability_only_orchestrator()

    order = OrderRequestDTO(
        symbol="BRK.A",  # Non-fractionable asset
        side="buy",
        quantity=Decimal("0.5"),  # Will be rounded to whole shares
        order_type="limit",
        limit_price=Decimal("500000.00"),
        time_in_force="day",
    )

    result = orchestrator.validate_and_adjust_order(order)
    print(f"Fractionability result: {result.quantity} shares")


def canonical_executor_integration():
    """Example showing integration with CanonicalOrderExecutor."""
    from the_alchemiser.execution.core.executor import CanonicalOrderExecutor
    from the_alchemiser.execution.orders.order_request import OrderRequest
    from the_alchemiser.execution.orders.order_type import OrderType
    from the_alchemiser.shared.types.quantity import Quantity
    from the_alchemiser.domain.trading.value_objects.side import Side
    from the_alchemiser.shared.value_objects.symbol import Symbol
    from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce

    # Setup
    repository = get_alpaca_repository()  # Your repository
    policy_orchestrator = PolicyFactory.create_orchestrator(
        trading_client=get_trading_client(),
        data_provider=get_data_provider(),
    )

    # Create canonical executor with policy integration
    executor = CanonicalOrderExecutor(
        repository=repository,
        policy_orchestrator=policy_orchestrator,
        shadow_mode=False,  # Set to True for testing
    )

    # Create domain order request
    domain_order = OrderRequest(
        symbol=Symbol("AAPL"),
        side=Side("buy"),
        quantity=Quantity(Decimal("10")),
        order_type=OrderType("market"),
        time_in_force=TimeInForce("day"),
    )

    # Execute with policy validation
    result = executor.execute(domain_order)

    if result.success:
        print(f"✅ Order executed: {result.order_id}")
    else:
        print(f"❌ Order failed: {result.error}")


def get_alpaca_repository():
    """Get Alpaca repository (placeholder)."""
    # Return your actual Alpaca repository


if __name__ == "__main__":
    print("📚 Unified Policy Layer Usage Examples")
    print("=====================================")

    print("\n1. Standard Policy Usage:")
    example_policy_usage()

    print("\n2. Fractionability Only:")
    fractionability_only_example()

    print("\n3. Canonical Executor Integration:")
    canonical_executor_integration()
