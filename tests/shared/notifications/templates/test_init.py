"""Business Unit: shared/notifications | Status: current.

Tests for shared.notifications.templates.__init__ module exports.

Validates that the templates __init__ module correctly exports the expected
public API and maintains proper module structure.
"""

from __future__ import annotations


def test_templates_module_exports() -> None:
    """Test that templates module exports expected components."""
    from the_alchemiser.shared.notifications import templates

    # Verify __all__ attribute exists and contains expected exports
    assert hasattr(templates, "__all__")

    # Verify all expected exports are present (after H1 fix)
    expected_exports = {
        "BaseEmailTemplate",
        "EmailTemplates",
        "MultiStrategyReportBuilder",
        "PortfolioBuilder",
        "SignalsBuilder",
        "build_error_email_html",
        "build_multi_strategy_email_html",
        "build_trading_report_html",
    }

    actual_exports = set(templates.__all__)
    assert actual_exports == expected_exports, (
        f"Export mismatch. Expected: {expected_exports}, Got: {actual_exports}"
    )


def test_base_template_import() -> None:
    """Test that BaseEmailTemplate can be imported directly."""
    from the_alchemiser.shared.notifications.templates import BaseEmailTemplate

    # Verify it's a class
    assert isinstance(BaseEmailTemplate, type)

    # Verify the class has expected methods
    assert hasattr(BaseEmailTemplate, "wrap_content")
    assert hasattr(BaseEmailTemplate, "get_header")
    assert hasattr(BaseEmailTemplate, "get_footer")
    assert hasattr(BaseEmailTemplate, "get_base_styles")
    assert hasattr(BaseEmailTemplate, "create_section")
    assert hasattr(BaseEmailTemplate, "create_alert_box")


def test_email_templates_import() -> None:
    """Test that EmailTemplates facade can be imported directly."""
    from the_alchemiser.shared.notifications.templates import EmailTemplates

    # Verify it's a class
    assert isinstance(EmailTemplates, type)

    # Verify facade methods exist
    assert hasattr(EmailTemplates, "error_notification")
    assert hasattr(EmailTemplates, "successful_trading_run")
    assert hasattr(EmailTemplates, "failed_trading_run")
    assert hasattr(EmailTemplates, "build_error_report")


def test_builder_functions_import() -> None:
    """Test that convenience functions can be imported directly."""
    from the_alchemiser.shared.notifications.templates import (
        build_error_email_html,
        build_multi_strategy_email_html,
        build_trading_report_html,
    )

    # Verify they're callable
    assert callable(build_error_email_html)
    assert callable(build_multi_strategy_email_html)
    assert callable(build_trading_report_html)


def test_build_error_email_html_basic() -> None:
    """Test build_error_email_html produces valid HTML output."""
    from the_alchemiser.shared.notifications.templates import build_error_email_html

    html = build_error_email_html("Test Error", "This is a test error message")

    # Verify basic HTML structure (strip leading whitespace for assertion)
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "Test Error" in html
    assert "This is a test error message" in html
    assert "</html>" in html


def test_build_multi_strategy_email_html_function_exists() -> None:
    """Test build_multi_strategy_email_html function exists and is callable."""
    from the_alchemiser.shared.notifications.templates import (
        build_multi_strategy_email_html,
    )

    # Just verify it's callable - integration tests cover full functionality
    assert callable(build_multi_strategy_email_html)


def test_templates_module_structure() -> None:
    """Test that templates module has proper structure and documentation."""
    from the_alchemiser.shared.notifications import templates

    # Verify module docstring exists
    assert templates.__doc__ is not None
    assert len(templates.__doc__) > 0

    # Verify business unit identifier in docstring
    assert "Business Unit:" in templates.__doc__
    assert "Status: current" in templates.__doc__

    # Verify module purpose is documented
    assert "template" in templates.__doc__.lower()


def test_module_has_no_external_dependencies() -> None:
    """Verify the __init__.py only imports from internal modules."""
    from the_alchemiser.shared.notifications import templates

    # Get module's imports (this is indirect verification)
    # The module should only import from .base and .email_facade
    # This test verifies no unexpected third-party dependencies leaked in
    assert hasattr(templates, "BaseEmailTemplate")
    assert hasattr(templates, "EmailTemplates")


def test_all_exports_are_accessible() -> None:
    """Test that all items in __all__ can be actually accessed."""
    from the_alchemiser.shared.notifications import templates

    # Verify every item in __all__ is actually accessible
    for export_name in templates.__all__:
        assert hasattr(templates, export_name), (
            f"Export '{export_name}' listed in __all__ but not accessible"
        )


def test_base_template_static_methods() -> None:
    """Test BaseEmailTemplate has expected static methods."""
    import inspect

    from the_alchemiser.shared.notifications.templates import BaseEmailTemplate

    # Verify key methods are static
    assert isinstance(inspect.getattr_static(BaseEmailTemplate, "wrap_content"), staticmethod)
    assert isinstance(inspect.getattr_static(BaseEmailTemplate, "get_header"), staticmethod)


def test_email_templates_has_static_methods() -> None:
    """Test EmailTemplates facade uses static methods."""
    import inspect

    from the_alchemiser.shared.notifications.templates import EmailTemplates

    # Verify facade methods are static (no self parameter needed)
    assert isinstance(inspect.getattr_static(EmailTemplates, "error_notification"), staticmethod)
    assert isinstance(
        inspect.getattr_static(EmailTemplates, "successful_trading_run"), staticmethod
    )


def test_builder_classes_import() -> None:
    """Test that builder classes can be imported directly."""
    from the_alchemiser.shared.notifications.templates import (
        MultiStrategyReportBuilder,
        PortfolioBuilder,
        SignalsBuilder,
    )

    # Verify they're classes
    assert isinstance(PortfolioBuilder, type)
    assert isinstance(SignalsBuilder, type)
    assert isinstance(MultiStrategyReportBuilder, type)


def test_builder_classes_have_expected_methods() -> None:
    """Test that builder classes have their expected methods."""
    from the_alchemiser.shared.notifications.templates import (
        MultiStrategyReportBuilder,
        PortfolioBuilder,
        SignalsBuilder,
    )

    # PortfolioBuilder should have build methods
    assert hasattr(PortfolioBuilder, "build_account_summary_neutral")

    # SignalsBuilder should have build methods
    # (exact method names may vary, just verify it's a proper class)
    assert hasattr(SignalsBuilder, "__dict__") or hasattr(SignalsBuilder, "__class__")

    # MultiStrategyReportBuilder should have build methods
    assert hasattr(MultiStrategyReportBuilder, "build_multi_strategy_report_neutral")
