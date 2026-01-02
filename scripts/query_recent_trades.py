#!/usr/bin/env python3
"""Query recent trades from the DynamoDB Trade Ledger for validation.

Defaults to the dev table `alchemiser-dev-trade-ledger` and queries trades
from yesterday (UTC). Prints a short summary and lists problematic items.

Usage:
    python scripts/query_recent_trades.py --stage dev
    python scripts/query_recent_trades.py --table <table_name> --start 2026-01-01 --end 2026-01-02
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr


def iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat()


def scan_trades(table, start_iso: str, end_iso: str) -> list[dict[str, Any]]:
    """Scan table for TRADE items with fill_timestamp in [start, end)."""
    results: list[dict[str, Any]] = []
    fe = Attr('PK').begins_with('TRADE#') & Attr('fill_timestamp').between(start_iso, end_iso)

    kwargs = {
        'FilterExpression': fe,
        'ProjectionExpression': '#pk, #sk, order_id, symbol, fill_price, filled_qty, fill_timestamp, strategy_names, direction',
        'ExpressionAttributeNames': {'#pk': 'PK', '#sk': 'SK'},
    }

    resp = table.scan(**kwargs)
    results.extend(resp.get('Items', []))
    while 'LastEvaluatedKey' in resp:
        kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
        resp = table.scan(**kwargs)
        results.extend(resp.get('Items', []))
    return results


def summarize(trades: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    per_strategy = {}
    for t in trades:
        order_id = t.get('order_id')
        symbol = t.get('symbol')
        price = t.get('fill_price')
        qty = t.get('filled_qty')
        strategies = t.get('strategy_names') or []
        direction = t.get('direction')

        # normalize types
        if isinstance(qty, (int, float)):
            qty = str(qty)
        if isinstance(price, (int, float)):
            price = str(price)

        # detect missing
        missing = []
        if not strategies:
            missing.append('strategy_names')
        if not price:
            missing.append('fill_price')
        if not qty:
            missing.append('filled_qty')

        if missing:
            issues.append({'order_id': order_id, 'symbol': symbol, 'missing': missing})

        for s in strategies:
            entry = per_strategy.setdefault(s, {'count': 0, 'trades': [], 'symbols': set()})
            entry['count'] += 1
            entry['trades'].append({'order_id': order_id, 'symbol': symbol, 'price': price, 'qty': qty, 'direction': direction})
            entry['symbols'].add(symbol)

    # convert sets
    for s in per_strategy.values():
        s['symbols'] = sorted(list(s['symbols']))
    return {'total_trades': len(trades), 'issues': issues, 'per_strategy': per_strategy}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--stage', choices=['dev', 'prod'], default='dev')
    p.add_argument('--table', help='Explicit table name (overrides --stage)')
    p.add_argument('--start', help='ISO start (inclusive)')
    p.add_argument('--end', help='ISO end (exclusive)')
    args = p.parse_args()

    table_name = args.table or f'alchemiser-{args.stage}-trade-ledger'
    print(f'Using table: {table_name}')

    # compute default start/end = yesterday UTC 00:00 -> today 00:00
    now = datetime.now(timezone.utc)
    default_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    default_end = default_start + timedelta(days=1)

    start_iso = args.start or iso(default_start)
    end_iso = args.end or iso(default_end)

    print(f'Querying fill_timestamp between {start_iso} and {end_iso} (UTC)')

    try:
        ddb = boto3.resource('dynamodb')
        table = ddb.Table(table_name)
    except Exception as e:
        print('ERROR: could not initialize DynamoDB resource:', e)
        return 2

    try:
        trades = scan_trades(table, start_iso, end_iso)
    except Exception as e:
        print('ERROR: scan failed:', e)
        return 3

    summary = summarize(trades)

    # Print short report
    print('\n=== Summary ===')
    print(json.dumps({'table': table_name, 'start': start_iso, 'end': end_iso, 'total_trades': summary['total_trades']}, default=str, indent=2))

    if summary['issues']:
        print('\nTrades with missing fields (first 20):')
        for i in summary['issues'][:20]:
            print(json.dumps(i, default=str))
    else:
        print('\nNo trades missing strategy_names/fill_price/filled_qty detected.')

    print('\nPer-strategy counts:')
    for s, v in summary['per_strategy'].items():
        print(f"  {s}: {v['count']} trades, symbols={v['symbols']}")

    # Exit success
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
