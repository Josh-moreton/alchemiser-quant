# Refactor Plan for `email_utils.py`

## Current Issues
- ~587 lines implementing email sending, HTML template generation and configuration lookup.
- Large monolithic functions produce huge HTML strings inline.
- Configuration and secrets retrieval mixed with email composition logic.
- Several near-duplicate HTML sections for different email types.

## Goals
- Isolate email configuration and sending from template construction.
- Use templating engine for HTML generation to reduce inline string noise.
- Make functions reusable for other notification types.

## Proposed Modules & Files
- `notifications/email_config.py` – helper to load SMTP settings and secrets.
- `notifications/templates/` – folder with Jinja2 templates for trading report, multi-strategy report and error emails.
- `notifications/email_sender.py` – thin wrapper around `smtplib` to send prepared messages.
- `notifications/renderers.py` – functions that render HTML using templates.

## Step-by-Step Refactor
1. **Introduce Jinja2 Templates**
   - Add Jinja2 as a dependency.
   - Create template files: `trading_report.html`, `multi_strategy.html`, `error_email.html` under `notifications/templates/`.
   - Templates include placeholders for account info, orders, portfolio state etc.

2. **Create `email_config.py`**
   - Encapsulate logic currently in `get_email_config`.
   - Provide a single function `load_email_settings()` returning SMTP server, port, sender and credentials.

3. **Create `email_sender.py`**
   - Implement `send_email(to_address, subject, html_body, attachments=None)`.
   - Handles connection, login and sending; uses `email_config` to fetch settings.

4. **Create `renderers.py`**
   - Implement `render_trading_report(data: dict) -> str`, `render_multi_strategy_report(data: dict) -> str`, and `render_error_email(data: dict) -> str`.
   - Move calculation of P&L and formatting of tables into small helper functions.

5. **Rewrite Public API of `email_utils.py`**
   - Keep simple functions `send_trading_report`, `send_multi_strategy_report`, `send_error_report` that compose data and call `email_sender.send_email` with rendered HTML.
   - Remove giant string-building functions from this file; delegate to templates.

6. **Unit Tests**
   - Add tests in `tests/notifications/test_renderers.py` to verify template output for sample data.
   - Mock SMTP in `tests/notifications/test_email_sender.py`.

## Rationale
- Templating separates presentation from logic and reduces duplication.
- Smaller focused modules make it easier to maintain and extend notifications.
- Reusable `email_sender` can later support other channels (SMS, Slack) by following similar interface.

