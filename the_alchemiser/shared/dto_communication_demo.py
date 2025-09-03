#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Demonstration of Phase 3 DTO-based inter-module communication.

This script shows how the new DTO-based communication patterns work
in practice, demonstrating the Strategy → Portfolio → Execution flow.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.adapters.integration_helpers import (
    CrossModuleCommunicationHelper,
    PortfolioExecutionAdapter,
    StrategyPortfolioAdapter,
)
from the_alchemiser.shared.dto import (
    OrderRequestDTO,
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    RebalancePlanDTO,
    RebalancePlanItemDTO,
    StrategySignalDTO,
)


def demo_strategy_to_portfolio_communication() -> dict[str, any]:
    """Demonstrate Strategy → Portfolio DTO communication."""
    print("📡 Strategy → Portfolio Communication Demo")
    print("=" * 50)

    # Create correlation context
    correlation_context = CrossModuleCommunicationHelper.create_correlation_context(
        module_name="strategy",
        operation="signal_generation",
    )

    # Mock strategy signals (in practice these come from TypedStrategyManager.generate_signals_dto())
    signals = [
        StrategySignalDTO(
            correlation_id=correlation_context["correlation_id"],
            causation_id=correlation_context["causation_id"],
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            confidence=Decimal("0.85"),
            reasoning="Strong technical breakout with high volume",
            strategy_name="nuclear_strategy",
            allocation_weight=Decimal("0.15"),  # 15% allocation
        ),
        StrategySignalDTO(
            correlation_id=f"{correlation_context['correlation_id']}_002",
            causation_id=correlation_context["causation_id"],
            timestamp=datetime.now(UTC),
            symbol="GOOGL",
            action="SELL",
            confidence=Decimal("0.70"),
            reasoning="Overbought conditions detected",
            strategy_name="nuclear_strategy",
            allocation_weight=Decimal("0.05"),  # Reduce to 5%
        ),
    ]

    print(f"🎯 Generated {len(signals)} strategy signals:")
    for signal in signals:
        print(
            f"  - {signal.symbol}: {signal.action} (confidence: {signal.confidence}, allocation: {signal.allocation_weight})"
        )

    # Portfolio module would consume these signals
    portfolio_context = StrategyPortfolioAdapter.signals_to_allocation_requests(
        signals=signals,
        strategy_name="nuclear_strategy",
    )

    print(f"\n📊 Portfolio received {len(portfolio_context)} signals for processing")
    print(f"Correlation ID: {portfolio_context[0].correlation_id if portfolio_context else 'N/A'}")

    return {
        "signals_generated": len(signals),
        "portfolio_signals": len(portfolio_context),
        "correlation_id": correlation_context["correlation_id"],
        "causation_id": correlation_context["causation_id"],
    }


def demo_portfolio_to_execution_communication() -> dict[str, any]:
    """Demonstrate Portfolio → Execution DTO communication."""
    print("\n📦 Portfolio → Execution Communication Demo")
    print("=" * 50)

    # Create correlation context (continuing from strategy signals)
    correlation_context = CrossModuleCommunicationHelper.create_correlation_context(
        module_name="portfolio",
        operation="rebalancing",
        parent_correlation_id="strategy_signal_generation_abc123",
    )

    # Mock rebalance plan (in practice this comes from PortfolioRebalancingService.create_rebalance_plan_dto())
    rebalance_plan = RebalancePlanDTO(
        correlation_id=correlation_context["correlation_id"],
        causation_id=correlation_context["causation_id"],
        timestamp=datetime.now(UTC),
        plan_id=f"rebalance_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        total_portfolio_value=Decimal("100000"),  # $100k portfolio
        total_trade_value=Decimal("10000"),  # $10k in trades
        items=[
            RebalancePlanItemDTO(
                symbol="AAPL",
                current_weight=Decimal("0.10"),  # Currently 10%
                target_weight=Decimal("0.15"),  # Target 15%
                weight_diff=Decimal("0.05"),  # +5%
                target_value=Decimal("15000"),  # $15k target
                current_value=Decimal("10000"),  # $10k current
                trade_amount=Decimal("5000"),  # Buy $5k
                action="BUY",
                priority=1,
            ),
            RebalancePlanItemDTO(
                symbol="GOOGL",
                current_weight=Decimal("0.12"),  # Currently 12%
                target_weight=Decimal("0.05"),  # Target 5%
                weight_diff=Decimal("-0.07"),  # -7%
                target_value=Decimal("5000"),  # $5k target
                current_value=Decimal("12000"),  # $12k current
                trade_amount=Decimal("-7000"),  # Sell $7k
                action="SELL",
                priority=2,
            ),
        ],
    )

    print(f"📋 Created rebalance plan: {rebalance_plan.plan_id}")
    print(f"   Total portfolio value: ${rebalance_plan.total_portfolio_value:,}")
    print(f"   Total trade value: ${rebalance_plan.total_trade_value:,}")
    print(f"   Number of items: {len(rebalance_plan.items)}")

    # Convert to order requests for execution
    order_requests = PortfolioExecutionAdapter.rebalance_plan_to_orders(
        rebalance_plan=rebalance_plan,
        portfolio_id="main_portfolio",
        execution_config={"execution_priority": "BALANCE", "time_in_force": "DAY"},
    )

    print(f"\n🎯 Generated {len(order_requests)} order requests:")
    for order in order_requests:
        print(f"  - {order.symbol}: {order.side} {order.quantity} shares")
        print(f"    Order type: {order.order_type}, Priority: {order.execution_priority}")

    return {
        "rebalance_items": len(rebalance_plan.items),
        "order_requests": len(order_requests),
        "total_trade_value": float(rebalance_plan.total_trade_value),
        "correlation_id": correlation_context["correlation_id"],
        "plan_id": rebalance_plan.plan_id,
    }


