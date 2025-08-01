#!/usr/bin/env python3
"""
Better Orders Configuration Inspector

Shows the current better orders configuration loaded from config.yaml
and provides examples of how to modify settings.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def inspect_better_orders_config():
    """Inspect and display the current better orders configuration."""
    print("🔍 Better Orders Configuration Inspector")
    print("=" * 60)
    
    try:
        from the_alchemiser.config.better_orders_config import (
            get_better_orders_config,
            get_config_summary,
            reload_better_orders_config
        )
        
        # Load current configuration
        config = get_better_orders_config()
        summary = get_config_summary()
        
        print("\n📋 Current Configuration (from config.yaml):")
        print("-" * 50)
        
        # Core settings
        print("🔧 Core Settings:")
        print(f"  ✅ Enabled: {config.enabled}")
        print(f"  🎯 Execution Mode: {config.execution_mode.value}")
        print(f"  ⚡ Timeout: {config.aggressive_timeout_seconds}s")
        print(f"  🔄 Max Re-pegs: {config.max_repegs}")
        print(f"  📊 Max Slippage: {config.max_slippage_bps} bps")
        
        # Market timing settings
        print("\n⏰ Market Timing:")
        print(f"  📈 Pre-market Assessment: {config.enable_premarket_assessment}")
        print(f"  🚀 Fast Market Open: {config.market_open_fast_execution}")
        
        # Spread settings
        print("\n📊 Spread Thresholds:")
        print(f"  🟢 Tight Spread: ≤{config.tight_spread_threshold}¢")
        print(f"  🔴 Wide Spread: >{config.wide_spread_threshold}¢")
        
        # Symbol classification
        print("\n🏷️ Symbol Classification:")
        print(f"  ⚡ Leveraged ETFs: {len(config.leveraged_etf_symbols or [])} symbols")
        if config.leveraged_etf_symbols:
            leveraged_sample = config.leveraged_etf_symbols[:6]
            print(f"    Examples: {', '.join(leveraged_sample)}")
            if len(config.leveraged_etf_symbols) > 6:
                print(f"    ... and {len(config.leveraged_etf_symbols) - 6} more")
        
        print(f"  📈 High-Volume ETFs: {len(config.high_volume_etfs or [])} symbols")
        if config.high_volume_etfs:
            volume_sample = config.high_volume_etfs[:6]
            print(f"    Examples: {', '.join(volume_sample)}")
            if len(config.high_volume_etfs) > 6:
                print(f"    ... and {len(config.high_volume_etfs) - 6} more")
        
        # Test some symbols
        print("\n🧪 Symbol Testing:")
        test_symbols = ["TQQQ", "SPY", "AAPL", "QQQ", "MSFT", "TECL"]
        
        for symbol in test_symbols:
            uses_better_orders = config.should_use_better_orders(symbol)
            slippage = config.get_slippage_tolerance(symbol)
            status = "✅ Better Orders" if uses_better_orders else "🔄 Standard"
            print(f"  {symbol:6} → {status:15} | {slippage:4.1f} bps slippage")
        
        # Configuration file location
        print("\n📁 Configuration Source:")
        config_path = None
        search_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'the_alchemiser', 'config.yaml'),
            os.path.join(os.getcwd(), 'config.yaml'),
            os.path.join(os.getcwd(), 'the_alchemiser', 'config.yaml'),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                config_path = os.path.abspath(path)
                break
        
        if config_path:
            print(f"  📄 Loaded from: {config_path}")
        else:
            print("  ⚠️  Using default configuration (config.yaml not found)")
        
        # Usage examples
        print("\n📝 Configuration Examples:")
        print("-" * 50)
        
        print("""
🔧 To modify better orders settings, edit your config.yaml:

# Enable/disable better orders entirely
better_orders:
  enabled: true                    # Set to false to disable

# Change execution mode
  execution_mode: "auto"           # Options: "auto", "better_orders", "standard"

# Adjust risk settings
  max_slippage_bps: 20.0          # Maximum slippage tolerance
  aggressive_timeout_seconds: 2.5  # How long to wait for fills
  max_repegs: 2                    # Max re-peg attempts

# Add/remove symbols from better orders
  leveraged_etf_symbols:
    - "TQQQ"
    - "SPXL" 
    - "YOUR_SYMBOL_HERE"           # Add your symbols

  high_volume_etfs:
    - "SPY"
    - "QQQ"
    - "YOUR_ETF_HERE"              # Add your ETFs
""")
        
        print("\n🔄 Programmatic Configuration:")
        print("""
# Reload configuration after editing config.yaml
from the_alchemiser.config.better_orders_config import reload_better_orders_config
reload_better_orders_config()

# Temporarily override settings (in-memory only)
from the_alchemiser.config.better_orders_config import update_better_orders_config
update_better_orders_config(max_slippage_bps=15.0, enabled=False)
""")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("\nThis might indicate:")
        print("  1. The better orders module is not properly installed")
        print("  2. The config.yaml file has syntax errors")
        print("  3. Missing dependencies (pyyaml)")
        
    print("\n" + "=" * 60)
    print("📖 For more information, see: better_orders_implementation_plan.md")

if __name__ == "__main__":
    inspect_better_orders_config()
