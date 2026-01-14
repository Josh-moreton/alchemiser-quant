"""Business Unit: data | Status: current.

Validate S3 market data against yfinance adjusted prices.

Simple validation: does S3 close price match yfinance Adj Close within 2% tolerance?
If not, it's a mismatch. Report it.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import pandas as pd
import yfinance as yf
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

TOLERANCE_PCT = 0.02  # 2% tolerance


@dataclass
class ValidationResult:
    """Result of validating a symbol."""

    symbol: str
    s3_records: int = 0
    yf_records: int = 0
    mismatches: int = 0
    gaps: int = 0  # dates in yfinance but not S3
    errors: list[str] = field(default_factory=list)
    sample_mismatches: list[dict] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.mismatches == 0 and self.gaps == 0 and not self.errors


def read_s3_data(s3_client, bucket: str, symbol: str) -> pd.DataFrame | None:
    """Read parquet data from S3."""
    try:
        key = f"{symbol}/daily.parquet"
        response = s3_client.get_object(Bucket=bucket, Key=key)
        with Path("/tmp/temp.parquet").open("wb") as f:
            f.write(response["Body"].read())
        df = pd.read_parquet("/tmp/temp.parquet")
        Path("/tmp/temp.parquet").unlink()
        return df
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


def fetch_yfinance_data(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """Fetch yfinance data with Adj Close."""
    import warnings
    warnings.filterwarnings("ignore")
    
    try:
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
        df = yf.download(symbol, start=start, end=end_dt.strftime("%Y-%m-%d"), 
                         auto_adjust=False, progress=False)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None


def validate_symbol(symbol: str, s3_client, bucket: str) -> ValidationResult:
    """Validate a single symbol. Simple: does price match within tolerance?"""
    result = ValidationResult(symbol=symbol)
    
    # Get S3 data
    s3_df = read_s3_data(s3_client, bucket, symbol)
    if s3_df is None:
        result.errors.append("No S3 data")
        return result
    
    result.s3_records = len(s3_df)
    
    # Normalize S3 timestamps
    s3_df["date"] = pd.to_datetime(s3_df["timestamp"]).dt.strftime("%Y-%m-%d")
    s3_by_date = s3_df.set_index("date")["close"].to_dict()
    
    start_date = min(s3_by_date.keys())
    end_date = max(s3_by_date.keys())
    
    # Get yfinance data
    yf_df = fetch_yfinance_data(symbol, start_date, end_date)
    if yf_df is None:
        result.errors.append("Failed to fetch yfinance")
        return result
    
    # Flatten multi-index if needed
    if isinstance(yf_df.columns, pd.MultiIndex):
        yf_df.columns = yf_df.columns.get_level_values(0)
    
    result.yf_records = len(yf_df)
    
    # Get Adj Close column
    adj_close_col = "Adj Close" if "Adj Close" in yf_df.columns else "Close"
    yf_df["date"] = yf_df.index.strftime("%Y-%m-%d")
    yf_by_date = yf_df.set_index("date")[adj_close_col].to_dict()
    
    # Compare
    for date, yf_price in yf_by_date.items():
        if date not in s3_by_date:
            result.gaps += 1
            continue
        
        s3_price = s3_by_date[date]
        if max(abs(s3_price), abs(yf_price)) == 0:
            continue
        
        pct_diff = abs(s3_price - yf_price) / max(abs(s3_price), abs(yf_price))
        if pct_diff > TOLERANCE_PCT:
            result.mismatches += 1
            if len(result.sample_mismatches) < 3:
                result.sample_mismatches.append({
                    "date": date,
                    "s3": round(s3_price, 2),
                    "yf": round(yf_price, 2),
                    "diff_pct": round(pct_diff * 100, 2),
                })
    
    return result


def list_s3_symbols(s3_client, bucket: str) -> list[str]:
    """List all symbols in S3."""
    symbols = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for prefix in page.get("CommonPrefixes", []):
            symbol = prefix["Prefix"].rstrip("/")
            if symbol:
                symbols.add(symbol)
    return sorted(symbols)


def write_bad_data_markers(results: list[ValidationResult], region: str) -> int:
    """Write markers for symbols with mismatches."""
    table_name = "alchemiser-bad-data-markers"
    
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from the_alchemiser.data_v2.bad_data_marker_service import BadDataMarkerService
    
    marker_service = BadDataMarkerService(table_name=table_name)
    count = 0
    
    for r in results:
        if r.mismatches == 0:
            continue
        if marker_service.mark_symbol_for_refetch(
            symbol=r.symbol,
            reason="price_mismatch",
            start_date="",
            end_date="",
            detected_ratio=None,
            source="validation_script",
        ):
            count += 1
            logger.info(f"Marked {r.symbol} ({r.mismatches} mismatches)")
    
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate S3 data against yfinance")
    parser.add_argument("--symbols", type=str, help="Comma-separated symbols")
    parser.add_argument("--limit", type=int, help="Max symbols to validate")
    parser.add_argument("--output", type=str, default="s3_validation_report.csv")
    parser.add_argument("--bucket", type=str, default="alchemiser-shared-market-data")
    parser.add_argument("--region", type=str, default="us-east-1")
    parser.add_argument("--mark-bad", action="store_true", help="Write DynamoDB markers")
    parser.add_argument("--debug", action="store_true", help="Show sample mismatches")
    args = parser.parse_args()
    
    s3_client = boto3.client("s3", region_name=args.region)
    
    # Get symbols
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        symbols = list_s3_symbols(s3_client, args.bucket)
    
    if args.limit:
        symbols = symbols[:args.limit]
    
    logger.info(f"Validating {len(symbols)} symbols...")
    
    # Validate
    results = []
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] {symbol}")
        result = validate_symbol(symbol, s3_client, args.bucket)
        results.append(result)
        
        if args.debug and result.sample_mismatches:
            for m in result.sample_mismatches:
                print(f"  {m['date']}: S3={m['s3']}, YF={m['yf']}, diff={m['diff_pct']}%")
    
    # Write CSV
    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Symbol", "S3 Records", "YF Records", "Mismatches", "Gaps", "Status"])
        for r in results:
            status = "VALID" if r.is_valid else "INVALID"
            writer.writerow([r.symbol, r.s3_records, r.yf_records, r.mismatches, r.gaps, status])
    
    # Mark bad if requested
    markers = 0
    if args.mark_bad:
        with_mismatches = [r for r in results if r.mismatches > 0]
        if with_mismatches:
            markers = write_bad_data_markers(results, args.region)
    
    # Summary
    valid = sum(1 for r in results if r.is_valid)
    invalid = len(results) - valid
    total_mismatches = sum(r.mismatches for r in results)
    
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total: {len(results)} | Valid: {valid} | Invalid: {invalid}")
    print(f"Total mismatches: {total_mismatches}")
    if markers:
        print(f"Markers written: {markers}")
    print(f"Report: {args.output}")
    
    if invalid > 0:
        print(f"\nInvalid symbols:")
        for r in results:
            if not r.is_valid:
                print(f"  {r.symbol}: {r.mismatches} mismatches, {r.gaps} gaps")


if __name__ == "__main__":
    main()
