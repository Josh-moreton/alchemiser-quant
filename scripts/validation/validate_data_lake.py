#!/usr/bin/env python3
"""Business Unit: data | Status: current.

Comprehensive S3 data lake validation against yfinance.

Validates:
1. Completeness - All symbols from strategy DSL configs exist in S3
2. Freshness - S3 data has the latest complete bar available on yfinance
3. Integrity - Close prices match yfinance Adj Close within tolerance
4. Gaps - No missing trading days in the data series

Usage:
    make validate-data-lake                    # Validate all configured symbols
    make validate-data-lake symbols=SPY,QQQ   # Validate specific symbols
    make validate-data-lake mark-bad=1        # Mark failed symbols for refetch
    make validate-data-lake debug=1           # Show sample mismatches
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
import pandas as pd
import yfinance as yf
from botocore.exceptions import ClientError

# Suppress yfinance warnings
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Price tolerance: maximum allowed difference between S3 close and yfinance Adj Close
PRICE_TOLERANCE_PCT = 0.02  # 2%

# S3 bucket for market data (production)
DEFAULT_BUCKET = "alchemiser-prod-market-data"

# Default AWS region
DEFAULT_REGION = "us-east-1"

# Output directory for validation reports
VALIDATION_RESULTS_DIR = Path(__file__).parent.parent.parent / "validation_results"

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


# ============================================================================
# VALIDATION RESULT DATA CLASSES
# ============================================================================


@dataclass
class SymbolValidationResult:
    """Result of validating a single symbol."""

    symbol: str
    s3_records: int = 0
    yf_records: int = 0
    s3_last_date: str = ""
    yf_last_date: str = ""
    is_fresh: bool = False
    price_mismatches: int = 0
    missing_dates: int = 0  # dates in yfinance but not S3 (gaps)
    errors: list[str] = field(default_factory=list)
    sample_mismatches: list[dict[str, Any]] = field(default_factory=list)
    sample_missing_dates: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Symbol passes all validation checks."""
        return (
            self.is_fresh
            and self.price_mismatches == 0
            and self.missing_dates == 0
            and not self.errors
        )

    @property
    def status(self) -> str:
        """Human-readable status."""
        if self.errors:
            return "ERROR"
        if not self.is_fresh:
            return "STALE"
        if self.price_mismatches > 0:
            return "MISMATCH"
        if self.missing_dates > 0:
            return "GAPS"
        return "VALID"


@dataclass
class DataLakeValidationReport:
    """Aggregate report of all symbol validations."""

    bucket: str
    timestamp: datetime
    results: list[SymbolValidationResult] = field(default_factory=list)
    configured_symbols: set[str] = field(default_factory=set)
    s3_symbols: set[str] = field(default_factory=set)

    @property
    def missing_symbols(self) -> set[str]:
        """Symbols configured but not in S3."""
        return self.configured_symbols - self.s3_symbols

    @property
    def valid_count(self) -> int:
        """Count of valid symbols."""
        return sum(1 for r in self.results if r.is_valid)

    @property
    def stale_count(self) -> int:
        """Count of stale symbols (not fresh)."""
        return sum(1 for r in self.results if not r.is_fresh and not r.errors)

    @property
    def mismatch_count(self) -> int:
        """Count of symbols with price mismatches."""
        return sum(1 for r in self.results if r.price_mismatches > 0)

    @property
    def gap_count(self) -> int:
        """Count of symbols with data gaps."""
        return sum(1 for r in self.results if r.missing_dates > 0)

    @property
    def error_count(self) -> int:
        """Count of symbols with errors."""
        return sum(1 for r in self.results if r.errors)


# ============================================================================
# S3 DATA ACCESS
# ============================================================================


def list_s3_symbols(s3_client: Any, bucket: str) -> set[str]:
    """List all symbols in S3 bucket.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name

    Returns:
        Set of symbol names (folder prefixes)
    """
    symbols: set[str] = set()
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for prefix in page.get("CommonPrefixes", []):
            symbol = prefix["Prefix"].rstrip("/")
            if symbol:
                symbols.add(symbol)

    return symbols


def read_s3_parquet(s3_client: Any, bucket: str, symbol: str) -> pd.DataFrame | None:
    """Read parquet data from S3 for a symbol.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        symbol: Symbol to read

    Returns:
        DataFrame with market data or None if not found
    """
    try:
        key = f"{symbol}/daily.parquet"
        response = s3_client.get_object(Bucket=bucket, Key=key)

        # Write to temp file and read
        temp_path = Path("/tmp/temp_validation.parquet")
        with temp_path.open("wb") as f:
            f.write(response["Body"].read())

        df = pd.read_parquet(temp_path)
        temp_path.unlink()
        return df

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


