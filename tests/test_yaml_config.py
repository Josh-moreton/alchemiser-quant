#!/usr/bin/env python3
"""
Test YAML configuration loading for Better Orders

Verifies that the better orders configuration can be loaded from config.yaml
and that all settings are applied correctly.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_yaml_config_loading():
    """Test loading better orders configuration from YAML."""
    print("🚀 Testing Better Orders YAML Configuration Loading...")

    # Import after adding to path
    from the_alchemiser.config.better_orders_config import (
        ExecutionMode,
        get_better_orders_config,
        get_config_summary,
        reload_better_orders_config,
    )

    # Test 1: Load configuration from YAML
    print("\n📋 1. Loading configuration from config.yaml...")

    # Force reload from YAML
    config_path = os.path.join(os.path.dirname(__file__), "..", "the_alchemiser", "config.yaml")
    reload_better_orders_config(config_path)

    config = get_better_orders_config()

    # Verify core settings
    assert config.enabled == True, "❌ Better orders should be enabled"
    assert config.execution_mode == ExecutionMode.AUTO, "❌ Execution mode should be AUTO"
    assert config.max_slippage_bps == 20.0, "❌ Max slippage should be 20.0 bps"
    assert config.aggressive_timeout_seconds == 2.5, "❌ Timeout should be 2.5 seconds"
    assert config.max_repegs == 2, "❌ Max re-pegs should be 2"

    print("✅ Core settings loaded correctly")
    print(f"  - Enabled: {config.enabled}")
    print(f"  - Execution mode: {config.execution_mode.value}")
    print(f"  - Max slippage: {config.max_slippage_bps} bps")
    print(f"  - Timeout: {config.aggressive_timeout_seconds}s")
    print(f"  - Max re-pegs: {config.max_repegs}")

    # Test 2: Verify symbol lists from YAML
    print("\n🏷️ 2. Verifying symbol lists from YAML...")

    # Check leveraged ETF symbols
    assert config.leveraged_etf_symbols is not None, "❌ Leveraged ETF symbols should be loaded"
    assert "TQQQ" in config.leveraged_etf_symbols, "❌ TQQQ should be in leveraged ETFs"
    assert "TECL" in config.leveraged_etf_symbols, "❌ TECL should be in leveraged ETFs"
    assert "SPXL" in config.leveraged_etf_symbols, "❌ SPXL should be in leveraged ETFs"

    # Check high-volume ETF symbols
    assert config.high_volume_etfs is not None, "❌ High-volume ETF symbols should be loaded"
    assert "SPY" in config.high_volume_etfs, "❌ SPY should be in high-volume ETFs"
    assert "QQQ" in config.high_volume_etfs, "❌ QQQ should be in high-volume ETFs"
    assert "TLT" in config.high_volume_etfs, "❌ TLT should be in high-volume ETFs"

    print("✅ Symbol lists loaded correctly")
    print(f"  - Leveraged ETFs: {len(config.leveraged_etf_symbols)} symbols")
    print(f"  - High-volume ETFs: {len(config.high_volume_etfs)} symbols")

    # Test 3: Verify spread thresholds
    print("\n📊 3. Verifying spread thresholds...")

    assert config.tight_spread_threshold == 3.0, "❌ Tight spread threshold should be 3.0¢"
    assert config.wide_spread_threshold == 5.0, "❌ Wide spread threshold should be 5.0¢"

    print("✅ Spread thresholds loaded correctly")
    print(f"  - Tight spread: ≤{config.tight_spread_threshold}¢")
    print(f"  - Wide spread: >{config.wide_spread_threshold}¢")

    # Test 4: Test symbol classification logic
    print("\n🔍 4. Testing symbol classification...")

    # Test leveraged ETF classification
    assert config.should_use_better_orders("TQQQ") == True, "❌ TQQQ should use better orders"
    assert config.should_use_better_orders("TECL") == True, "❌ TECL should use better orders"
    assert config.should_use_better_orders("SPXL") == True, "❌ SPXL should use better orders"

    # Test high-volume ETF classification
    assert config.should_use_better_orders("SPY") == True, "❌ SPY should use better orders"
    assert config.should_use_better_orders("QQQ") == True, "❌ QQQ should use better orders"

    # Test individual stock classification
    assert config.should_use_better_orders("AAPL") == False, "❌ AAPL should NOT use better orders"
    assert config.should_use_better_orders("MSFT") == False, "❌ MSFT should NOT use better orders"

    print("✅ Symbol classification working correctly")
    print("  - TQQQ, TECL, SPXL → Better orders ✅")
    print("  - SPY, QQQ → Better orders ✅")
    print("  - AAPL, MSFT → Standard execution ✅")

    # Test 5: Test slippage tolerance
    print("\n⚖️ 5. Testing slippage tolerance...")

    # Leveraged ETFs should have higher tolerance
    tqqq_slippage = config.get_slippage_tolerance("TQQQ")
    assert tqqq_slippage == 20.0, f"❌ TQQQ slippage should be 20.0, got {tqqq_slippage}"

    # High-volume ETFs should have lower tolerance
    spy_slippage = config.get_slippage_tolerance("SPY")
    assert spy_slippage == 10.0, f"❌ SPY slippage should be 10.0, got {spy_slippage}"

    # Individual stocks should have medium tolerance
    aapl_slippage = config.get_slippage_tolerance("AAPL")
    assert aapl_slippage == 15.0, f"❌ AAPL slippage should be 15.0, got {aapl_slippage}"

    print("✅ Slippage tolerance calculated correctly")
    print(f"  - TQQQ (leveraged): {tqqq_slippage} bps")
    print(f"  - SPY (high-volume): {spy_slippage} bps")
    print(f"  - AAPL (individual): {aapl_slippage} bps")

    # Test 6: Configuration summary
    print("\n📋 6. Configuration summary...")

    summary = get_config_summary()
    expected_keys = [
        "enabled",
        "execution_mode",
        "max_slippage_bps",
        "aggressive_timeout_seconds",
        "max_repegs",
        "leveraged_etf_count",
        "high_volume_etf_count",
        "tight_spread_threshold",
        "wide_spread_threshold",
    ]

    for key in expected_keys:
        assert key in summary, f"❌ Summary should contain {key}"

    print("✅ Configuration summary generated correctly")
    for key, value in summary.items():
        print(f"  - {key}: {value}")

    print("\n🎯 YAML Configuration Test Summary:")
    print("✅ Configuration loading from config.yaml")
    print("✅ Core settings validation")
    print("✅ Symbol lists verification")
    print("✅ Spread thresholds validation")
    print("✅ Symbol classification logic")
    print("✅ Slippage tolerance calculation")
    print("✅ Configuration summary generation")
    print("\n🚀 YAML configuration integration is fully operational!")


if __name__ == "__main__":
    test_yaml_config_loading()
