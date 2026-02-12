"""Business Unit: notifications | Status: current.

Handler for HedgeEvaluationCompleted events.
"""

from __future__ import annotations

import decimal
import os
from decimal import Decimal
from typing import Any

from service import NotificationService

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class HedgeHandler:
    """Handles HedgeEvaluationCompleted events."""

    def handle(self, detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        """Process HedgeEvaluationCompleted event.

        Args:
            detail: The detail payload from HedgeEvaluationCompleted event.
            correlation_id: Correlation ID for tracing.

        Returns:
            Response with status code and message.

        """
        skip_reason = detail.get("skip_reason")
        recommendations = detail.get("recommendations", [])

        if skip_reason:
            logger.info(
                "Hedge evaluation skipped, no notification sent",
                extra={"correlation_id": correlation_id, "skip_reason": skip_reason},
            )
            return {
                "statusCode": 200,
                "body": f"Hedge skipped ({skip_reason}), no notification for {correlation_id}",
            }

        logger.info(
            "Processing HedgeEvaluationCompleted",
            extra={
                "correlation_id": correlation_id,
                "recommendation_count": len(recommendations),
                "vix_tier": detail.get("vix_tier"),
            },
        )

        context = self._build_context(detail, correlation_id)
        self._send_email(context, correlation_id)

        return {
            "statusCode": 200,
            "body": f"Hedge evaluation notification sent for {correlation_id}",
        }

    def _build_context(self, detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        """Build template context for hedge evaluation success email."""
        stage = os.environ.get("APP__STAGE", "dev")

        container = ApplicationContainer.create_for_notifications("production")
        notification_service = NotificationService(container)
        logs_url = notification_service.build_logs_url(correlation_id)

        budget_nav_pct = detail.get("budget_nav_pct", "0")
        try:
            budget_display = str(round(Decimal(str(budget_nav_pct)) * 100, 3))
        except (decimal.InvalidOperation, TypeError, ValueError):
            budget_display = str(budget_nav_pct)

        return {
            "env": stage,
            "run_id": correlation_id,
            "portfolio_nav": detail.get("portfolio_nav", "N/A"),
            "vix_tier": detail.get("vix_tier", "unknown"),
            "template_selected": detail.get("template_selected", "unknown"),
            "template_regime": detail.get("template_regime", "N/A"),
            "template_selection_reason": detail.get("template_selection_reason", ""),
            "total_premium_budget": detail.get("total_premium_budget", "N/A"),
            "budget_nav_pct": budget_display,
            "current_vix": detail.get("current_vix", "N/A"),
            "exposure_multiplier": detail.get("exposure_multiplier", "1.0"),
            "recommendations": detail.get("recommendations", []),
            "logs_url": logs_url,
        }

    def _send_email(self, context: dict[str, Any], correlation_id: str) -> None:
        """Render and send hedge evaluation success email."""
        from the_alchemiser.shared.notifications.hedge_templates import (
            render_hedge_evaluation_success_html,
            render_hedge_evaluation_success_text,
        )

        html_body = render_hedge_evaluation_success_html(context)
        text_body = render_hedge_evaluation_success_text(context)

        container = ApplicationContainer.create_for_notifications("production")
        notification_service = NotificationService(container)
        notification_service.send_notification(
            component="hedge evaluation",
            status="SUCCESS",
            html_body=html_body,
            text_body=text_body,
            correlation_id=correlation_id,
        )

        logger.info(
            "Hedge evaluation notification dispatched via NotificationService",
            extra={"correlation_id": correlation_id},
        )
