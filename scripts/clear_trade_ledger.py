#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Script to clear trade ledger data from DynamoDB.

Use this to reset the trade ledger when data quality issues require a fresh start.
Will delete all TRADE, LOT, and SIGNAL entities but preserve STRATEGY_METADATA.

Usage:
    python scripts/clear_trade_ledger.py --stage dev --dry-run   # Preview
    python scripts/clear_trade_ledger.py --stage dev             # Execute
    python scripts/clear_trade_ledger.py --stage prod            # Production (requires confirmation)
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import _setup_imports  # noqa: F401

import boto3
from botocore.exceptions import ClientError

# Table name pattern
TABLE_NAME_PATTERN = "alchemiser-{stage}-trade-ledger"

# Entity types to delete (preserving STRATEGY_METADATA for reuse)
ENTITIES_TO_DELETE = ["TRADE", "STRATEGY_LOT", "SIGNAL", "STRATEGY_TRADE"]

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def scan_items_to_delete(table, dry_run: bool = False) -> list[dict[str, Any]]:
    """Scan for items that should be deleted.
    
    Args:
        table: DynamoDB table resource
        dry_run: If True, just count items
        
    Returns:
        List of items to delete (with PK/SK keys)
    """
    items_to_delete: list[dict[str, Any]] = []
    last_key = None
    
    print("Scanning for items to delete...")
    
    while True:
        scan_kwargs: dict[str, Any] = {}
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key
            
        response = table.scan(**scan_kwargs)
        
        for item in response.get("Items", []):
            entity_type = item.get("EntityType", "")
            pk = item.get("PK", "")
            
            # Delete if entity type matches OR PK pattern matches (for items without EntityType)
            should_delete = (
                entity_type in ENTITIES_TO_DELETE
                or pk.startswith("TRADE#")
                or pk.startswith("LOT#")
                or pk.startswith("SIGNAL#")
            )
            
            # Don't delete strategy metadata
            if pk.startswith("STRATEGY#") and entity_type == "STRATEGY_METADATA":
                should_delete = False
                
            if should_delete:
                items_to_delete.append({
                    "PK": item["PK"],
                    "SK": item["SK"],
                })
                
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
            
        # Progress indicator
        print(f"  Scanned {len(items_to_delete)} items to delete so far...")
            
    return items_to_delete


def batch_delete_items(table, items: list[dict[str, Any]]) -> tuple[int, int]:
    """Delete items in batches of 25.
    
    Args:
        table: DynamoDB table resource
        items: List of items with PK/SK keys
        
    Returns:
        Tuple of (deleted_count, failed_count)
    """
    deleted = 0
    failed = 0
    
    # Process in batches of 25 (DynamoDB batch limit)
    batch_size = 25
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        try:
            with table.batch_writer() as writer:
                for item in batch:
                    writer.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
            deleted += len(batch)
            
            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f"  Progress: {batch_num}/{total_batches} batches ({deleted} items deleted)")
                
        except ClientError as e:
            print(f"  {RED}Batch {batch_num} failed: {e}{RESET}")
            failed += len(batch)
            
    return deleted, failed


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clear trade ledger data from DynamoDB"
    )
    parser.add_argument(
        "--stage",
        choices=["dev", "staging", "prod"],
        required=True,
        help="Environment stage",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    
    args = parser.parse_args()
    table_name = TABLE_NAME_PATTERN.format(stage=args.stage)
    
    print(f"\n{'=' * 60}")
    print(f" Trade Ledger Cleaner - {args.stage.upper()}")
    print(f"{'=' * 60}")
    print(f"Table: {table_name}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE DELETE'}")
    print()
    
    # Require confirmation for prod
    if args.stage == "prod" and not args.dry_run:
        print(f"{RED}⚠️  WARNING: This will DELETE ALL trade data from PRODUCTION!{RESET}")
        print(f"{RED}   This action cannot be undone.{RESET}")
        print()
        confirm = input("Type 'DELETE PROD DATA' to confirm: ")
        if confirm != "DELETE PROD DATA":
            print("Cancelled.")
            return 1
        print()
        
    # Connect to DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    
    # Scan for items to delete
    items_to_delete = scan_items_to_delete(table, dry_run=args.dry_run)
    
    print(f"\nFound {len(items_to_delete)} items to delete")
    print(f"  (Preserving STRATEGY_METADATA entities)")
    
    if not items_to_delete:
        print(f"\n{GREEN}✓ No items to delete{RESET}")
        return 0
        
    if args.dry_run:
        print(f"\n{YELLOW}DRY RUN: Would delete {len(items_to_delete)} items{RESET}")
        
        # Show sample of what would be deleted
        print("\nSample items that would be deleted:")
        for item in items_to_delete[:10]:
            print(f"  - PK: {item['PK'][:50]}... SK: {item['SK']}")
        if len(items_to_delete) > 10:
            print(f"  ... and {len(items_to_delete) - 10} more")
            
        return 0
        
    # Actually delete
    print(f"\nDeleting {len(items_to_delete)} items...")
    deleted, failed = batch_delete_items(table, items_to_delete)
    
    print(f"\n{'=' * 60}")
    if failed == 0:
        print(f"{GREEN}✓ Successfully deleted {deleted} items{RESET}")
    else:
        print(f"{YELLOW}⚠ Deleted {deleted} items, {failed} failed{RESET}")
    print(f"{'=' * 60}\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
