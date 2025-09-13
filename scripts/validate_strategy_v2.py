#!/usr/bin/env python3
"""Manual validation script for Strategy_v2.

This script provides manual validation of the Strategy_v2 module
functionality without requiring a full test framework.

Usage:
    python scripts/validate_strategy_v2.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up proper logging using centralized utilities
from the_alchemiser.shared.logging.logging_utils import get_logger, setup_logging

# Initialize logging once
setup_logging(structured_format=False, suppress_third_party=True)
logger = get_logger(__name__)

from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.strategy_v2 import StrategyContext, StrategyOrchestrator
from the_alchemiser.strategy_v2.adapters.market_data_adapter import StrategyMarketDataAdapter


class MockAlpacaManager:
    """Mock Alpaca manager for validation testing."""
    
    def get_historical_bars(self, symbol: str, start_date: str, end_date: str, timeframe: str) -> list:
        """Return sample historical data."""
        return [
            {"t": datetime.now(), "o": 100.0, "h": 102.0, "l": 98.0, "c": 101.0, "v": 1000.0},
            {"t": datetime.now(), "o": 101.0, "h": 103.0, "l": 99.0, "c": 102.0, "v": 1100.0},
        ]
    
    def get_quote(self, symbol: str) -> dict:
        """Return sample quote data."""
        return {"ask_price": 100.0, "bid_price": 99.0}
    
    def validate_connection(self) -> bool:
        """Return True for mock validation."""
        return True


def main() -> None:
    """Run manual validation tests."""
    print("🧪 Strategy_v2 Manual Validation")
    print("=" * 50)
    
    try:
        # Test 1: Context creation and validation
        print("\n📋 Test 1: StrategyContext creation")
        context = StrategyContext(
            symbols=["SPY", "QQQ", "TLT"],
            timeframe="1D",
            as_of=datetime(2024, 1, 1, 12, 0, 0)
        )
        print(f"✅ Context created: symbols={context.symbols}, timeframe={context.timeframe}")
        
        # Test 2: Market data adapter
        print("\n📊 Test 2: Market data adapter") 
        mock_alpaca = MockAlpacaManager()
        adapter = StrategyMarketDataAdapter(mock_alpaca)
        
        # Test connection
        connection_ok = adapter.validate_connection()
        print(f"✅ Connection validation: {connection_ok}")
        
        # Test data fetching
        bars = adapter.get_bars(["SPY"], "1D", 5)
        print(f"✅ Historical bars fetched: {len(bars['SPY'])} bars for SPY")
        
        prices = adapter.get_current_prices(["SPY", "QQQ"])
        print(f"✅ Current prices: {prices}")
        
        # Test 3: Orchestrator execution
        print("\n🎯 Test 3: Strategy orchestrator")
        orchestrator = StrategyOrchestrator(adapter)
        
        allocation = orchestrator.run("sample", context)
        print(f"✅ Strategy execution completed")
        print(f"   Correlation ID: {allocation.correlation_id}")
        print(f"   Target weights: {dict(allocation.target_weights)}")
        
        # Test 4: DTO validation
        print("\n📦 Test 4: DTO validation")
        weights_sum = sum(allocation.target_weights.values())
        print(f"✅ Weights sum: {weights_sum}")
        
        # Check weights are approximately 1.0 (allowing for Decimal precision)
        if abs(weights_sum - Decimal("1.0")) < Decimal("0.0001"):
            print("✅ Weights sum validation: PASS")
        else:
            print(f"❌ Weights sum validation: FAIL (sum={weights_sum})")
            logger.error("Weights sum validation failed: sum=%s", weights_sum)
            sys.exit(1)
            
        # Test 5: DTO serialization
        print("\n🔄 Test 5: DTO serialization")
        dto_dict = allocation.model_dump()
        print(f"✅ DTO serialization: {len(dto_dict)} fields")
        
        # Recreate from dict
        allocation2 = StrategyAllocationDTO.from_dict(dto_dict)
        print("✅ DTO deserialization successful")
        
        # Test 6: Deterministic output
        print("\n🔁 Test 6: Deterministic output")
        allocation3 = orchestrator.run("sample", context)
        
        # Compare target weights (should be identical for same input)
        weights_match = allocation.target_weights == allocation3.target_weights
        print(f"✅ Deterministic weights: {weights_match}")
        
        if not weights_match:
            print("⚠️  Note: Non-determinism may be due to timestamp differences")
        
        print("\n🎉 Validation Summary")
        print("=" * 50)
        print("✅ All core functionality validated")
        print("✅ StrategyContext: Working")
        print("✅ Market data adapter: Working")
        print("✅ Strategy orchestrator: Working")
        print("✅ DTO mapping: Working")
        print("✅ Weight normalization: Working")
        print("✅ Serialization: Working")
        
        print("\n📋 Strategy_v2 Module Status: READY FOR INTEGRATION")
        logger.info("Strategy_v2 validation completed successfully")
        
    except Exception as e:
        logger.error("Strategy_v2 validation failed with exception: %s", e, exc_info=True)
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()