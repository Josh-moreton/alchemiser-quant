"""Business Unit: shared | Status: current.

Tests for strategy tracking protocol conformance.

Validates that the strategy tracking protocols are correctly defined and that
implementations can conform to them properly. Tests verify type safety,
Decimal usage for money, and timezone awareness.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from the_alchemiser.shared.protocols.strategy_tracking import (
    StrategyOrderProtocol,
    StrategyOrderTrackerProtocol,
    StrategyPnLSummaryProtocol,
    StrategyPositionProtocol,
)


# Mock implementations for testing protocol conformance


class MockStrategyPosition:
    """Mock implementation that conforms to StrategyPositionProtocol."""

    def __init__(
        self,
        strategy: str,
        symbol: str,
        quantity: Decimal,
        average_cost: Decimal,
    ) -> None:
        """Initialize mock position."""
        self._strategy = strategy
        self._symbol = symbol
        self._quantity = quantity
        self._average_cost = average_cost
        self._total_cost = quantity * average_cost
        self._last_updated = datetime.now(timezone.utc)

    @property
    def strategy(self) -> str:
        """Strategy name."""
        return self._strategy

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        return self._symbol

    @property
    def quantity(self) -> Decimal:
        """Position quantity."""
        return self._quantity

    @property
    def average_cost(self) -> Decimal:
        """Average entry cost."""
        return self._average_cost

    @property
    def total_cost(self) -> Decimal:
        """Total cost basis."""
        return self._total_cost

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp."""
        return self._last_updated


class MockStrategyPnLSummary:
    """Mock implementation that conforms to StrategyPnLSummaryProtocol."""

    def __init__(
        self,
        realized: Decimal,
        unrealized: Decimal,
        basis: Decimal,
        total_orders: int = 10,
        successful_orders: int = 8,
    ) -> None:
        """Initialize mock P&L summary."""
        self._realized_pnl = realized
        self._unrealized_pnl = unrealized
        self._cost_basis = basis
        self._total_orders = total_orders
        self._successful_orders = successful_orders
        self._position_count = 5
        self._last_updated = datetime.now(timezone.utc)

    @property
    def total_pnl(self) -> Decimal:
        """Total profit and loss."""
        return self._realized_pnl + self._unrealized_pnl

    @property
    def total_profit_loss(self) -> Decimal:
        """Total profit and loss (alias for total_pnl)."""
        return self.total_pnl

    @property
    def total_orders(self) -> int:
        """Total number of orders."""
        return self._total_orders

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self._total_orders == 0:
            return 0.0
        return self._successful_orders / self._total_orders * 100.0

    @property
    def avg_profit_per_trade(self) -> Decimal:
        """Average profit per trade."""
        if self._total_orders == 0:
            return Decimal("0")
        return self.total_pnl / Decimal(str(self._total_orders))

    @property
    def total_return_pct(self) -> float:
        """Total return percentage."""
        if self._cost_basis == 0:
            return 0.0
        return float(self.total_pnl / self._cost_basis * 100)

    @property
    def position_count(self) -> int:
        """Number of positions."""
        return self._position_count

    @property
    def realized_pnl(self) -> Decimal:
        """Realized profit and loss."""
        return self._realized_pnl

    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit and loss."""
        return self._unrealized_pnl

    @property
    def cost_basis(self) -> Decimal:
        """Cost basis for return calculation."""
        return self._cost_basis

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp."""
        return self._last_updated


class MockStrategyOrder:
    """Mock implementation that conforms to StrategyOrderProtocol."""

    def __init__(self, order_id: str, strategy: str, symbol: str) -> None:
        """Initialize mock order."""
        self._order_id = order_id
        self._strategy = strategy
        self._symbol = symbol

    @property
    def order_id(self) -> str:
        """Unique order identifier."""
        return self._order_id

    @property
    def strategy(self) -> str:
        """Strategy name."""
        return self._strategy

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        return self._symbol


class MockStrategyOrderTracker:
    """Mock implementation that conforms to StrategyOrderTrackerProtocol."""

    def __init__(self) -> None:
        """Initialize mock tracker."""
        self._positions: dict[str, list[StrategyPositionProtocol]] = {}
        self._summaries: dict[str, StrategyPnLSummaryProtocol] = {}
        self._orders: dict[str, list[StrategyOrderProtocol]] = {}

    def add_position(self, position: StrategyPositionProtocol) -> None:
        """Add a position for testing."""
        if position.strategy not in self._positions:
            self._positions[position.strategy] = []
        self._positions[position.strategy].append(position)

    def add_summary(self, strategy: str, summary: StrategyPnLSummaryProtocol) -> None:
        """Add a summary for testing."""
        self._summaries[strategy] = summary

    def add_order(self, order: StrategyOrderProtocol) -> None:
        """Add an order for testing."""
        if order.strategy not in self._orders:
            self._orders[order.strategy] = []
        self._orders[order.strategy].append(order)

    def get_positions_summary(self) -> list[StrategyPositionProtocol]:
        """Get positions summary."""
        return [pos for positions in self._positions.values() for pos in positions]

    def get_pnl_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol:
        """Get PnL summary for strategy."""
        if strategy_name not in self._summaries:
            raise KeyError(f"Strategy {strategy_name} not found")
        return self._summaries[strategy_name]

    def get_orders_for_strategy(self, strategy_name: str) -> list[StrategyOrderProtocol]:
        """Get orders for strategy."""
        return self._orders.get(strategy_name, [])

    def get_strategy_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol | None:
        """Get strategy summary for strategy."""
        return self._summaries.get(strategy_name)


