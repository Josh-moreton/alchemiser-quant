#!/usr/bin/env python3
"""
Portfolio Rebalancer Modernization - Usage Example

This script demonstrates how to use the new modular portfolio rebalancing system
both as a drop-in replacement for the existing system and with enhanced features.
"""

import os
from decimal import Decimal
from typing import Any

from the_alchemiser.application.portfolio.services.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.infrastructure.adapters.legacy_portfolio_adapter import (
    LegacyPortfolioRebalancerAdapter,
)
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


def example_legacy_compatibility_mode():
    """Example showing drop-in replacement for existing portfolio_rebalancer.py."""
    print("=== Legacy Compatibility Mode ===")

    # Initialize with existing TradingServiceManager
    trading_manager = TradingServiceManager(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY"), paper=True
    )

    # Create adapter with legacy mode (default)
    adapter = LegacyPortfolioRebalancerAdapter(
        trading_manager=trading_manager, use_new_system=False  # Legacy mode
    )

    # Use exactly the same interface as the old system
    target_weights = {"AAPL": 0.6, "MSFT": 0.4}
    current_values = {"AAPL": 5000.0, "MSFT": 3000.0}
    portfolio_value = 10000.0

    # This call is identical to the old portfolio_rebalancer.py
    rebalance_result = adapter.calculate_rebalance_amounts(
        target_weights, current_values, portfolio_value
    )

    print("Legacy rebalance calculation:")
    for symbol, data in rebalance_result.items():
        print(f"  {symbol}: trade ${data['trade_amount']:.2f} (needs: {data['needs_rebalance']})")


def example_new_system_with_adapter():
    """Example showing new system through the legacy adapter."""
    print("\n=== New System Through Legacy Adapter ===")

    trading_manager = TradingServiceManager(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY"), paper=True
    )

    # Create adapter with new system enabled
    adapter = LegacyPortfolioRebalancerAdapter(
        trading_manager=trading_manager, use_new_system=True  # New system
    )

    target_weights = {"AAPL": 0.6, "MSFT": 0.4}

    # Same interface, but powered by new system
    rebalance_result = adapter.calculate_rebalance_amounts(
        target_weights, {}, 0  # Will fetch current data automatically
    )

    print("New system rebalance calculation:")
    for symbol, data in rebalance_result.items():
        print(f"  {symbol}: trade ${data['trade_amount']:.2f} (needs: {data['needs_rebalance']})")

    # Enhanced capabilities available through adapter
    portfolio_analysis = adapter.get_portfolio_analysis()
    print(f"\nPortfolio analysis: ${portfolio_analysis.get('portfolio_value', 0):.2f} total value")


def example_system_comparison():
    """Example showing side-by-side comparison of old vs new systems."""
    print("\n=== System Comparison ===")

    trading_manager = TradingServiceManager(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY"), paper=True
    )

    adapter = LegacyPortfolioRebalancerAdapter(trading_manager, use_new_system=False)

    target_weights = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}

    # Compare both systems for validation
    comparison = adapter.compare_systems(target_weights)

    print(f"Systems match: {comparison['systems_match']}")
    print("Differences found:")
    for symbol, diff in comparison["differences"].items():
        print(f"  {symbol}: trade amount diff ${diff['trade_amount_diff']:.2f}")


