from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from the_alchemiser.application.tracking import strategy_order_tracker as tracker_mod
from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.interfaces.schemas.tracking import StrategyOrderDTO


class _DummyS3Handler:
    """In-memory S3 stub for tracker tests."""

    def __init__(self) -> None:
        self.storage: dict[str, Any] = {}

    # Persistence API used by tracker
    def file_exists(self, path: str) -> bool:  # noqa: D401 - simple stub
        return path in self.storage

    def read_json(self, path: str) -> Any:  # noqa: D401 - simple stub
        return self.storage.get(path)

    def write_json(self, path: str, data: Any) -> bool:  # noqa: D401 - simple stub
        self.storage[path] = data
        return True


@pytest.fixture(autouse=True)
def patch_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch get_s3_handler to return in-memory stub for all tests in module."""

    def _get_stub() -> _DummyS3Handler:
        return _DummyS3Handler()

    monkeypatch.setattr(tracker_mod, "get_s3_handler", _get_stub)


def _make_tracker() -> tracker_mod.StrategyOrderTracker:
    return tracker_mod.StrategyOrderTracker(paper_trading=True)


def test_add_order_dto_round_trip() -> None:
    tracker = _make_tracker()

    order = StrategyOrderDTO(
        order_id="order_1",
        strategy=StrategyType.NUCLEAR.value,  # type: ignore[arg-type]
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        price=Decimal("150.25"),
        timestamp=datetime.now(UTC),
    )

    tracker.add_order(order)

    # Retrieve via DTO accessor
    orders = tracker.get_orders_for_strategy(StrategyType.NUCLEAR.value)
    assert len(orders) == 1
    o = orders[0]
    assert o.order_id == "order_1"
    assert o.symbol == "AAPL"
    # Use approx for numeric comparisons (policy: no direct float equality)
    assert float(o.quantity) == pytest.approx(10.0)
    assert float(o.price) == pytest.approx(150.25)


def test_get_pnl_summary_internal_failure_zeroed(monkeypatch: pytest.MonkeyPatch) -> None:
    tracker = _make_tracker()

    def _boom(*_args: Any, **_kwargs: Any) -> Any:  # noqa: D401 - test stub
        raise RuntimeError("forced error")

    monkeypatch.setattr(tracker, "get_strategy_pnl", _boom)

    pnl = tracker.get_pnl_summary(StrategyType.NUCLEAR.value)
    assert pnl.total_pnl == Decimal("0")
    assert pnl.realized_pnl == Decimal("0")
    assert pnl.unrealized_pnl == Decimal("0")


def test_get_pnl_summary_invalid_strategy_raises() -> None:
    tracker = _make_tracker()
    with pytest.raises(ValueError):
        tracker.get_pnl_summary("NOT_A_STRATEGY")