# Protocol conformance tests


def test_strategy_position_protocol_conformance() -> None:
    """Test that MockStrategyPosition conforms to StrategyPositionProtocol."""
    position = MockStrategyPosition(
        strategy="NUCLEAR",
        symbol="SPY",
        quantity=Decimal("10.0"),
        average_cost=Decimal("450.50"),
    )
    assert isinstance(position, StrategyPositionProtocol)


def test_strategy_position_uses_decimal() -> None:
    """Test that position uses Decimal for monetary values."""
    position = MockStrategyPosition(
        strategy="NUCLEAR",
        symbol="SPY",
        quantity=Decimal("10.0"),
        average_cost=Decimal("450.50"),
    )
    
    # Verify types are Decimal, not float
    assert isinstance(position.quantity, Decimal)
    assert isinstance(position.average_cost, Decimal)
    assert isinstance(position.total_cost, Decimal)
    
    # Verify calculations maintain precision
    assert position.total_cost == Decimal("4505.00")


def test_strategy_position_timezone_aware() -> None:
    """Test that position uses timezone-aware datetime."""
    position = MockStrategyPosition(
        strategy="NUCLEAR",
        symbol="SPY",
        quantity=Decimal("10.0"),
        average_cost=Decimal("450.50"),
    )
    
    assert position.last_updated.tzinfo is not None
    assert position.last_updated.tzinfo == timezone.utc


def test_strategy_pnl_summary_protocol_conformance() -> None:
    """Test that MockStrategyPnLSummary conforms to StrategyPnLSummaryProtocol."""
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000.50"),
        unrealized=Decimal("500.25"),
        basis=Decimal("10000.00"),
    )
    assert isinstance(summary, StrategyPnLSummaryProtocol)


def test_strategy_pnl_summary_uses_decimal() -> None:
    """Test that P&L summary uses Decimal for monetary values."""
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000.50"),
        unrealized=Decimal("500.25"),
        basis=Decimal("10000.00"),
    )
    
    # Verify money fields are Decimal
    assert isinstance(summary.total_pnl, Decimal)
    assert isinstance(summary.total_profit_loss, Decimal)
    assert isinstance(summary.realized_pnl, Decimal)
    assert isinstance(summary.unrealized_pnl, Decimal)
    assert isinstance(summary.cost_basis, Decimal)
    assert isinstance(summary.avg_profit_per_trade, Decimal)
    
    # Verify percentages are float (not Decimal)
    assert isinstance(summary.success_rate, float)
    assert isinstance(summary.total_return_pct, float)


def test_strategy_pnl_summary_alias_consistency() -> None:
    """Test that total_pnl and total_profit_loss return same value."""
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000.50"),
        unrealized=Decimal("500.25"),
        basis=Decimal("10000.00"),
    )
    
    assert summary.total_pnl == summary.total_profit_loss
    assert summary.total_pnl == Decimal("1500.75")


def test_strategy_pnl_summary_edge_cases() -> None:
    """Test P&L summary edge cases (zero trades, zero cost basis)."""
    # Zero trades
    summary_no_trades = MockStrategyPnLSummary(
        realized=Decimal("0"),
        unrealized=Decimal("0"),
        basis=Decimal("10000.00"),
        total_orders=0,
        successful_orders=0,
    )
    assert summary_no_trades.success_rate == 0.0
    assert summary_no_trades.avg_profit_per_trade == Decimal("0")
    
    # Zero cost basis
    summary_no_basis = MockStrategyPnLSummary(
        realized=Decimal("100.00"),
        unrealized=Decimal("50.00"),
        basis=Decimal("0"),
    )
    assert summary_no_basis.total_return_pct == 0.0


def test_strategy_pnl_summary_percentage_ranges() -> None:
    """Test that percentages are in expected ranges."""
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000.00"),
        unrealized=Decimal("500.00"),
        basis=Decimal("10000.00"),
        total_orders=10,
        successful_orders=8,
    )
    
    # success_rate should be in [0.0, 100.0]
    assert 0.0 <= summary.success_rate <= 100.0
    assert summary.success_rate == 80.0
    
    # total_return_pct can be negative or positive
    assert summary.total_return_pct == 15.0  # 1500/10000 * 100


