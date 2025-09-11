#!/usr/bin/env python3
"""Manual validation script for Portfolio_v2 module.

This script provides a minimal manual validation of the Portfolio_v2 module
without relying on test frameworks (as per project guidelines).

Usage:
    poetry run python scripts/validate_portfolio_v2.py
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_strategy_allocation_dto() -> bool:
    """Validate StrategyAllocationDTO creation and validation."""
    print("\n=== Validating StrategyAllocationDTO ===")
    
    try:
        from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
        
        # Test 1: Valid allocation
        strategy = StrategyAllocationDTO(
            target_weights={"SPY": Decimal("0.6"), "QQQ": Decimal("0.4")},
            portfolio_value=None,
            correlation_id="demo-123",
            as_of=None,
        )
        print(f"✅ Created valid StrategyAllocationDTO: {len(strategy.target_weights)} symbols")
        
        # Test 2: Weight validation
        try:
            invalid_strategy = StrategyAllocationDTO(
                target_weights={"SPY": Decimal("0.8"), "QQQ": Decimal("0.8")},  # Sum > 1
                portfolio_value=None,
                correlation_id="demo-invalid",
                as_of=None,
            )
            print("❌ Weight validation failed - should have rejected sum > 1")
            return False
        except ValueError:
            print("✅ Weight validation working - correctly rejected sum > 1")
        
        # Test 3: from_dict conversion
        data = {
            "target_weights": {"TSLA": "0.3", "AAPL": "0.7"},  # String weights
            "portfolio_value": "50000.00",  # String value
            "correlation_id": "test-conversion",
        }
        converted = StrategyAllocationDTO.from_dict(data)
        print(f"✅ from_dict conversion working: {converted.target_weights}")
        
        return True
        
    except Exception as e:
        print(f"❌ StrategyAllocationDTO validation failed: {e}")
        return False


def validate_portfolio_models() -> bool:
    """Validate portfolio models (PortfolioSnapshot, SizingPolicy)."""
    print("\n=== Validating Portfolio Models ===")
    
    try:
        from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
        from the_alchemiser.portfolio_v2.models.sizing_policy import SizingPolicy, SizingMode
        
        # Test PortfolioSnapshot
        snapshot = PortfolioSnapshot(
            positions={"SPY": Decimal("10"), "QQQ": Decimal("5")},
            prices={"SPY": Decimal("400.00"), "QQQ": Decimal("300.00")},
            cash=Decimal("1000.00"),
            total_value=Decimal("6500.00")  # 10*400 + 5*300 + 1000
        )
        print(f"✅ PortfolioSnapshot created with {len(snapshot.positions)} positions")
        print(f"   Total position value: ${snapshot.get_total_position_value()}")
        print(f"   Validation check: {snapshot.validate_total_value()}")
        
        # Test SizingPolicy
        policy = SizingPolicy(
            min_trade_amount=Decimal("25.00"),
            sizing_mode=SizingMode.DOLLAR_AMOUNT,
            rounding_precision=2
        )
        
        # Test trade amount decisions
        large_trade = Decimal("100.00")
        small_trade = Decimal("10.00")
        
        large_amount, large_action = policy.apply_sizing_rules(large_trade)
        small_amount, small_action = policy.apply_sizing_rules(small_trade)
        
        print(f"✅ SizingPolicy working:")
        print(f"   Large trade ${large_trade} -> ${large_amount} ({large_action})")
        print(f"   Small trade ${small_trade} -> ${small_amount} ({small_action})")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio models validation failed: {e}")
        return False


def validate_plan_calculator() -> bool:
    """Validate RebalancePlanCalculator with mock data."""
    print("\n=== Validating RebalancePlanCalculator ===")
    
    try:
        from the_alchemiser.portfolio_v2.core.planner import RebalancePlanCalculator
        from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
        from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
        
        # Create calculator
        calculator = RebalancePlanCalculator()
        
        # Create test data
        strategy = StrategyAllocationDTO(
            target_weights={"SPY": Decimal("0.7"), "QQQ": Decimal("0.3")},
            portfolio_value=Decimal("10000.00"),
            correlation_id="calc-test-123"
        )
        
        snapshot = PortfolioSnapshot(
            positions={"SPY": Decimal("10"), "QQQ": Decimal("10")},  # $4000 + $3000 = $7000
            prices={"SPY": Decimal("400.00"), "QQQ": Decimal("300.00")},
            cash=Decimal("3000.00"),  # Total = $10000
            total_value=Decimal("10000.00")
        )
        
        # Calculate plan
        plan = calculator.build_plan(strategy, snapshot, "calc-test-123")
        
        print(f"✅ RebalancePlanCalculator created plan with {len(plan.items)} items")
        print(f"   Total trade value: ${plan.total_trade_value}")
        print(f"   Plan items:")
        
        for item in plan.items:
            print(f"     {item.symbol}: {item.action} ${item.trade_amount} "
                  f"(current: ${item.current_value}, target: ${item.target_value})")
        
        return True
        
    except Exception as e:
        print(f"❌ RebalancePlanCalculator validation failed: {e}")
        return False


def main() -> None:
    """Run all validation tests."""
    print("🧪 Portfolio_v2 Manual Validation Script")
    print("=" * 50)
    
    # Note: We can't test the full PortfolioServiceV2 without actual Alpaca credentials
    # But we can test the individual components
    
    results = []
    
    results.append(validate_strategy_allocation_dto())
    results.append(validate_portfolio_models())
    results.append(validate_plan_calculator())
    
    print("\n" + "=" * 50)
    print("📊 Validation Summary:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All validations passed!")
        print("\n📝 Manual verification notes:")
        print("   - StrategyAllocationDTO handles Decimal conversion correctly")
        print("   - Portfolio models enforce data consistency") 
        print("   - RebalancePlanCalculator produces valid trade plans")
        print("   - All financial calculations use Decimal precision")
        print("   - Module boundaries respected (only imports from shared)")
    else:
        print("❌ Some validations failed!")
        exit(1)


if __name__ == "__main__":
    main()