def demo_execution_feedback_communication() -> dict[str, any]:
    """Demonstrate Execution → Portfolio feedback DTO communication."""
    print("\n⚡ Execution → Portfolio Feedback Demo")
    print("=" * 50)

    # Mock execution report (in practice this comes from execution module)
    from the_alchemiser.shared.adapters.integration_helpers import ExecutionPortfolioAdapter
    from the_alchemiser.shared.dto.execution_report_dto import (
        ExecutedOrderDTO,
        ExecutionReportDTO,
    )

    execution_report = ExecutionReportDTO(
        correlation_id="portfolio_rebalancing_def456",
        causation_id="strategy_signal_generation_abc123",
        timestamp=datetime.now(UTC),
        execution_id=f"exec_{uuid.uuid4().hex[:12]}",
        session_id="trading_session_001",
        total_orders=2,
        successful_orders=2,
        failed_orders=0,
        total_value_traded=Decimal("12000"),
        total_commissions=Decimal("4.00"),
        total_fees=Decimal("0.50"),
        net_cash_flow=Decimal("-2004.50"),  # Net purchase after costs
        execution_start_time=datetime.now(UTC),
        execution_end_time=datetime.now(UTC),
        total_duration_seconds=120,  # 2 minutes
        orders=[
            ExecutedOrderDTO(
                order_id="order_001",
                symbol="AAPL",
                action="BUY",
                quantity=Decimal("50"),
                filled_quantity=Decimal("50"),
                price=Decimal("150.00"),
                total_value=Decimal("7500.00"),
                status="FILLED",
                execution_timestamp=datetime.now(UTC),
                commission=Decimal("2.00"),
            ),
            ExecutedOrderDTO(
                order_id="order_002",
                symbol="GOOGL",
                action="SELL",
                quantity=Decimal("30"),
                filled_quantity=Decimal("30"),
                price=Decimal("150.00"),
                total_value=Decimal("4500.00"),
                status="FILLED",
                execution_timestamp=datetime.now(UTC),
                commission=Decimal("2.00"),
            ),
        ],
        success_rate=Decimal("1.0"),  # 100% success
        average_execution_time_seconds=Decimal("60"),
        broker_used="alpaca",
        execution_strategy="market_orders",
    )

    print(f"⚡ Execution completed: {execution_report.execution_id}")
    print(
        f"   Orders executed: {execution_report.successful_orders}/{execution_report.total_orders}"
    )
    print(f"   Total value traded: ${execution_report.total_value_traded:,}")
    print(f"   Success rate: {float(execution_report.success_rate) * 100:.1f}%")

    # Convert to portfolio update context
    portfolio_update = ExecutionPortfolioAdapter.execution_results_to_portfolio_update(
        execution_report
    )

    print("\n📊 Portfolio update context prepared:")
    print(f"   Net cash flow: ${portfolio_update['net_cash_flow']:,}")
    print(f"   Orders processed: {len(portfolio_update['orders'])}")
    print(f"   Correlation maintained: {portfolio_update['correlation_id']}")

    return {
        "execution_id": execution_report.execution_id,
        "orders_executed": execution_report.successful_orders,
        "net_cash_flow": float(execution_report.net_cash_flow),
        "success_rate": float(execution_report.success_rate),
        "correlation_id": execution_report.correlation_id,
    }