def test_strategy_order_protocol_conformance() -> None:
    """Test that MockStrategyOrder conforms to StrategyOrderProtocol."""
    order = MockStrategyOrder(
        order_id="ORDER123",
        strategy="NUCLEAR",
        symbol="SPY",
    )
    assert isinstance(order, StrategyOrderProtocol)


def test_strategy_order_tracker_protocol_conformance() -> None:
    """Test that MockStrategyOrderTracker conforms to StrategyOrderTrackerProtocol."""
    tracker = MockStrategyOrderTracker()
    assert isinstance(tracker, StrategyOrderTrackerProtocol)


def test_strategy_order_tracker_positions_summary() -> None:
    """Test get_positions_summary returns all positions."""
    tracker = MockStrategyOrderTracker()
    
    pos1 = MockStrategyPosition("NUCLEAR", "SPY", Decimal("10"), Decimal("450"))
    pos2 = MockStrategyPosition("TECL", "QQQ", Decimal("5"), Decimal("350"))
    
    tracker.add_position(pos1)
    tracker.add_position(pos2)
    
    positions = tracker.get_positions_summary()
    assert len(positions) == 2
    assert all(isinstance(p, StrategyPositionProtocol) for p in positions)


def test_strategy_order_tracker_pnl_summary_found() -> None:
    """Test get_pnl_summary returns summary when strategy exists."""
    tracker = MockStrategyOrderTracker()
    
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000"),
        unrealized=Decimal("500"),
        basis=Decimal("10000"),
    )
    tracker.add_summary("NUCLEAR", summary)
    
    result = tracker.get_pnl_summary("NUCLEAR")
    assert isinstance(result, StrategyPnLSummaryProtocol)
    assert result.total_pnl == Decimal("1500")


def test_strategy_order_tracker_pnl_summary_not_found() -> None:
    """Test get_pnl_summary raises KeyError when strategy not found."""
    tracker = MockStrategyOrderTracker()
    
    try:
        tracker.get_pnl_summary("UNKNOWN")
        assert False, "Expected KeyError to be raised"
    except KeyError as e:
        assert "UNKNOWN not found" in str(e)


def test_strategy_order_tracker_orders_for_strategy() -> None:
    """Test get_orders_for_strategy returns orders for strategy."""
    tracker = MockStrategyOrderTracker()
    
    order1 = MockStrategyOrder("ORDER1", "NUCLEAR", "SPY")
    order2 = MockStrategyOrder("ORDER2", "NUCLEAR", "QQQ")
    order3 = MockStrategyOrder("ORDER3", "TECL", "AAPL")
    
    tracker.add_order(order1)
    tracker.add_order(order2)
    tracker.add_order(order3)
    
    nuclear_orders = tracker.get_orders_for_strategy("NUCLEAR")
    assert len(nuclear_orders) == 2
    assert all(o.strategy == "NUCLEAR" for o in nuclear_orders)
    
    # Unknown strategy returns empty list (graceful handling)
    unknown_orders = tracker.get_orders_for_strategy("UNKNOWN")
    assert unknown_orders == []


def test_strategy_order_tracker_optional_summary() -> None:
    """Test get_strategy_summary returns None for missing strategy."""
    tracker = MockStrategyOrderTracker()
    
    summary = MockStrategyPnLSummary(
        realized=Decimal("1000"),
        unrealized=Decimal("500"),
        basis=Decimal("10000"),
    )
    tracker.add_summary("NUCLEAR", summary)
    
    # Found strategy
    result = tracker.get_strategy_summary("NUCLEAR")
    assert result is not None
    assert isinstance(result, StrategyPnLSummaryProtocol)
    
    # Unknown strategy returns None
    result_none = tracker.get_strategy_summary("UNKNOWN")
    assert result_none is None


def test_non_conforming_position_rejected() -> None:
    """Test that non-conforming implementations are rejected."""
    
    class NonConformingPosition:
        """Missing required properties."""
        
        @property
        def strategy(self) -> str:
            return "NUCLEAR"
        
        # Missing other required properties
    
    position = NonConformingPosition()
    assert not isinstance(position, StrategyPositionProtocol)


def test_decimal_precision_maintained() -> None:
    """Test that Decimal precision is maintained in calculations."""
    position = MockStrategyPosition(
        strategy="NUCLEAR",
        symbol="SPY",
        quantity=Decimal("10.123456789"),
        average_cost=Decimal("450.987654321"),
    )
    
    # High precision multiplication
    expected_total = Decimal("10.123456789") * Decimal("450.987654321")
    assert position.total_cost == expected_total
    
    # Verify no float conversion has occurred
    assert str(position.total_cost).count(".") == 1  # Still a decimal, not scientific notation
