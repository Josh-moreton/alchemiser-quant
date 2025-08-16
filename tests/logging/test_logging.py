from __future__ import annotations

import json
import logging

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from the_alchemiser.logging import configure_logging, get_logger, context


def _setup() -> None:
    configure_logging(env="DEV", service="test", version="test", region="test")
    trace.set_tracer_provider(TracerProvider())


def test_info_log_shape(capsys: pytest.CaptureFixture[str]) -> None:
    _setup()
    logger = get_logger(__name__)
    logger.info("hello", extra={"event": "test.event", "symbol": "AAPL"})
    out = capsys.readouterr().err.strip().splitlines()[-1]
    rec = json.loads(out)
    assert rec["message"] == "hello"
    assert rec["event"] == "test.event"
    assert rec["symbol"] == "AAPL"
    assert rec["log.level"] == "INFO"
    assert "correlation_id" in rec or "trace.id" in rec


def test_exception_logging(capsys: pytest.CaptureFixture[str]) -> None:
    _setup()
    logger = get_logger(__name__)
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("err", extra={"event": "test.err"})
    out = capsys.readouterr().err.strip().splitlines()[-1]
    rec = json.loads(out)
    assert rec["error.kind"] == "ValueError"
    assert rec["error.message"] == "boom"
    assert "error.stack" in rec


def test_context_propagation(capsys: pytest.CaptureFixture[str]) -> None:
    _setup()
    logger = get_logger(__name__)
    with context(order_id="1", symbol="IBM"):
        logger.info("trade", extra={"event": "trade"})
    out = capsys.readouterr().err.strip().splitlines()[-1]
    rec = json.loads(out)
    assert rec["order_id"] == "1"
    assert rec["symbol"] == "IBM"


def test_redaction(capsys: pytest.CaptureFixture[str]) -> None:
    _setup()
    logger = get_logger(__name__)
    logger.info(
        "secret",
        extra={
            "event": "sec",
            "key": "AKIA1234567890ABCDE0",
            "email": "user@example.com",
        },
    )
    out = capsys.readouterr().err.strip().splitlines()[-1]
    rec = json.loads(out)
    assert rec["key"] == "***REDACTED***"
    assert rec["email"] == "***REDACTED***"


def test_otel_correlation(capsys: pytest.CaptureFixture[str]) -> None:
    _setup()
    tracer = trace.get_tracer(__name__)
    logger = get_logger(__name__)
    with tracer.start_as_current_span("span"):
        logger.info("otel", extra={"event": "otel"})
    out = capsys.readouterr().err.strip().splitlines()[-1]
    rec = json.loads(out)
    assert "trace.id" in rec and "span.id" in rec
