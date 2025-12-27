"""Business Unit: data | Status: current.

Validate S3 market data against yfinance for data integrity.

This script connects to the S3 datalake and validates each symbol's
entire data store against yfinance, checking date, price, and volume.
Discrepancies are logged for manual review.

Run locally (yfinance blocks Lambda IP ranges):
    python scripts/validate_s3_against_yfinance.py [--symbols AAPL,MSFT] [--output report.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import pandas as pd
import yfinance as yf
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DataPoint:
    """A single OHLCV data point."""

    date: str  # YYYY-MM-DD
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

    def __hash__(self) -> int:
        """Make hashable for set operations."""
        return hash((self.date, self.close_price, self.volume))

    def __eq__(self, other: object) -> bool:
        """Check equality allowing for minor float precision and volume differences.

        Tolerances:
        - Price: 0.02 (accounts for rounding differences between feeds)
        - Volume: 0.01% (accounts for minor reporting differences)
        """
        if not isinstance(other, DataPoint):
            return NotImplemented

        # Volume tolerance: allow 0.01% difference (min 100 shares)
        max_vol = max(self.volume, other.volume, 1)
        volume_tolerance = max(100, int(max_vol * 0.0001))
        volume_match = abs(self.volume - other.volume) <= volume_tolerance

        return (
            self.date == other.date
            and abs(self.open_price - other.open_price) < 0.02
            and abs(self.high_price - other.high_price) < 0.02
            and abs(self.low_price - other.low_price) < 0.02
            and abs(self.close_price - other.close_price) < 0.02
            and volume_match
        )


@dataclass
class SymbolValidationResult:
    """Result of validating a symbol against yfinance."""

    symbol: str
    s3_record_count: int
    yfinance_record_count: int
    s3_start_date: str = ""  # Earliest date in S3
    s3_end_date: str = ""  # Latest date in S3
    missing_in_s3: list[DataPoint] = field(default_factory=list)
    missing_in_yfinance: list[DataPoint] = field(default_factory=list)
    mismatched_records: list[tuple[DataPoint, DataPoint]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def missing_in_s3_recent(self) -> list[DataPoint]:
        """Records missing in S3 that are within the S3 date range (unexpected gaps)."""
        if not self.s3_start_date or not self.s3_end_date:
            return []
        return [
            p
            for p in self.missing_in_s3
            if self.s3_start_date <= p.date <= self.s3_end_date
        ]

    @property
    def missing_in_s3_historical(self) -> list[DataPoint]:
        """Records missing in S3 that are before S3 start date (expected - not seeded)."""
        if not self.s3_start_date:
            return self.missing_in_s3
        return [p for p in self.missing_in_s3 if p.date < self.s3_start_date]

    @property
    def is_valid(self) -> bool:
        """Check if symbol passed all validations.

        A symbol is valid if:
        - No unexpected gaps (missing within S3 date range)
        - No missing in yfinance (S3 has extra data somehow)
        - No price/volume mismatches
        - No errors

        Historical gaps (before S3 start date) are expected and don't fail validation.
        """
        return (
            not self.missing_in_s3_recent
            and not self.missing_in_yfinance
            and not self.mismatched_records
            and not self.errors
        )

    @property
    def discrepancy_count(self) -> int:
        """Total number of actionable discrepancies (excludes historical gaps)."""
        return (
            len(self.missing_in_s3_recent)
            + len(self.missing_in_yfinance)
            + len(self.mismatched_records)
        )

    @property
    def historical_gap_count(self) -> int:
        """Number of expected historical gaps (before S3 start date)."""
        return len(self.missing_in_s3_historical)


def read_s3_data(
    s3_client: "boto3.client",
    bucket: str,
    symbol: str,
) -> pd.DataFrame | None:
    """Read Parquet data for a symbol from S3.

    Args:
        s3_client: Initialized S3 client
        bucket: S3 bucket name
        symbol: Ticker symbol

    Returns:
        DataFrame with OHLCV data, or None if not found

    """
    try:
        key = f"{symbol}/daily.parquet"
        response = s3_client.get_object(Bucket=bucket, Key=key)

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            tmp.write(response["Body"].read())
            tmp_path = tmp.name

        df = pd.read_parquet(tmp_path, engine="pyarrow")
        Path(tmp_path).unlink()

        logger.info(f"Read {len(df)} records from S3 for {symbol}")
        return df

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.warning(f"No data found in S3 for {symbol}")
            return None
        raise
    except Exception as e:
        logger.error(f"Error reading S3 data for {symbol}: {e}")
        return None


def fetch_yfinance_data(symbol: str, max_retries: int = 3) -> pd.DataFrame | None:
    """Fetch historical data from yfinance.

    Args:
        symbol: Ticker symbol
        max_retries: Number of retries on failure

    Returns:
        DataFrame with OHLCV data, or None if fetch fails

    """
    import warnings

    # Suppress yfinance FutureWarning about auto_adjust default
    warnings.filterwarnings("ignore", message=".*auto_adjust default to True.*")

    for attempt in range(max_retries):
        try:
            df = yf.download(symbol, progress=False, period="max", auto_adjust=False)
            if df is None or df.empty:
                logger.warning(f"Empty data from yfinance for {symbol}")
                return None
            logger.info(f"Fetched {len(df)} records from yfinance for {symbol}")
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {symbol}, retrying: {e}"
                )
            else:
                logger.error(f"Failed to fetch yfinance data for {symbol}: {e}")
                return None
    return None


def normalize_dataframe(df: pd.DataFrame, source: str) -> list[DataPoint]:
    """Normalize a dataframe to a list of DataPoint objects.

    Args:
        df: DataFrame with OHLCV data
        source: Source name for logging (e.g., "S3", "yfinance")

    Returns:
        List of DataPoint objects

    """
    if df is None or df.empty:
        return []

    points: list[DataPoint] = []

    # Handle yfinance MultiIndex columns (tuples) by flattening to single level
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten MultiIndex: take first level only (the OHLCV names)
        df.columns = df.columns.get_level_values(0)

    # Create lowercase mapping for case-insensitive column lookup
    columns_lower: dict[str, str] = {}
    for col in df.columns:
        # Handle both string and non-string column names
        col_str = str(col)
        columns_lower[col_str.lower()] = col

    # Determine date column/index
    # S3 data uses 'timestamp' column, yfinance uses DatetimeIndex
    has_timestamp_col = "timestamp" in columns_lower
    date_col = columns_lower.get("timestamp") if has_timestamp_col else None

    # Find OHLCV columns
    # Note: Use regular Close (not Adj Close) for comparison since S3 stores unadjusted prices
    open_col = columns_lower.get("open")
    high_col = columns_lower.get("high")
    low_col = columns_lower.get("low")
    close_col = columns_lower.get("close")  # Prefer Close over Adj Close for S3 compatibility
    volume_col = columns_lower.get("volume")

    # Fallback to pattern matching if not found
    if not open_col:
        open_col = next((c for c in df.columns if "open" in str(c).lower()), None)
    if not high_col:
        high_col = next((c for c in df.columns if "high" in str(c).lower()), None)
    if not low_col:
        low_col = next((c for c in df.columns if "low" in str(c).lower()), None)
    if not close_col:
        # Prefer regular Close over Adj Close for S3 compatibility
        close_col = next(
            (c for c in df.columns if str(c).lower() == "close"),
            next((c for c in df.columns if "close" in str(c).lower()), None),
        )
    if not volume_col:
        volume_col = next((c for c in df.columns if "volume" in str(c).lower()), None)

    for idx, row in df.iterrows():
        try:
            # Parse date - S3 has 'timestamp' column, yfinance uses index
            if has_timestamp_col and date_col:
                date_val = row[date_col]
            else:
                date_val = idx

            # Convert to YYYY-MM-DD string
            if isinstance(date_val, str):
                date_str = date_val[:10]  # Take first 10 chars
            else:
                date_str = pd.to_datetime(date_val).strftime("%Y-%m-%d")

            point = DataPoint(
                date=date_str,
                open_price=float(row.get(open_col, 0)) if open_col else 0.0,
                high_price=float(row.get(high_col, 0)) if high_col else 0.0,
                low_price=float(row.get(low_col, 0)) if low_col else 0.0,
                close_price=float(row.get(close_col, 0)) if close_col else 0.0,
                volume=int(row.get(volume_col, 0)) if volume_col else 0,
            )
            points.append(point)
        except Exception as e:
            logger.warning(f"Failed to parse row for {idx}: {e}")
            continue

    logger.debug(f"Normalized {len(points)} points from {source}")
    return points


def validate_symbol(
    symbol: str,
    s3_client: "boto3.client",
    bucket: str,
) -> SymbolValidationResult:
    """Validate a single symbol's data against yfinance.

    Args:
        symbol: Ticker symbol
        s3_client: Initialized S3 client
        bucket: S3 bucket name

    Returns:
        SymbolValidationResult with discrepancies

    """
    result = SymbolValidationResult(symbol=symbol, s3_record_count=0, yfinance_record_count=0)

    # Fetch S3 data
    s3_df = read_s3_data(s3_client, bucket, symbol)
    if s3_df is None:
        result.errors.append(f"No S3 data found for {symbol}")
        return result

    result.s3_record_count = len(s3_df)

    # Fetch yfinance data
    yf_df = fetch_yfinance_data(symbol)
    if yf_df is None:
        result.errors.append(f"Failed to fetch yfinance data for {symbol}")
        return result

    result.yfinance_record_count = len(yf_df)

    # Normalize to DataPoint lists
    s3_points = normalize_dataframe(s3_df, "S3")
    yf_points = normalize_dataframe(yf_df, "yfinance")

    # Capture S3 date range for distinguishing historical vs unexpected gaps
    if s3_points:
        sorted_dates = sorted(p.date for p in s3_points)
        result.s3_start_date = sorted_dates[0]
        result.s3_end_date = sorted_dates[-1]

    # Convert to sets for comparison (by date)
    s3_by_date = {p.date: p for p in s3_points}
    yf_by_date = {p.date: p for p in yf_points}

    # Find missing dates
    s3_dates = set(s3_by_date.keys())
    yf_dates = set(yf_by_date.keys())

    for date in yf_dates - s3_dates:
        result.missing_in_s3.append(yf_by_date[date])

    for date in s3_dates - yf_dates:
        result.missing_in_yfinance.append(s3_by_date[date])

    # Check for mismatches in overlapping dates
    for date in s3_dates & yf_dates:
        s3_point = s3_by_date[date]
        yf_point = yf_by_date[date]
        if s3_point != yf_point:
            result.mismatched_records.append((s3_point, yf_point))

    logger.info(
        f"Validation complete for {symbol}: "
        f"S3={result.s3_record_count} ({result.s3_start_date} to {result.s3_end_date}), "
        f"yfinance={result.yfinance_record_count}, "
        f"gaps={result.historical_gap_count} historical + {len(result.missing_in_s3_recent)} unexpected, "
        f"mismatches={len(result.mismatched_records)}"
    )

    return result


def list_s3_symbols(s3_client: "boto3.client", bucket: str) -> list[str]:
    """List all symbols available in S3.

    Args:
        s3_client: Initialized S3 client
        bucket: S3 bucket name

    Returns:
        List of symbol names

    """
    symbols: set[str] = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Delimiter="/")

    for page in pages:
        if "CommonPrefixes" in page:
            for prefix in page["CommonPrefixes"]:
                symbol = prefix["Prefix"].rstrip("/")
                if symbol:
                    symbols.add(symbol)

    return sorted(symbols)


def write_csv_report(results: list[SymbolValidationResult], output_file: str) -> None:
    """Write validation results to CSV report.

    Args:
        results: List of SymbolValidationResult objects
        output_file: Path to output CSV file

    """
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write summary header
        writer.writerow(["VALIDATION REPORT", datetime.now(UTC).isoformat()])
        writer.writerow([])

        # Summary stats
        total_symbols = len(results)
        valid_symbols = sum(1 for r in results if r.is_valid)
        writer.writerow(["Total Symbols", total_symbols])
        writer.writerow(["Valid Symbols", valid_symbols])
        writer.writerow(["Invalid Symbols", total_symbols - valid_symbols])
        writer.writerow([])

        # Symbol details header
        writer.writerow([
            "Symbol",
            "S3 Records",
            "S3 Date Range",
            "yfinance Records",
            "Historical Gaps",
            "Unexpected Gaps",
            "Missing in yfinance",
            "Mismatched",
            "Errors",
            "Status",
        ])

        for result in results:
            date_range = f"{result.s3_start_date} to {result.s3_end_date}" if result.s3_start_date else "N/A"
            writer.writerow([
                result.symbol,
                result.s3_record_count,
                date_range,
                result.yfinance_record_count,
                result.historical_gap_count,
                len(result.missing_in_s3_recent),
                len(result.missing_in_yfinance),
                len(result.mismatched_records),
                "; ".join(result.errors) if result.errors else "",
                "VALID" if result.is_valid else "INVALID",
            ])

    logger.info(f"Report written to {output_file}")


def write_detailed_report(results: list[SymbolValidationResult], output_file: str) -> None:
    """Write detailed discrepancies to JSON file.

    Args:
        results: List of SymbolValidationResult objects
        output_file: Path to output JSON file

    """
    report: dict[str, dict] = {}

    for result in results:
        if not result.is_valid or result.historical_gap_count > 0:
            symbol_report: dict = {
                "s3_record_count": result.s3_record_count,
                "yfinance_record_count": result.yfinance_record_count,
                "s3_date_range": f"{result.s3_start_date} to {result.s3_end_date}" if result.s3_start_date else "N/A",
                "historical_gaps": result.historical_gap_count,
                "unexpected_gaps": len(result.missing_in_s3_recent),
                "is_valid": result.is_valid,
                "errors": result.errors,
            }

            # Only include unexpected gaps in detail (not historical)
            if result.missing_in_s3_recent:
                symbol_report["unexpected_gaps_detail"] = [
                    {
                        "date": p.date,
                        "close": p.close_price,
                        "volume": p.volume,
                    }
                    for p in result.missing_in_s3_recent[:20]  # Limit to 20
                ]

            if result.missing_in_yfinance:
                symbol_report["missing_in_yfinance"] = [
                    {
                        "date": p.date,
                        "close": p.close_price,
                        "volume": p.volume,
                    }
                    for p in result.missing_in_yfinance
                ]

            if result.mismatched_records:
                symbol_report["mismatched"] = [
                    {
                        "date": s3_point.date,
                        "s3_close": s3_point.close_price,
                        "yf_close": yf_point.close_price,
                        "s3_volume": s3_point.volume,
                        "yf_volume": yf_point.volume,
                    }
                    for s3_point, yf_point in result.mismatched_records[:10]  # Limit to 10
                ]

            report[result.symbol] = symbol_report

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Detailed report written to {output_file}")


def discover_bucket_from_cloudformation(region: str) -> str | None:
    """Attempt to discover bucket from CloudFormation stack outputs.

    Looks for stack outputs named MarketDataBucketName in stacks matching:
    - alchemiser-dev (dev stage)
    - alchemiser-staging (staging stage)
    - alchemiser-prod (prod stage)

    Args:
        region: AWS region

    Returns:
        Bucket name if found, None otherwise

    """
    try:
        cf_client = boto3.client("cloudformation", region_name=region)

        # Try common stack names in order of likelihood
        stack_names = [
            "alchemiser-dev",
            "alchemiser-staging",
            "alchemiser-prod",
        ]

        for stack_name in stack_names:
            try:
                response = cf_client.describe_stacks(StackName=stack_name)
                if response["Stacks"]:
                    stack = response["Stacks"][0]
                    if "Outputs" in stack:
                        for output in stack["Outputs"]:
                            if output.get("OutputKey") == "MarketDataBucketName":
                                bucket = output.get("OutputValue")
                                logger.info(
                                    f"Auto-discovered bucket from CloudFormation stack {stack_name}: {bucket}"
                                )
                                return bucket
            except cf_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] != "ValidationError":
                    raise
                # Stack doesn't exist, try next one
                continue

    except Exception as e:
        logger.warning(f"Failed to auto-discover bucket from CloudFormation: {e}")

    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate S3 market data against yfinance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all symbols (auto-discovers bucket from CloudFormation)
  python scripts/validate_s3_against_yfinance.py

  # Validate specific symbols
  python scripts/validate_s3_against_yfinance.py --symbols AAPL,MSFT,GOOGL

  # Limit to first 10 symbols
  python scripts/validate_s3_against_yfinance.py --limit 10

  # Custom output file
  python scripts/validate_s3_against_yfinance.py --output validation_report.csv

  # Explicit bucket (overrides auto-discovery)
  python scripts/validate_s3_against_yfinance.py --bucket my-bucket
        """,
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated list of symbols to validate (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of symbols to validate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="s3_validation_report.csv",
        help="Output CSV report file (default: s3_validation_report.csv)",
    )
    parser.add_argument(
        "--detailed",
        type=str,
        help="Output detailed JSON report of discrepancies",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="S3 bucket name (default: auto-discover from CloudFormation, MARKET_DATA_BUCKET env var, or specify explicitly)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    args = parser.parse_args()

    # Resolve bucket: explicit arg > env var > CloudFormation auto-discovery
    bucket = args.bucket or os.environ.get("MARKET_DATA_BUCKET")

    if not bucket:
        logger.info("Attempting to auto-discover bucket from CloudFormation...")
        bucket = discover_bucket_from_cloudformation(args.region)

    if not bucket:
        logger.error(
            "Bucket not found. Provide via:\n"
            "  1. --bucket argument\n"
            "  2. MARKET_DATA_BUCKET env var\n"
            "  3. CloudFormation stack output (auto-discovered from alchemiser-dev/staging/prod stacks)"
        )
        sys.exit(1)

    logger.info(f"Using bucket: {bucket}")

    # Initialize S3 client
    s3_client = boto3.client("s3", region_name=args.region)

    # Determine symbols to validate
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        logger.info("Listing symbols from S3...")
        symbols = list_s3_symbols(s3_client, bucket)
        logger.info(f"Found {len(symbols)} symbols in S3")

    if args.limit:
        symbols = symbols[: args.limit]
        logger.info(f"Limiting to first {args.limit} symbols")

    # Validate each symbol
    results: list[SymbolValidationResult] = []
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] Validating {symbol}...")
        try:
            result = validate_symbol(symbol, s3_client, bucket)
            results.append(result)
        except Exception as e:
            logger.error(f"Unexpected error validating {symbol}: {e}")
            result = SymbolValidationResult(
                symbol=symbol,
                s3_record_count=0,
                yfinance_record_count=0,
                errors=[str(e)],
            )
            results.append(result)

    # Write reports
    write_csv_report(results, args.output)

    if args.detailed:
        write_detailed_report(results, args.detailed)

    # Print summary
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    total_discrepancies = sum(r.discrepancy_count for r in results)
    total_historical_gaps = sum(r.historical_gap_count for r in results)

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Symbols Validated: {len(results)}")
    print(f"Valid Symbols: {valid_count}")
    print(f"Invalid Symbols: {invalid_count}")
    print(f"Total Actionable Discrepancies: {total_discrepancies}")
    print(f"Total Historical Gaps (expected): {total_historical_gaps}")
    print(f"Report: {args.output}")
    if args.detailed:
        print(f"Detailed Report: {args.detailed}")
    print("=" * 80)

    if invalid_count > 0:
        print("\nInvalid Symbols:")
        for result in results:
            if not result.is_valid:
                print(
                    f"  - {result.symbol} ({result.s3_start_date} to {result.s3_end_date}): "
                    f"{len(result.missing_in_s3_recent)} unexpected gaps, "
                    f"{len(result.missing_in_yfinance)} extra in S3, "
                    f"{len(result.mismatched_records)} mismatched"
                )

    # Show symbols with only historical gaps (valid but worth noting)
    symbols_with_historical_gaps = [r for r in results if r.is_valid and r.historical_gap_count > 0]
    if symbols_with_historical_gaps and len(symbols_with_historical_gaps) <= 10:
        print("\nSymbols with Historical Gaps (valid - data before S3 seeding):")
        for result in symbols_with_historical_gaps:
            print(
                f"  - {result.symbol}: S3 has {result.s3_record_count} records "
                f"({result.s3_start_date} to {result.s3_end_date}), "
                f"{result.historical_gap_count} historical records not seeded"
            )
    elif symbols_with_historical_gaps:
        print(f"\n{len(symbols_with_historical_gaps)} symbols have historical gaps (data before S3 seeding - this is expected)")


if __name__ == "__main__":
    main()