# ============================================================================
# YFINANCE DATA ACCESS
# ============================================================================


def fetch_yfinance_data(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """Fetch yfinance data with Adj Close.

    Args:
        symbol: Ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD), inclusive

    Returns:
        DataFrame with OHLCV + Adj Close or None if fetch failed
    """
    try:
        # Add one day to end because yfinance is exclusive on end date
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)

        df = yf.download(
            symbol,
            start=start,
            end=end_dt.strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
        )

        if df is None or df.empty:
            return None

        # Flatten multi-index columns if needed (yfinance behavior varies)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except Exception:
        return None


def get_yfinance_latest_date(symbol: str) -> str | None:
    """Get the latest complete bar date from yfinance.

    Fetches recent data and returns the most recent date available.
    This accounts for weekends, holidays, and market closures.

    Args:
        symbol: Ticker symbol

    Returns:
        Latest date as YYYY-MM-DD string, or None if fetch failed
    """
    try:
        # Fetch last 10 days to ensure we get the latest bar
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=10)

        df = yf.download(
            symbol,
            start=start_dt.strftime("%Y-%m-%d"),
            end=end_dt.strftime("%Y-%m-%d"),
            auto_adjust=False,
            progress=False,
        )

        if df is None or df.empty:
            return None

        # Return the last date in the index
        return df.index[-1].strftime("%Y-%m-%d")

    except Exception:
        return None


# ============================================================================
# SYMBOL EXTRACTION FROM DSL CONFIGS
# ============================================================================


def get_configured_symbols() -> set[str]:
    """Get all symbols from strategy DSL configurations.

    Uses the symbol_extractor from the data Lambda function.

    Returns:
        Set of unique ticker symbols across all configured strategies
    """
    # Add the layers/shared directory to path for imports
    layers_shared = Path(__file__).parent.parent.parent / "layers" / "shared"
    functions_data = Path(__file__).parent.parent.parent / "functions" / "data"

    if str(layers_shared) not in sys.path:
        sys.path.insert(0, str(layers_shared))
    if str(functions_data) not in sys.path:
        sys.path.insert(0, str(functions_data))

    try:
        from symbol_extractor import get_all_configured_symbols

        return get_all_configured_symbols()
    except ImportError as e:
        print(f"Warning: Could not import symbol_extractor: {e}")
        print("Falling back to S3 symbol list only")
        return set()


# ============================================================================
# VALIDATION LOGIC
# ============================================================================


def validate_symbol(
    symbol: str,
    s3_client: Any,
    bucket: str,
    debug: bool = False,
) -> SymbolValidationResult:
    """Validate a single symbol against yfinance.

    Checks:
    1. Freshness - S3 has the latest bar available on yfinance
    2. Price integrity - Close prices match yfinance Adj Close within tolerance
    3. Gaps - No missing trading days

    Args:
        symbol: Symbol to validate
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        debug: Show detailed debug output

    Returns:
        SymbolValidationResult with validation details
    """
    result = SymbolValidationResult(symbol=symbol)

    # 1. Read S3 data
    s3_df = read_s3_parquet(s3_client, bucket, symbol)
    if s3_df is None:
        result.errors.append("No S3 data")
        return result

    result.s3_records = len(s3_df)

    # Normalize S3 timestamps to date strings
    s3_df["date"] = pd.to_datetime(s3_df["timestamp"]).dt.strftime("%Y-%m-%d")
    s3_by_date = s3_df.set_index("date")["close"].to_dict()

    s3_start = min(s3_by_date.keys())
    s3_end = max(s3_by_date.keys())
    result.s3_last_date = s3_end

    # 2. Get yfinance latest date for freshness check
    yf_latest = get_yfinance_latest_date(symbol)
    if yf_latest is None:
        result.errors.append("Failed to fetch yfinance latest date")
        return result

    result.yf_last_date = yf_latest

    # 3. Freshness check - S3 must have the same latest date as yfinance
    result.is_fresh = s3_end >= yf_latest

    # 4. Fetch full yfinance data for price comparison
    yf_df = fetch_yfinance_data(symbol, s3_start, yf_latest)
    if yf_df is None:
        result.errors.append("Failed to fetch yfinance data")
        return result

    # Flatten multi-index if needed
    if isinstance(yf_df.columns, pd.MultiIndex):
        yf_df.columns = yf_df.columns.get_level_values(0)

    result.yf_records = len(yf_df)

    # Use Adj Close for comparison (accounts for splits/dividends)
    adj_close_col = "Adj Close" if "Adj Close" in yf_df.columns else "Close"
    yf_df["date"] = yf_df.index.strftime("%Y-%m-%d")
    yf_by_date = yf_df.set_index("date")[adj_close_col].to_dict()

    # 5. Compare prices and check for gaps
    for date, yf_price in yf_by_date.items():
        if date not in s3_by_date:
            # Gap - date in yfinance but not in S3
            result.missing_dates += 1
            if len(result.sample_missing_dates) < 5:
                result.sample_missing_dates.append(date)
            continue

        s3_price = s3_by_date[date]

        # Avoid division by zero
        if max(abs(s3_price), abs(yf_price)) == 0:
            continue

        pct_diff = abs(s3_price - yf_price) / max(abs(s3_price), abs(yf_price))

        if pct_diff > PRICE_TOLERANCE_PCT:
            result.price_mismatches += 1
            if len(result.sample_mismatches) < 5:
                result.sample_mismatches.append({
                    "date": date,
                    "s3_close": round(s3_price, 4),
                    "yf_adj_close": round(yf_price, 4),
                    "diff_pct": round(pct_diff * 100, 2),
                })

    return result


