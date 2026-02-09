"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import boto3
from boto3.dynamodb.conditions import Key
from collections import Counter

TABLE_NAME = "alchemiser-dev-group-history"

GROUP_IDS = [
    "ftl_starburst__wyld_combo",
    "ftl_starburst__nova_switcher",
    "ftl_starburst__walters_champagne",
]


def main() -> None:
    table = boto3.resource("dynamodb", region_name="us-east-1").Table(TABLE_NAME)

    for gid in GROUP_IDS:
        resp = table.query(
            KeyConditionExpression=Key("group_id").eq(gid),
            ScanIndexForward=False,
            Limit=25,
        )
        items = resp["Items"]
        print(f"\n=== {gid} ({len(items)} rows) ===")
        print(f"  {'Date':<12} {'Selections':<50} {'Daily Return':>14}")
        print(f"  {'-'*12} {'-'*50} {'-'*14}")

        selections_list: list[str] = []
        returns_list: list[str] = []

        for item in items:
            dt = item.get("record_date", "?")
            sels = item.get("selections", {})
            sel_str = (
                ", ".join(f"{k}:{v}" for k, v in sorted(sels.items()))
                if sels
                else "NONE"
            )
            ret = item.get("portfolio_daily_return", "?")
            print(f"  {dt:<12} {sel_str:<50} {str(ret):>14}")
            selections_list.append(sel_str)
            returns_list.append(str(ret))

        unique_sels = len(set(selections_list))
        unique_rets = len(set(returns_list))
        print(
            f"  --- Unique selections: {unique_sels}/{len(items)}, "
            f"Unique returns: {unique_rets}/{len(items)}"
        )

        sel_counts = Counter(selections_list)
        print(f"  --- Selection distribution: {dict(sel_counts)}")


if __name__ == "__main__":
    main()
