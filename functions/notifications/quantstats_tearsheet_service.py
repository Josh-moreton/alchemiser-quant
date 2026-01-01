"""Business Unit: notifications | Status: current.

QuantStats tearsheet generation service for performance reporting.

This service generates QuantStats HTML tearsheets from trade history data stored in DynamoDB,
uploads them to S3, and provides tearsheet content for email attachments.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.reporting.quantstats_report import generate_tearsheet_from_trades

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

    from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
        DynamoDBTradeLedgerRepository,
    )
    from the_alchemiser.shared.schemas.strategy_lot import StrategyLot

logger = get_logger(__name__)


@dataclass(frozen=True)
class TearsheetGenerationResult:
    """Result of tearsheet generation operation.

    Attributes:
        success: Whether tearsheet generation succeeded
        portfolio_s3_key: S3 object key for portfolio tearsheet (if successful)
        portfolio_html_content: HTML content of portfolio tearsheet for email attachment
        strategy_s3_keys: Mapping of strategy name to S3 object key for per-strategy tearsheets
        error_message: Error message if generation failed

    """

    success: bool
    portfolio_s3_key: str | None = None
    portfolio_html_content: str | None = None
    strategy_s3_keys: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None


class QuantStatsTearsheetService:
    """Service for generating QuantStats performance tearsheets from trade data.

    This service:
    1. Queries closed trade lots from DynamoDB trade ledger
    2. Generates portfolio-level and per-strategy QuantStats HTML tearsheets
    3. Uploads tearsheets to S3 with 30-day lifecycle
    4. Returns tearsheet content for email attachment

    Usage:
        service = QuantStatsTearsheetService(
            repository=trade_ledger_repository,
            bucket_name="alchemiser-prod-reports",
            initial_capital=Decimal("100000"),
        )
        result = service.generate_tearsheets(correlation_id="abc123")
        if result.success:
            # Use result.portfolio_html_content for email attachment
            # Per-strategy tearsheets stored in S3 at result.strategy_s3_keys

    """

    def __init__(
        self,
        repository: DynamoDBTradeLedgerRepository,
        bucket_name: str,
        initial_capital: Decimal = Decimal("100000"),
    ) -> None:
        """Initialize QuantStats tearsheet service.

        Args:
            repository: DynamoDB trade ledger repository for querying closed lots
            bucket_name: S3 bucket name for storing tearsheet HTML files
            initial_capital: Initial capital for equity curve calculation (default: $100,000)

        """
        self.repository = repository
        self.bucket_name = bucket_name
        self.initial_capital = initial_capital
        self._s3_client: S3Client = boto3.client("s3")

    def generate_tearsheets(self, correlation_id: str) -> TearsheetGenerationResult:
        """Generate portfolio and per-strategy QuantStats tearsheets.

        This method:
        1. Queries all closed lots from DynamoDB
        2. Checks minimum data threshold (requires ≥5 closed lots)
        3. Generates portfolio-level tearsheet (all trades combined)
        4. Generates per-strategy tearsheets (for strategies with ≥5 lots)
        5. Uploads all tearsheets to S3
        6. Returns result with S3 keys and portfolio HTML content

        Args:
            correlation_id: Correlation ID for tracing and S3 key generation

        Returns:
            TearsheetGenerationResult with success status, S3 keys, and HTML content

        """
        try:
            # Query all closed lots from DynamoDB
            logger.info(
                "Querying closed lots from DynamoDB for tearsheet generation",
                extra={"correlation_id": correlation_id},
            )

            all_strategies = self.repository.discover_strategies_with_closed_lots()
            all_closed_lots: list[StrategyLot] = []

            for strategy_name in all_strategies:
                lots = self.repository.query_closed_lots_by_strategy(strategy_name)
                all_closed_lots.extend(lots)

            # Check minimum data threshold
            if len(all_closed_lots) < 5:
                logger.info(
                    "Insufficient closed lots for tearsheet generation (< 5 lots)",
                    extra={
                        "correlation_id": correlation_id,
                        "lot_count": len(all_closed_lots),
                    },
                )
                return TearsheetGenerationResult(
                    success=False,
                    error_message=f"Insufficient trade history ({len(all_closed_lots)} closed lots, need ≥5)",
                )

            logger.info(
                f"Generating tearsheets for {len(all_closed_lots)} closed lots across {len(all_strategies)} strategies",
                extra={
                    "correlation_id": correlation_id,
                    "lot_count": len(all_closed_lots),
                    "strategy_count": len(all_strategies),
                },
            )

            # Generate portfolio-level tearsheet
            portfolio_html = self._generate_portfolio_tearsheet(all_closed_lots)
            portfolio_s3_key = self._upload_to_s3(
                html_content=portfolio_html,
                correlation_id=correlation_id,
                report_type="portfolio",
            )

            # Generate per-strategy tearsheets (parallel execution for >3 strategies)
            strategy_s3_keys = self._generate_strategy_tearsheets(
                all_strategies=all_strategies,
                correlation_id=correlation_id,
            )

            logger.info(
                "Tearsheet generation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "portfolio_s3_key": portfolio_s3_key,
                    "strategy_tearsheet_count": len(strategy_s3_keys),
                },
            )

            return TearsheetGenerationResult(
                success=True,
                portfolio_s3_key=portfolio_s3_key,
                portfolio_html_content=portfolio_html,
                strategy_s3_keys=strategy_s3_keys,
            )

        except Exception as e:
            logger.error(
                f"Failed to generate tearsheets: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
            return TearsheetGenerationResult(
                success=False,
                error_message=f"{type(e).__name__}: {e!s}",
            )

    def _generate_portfolio_tearsheet(self, all_closed_lots: list[StrategyLot]) -> str:
        """Generate portfolio-level tearsheet from all closed lots.

        Args:
            all_closed_lots: List of all closed strategy lots

        Returns:
            HTML content of portfolio tearsheet

        Raises:
            ValueError: If QuantStats generation fails

        """
        run_date = datetime.now(UTC).strftime("%Y-%m-%d")
        title = f"Portfolio Performance — {run_date}"

        return generate_tearsheet_from_trades(
            trades=all_closed_lots,
            initial_capital=self.initial_capital,
            output_path=None,  # Return string, don't save to file
            title=title,
            benchmark="SPY",
        )

    def _generate_strategy_tearsheets(
        self,
        all_strategies: list[str],
        correlation_id: str,
    ) -> dict[str, str]:
        """Generate per-strategy tearsheets (parallel execution for >3 strategies).

        Args:
            all_strategies: List of strategy names
            correlation_id: Correlation ID for tracing

        Returns:
            Mapping of strategy name to S3 object key

        """
        strategy_s3_keys: dict[str, str] = {}

        # Use parallel execution for >3 strategies
        if len(all_strategies) > 3:
            return self._generate_strategy_tearsheets_parallel(
                all_strategies=all_strategies,
                correlation_id=correlation_id,
            )

        # Sequential execution for ≤3 strategies
        for strategy_name in all_strategies:
            result = self._generate_single_strategy_tearsheet(
                strategy_name=strategy_name,
                correlation_id=correlation_id,
            )
            if result:
                strategy_s3_keys[strategy_name] = result

        return strategy_s3_keys

    def _generate_strategy_tearsheets_parallel(
        self,
        all_strategies: list[str],
        correlation_id: str,
    ) -> dict[str, str]:
        """Generate per-strategy tearsheets in parallel using ThreadPoolExecutor.

        Args:
            all_strategies: List of strategy names
            correlation_id: Correlation ID for tracing

        Returns:
            Mapping of strategy name to S3 object key

        """
        strategy_s3_keys: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_strategy = {
                executor.submit(
                    self._generate_single_strategy_tearsheet,
                    strategy_name=strategy_name,
                    correlation_id=correlation_id,
                ): strategy_name
                for strategy_name in all_strategies
            }

            for future in as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    s3_key = future.result()
                    if s3_key:
                        strategy_s3_keys[strategy_name] = s3_key
                except Exception as e:
                    logger.error(
                        f"Strategy tearsheet generation failed for {strategy_name}: {e}",
                        extra={
                            "correlation_id": correlation_id,
                            "strategy_name": strategy_name,
                            "error_type": type(e).__name__,
                        },
                    )

        return strategy_s3_keys

    def _generate_single_strategy_tearsheet(
        self,
        strategy_name: str,
        correlation_id: str,
    ) -> str | None:
        """Generate tearsheet for a single strategy.

        Args:
            strategy_name: Name of the strategy
            correlation_id: Correlation ID for tracing

        Returns:
            S3 object key if successful, None if skipped or failed

        """
        try:
            # Query closed lots for this strategy
            strategy_lots = self.repository.query_closed_lots_by_strategy(strategy_name)

            # Skip if insufficient data
            if len(strategy_lots) < 5:
                logger.debug(
                    f"Skipping strategy tearsheet for {strategy_name} (< 5 lots)",
                    extra={
                        "correlation_id": correlation_id,
                        "strategy_name": strategy_name,
                        "lot_count": len(strategy_lots),
                    },
                )
                return None

            # Calculate initial capital for this strategy (from first lot entry value)
            strategy_initial_capital = self._calculate_strategy_capital(strategy_lots)

            # Generate tearsheet
            run_date = datetime.now(UTC).strftime("%Y-%m-%d")
            title = f"{strategy_name} Performance — {run_date}"

            html_content = generate_tearsheet_from_trades(
                trades=strategy_lots,
                initial_capital=strategy_initial_capital,
                output_path=None,
                title=title,
                benchmark="SPY",
            )

            # Upload to S3
            s3_key = self._upload_to_s3(
                html_content=html_content,
                correlation_id=correlation_id,
                report_type=strategy_name,
            )

            logger.debug(
                f"Strategy tearsheet generated for {strategy_name}",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_name": strategy_name,
                    "s3_key": s3_key,
                    "lot_count": len(strategy_lots),
                },
            )

            return s3_key

        except Exception as e:
            logger.warning(
                f"Failed to generate strategy tearsheet for {strategy_name}: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_name": strategy_name,
                    "error_type": type(e).__name__,
                },
            )
            return None

    def _calculate_strategy_capital(self, strategy_lots: list[StrategyLot]) -> Decimal:
        """Calculate initial capital for a strategy based on first lot entry value.

        Args:
            strategy_lots: List of closed lots for the strategy

        Returns:
            Initial capital estimate (defaults to self.initial_capital if calculation fails)

        """
        if not strategy_lots:
            return self.initial_capital

        try:
            # Sort by entry timestamp
            sorted_lots = sorted(strategy_lots, key=lambda lot: lot.entry_timestamp)
            first_lot = sorted_lots[0]

            # Estimate initial capital from first lot's entry value
            # Use entry price * entry_qty as a rough estimate
            if first_lot.entry_price and first_lot.entry_qty:
                estimated_capital: Decimal = first_lot.entry_price * abs(first_lot.entry_qty)
                # Scale up to account for diversification (assume 10% position size)
                return estimated_capital * Decimal("10")

        except (AttributeError, TypeError, ValueError) as e:
            logger.debug(
                f"Could not calculate strategy capital, using default: {e}",
                extra={"error_type": type(e).__name__},
            )

        return self.initial_capital

    def _upload_to_s3(
        self,
        html_content: str,
        correlation_id: str,
        report_type: str,
    ) -> str:
        """Upload tearsheet HTML to S3.

        Args:
            html_content: HTML content to upload
            correlation_id: Correlation ID for S3 key generation
            report_type: Report type ("portfolio" or strategy name)

        Returns:
            S3 object key

        Raises:
            ClientError: If S3 upload fails

        """
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")

        if report_type == "portfolio":
            object_key = f"reports/{timestamp}_{correlation_id[:8]}_portfolio_tearsheet.html"
        else:
            # Strategy tearsheet (report_type is strategy name)
            # Sanitize strategy name for S3 key (replace spaces with underscores)
            safe_strategy_name = report_type.replace(" ", "_").replace("/", "_")
            object_key = f"reports/strategy_tearsheets/{timestamp}_{correlation_id[:8]}_{safe_strategy_name}.html"

        try:
            self._s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=html_content.encode("utf-8"),
                ContentType="text/html",
                ContentDisposition=f'inline; filename="tearsheet_{timestamp}.html"',
            )

            logger.debug(
                f"Tearsheet uploaded to S3: {object_key}",
                extra={
                    "s3_bucket": self.bucket_name,
                    "s3_key": object_key,
                    "report_type": report_type,
                    "content_size_kb": len(html_content) // 1024,
                },
            )

            return object_key

        except (ClientError, BotoCoreError) as e:
            logger.error(
                f"S3 upload failed for {report_type} tearsheet: {e}",
                exc_info=True,
                extra={
                    "s3_bucket": self.bucket_name,
                    "s3_key": object_key,
                    "report_type": report_type,
                    "error_type": type(e).__name__,
                },
            )
            raise