# ============================================================================
# BAD DATA MARKERS (for automatic refetch)
# ============================================================================


def write_bad_data_markers(results: list[SymbolValidationResult], region: str) -> int:
    """Write DynamoDB markers for symbols that need refetch.

    Args:
        results: List of validation results
        region: AWS region

    Returns:
        Number of markers written
    """
    # Import the marker service
    layers_shared = Path(__file__).parent.parent.parent / "layers" / "shared"
    if str(layers_shared) not in sys.path:
        sys.path.insert(0, str(layers_shared))

    try:
        from the_alchemiser.data_v2.bad_data_marker_service import BadDataMarkerService
    except ImportError:
        print("Warning: Could not import BadDataMarkerService")
        return 0

    table_name = "alchemiser-bad-data-markers"
    marker_service = BadDataMarkerService(table_name=table_name)
    count = 0

    for r in results:
        if r.is_valid:
            continue

        # Determine reason
        if not r.is_fresh:
            reason = "stale_data"
        elif r.price_mismatches > 0:
            reason = "price_mismatch"
        elif r.missing_dates > 0:
            reason = "data_gaps"
        else:
            reason = "validation_error"

        if marker_service.mark_symbol_for_refetch(
            symbol=r.symbol,
            reason=reason,
            start_date=r.s3_last_date,
            end_date=r.yf_last_date,
            detected_ratio=None,
            source="validate_data_lake",
        ):
            count += 1
            print(f"  Marked {r.symbol} for refetch ({reason})")

    return count


# ============================================================================
# REPORTING
# ============================================================================


