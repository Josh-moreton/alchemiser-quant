"""Business Unit: shared | Status: current.

Tests for market data Protocol conformance.

Validates that the ModelDumpable and BarsIterable protocols are correctly
defined and that implementations conform to them properly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from the_alchemiser.shared.protocols.market_data import BarsIterable, ModelDumpable

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class MockModelDumpable:
    """Mock implementation that conforms to ModelDumpable protocol."""

    def __init__(self, data: dict[str, object]) -> None:
        """Initialize with test data."""
        self._data = data

    def model_dump(self) -> dict[str, object]:
        """Return dict representation."""
        return self._data.copy()


class MockBar(MockModelDumpable):
    """Mock bar model for testing."""

    def __init__(self, symbol: str, open_price: float, close_price: float) -> None:
        """Initialize mock bar."""
        super().__init__(
            {
                "symbol": symbol,
                "open": open_price,
                "close": close_price,
                "high": max(open_price, close_price),
                "low": min(open_price, close_price),
                "volume": 1000,
            }
        )


class MockBarsIterable:
    """Mock implementation that conforms to BarsIterable protocol."""

    def __init__(self, bars: Sequence[MockModelDumpable]) -> None:
        """Initialize with bars."""
        self._bars = list(bars)

    def __iter__(self) -> Iterator[MockModelDumpable]:
        """Iterate over bars."""
        return iter(self._bars)


class NonConformingModel:
    """Test implementation that doesn't conform to ModelDumpable (missing method)."""

    def to_dict(self) -> dict[str, object]:
        """Wrong method name."""
        return {}


def test_modeldumpable_protocol_conformance() -> None:
    """Test that conforming implementation is recognized by ModelDumpable protocol."""
    model = MockModelDumpable({"key": "value"})
    assert isinstance(model, ModelDumpable)


def test_modeldumpable_protocol_rejection() -> None:
    """Test that non-conforming implementation is rejected by ModelDumpable protocol."""
    model = NonConformingModel()
    assert not isinstance(model, ModelDumpable)


def test_modeldumpable_model_dump_returns_dict() -> None:
    """Test that model_dump returns a dictionary."""
    test_data = {"symbol": "AAPL", "price": 150.0}
    model = MockModelDumpable(test_data)

    result = model.model_dump()

    assert isinstance(result, dict)
    assert result == test_data
    # Verify it returns a copy, not the original
    assert result is not model._data


def test_barsiterable_protocol_conformance() -> None:
    """Test that conforming implementation is recognized by BarsIterable protocol."""
    bars = [MockBar("AAPL", 150.0, 151.0), MockBar("MSFT", 300.0, 301.0)]
    bars_iterable = MockBarsIterable(bars)

    assert isinstance(bars_iterable, BarsIterable)


def test_barsiterable_iteration() -> None:
    """Test that BarsIterable can be iterated over."""
    bars = [MockBar("AAPL", 150.0, 151.0), MockBar("MSFT", 300.0, 301.0)]
    bars_iterable = MockBarsIterable(bars)

    # Should be iterable
    result = list(bars_iterable)

    assert len(result) == 2
    assert all(isinstance(bar, MockModelDumpable) for bar in result)


def test_barsiterable_elements_are_modeldumpable() -> None:
    """Test that BarsIterable elements conform to ModelDumpable."""
    bars = [MockBar("AAPL", 150.0, 151.0), MockBar("MSFT", 300.0, 301.0)]
    bars_iterable = MockBarsIterable(bars)

    for bar in bars_iterable:
        # Each element should be ModelDumpable
        assert isinstance(bar, ModelDumpable)
        # Should have model_dump method
        data = bar.model_dump()
        assert isinstance(data, dict)
        assert "symbol" in data


def test_barsiterable_empty_collection() -> None:
    """Test that BarsIterable works with empty collections."""
    bars_iterable = MockBarsIterable([])

    assert isinstance(bars_iterable, BarsIterable)
    result = list(bars_iterable)
    assert len(result) == 0


def test_modeldumpable_with_various_data_types() -> None:
    """Test ModelDumpable with different data types in dict."""
    test_data = {
        "string": "value",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }
    model = MockModelDumpable(test_data)

    result = model.model_dump()

    assert result == test_data
    assert isinstance(result["string"], str)
    assert isinstance(result["int"], int)
    assert isinstance(result["float"], float)


def test_protocol_with_alpaca_like_structure() -> None:
    """Test that mock resembling Alpaca SDK structure conforms."""

    class AlpacaLikeBar:
        """Mock resembling Alpaca SDK Bar structure."""

        def __init__(self) -> None:
            """Initialize with typical bar data."""
            self.symbol = "AAPL"
            self.open = 150.0
            self.high = 151.5
            self.low = 149.5
            self.close = 151.0
            self.volume = 1_000_000

        def model_dump(self) -> dict[str, object]:
            """Serialize to dict (Pydantic-style)."""
            return {
                "symbol": self.symbol,
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            }

    bar = AlpacaLikeBar()
    assert isinstance(bar, ModelDumpable)

    data = bar.model_dump()
    assert data["symbol"] == "AAPL"
    assert data["open"] == 150.0


@pytest.mark.parametrize(
    ("bar_count", "expected_len"),
    [
        (1, 1),
        (10, 10),
        (100, 100),
    ],
)
def test_barsiterable_with_various_sizes(bar_count: int, expected_len: int) -> None:
    """Test BarsIterable with various collection sizes."""
    bars = [MockBar(f"SYM{i}", 100.0 + i, 101.0 + i) for i in range(bar_count)]
    bars_iterable = MockBarsIterable(bars)

    result = list(bars_iterable)
    assert len(result) == expected_len


def test_runtime_checkable_behavior() -> None:
    """Test that @runtime_checkable allows isinstance() checks."""
    # This is the key feature of runtime_checkable protocols

    class DuckTypedBar:
        """Class that happens to have model_dump without inheriting."""

        def model_dump(self) -> dict[str, object]:
            """Duck-typed method."""
            return {"duck": "typed"}

    duck_bar = DuckTypedBar()

    # Should pass isinstance check due to structural typing
    assert isinstance(duck_bar, ModelDumpable)

    # And the method should work
    result = duck_bar.model_dump()
    assert result == {"duck": "typed"}
