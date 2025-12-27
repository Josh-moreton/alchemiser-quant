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
        """Check equality allowing for minor float precision differences."""
        if not isinstance(other, DataPoint):
            return NotImplemented
        return (
            self.date == other.date
            and abs(self.open_price - other.open_price) < 0.01
            and abs(self.high_price - other.high_price) < 0.01
            and abs(self.low_price - other.low_price) < 0.01
            and abs(self.close_price - other.close_price) < 0.01
            and self.volume == other.volume
        )


@dataclass
class SymbolValidationResult:
    """Result of validating a symbol against yfinance."""

    symbol: str
    s3_record_count: int
    yfinance_record_count: int
    missing_in_s3: list[DataPoint] = field(default_factory=list)
    missing_in_yfinance: list[DataPoint] = field(default_factory=list)
    mismatched_records: list[tuple[DataPoint, DataPoint]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if symbol passed all validations."""
        return (
            not self.missing_in_s3
            and not self.missing_in_yfinance
            and not self.mismatched_records
            and not self.errors
        )

    @property
    def discrepancy_count(self) -> int:
        """Total number of discrepancies."""
        return (
            len(self.missing_in_s3)
            + len(self.missing_in_yfinance)
            + len(self.mismatched_records)
        )


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
    for attempt in range(max_retries):
        try:
            df = yf.download(symbol, progress=False, period="max")
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

    # Handle different column name conventions
    columns_lower = {col.lower(): col for col in df.columns}

    for date_idx, row in df.iterrows():
        try:
            # Parse date
            if isinstance(date_idx, str):
                date_str = date_idx
            else:
                date_str = pd.to_datetime(date_idx).strftime("%Y-%m-%d")

            # Extract price/volume columns (yfinance uses Adj Close, S3 might use Close)
            open_col = columns_lower.get("open") or "Open"
            high_col = columns_lower.get("high") or "High"
            low_col = columns_lower.get("low") or "Low"
            close_col = columns_lower.get("adj close") or columns_lower.get("close") or "Close"
            volume_col = columns_lower.get("volume") or "Volume"

            point = DataPoint(
                date=date_str,
                open_price=float(row.get(open_col, 0)) or 0.0,
                high_price=float(row.get(high_col, 0)) or 0.0,
                low_price=float(row.get(low_col, 0)) or 0.0,
                close_price=float(row.get(close_col, 0)) or 0.0,
                volume=int(row.get(volume_col, 0)) or 0,
            )
            points.append(point)
        except Exception as e:
            logger.warning(f"Failed to parse row for {date_idx}: {e}")
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
        f"S3={result.s3_record_count}, yfinance={result.yfinance_record_count}, "
        f"discrepancies={result.discrepancy_count}"
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
            "yfinance Records",
            "Missing in S3",
            "Missing in yfinance",
            "Mismatched",
            "Errors",
            "Status",
        ])

        for result in results:
            writer.writerow([
                result.symbol,
                result.s3_record_count,
                result.yfinance_record_count,
                len(result.missing_in_s3),
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
        if not result.is_valid:
            symbol_report: dict = {
                "s3_record_count": result.s3_record_count,
                "yfinance_record_count": result.yfinance_record_count,
                "errors": result.errors,
            }

            if result.missing_in_s3:
                symbol_report["missing_in_s3"] = [
                    {
                        "date": p.date,
                        "close": p.close_price,
                        "volume": p.volume,
                    }
                    for p in result.missing_in_s3
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


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate S3 market data against yfinance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all symbols
  python scripts/validate_s3_against_yfinance.py

  # Validate specific symbols
  python scripts/validate_s3_against_yfinance.py --symbols AAPL,MSFT,GOOGL

  # Limit to first 10 symbols
  python scripts/validate_s3_against_yfinance.py --limit 10

  # Custom output file
  python scripts/validate_s3_against_yfinance.py --output validation_report.csv
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
        help="S3 bucket name (default: MARKET_DATA_BUCKET env var)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    args = parser.parse_args()

    # Resolve bucket
    bucket = args.bucket or os.environ.get("MARKET_DATA_BUCKET")
    if not bucket:
        logger.error("Bucket not specified. Set --bucket or MARKET_DATA_BUCKET env var")
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

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Symbols Validated: {len(results)}")
    print(f"Valid Symbols: {valid_count}")
    print(f"Invalid Symbols: {invalid_count}")
    print(f"Total Discrepancies: {total_discrepancies}")
    print(f"Report: {args.output}")
    if args.detailed:
        print(f"Detailed Report: {args.detailed}")
    print("=" * 80)

    if invalid_count > 0:
        print("\nInvalid Symbols:")
        for result in results:
            if not result.is_valid:
                print(
                    f"  - {result.symbol}: "
                    f"{len(result.missing_in_s3)} missing in S3, "
                    f"{len(result.missing_in_yfinance)} missing in yfinance, "
                    f"{len(result.mismatched_records)} mismatched"
                )


if __name__ == "__main__":
    main()