def write_csv_report(report: DataLakeValidationReport, output_path: Path) -> None:
    """Write validation report to CSV.

    Args:
        report: Validation report
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Symbol",
            "Status",
            "S3 Records",
            "YF Records",
            "S3 Last Date",
            "YF Last Date",
            "Is Fresh",
            "Price Mismatches",
            "Missing Dates",
            "Errors",
        ])

        for r in report.results:
            writer.writerow([
                r.symbol,
                r.status,
                r.s3_records,
                r.yf_records,
                r.s3_last_date,
                r.yf_last_date,
                r.is_fresh,
                r.price_mismatches,
                r.missing_dates,
                "; ".join(r.errors) if r.errors else "",
            ])


def print_report(report: DataLakeValidationReport, debug: bool = False) -> None:
    """Print formatted validation report to terminal.

    Args:
        report: Validation report
        debug: Show detailed debug output
    """
    print()
    print(colorize("=" * 70, "bold"))
    print(colorize(" Data Lake Validation Report", "bold"))
    print(colorize("=" * 70, "bold"))
    print()
    print(f"Bucket: {report.bucket}")
    print(f"Timestamp: {report.timestamp.isoformat()}")
    print(f"Configured Symbols: {len(report.configured_symbols)}")
    print(f"S3 Symbols: {len(report.s3_symbols)}")
    print()

    # Missing symbols check
    if report.missing_symbols:
        print(colorize("⚠️  Missing from S3:", "yellow"))
        for s in sorted(report.missing_symbols):
            print(f"   {s}")
        print()

    # Summary counts
    print(colorize("📊 Validation Summary:", "bold"))
    print(f"   {colorize('✓ Valid:', 'green')} {report.valid_count}")
    print(f"   {colorize('⏰ Stale:', 'yellow')} {report.stale_count}")
    print(f"   {colorize('⚡ Price Mismatches:', 'red')} {report.mismatch_count}")
    print(f"   {colorize('📅 Data Gaps:', 'yellow')} {report.gap_count}")
    print(f"   {colorize('❌ Errors:', 'red')} {report.error_count}")
    print()

    # Detailed results for invalid symbols
    invalid_results = [r for r in report.results if not r.is_valid]
    if invalid_results:
        print(colorize("🔍 Invalid Symbols:", "bold"))
        for r in sorted(invalid_results, key=lambda x: x.symbol):
            status_color = "red" if r.errors or r.price_mismatches > 0 else "yellow"
            print(f"   {colorize(r.symbol, status_color)}: {r.status}")
            print(f"      S3 last: {r.s3_last_date} | YF last: {r.yf_last_date}")

            if r.price_mismatches > 0:
                print(f"      Price mismatches: {r.price_mismatches}")
                if debug and r.sample_mismatches:
                    for m in r.sample_mismatches[:3]:
                        print(
                            f"        {m['date']}: S3={m['s3_close']}, "
                            f"YF={m['yf_adj_close']}, diff={m['diff_pct']}%"
                        )

            if r.missing_dates > 0:
                print(f"      Missing dates: {r.missing_dates}")
                if debug and r.sample_missing_dates:
                    print(f"        Sample: {', '.join(r.sample_missing_dates[:5])}")

            if r.errors:
                print(f"      Errors: {', '.join(r.errors)}")
        print()

    # Overall status
    print(colorize("=" * 70, "bold"))
    if report.valid_count == len(report.results) and not report.missing_symbols:
        print(colorize("✅ OVERALL: Data lake is healthy!", "green"))
    else:
        issues = len(report.results) - report.valid_count + len(report.missing_symbols)
        print(colorize(f"⚠️  OVERALL: {issues} symbols need attention", "yellow"))
    print(colorize("=" * 70, "bold"))
    print()


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = validation failures)
    """
    parser = argparse.ArgumentParser(
        description="Validate S3 data lake against yfinance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols to validate (default: all configured)",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=DEFAULT_BUCKET,
        help=f"S3 bucket name (default: {DEFAULT_BUCKET})",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=DEFAULT_REGION,
        help=f"AWS region (default: {DEFAULT_REGION})",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV path (default: validation_results/data_lake_validation_<date>.csv)",
    )
    parser.add_argument(
        "--mark-bad",
        action="store_true",
        help="Write DynamoDB markers for symbols that need refetch",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed debug output (sample mismatches, etc.)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of symbols to validate (for testing)",
    )

    args = parser.parse_args()

    # Initialize S3 client
    s3_client = boto3.client("s3", region_name=args.region)

    # Get symbols to validate
    if args.symbols:
        symbols_to_validate = set(s.strip().upper() for s in args.symbols.split(","))
        configured_symbols = symbols_to_validate
    else:
        configured_symbols = get_configured_symbols()
        symbols_to_validate = configured_symbols

    # Get S3 symbols
    print("Scanning S3 bucket for symbols...")
    s3_symbols = list_s3_symbols(s3_client, args.bucket)
    print(f"Found {len(s3_symbols)} symbols in S3")

    # Filter to only symbols that exist in S3
    symbols_to_validate = symbols_to_validate & s3_symbols

    if args.limit:
        symbols_to_validate = set(sorted(symbols_to_validate)[:args.limit])

    print(f"Validating {len(symbols_to_validate)} symbols...")
    print()

    # Create report
    report = DataLakeValidationReport(
        bucket=args.bucket,
        timestamp=datetime.now(),
        configured_symbols=configured_symbols,
        s3_symbols=s3_symbols,
    )

    # Validate each symbol
    for i, symbol in enumerate(sorted(symbols_to_validate), 1):
        status_prefix = f"[{i}/{len(symbols_to_validate)}]"
        print(f"{status_prefix} Validating {symbol}...", end=" ", flush=True)

        result = validate_symbol(symbol, s3_client, args.bucket, debug=args.debug)
        report.results.append(result)

        # Print inline status
        if result.is_valid:
            print(colorize("✓", "green"))
        else:
            print(colorize(f"✗ ({result.status})", "red"))

    # Write CSV report
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = VALIDATION_RESULTS_DIR / f"data_lake_validation_{date_str}.csv"

    write_csv_report(report, output_path)
    print(f"\nReport saved to: {output_path}")

    # Print summary
    print_report(report, debug=args.debug)

    # Mark bad symbols if requested
    if args.mark_bad:
        invalid_results = [r for r in report.results if not r.is_valid]
        if invalid_results:
            print("Writing DynamoDB markers for refetch...")
            markers = write_bad_data_markers(invalid_results, args.region)
            print(f"Marked {markers} symbols for refetch")

    # Return exit code
    all_valid = report.valid_count == len(report.results) and not report.missing_symbols
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
