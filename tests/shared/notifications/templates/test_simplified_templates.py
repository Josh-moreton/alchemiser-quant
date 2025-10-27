"""Business Unit: shared/notifications | Status: current.

Tests for simplified email templates (Hargreaves Lansdown style).

Validates that the new simplified email templates produce clean, professional
emails suitable for production use.
"""

from __future__ import annotations


def test_simple_trading_notification_success() -> None:
    """Test simplified success notification generates valid HTML."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=5,
        correlation_id="test-correlation-123",
        pdf_attached=False,
    )

    # Verify basic HTML structure
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html

    # Verify success-specific content
    assert "Execution Completed Successfully" in html
    assert "pleased to confirm" in html
    assert "5 rebalancing orders" in html
    assert "PAPER" in html
    assert "test-correlation-123" in html

    # Verify it's simplified (should NOT contain detailed tables)
    assert "Portfolio Rebalancing Plan" not in html
    assert "Order Execution Details" not in html

    # Verify professional tone
    assert "Dear Investor" in html
    assert "contact our support team" in html


def test_simple_trading_notification_failure() -> None:
    """Test simplified failure notification generates valid HTML."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=False,
        mode="LIVE",
        orders_count=0,
        correlation_id="test-correlation-456",
        pdf_attached=False,
    )

    # Verify basic HTML structure
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html

    # Verify failure-specific content
    assert "Execution Failed" in html
    assert "regret to inform" in html
    assert "encountered an error" in html
    assert "LIVE" in html
    assert "test-correlation-456" in html

    # Verify it's simplified (should NOT contain detailed tables)
    assert "Portfolio Rebalancing Plan" not in html
    assert "Order Execution Details" not in html

    # Verify professional tone
    assert "Dear Investor" in html
    assert "contact our support team" in html


def test_simple_trading_notification_with_pdf_reference() -> None:
    """Test simplified notification with PDF attachment reference."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=3,
        correlation_id="test-correlation-789",
        pdf_attached=True,
    )

    # Verify PDF reference is included
    assert "detailed execution report is attached" in html
    assert "PDF document" in html
    assert "strategy signals" in html
    assert "allocation changes" in html


def test_simple_trading_notification_without_pdf_reference() -> None:
    """Test simplified notification without PDF attachment reference."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=3,
        correlation_id="test-correlation-789",
        pdf_attached=False,
    )

    # Verify alternative message is included
    assert "review the system logs" in html or "contact support" in html

    # Verify PDF reference is NOT included
    assert "attached" not in html.lower() or "report is attached" not in html


def test_simple_trading_notification_singular_order() -> None:
    """Test notification handles singular order count correctly."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=1,
        correlation_id="test-correlation-single",
        pdf_attached=False,
    )

    # Should use singular "order" not "orders"
    assert "1 rebalancing order" in html


def test_simple_trading_notification_xss_protection() -> None:
    """Test that correlation ID is properly escaped to prevent XSS."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    malicious_id = "<script>alert('xss')</script>"
    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=1,
        correlation_id=malicious_id,
        pdf_attached=False,
    )

    # Verify script tag is escaped
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_simple_trading_notification_no_correlation_id() -> None:
    """Test notification works without correlation ID."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=2,
        correlation_id=None,
        pdf_attached=False,
    )

    # Should still generate valid HTML
    assert "<!DOCTYPE html>" in html
    assert "Execution Completed Successfully" in html

    # Correlation ID section should be empty or not present
    assert "Correlation ID:" not in html


def test_simple_trading_notification_email_structure() -> None:
    """Test that email has proper structure for email clients."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    html = EmailTemplates.simple_trading_notification(
        success=True,
        mode="PAPER",
        orders_count=3,
        correlation_id="test-structure",
        pdf_attached=True,
    )

    # Verify DOCTYPE
    assert "<!DOCTYPE html>" in html

    # Verify HTML and meta tags for email clients
    assert "<html" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "</head>" in html

    # Verify body structure
    assert "<body" in html
    assert "</body>" in html

    # Verify table-based layout (for email compatibility)
    assert "<table" in html
    assert "</table>" in html
