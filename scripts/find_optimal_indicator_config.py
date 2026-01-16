#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Find optimal per-indicator live bar configuration.

Runs SEQUENTIALLY with disk-cached data - network I/O is the bottleneck, not CPU.

Usage:
    poetry run python scripts/find_optimal_indicator_config.py --strategy rains_concise_em --expected "EDZ XLF"

"""

from __future__ import annotations

import argparse
import itertools
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Setup paths BEFORE imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from dotenv import load_dotenv
load_dotenv()

# Suppress ALL logging
logging.disable(logging.CRITICAL)
os.environ["STRUCTLOG_LEVEL"] = "CRITICAL"

try:
    import structlog
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(100))
except Exception:
    pass

ALL_INDICATORS = [
    "current_price", "rsi", "moving_average", "exponential_moving_average_price",
    "moving_average_return", "cumulative_return", "stdev_return", "stdev_price", "max_drawdown",
]

CURRENT_CONFIG = {
    "current_price": True, "rsi": True, "moving_average": True,
    "exponential_moving_average_price": False, "moving_average_return": True,
    "cumulative_return": False, "stdev_return": True, "stdev_price": False, "max_drawdown": True,
}

STRATEGY_DIR = PROJECT_ROOT / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"

# Global cached adapter and engine - reused across all tests
_CACHED_ADAPTER = None
_CACHED_ENGINE = None


@dataclass
class TestResult:
    config: dict[str, bool]
    symbols: set[str]
    allocation: dict[str, float]
    matches: bool
    config_idx: int


def get_engine():
    """Get cached engine instance."""
    global _CACHED_ADAPTER, _CACHED_ENGINE
    
    if _CACHED_ENGINE is None:
        from engines.dsl.engine import DslEngine
        from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
        
        _CACHED_ADAPTER = CachedMarketDataAdapter(append_live_bar=True)
        _CACHED_ENGINE = DslEngine(
            strategy_config_path=STRATEGY_DIR,
            market_data_adapter=_CACHED_ADAPTER,
            debug_mode=False,
        )
    
    return _CACHED_ENGINE


def run_with_config(config: dict[str, bool], strategy_name: str) -> tuple[frozenset[str], dict[str, float]]:
    """Run strategy with specific indicator config. Uses cached engine."""
    import indicators.indicator_service as indicator_service_mod
    
    # Patch should_use_live_bar for this config
    def custom_should_use_live_bar(indicator_type: str) -> bool:
        return config.get(indicator_type, True)
    
    indicator_service_mod.should_use_live_bar = custom_should_use_live_bar
    
    engine = get_engine()
    allocation_result, _ = engine.evaluate_strategy(f"{strategy_name}.clj", "test")
    allocation = {k: float(v) for k, v in allocation_result.target_weights.items()}
    symbols = frozenset(s for s, w in allocation.items() if w > 0.001)
    
    return symbols, allocation


def generate_all_configs() -> list[tuple[int, dict[str, bool]]]:
    """Generate all 512 configurations."""
    configs = []
    for i, bits in enumerate(itertools.product([False, True], repeat=len(ALL_INDICATORS))):
        config = dict(zip(ALL_INDICATORS, bits))
        configs.append((i, config))
    return configs


def warmup_cache(strategy_name: str):
    """Run once to populate disk cache with all market data."""
    print("   Warming up cache (first run fetches all data)...")
    config = {ind: True for ind in ALL_INDICATORS}
    run_with_config(config, strategy_name)
    print("   Cache warm!")


def run_full_search(strategy_name: str, expected: frozenset[str]) -> list[TestResult]:
    """Run all 512 configs sequentially with cached data."""
    all_configs = generate_all_configs()
    
    print(f"\n🚀 Testing {len(all_configs)} configs sequentially (cached data)...")
    print(f"   Expected: {sorted(expected)}")
    
    # Warmup to ensure cache is populated
    warmup_cache(strategy_name)
    
    start = datetime.now(timezone.utc)
    matches: list[TestResult] = []
    
    for i, (config_idx, config) in enumerate(all_configs):
        if (i + 1) % 50 == 0:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"   Progress: {i+1}/{len(all_configs)} ({rate:.1f}/sec)")
        
        try:
            symbols, allocation = run_with_config(config, strategy_name)
            if symbols == expected:
                matches.append(TestResult(
                    config=config,
                    symbols=set(symbols),
                    allocation=allocation,
                    matches=True,
                    config_idx=config_idx,
                ))
        except Exception as e:
            print(f"   Error on config {config_idx}: {e}")
    
    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    print(f"   ✅ Done in {elapsed:.1f}s ({len(all_configs)/elapsed:.1f} configs/sec)")
    print(f"   Found {len(matches)} matching config(s)")
    
    return matches


def run_quick_test(strategy_name: str, expected: frozenset[str]) -> list[TestResult]:
    """Quick test of key configs."""
    print(f"\n🔍 Quick test for {strategy_name}...")
    print(f"   Expected: {sorted(expected)}")
    
    key_configs = [
        ("all-live", {ind: True for ind in ALL_INDICATORS}),
        ("none-live", {ind: False for ind in ALL_INDICATORS}),
        ("current", CURRENT_CONFIG.copy()),
    ]
    
    matches: list[TestResult] = []
    
    for name, config in key_configs:
        symbols, allocation = run_with_config(config, strategy_name)
        is_match = symbols == expected
        status = "✅ MATCH" if is_match else "❌"
        print(f"   {name}: {sorted(symbols)} {status}")
        
        if is_match:
            matches.append(TestResult(config=config, symbols=set(symbols), allocation=allocation, matches=True, config_idx=0))
    
    return matches


def config_diff(config: dict[str, bool]) -> dict[str, str]:
    """Show diff from current config."""
    return {ind: ("LIVE" if val else "OFF") for ind, val in config.items() if CURRENT_CONFIG.get(ind) != val}


def main():
    parser = argparse.ArgumentParser(description="Find optimal indicator config")
    parser.add_argument("--strategy", help="Strategy name")
    parser.add_argument("--expected", help="Expected symbols (e.g., 'EDZ XLF')")
    parser.add_argument("--full", action="store_true", help="Skip quick test, go straight to full search")
    parser.add_argument("--list", action="store_true", help="List strategies")
    
    args = parser.parse_args()
    
    if args.list:
        for f in sorted(STRATEGY_DIR.glob("*.clj")):
            if f.stem != "strategy_ledger":
                print(f.stem)
        return
    
    if not args.strategy or not args.expected:
        parser.error("--strategy and --expected are required")
    
    expected = frozenset(s.strip().upper() for s in args.expected.replace(",", " ").split() if s.strip())
    
    print("=" * 70)
    print(f"INDICATOR CONFIG OPTIMIZER - {args.strategy}")
    print(f"Looking for: {sorted(expected)}")
    print("=" * 70)
    
    if not args.full:
        matches = run_quick_test(args.strategy, expected)
        if matches:
            print(f"\n✅ Found match in quick test!")
            for m in matches:
                diff = config_diff(m.config)
                print(f"   Changes needed: {diff}" if diff else "   Current config works!")
            return
        print("\n⚠️  No quick match. Running full search...")
    
    matches = run_full_search(args.strategy, expected)
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if not matches:
        print("❌ NO CONFIG FOUND that produces the expected symbols!")
        print("   The divergence is NOT due to live/non-live indicator settings.")
    else:
        print(f"✅ Found {len(matches)} matching config(s):")
        for i, m in enumerate(matches[:5], 1):
            diff = config_diff(m.config)
            print(f"\n   Config #{i}: {sorted(m.symbols)}")
            print(f"     Changes: {diff}" if diff else "     Current config works!")


if __name__ == "__main__":
    main()
