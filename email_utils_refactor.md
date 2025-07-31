# Refactoring Plan for `the_alchemiser/core/ui/email_utils.py`

The current `email_utils.py` file mixes configuration loading, SMTP operations, and large HTML string creation. Splitting it into smaller modules will make it far easier to maintain.

## Key Problems

- Configuration, SMTP handling, and extensive HTML generation are intertwined in a single 1000-line module.
- Dozens of helper functions build HTML fragments directly within the Python code.

## Proposed Modules

1. **`email/client.py`** – `EmailClient` class to manage SMTP configuration, login, and message sending.
2. **`email/config.py`** – Load email settings and secrets (replaces `get_email_config`).
3. **`email/templates/`** – Use a template engine (e.g., Jinja2) for HTML content.
4. **Content builders**
   - `portfolio.py` for portfolio tables.
   - `performance.py` for trading summaries and metrics.
   - `signals.py` for technical indicator sections.

## Additional Improvements

- Provide plain-text fallbacks and attachment support within `EmailClient`.
- Unit test each template-rendering function with representative data.
- Add type hints for configuration and template parameters.
