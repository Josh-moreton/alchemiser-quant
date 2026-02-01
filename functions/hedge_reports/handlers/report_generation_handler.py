"""Business Unit: hedge_reports | Status: current.

Report generation handler for hedge reports Lambda.

Orchestrates daily and weekly report generation, SNS publishing,
and S3 storage for detailed reports.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.hedge_report_generator import HedgeReportGenerator

logger = get_logger(__name__)


class ReportGenerationHandler:
    """Handles hedge report generation and distribution."""

    def __init__(
        self,
        account_id: str,
        correlation_id: str,
    ) -> None:
        """Initialize handler.

        Args:
            account_id: Account ID
            correlation_id: Correlation ID for tracing

        """
        self._account_id = account_id
        self._correlation_id = correlation_id
        self._sns_client = boto3.client("sns")
        self._s3_client = boto3.client("s3")

    def generate_daily_report(
        self,
        current_nav: Decimal | None = None,
        underlying_prices: dict[str, Decimal] | None = None,
    ) -> dict[str, Any]:
        """Generate and distribute daily hedge report.

        Args:
            current_nav: Current portfolio NAV (optional, will fetch if not provided)
            underlying_prices: Current underlying prices (optional)

        Returns:
            Summary of report generation

        """
        logger.info(
            "Generating daily hedge report",
            account_id=self._account_id,
            correlation_id=self._correlation_id,
        )

        # Create report generator from environment
        generator = HedgeReportGenerator.from_environment(self._account_id)

        # Use provided NAV or default for testing
        if current_nav is None:
            current_nav = self._get_current_nav()

        # Default underlying prices if not provided
        if underlying_prices is None:
            underlying_prices = self._get_underlying_prices()

        # Generate report
        report = generator.generate_daily_report(
            current_nav=current_nav,
            underlying_prices=underlying_prices,
        )

        # Format summary for SNS notification
        summary = self._format_daily_summary(report)

        # Publish to SNS
        self._publish_to_sns(
            subject=f"Daily Hedge Report - {report.report_date}",
            message=summary,
        )

        # Store full report to S3 (optional)
        report_key = self._store_report_to_s3(
            report_type="daily",
            report_date=report.report_date.isoformat(),
            report_data=report.model_dump(),
        )

        logger.info(
            "Daily hedge report generated and distributed",
            account_id=self._account_id,
            correlation_id=self._correlation_id,
            report_date=report.report_date.isoformat(),
            active_positions=report.total_active_hedges,
            alerts_count=len(report.alerts),
        )

        return {
            "report_type": "daily",
            "report_date": report.report_date.isoformat(),
            "active_positions_count": report.total_active_hedges,
            "hedges_placed_today": report.hedges_placed_today,
            "hedges_rolled_today": report.hedges_rolled_today,
            "premium_spent_ytd": str(report.premium_spend.spend_ytd),
            "premium_ytd_pct_of_cap": str(report.premium_spend.spend_ytd_pct_of_cap),
            "alerts": report.alerts,
            "s3_report_key": report_key,
        }

    def generate_weekly_report(
        self,
        current_nav: Decimal | None = None,
        underlying_prices: dict[str, Decimal] | None = None,
    ) -> dict[str, Any]:
        """Generate and distribute weekly hedge report.

        Args:
            current_nav: Current portfolio NAV (optional)
            underlying_prices: Current underlying prices (optional)

        Returns:
            Summary of report generation

        """
        logger.info(
            "Generating weekly hedge report",
            account_id=self._account_id,
            correlation_id=self._correlation_id,
        )

        # Create report generator from environment
        generator = HedgeReportGenerator.from_environment(self._account_id)

        # Use provided NAV or default
        if current_nav is None:
            current_nav = self._get_current_nav()

        # Default underlying prices if not provided
        if underlying_prices is None:
            underlying_prices = self._get_underlying_prices()

        # Generate report
        report = generator.generate_weekly_report(
            current_nav=current_nav,
            underlying_prices=underlying_prices,
        )

        # Format summary for SNS notification
        summary = self._format_weekly_summary(report)

        # Publish to SNS
        self._publish_to_sns(
            subject=f"Weekly Hedge Report - Week of {report.report_week_start}",
            message=summary,
        )

        # Store full report to S3
        report_key = self._store_report_to_s3(
            report_type="weekly",
            report_date=report.report_week_end.isoformat(),
            report_data=report.model_dump(),
        )

        logger.info(
            "Weekly hedge report generated and distributed",
            account_id=self._account_id,
            correlation_id=self._correlation_id,
            week_start=report.report_week_start.isoformat(),
            week_end=report.report_week_end.isoformat(),
            active_positions=report.active_positions_count,
        )

        return {
            "report_type": "weekly",
            "week_start": report.report_week_start.isoformat(),
            "week_end": report.report_week_end.isoformat(),
            "active_positions_count": report.active_positions_count,
            "total_hedges_placed": report.total_hedges_placed,
            "total_hedges_rolled": report.total_hedges_rolled,
            "premium_spent_this_week": str(report.premium_spent_this_week),
            "premium_spent_ytd": str(report.premium_spent_ytd),
            "s3_report_key": report_key,
        }

    def generate_inventory_report(
        self,
        current_nav: Decimal | None = None,
    ) -> dict[str, Any]:
        """Generate detailed inventory report.

        Args:
            current_nav: Current portfolio NAV

        Returns:
            Summary of inventory report

        """
        logger.info(
            "Generating hedge inventory report",
            account_id=self._account_id,
            correlation_id=self._correlation_id,
        )

        generator = HedgeReportGenerator.from_environment(self._account_id)

        if current_nav is None:
            current_nav = self._get_current_nav()

        report = generator.generate_inventory_report(current_nav=current_nav)

        # Store to S3
        report_key = self._store_report_to_s3(
            report_type="inventory",
            report_date=datetime.now(UTC).date().isoformat(),
            report_data=report.to_dict(),
        )

        return {
            "report_type": "inventory",
            "total_positions": report.total_positions,
            "total_contracts": report.total_contracts,
            "total_premium_invested": str(report.total_premium_invested),
            "total_unrealized_pnl": str(report.total_unrealized_pnl),
            "portfolio_delta": str(report.portfolio_delta),
            "s3_report_key": report_key,
        }

    def _get_current_nav(self) -> Decimal:
        """Get current portfolio NAV from Alpaca or default.

        Returns:
            Current NAV

        """
        # In production, this would query Alpaca for actual NAV
        # For now, return a sensible default or environment variable
        default_nav = os.environ.get("DEFAULT_NAV_FOR_TESTING", "100000")
        return Decimal(default_nav)

    def _get_underlying_prices(self) -> dict[str, Decimal]:
        """Get current underlying prices.

        Returns:
            Dict of underlying symbol to current price

        """
        # In production, this would query Alpaca for actual prices
        # Return placeholder values for now
        return {
            "QQQ": Decimal("500"),
            "SPY": Decimal("600"),
        }

    def _format_daily_summary(self, report: Any) -> str:
        """Format daily report for SNS notification."""
        lines = [
            f"Daily Hedge Report for {report.report_date}",
            "=" * 40,
            "",
            "📊 Activity Today:",
            f"  - Hedges placed: {report.hedges_placed_today}",
            f"  - Hedges rolled: {report.hedges_rolled_today}",
            f"  - Hedges closed: {report.hedges_closed_today}",
            f"  - Hedges expired: {report.hedges_expired_today}",
            "",
            f"📈 Active Positions: {report.total_active_hedges}",
            "",
            "💰 Premium Spend:",
            f"  - Today: ${report.premium_spend.spend_today:,.2f}",
            f"  - MTD: ${report.premium_spend.spend_mtd:,.2f}",
            f"  - YTD: ${report.premium_spend.spend_ytd:,.2f}",
            f"  - Annual Cap: ${report.premium_spend.annual_cap:,.2f}",
            f"  - YTD % of Cap: {report.premium_spend.spend_ytd_pct_of_cap:.1f}%",
            f"  - Remaining Capacity: ${report.premium_spend.remaining_capacity:,.2f}",
        ]

        # Add scenario projections if available
        if report.scenario_projection:
            proj = report.scenario_projection
            lines.extend(
                [
                    "",
                    "📉 Scenario Projections:",
                    f"  - At -10%: ${proj.total_payoff_at_minus_10:,.2f} ({proj.total_payoff_nav_pct_at_minus_10:.2f}% NAV)",
                    f"  - At -20%: ${proj.total_payoff_at_minus_20:,.2f} ({proj.total_payoff_nav_pct_at_minus_20:.2f}% NAV)",
                    f"  - At -30%: ${proj.total_payoff_at_minus_30:,.2f} ({proj.total_payoff_nav_pct_at_minus_30:.2f}% NAV)",
                ]
            )

        # Add alerts
        if report.alerts:
            lines.extend(
                [
                    "",
                    "⚠️ Alerts:",
                ]
            )
            for alert in report.alerts:
                lines.append(f"  - {alert}")

        # Add attribution if present
        if report.attribution_report:
            lines.extend(
                [
                    "",
                    "📊 Attribution Report:",
                    f"  {report.attribution_report.summary}",
                ]
            )

        lines.extend(
            [
                "",
                f"Generated at: {report.generated_at.isoformat()}",
            ]
        )

        return "\n".join(lines)

    def _format_weekly_summary(self, report: Any) -> str:
        """Format weekly report for SNS notification."""
        lines = [
            f"Weekly Hedge Report: {report.report_week_start} to {report.report_week_end}",
            "=" * 50,
            "",
            "📊 Weekly Activity:",
            f"  - Hedges placed: {report.total_hedges_placed}",
            f"  - Hedges rolled: {report.total_hedges_rolled}",
            f"  - Hedges closed: {report.total_hedges_closed}",
            f"  - Hedges expired: {report.total_hedges_expired}",
            "",
            f"📈 End-of-Week Positions: {report.active_positions_count}",
            "",
            "💰 Premium Spend:",
            f"  - This Week: ${report.premium_spent_this_week:,.2f}",
            f"  - MTD: ${report.premium_spent_mtd:,.2f}",
            f"  - YTD: ${report.premium_spent_ytd:,.2f}",
        ]

        if report.average_fill_slippage_pct:
            lines.append(f"  - Avg Fill Slippage: {report.average_fill_slippage_pct:.2f}%")

        # Add scenario projections if available
        if report.scenario_projection:
            proj = report.scenario_projection
            lines.extend(
                [
                    "",
                    "📉 Scenario Projections:",
                    f"  - At -10%: ${proj.total_payoff_at_minus_10:,.2f} ({proj.total_payoff_nav_pct_at_minus_10:.2f}% NAV)",
                    f"  - At -20%: ${proj.total_payoff_at_minus_20:,.2f} ({proj.total_payoff_nav_pct_at_minus_20:.2f}% NAV)",
                    f"  - At -30%: ${proj.total_payoff_at_minus_30:,.2f} ({proj.total_payoff_nav_pct_at_minus_30:.2f}% NAV)",
                ]
            )

        lines.extend(
            [
                "",
                f"Generated at: {report.generated_at.isoformat()}",
            ]
        )

        return "\n".join(lines)

    def _publish_to_sns(self, subject: str, message: str) -> bool:
        """Publish report summary to SNS topic.

        Args:
            subject: Email subject
            message: Report content

        Returns:
            True if published successfully

        """
        topic_arn = os.environ.get("TRADING_NOTIFICATIONS_TOPIC_ARN")
        if not topic_arn:
            logger.warning(
                "TRADING_NOTIFICATIONS_TOPIC_ARN not set, skipping SNS notification",
                correlation_id=self._correlation_id,
            )
            return False

        try:
            self._sns_client.publish(
                TopicArn=topic_arn,
                Subject=subject[:100],  # SNS subject limit
                Message=message,
            )
            logger.info(
                "Published hedge report to SNS",
                topic_arn=topic_arn,
                subject=subject,
                correlation_id=self._correlation_id,
            )
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(
                "Failed to publish to SNS",
                error=str(e),
                topic_arn=topic_arn,
                correlation_id=self._correlation_id,
            )
            return False

    def _store_report_to_s3(
        self,
        report_type: str,
        report_date: str,
        report_data: dict[str, Any],
    ) -> str | None:
        """Store full report to S3.

        Args:
            report_type: Type of report (daily, weekly, inventory)
            report_date: Report date string
            report_data: Full report data

        Returns:
            S3 key if stored successfully, None otherwise

        """
        bucket_name = os.environ.get("HEDGE_REPORTS_BUCKET")
        if not bucket_name:
            logger.debug(
                "HEDGE_REPORTS_BUCKET not set, skipping S3 storage",
                correlation_id=self._correlation_id,
            )
            return None

        key = f"hedge-reports/{report_type}/{report_date}.json"

        try:
            self._s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(report_data, default=str, indent=2),
                ContentType="application/json",
            )
            logger.info(
                "Stored hedge report to S3",
                bucket=bucket_name,
                key=key,
                correlation_id=self._correlation_id,
            )
            return key
        except (ClientError, BotoCoreError) as e:
            logger.error(
                "Failed to store report to S3",
                error=str(e),
                bucket=bucket_name,
                key=key,
                correlation_id=self._correlation_id,
            )
            return None
