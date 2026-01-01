#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

QuantStats Report Generator - GitHub Actions Entry Point.

Generates tearsheet reports for all strategies and the combined portfolio,
uploads to S3, and outputs a manifest with presigned URLs.

Environment Variables:
    TRADE_LEDGER_TABLE: DynamoDB table name for trade ledger
    REPORTS_BUCKET: S3 bucket name for report uploads
    ALPACA_KEY: Alpaca API key for benchmark data
    ALPACA_SECRET: Alpaca API secret
    DAYS_LOOKBACK: Days of history to include (default: 90)

Usage:
    python scripts/generate_quantstats_reports.py

    # Or with custom lookback:
    DAYS_LOOKBACK=180 python scripts/generate_quantstats_reports.py
"""

from __future__ import annotations

# Configure matplotlib BEFORE any imports that use it (quantstats, etc.)
# This prevents "Font family 'Arial' not found" warnings on Linux/CI systems
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"
# Suppress font manager warnings
import logging as _logging

_logging.getLogger("matplotlib.font_manager").setLevel(_logging.ERROR)

import logging
import os
import sys
from datetime import UTC, datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for report generation.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    logger.info("=" * 60)
    logger.info("QuantStats Report Generator")
    logger.info("=" * 60)

    # Load configuration from environment
    table_name = os.environ.get("TRADE_LEDGER_TABLE")
    bucket_name = os.environ.get("REPORTS_BUCKET")
    alpaca_key = os.environ.get("ALPACA_KEY")
    alpaca_secret = os.environ.get("ALPACA_SECRET")
    days_lookback = int(os.environ.get("DAYS_LOOKBACK", "90"))

    # Validate required configuration
    missing = []
    if not table_name:
        missing.append("TRADE_LEDGER_TABLE")
    if not bucket_name:
        missing.append("REPORTS_BUCKET")
    if not alpaca_key:
        missing.append("ALPACA_KEY")
    if not alpaca_secret:
        missing.append("ALPACA_SECRET")

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return 1

    logger.info(f"Configuration:")
    logger.info(f"  Table: {table_name}")
    logger.info(f"  Bucket: {bucket_name}")
    logger.info(f"  Days lookback: {days_lookback}")

    # Import modules after validation (faster failure on missing config)
    from quantstats_reports.benchmark_service import BenchmarkService
    from quantstats_reports.report_generator import ReportGenerator
    from quantstats_reports.returns_builder import ReturnsBuilder
    from quantstats_reports.s3_uploader import (
        ManifestEntry,
        ReportsManifest,
        S3Uploader,
    )

    # Initialize services
    returns_builder = ReturnsBuilder(table_name)
    benchmark_service = BenchmarkService(alpaca_key, alpaca_secret)
    report_generator = ReportGenerator()
    s3_uploader = S3Uploader(bucket_name)

    # Initialize manifest
    manifest = ReportsManifest(
        generated_at=datetime.now(UTC).isoformat(),
        period_start=None,
        period_end=None,
        benchmark="SPY",
    )

    # Discover strategies
    logger.info("Discovering strategies with closed lots...")
    strategies = returns_builder.discover_strategies()

    if not strategies:
        logger.warning("No strategies found with closed lots. Exiting.")
        manifest.errors.append("No strategies found with closed lots")
        _upload_manifest(s3_uploader, manifest)
        return 0

    logger.info(f"Found {len(strategies)} strategies: {strategies}")

    # Track period bounds for manifest
    all_period_starts = []
    all_period_ends = []

    # Generate strategy-level reports
    logger.info("=" * 40)
    logger.info("Generating strategy reports...")
    logger.info("=" * 40)

    for strategy_name in strategies:
        logger.info(f"Processing strategy: {strategy_name}")

        try:
            # Build returns for this strategy
            returns = returns_builder.build_returns_series(strategy_name, days_lookback)

            if returns.empty:
                logger.warning(f"No returns data for {strategy_name}, skipping")
                manifest.errors.append(f"No returns data for {strategy_name}")
                continue

            # Track period bounds
            all_period_starts.append(returns.index.min())
            all_period_ends.append(returns.index.max())

            # Get aligned benchmark returns
            benchmark_returns = benchmark_service.align_benchmark_to_strategy(returns, "SPY")

            # Generate tearsheet
            result = report_generator.generate_strategy_report(
                returns=returns,
                strategy_name=strategy_name,
                benchmark_returns=benchmark_returns,
            )

            if not result.success:
                logger.error(f"Failed to generate report for {strategy_name}: {result.error_message}")
                manifest.errors.append(f"Report generation failed for {strategy_name}: {result.error_message}")
                continue

            # Upload to S3
            upload_result = s3_uploader.upload_strategy_report(
                html_content=result.html_content,
                strategy_name=strategy_name,
            )

            if not upload_result.success:
                logger.error(f"Failed to upload {strategy_name} report: {upload_result.error_message}")
                manifest.errors.append(f"Upload failed for {strategy_name}: {upload_result.error_message}")
                continue

            # Add to manifest
            manifest.strategies[strategy_name] = ManifestEntry(
                s3_key=upload_result.s3_key,
                presigned_url=upload_result.presigned_url,
            )
            logger.info(f"Successfully generated and uploaded {strategy_name} report")

        except Exception as e:
            logger.exception(f"Error processing strategy {strategy_name}: {e}")
            manifest.errors.append(f"Exception for {strategy_name}: {str(e)}")

    # Generate portfolio report
    logger.info("=" * 40)
    logger.info("Generating portfolio report...")
    logger.info("=" * 40)

    try:
        portfolio_returns = returns_builder.build_portfolio_returns(
            days_lookback=days_lookback,
            strategies=strategies,
        )

        if portfolio_returns.empty:
            logger.warning("No portfolio returns data, skipping portfolio report")
            manifest.errors.append("No portfolio returns data")
        else:
            # Track period bounds
            all_period_starts.append(portfolio_returns.index.min())
            all_period_ends.append(portfolio_returns.index.max())

            # Get aligned benchmark returns
            benchmark_returns = benchmark_service.align_benchmark_to_strategy(
                portfolio_returns, "SPY"
            )

            # Generate tearsheet
            result = report_generator.generate_portfolio_report(
                returns=portfolio_returns,
                benchmark_returns=benchmark_returns,
            )

            if not result.success:
                logger.error(f"Failed to generate portfolio report: {result.error_message}")
                manifest.errors.append(f"Portfolio report failed: {result.error_message}")
            else:
                # Upload to S3
                upload_result = s3_uploader.upload_portfolio_report(
                    html_content=result.html_content,
                )

                if not upload_result.success:
                    logger.error(f"Failed to upload portfolio report: {upload_result.error_message}")
                    manifest.errors.append(f"Portfolio upload failed: {upload_result.error_message}")
                else:
                    manifest.portfolio = ManifestEntry(
                        s3_key=upload_result.s3_key,
                        presigned_url=upload_result.presigned_url,
                    )
                    logger.info("Successfully generated and uploaded portfolio report")

    except Exception as e:
        logger.exception(f"Error generating portfolio report: {e}")
        manifest.errors.append(f"Portfolio exception: {str(e)}")

    # Update manifest period bounds
    if all_period_starts:
        manifest.period_start = min(all_period_starts).strftime("%Y-%m-%d")
    if all_period_ends:
        manifest.period_end = max(all_period_ends).strftime("%Y-%m-%d")

    # Upload manifest
    _upload_manifest(s3_uploader, manifest)

    # Summary
    logger.info("=" * 60)
    logger.info("Report Generation Complete")
    logger.info("=" * 60)
    logger.info(f"Strategies processed: {len(manifest.strategies)}")
    logger.info(f"Portfolio report: {'Yes' if manifest.portfolio else 'No'}")
    logger.info(f"Errors: {len(manifest.errors)}")

    if manifest.errors:
        logger.warning("Errors encountered:")
        for error in manifest.errors:
            logger.warning(f"  - {error}")

    # Print manifest URLs for GitHub Actions output
    logger.info("")
    logger.info("Report URLs:")
    if manifest.portfolio:
        logger.info(f"  Portfolio: {manifest.portfolio.presigned_url}")
    for name, entry in manifest.strategies.items():
        logger.info(f"  {name}: {entry.presigned_url}")

    # Return success if at least one report was generated
    if manifest.portfolio or manifest.strategies:
        return 0
    return 1


def _upload_manifest(s3_uploader, manifest: ReportsManifest) -> None:
    """Upload manifest to S3.

    Args:
        s3_uploader: S3Uploader instance
        manifest: ReportsManifest to upload

    """
    logger.info("Uploading manifest...")
    manifest_result = s3_uploader.upload_manifest(manifest)
    if manifest_result.success:
        logger.info(f"Manifest uploaded: {manifest_result.presigned_url}")
    else:
        logger.error(f"Failed to upload manifest: {manifest_result.error_message}")


if __name__ == "__main__":
    sys.exit(main())
