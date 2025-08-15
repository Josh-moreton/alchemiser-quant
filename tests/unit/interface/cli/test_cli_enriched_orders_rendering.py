import re

from rich.console import Console

from the_alchemiser.interface.cli.cli_formatter import render_enriched_order_summaries


def test_render_enriched_order_summaries_basic():
    console = Console(record=True)
    enriched = [
        {
            "summary": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "AAPL",
                "qty": 10.0,
                "status": "new",
                "type": "limit",
                "limit_price": 195.5,
                "created_at": "2025-08-15T12:34:56Z",
            }
        }
    ]

    render_enriched_order_summaries(enriched, console)
    output = console.export_text()

    # Basic assertions that table content is present
    assert "Open Orders (Enriched)" in output
    assert "AAPL" in output
    assert re.search(r"195\.50|195\.5", output)


def test_render_enriched_order_summaries_handles_empty():
    console = Console(record=True)
    render_enriched_order_summaries([], console)
    output = console.export_text()
    assert "No open orders" in output


def test_render_enriched_order_summaries_tolerates_raw_dicts():
    console = Console(record=True)
    # Already-summary-like dicts without 'summary' wrapper
    items = [
        {
            "id": "abc",
            "symbol": "MSFT",
            "qty": 5,
            "status": "filled",
            "type": "market",
            "limit_price": None,
            "created_at": "2025-08-15T00:00:00Z",
        }
    ]

    render_enriched_order_summaries(items, console)
    output = console.export_text()
    assert "MSFT" in output
    assert "FILLED" in output
