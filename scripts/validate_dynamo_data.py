#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

DynamoDB data validation script for per-strategy performance metrics.

This script queries production DynamoDB tables and validates that the data
captured is correct and complete enough to provide robust per-strategy
performance metrics.

Validates:
1. TradeLedgerTable entity completeness (TRADE, STRATEGY_LOT, SIGNAL, STRATEGY_METADATA)
2. Strategy attribution on trades (strategy_names, strategy_weights)
3. Lot data quality (entry/exit records, P&L calculations)
4. Data linkage (correlation_id chains, signal-to-trade matching)

Usage:
    make validate-dynamo                    # Validate prod data (default)
    make validate-dynamo stage=dev          # Validate dev data
    make validate-dynamo verbose=1          # Show detailed output
    make validate-dynamo fix=1              # Attempt to fix issues (dry-run)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import _setup_imports  # noqa: F401

import boto3
from botocore.exceptions import ClientError

# Constants
TABLE_NAME_PATTERN = "alchemiser-{stage}-trade-ledger"

# ANSI colors for terminal output
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def colorize(text: str, color: str) -> str:
    """Add ANSI color codes to text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    check_name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # "error", "warning", "info"

    def __str__(self) -> str:
        status = colorize("✓ PASS", "green") if self.passed else colorize("✗ FAIL", "red")
        if not self.passed and self.severity == "warning":
            status = colorize("⚠ WARN", "yellow")
        return f"{status} {self.check_name}: {self.message}"


@dataclass
class DataQualityReport:
    """Aggregate report of all validation checks."""

    stage: str
    table_name: str
    timestamp: datetime
    results: list[ValidationResult] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    strategy_summary: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Check if all critical validations passed."""
        return all(r.passed or r.severity != "error" for r in self.results)

    @property
    def error_count(self) -> int:
        """Count of failed error-level checks."""
        return sum(1 for r in self.results if not r.passed and r.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of failed warning-level checks."""
        return sum(1 for r in self.results if not r.passed and r.severity == "warning")


class DynamoDBValidator:
    """Validates DynamoDB data quality for per-strategy metrics."""

    def __init__(self, stage: str, verbose: bool = False) -> None:
        """Initialize validator with AWS resources.

        Args:
            stage: Environment stage (dev, staging, prod)
            verbose: Enable verbose output

        """
        self.stage = stage
        self.verbose = verbose
        self.table_name = TABLE_NAME_PATTERN.format(stage=stage)
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

        # Data collections for analysis
        self.trades: list[dict[str, Any]] = []
        self.lots: list[dict[str, Any]] = []
        self.signals: list[dict[str, Any]] = []
        self.strategy_metadata: list[dict[str, Any]] = []

    def log(self, msg: str, level: str = "info") -> None:
        """Log message with appropriate formatting."""
        if level == "verbose" and not self.verbose:
            return
        prefix = {
            "info": colorize("ℹ", "blue"),
            "success": colorize("✓", "green"),
            "warning": colorize("⚠", "yellow"),
            "error": colorize("✗", "red"),
            "verbose": colorize("→", "blue"),
        }.get(level, "")
        print(f"{prefix} {msg}")

    def fetch_all_entities(self) -> bool:
        """Scan table and categorize entities by type.

        Returns:
            True if fetch succeeded, False otherwise

        """
        self.log(f"Scanning table: {self.table_name}...")

        try:
            # Scan with pagination
            items: list[dict[str, Any]] = []
            last_key = None

            while True:
                scan_kwargs: dict[str, Any] = {"Limit": 1000}
                if last_key:
                    scan_kwargs["ExclusiveStartKey"] = last_key

                response = self.table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))
                last_key = response.get("LastEvaluatedKey")

                if not last_key:
                    break

            self.log(f"Retrieved {len(items)} items from DynamoDB", "success")

            # Categorize by entity type
            for item in items:
                entity_type = item.get("EntityType", "UNKNOWN")
                pk = item.get("PK", "")

                if entity_type == "TRADE" or pk.startswith("TRADE#"):
                    self.trades.append(item)
                elif entity_type == "STRATEGY_LOT" or pk.startswith("LOT#"):
                    self.lots.append(item)
                elif entity_type == "SIGNAL" or pk.startswith("SIGNAL#"):
                    self.signals.append(item)
                elif entity_type == "STRATEGY_METADATA" or pk.startswith("STRATEGY#"):
                    self.strategy_metadata.append(item)

            return True

        except ClientError as e:
            self.log(f"Failed to scan table: {e}", "error")
            return False

    def validate_entity_counts(self) -> ValidationResult:
        """Check that we have entities of each type."""
        counts = {
            "trades": len(self.trades),
            "lots": len(self.lots),
            "signals": len(self.signals),
            "strategy_metadata": len(self.strategy_metadata),
        }

        # Determine pass/fail
        has_trades = counts["trades"] > 0
        has_lots = counts["lots"] > 0

        if has_trades and has_lots:
            return ValidationResult(
                check_name="Entity Counts",
                passed=True,
                message=f"Found {counts['trades']} trades, {counts['lots']} lots, "
                f"{counts['signals']} signals, {counts['strategy_metadata']} strategy metadata",
                details=counts,
            )
        elif has_trades and not has_lots:
            return ValidationResult(
                check_name="Entity Counts",
                passed=False,
                message="Found trades but no strategy lots - P&L tracking may be incomplete",
                details=counts,
                severity="warning",
            )
        else:
            return ValidationResult(
                check_name="Entity Counts",
                passed=False,
                message="No trade data found in table",
                details=counts,
                severity="error",
            )

    def validate_trade_strategy_attribution(self) -> ValidationResult:
        """Check that trades have proper strategy attribution."""
        total_trades = len(self.trades)
        if total_trades == 0:
            return ValidationResult(
                check_name="Trade Strategy Attribution",
                passed=False,
                message="No trades to validate",
                severity="warning",
            )

        trades_with_strategy = 0
        trades_with_weights = 0
        missing_attribution: list[str] = []

        for trade in self.trades:
            strategy_names = trade.get("strategy_names", [])
            strategy_weights = trade.get("strategy_weights")

            if strategy_names and len(strategy_names) > 0:
                trades_with_strategy += 1
                if strategy_weights:
                    trades_with_weights += 1
            else:
                order_id = trade.get("order_id", trade.get("PK", "unknown"))
                missing_attribution.append(order_id)

        attribution_pct = (trades_with_strategy / total_trades) * 100 if total_trades > 0 else 0

        details = {
            "total_trades": total_trades,
            "with_strategy_names": trades_with_strategy,
            "with_strategy_weights": trades_with_weights,
            "attribution_percentage": round(attribution_pct, 1),
            "missing_attribution_sample": missing_attribution[:5],
        }

        if attribution_pct >= 95:
            return ValidationResult(
                check_name="Trade Strategy Attribution",
                passed=True,
                message=f"{attribution_pct:.1f}% of trades have strategy attribution",
                details=details,
            )
        elif attribution_pct >= 80:
            return ValidationResult(
                check_name="Trade Strategy Attribution",
                passed=False,
                message=f"Only {attribution_pct:.1f}% of trades have strategy attribution",
                details=details,
                severity="warning",
            )
        else:
            return ValidationResult(
                check_name="Trade Strategy Attribution",
                passed=False,
                message=f"Only {attribution_pct:.1f}% of trades have strategy attribution - "
                "per-strategy metrics will be incomplete",
                details=details,
                severity="error",
            )

    def validate_lot_data_quality(self) -> ValidationResult:
        """Check that lots have valid entry/exit data for P&L calculation."""
        total_lots = len(self.lots)
        if total_lots == 0:
            return ValidationResult(
                check_name="Lot Data Quality",
                passed=False,
                message="No strategy lots found - cannot calculate per-strategy P&L",
                severity="error",
            )

        valid_lots = 0
        open_lots = 0
        closed_lots = 0
        lots_with_exits = 0
        issues: list[str] = []

        for lot in self.lots:
            lot_id = lot.get("lot_id", lot.get("PK", "unknown"))
            is_valid = True

            # Check required fields
            required_fields = [
                "strategy_name",
                "symbol",
                "entry_qty",
                "entry_price",
                "remaining_qty",
            ]
            for field_name in required_fields:
                if field_name not in lot:
                    issues.append(f"Lot {lot_id} missing {field_name}")
                    is_valid = False
                    break

            if not is_valid:
                continue

            # Validate numeric fields
            try:
                entry_qty = Decimal(str(lot.get("entry_qty", 0)))
                entry_price = Decimal(str(lot.get("entry_price", 0)))
                remaining_qty = Decimal(str(lot.get("remaining_qty", 0)))

                if entry_qty <= 0:
                    issues.append(f"Lot {lot_id} has invalid entry_qty: {entry_qty}")
                    is_valid = False
                if entry_price <= 0:
                    issues.append(f"Lot {lot_id} has invalid entry_price: {entry_price}")
                    is_valid = False
                if remaining_qty < 0:
                    issues.append(f"Lot {lot_id} has negative remaining_qty: {remaining_qty}")
                    is_valid = False

            except (InvalidOperation, TypeError) as e:
                issues.append(f"Lot {lot_id} has invalid numeric data: {e}")
                is_valid = False

            if is_valid:
                valid_lots += 1
                is_open = lot.get("is_open", True)
                if is_open:
                    open_lots += 1
                else:
                    closed_lots += 1

                exit_records = lot.get("exit_records", [])
                if exit_records:
                    lots_with_exits += 1

        validity_pct = (valid_lots / total_lots) * 100 if total_lots > 0 else 0

        details = {
            "total_lots": total_lots,
            "valid_lots": valid_lots,
            "open_lots": open_lots,
            "closed_lots": closed_lots,
            "lots_with_exits": lots_with_exits,
            "validity_percentage": round(validity_pct, 1),
            "issues_sample": issues[:5],
        }

        if validity_pct >= 95:
            return ValidationResult(
                check_name="Lot Data Quality",
                passed=True,
                message=f"{valid_lots} valid lots ({open_lots} open, {closed_lots} closed)",
                details=details,
            )
        else:
            return ValidationResult(
                check_name="Lot Data Quality",
                passed=False,
                message=f"Only {validity_pct:.1f}% of lots have valid data",
                details=details,
                severity="error" if validity_pct < 80 else "warning",
            )

    def validate_pnl_calculations(self) -> ValidationResult:
        """Verify P&L calculations are correct on closed lots."""
        closed_lots = [lot for lot in self.lots if not lot.get("is_open", True)]

        if not closed_lots:
            return ValidationResult(
                check_name="P&L Calculations",
                passed=True,
                message="No closed lots to validate P&L (all positions still open)",
                severity="info",
            )

        correct_pnl = 0
        incorrect_pnl = 0
        calculation_errors: list[dict[str, Any]] = []

        for lot in closed_lots:
            lot_id = lot.get("lot_id", "unknown")
            exit_records = lot.get("exit_records", [])

            if not exit_records:
                continue

            try:
                entry_price = Decimal(str(lot.get("entry_price", 0)))
                stored_pnl = Decimal(str(lot.get("realized_pnl", 0)))

                # Calculate expected P&L from exit records
                calculated_pnl = Decimal("0")
                for exit_rec in exit_records:
                    exit_qty = Decimal(str(exit_rec.get("exit_qty", 0)))
                    exit_price = Decimal(str(exit_rec.get("exit_price", 0)))
                    calculated_pnl += (exit_price - entry_price) * exit_qty

                # Allow small tolerance for rounding
                diff = abs(stored_pnl - calculated_pnl)
                if diff <= Decimal("0.01"):
                    correct_pnl += 1
                else:
                    incorrect_pnl += 1
                    calculation_errors.append(
                        {
                            "lot_id": lot_id,
                            "stored_pnl": str(stored_pnl),
                            "calculated_pnl": str(calculated_pnl),
                            "difference": str(diff),
                        }
                    )

            except (InvalidOperation, TypeError, KeyError) as e:
                calculation_errors.append({"lot_id": lot_id, "error": str(e)})

        total_checked = correct_pnl + incorrect_pnl
        accuracy_pct = (correct_pnl / total_checked) * 100 if total_checked > 0 else 100

        details = {
            "closed_lots_checked": total_checked,
            "correct_pnl": correct_pnl,
            "incorrect_pnl": incorrect_pnl,
            "accuracy_percentage": round(accuracy_pct, 1),
            "errors_sample": calculation_errors[:3],
        }

        if accuracy_pct >= 99:
            return ValidationResult(
                check_name="P&L Calculations",
                passed=True,
                message=f"P&L calculations verified for {total_checked} closed lots",
                details=details,
            )
        else:
            return ValidationResult(
                check_name="P&L Calculations",
                passed=False,
                message=f"P&L calculation errors in {incorrect_pnl} lots",
                details=details,
                severity="error",
            )

    def validate_strategy_coverage(self) -> ValidationResult:
        """Check which strategies have data and their completeness."""
        strategy_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"trades": 0, "lots": 0, "open_lots": 0, "closed_lots": 0}
        )

        # Count trades per strategy
        for trade in self.trades:
            strategy_names = trade.get("strategy_names", [])
            for name in strategy_names:
                strategy_stats[name]["trades"] += 1

        # Count lots per strategy
        for lot in self.lots:
            strategy_name = lot.get("strategy_name", "UNKNOWN")
            strategy_stats[strategy_name]["lots"] += 1
            if lot.get("is_open", True):
                strategy_stats[strategy_name]["open_lots"] += 1
            else:
                strategy_stats[strategy_name]["closed_lots"] += 1

        # Check for strategies with unbalanced data
        issues: list[str] = []
        strategies_ready = 0

        for name, stats in strategy_stats.items():
            if name == "UNKNOWN":
                continue

            if stats["trades"] > 0 and stats["lots"] == 0:
                issues.append(f"{name}: {stats['trades']} trades but no lots")
            elif stats["lots"] > 0:
                strategies_ready += 1

        details = {
            "strategies_found": len(strategy_stats),
            "strategies_ready_for_metrics": strategies_ready,
            "strategy_breakdown": dict(strategy_stats),
            "issues": issues,
        }

        if strategies_ready > 0 and not issues:
            return ValidationResult(
                check_name="Strategy Coverage",
                passed=True,
                message=f"{strategies_ready} strategies have complete data for metrics",
                details=details,
            )
        elif strategies_ready > 0:
            return ValidationResult(
                check_name="Strategy Coverage",
                passed=False,
                message=f"{strategies_ready} strategies ready, but {len(issues)} have issues",
                details=details,
                severity="warning",
            )
        else:
            return ValidationResult(
                check_name="Strategy Coverage",
                passed=False,
                message="No strategies have complete lot data",
                details=details,
                severity="error",
            )

    def validate_correlation_chain(self) -> ValidationResult:
        """Validate that correlation_ids link entities correctly."""
        # Build correlation_id -> entities mapping
        correlation_map: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: {"trades": [], "lots": [], "signals": []}
        )

        for trade in self.trades:
            corr_id = trade.get("correlation_id")
            if corr_id:
                correlation_map[corr_id]["trades"].append(trade.get("order_id", "unknown"))

        for lot in self.lots:
            corr_id = lot.get("correlation_id")
            if corr_id:
                correlation_map[corr_id]["lots"].append(lot.get("lot_id", "unknown"))

        for signal in self.signals:
            corr_id = signal.get("correlation_id")
            if corr_id:
                correlation_map[corr_id]["signals"].append(signal.get("signal_id", "unknown"))

        # Analyze correlation chains
        complete_chains = 0
        partial_chains = 0
        orphan_trades = 0

        for corr_id, entities in correlation_map.items():
            has_trades = len(entities["trades"]) > 0
            has_lots = len(entities["lots"]) > 0

            if has_trades and has_lots:
                complete_chains += 1
            elif has_trades:
                orphan_trades += len(entities["trades"])
                partial_chains += 1

        details = {
            "total_correlation_ids": len(correlation_map),
            "complete_chains": complete_chains,
            "partial_chains": partial_chains,
            "orphan_trades": orphan_trades,
        }

        if complete_chains > 0 and orphan_trades == 0:
            return ValidationResult(
                check_name="Correlation Chain Integrity",
                passed=True,
                message=f"{complete_chains} complete trade-lot correlation chains",
                details=details,
            )
        elif complete_chains > 0:
            return ValidationResult(
                check_name="Correlation Chain Integrity",
                passed=False,
                message=f"{orphan_trades} trades without matching lots (may be pre-existing positions)",
                details=details,
                severity="warning",
            )
        else:
            return ValidationResult(
                check_name="Correlation Chain Integrity",
                passed=False,
                message="No complete correlation chains found",
                details=details,
                severity="error",
            )

    def generate_strategy_summary(self) -> dict[str, dict[str, Any]]:
        """Generate per-strategy metrics summary."""
        summary: dict[str, dict[str, Any]] = {}

        for lot in self.lots:
            strategy = lot.get("strategy_name", "UNKNOWN")
            if strategy not in summary:
                summary[strategy] = {
                    "total_lots": 0,
                    "open_lots": 0,
                    "closed_lots": 0,
                    "realized_pnl": Decimal("0"),
                    "open_cost_basis": Decimal("0"),
                    "symbols": set(),
                }

            summary[strategy]["total_lots"] += 1
            summary[strategy]["symbols"].add(lot.get("symbol", "???"))

            is_open = lot.get("is_open", True)
            if is_open:
                summary[strategy]["open_lots"] += 1
                try:
                    entry_qty = Decimal(str(lot.get("entry_qty", 0)))
                    entry_price = Decimal(str(lot.get("entry_price", 0)))
                    remaining_qty = Decimal(str(lot.get("remaining_qty", 0)))
                    cost_basis = remaining_qty * entry_price
                    summary[strategy]["open_cost_basis"] += cost_basis
                except (InvalidOperation, TypeError):
                    pass
            else:
                summary[strategy]["closed_lots"] += 1
                try:
                    pnl = Decimal(str(lot.get("realized_pnl", 0)))
                    summary[strategy]["realized_pnl"] += pnl
                except (InvalidOperation, TypeError):
                    pass

        # Convert sets to lists for JSON serialization
        for strategy in summary:
            summary[strategy]["symbols"] = list(summary[strategy]["symbols"])
            summary[strategy]["realized_pnl"] = str(summary[strategy]["realized_pnl"])
            summary[strategy]["open_cost_basis"] = str(summary[strategy]["open_cost_basis"])

        return summary

    def run_validation(self) -> DataQualityReport:
        """Run all validation checks and return report."""
        report = DataQualityReport(
            stage=self.stage,
            table_name=self.table_name,
            timestamp=datetime.now(UTC),
        )

        # Fetch data
        if not self.fetch_all_entities():
            report.results.append(
                ValidationResult(
                    check_name="Data Fetch",
                    passed=False,
                    message="Failed to fetch data from DynamoDB",
                    severity="error",
                )
            )
            return report

        report.entity_counts = {
            "trades": len(self.trades),
            "lots": len(self.lots),
            "signals": len(self.signals),
            "strategy_metadata": len(self.strategy_metadata),
        }

        # Run validation checks
        checks = [
            self.validate_entity_counts,
            self.validate_trade_strategy_attribution,
            self.validate_lot_data_quality,
            self.validate_pnl_calculations,
            self.validate_strategy_coverage,
            self.validate_correlation_chain,
        ]

        for check in checks:
            try:
                result = check()
                report.results.append(result)
            except Exception as e:
                report.results.append(
                    ValidationResult(
                        check_name=check.__name__.replace("validate_", "").replace("_", " ").title(),
                        passed=False,
                        message=f"Check failed with exception: {e}",
                        severity="error",
                    )
                )

        # Generate strategy summary
        report.strategy_summary = self.generate_strategy_summary()

        return report


def print_report(report: DataQualityReport, verbose: bool = False) -> None:
    """Print formatted validation report."""
    print()
    print(colorize("=" * 70, "bold"))
    print(colorize(f" DynamoDB Data Quality Report - {report.stage.upper()}", "bold"))
    print(colorize("=" * 70, "bold"))
    print()
    print(f"Table: {report.table_name}")
    print(f"Timestamp: {report.timestamp.isoformat()}")
    print()

    # Entity counts
    print(colorize("📊 Entity Counts:", "bold"))
    for entity, count in report.entity_counts.items():
        print(f"   {entity}: {count}")
    print()

    # Validation results
    print(colorize("🔍 Validation Results:", "bold"))
    for result in report.results:
        print(f"   {result}")
        if verbose and result.details:
            for key, value in result.details.items():
                if isinstance(value, list) and len(value) > 3:
                    print(f"      {key}: {value[:3]} ... ({len(value)} total)")
                elif isinstance(value, dict) and len(value) > 5:
                    print(f"      {key}: (truncated, {len(value)} items)")
                else:
                    print(f"      {key}: {value}")
    print()

    # Strategy summary
    if report.strategy_summary:
        print(colorize("📈 Per-Strategy Summary:", "bold"))
        for strategy, stats in sorted(report.strategy_summary.items()):
            if strategy == "UNKNOWN":
                continue
            pnl = stats.get("realized_pnl", "0")
            pnl_color = "green" if float(pnl) >= 0 else "red"
            print(f"   {colorize(strategy, 'bold')}:")
            print(
                f"      Lots: {stats['total_lots']} ({stats['open_lots']} open, {stats['closed_lots']} closed)"
            )
            print(f"      Realized P&L: {colorize(f'${pnl}', pnl_color)}")
            print(f"      Open Cost Basis: ${stats['open_cost_basis']}")
            print(f"      Symbols: {', '.join(stats['symbols'][:5])}")
        print()

    # Summary
    print(colorize("=" * 70, "bold"))
    if report.passed:
        print(colorize("✅ OVERALL: Data is ready for per-strategy performance metrics", "green"))
    else:
        if report.error_count > 0:
            print(
                colorize(
                    f"❌ OVERALL: {report.error_count} errors, {report.warning_count} warnings - "
                    "data quality issues need attention",
                    "red",
                )
            )
        else:
            print(
                colorize(
                    f"⚠️ OVERALL: {report.warning_count} warnings - data is usable but has gaps",
                    "yellow",
                )
            )
    print(colorize("=" * 70, "bold"))
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate DynamoDB data quality for per-strategy performance metrics"
    )
    parser.add_argument(
        "--stage",
        choices=["dev", "staging", "prod"],
        default="prod",
        help="Environment stage (default: prod)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    # Run validation
    validator = DynamoDBValidator(stage=args.stage, verbose=args.verbose)
    report = validator.run_validation()

    if args.json:
        # Output as JSON
        output = {
            "stage": report.stage,
            "table_name": report.table_name,
            "timestamp": report.timestamp.isoformat(),
            "passed": report.passed,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "entity_counts": report.entity_counts,
            "results": [
                {
                    "check_name": r.check_name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details,
                }
                for r in report.results
            ],
            "strategy_summary": report.strategy_summary,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print_report(report, verbose=args.verbose)

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
