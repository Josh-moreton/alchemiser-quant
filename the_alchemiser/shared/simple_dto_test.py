#!/usr/bin/env python3
"""Simple demonstration of DTO-based communication patterns."""

from datetime import UTC, datetime
from decimal import Decimal


# Test basic DTO functionality
def test_dto_creation():
    """Test basic DTO creation and serialization."""
    print("🧪 Testing DTO creation and serialization...")

    from the_alchemiser.shared.dto import StrategySignalDTO

    signal = StrategySignalDTO(
        correlation_id="test_signal_001",
        causation_id="test_signal_001",
        timestamp=datetime.now(UTC),
        symbol="AAPL",
        action="BUY",
        confidence=Decimal("0.85"),
        reasoning="Strong technical breakout",
        strategy_name="test_strategy",
        allocation_weight=Decimal("0.15"),
    )

    print(f"✅ Signal created: {signal.symbol} {signal.action}")
    print(f"   Confidence: {signal.confidence}")
    print(f"   Strategy: {signal.strategy_name}")

    # Test serialization
    signal_dict = signal.to_dict()
    print(f"✅ Serialized to dict: {len(signal_dict)} fields")

    # Test deserialization
    signal_restored = StrategySignalDTO.from_dict(signal_dict)
    print(f"✅ Restored from dict: {signal_restored.symbol}")

    return True


def test_adapter_functionality():
    """Test adapter functionality without complex imports."""
    print("\n🔄 Testing adapter functionality...")

    from the_alchemiser.shared.adapters.strategy_adapters import strategy_signal_to_dto

    # Mock signal object
    class MockSignal:
        def __init__(self):
            self.symbol = "GOOGL"
            self.action = "SELL"
            self.confidence = Decimal("0.70")
            self.reasoning = "Overbought conditions"
            self.timestamp = datetime.now(UTC)

    mock_signal = MockSignal()

    # Convert using adapter
    signal_dto = strategy_signal_to_dto(signal=mock_signal, strategy_name="test_adapter")

    print(f"✅ Adapter conversion: {signal_dto.symbol} {signal_dto.action}")
    print(f"   Original confidence: {mock_signal.confidence}")
    print(f"   DTO confidence: {signal_dto.confidence}")

    return True


def test_portfolio_dto():
    """Test portfolio DTO creation."""
    print("\n📊 Testing portfolio DTO...")

    from the_alchemiser.shared.dto import PortfolioMetricsDTO, PortfolioStateDTO

    metrics = PortfolioMetricsDTO(
        total_value=Decimal("100000"),
        cash_value=Decimal("20000"),
        equity_value=Decimal("80000"),
        buying_power=Decimal("25000"),
        day_pnl=Decimal("1500"),
        day_pnl_percent=Decimal("0.015"),
        total_pnl=Decimal("8000"),
        total_pnl_percent=Decimal("0.08"),
    )

    portfolio = PortfolioStateDTO(
        correlation_id="portfolio_test_001",
        causation_id="portfolio_test_001",
        timestamp=datetime.now(UTC),
        portfolio_id="test_portfolio",
        positions=[],
        metrics=metrics,
    )

    print(f"✅ Portfolio created: {portfolio.portfolio_id}")
    print(f"   Total value: ${portfolio.metrics.total_value:,}")
    print(f"   Day P&L: ${portfolio.metrics.day_pnl:,}")

    return True


def main():
    """Run all DTO tests."""
    print("🚀 Phase 3 DTO Functionality Test")
    print("=" * 40)

    try:
        test_dto_creation()
        test_adapter_functionality()
        test_portfolio_dto()

        print("\n🎉 All tests passed!")
        print("✅ DTOs created and serialized successfully")
        print("✅ Adapters convert objects to DTOs")
        print("✅ Portfolio DTOs work correctly")
        print("\n📝 Phase 3 implementation is working correctly!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
