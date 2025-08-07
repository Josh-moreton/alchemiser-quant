"""
Unit tests for portfolio management and rebalancing logic.

Tests portfolio state management, rebalancing calculations, and position tracking
to ensure correct portfolio operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any


class TestPortfolioRebalancing:
    """Test portfolio rebalancing logic and calculations."""

    def test_equal_weight_rebalancing(self):
        """Test equal weight rebalancing across multiple assets."""
        portfolio_value = Decimal("100000.00")
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        # Equal allocation: 25% each
        target_allocations = {symbol: Decimal("0.25") for symbol in symbols}

        # Current unbalanced state
        current_positions = {
            "AAPL": {"market_value": Decimal("40000.00"), "shares": 200},
            "GOOGL": {"market_value": Decimal("20000.00"), "shares": 10},
            "MSFT": {"market_value": Decimal("30000.00"), "shares": 100},
            "TSLA": {"market_value": Decimal("10000.00"), "shares": 50},
        }

        # Calculate rebalancing needs
        rebalancing_needs = calculate_rebalancing_needs(
            portfolio_value, target_allocations, current_positions
        )

        # Each position should target $25,000
        expected_rebalancing = {
            "AAPL": Decimal("-15000.00"),  # Reduce from 40k to 25k
            "GOOGL": Decimal("5000.00"),  # Increase from 20k to 25k
            "MSFT": Decimal("-5000.00"),  # Reduce from 30k to 25k
            "TSLA": Decimal("15000.00"),  # Increase from 10k to 25k
        }

        for symbol, expected_change in expected_rebalancing.items():
            assert rebalancing_needs[symbol] == expected_change

        # Total rebalancing should sum to zero
        assert sum(rebalancing_needs.values()) == Decimal("0.00")

    def test_target_allocation_rebalancing(self):
        """Test rebalancing to specific target allocations."""
        portfolio_value = Decimal("200000.00")

        target_allocations = {
            "AAPL": Decimal("0.40"),  # 40%
            "GOOGL": Decimal("0.30"),  # 30%
            "MSFT": Decimal("0.20"),  # 20%
            "CASH": Decimal("0.10"),  # 10%
        }

        current_positions = {
            "AAPL": {"market_value": Decimal("60000.00")},
            "GOOGL": {"market_value": Decimal("80000.00")},
            "MSFT": {"market_value": Decimal("40000.00")},
        }
        current_cash = Decimal("20000.00")

        rebalancing_needs = calculate_rebalancing_needs_with_cash(
            portfolio_value, target_allocations, current_positions, current_cash
        )

        {
            "AAPL": Decimal("80000.00"),  # 40% of 200k
            "GOOGL": Decimal("60000.00"),  # 30% of 200k
            "MSFT": Decimal("40000.00"),  # 20% of 200k
            "CASH": Decimal("20000.00"),  # 10% of 200k
        }

        expected_changes = {
            "AAPL": Decimal("20000.00"),  # Need to buy 20k more
            "GOOGL": Decimal("-20000.00"),  # Need to sell 20k
            "MSFT": Decimal("0.00"),  # No change needed
            "CASH": Decimal("0.00"),  # No change needed
        }

        for symbol, expected_change in expected_changes.items():
            assert rebalancing_needs[symbol] == expected_change

    def test_rebalancing_with_minimum_trade_size(self):
        """Test rebalancing respects minimum trade sizes."""
        portfolio_value = Decimal("100000.00")
        min_trade_size = Decimal("1000.00")  # $1000 minimum trade

        target_allocations = {"AAPL": Decimal("0.50"), "GOOGL": Decimal("0.50")}

        # Small imbalance that's below minimum trade size
        current_positions = {
            "AAPL": {"market_value": Decimal("50500.00")},
            "GOOGL": {"market_value": Decimal("49500.00")},
        }

        rebalancing_needs = calculate_rebalancing_needs_with_minimum(
            portfolio_value, target_allocations, current_positions, min_trade_size
        )

        # Changes should be zero since they're below minimum trade size
        assert rebalancing_needs["AAPL"] == Decimal("0.00")
        assert rebalancing_needs["GOOGL"] == Decimal("0.00")

        # Test with larger imbalance
        current_positions_large = {
            "AAPL": {"market_value": Decimal("52000.00")},
            "GOOGL": {"market_value": Decimal("48000.00")},
        }

        rebalancing_needs_large = calculate_rebalancing_needs_with_minimum(
            portfolio_value, target_allocations, current_positions_large, min_trade_size
        )

        # Should rebalance since changes are above minimum
        assert abs(rebalancing_needs_large["AAPL"]) >= min_trade_size
        assert abs(rebalancing_needs_large["GOOGL"]) >= min_trade_size

    def test_drift_tolerance_rebalancing(self):
        """Test rebalancing with drift tolerance."""
        portfolio_value = Decimal("100000.00")
        drift_tolerance = Decimal("0.05")  # 5% drift tolerance

        target_allocations = {
            "AAPL": Decimal("0.50"),  # Target 50%
            "GOOGL": Decimal("0.50"),  # Target 50%
        }

        # Small drift within tolerance (3% drift)
        current_positions_small_drift = {
            "AAPL": {"market_value": Decimal("53000.00")},  # 53% vs 50% target
            "GOOGL": {"market_value": Decimal("47000.00")},  # 47% vs 50% target
        }

        rebalancing_needs = calculate_rebalancing_needs_with_drift_tolerance(
            portfolio_value, target_allocations, current_positions_small_drift, drift_tolerance
        )

        # Should not rebalance within tolerance
        assert rebalancing_needs["AAPL"] == Decimal("0.00")
        assert rebalancing_needs["GOOGL"] == Decimal("0.00")

        # Large drift outside tolerance (8% drift)
        current_positions_large_drift = {
            "AAPL": {"market_value": Decimal("58000.00")},  # 58% vs 50% target (8% drift)
            "GOOGL": {"market_value": Decimal("42000.00")},  # 42% vs 50% target (8% drift)
        }

        rebalancing_needs_large = calculate_rebalancing_needs_with_drift_tolerance(
            portfolio_value, target_allocations, current_positions_large_drift, drift_tolerance
        )

        # Should rebalance outside tolerance
        assert rebalancing_needs_large["AAPL"] < Decimal("0.00")  # Sell AAPL
        assert rebalancing_needs_large["GOOGL"] > Decimal("0.00")  # Buy GOOGL


class TestPortfolioState:
    """Test portfolio state management."""

    def test_portfolio_state_creation(self):
        """Test creating and updating portfolio state."""
        positions = {
            "AAPL": {
                "symbol": "AAPL",
                "shares": Decimal("100"),
                "avg_price": Decimal("150.00"),
                "current_price": Decimal("155.00"),
                "market_value": Decimal("15500.00"),
                "unrealized_pnl": Decimal("500.00"),
            }
        }

        portfolio_state = PortfolioState(
            total_value=Decimal("100000.00"),
            cash=Decimal("84500.00"),
            positions=positions,
            timestamp=datetime.now(),
        )

        assert portfolio_state.total_value == Decimal("100000.00")
        assert portfolio_state.cash == Decimal("84500.00")
        assert len(portfolio_state.positions) == 1

        # Verify position details
        aapl_position = portfolio_state.positions["AAPL"]
        assert aapl_position["shares"] == Decimal("100")
        assert aapl_position["market_value"] == Decimal("15500.00")

    def test_portfolio_state_validation(self):
        """Test portfolio state validation."""
        positions = {
            "AAPL": {"market_value": Decimal("50000.00")},
            "GOOGL": {"market_value": Decimal("30000.00")},
        }
        cash = Decimal("20000.00")
        total_value = Decimal("100000.00")

        # Portfolio should balance
        calculated_total = sum(pos["market_value"] for pos in positions.values()) + cash
        assert calculated_total == total_value

        # Test with imbalanced portfolio (should be detected)
        imbalanced_cash = Decimal("25000.00")  # Wrong cash amount
        calculated_imbalanced = (
            sum(pos["market_value"] for pos in positions.values()) + imbalanced_cash
        )
        assert calculated_imbalanced != total_value

    def test_position_updates(self):
        """Test updating positions in portfolio state."""
        initial_positions = {
            "AAPL": {
                "shares": Decimal("100"),
                "avg_price": Decimal("150.00"),
                "current_price": Decimal("150.00"),
                "market_value": Decimal("15000.00"),
            }
        }

        # Update price
        updated_price = Decimal("155.00")
        updated_positions = update_position_prices(initial_positions, {"AAPL": updated_price})

        assert updated_positions["AAPL"]["current_price"] == updated_price
        assert updated_positions["AAPL"]["market_value"] == Decimal("15500.00")

        # Calculate unrealized P&L
        unrealized_pnl = (
            updated_price - initial_positions["AAPL"]["avg_price"]
        ) * initial_positions["AAPL"]["shares"]
        assert unrealized_pnl == Decimal("500.00")


class TestAllocationCalculations:
    """Test allocation percentage calculations."""

    def test_current_allocations(self):
        """Test calculating current portfolio allocations."""
        portfolio_value = Decimal("100000.00")
        positions = {
            "AAPL": {"market_value": Decimal("40000.00")},
            "GOOGL": {"market_value": Decimal("30000.00")},
            "MSFT": {"market_value": Decimal("20000.00")},
        }
        cash = Decimal("10000.00")

        current_allocations = calculate_current_allocations(positions, cash, portfolio_value)

        expected_allocations = {
            "AAPL": Decimal("0.40"),  # 40%
            "GOOGL": Decimal("0.30"),  # 30%
            "MSFT": Decimal("0.20"),  # 20%
            "CASH": Decimal("0.10"),  # 10%
        }

        for symbol, expected_allocation in expected_allocations.items():
            assert current_allocations[symbol] == expected_allocation

        # Total should sum to 1.0
        assert sum(current_allocations.values()) == Decimal("1.00")

    def test_allocation_drift_calculation(self):
        """Test calculating allocation drift from targets."""
        target_allocations = {
            "AAPL": Decimal("0.50"),
            "GOOGL": Decimal("0.30"),
            "MSFT": Decimal("0.20"),
        }

        current_allocations = {
            "AAPL": Decimal("0.45"),  # 5% under
            "GOOGL": Decimal("0.35"),  # 5% over
            "MSFT": Decimal("0.20"),  # On target
        }

        drift = calculate_allocation_drift(target_allocations, current_allocations)

        expected_drift = {
            "AAPL": Decimal("-0.05"),  # 5% under target
            "GOOGL": Decimal("0.05"),  # 5% over target
            "MSFT": Decimal("0.00"),  # On target
        }

        for symbol, expected_drift_value in expected_drift.items():
            assert drift[symbol] == expected_drift_value

    def test_maximum_drift_detection(self):
        """Test detecting maximum drift in portfolio."""
        target_allocations = {
            "AAPL": Decimal("0.25"),
            "GOOGL": Decimal("0.25"),
            "MSFT": Decimal("0.25"),
            "TSLA": Decimal("0.25"),
        }

        current_allocations = {
            "AAPL": Decimal("0.35"),  # +10% drift
            "GOOGL": Decimal("0.20"),  # -5% drift
            "MSFT": Decimal("0.25"),  # 0% drift
            "TSLA": Decimal("0.20"),  # -5% drift
        }

        max_drift = calculate_maximum_drift(target_allocations, current_allocations)

        # Maximum absolute drift should be 10% (AAPL)
        assert max_drift == Decimal("0.10")


# Helper functions for portfolio calculations
def calculate_rebalancing_needs(
    portfolio_value: Decimal,
    target_allocations: dict[str, Decimal],
    current_positions: dict[str, dict[str, Decimal]],
) -> dict[str, Decimal]:
    """Calculate rebalancing needs for each position."""
    rebalancing_needs = {}

    for symbol, target_allocation in target_allocations.items():
        target_value = portfolio_value * target_allocation
        current_value = current_positions[symbol]["market_value"]
        rebalancing_needs[symbol] = target_value - current_value

    return rebalancing_needs


def calculate_rebalancing_needs_with_cash(
    portfolio_value: Decimal,
    target_allocations: dict[str, Decimal],
    current_positions: dict[str, dict[str, Decimal]],
    current_cash: Decimal,
) -> dict[str, Decimal]:
    """Calculate rebalancing needs including cash allocation."""
    rebalancing_needs = {}

    for symbol, target_allocation in target_allocations.items():
        target_value = portfolio_value * target_allocation

        if symbol == "CASH":
            current_value = current_cash
        else:
            current_value = current_positions[symbol]["market_value"]

        rebalancing_needs[symbol] = target_value - current_value

    return rebalancing_needs


def calculate_rebalancing_needs_with_minimum(
    portfolio_value: Decimal,
    target_allocations: dict[str, Decimal],
    current_positions: dict[str, dict[str, Decimal]],
    min_trade_size: Decimal,
) -> dict[str, Decimal]:
    """Calculate rebalancing needs with minimum trade size filter."""
    base_needs = calculate_rebalancing_needs(portfolio_value, target_allocations, current_positions)

    # Filter out trades below minimum size
    filtered_needs = {}
    for symbol, need in base_needs.items():
        if abs(need) >= min_trade_size:
            filtered_needs[symbol] = need
        else:
            filtered_needs[symbol] = Decimal("0.00")

    return filtered_needs


def calculate_rebalancing_needs_with_drift_tolerance(
    portfolio_value: Decimal,
    target_allocations: dict[str, Decimal],
    current_positions: dict[str, dict[str, Decimal]],
    drift_tolerance: Decimal,
) -> dict[str, Decimal]:
    """Calculate rebalancing needs with drift tolerance."""
    current_allocations = {}
    for symbol in target_allocations:
        current_value = current_positions[symbol]["market_value"]
        current_allocations[symbol] = current_value / portfolio_value

    rebalancing_needs = {}
    for symbol, target_allocation in target_allocations.items():
        current_allocation = current_allocations[symbol]
        drift = abs(current_allocation - target_allocation)

        if drift > drift_tolerance:
            target_value = portfolio_value * target_allocation
            current_value = current_positions[symbol]["market_value"]
            rebalancing_needs[symbol] = target_value - current_value
        else:
            rebalancing_needs[symbol] = Decimal("0.00")

    return rebalancing_needs


class PortfolioState:
    """Simple portfolio state class for testing."""

    def __init__(
        self, total_value: Decimal, cash: Decimal, positions: dict[str, Any], timestamp: datetime
    ):
        self.total_value = total_value
        self.cash = cash
        self.positions = positions
        self.timestamp = timestamp


def update_position_prices(
    positions: dict[str, dict[str, Decimal]], new_prices: dict[str, Decimal]
) -> dict[str, dict[str, Decimal]]:
    """Update position prices and recalculate market values."""
    updated_positions = {}

    for symbol, position in positions.items():
        updated_position = position.copy()
        if symbol in new_prices:
            updated_position["current_price"] = new_prices[symbol]
            updated_position["market_value"] = updated_position["shares"] * new_prices[symbol]
        updated_positions[symbol] = updated_position

    return updated_positions


def calculate_current_allocations(
    positions: dict[str, dict[str, Decimal]], cash: Decimal, portfolio_value: Decimal
) -> dict[str, Decimal]:
    """Calculate current portfolio allocations."""
    allocations = {}

    for symbol, position in positions.items():
        allocations[symbol] = position["market_value"] / portfolio_value

    allocations["CASH"] = cash / portfolio_value

    return allocations


def calculate_allocation_drift(
    target_allocations: dict[str, Decimal], current_allocations: dict[str, Decimal]
) -> dict[str, Decimal]:
    """Calculate drift from target allocations."""
    drift = {}

    for symbol in target_allocations:
        drift[symbol] = current_allocations[symbol] - target_allocations[symbol]

    return drift


def calculate_maximum_drift(
    target_allocations: dict[str, Decimal], current_allocations: dict[str, Decimal]
) -> Decimal:
    """Calculate maximum absolute drift."""
    drifts = calculate_allocation_drift(target_allocations, current_allocations)
    return max(abs(drift) for drift in drifts.values())
