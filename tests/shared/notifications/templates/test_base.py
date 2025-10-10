#!/usr/bin/env python3
"""Test suite for base.py notification template module.

Tests BaseEmailTemplate for:
- Type safety and return values
- HTML structure correctness
- Datetime handling (deterministic timestamps)
- Edge cases (empty strings, None values)
- CSS styling and email client compatibility
- Method behavior and contracts
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from the_alchemiser.shared.constants import APPLICATION_NAME
from the_alchemiser.shared.notifications.templates.base import BaseEmailTemplate


class TestBaseEmailTemplateClass:
    """Test BaseEmailTemplate class structure and configuration."""

    def test_class_has_logo_configuration(self):
        """Test that class has logo configuration constants."""
        assert hasattr(BaseEmailTemplate, "LOGO_URL")
        assert hasattr(BaseEmailTemplate, "LOGO_SIZE")
        assert isinstance(BaseEmailTemplate.LOGO_URL, str)
        assert isinstance(BaseEmailTemplate.LOGO_SIZE, str)

    def test_logo_url_is_https(self):
        """Test that logo URL uses HTTPS for security."""
        assert BaseEmailTemplate.LOGO_URL.startswith("https://")

    def test_logo_size_has_units(self):
        """Test that logo size includes CSS units."""
        assert BaseEmailTemplate.LOGO_SIZE.endswith("px")


class TestGetBaseStyles:
    """Test get_base_styles method."""

    def test_returns_string(self):
        """Test that get_base_styles returns a string."""
        result = BaseEmailTemplate.get_base_styles()
        assert isinstance(result, str)

    def test_contains_style_tag(self):
        """Test that result contains <style> tags."""
        result = BaseEmailTemplate.get_base_styles()
        assert "<style>" in result
        assert "</style>" in result

    def test_contains_media_query(self):
        """Test that result contains responsive media query."""
        result = BaseEmailTemplate.get_base_styles()
        assert "@media" in result
        assert "max-width: 600px" in result

    def test_contains_responsive_classes(self):
        """Test that result contains responsive utility classes."""
        result = BaseEmailTemplate.get_base_styles()
        assert "sm-w-full" in result
        assert "sm-px-24" in result


class TestGetHeader:
    """Test get_header method."""

    def test_returns_string(self):
        """Test that get_header returns a string."""
        result = BaseEmailTemplate.get_header()
        assert isinstance(result, str)

    def test_default_subtitle(self):
        """Test header with default subtitle."""
        result = BaseEmailTemplate.get_header()
        assert "Institutional Portfolio Management System" in result

    def test_custom_subtitle(self):
        """Test header with custom subtitle."""
        custom_subtitle = "Custom Trading System"
        result = BaseEmailTemplate.get_header(subtitle=custom_subtitle)
        assert custom_subtitle in result
        assert "Institutional Portfolio Management System" not in result

    def test_contains_application_name(self):
        """Test that header contains application name."""
        result = BaseEmailTemplate.get_header()
        assert APPLICATION_NAME in result

    def test_contains_logo(self):
        """Test that header contains logo img tag."""
        result = BaseEmailTemplate.get_header()
        assert "<img" in result
        assert BaseEmailTemplate.LOGO_URL in result
        assert "alt=" in result

    def test_contains_table_structure(self):
        """Test that header uses proper HTML table structure."""
        result = BaseEmailTemplate.get_header()
        assert "<tr>" in result
        assert "<td" in result
        assert "</td>" in result
        assert "</tr>" in result


class TestGetCombinedHeaderStatus:
    """Test get_combined_header_status method."""

    def test_returns_string(self):
        """Test that method returns a string."""
        result = BaseEmailTemplate.get_combined_header_status(
            title="Test", status="Success", status_color="#10B981", _status_emoji="✅"
        )
        assert isinstance(result, str)

    def test_contains_title(self):
        """Test that result contains the title."""
        title = "Trading Report"
        result = BaseEmailTemplate.get_combined_header_status(
            title=title, status="Success", status_color="#10B981", _status_emoji="✅"
        )
        assert title in result

    def test_contains_status(self):
        """Test that result contains the status text."""
        status = "Completed"
        result = BaseEmailTemplate.get_combined_header_status(
            title="Report", status=status, status_color="#10B981", _status_emoji="✅"
        )
        assert status in result

    def test_uses_status_color(self):
        """Test that result uses the provided status color."""
        color = "#FF5733"
        result = BaseEmailTemplate.get_combined_header_status(
            title="Test", status="Warning", status_color=color, _status_emoji="⚠️"
        )
        assert color in result

    def test_default_timestamp_is_utc(self):
        """Test that default timestamp is UTC aware."""
        result = BaseEmailTemplate.get_combined_header_status(
            title="Test", status="Success", status_color="#10B981", _status_emoji="✅"
        )
        assert "UTC" in result

    def test_custom_timestamp(self):
        """Test with custom timestamp."""
        timestamp = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        result = BaseEmailTemplate.get_combined_header_status(
            title="Test",
            status="Success",
            status_color="#10B981",
            _status_emoji="✅",
            timestamp=timestamp,
        )
        assert "2024-01-15" in result
        assert "10:30:45" in result

    def test_contains_application_name(self):
        """Test that combined header contains application name."""
        result = BaseEmailTemplate.get_combined_header_status(
            title="Test", status="Success", status_color="#10B981", _status_emoji="✅"
        )
        assert APPLICATION_NAME in result


class TestGetStatusBanner:
    """Test get_status_banner method."""

    def test_returns_string(self):
        """Test that method returns a string."""
        result = BaseEmailTemplate.get_status_banner(
            title="Test", status="Success", status_color="#10B981", status_emoji="✅"
        )
        assert isinstance(result, str)

    def test_contains_title(self):
        """Test that result contains the title."""
        title = "Workflow Complete"
        result = BaseEmailTemplate.get_status_banner(
            title=title, status="Success", status_color="#10B981", status_emoji="✅"
        )
        assert title in result

    def test_contains_status(self):
        """Test that result contains the status text."""
        status = "Failed"
        result = BaseEmailTemplate.get_status_banner(
            title="Error", status=status, status_color="#EF4444", status_emoji="❌"
        )
        assert status in result

    def test_uses_status_color(self):
        """Test that result uses the provided status color."""
        color = "#F59E0B"
        result = BaseEmailTemplate.get_status_banner(
            title="Test", status="Warning", status_color=color, status_emoji="⚠️"
        )
        assert color in result

    def test_default_timestamp_is_utc(self):
        """Test that default timestamp is UTC aware."""
        result = BaseEmailTemplate.get_status_banner(
            title="Test", status="Success", status_color="#10B981", status_emoji="✅"
        )
        assert "UTC" in result

    def test_custom_timestamp(self):
        """Test with custom timestamp."""
        timestamp = datetime(2024, 6, 20, 14, 22, 10, tzinfo=UTC)
        result = BaseEmailTemplate.get_status_banner(
            title="Test",
            status="Success",
            status_color="#10B981",
            status_emoji="✅",
            timestamp=timestamp,
        )
        assert "2024-06-20" in result
        assert "14:22:10" in result


class TestGetFooter:
    """Test get_footer method."""

    def test_returns_string(self):
        """Test that get_footer returns a string."""
        result = BaseEmailTemplate.get_footer()
        assert isinstance(result, str)

    def test_contains_application_name(self):
        """Test that footer contains application name."""
        result = BaseEmailTemplate.get_footer()
        assert APPLICATION_NAME in result

    def test_contains_disclaimer(self):
        """Test that footer contains legal disclaimer."""
        result = BaseEmailTemplate.get_footer()
        assert "informational purposes" in result
        assert "investment advice" in result

    def test_contains_tagline(self):
        """Test that footer contains system tagline."""
        result = BaseEmailTemplate.get_footer()
        assert "Multi-Strategy" in result or "Portfolio Management" in result


class TestWrapContent:
    """Test wrap_content method."""

    def test_returns_string(self):
        """Test that wrap_content returns a string."""
        result = BaseEmailTemplate.wrap_content("Test content")
        assert isinstance(result, str)

    def test_contains_doctype(self):
        """Test that result contains HTML5 DOCTYPE."""
        result = BaseEmailTemplate.wrap_content("Test content")
        assert "<!DOCTYPE html>" in result

    def test_contains_html_tags(self):
        """Test that result contains proper HTML structure."""
        result = BaseEmailTemplate.wrap_content("Test content")
        assert "<html" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "</head>" in result
        assert "<body" in result
        assert "</body>" in result

    def test_contains_meta_tags(self):
        """Test that result contains email client meta tags."""
        result = BaseEmailTemplate.wrap_content("Test content")
        assert '<meta charset="utf-8">' in result
        assert 'name="viewport"' in result
        assert 'name="format-detection"' in result

    def test_contains_provided_content(self):
        """Test that result contains the provided content."""
        content = "This is my custom content"
        result = BaseEmailTemplate.wrap_content(content)
        assert content in result

    def test_default_title(self):
        """Test that default title is APPLICATION_NAME."""
        result = BaseEmailTemplate.wrap_content("Test")
        assert f"<title>{APPLICATION_NAME}</title>" in result

    def test_custom_title(self):
        """Test with custom title."""
        custom_title = "Custom Email Title"
        result = BaseEmailTemplate.wrap_content("Test", title=custom_title)
        assert f"<title>{custom_title}</title>" in result

    def test_includes_base_styles(self):
        """Test that wrapped content includes base styles."""
        result = BaseEmailTemplate.wrap_content("Test")
        assert "<style>" in result
        assert "@media" in result

    def test_outlook_compatibility(self):
        """Test that result includes Outlook/MSO compatibility code."""
        result = BaseEmailTemplate.wrap_content("Test")
        assert "<!--[if mso]>" in result
        assert "<![endif]-->" in result
        assert "PixelsPerInch" in result

    def test_preview_text(self):
        """Test that result includes hidden preview text."""
        title = "Test Title"
        result = BaseEmailTemplate.wrap_content("Content", title=title)
        assert f'<div style="display: none;">{title}' in result


class TestCreateSection:
    """Test create_section method."""

    def test_returns_string(self):
        """Test that create_section returns a string."""
        result = BaseEmailTemplate.create_section("Title", "Content")
        assert isinstance(result, str)

    def test_contains_title(self):
        """Test that result contains the section title."""
        title = "Performance Metrics"
        result = BaseEmailTemplate.create_section(title, "Some content")
        assert title in result

    def test_contains_content(self):
        """Test that result contains the section content."""
        content = "This is the section body"
        result = BaseEmailTemplate.create_section("Title", content)
        assert content in result

    def test_default_margin(self):
        """Test that default margin is applied."""
        result = BaseEmailTemplate.create_section("Title", "Content")
        assert "24px 0" in result

    def test_custom_margin(self):
        """Test that custom margin is applied."""
        custom_margin = "10px 20px"
        result = BaseEmailTemplate.create_section("Title", "Content", margin=custom_margin)
        assert custom_margin in result

    def test_contains_h3_tag(self):
        """Test that title uses h3 tag."""
        result = BaseEmailTemplate.create_section("Title", "Content")
        assert "<h3" in result
        assert "</h3>" in result


class TestCreateAlertBox:
    """Test create_alert_box method."""

    def test_returns_string(self):
        """Test that create_alert_box returns a string."""
        result = BaseEmailTemplate.create_alert_box("Alert message")
        assert isinstance(result, str)

    def test_contains_message(self):
        """Test that result contains the alert message."""
        message = "This is an important alert"
        result = BaseEmailTemplate.create_alert_box(message)
        assert message in result

    def test_default_alert_type_is_info(self):
        """Test that default alert type is info (blue)."""
        result = BaseEmailTemplate.create_alert_box("Message")
        assert "#3B82F6" in result or "#DBEAFE" in result  # Info colors

    def test_success_alert_color(self):
        """Test that success alert uses green color."""
        result = BaseEmailTemplate.create_alert_box("Success!", "success")
        assert "#10B981" in result or "#D1FAE5" in result  # Success colors

    def test_error_alert_color(self):
        """Test that error alert uses red color."""
        result = BaseEmailTemplate.create_alert_box("Error!", "error")
        assert "#EF4444" in result or "#FEE2E2" in result  # Error colors

    def test_warning_alert_color(self):
        """Test that warning alert uses yellow/orange color."""
        result = BaseEmailTemplate.create_alert_box("Warning!", "warning")
        assert "#F59E0B" in result or "#FEF3C7" in result  # Warning colors

    def test_invalid_alert_type_falls_back_to_info(self):
        """Test that invalid alert type falls back to info styling."""
        result = BaseEmailTemplate.create_alert_box("Message", "invalid_type")
        assert "#3B82F6" in result or "#DBEAFE" in result  # Info colors (fallback)

    def test_has_border(self):
        """Test that alert box has a border."""
        result = BaseEmailTemplate.create_alert_box("Message")
        assert "border" in result


class TestCreateTable:
    """Test create_table method."""

    def test_returns_string(self):
        """Test that create_table returns a string."""
        result = BaseEmailTemplate.create_table(["Header 1"], [["Cell 1"]])
        assert isinstance(result, str)

    def test_contains_headers(self):
        """Test that result contains all header values."""
        headers = ["Symbol", "Quantity", "Price"]
        result = BaseEmailTemplate.create_table(headers, [])
        for header in headers:
            assert header in result

    def test_contains_row_data(self):
        """Test that result contains all row data."""
        rows = [["AAPL", "100", "$150.00"], ["GOOGL", "50", "$2800.00"]]
        result = BaseEmailTemplate.create_table(["Symbol", "Qty", "Price"], rows)
        for row in rows:
            for cell in row:
                assert cell in result

    def test_empty_table(self):
        """Test table with no rows."""
        headers = ["Column 1", "Column 2"]
        result = BaseEmailTemplate.create_table(headers, [])
        assert "<thead>" in result
        assert "<tbody>" in result
        for header in headers:
            assert header in result

    def test_table_structure(self):
        """Test that result has proper table HTML structure."""
        result = BaseEmailTemplate.create_table(["H1"], [["C1"]])
        assert "<table" in result
        assert "</table>" in result
        assert "<thead>" in result
        assert "</thead>" in result
        assert "<tbody>" in result
        assert "</tbody>" in result
        assert "<tr>" in result
        assert "</tr>" in result
        assert "<th" in result
        assert "</th>" in result
        assert "<td" in result
        assert "</td>" in result

    def test_table_id_attribute(self):
        """Test that table id attribute is set when provided."""
        table_id = "performance-metrics-table"
        result = BaseEmailTemplate.create_table(
            ["Header"], [["Data"]], table_id=table_id
        )
        assert f'id="{table_id}"' in result

    def test_table_no_id_when_empty_string(self):
        """Test that table has empty id when not provided."""
        result = BaseEmailTemplate.create_table(["Header"], [["Data"]])
        assert 'id=""' in result

    def test_multiple_columns(self):
        """Test table with multiple columns."""
        headers = ["Col1", "Col2", "Col3", "Col4"]
        rows = [["A1", "A2", "A3", "A4"], ["B1", "B2", "B3", "B4"]]
        result = BaseEmailTemplate.create_table(headers, rows)
        # All headers should be present
        for header in headers:
            assert header in result
        # All cell values should be present
        for row in rows:
            for cell in row:
                assert cell in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_content(self):
        """Test methods with empty string inputs."""
        # These should not raise exceptions
        BaseEmailTemplate.wrap_content("")
        BaseEmailTemplate.create_section("", "")
        BaseEmailTemplate.create_alert_box("")

    def test_special_html_characters(self):
        """Test that special characters are passed through (not escaped)."""
        # Note: This module doesn't escape HTML by design (internal use only)
        content = "<strong>Bold</strong> & <em>italic</em>"
        result = BaseEmailTemplate.create_alert_box(content)
        assert content in result

    def test_very_long_strings(self):
        """Test that methods handle very long strings."""
        long_content = "A" * 10000
        result = BaseEmailTemplate.wrap_content(long_content)
        assert long_content in result

    def test_none_timestamp_uses_default(self):
        """Test that None timestamp uses current UTC time."""
        result = BaseEmailTemplate.get_status_banner(
            title="Test",
            status="Success",
            status_color="#10B981",
            status_emoji="✅",
            timestamp=None,
        )
        # Should contain "UTC" timestamp
        assert "UTC" in result

    def test_table_with_mismatched_columns(self):
        """Test table where rows have different column counts than headers."""
        headers = ["H1", "H2", "H3"]
        rows = [["A1", "A2"], ["B1", "B2", "B3", "B4"]]  # Mismatched columns
        # Should not raise exception
        result = BaseEmailTemplate.create_table(headers, rows)
        assert isinstance(result, str)


class TestDeterminism:
    """Test deterministic behavior for testability."""

    def test_same_inputs_produce_same_output(self):
        """Test that same inputs always produce same output (pure function)."""
        title = "Test"
        content = "Content"

        result1 = BaseEmailTemplate.create_section(title, content)
        result2 = BaseEmailTemplate.create_section(title, content)

        assert result1 == result2

    def test_timestamp_formatting_is_consistent(self):
        """Test that timestamp formatting is consistent."""
        timestamp = datetime(2024, 3, 15, 9, 30, 0, tzinfo=UTC)

        result1 = BaseEmailTemplate.get_status_banner(
            title="Test",
            status="Success",
            status_color="#10B981",
            status_emoji="✅",
            timestamp=timestamp,
        )
        result2 = BaseEmailTemplate.get_status_banner(
            title="Test",
            status="Success",
            status_color="#10B981",
            status_emoji="✅",
            timestamp=timestamp,
        )

        assert result1 == result2
        assert "2024-03-15 09:30:00 UTC" in result1
