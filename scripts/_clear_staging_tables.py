"""One-off script to clear staging DynamoDB tables after architecture migration."""
from __future__ import annotations

import boto3

REGION = "us-east-1"
TABLES = [
    "alchemiser-staging-trade-ledger",
    "alchemiser-staging-strategy-performance",
    "alchemiser-staging-execution-runs",
    "alchemiser-staging-rebalance-plans",
]


def clear_table(table_name: str) -> int:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(table_name)
    total = 0
    scan_kwargs: dict = {"ProjectionExpression": "PK, SK"}
    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        if not items:
            break
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
        total += len(items)
        print(f"  Deleted {len(items)} items ({total} total)")
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return total


def main() -> None:
    for table_name in TABLES:
        print(f"--- Clearing {table_name} ---")
        removed = clear_table(table_name)
        print(f"  Done: {removed} items removed\n")
    print("All tables cleared.")


if __name__ == "__main__":
    main()
