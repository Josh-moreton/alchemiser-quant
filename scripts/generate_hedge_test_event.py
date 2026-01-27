#!/usr/bin/env python3
"""Generate hedge evaluator test event from DynamoDB rebalance plan."""

import json
import subprocess
import sys


def get_latest_rebalance_plan(date_prefix: str = "2026-01-26") -> dict:
    """Query DynamoDB for rebalance plan from specified date."""
    cmd = [
        "aws", "dynamodb", "scan",
        "--table-name", "alchemiser-dev-rebalance-plans",
        "--region", "us-east-1",
        "--no-cli-pager",
        "--filter-expression", "begins_with(GSI1SK, :prefix)",
        "--expression-attribute-values", f'{{":prefix": {{"S": "PLAN#{date_prefix}"}}}}'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error querying DynamoDB: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(result.stdout)
    if not data.get("Items"):
        print(f"No rebalance plans found for date {date_prefix}", file=sys.stderr)
        sys.exit(1)
    
    # Get the first (most recent) item
    item = data["Items"][0]
    plan_data_str = item["plan_data"]["S"]
    return json.loads(plan_data_str)


def build_eventbridge_event(rebalance_plan: dict) -> dict:
    """Build EventBridge event structure from rebalance plan."""
    # Build allocation comparison from items
    # AllocationComparison requires: target_values, current_values, deltas (all Decimal dicts)
    target_values = {}
    current_values = {}
    deltas = {}

    for item in rebalance_plan["items"]:
        symbol = item["symbol"]
        # Use actual dollar values, not weights
        current_values[symbol] = item["current_value"]
        target_values[symbol] = item["target_value"]
        deltas[symbol] = item["trade_amount"]  # delta = target - current (trade amount)

    # Create EventBridge event structure
    return {
        "version": "0",
        "id": "test-event-from-dynamo-001",
        "detail-type": "RebalancePlanned",
        "source": "the_alchemiser.portfolio_v2",
        "account": "123456789012",
        "time": rebalance_plan["timestamp"].split(".")[0] + "Z",
        "region": "us-east-1",
        "resources": [],
        "detail": {
            "correlation_id": rebalance_plan["correlation_id"],
            "causation_id": rebalance_plan["causation_id"],
            "event_id": f"rebalance-planned-{rebalance_plan['plan_id']}",
            "timestamp": rebalance_plan["timestamp"],
            "source_module": "portfolio_v2",
            "source_component": "portfolio_manager",
            "trades_required": True,
            "metadata": {},
            "rebalance_plan": rebalance_plan,
            "allocation_comparison": {
                "target_values": target_values,
                "current_values": current_values,
                "deltas": deltas
            }
        }
    }


def main():
    """Main entry point."""
    date_prefix = sys.argv[1] if len(sys.argv) > 1 else "2026-01-26"
    
    print(f"Fetching rebalance plan for {date_prefix}...", file=sys.stderr)
    rebalance_plan = get_latest_rebalance_plan(date_prefix)
    
    print(f"Building EventBridge event for plan: {rebalance_plan['plan_id']}", file=sys.stderr)
    event = build_eventbridge_event(rebalance_plan)
    
    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()
