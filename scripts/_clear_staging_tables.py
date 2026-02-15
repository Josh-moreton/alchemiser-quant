"""Business Unit: scripts | Status: current.

One-off script to clear staging DynamoDB tables after architecture migration.

Derives key attributes dynamically from each table's key schema so it works
regardless of whether the table has a sort key or uses non-standard key names.
Requires explicit --confirm flag to prevent accidental execution.
"""
from __future__ import annotations

import argparse
import sys

import boto3

REGION = "us-east-1"
TABLES = [
    "alchemiser-staging-trade-ledger",
    "alchemiser-staging-strategy-performance",
    "alchemiser-staging-execution-runs",
    "alchemiser-staging-rebalance-plans",
]


def _get_key_attr_names(table_resource: object) -> list[str]:
    """Derive key attribute names from a DynamoDB table's key schema."""
    key_schema = table_resource.key_schema  # type: ignore[attr-defined]
    return [k["AttributeName"] for k in key_schema]


def clear_table(table_name: str) -> int:
    """Delete all items from a DynamoDB table, respecting its actual key schema."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(table_name)

    key_attrs = _get_key_attr_names(table)
    projection_expr = ", ".join(key_attrs)

    total = 0
    scan_kwargs: dict[str, object] = {"ProjectionExpression": projection_expr}
    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        if not items:
            break
        with table.batch_writer() as batch:
            for item in items:
                key = {attr: item[attr] for attr in key_attrs if attr in item}
                batch.delete_item(Key=key)
        total += len(items)
        print(f"  Deleted {len(items)} items ({total} total)")
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return total


def main() -> None:
    """Entry point -- requires --confirm flag for safety."""
    parser = argparse.ArgumentParser(description="Clear staging DynamoDB tables after migration.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required flag to confirm destructive table clearing.",
    )
    args = parser.parse_args()

    if not args.confirm:
        print("This will DELETE ALL ITEMS from the following staging tables:")
        for t in TABLES:
            print(f"  - {t}")
        print("\nRe-run with --confirm to proceed.")
        sys.exit(1)

    for table_name in TABLES:
        print(f"--- Clearing {table_name} ---")
        removed = clear_table(table_name)
        print(f"  Done: {removed} items removed\n")
    print("All tables cleared.")


if __name__ == "__main__":
    main()
