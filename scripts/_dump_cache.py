#!/usr/bin/env python3
"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict


def main() -> None:
    """Dump all group history cache records from DynamoDB."""
    result = subprocess.run(
        [
            "aws", "dynamodb", "scan",
            "--table-name", "alchemiser-dev-group-history",
            "--no-cli-pager",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)["Items"]

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in data:
        gid = item["group_id"]["S"]
        rec: dict[str, str] = {"date": item.get("record_date", {}).get("S", "?")}
        for k, v in item.items():
            if k in ("group_id", "record_date"):
                continue
            val = list(v.values())[0] if isinstance(v, dict) else str(v)
            rec[k] = str(val)
        groups[gid].append(rec)

    for gid in sorted(groups.keys()):
        records = sorted(groups[gid], key=lambda r: r["date"])
        print(f"\n{'=' * 100}")
        print(f"GROUP: {gid}  ({len(records)} days)")
        print(f"{'=' * 100}")

        all_keys: set[str] = set()
        for r in records:
            all_keys.update(r.keys())
        all_keys.discard("date")
        extra_keys = sorted(all_keys)

        hdr = f"{'date':<12s}"
        for k in extra_keys:
            hdr += f"  {k:<22s}"
        print(hdr)
        print("-" * len(hdr))

        for r in records:
            line = f"{r['date']:<12s}"
            for k in extra_keys:
                val = r.get(k, "")
                if len(val) > 20:
                    val = val[:20] + ".."
                line += f"  {val:<22s}"
            print(line)


if __name__ == "__main__":
    main()
