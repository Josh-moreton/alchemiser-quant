#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy Module CLI for Signal Generation.

Allows running the strategy_v2 module directly to generate current signals
without triggering trading. Provides signal output and analysis capabilities
for development and testing purposes.

Usage:
    python -m the_alchemiser.strategy_v2 [OPTIONS]

Examples:
    python -m the_alchemiser.strategy_v2                    # Run all strategies
    python -m the_alchemiser.strategy_v2 --list             # List available strategies
    python -m the_alchemiser.strategy_v2 --strategy Nuclear # Run specific strategy
    python -m the_alchemiser.strategy_v2 --format json      # Output as JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add the project root to Python path to ensure imports work
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging.logging_utils import configure_application_logging
from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI.
    
    Args:
        verbose: Enable debug logging if True
    """
    import logging
    configure_application_logging()
    
    # Adjust log level if verbose requested
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


def find_strategy_files() -> list[Path]:
    """Find all available strategy files.
    
    Returns:
        List of strategy file paths
    """
    strategies_dir = Path(__file__).parent / "strategies"
    if not strategies_dir.exists():
        return []
    
    return list(strategies_dir.glob("*.clj"))


def list_strategies() -> None:
    """List all available strategy files."""
    strategy_files = find_strategy_files()
    
    if not strategy_files:
        print("No strategy files found.")
        return
    
    print("Available strategies:")
    for strategy_file in sorted(strategy_files):
        strategy_name = strategy_file.stem
        print(f"  {strategy_name}")


def run_strategy(strategy_name: str | None = None, output_format: str = "table") -> None:
    """Run strategy signal generation.
    
    Args:
        strategy_name: Specific strategy to run, or None for all
        output_format: Output format (table, json)
    """
    try:
        # Load settings and configure system
        settings = load_settings()
        
        # Create a minimal container for dependencies
        # For CLI usage, we'll use test environment to avoid requiring real credentials
        container = ApplicationContainer.create_for_environment("test")
        
        # Get strategy files to run
        if strategy_name:
            strategy_files = find_strategy_files()
            # Try exact match first, then partial match
            matching_files = [f for f in strategy_files if f.stem.lower() == strategy_name.lower()]
            if not matching_files:
                # Try partial matching (e.g., "Nuclear" matches "2-Nuclear")
                matching_files = [f for f in strategy_files if strategy_name.lower() in f.stem.lower()]
            
            if not matching_files:
                print(f"Strategy '{strategy_name}' not found.")
                print("Available strategies:")
                for f in sorted(strategy_files):
                    print(f"  {f.stem}")
                sys.exit(1)
            
            # Run single strategy
            strategy_file = matching_files[0]
            print(f"🔄 Running strategy: {strategy_file.stem}")
            
            # Initialize the strategy engine
            market_data_port = container.infrastructure.market_data_service()
            engine = DslStrategyEngine(market_data_port, strategy_file.name)
            
            # Override the strategy configuration directly after creation
            from types import SimpleNamespace
            strategy_config = SimpleNamespace()
            strategy_config.dsl_files = [strategy_file.name]
            strategy_config.dsl_allocations = {strategy_file.name: 1.0}
            
            # Patch the settings temporarily
            original_strategy = engine.settings.strategy
            engine.settings.strategy = strategy_config
            
            try:
                # Generate signals with overridden configuration  
                timestamp = datetime.now(UTC)
                signals = engine.generate_signals(timestamp)
            finally:
                # Restore original settings
                engine.settings.strategy = original_strategy
            
        else:
            # Run all strategies (default behavior)
            print("🔄 Running all configured strategies...")
            market_data_port = container.infrastructure.market_data_service()
            engine = DslStrategyEngine(market_data_port)
            
            # Generate signals
            timestamp = datetime.now(UTC)
            signals = engine.generate_signals(timestamp)
        
        # Generate signals
        timestamp = datetime.now(UTC)
        signals = engine.generate_signals(timestamp)
        
        # Output results
        if output_format.lower() == "json":
            output_signals_json(signals)
        else:
            output_signals_table(signals)
            
    except Exception as e:
        print(f"❌ Error running strategy: {e}")
        print("\n💡 Note: This CLI runs in test mode with mock market data.")
        print("For live data, ensure proper Alpaca credentials are configured.")
        sys.exit(1)


def output_signals_table(signals: list[Any]) -> None:
    """Output signals in table format.
    
    Args:
        signals: List of strategy signals
    """
    if not signals:
        print("No signals generated.")
        return
    
    print("\n📊 Generated Signals:")
    print("=" * 80)
    print(f"{'Symbol':<10} {'Action':<6} {'Strategy':<15} {'Reasoning'}")
    print("-" * 80)
    
    for signal in signals:
        symbol = str(getattr(signal, 'symbol', 'UNKNOWN'))
        action = str(getattr(signal, 'action', 'UNKNOWN'))
        strategy = str(getattr(signal, 'strategy', 'UNKNOWN'))
        reasoning = str(getattr(signal, 'reasoning', 'No reasoning provided'))
        
        # Truncate reasoning for display
        if len(reasoning) > 45:
            reasoning = reasoning[:42] + "..."
            
        print(f"{symbol:<10} {action:<6} {strategy:<15} {reasoning}")
    
    print("=" * 80)
    print(f"Total signals: {len(signals)}")


def output_signals_json(signals: list[Any]) -> None:
    """Output signals in JSON format.
    
    Args:
        signals: List of strategy signals
    """
    signal_data = []
    for signal in signals:
        signal_dict = {
            "symbol": str(getattr(signal, 'symbol', 'UNKNOWN')),
            "action": str(getattr(signal, 'action', 'UNKNOWN')),
            "strategy": str(getattr(signal, 'strategy', 'UNKNOWN')),
            "reasoning": str(getattr(signal, 'reasoning', 'No reasoning provided')),
            "timestamp": getattr(signal, 'timestamp', datetime.now(UTC)).isoformat(),
            "data_source": str(getattr(signal, 'data_source', 'unknown')),
            "fallback": bool(getattr(signal, 'fallback', False)),
        }
        signal_data.append(signal_dict)
    
    print(json.dumps(signal_data, indent=2))


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Strategy Module CLI - Generate current signals without trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m the_alchemiser.strategy_v2                    # Run all strategies
  python -m the_alchemiser.strategy_v2 --list             # List available strategies  
  python -m the_alchemiser.strategy_v2 --strategy Nuclear # Run specific strategy
  python -m the_alchemiser.strategy_v2 --format json      # Output as JSON
        """,
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available strategy files",
    )
    
    parser.add_argument(
        "--strategy",
        help="Run specific strategy by name (e.g., Nuclear, TECL)",
        metavar="NAME",
    )
    
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    if args.list:
        list_strategies()
        return
    
    run_strategy(args.strategy, args.format)


if __name__ == "__main__":
    main()