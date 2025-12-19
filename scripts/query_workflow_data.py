#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Query DynamoDB to analyze a workflow run's signal and rebalance plan.

Usage:
    python scripts/query_workflow_data.py <correlation_id>

Example:
    python scripts/query_workflow_data.py workflow-06eaa5c9-3058-4ca0-aeff-9222cdacab5e
"""

import json
import sys
from decimal import Decimal
from typing import Any

import boto3


def get_dynamodb_client(stage: str = "dev") -> Any:
    """Get DynamoDB client."""
    return boto3.client("dynamodb", region_name="us-east-1")


def get_rebalance_plan(dynamodb: Any, correlation_id: str, stage: str = "dev") -> dict | None:
    """Query rebalance plan from DynamoDB."""
    table_name = f"alchemiser-{stage}-rebalance-plans"

    # Query using GSI on correlation_id
    response = dynamodb.query(
        TableName=table_name,
        IndexName="GSI1-CorrelationIndex",
        KeyConditionExpression="GSI1PK = :pk",
        ExpressionAttributeValues={":pk": {"S": f"CORR#{correlation_id}"}},
        Limit=1,
        ScanIndexForward=False,  # Most recent first
    )

    if not response.get("Items"):
        print(f"No rebalance plan found for {correlation_id}")
        return None

    item = response["Items"][0]
    plan_data_str = item.get("plan_data", {}).get("S", "{}")
    return json.loads(plan_data_str)


def get_aggregated_signal(dynamodb: Any, correlation_id: str, stage: str = "dev") -> dict | None:
    """Query aggregated signal from DynamoDB."""
    table_name = f"alchemiser-{stage}-aggregation-sessions"

    # Query using correlation_id
    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": {"S": f"SESSION#{correlation_id}"}},
        Limit=1,
    )

    if not response.get("Items"):
        print(f"No aggregation session found for {correlation_id}")
        return None

    item = response["Items"][0]

    # Parse merged_signal if present
    merged_signal_str = item.get("merged_signal", {}).get("S")
    if merged_signal_str:
        return json.loads(merged_signal_str)

    return item


def format_decimal(value: str | Decimal | float) -> str:
    """Format a decimal value for display."""
    try:
        d = Decimal(str(value))
        return f"${float(d):,.2f}"
    except Exception:
        return str(value)


def format_percentage(value: str | Decimal | float) -> str:
    """Format a percentage for display."""
    try:
        d = Decimal(str(value))
        return f"{float(d) * 100:.2f}%"
    except Exception:
        return str(value)


def analyze_rebalance_plan(plan: dict) -> None:
    """Analyze and print rebalance plan details."""
    print("\n" + "=" * 80)
    print("REBALANCE PLAN ANALYSIS")
    print("=" * 80)

    # Metadata
    metadata = plan.get("metadata", {})
    portfolio_value = metadata.get("portfolio_value", plan.get("total_portfolio_value", "N/A"))
    cash_balance = metadata.get("cash_balance", "N/A")

    print(f"\nPortfolio Value: {format_decimal(portfolio_value)}")
    print(f"Cash Balance: {format_decimal(cash_balance)}")
    print(f"Total Trade Value: {format_decimal(plan.get('total_trade_value', 'N/A'))}")
    print(f"Plan ID: {plan.get('plan_id', 'N/A')}")
    print(f"Correlation ID: {plan.get('correlation_id', 'N/A')}")

    items = plan.get("items", [])

    # Separate by action
    buys = [i for i in items if i.get("action") == "BUY"]
    sells = [i for i in items if i.get("action") == "SELL"]
    holds = [i for i in items if i.get("action") == "HOLD"]

    # Calculate totals
    total_buy = sum(Decimal(str(i.get("trade_amount", 0))) for i in buys)
    total_sell = sum(abs(Decimal(str(i.get("trade_amount", 0)))) for i in sells)

    # Sum of all target values
    total_target_value = sum(Decimal(str(i.get("target_value", 0))) for i in items)

    print(f"\nTrade Summary:")
    print(f"  BUY orders:  {len(buys):3d} totaling {format_decimal(total_buy)}")
    print(f"  SELL orders: {len(sells):3d} totaling {format_decimal(total_sell)}")
    print(f"  HOLD:        {len(holds):3d}")
    print(f"  Net capital needed: {format_decimal(total_buy - total_sell)}")
    print(f"\n  Sum of ALL target values: {format_decimal(total_target_value)}")
    print(f"  Portfolio value: {format_decimal(portfolio_value)}")

    pv = Decimal(str(portfolio_value))
    if pv > 0:
        deployment_pct = (total_target_value / pv) * 100
        print(f"  ==> DEPLOYMENT RATIO: {float(deployment_pct):.1f}%")
        if deployment_pct > 100:
            print(f"  ⚠️  WARNING: Attempting to deploy MORE than 100% of equity!")

    # Check if weights sum to ~100%
    total_target_weight = sum(Decimal(str(i.get("target_weight", 0))) for i in items)
    print(f"\nTarget weights sum: {format_percentage(total_target_weight)}")

    # Print SELL orders
    if sells:
        print(f"\n{'─' * 90}")
        print("SELL ORDERS (sorted by value)")
        print(f"{'─' * 90}")
        print(
            f"{'Symbol':<8} {'Current $':>12} {'Target $':>12} {'Trade $':>12} {'Curr %':>8} {'Tgt %':>8}"
        )
        print(f"{'─' * 90}")

        sells_sorted = sorted(
            sells, key=lambda x: abs(Decimal(str(x.get("trade_amount", 0)))), reverse=True
        )
        for item in sells_sorted:
            symbol = item.get("symbol", "?")
            current_val = format_decimal(item.get("current_value", 0))
            target_val = format_decimal(item.get("target_value", 0))
            trade_amt = format_decimal(item.get("trade_amount", 0))
            curr_wt = format_percentage(item.get("current_weight", 0))
            tgt_wt = format_percentage(item.get("target_weight", 0))
            print(
                f"{symbol:<8} {current_val:>12} {target_val:>12} {trade_amt:>12} {curr_wt:>8} {tgt_wt:>8}"
            )

    # Print BUY orders
    if buys:
        print(f"\n{'─' * 90}")
        print("BUY ORDERS (sorted by value)")
        print(f"{'─' * 90}")
        print(
            f"{'Symbol':<8} {'Current $':>12} {'Target $':>12} {'Trade $':>12} {'Curr %':>8} {'Tgt %':>8}"
        )
        print(f"{'─' * 90}")

        buys_sorted = sorted(
            buys, key=lambda x: Decimal(str(x.get("trade_amount", 0))), reverse=True
        )
        for item in buys_sorted:
            symbol = item.get("symbol", "?")
            current_val = format_decimal(item.get("current_value", 0))
            target_val = format_decimal(item.get("target_value", 0))
            trade_amt = format_decimal(item.get("trade_amount", 0))
            curr_wt = format_percentage(item.get("current_weight", 0))
            tgt_wt = format_percentage(item.get("target_weight", 0))
            print(
                f"{symbol:<8} {current_val:>12} {target_val:>12} {trade_amt:>12} {curr_wt:>8} {tgt_wt:>8}"
            )

    # Print HOLD orders
    if holds:
        print(f"\n{'─' * 90}")
        print("HOLD POSITIONS")
        print(f"{'─' * 90}")
        print(f"{'Symbol':<8} {'Current $':>12} {'Target $':>12} {'Curr %':>8} {'Tgt %':>8}")
        print(f"{'─' * 90}")

        for item in holds:
            symbol = item.get("symbol", "?")
            current_val = format_decimal(item.get("current_value", 0))
            target_val = format_decimal(item.get("target_value", 0))
            curr_wt = format_percentage(item.get("current_weight", 0))
            tgt_wt = format_percentage(item.get("target_weight", 0))
            print(f"{symbol:<8} {current_val:>12} {target_val:>12} {curr_wt:>8} {tgt_wt:>8}")


def analyze_signal(signal: dict) -> None:
    """Analyze and print aggregated signal details."""
    print("\n" + "=" * 80)
    print("AGGREGATED SIGNAL ANALYSIS")
    print("=" * 80)

    # Check structure - could be wrapped in various ways
    allocations = signal.get("allocations") or signal.get("target_allocations") or {}

    if not allocations:
        print("No allocations found in signal")
        print(f"Signal keys: {list(signal.keys())}")
        return

    print(f"\nTotal symbols: {len(allocations)}")

    # Calculate total weight
    total_weight = sum(Decimal(str(v)) for v in allocations.values())
    print(f"Total weight: {format_percentage(total_weight)}")

    if total_weight > Decimal("1.0"):
        print(f"⚠️  WARNING: Signal weights sum to > 100%!")

    # Sort by weight
    print(f"\n{'─' * 60}")
    print("TARGET ALLOCATIONS (sorted by weight)")
    print(f"{'─' * 60}")
    print(f"{'Symbol':<10} {'Weight':>12}")
    print(f"{'─' * 60}")

    sorted_allocs = sorted(allocations.items(), key=lambda x: Decimal(str(x[1])), reverse=True)
    for symbol, weight in sorted_allocs:
        print(f"{symbol:<10} {format_percentage(weight):>12}")


def main() -> None:
    """Main entry point."""
    stage = "dev"

    # Get correlation_id from args
    if len(sys.argv) < 2:
        print("Usage: python scripts/query_workflow_data.py <correlation_id>")
        print(
            "Example: python scripts/query_workflow_data.py workflow-06eaa5c9-3058-4ca0-aeff-9222cdacab5e"
        )
        sys.exit(1)

    correlation_id = sys.argv[1]

    print(f"\n{'=' * 80}")
    print(f"WORKFLOW DATA ANALYSIS: {correlation_id}")
    print(f"{'=' * 80}")

    dynamodb = get_dynamodb_client(stage)

    # Get and analyze signal
    signal = get_aggregated_signal(dynamodb, correlation_id, stage)
    if signal:
        analyze_signal(signal)

    # Get and analyze rebalance plan
    plan = get_rebalance_plan(dynamodb, correlation_id, stage)
    if plan:
        analyze_rebalance_plan(plan)


if __name__ == "__main__":
    main()