def example_direct_new_system():
    """Example showing direct usage of the new system with all features."""
    print("\n=== Direct New System Usage ===")

    trading_manager = TradingServiceManager(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY"), paper=True
    )

    # Use the new system directly for maximum power
    portfolio_facade = PortfolioManagementFacade(trading_manager)

    target_weights = {
        "AAPL": Decimal("0.4"),
        "MSFT": Decimal("0.3"),
        "GOOGL": Decimal("0.2"),
        "AMZN": Decimal("0.1"),
    }

    # 1. Get comprehensive portfolio analysis
    print("1. Portfolio Analysis:")
    analysis = portfolio_facade.get_portfolio_analysis()
    portfolio_summary = analysis.get("portfolio_summary", {})
    print(f"   Total Value: ${portfolio_summary.get('total_value', 0)}")
    print(f"   Positions: {portfolio_summary.get('num_positions', 0)}")

    # 2. Analyze drift from target allocations
    print("\n2. Portfolio Drift Analysis:")
    drift = portfolio_facade.analyze_portfolio_drift(target_weights)
    overall_metrics = drift.get("overall_metrics", {})
    print(f"   Total Drift: {overall_metrics.get('total_absolute_drift', 0):.1%}")
    print(f"   Drift Severity: {overall_metrics.get('drift_severity', 'unknown')}")

    # 3. Get strategy attribution
    print("\n3. Strategy Performance:")
    strategy_perf = portfolio_facade.get_strategy_performance()
    strategy_breakdown = strategy_perf.get("strategy_breakdown", {})
    for strategy, data in strategy_breakdown.items():
        allocation = data.get("allocation_percentage", 0)
        print(f"   {strategy}: {allocation:.1%}")

    # 4. Calculate and validate rebalancing plan
    print("\n4. Rebalancing Plan:")
    rebalance_summary = portfolio_facade.get_rebalancing_summary(target_weights)

    total_trade_value = rebalance_summary.get("total_trade_value", 0)
    portfolio_turnover = rebalance_summary.get("portfolio_turnover", 0)

    print(f"   Total Trade Value: ${total_trade_value}")
    print(f"   Portfolio Turnover: {portfolio_turnover:.1%}")

    # 5. Execute rebalancing (dry run)
    print("\n5. Rebalancing Execution (Dry Run):")
    execution_result = portfolio_facade.execute_rebalancing(target_weights, dry_run=True)

    if execution_result["status"] == "completed":
        execution_details = execution_result["execution_results"]
        orders_placed = execution_details.get("orders_placed", {})
        print(f"   Orders to place: {len(orders_placed)}")

        for symbol, order in orders_placed.items():
            status = order.get("status", "unknown")
            message = order.get("message", "No details")
            print(f"     {symbol}: {status} - {message}")
    else:
        print(f"   Execution failed: {execution_result.get('status')}")


def example_complete_workflow():
    """Example showing the complete rebalancing workflow."""
    print("\n=== Complete Rebalancing Workflow ===")

    trading_manager = TradingServiceManager(
        api_key=os.getenv("ALPACA_API_KEY"), secret_key=os.getenv("ALPACA_SECRET_KEY"), paper=True
    )

    portfolio_facade = PortfolioManagementFacade(trading_manager)

    target_weights = {
        "SPY": Decimal("0.4"),  # S&P 500 ETF
        "QQQ": Decimal("0.3"),  # NASDAQ ETF
        "IWM": Decimal("0.2"),  # Russell 2000 ETF
        "TLT": Decimal("0.1"),  # Treasury Bond ETF
    }

    # Complete workflow with analysis and execution
    workflow_result = portfolio_facade.perform_portfolio_rebalancing_workflow(
        target_weights=target_weights, dry_run=True, include_analysis=True  # Safe simulation mode
    )

    print("Complete workflow results:")

    # Pre-rebalancing analysis
    if "pre_rebalancing_analysis" in workflow_result:
        pre_analysis = workflow_result["pre_rebalancing_analysis"]
        drift_analysis = pre_analysis.get("drift_analysis", {})
        overall_metrics = drift_analysis.get("overall_metrics", {})
        print(f"   Pre-rebalance drift: {overall_metrics.get('total_absolute_drift', 0):.1%}")

    # Rebalancing plan
    rebalancing_plan = workflow_result.get("rebalancing_plan", {})
    validation = rebalancing_plan.get("validation", {})
    print(f"   Plan validation: {'✅ Valid' if validation.get('is_valid') else '❌ Invalid'}")

    if not validation.get("is_valid"):
        issues = validation.get("issues", [])
        for issue in issues:
            print(f"     Issue: {issue}")

    # Execution results
    execution = workflow_result.get("execution", {})
    execution_status = execution.get("status", "unknown")
    print(f"   Execution status: {execution_status}")

    if execution_status == "success":
        summary = execution.get("execution_summary", {})
        successful_orders = summary.get("successful_orders", 0)
        total_orders = summary.get("total_orders", 0)
        print(f"   Orders: {successful_orders}/{total_orders} successful")


def main():
    """Main demonstration function."""
    print("Portfolio Rebalancer Modernization - Usage Examples")
    print("=" * 60)

    # Check for required environment variables
    if not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_SECRET_KEY"):
        print("⚠️  ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables required")
        print("   Set paper trading credentials to run examples")
        return

    try:
        # Run all examples
        example_legacy_compatibility_mode()
        example_new_system_with_adapter()
        example_system_comparison()
        example_direct_new_system()
        example_complete_workflow()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nKey Benefits of the New System:")
        print("• 🔄 Drop-in replacement for existing code")
        print("• 📊 Rich portfolio analysis and strategy attribution")
        print("• 🎯 Smart execution with market impact optimization")
        print("• 🛡️  Comprehensive validation and error handling")
        print("• 🧪 Safe migration with feature flags and comparison")
        print("• 🏗️  Modular, testable architecture")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("   This is expected in a development environment without live market data")


if __name__ == "__main__":
    main()
