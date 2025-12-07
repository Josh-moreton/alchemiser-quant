"""Tests for Symbol JSON serialization in structlog JSONRenderer default."""

from __future__ import annotations

import json
import logging
from io import StringIO
from unittest.mock import patch

from the_alchemiser.shared.logging.structlog_config import (
    configure_structlog,
    get_structlog_logger,
)
from the_alchemiser.shared.value_objects.symbol import Symbol


def test_structlog_serializes_symbol_value_object() -> None:
    """Ensure Symbol instances in logs are rendered as simple strings."""
    with patch("sys.stdout", new=StringIO()) as fake_out:
        configure_structlog(
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
            use_json=True,
            use_colors=False,
        )
        logger = get_structlog_logger(__name__)

        sym = Symbol("TQQQ")
        # Log with Symbol inside a list to mirror real payloads from DSL engine
        logger.info("symbol list", symbols=[sym])

        output = fake_out.getvalue()
        data = json.loads(output)

        assert data["event"] == "symbol list"
        assert data["symbols"] == ["TQQQ"]
