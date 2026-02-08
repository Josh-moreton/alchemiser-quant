"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource("dynamodb", region_name="us-east-1").Table(
    "alchemiser-dev-group-history"
)

for gid in [
    "ftl_starburst__wyld_combo",
    "ftl_starburst__walters_champagne",
    "ftl_starburst__nova_switcher",
]:
    resp = table.query(
        KeyConditionExpression=Key("group_id").eq(gid),
        ScanIndexForward=False,
        Limit=5,
    )
    print(f"\n=== {gid} (last 5) ===")
    for item in resp["Items"]:
        print(f"  {item}")