def demo_end_to_end_correlation_tracking() -> bool:
    """Demonstrate end-to-end correlation tracking across modules."""
    print("\n🔗 End-to-End Correlation Tracking Demo")
    print("=" * 50)

    # Create initial correlation context
    base_correlation_id = f"e2e_demo_{uuid.uuid4().hex[:12]}"

    # Mock signals with correlation tracking
    signal = StrategySignalDTO(
        correlation_id=f"{base_correlation_id}_signal",
        causation_id=base_correlation_id,
        timestamp=datetime.now(UTC),
        symbol="TSLA",
        action="BUY",
        confidence=Decimal("0.80"),
        reasoning="Demo signal for correlation tracking",
        strategy_name="demo_strategy",
        allocation_weight=Decimal("0.10"),
    )

    # Mock portfolio state with correlation
    portfolio_state = PortfolioStateDTO(
        correlation_id=f"{base_correlation_id}_portfolio",
        causation_id=f"{base_correlation_id}_signal",
        timestamp=datetime.now(UTC),
        portfolio_id="demo_portfolio",
        positions=[],
        metrics=PortfolioMetricsDTO(
            total_value=Decimal("50000"),
            cash_value=Decimal("10000"),
            equity_value=Decimal("40000"),
            buying_power=Decimal("15000"),
            day_pnl=Decimal("500"),
            day_pnl_percent=Decimal("0.01"),
            total_pnl=Decimal("2500"),
            total_pnl_percent=Decimal("0.05"),
        ),
    )

    # Mock order request with correlation
    order_request = OrderRequestDTO(
        correlation_id=f"{base_correlation_id}_order",
        causation_id=f"{base_correlation_id}_portfolio",
        timestamp=datetime.now(UTC),
        request_id=f"order_{uuid.uuid4().hex[:8]}",
        portfolio_id="demo_portfolio",
        symbol="TSLA",
        side="BUY",
        quantity=Decimal("25"),
        order_type="MARKET",
    )

    # Mock execution report with correlation
    from the_alchemiser.shared.dto.execution_report_dto import ExecutionReportDTO

    execution_report = ExecutionReportDTO(
        correlation_id=f"{base_correlation_id}_execution",
        causation_id=f"{base_correlation_id}_order",
        timestamp=datetime.now(UTC),
        execution_id=f"exec_{uuid.uuid4().hex[:12]}",
        total_orders=1,
        successful_orders=1,
        failed_orders=0,
        total_value_traded=Decimal("5000"),
        total_commissions=Decimal("2"),
        total_fees=Decimal("0.50"),
        net_cash_flow=Decimal("-5002.50"),
        execution_start_time=datetime.now(UTC),
        execution_end_time=datetime.now(UTC),
        total_duration_seconds=30,
        orders=[],
        success_rate=Decimal("1.0"),
    )

    # Validate correlation chain
    is_valid = CrossModuleCommunicationHelper.validate_dto_communication_chain(
        strategy_signals=[signal],
        portfolio_state=portfolio_state,
        order_requests=[order_request],
        execution_report=execution_report,
    )

    print(f"🔗 Correlation tracking validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print(f"   Base correlation ID: {base_correlation_id}")
    print(f"   Signal correlation: {signal.correlation_id}")
    print(f"   Portfolio correlation: {portfolio_state.correlation_id}")
    print(f"   Order correlation: {order_request.correlation_id}")
    print(f"   Execution correlation: {execution_report.correlation_id}")

    return is_valid


def main() -> None:
    """Run the complete Phase 3 DTO communication demonstration."""
    print("🚀 Phase 3 DTO-Based Inter-Module Communication Demo")
    print("=" * 60)
    print("This demonstrates how modules communicate using DTOs and adapters")
    print("while maintaining correlation tracking and type safety.\n")

    try:
        # Run each demo
        strategy_results = demo_strategy_to_portfolio_communication()
        portfolio_results = demo_portfolio_to_execution_communication()
        execution_results = demo_execution_feedback_communication()
        correlation_valid = demo_end_to_end_correlation_tracking()

        # Summary
        print("\n📋 Demo Summary")
        print("=" * 50)
        print(f"✅ Strategy signals generated: {strategy_results['signals_generated']}")
        print(f"✅ Portfolio rebalance items: {portfolio_results['rebalance_items']}")
        print(f"✅ Order requests created: {portfolio_results['order_requests']}")
        print(f"✅ Orders executed: {execution_results['orders_executed']}")
        print(f"✅ Correlation tracking: {'Valid' if correlation_valid else 'Invalid'}")
        print("\n🎯 End-to-end flow completed successfully!")
        print("   All modules communicated using DTOs with proper correlation tracking.")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
