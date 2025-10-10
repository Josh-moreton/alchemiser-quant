"""Business Unit: shared; Status: current.

Base HTML email template module.

This module provides the core HTML template structure and common styling
used across all email types in the notification system.

The BaseEmailTemplate class offers static methods for generating responsive,
email-client-compatible HTML templates with consistent branding and styling.
All methods are pure functions with no side effects.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ...constants import APPLICATION_NAME


class BaseEmailTemplate:
    """Base class for HTML email templates with responsive design.

    This class provides static methods for building professional HTML email templates
    with consistent branding, responsive layouts, and email client compatibility
    (including Outlook/MSO support).

    All methods are pure functions (no side effects) and return HTML strings.
    The templates use inline CSS for maximum email client compatibility.

    Usage:
        >>> content = BaseEmailTemplate.create_alert_box("Success!", "success")
        >>> header = BaseEmailTemplate.get_header()
        >>> footer = BaseEmailTemplate.get_footer()
        >>> email_html = BaseEmailTemplate.wrap_content(header + content + footer)

    """

    # Logo configuration - update this URL to your hosted logo
    LOGO_URL = "https://alchemiser.rwxt.org/android-chrome-512x512.png"
    LOGO_SIZE = "32px"

    @staticmethod
    def get_base_styles() -> str:
        """Get common CSS styles for email templates.

        Returns:
            str: CSS <style> block with responsive media queries for mobile devices.
                 Includes width adjustments and padding for screens under 600px.

        """
        return """
        <style>
            @media (max-width: 600px) {
                .sm-w-full { width: 100% !important; }
                .sm-px-24 { padding-left: 24px !important; padding-right: 24px !important; }
            }
        </style>
        """

    @staticmethod
    def get_header(subtitle: str = "Institutional Portfolio Management System") -> str:
        """Get HTML header section with logo and branding.

        Args:
            subtitle: Subtitle text displayed under the main application name.
                     Defaults to "Institutional Portfolio Management System".

        Returns:
            str: HTML table row containing the header with gradient background,
                 logo, application name, and subtitle.

        """
        return f"""
        <tr>
            <td style="padding: 16px 24px; text-align: center; background: linear-gradient(135deg, #1F2937, #374151); border-radius: 8px 8px 0 0;">
                <img src="{BaseEmailTemplate.LOGO_URL}" alt="{APPLICATION_NAME} Logo" style="width: {BaseEmailTemplate.LOGO_SIZE}; height: {BaseEmailTemplate.LOGO_SIZE}; margin-bottom: 8px;" />
                <h1 style="margin: 0; color: white; font-size: 18px; font-weight: 600; letter-spacing: 0.5px;">
                    {APPLICATION_NAME}
                </h1>
                <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500;">
                    {subtitle}
                </p>
            </td>
        </tr>
        """

    @staticmethod
    def get_combined_header_status(
        title: str,
        status: str,
        status_color: str,
        _status_emoji: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Get combined header and status in one section.

        Args:
            title: Title for the status section
            status: Status text
            status_color: Background color for status
            _status_emoji: Status emoji (currently unused in this template variant)
            timestamp: Optional timestamp

        """
        timestamp = timestamp or datetime.now(UTC)

        return f"""
        <tr>
            <td style="padding: 16px 24px; text-align: center; background: linear-gradient(135deg, #1F2937, #374151); border-radius: 8px 8px 0 0;">
                <img src="{BaseEmailTemplate.LOGO_URL}" alt="{APPLICATION_NAME} Logo" style="width: {BaseEmailTemplate.LOGO_SIZE}; height: {BaseEmailTemplate.LOGO_SIZE}; margin-bottom: 8px;" />
                <h1 style="margin: 0; color: white; font-size: 18px; font-weight: 600; letter-spacing: 0.5px;">
                    {APPLICATION_NAME}
                </h1>
                <p style="margin: 4px 0 8px 0; color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500;">
                    Institutional Portfolio Management System
                </p>
                <div style="background: {status_color}; padding: 10px 18px; border-radius: 6px; margin-top: 10px;">
                    <h2 style="margin: 0; color: white; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
                        {title}
                    </h2>
                    <p style="margin: 4px 0 0 0; color: rgba(255,255,255,0.95); font-size: 12px; font-weight: 500;">
                        Status: {status} | {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
                    </p>
                </div>
            </td>
        </tr>
        """

    @staticmethod
    def get_status_banner(
        title: str,
        status: str,
        status_color: str,
        status_emoji: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Get HTML status banner section.

        Args:
            title: Main title text for the banner
            status: Status text (e.g., "Success", "Failed", "Running")
            status_color: Background color for the banner (e.g., "#10B981", "#EF4444")
            status_emoji: Status emoji (currently not displayed in output)
            timestamp: Optional timestamp. If None, uses current UTC time.

        Returns:
            str: HTML table row containing the status banner with colored background.

        """
        timestamp = timestamp or datetime.now(UTC)

        return f"""
        <tr>
            <td style="padding: 24px; background-color: {status_color}; text-align: center;">
                <h2 style="margin: 0; color: white; font-size: 22px; font-weight: 600; letter-spacing: 0.3px;">
                    {title}
                </h2>
                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.95); font-size: 14px; font-weight: 500;">
                    Status: {status} | {timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}
                </p>
            </td>
        </tr>
        """

    @staticmethod
    def get_footer() -> str:
        """Get HTML footer section with branding and disclaimers.

        Returns:
            str: HTML table row containing the footer with dark background,
                 application name, tagline, and legal disclaimer.

        """
        return f"""
        <tr>
            <td style="padding: 24px; background-color: #1F2937; border-radius: 0 0 12px 12px; text-align: center;">
                <p style="margin: 0; color: #9CA3AF; font-size: 13px; font-weight: 500;">
                    {APPLICATION_NAME} Quantitative Trading Platform
                </p>
                <p style="margin: 8px 0 0 0; color: #6B7280; font-size: 12px;">
                    Multi-Strategy Portfolio Management | Nuclear & Technology Enhanced Strategies
                </p>
                <p style="margin: 12px 0 0 0; color: #6B7280; font-size: 11px; font-style: italic;">
                    This report is for informational purposes only and does not constitute investment advice.
                </p>
            </td>
        </tr>
        """

    @staticmethod
    def wrap_content(content: str, title: str = APPLICATION_NAME) -> str:
        """Wrap content in base HTML email structure.

        Args:
            content: Inner HTML content to wrap (typically includes header, body, footer)
            title: Email title used in <title> tag and preview text.
                  Defaults to APPLICATION_NAME constant.

        Returns:
            str: Complete HTML document with DOCTYPE, head section (meta tags, styles),
                 and body containing the wrapped content in a responsive email layout.

        """
        return f"""
        <!DOCTYPE html>
        <html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
        <head>
            <meta charset="utf-8">
            <meta name="x-apple-disable-message-reformatting">
            <meta http-equiv="x-ua-compatible" content="ie=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
            <title>{title}</title>
            <!--[if mso]>
            <noscript>
                <xml>
                    <o:OfficeDocumentSettings>
                        <o:PixelsPerInch>96</o:PixelsPerInch>
                    </o:OfficeDocumentSettings>
                </xml>
            </noscript>
            <style>
                td,th,div,p,a,h1,h2,h3,h4,h5,h6 {{font-family: "Segoe UI", sans-serif; mso-line-height-rule: exactly;}}
            </style>
            <![endif]-->
            {BaseEmailTemplate.get_base_styles()}
        </head>
        <body style="margin: 0; width: 100%; padding: 0; word-break: break-word; -webkit-font-smoothing: antialiased; background-color: #F3F4F6;">
            <div style="display: none;">{title} - Quantitative Trading System Report</div>
            <div role="article" aria-roledescription="email" aria-label="{title}" lang="en">
                <table style="width: 100%; font-family: 'Segoe UI', ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif;" cellpadding="0" cellspacing="0" role="presentation">
                    <tr>
                        <td align="center" style="background-color: #F3F4F6; padding: 24px 0;">
                            <table class="sm-w-full" style="width: 600px;" cellpadding="0" cellspacing="0" role="presentation">
                                {content}
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def create_section(title: str, content: str, margin: str = "24px 0") -> str:
        """Create a content section with title.

        Args:
            title: Section title text
            content: HTML content for the section body
            margin: CSS margin value for the section. Defaults to "24px 0".

        Returns:
            str: HTML div containing the title (h3) and content with specified styling.

        """
        return f"""
        <div style="margin: {margin};">
            <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">{title}</h3>
            {content}
        </div>
        """

    @staticmethod
    def create_alert_box(content: str, alert_type: str = "info") -> str:
        """Create an alert/notification box.

        Args:
            content: Alert message content (HTML allowed)
            alert_type: Type of alert determining color scheme.
                       Valid values: "success", "error", "warning", "info" (default).
                       Invalid values fall back to "info" styling.

        Returns:
            str: HTML div with colored background, border, and padding styled
                 according to the alert type.

        """
        colors = {
            "success": {"bg": "#D1FAE5", "border": "#10B981", "text": "#065F46"},
            "error": {"bg": "#FEE2E2", "border": "#EF4444", "text": "#DC2626"},
            "warning": {"bg": "#FEF3C7", "border": "#F59E0B", "text": "#92400E"},
            "info": {"bg": "#DBEAFE", "border": "#3B82F6", "text": "#1E40AF"},
        }

        color_scheme = colors.get(alert_type, colors["info"])

        return f"""
        <div style="margin: 24px 0; padding: 16px; background-color: {color_scheme["bg"]}; border-left: 4px solid {color_scheme["border"]}; border-radius: 8px;">
            <p style="margin: 0; color: {color_scheme["text"]};">{content}</p>
        </div>
        """

    @staticmethod
    def create_table(headers: list[str], rows: list[list[str]], table_id: str = "") -> str:
        """Create a responsive table.

        Args:
            headers: List of header column names
            rows: List of rows, where each row is a list of cell values (strings)
            table_id: Optional HTML id attribute for the table element

        Returns:
            str: HTML table with styled header and body rows. Includes responsive
                 styling with borders, shadows, and alternating row colors.

        """
        header_html = "".join(
            [
                f"<th style='padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;'>{header}</th>"
                for header in headers
            ]
        )

        rows_html = ""
        for row in rows:
            row_html = "".join(
                [
                    f"<td style='padding: 8px 12px; border-bottom: 1px solid #E5E7EB;'>{cell}</td>"
                    for cell in row
                ]
            )
            rows_html += f"<tr>{row_html}</tr>"

        return f"""
        <table id="{table_id}" style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """
